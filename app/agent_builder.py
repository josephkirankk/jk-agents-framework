from __future__ import annotations
import logging
from typing import Dict

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .mcp_loader import load_mcp_tools, build_http_tools
from .config import AgentConfig
from .template_utils import render_prompt

log = logging.getLogger("agent_builder")


def _format_mcp_summary(servers_cfg: Dict[str, Dict]) -> str:
    if not servers_cfg:
        return "(no MCP servers configured)"
    lines = []
    for sid, s in servers_cfg.items():
        desc = s.get("description", "")
        transport = s.get("transport", "")
        if transport == "stdio":
            location = f"command: {s.get('command')}"
        else:
            location = f"url: {s.get('url')}"
        lines.append(f"- {sid}: {desc} (transport={transport}, {location})")
    return "\n".join(lines)


async def build_react_agent(
    agent_cfg: AgentConfig,
    default_model: str,
    checkpointer=MemorySaver(),
    *,
    business_context: str = "",
    original_user_question: str = "",
    dependent_request_responses: str = "",
):

    model_id = agent_cfg.model or default_model
    servers_raw = {
        k: v.dict(exclude_none=True)
        for k, v in agent_cfg.mcp_servers.items()
    }

    mcp_client, tools = await load_mcp_tools(servers_raw)
    # Merge in HTTP tools (non-MCP) if configured
    try:
        http_tools = build_http_tools(agent_cfg.http_tools)
    except Exception as e:
        log.exception(
            "Failed building HTTP tools for agent %s: %s",
            agent_cfg.name,
            e,
        )
        http_tools = []
    tools = list(tools) + list(http_tools)

    summary = _format_mcp_summary(servers_raw)
    # Render prompt with Jinja2 so templates can use variables like
    # {{ mcpservers }}, {{ businessContext }}, {{ original_user_question }}, {{ agent_name }}, {{ dependent_request_responses }}
    ctx = {
        "mcpservers": summary,
        "businessContext": business_context or "",
        "original_user_question": original_user_question or "",
        "agent_name": agent_cfg.name,
        "dependent_request_responses": dependent_request_responses or "",
    }
    try:
        prompt_filled = render_prompt(agent_cfg.prompt or "", ctx)
    except Exception as e:
        log.exception(
            "Failed to render prompt for agent %s with Jinja2: %s. Falling back to raw prompt.",
            agent_cfg.name,
            e,
        )
        # Fallback to simple replacement for mcpservers
        prompt_filled = (agent_cfg.prompt or "").replace("{{mcpservers}}", summary)

    agent = create_react_agent(
        model=model_id,
        tools=tools,
        prompt=prompt_filled,
        name=agent_cfg.name,
        version="v2",
        checkpointer=checkpointer,
    )
    # Attach model identifier for downstream logging without changing APIs
    try:
        setattr(agent, "_model_id", model_id)
        setattr(agent, "_rendered_prompt", prompt_filled)
    except Exception:
        pass
    log.info("Agent prompt:\n%s", prompt_filled)
    log.info("Built agent %s with %d tools", agent_cfg.name, len(tools))
    return agent, mcp_client
