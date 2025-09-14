from __future__ import annotations
import logging
from typing import List, Optional
from pathlib import Path

from langgraph.prebuilt import create_react_agent
from .checkpointer_manager import get_global_checkpointer
from .config import SupervisorConfig, AgentConfig
from .template_utils import render_prompt
from .agent_builder import create_model_instance
from .prompt_loader import load_prompt_content, get_config_directory

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
    checkpointer=None,
    *,
    original_user_question: str = "",
    config_path: Optional[str] = None,
):
    # Use global checkpointer for memory persistence across API calls
    if checkpointer is None:
        checkpointer = get_global_checkpointer()
        log.info("Using global checkpointer for supervisor")

    agents_list = _format_agents_listing(agents_cfg)

    # Load prompt content from either direct text or file
    try:
        config_dir = get_config_directory(
            Path(config_path) if config_path else None
        )
        prompt_content = load_prompt_content(
            prompt=supervisor_cfg.prompt,
            prompt_file=supervisor_cfg.prompt_file,
            config_dir=config_dir,
        )
    except Exception as e:
        log.error(
            "Failed to load prompt for supervisor: %s",
            e,
        )
        raise

    # Render with Jinja2 so templates can use:
    # {{ agents }}, {{ business_context }}, {{ original_user_question }}
    ctx = {
        "agents": agents_list,
        "business_context": business_context or "",
        "original_user_question": original_user_question or "",
    }
    try:
        prompt_filled = render_prompt(prompt_content, ctx)
    except Exception:
        # Fall back to simple replacements
        prompt_filled = prompt_content.replace("{{agents}}", agents_list)
        prompt_filled = prompt_filled.replace(
            "{{business_context}}", business_context
        )

    supervisor_model = supervisor_cfg.model or default_model
    # Create the appropriate model instance (handles google: prefix)
    supervisor_model_instance = create_model_instance(supervisor_model)

    sup_agent = create_react_agent(
        model=supervisor_model_instance,
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
