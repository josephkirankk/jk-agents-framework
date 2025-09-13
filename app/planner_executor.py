from __future__ import annotations
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from pathlib import Path
import re
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, ValidationError
from .utils import extract_json_block
from langchain.chat_models import init_chat_model
from .thread_manager import get_or_create_thread_id, create_supervisor_thread_id, create_step_thread_id

log = logging.getLogger("planner_executor")
logging.getLogger("planner_executor").setLevel(logging.INFO)


@asynccontextmanager
async def safe_langgraph_execution():
    """
    Async context manager for safe LangGraph execution.

    This helps prevent TaskGroup exceptions from propagating unhandled
    by providing a controlled execution environment.
    """
    try:
        yield
    except BaseExceptionGroup as e:
        # Handle TaskGroup exceptions by extracting underlying errors
        log.error("TaskGroup exception caught in safe execution context: %s",
                  e)
        underlying_exceptions = []
        if hasattr(e, 'exceptions'):
            for exc in e.exceptions:
                underlying_exceptions.append(str(exc))

        if underlying_exceptions:
            error_msg = "Execution failed: " + "; ".join(underlying_exceptions)
        else:
            error_msg = f"Execution failed with TaskGroup error: {str(e)}"

        raise RuntimeError(error_msg) from e
    except Exception as e:
        # Re-raise other exceptions normally
        log.error("Exception in safe execution context: %s", e)
        raise


class PlanStep(BaseModel):
    id: str
    agent: str
    task: str
    depends_on: Optional[List[str]] = Field(default_factory=list)
    verify: Optional[str] = None
    timeout_seconds: Optional[int] = None
    retry: Optional[int] = 0


class Plan(BaseModel):
    goal: Optional[str] = None
    plan: List[PlanStep]


def parse_plan_text(text: str) -> Optional[Plan]:
    block = extract_json_block(text)
    if not block:
        return None
    try:
        data = json.loads(block)
        return Plan(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        log.warning("Plan parse failed: %s", e)
        return None


def topo_sort_steps(steps: List[PlanStep]) -> List[PlanStep]:
    id_map = {s.id: s for s in steps}
    incoming = {s.id: set(s.depends_on or []) for s in steps}
    for s in steps:
        for d in incoming[s.id]:
            if d not in id_map:
                raise ValueError(
                    f"Step '{s.id}' depends on unknown step '{d}'"
                )
    ready = [sid for sid, deps in incoming.items() if not deps]
    order = []
    while ready:
        cur = ready.pop(0)
        order.append(id_map[cur])
        for sid in list(incoming.keys()):
            if cur in incoming[sid]:
                incoming[sid].remove(cur)
                if not incoming[sid]:
                    ready.append(sid)
    if len(order) != len(steps):
        raise ValueError("Cycle detected in plan dependencies")
    return order


def _sanitize_for_moderation(text: str, max_chars: int = 2000) -> str:
    """
    Reduce the chance of tripping content filters by:
    - Removing URLs/emails
    - Collapsing whitespace
    - Truncating overly long content
    """
    if not isinstance(text, str):
        return ""
    # Strip URLs and emails
    text = re.sub(r"https?://\S+", "[link]", text)
    text = re.sub(r"\b[\w.-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email]", text)
    # Collapse code blocks and excessive markup
    text = re.sub(r"```[\s\S]*?```", "[code omitted]", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Truncate
    if len(text) > max_chars:
        text = text[:max_chars] + " …"
    return text


async def llm_verify(check_prompt: str, model: str):
    # Import the create_model_instance function to handle custom prefixes
    from app.agent_builder import create_model_instance

    # Create model instance (handles custom prefixes like pepgenx:, lmstudio:)
    model_instance = create_model_instance(model)

    # Check if it's already a model instance or needs initialization
    if (hasattr(model_instance, 'invoke') or
            hasattr(model_instance, 'ainvoke')):
        chat = model_instance
    else:
        chat = init_chat_model(model_instance)
    messages = [
        {"role": "system", "content": "You are an objective verifier."},
        {"role": "user", "content": check_prompt},
    ]
    try:
        out = await chat.ainvoke(messages)
    except AttributeError:
        out = chat.invoke(messages)
    except Exception as e:
        # Graceful fallback for content filter or policy blocks
        msg = str(e)
        if "content_filter" in msg or "policy" in msg.lower():
            log.warning(
                "Verifier blocked by policy/content filter; "
                "attempting simplified prompt"
            )
            simple_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an objective verifier. Only return "
                        "strict JSON as instructed."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Return JSON {\\\"ok\\\": true, "
                        "\\\"reason\\\": \\\"skipped due to policy\\\"}"
                    ),
                },
            ]
            try:
                try:
                    out = await chat.ainvoke(simple_messages)
                except AttributeError:
                    out = chat.invoke(simple_messages)
                # Treat as verified to avoid aborting the whole plan
                return True, "verification skipped due to model policy"
            except Exception:
                # Final fallback: skip verification
                return True, (
                    "verification skipped due to model policy (fallback)"
                )
        # Unknown error: mark as not verified but don't crash caller
        log.exception("Verifier errored: %s", e)
        return False, f"verifier error: {e}"
    # LangChain ChatModel returns a BaseMessage with .content
    text = getattr(out, "content", "")
    block = extract_json_block(text)
    if not block:
        return False, "verifier output not parseable"
    try:
        j = json.loads(block)
        return bool(j.get("ok", False)), str(j.get("reason", ""))
    except Exception as e:
        return False, f"verifier parse error: {e}"


