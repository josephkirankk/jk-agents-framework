from __future__ import annotations
import asyncio, logging
from typing import Any, Dict, List, Tuple, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools.base import BaseTool

log = logging.getLogger("mcp_loader")

class TimeoutTool(BaseTool):
    name: str
    description: Optional[str]

    def __init__(self, inner: BaseTool, timeout: float = 15.0, retries: int = 2):
        self._inner = inner
        self.name = getattr(inner, "name", getattr(inner, "tool_name", "unnamed_tool"))
        self.description = getattr(inner, "description", "")
        self._timeout = float(timeout)
        self._retries = int(retries)

    def _run(self, input: str):
        last_exc = None
        for attempt in range(self._retries):
            try:
                return self._inner.run(input)
            except Exception as e:
                last_exc = e
        raise last_exc

    async def _arun(self, input: str):
        last_exc = None
        for attempt in range(self._retries):
            try:
                if hasattr(self._inner, "arun"):
                    coro = self._inner.arun(input)
                else:
                    loop = asyncio.get_running_loop()
                    coro = loop.run_in_executor(None, self._inner.run, input)
                return await asyncio.wait_for(coro, timeout=self._timeout)
            except Exception as e:
                last_exc = e
        raise last_exc

async def load_mcp_tools(servers_cfg: Dict[str, Any], tool_timeout: float = 15.0, tool_retries: int = 2) -> Tuple[Optional[MultiServerMCPClient], List[BaseTool]]:
    if not servers_cfg:
        return None, []

    client_cfg: Dict[str, Any] = {}
    for name, spec in servers_cfg.items():
        transport = spec.get("transport", "stdio")
        if transport == "stdio":
            if "command" not in spec:
                raise ValueError(f"stdio MCP server '{name}' requires 'command'")
            client_cfg[name] = {
                "transport": "stdio",
                "command": spec["command"],
                "args": spec.get("args", []),
                "env": spec.get("env", {}),
            }
        elif transport in ("sse", "streamable_http", "http"):
            if "url" not in spec:
                raise ValueError(f"{transport} MCP server '{name}' requires 'url'")
            client_cfg[name] = {
                "transport": transport,
                "url": spec["url"],
                "headers": spec.get("headers", {}),
            }
        else:
            raise ValueError(f"Unsupported transport '{transport}' for MCP server '{name}'")

    mcp_client = MultiServerMCPClient(client_cfg)
    tools = await mcp_client.get_tools()

    if isinstance(tools, dict):
        flat = []
        for arr in tools.values():
            flat.extend(arr)
        tools = flat
    elif not isinstance(tools, (list, tuple)):
        raise RuntimeError(f"Unexpected get_tools() return type: {type(tools)}")


    wrapped: List[BaseTool] = []
    bad = []
    for t in tools:
        if not (hasattr(t, "name") and (callable(getattr(t, "run", None)) or callable(getattr(t, "arun", None)))):
            bad.append(type(t).__name__)
            continue
        wrapped.append(TimeoutTool(t, timeout=tool_timeout, retries=tool_retries))
    if bad:
        raise RuntimeError(f"get_tools() returned unexpected objects: {set(bad)}")

    log_names = ", ".join([getattr(t, "name", "<unknown>") for t in wrapped])
    log.info("Loaded and wrapped %d tools from MCP servers: %s", len(wrapped), log_names)
    return mcp_client, list(wrapped)

async def close_mcp_client(mcp_client: Optional[MultiServerMCPClient]):
    if not mcp_client:
        return
    aclose = getattr(mcp_client, "aclose", None)
    if callable(aclose):
        maybe = aclose()
        if asyncio.iscoroutine(maybe):
            await maybe
        return
    close = getattr(mcp_client, "close", None)
    if callable(close):
        maybe = close()
        if asyncio.iscoroutine(maybe):
            await maybe
        return
