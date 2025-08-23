from __future__ import annotations
import logging
from typing import List

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from .config import SupervisorConfig, AgentConfig
from .template_utils import render_prompt

log = logging.getLogger("supervisor_builder")


def _format_agents_listing(agents: List[AgentConfig]) -> str:
    lines = []
    for a in agents:
        lines.append(f"- {a.name}: {a.description or '(no description)'}")
    return "\n".join(lines)


def build_supervisor_compiled(
    supervisor_cfg: SupervisorConfig,
    agents_cfg: List[AgentConfig],
    default_model: str,
    business_context: str = "",
    checkpointer=MemorySaver(),
    *,
    original_user_question: str = "",
):
    agents_list = _format_agents_listing(agents_cfg)
    # Render with Jinja2 so templates can use:
    # {{ agents }}, {{ business_context }}, {{ original_user_question }}
    ctx = {
        "agents": agents_list,
        "business_context": business_context or "",
        "original_user_question": original_user_question or "",
    }
    try:
        prompt_filled = render_prompt(supervisor_cfg.prompt or "", ctx)
    except Exception:
        # Fall back to simple replacements
        prompt_filled = (supervisor_cfg.prompt or "").replace("{{agents}}", agents_list)
        prompt_filled = prompt_filled.replace("{{business_context}}", business_context)

    supervisor_model = supervisor_cfg.model or default_model

    sup_agent = create_react_agent(
        model=supervisor_model,
        tools=[],
        prompt=prompt_filled.strip(),
        name="supervisor",
        version="v2",
        checkpointer=checkpointer,
    )
    # Attach model identifier for downstream logging without changing APIs
    try:
        setattr(sup_agent, "_model_id", supervisor_model)
        setattr(sup_agent, "_rendered_prompt", prompt_filled.strip())
    except Exception:
        pass
    # Print/log the exact planning prompt used
    try:
        full_prompt = prompt_filled.strip()
        log.info(
            "Supervisor planning prompt (model=%s):\n%s",
            supervisor_model,
            full_prompt,
        )
        print(
            "Supervisor planning prompt (model="
            + str(supervisor_model)
            + "):\n"
            + full_prompt
        )
    except Exception as e:
        log.warning("Failed to print supervisor planning prompt: %s", e)

    log.info("Supervisor compiled (model=%s)", supervisor_model)
    return sup_agent