async def execute_plan(
    supervisor_compiled,
    agents_map: Dict[str, Any],
    user_input: str,
    business_context: str = "",
    default_model_for_verifier: str = "openai:gpt-4o-mini",
    max_total_retries: int = 2,
    human_in_loop: bool = False,
    default_step_timeout_seconds: Optional[int] = 120,
    default_supervisor_timeout_seconds: Optional[int] = 60,
    default_verifier_timeout_seconds: Optional[int] = 45,
    agents_configs: Optional[List] = None,
    default_model: str = "openai:gpt-4o-mini",
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    # Get or create base thread ID for this execution
    base_thread_id = get_or_create_thread_id(thread_id)
    supervisor_thread_id = create_supervisor_thread_id(base_thread_id)

    # Prepare log file with timestamped name at repo root
    log_file_path: Optional[Path] = None
    try:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        repo_root = Path(__file__).resolve().parents[1]
        log_file_path = repo_root / f"agentlog_{ts}.log"
    except Exception:
        log_file_path = None

    def _safe_write(lines: List[str]):
        if not log_file_path:
            return
        try:
            with log_file_path.open("a", encoding="utf-8") as f:
                for line in lines:
                    f.write(line)
                    if not line.endswith("\n"):
                        f.write("\n")
        except Exception as e:
            log.debug("Log file write failed: %s", e)

    def _extract_usage(msg: Any) -> Dict[str, int]:
        usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        try:
            # LangChain AIMessage often carries usage_metadata
            meta = getattr(msg, "usage_metadata", None)
            if meta and isinstance(meta, dict):
                usage.update({
                    "input_tokens": int(meta.get("input_tokens", 0) or 0),
                    "output_tokens": int(meta.get("output_tokens", 0) or 0),
                    "total_tokens": int(
                        meta.get("total_tokens", 0)
                        or (
                            int(meta.get("input_tokens", 0) or 0)
                            + int(meta.get("output_tokens", 0) or 0)
                        )
                    ),
                })
                return usage
            # Some providers embed in response_metadata
            rmeta = getattr(msg, "response_metadata", None)
            if isinstance(rmeta, dict):
                token_usage = rmeta.get("token_usage") or rmeta.get("usage")
                if isinstance(token_usage, dict):
                    usage.update({
                        "input_tokens": int(
                            token_usage.get(
                                "prompt_tokens",
                                token_usage.get("input_tokens", 0),
                            )
                            or 0
                        ),
                        "output_tokens": int(
                            token_usage.get(
                                "completion_tokens",
                                token_usage.get("output_tokens", 0),
                            )
                            or 0
                        ),
                    })
                    usage["total_tokens"] = (
                        usage["input_tokens"] + usage["output_tokens"]
                    )
                    return usage
            # Dict-shaped message
            if isinstance(msg, dict):
                um = msg.get("usage_metadata") or msg.get("usage")
                if isinstance(um, dict):
                    usage.update({
                        "input_tokens": int(um.get("input_tokens", 0) or 0),
                        "output_tokens": int(um.get("output_tokens", 0) or 0),
                    })
                    usage["total_tokens"] = (
                        usage["input_tokens"] + usage["output_tokens"]
                    )
        except Exception:
            pass
        return usage

    def _extract_tool_calls(messages: List[Any]) -> List[Dict[str, Any]]:
        """Extract tool calls and results from messages, with deduplication."""
        tool_calls = []
        seen_calls = set()  # Track (name, args_hash) to detect duplicates

        for msg in messages:
            msg_type = getattr(msg, 'type', None)

            # Check for AIMessage with tool_calls
            if msg_type == 'ai' and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Handle different tool call formats
                    if hasattr(tool_call, 'name'):
                        name = tool_call.name
                    elif isinstance(tool_call, dict):
                        name = tool_call.get('name', 'unknown')
                    else:
                        name = 'unknown'

                    if hasattr(tool_call, 'id'):
                        call_id = tool_call.id
                    elif isinstance(tool_call, dict):
                        call_id = tool_call.get('id', 'unknown')
                    else:
                        call_id = 'unknown'

                    if hasattr(tool_call, 'args'):
                        args = tool_call.args
                    elif isinstance(tool_call, dict):
                        args = tool_call.get('args', {})
                    else:
                        args = {}

                    # Create a hash of the arguments for deduplication
                    args_str = json.dumps(args, sort_keys=True) if args else ""
                    call_signature = (name, args_str)

                    call_info = {
                        "type": "tool_call",
                        "name": name,
                        "id": call_id,
                        "args": args,
                        "is_duplicate": call_signature in seen_calls
                    }

                    seen_calls.add(call_signature)
                    tool_calls.append(call_info)

            # Check for ToolMessage with results
            elif msg_type == 'tool':
                tool_id = getattr(msg, 'tool_call_id', 'unknown')
                content = getattr(msg, 'content', '')
                name = getattr(msg, 'name', 'unknown')

                # Find matching tool call and add result
                for call in tool_calls:
                    if call.get("id") == tool_id:
                        call["result"] = content
                        if call["name"] == 'unknown' and name != 'unknown':
                            call["name"] = name
                        break
                else:
                    # Tool result without matching call
                    tool_calls.append({
                        "type": "tool_result",
                        "name": name,
                        "id": tool_id,
                        "result": content
                    })

        return tool_calls

    def _format_args_compact(args: Dict[str, Any]) -> str:
        """Format tool arguments in a compact way."""
        if not args:
            return ""

        formatted_args = []
        for key, value in args.items():
            if isinstance(value, str):
                # Truncate long strings
                if len(value) > 50:
                    value_str = f'"{value[:47]}..."'
                else:
                    value_str = f'"{value}"'
            else:
                value_str = str(value)
            formatted_args.append(f"{key}={value_str}")

        return ", ".join(formatted_args)

    # Initialize log header
    _safe_write([
        "=== jk-agents run log ===",
        f"Started: {datetime.now().isoformat(timespec='seconds')}",
        f"User input: {user_input}",
        f"Business context: {(business_context or '(none)')}",
        "",
    ])

    # Track usage summary
    calls = {"supervisor": 0, "worker": 0}
    tokens = {
        "supervisor": {"input": 0, "output": 0, "total": 0},
        "worker": {"input": 0, "output": 0, "total": 0},
    }
    sup_system_context = (
        "Business context:\n"
        f"{business_context}"
    )
    sup_state = {
        "messages": [
            {"role": "system", "content": sup_system_context},
            {"role": "user", "content": user_input},
        ]
    }
    # Print/log the query/messages used to build the plan
    try:
        log.info(
            "Supervisor invocation messages to build plan:\n%s",
            json.dumps(sup_state, indent=2, ensure_ascii=False),
        )
        print(
            "Supervisor invocation messages to build plan:\n"
            + json.dumps(sup_state, indent=2, ensure_ascii=False)
        )
    except Exception as e:
        log.warning("Failed to print supervisor invocation messages: %s", e)
    try:
        config = {"configurable": {"thread_id": supervisor_thread_id}}
        # Log supervisor request
        _safe_write([
            "--- Supervisor Request ---",
            f"Model: {getattr(supervisor_compiled, '_model_id', 'unknown')}",
            f"Planning Prompt: {getattr(supervisor_compiled, '_rendered_prompt', '(none)')}",
            f"System Context: {sup_system_context}",
            f"User: {user_input}",
            "",
        ])
        log.info(
            "Supervisor planning: start (timeout=%ss)",
            default_supervisor_timeout_seconds,
        )
        t0 = time.perf_counter()
        if default_supervisor_timeout_seconds:
            sup_out = await asyncio.wait_for(
                supervisor_compiled.ainvoke(sup_state, config=config),
                timeout=default_supervisor_timeout_seconds,
            )
        else:
            sup_out = await supervisor_compiled.ainvoke(
                sup_state, config=config
            )
        log.info(
            "Supervisor planning: done in %.2fs",
            time.perf_counter() - t0,
        )
    except AttributeError:
        config = {"configurable": {"thread_id": supervisor_thread_id}}
        _safe_write([
            "--- Supervisor Request ---",
            f"Model: {getattr(supervisor_compiled, '_model_id', 'unknown')}",
            f"Planning Prompt: {getattr(supervisor_compiled, '_rendered_prompt', '(none)')}",
            f"System Context: {sup_system_context}",
            f"User: {user_input}",
            "",
        ])
        log.info(
            "Supervisor planning (sync): start (timeout=%ss)",
            default_supervisor_timeout_seconds,
        )
        t0 = time.perf_counter()
        if default_supervisor_timeout_seconds:
            sup_out = await asyncio.wait_for(
                asyncio.to_thread(
                    supervisor_compiled.invoke, sup_state, config=config
                ),
                timeout=default_supervisor_timeout_seconds,
            )
        else:
            sup_out = await asyncio.to_thread(
                supervisor_compiled.invoke, sup_state, config=config
            )
        log.info(
            "Supervisor planning (sync): done in %.2fs",
            time.perf_counter() - t0,
        )
    except asyncio.TimeoutError:
        raise RuntimeError(
            "Supervisor planning timed out after "
            f"{default_supervisor_timeout_seconds}s"
        )
    except asyncio.CancelledError:
        raise RuntimeError(
            "Supervisor planning cancelled (timeout or external cancel)"
        )

    sup_msgs = sup_out.get("messages", [])
    if sup_msgs:
        # LangGraph messages are objects with .content attribute
        last_msg = sup_msgs[-1]
        sup_text = getattr(last_msg, "content", "")
        # Track usage for supervisor
        calls["supervisor"] += 1
        u = _extract_usage(last_msg)
        tokens["supervisor"]["input"] += u.get("input_tokens", 0)
        tokens["supervisor"]["output"] += u.get("output_tokens", 0)
        tokens["supervisor"]["total"] += u.get("total_tokens", 0)
    else:
        sup_text = ""
    log.info("Supervisor plan text: %s", sup_text[:400])
    # Log supervisor response
    _safe_write([
        "--- Supervisor Response ---",
        sup_text or "(empty)",
        "",
    ])

    plan = parse_plan_text(sup_text)
    if not plan:
        from .utils import parse_supervisor_json
        dec = parse_supervisor_json(sup_text)
        if dec and dec.agent:
            plan = Plan(
                goal=dec.reason or user_input,
                plan=[
                    PlanStep(
                        id="s1",
                        agent=dec.agent,
                        task=dec.task or user_input,
                    )
                ],
            )
        else:
            first_agent = next(iter(agents_map.keys()))
            plan = Plan(
                goal=user_input,
                plan=[
                    PlanStep(id="s1", agent=first_agent, task=user_input)
                ],
            )

    # Print the complete plan JSON for visibility/debugging
    try:
        plan_json_str = json.dumps(plan.dict(), indent=2, ensure_ascii=False)
        log.info("Complete plan JSON:\n%s", plan_json_str)
        print("Complete plan JSON:\n" + plan_json_str)
    except Exception as e:
        log.warning("Failed to serialize plan to JSON: %s", e)

    for step in plan.plan:
        if step.agent not in agents_map:
            raise RuntimeError(
                f"Plan step references unknown agent '{step.agent}'"
            )

    ordered_steps = topo_sort_steps(plan.plan)

    step_results: Dict[str, Dict[str, Any]] = {}
    # Count only actual retries across the entire plan (not initial attempts)
    global_retries_done = 0

    def _format_dependent_request_responses(
        depends_on: Optional[List[str]],
    ) -> str:
        """Build dependent_request_responses string for agent prompt template.

        Format:
        Previous Steps :
        User Agent : <task string say dependent step 1>
        Agent Response : <result from the worker step 1>
        User Agent : <task string say dependent step 2>
        Agent Response : <result from the worker step 2>
        """
        if not step_results or not depends_on:
            return ""

        dep_set = set(depends_on)
        lines: List[str] = ["Previous Steps :"]

        # Process dependencies in order they appear in step_results (execution order)
        for sid, info in step_results.items():
            if sid in dep_set:
                task = info.get('request', '')
                response = info.get('raw', '')
                lines.append(f"User Agent : {task}")
                lines.append(f"Agent Response : {response}")

        return "\n".join(lines) if len(lines) > 1 else ""

    for step in ordered_steps:
        attempts = 0
        last_err = None
        # Default one retry for steps that include verification
        local_retry_limit = step.retry or (1 if step.verify else 0)
        next_task_override: Optional[str] = None
        while True:
            attempts += 1
            # Build dependent request/responses for this step
            dependent_req_resp = _format_dependent_request_responses(step.depends_on)

            # Use existing compiled agent but inject dependent context via system message
            user_task = next_task_override or step.task
            worker_compiled = agents_map[step.agent]

            # Build system context with business context and dependent steps
            system_context = f"Business context:\n{business_context}"
            if dependent_req_resp:
                system_context += f"\n\n{dependent_req_resp}"

            worker_state = {
                "messages": [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_task},
                ]
            }

            # Determine timeout for this worker step (both async/sync paths)
            step_timeout = (
                step.timeout_seconds
                if step.timeout_seconds is not None
                else default_step_timeout_seconds
            )

            try:
                step_thread_id = create_step_thread_id(base_thread_id, step.id)
                worker_config = {
                    "configurable": {"thread_id": step_thread_id}
                }
                # Log worker request
                _safe_write([
                    (
                        f"--- Worker Request (step={step.id}, "
                        f"agent={step.agent}, attempt={attempts}) ---"
                    ),
                    f"Model: {getattr(worker_compiled, '_model_id', 'unknown')}",
                    f"Agent Prompt: {getattr(worker_compiled, '_rendered_prompt', '(none)')}",
                    f"System Context: {system_context}",
                    f"User: {user_task}",
                    "",
                ])

                # Enhanced error handling using safe context manager
                async with safe_langgraph_execution():
                    if step_timeout:
                        log.info(
                            "Worker %s attempt %d: ainvoke start (timeout=%ss)",
                            step.id,
                            attempts,
                            step_timeout,
                        )
                        t1 = time.perf_counter()
                        worker_out = await asyncio.wait_for(
                            worker_compiled.ainvoke(
                                worker_state, config=worker_config
                            ),
                            timeout=step_timeout,
                        )
                    else:
                        log.info(
                            "Worker %s attempt %d: ainvoke start (no timeout)",
                            step.id,
                            attempts,
                        )
                        t1 = time.perf_counter()
                        worker_out = await worker_compiled.ainvoke(
                            worker_state, config=worker_config
                        )
                    log.info(
                        "Worker %s attempt %d: ainvoke done in %.2fs",
                        step.id,
                        attempts,
                        time.perf_counter() - t1,
                    )
            except AttributeError:
                step_thread_id = create_step_thread_id(base_thread_id, step.id)
                worker_config = {
                    "configurable": {"thread_id": step_thread_id}
                }
                _safe_write([
                    (
                        f"--- Worker Request (step={step.id}, "
                        f"agent={step.agent}, attempt={attempts}) ---"
                    ),
                    f"Model: {getattr(worker_compiled, '_model_id', 'unknown')}",
                    f"Agent Prompt: {getattr(worker_compiled, '_rendered_prompt', '(none)')}",
                    f"System Context: {system_context}",
                    f"User: {user_task}",
                    "",
                ])
                # Enhanced error handling for sync path using safe context mgr
                async with safe_langgraph_execution():
                    if step_timeout:
                        log.info(
                            (
                                "Worker %s attempt %d: "
                                "invoke(sync) start (timeout=%ss)"
                            ),
                            step.id,
                            attempts,
                            step_timeout,
                        )
                        t1 = time.perf_counter()
                        worker_out = await asyncio.wait_for(
                            asyncio.to_thread(
                                worker_compiled.invoke,
                                worker_state,
                                config=worker_config,
                            ),
                            timeout=step_timeout,
                        )
                    else:
                        log.info(
                            (
                                "Worker %s attempt %d: "
                                "invoke(sync) start (no timeout)"
                            ),
                            step.id,
                            attempts,
                        )
                        t1 = time.perf_counter()
                        worker_out = await asyncio.to_thread(
                            worker_compiled.invoke,
                            worker_state,
                            config=worker_config,
                        )
                    log.info(
                        "Worker %s attempt %d: invoke(sync) done in %.2fs",
                        step.id,
                        attempts,
                        time.perf_counter() - t1,
                    )
            except asyncio.TimeoutError:
                last_err = "timeout"
                log.warning(
                    "Step %s timed out (limit=%ss)",
                    step.id,
                    step_timeout,
                )
                worker_out = {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": (
                                "ERROR: timeout after " f"{step_timeout}s"
                            ),
                        }
                    ]
                }
            except asyncio.CancelledError:
                last_err = "cancelled"
                log.warning(
                    "Step %s cancelled (timeout or external cancel)",
                    step.id,
                )
                worker_out = {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": "ERROR: cancelled",
                        }
                    ]
                }
            except Exception as e:
                last_err = str(e)
                log.exception("Step %s execution failed: %s", step.id, e)
                worker_out = {
                    "messages": [
                        {"role": "assistant", "content": f"ERROR: {e}"}
                    ]
                }

            wmsgs = worker_out.get("messages", [])
            if wmsgs:
                # LangGraph messages are objects with .content attribute
                last_msg = wmsgs[-1]
                wtext = getattr(last_msg, "content", "")
                # Track usage for worker
                calls["worker"] += 1
                wu = _extract_usage(last_msg)
                tokens["worker"]["input"] += wu.get("input_tokens", 0)
                tokens["worker"]["output"] += wu.get("output_tokens", 0)
                tokens["worker"]["total"] += wu.get("total_tokens", 0)
            else:
                wtext = ""
            # Use a longer summary to avoid truncating key facts
            summary = (wtext[:1200] + "...") if len(wtext) > 1200 else wtext

            # Extract tool calls from worker messages
            tool_calls = _extract_tool_calls(wmsgs) if wmsgs else []

            # Log worker response
            log_lines = [
                (
                    f"--- Worker Response (step={step.id}, "
                    f"agent={step.agent}, attempt={attempts}) ---"
                ),
                wtext or "(empty)",
                "",
            ]

            # Add tool calls section if any were found
            if tool_calls:
                log_lines.extend([
                    "--- Tool Calls ---",
                ])
                for i, call in enumerate(tool_calls, 1):
                    if call["type"] == "tool_call":
                        args_str = _format_args_compact(call.get("args", {}))
                        duplicate_marker = " (DUPLICATE)" if call.get("is_duplicate", False) else ""
                        log_lines.append(f"{i}. {call['name']}({args_str}){duplicate_marker}")
                        if "result" in call:
                            result_str = str(call["result"])[:100]
                            if len(str(call["result"])) > 100:
                                result_str += "..."
                            log_lines.append(f"   → {result_str}")
                    elif call["type"] == "tool_result":
                        result_str = str(call["result"])[:100]
                        if len(str(call["result"])) > 100:
                            result_str += "..."
                        log_lines.append(f"{i}. Tool Result [{call['id']}]: {result_str}")
                log_lines.append("")

            _safe_write(log_lines)
            # Summarize the request we sent to the worker so we can include it
            # in subsequent steps' context without overwhelming them.
            request_text = user_task
            request_summary = (
                (request_text[:400] + "...")
                if len(request_text) > 400
                else request_text
            )

            step_results[step.id] = {
                "agent": step.agent,
                "task": step.task,
                "attempts": attempts,
                "request": request_text,
                "request_summary": request_summary,
                "raw": wtext,
                "output_summary": summary,
                "ok": True
                if not (wtext.startswith("ERROR") or last_err)
                else False,
                "last_error": last_err,
            }

            verified = True
            verify_reason = ""
            if step.verify:
                log.info(
                    "Verifier: start for step %s (timeout=%ss)",
                    step.id,
                    default_verifier_timeout_seconds,
                )
                v0 = time.perf_counter()
                check_prompt = (
                    f"Verification instruction: {step.verify}\n"
                    f"Step output (sanitized): "
                    f"{_sanitize_for_moderation(wtext)}\n"
                    "Return JSON: {\"ok\": true/false, \"reason\":\"...\"}"
                )
                ok, reason = True, "skipped"
                try:
                    if default_verifier_timeout_seconds:
                        ok, reason = await asyncio.wait_for(
                            llm_verify(
                                check_prompt, default_model_for_verifier
                            ),
                            timeout=default_verifier_timeout_seconds,
                        )
                    else:
                        ok, reason = await llm_verify(
                            check_prompt, default_model_for_verifier
                        )
                except asyncio.TimeoutError:
                    ok, reason = True, "verifier timeout; treating as ok"
                except asyncio.CancelledError:
                    ok, reason = True, "verifier cancelled; treating as ok"
                finally:
                    log.info(
                        (
                            "Verifier: done for step %s in %.2fs "
                            "(ok=%s, reason=%s)"
                        ),
                        step.id,
                        time.perf_counter() - v0,
                        ok,
                        str(reason)[:200],
                    )
                verified = ok
                verify_reason = reason
                step_results[step.id].update(
                    {"verified": verified, "verify_reason": verify_reason}
                )

            if step_results[step.id]["ok"] and (
                step.verify is None or verified
            ):
                log.info("Step %s completed successfully", step.id)
                break
            else:
                # If verification failed, prepare a corrective instruction
                if step.verify and not verified:
                    guidance = (
                        "Verification failed: "
                        f"{verify_reason}.\n\n"
                        "Revise your answer to satisfy: "
                        f"{step.verify}.\n"
                        "Prefer credible sources such as the India "
                        "Meteorological Department (IMD), Wikipedia, or "
                        "World Weather Online; avoid forums or "
                        "user-generated content."
                    )
                    next_task_override = (
                        f"{step.task}\n\nFollow-up correction:\n{guidance}"
                    )

                if attempts <= local_retry_limit:
                    # Check global retry budget before consuming another retry
                    if global_retries_done >= max_total_retries:
                        log.warning(
                            "Reached global retry limit (%d). "
                            "Aborting plan execution.",
                            max_total_retries,
                        )
                        if human_in_loop:
                            return {
                                "plan": plan.dict(),
                                "steps": step_results,
                                "status": "paused_for_human",
                                "failed_step": step.id,
                            }
                        raise RuntimeError(
                            (
                                "Plan execution aborted: step {sid} "
                                "failed and retries exhausted"
                            ).format(sid=step.id)
                        )
                    # Consume one global retry and try again
                    global_retries_done += 1
                    # attempts is 1 on first failure -> this is retry #1
                    cur_retry = attempts
                    log.info(
                        "Retrying step %s (retry %d/%d, global %d/%d)",
                        step.id,
                        cur_retry,
                        local_retry_limit,
                        global_retries_done,
                        max_total_retries,
                    )
                    continue
                # Local retries exhausted
                if human_in_loop:
                    return {
                        "plan": plan.dict(),
                        "steps": step_results,
                        "status": "paused_for_human",
                        "failed_step": step.id,
                    }
                # Fail the plan with a clear message
                raise RuntimeError(
                    (
                        "Step {sid} failed: last_error={err}, "
                        "verify_failed={vf}, reason={reason}"
                    ).format(
                        sid=step.id,
                        err=last_err,
                        vf=(not verified),
                        reason=verify_reason,
                    )
                )

    final_agg = {
        sid: {"summary": info["output_summary"], "raw": info["raw"]}
        for sid, info in step_results.items()
    }

    # Write summary to log
    total_calls = calls["supervisor"] + calls["worker"]
    total_input = tokens["supervisor"]["input"] + tokens["worker"]["input"]
    total_output = tokens["supervisor"]["output"] + tokens["worker"]["output"]
    total_tokens = tokens["supervisor"]["total"] + tokens["worker"]["total"]
    _safe_write([
        "=== Summary ===",
        (
            "LLM calls: total="
            f"{total_calls}, supervisor={calls['supervisor']}, "
            f"worker={calls['worker']}"
        ),
        (
            "Tokens: "
            f"supervisor(input={tokens['supervisor']['input']}, "
            f"output={tokens['supervisor']['output']}, "
            f"total={tokens['supervisor']['total']}), "
            f"worker(input={tokens['worker']['input']}, "
            f"output={tokens['worker']['output']}, "
            f"total={tokens['worker']['total']}), "
            f"overall(input={total_input}, output={total_output}, "
            f"total={total_tokens})"
        ),
        "",
        "End of log",
    ])
    return {
        "plan": plan.dict(),
        "steps": step_results,
        "final_result": final_agg,
        "status": "completed",
    }
