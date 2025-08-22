from __future__ import annotations
import logging
from typing import List

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from .config import SupervisorConfig, AgentConfig

log = logging.getLogger("supervisor_builder")


def _format_agents_listing(agents: List[AgentConfig]) -> str:
    lines = []
    for a in agents:
        lines.append(f"- {a.name}: {a.description or '(no description)'}")
    return "\n".join(lines)


def build_supervisor_compiled(supervisor_cfg: SupervisorConfig, agents_cfg: List[AgentConfig], default_model: str, business_context: str = "", checkpointer=MemorySaver()):
    agents_list = _format_agents_listing(agents_cfg)
    prompt_filled = supervisor_cfg.prompt.replace("{{agents}}", agents_list)
    prompt_filled = prompt_filled.replace("{{business_context}}", business_context)

    supervisor_model = supervisor_cfg.model or default_model

    sup_agent = create_react_agent(
        model=supervisor_model,
        tools=[],
        prompt=(
            prompt_filled.strip()
            + "\n\nIMPORTANT: Return the agent routing decision as a JSON object only, with keys: agent, task, reason. Example:\n"
            + '{"agent":"math_agent","task":"Compute 19*37","reason":"explicit arithmetic request"}\n'
            + "Respond with JSON only and nothing else."
        ),
        name="supervisor",
        version="v2",
    )
    compiled = sup_agent.compile(checkpointer=checkpointer)
    log.info("Supervisor compiled (model=%s)", supervisor_model)
    return compiled
