from __future__ import annotations
import logging
from typing import Dict, Tuple, Optional

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .mcp_loader import load_mcp_tools, close_mcp_client
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


async def build_react_agent(agent_cfg: AgentConfig, default_model: str, checkpointer=MemorySaver()):

    model_id = agent_cfg.model or default_model
    servers_raw = {k: v.dict(exclude_none=True) for k, v in agent_cfg.mcp_servers.items()}

    mcp_client, tools = await load_mcp_tools(servers_raw)

    summary = _format_mcp_summary(servers_raw)
    prompt_filled = agent_cfg.prompt.replace("{{mcpservers}}", summary)

    agent = create_react_agent(
        model=model_id,
        tools=tools,
        prompt=prompt_filled,
        name=agent_cfg.name,
        version="v2",
    )
    compiled = agent.compile(checkpointer=checkpointer)
    log.info("Built agent %s with %d tools", agent_cfg.name, len(tools))
    return compiled, mcp_client
