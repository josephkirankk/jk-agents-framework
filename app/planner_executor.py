from __future__ import annotations
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ValidationError
from .utils import extract_json_block
from langchain.chat_models import init_chat_model

log = logging.getLogger("planner_executor")
logging.getLogger("planner_executor").setLevel(logging.INFO)


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


async def llm_verify(check_prompt: str, model: str):
    chat = init_chat_model(model)
    messages = [
        {"role": "system", "content": "You are an objective verifier."},
        {"role": "user", "content": check_prompt},
    ]
    try:
        out = await chat.ainvoke(messages)
    except AttributeError:
        out = chat.invoke(messages)
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
) -> Dict[str, Any]:
    sup_state = {
        "messages": [
            {"role": "system", "content": business_context},
            {"role": "user", "content": user_input},
        ]
    }
    try:
        config = {"configurable": {"thread_id": "execute-plan-thread"}}
        sup_out = await supervisor_compiled.ainvoke(sup_state, config=config)
    except AttributeError:
        config = {"configurable": {"thread_id": "execute-plan-thread"}}
        sup_out = supervisor_compiled.invoke(sup_state, config=config)

    sup_msgs = sup_out.get("messages", [])
    if sup_msgs:
        # LangGraph messages are objects with .content attribute
        last_msg = sup_msgs[-1]
        sup_text = getattr(last_msg, "content", "")
    else:
        sup_text = ""
    log.info("Supervisor plan text: %s", sup_text[:400])

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

    for step in plan.plan:
        if step.agent not in agents_map:
            raise RuntimeError(
                f"Plan step references unknown agent '{step.agent}'"
            )

    ordered_steps = topo_sort_steps(plan.plan)

    step_results: Dict[str, Dict[str, Any]] = {}
    global_attempts = 0

    def summarize_results() -> str:
        parts = []
        for sid, info in step_results.items():
            parts.append(
                f"{sid}: {info.get('output_summary', '(no output)')}"
            )
        return "\n".join(parts)

    for step in ordered_steps:
        attempts = 0
        last_err = None
        while True:
            attempts += 1
            global_attempts += 1
            system_context = (
                "Business context:\n"
                f"{business_context}\n\n"
                f"Previous step results:\n{summarize_results()}"
            )
            user_task = step.task
            worker_compiled = agents_map[step.agent]
            worker_state = {
                "messages": [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_task},
                ]
            }

            try:
                worker_config = {"configurable": {"thread_id": f"step-{step.id}"}}
                if step.timeout_seconds:
                    worker_out = await asyncio.wait_for(
                        worker_compiled.ainvoke(worker_state, config=worker_config),
                        timeout=step.timeout_seconds,
                    )
                else:
                    worker_out = await worker_compiled.ainvoke(worker_state, config=worker_config)
            except AttributeError:
                worker_config = {"configurable": {"thread_id": f"step-{step.id}"}}
                worker_out = worker_compiled.invoke(worker_state, config=worker_config)
            except asyncio.TimeoutError:
                last_err = "timeout"
                log.warning("Step %s timed out", step.id)
                worker_out = {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": (
                                f"ERROR: timeout after {step.timeout_seconds}s"
                            ),
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
            else:
                wtext = ""
            summary = (wtext[:400] + "...") if len(wtext) > 400 else wtext

            step_results[step.id] = {
                "agent": step.agent,
                "task": step.task,
                "attempts": attempts,
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
                check_prompt = (
                    f"Verification instruction: {step.verify}\n"
                    f"Step output: {wtext}\n"
                    "Return JSON: {\"ok\": true/false, \"reason\":\"...\"}"
                )
                ok, reason = await llm_verify(
                    check_prompt, default_model_for_verifier
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
                if attempts <= (step.retry or 0):
                    log.info(
                        "Retrying step %s (attempt %d/%d)",
                        step.id,
                        attempts,
                        (step.retry or 0),
                    )
                    continue
                if global_attempts >= max_total_retries:
                    log.warning(
                        "Reached global retry limit (%d). Aborting plan "
                        "execution.",
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
                        "Plan execution aborted: step {sid} failed and "
                        "retries exhausted".format(sid=step.id)
                    )
                if human_in_loop:
                    return {
                        "plan": plan.dict(),
                        "steps": step_results,
                        "status": "paused_for_human",
                        "failed_step": step.id,
                    }
                raise RuntimeError(
                    "Step {sid} failed: last_error={err}, verify_failed={vf}, "
                    "reason={reason}".format(
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
    return {
        "plan": plan.dict(),
        "steps": step_results,
        "final_result": final_agg,
        "status": "completed",
    }
