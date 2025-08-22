from __future__ import annotations
import logging
from typing import Dict

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .mcp_loader import load_mcp_tools, build_http_tools
from .config import AgentConfig

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
    prompt_filled = agent_cfg.prompt.replace("{{mcpservers}}", summary)

    agent = create_react_agent(
        model=model_id,
        tools=tools,
        prompt=prompt_filled,
        name=agent_cfg.name,
        version="v2",
        checkpointer=checkpointer,
    )
    log.info("Agent prompt:\n%s", prompt_filled)
    log.info("Built agent %s with %d tools", agent_cfg.name, len(tools))
    return agent, mcp_client
