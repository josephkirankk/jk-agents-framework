from __future__ import annotations
import asyncio, logging, json
from typing import Any, Dict, List, Tuple, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools.base import BaseTool
from langchain.tools import Tool
import aiohttp
import requests

log = logging.getLogger("mcp_loader")

class TimeoutTool(BaseTool):
    name: str = "timeout_wrapper"
    description: str = ""

    def __init__(
        self,
        inner: BaseTool,
        timeout: float = 15.0,
        retries: int = 2,
        **kwargs,
    ):
        tool_name = getattr(
            inner, "name", getattr(inner, "tool_name", "unnamed_tool")
        )
        tool_desc = getattr(inner, "description", "")
        
        super().__init__(
            name=tool_name,
            description=tool_desc,
            **kwargs
        )
        
        self._inner = inner
        self._timeout = float(timeout)
        self._retries = int(retries)

    def _run(self, input: str):
        last_exc: Optional[BaseException] = None
        for attempt in range(self._retries):
            try:
                return self._inner.run(input)
            except Exception as e:
                last_exc = e
        raise last_exc or RuntimeError("Inner tool failed with unknown error")

    async def _arun(self, input: str):
        last_exc: Optional[BaseException] = None
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
        raise last_exc or RuntimeError("Inner tool failed with unknown error")

async def load_mcp_tools(
    servers_cfg: Dict[str, Any],
    tool_timeout: float = 15.0,
    tool_retries: int = 2,
) -> Tuple[Optional[MultiServerMCPClient], List[BaseTool]]:
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
            raise ValueError(
                f"Unsupported transport '{transport}' for MCP server '{name}'"
            )

    mcp_client = MultiServerMCPClient(client_cfg)
    tools = await mcp_client.get_tools()

    if isinstance(tools, dict):
        flat = []
        for arr in tools.values():
            flat.extend(arr)
        tools = flat
    elif not isinstance(tools, (list, tuple)):
        raise RuntimeError(
            f"Unexpected get_tools() return type: {type(tools)}"
        )


    wrapped: List[BaseTool] = []
    bad = []
    for t in tools:
        if not (
            hasattr(t, "name")
            and (
                callable(getattr(t, "run", None))
                or callable(getattr(t, "arun", None))
            )
        ):
            bad.append(type(t).__name__)
            continue
        # Use tools directly without wrapping for now to avoid Pydantic issues
        wrapped.append(t)
    if bad:
        raise RuntimeError(f"get_tools() returned unexpected objects: {set(bad)}")

    log_names = ", ".join([getattr(t, "name", "<unknown>") for t in wrapped])
    log.info(
        "Loaded %d tools from MCP servers: %s", len(wrapped), log_names
    )
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


def build_http_tools(http_tools_cfg: Dict[str, Any]) -> List[BaseTool]:
    """Create simple HTTP-based LangChain tools from config.

    Schema per tool (example):
      weather:
        description: "Get weather for a city"
        method: GET
        url: http://localhost:8002/weather
        params:
          - name: city
            in: query
            description: City name
        response_path: result  # optional JSONPath-like dot path to extract
        headers:
          X-API-Key: ...

      math_calc:
        description: "Calculate arithmetic expression"
        method: GET
        url: http://localhost:8001/calculate
        params:
          - name: expression
            in: query

    The generated tool will accept a JSON string of parameters or a raw
    string if there's a single query param named 'q' or 'expression'.
    """
    built: List[BaseTool] = []

    for name, spec in (http_tools_cfg or {}).items():
        method = (spec.get("method") or "GET").upper()
        url = spec.get("url")
        if not url:
            log.warning("Skipping http_tool '%s' without url", name)
            continue
        desc = spec.get("description", f"HTTP tool calling {url}")
        headers = spec.get("headers", {})
        params_schema = spec.get("params", [])
        response_path = spec.get("response_path")

        single_param = None
        if isinstance(params_schema, list) and len(params_schema) == 1:
            single_param = params_schema[0].get("name")

        async def _http_async(input: str, _method=method, _url=url, _headers=headers, _params_schema=params_schema, _response_path=response_path, _single_param=single_param):
            """Async HTTP call implementation."""
            payload: Dict[str, Any] = {}
            if input:
                try:
                    payload = json.loads(input) if isinstance(input, str) else input
                except Exception:
                    if _single_param:
                        payload = {_single_param: input}
                    else:
                        payload = {"q": input}

            query: Dict[str, Any] = {}
            body: Optional[Dict[str, Any]] = None
            for p in _params_schema or []:
                pname = p.get("name")
                where = p.get("in", "query")
                if pname in payload:
                    if where == "query":
                        query[pname] = payload[pname]
                    else:
                        if body is None:
                            body = {}
                        body[pname] = payload[pname]

            async with aiohttp.ClientSession() as session:
                if _method == "GET":
                    resp = await session.get(_url, params=query, headers=_headers)
                elif _method == "POST":
                    resp = await session.post(_url, params=query, json=body, headers=_headers)
                else:
                    resp = await session.request(_method, _url, params=query, json=body, headers=_headers)
                async with resp:
                    txt = await resp.text()
            try:
                data = json.loads(txt)
            except Exception:
                return txt
            if _response_path:
                cur = data
                for part in _response_path.split('.'):
                    if isinstance(cur, dict) and part in cur:
                        cur = cur[part]
                    else:
                        break
                return json.dumps(cur)
            return json.dumps(data)

        def _http_sync(input: str, _method=method, _url=url, _headers=headers, _params_schema=params_schema, _response_path=response_path, _single_param=single_param):
            """Sync HTTP call implementation for tool.run."""
            payload: Dict[str, Any] = {}
            if input:
                try:
                    payload = json.loads(input) if isinstance(input, str) else input
                except Exception:
                    if _single_param:
                        payload = {_single_param: input}
                    else:
                        payload = {"q": input}

            query: Dict[str, Any] = {}
            body: Optional[Dict[str, Any]] = None
            for p in _params_schema or []:
                pname = p.get("name")
                where = p.get("in", "query")
                if pname in payload:
                    if where == "query":
                        query[pname] = payload[pname]
                    else:
                        if body is None:
                            body = {}
                        body[pname] = payload[pname]

            if _method == "GET":
                r = requests.get(_url, params=query, headers=_headers, timeout=15)
            elif _method == "POST":
                r = requests.post(_url, params=query, json=body, headers=_headers, timeout=15)
            else:
                r = requests.request(_method, _url, params=query, json=body, headers=_headers, timeout=15)
            txt = r.text
            try:
                data = json.loads(txt)
            except Exception:
                return txt
            if _response_path:
                cur = data
                for part in _response_path.split('.'):
                    if isinstance(cur, dict) and part in cur:
                        cur = cur[part]
                    else:
                        break
                return json.dumps(cur)
            return json.dumps(data)

        built.append(
            Tool(
                name=name,
                description=desc,
                func=_http_sync,
                coroutine=_http_async,
            )
        )

    return built
