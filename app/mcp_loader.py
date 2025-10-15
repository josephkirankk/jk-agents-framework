from __future__ import annotations
import asyncio
import logging
import json
import os
import re
import time
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
        retries: int = 0,
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
        # Propagate structured args schema and return behavior so callers
        # know how to format inputs and handle outputs.
        try:
            self.args_schema = getattr(inner, "args_schema", None)
        except Exception:
            # Some tools may raise on access; ignore.
            self.args_schema = None
        try:
            self.return_direct = bool(getattr(inner, "return_direct", False))
        except Exception:
            self.return_direct = False

    def _run(self, *args: Any, **kwargs: Any):
        last_exc: Optional[BaseException] = None
        for attempt in range(self._retries):
            try:
                # Prefer structured kwargs if provided
                payload: Any
                if kwargs:
                    payload = dict(kwargs)
                elif args:
                    payload = args[0]
                else:
                    # For functions with empty parameter schemas, use empty dict instead of None
                    try:
                        inner_schema = getattr(self._inner, "args_schema", None)
                        if inner_schema is not None:
                            payload = {}
                        else:
                            # Always use empty dict instead of None
                            payload = {}
                    except Exception:
                        payload = {}
                # If the inner tool expects structured args (args_schema), but
                # got a string, coerce to a dict so inner BaseTool doesn't
                # fail.
                try:
                    inner_schema = getattr(self._inner, "args_schema", None)
                except Exception:
                    inner_schema = None
                if inner_schema is not None and isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        # Common generic key for text-like inputs
                        payload = {"query": payload}

                # Filter out empty arrays and empty strings to avoid backend API issues
                if isinstance(payload, dict):
                    filtered_payload = {}
                    for key, value in payload.items():
                        if isinstance(value, list) and len(value) == 0:
                            continue  # Skip empty arrays
                        if isinstance(value, str) and value == "":
                            continue  # Skip empty strings
                        filtered_payload[key] = value
                    payload = filtered_payload

                return self._inner.run(payload)
            except Exception as e:
                last_exc = e
        raise last_exc or RuntimeError("Inner tool failed with unknown error")

    async def _arun(self, *args: Any, **kwargs: Any):
        last_exc: Optional[BaseException] = None
        for attempt in range(self._retries + 1):
            try:
                # Prefer structured kwargs if provided
                payload: Any
                if kwargs:
                    payload = dict(kwargs)
                elif args:
                    payload = args[0]
                else:
                    # For functions with empty parameter schemas, use empty dict instead of None
                    try:
                        inner_schema = getattr(self._inner, "args_schema", None)
                        if inner_schema is not None:
                            payload = {}
                        else:
                            # Always use empty dict instead of None
                            payload = {}
                    except Exception:
                        payload = {}
                try:
                    inner_schema = getattr(self._inner, "args_schema", None)
                except Exception:
                    inner_schema = None
                if inner_schema is not None and isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except Exception:
                        payload = {"query": payload}

                # Filter out empty arrays and empty strings to avoid backend API issues
                if isinstance(payload, dict):
                    filtered_payload = {}
                    for key, value in payload.items():
                        if isinstance(value, list) and len(value) == 0:
                            continue  # Skip empty arrays
                        if isinstance(value, str) and value == "":
                            continue  # Skip empty strings
                        filtered_payload[key] = value
                    payload = filtered_payload

                if hasattr(self._inner, "arun"):
                    coro = self._inner.arun(payload)
                else:
                    loop = asyncio.get_running_loop()
                    coro = loop.run_in_executor(None, self._inner.run, payload)
                result = await asyncio.wait_for(coro, timeout=self._timeout)
                log.debug(
                    f"Tool {self._inner.name} succeeded on "
                    f"attempt {attempt + 1}"
                )
                return result
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                # Categorize common error patterns for better user experience
                if "parameter" in error_msg.lower() and ("conflict" in error_msg.lower() or "cannot" in error_msg.lower()):
                    log.error(
                        f"Tool {self._inner.name} failed due to parameter conflict on "
                        f"attempt {attempt + 1}: {error_msg}"
                    )
                elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    log.error(
                        f"Tool {self._inner.name} failed due to authentication issue on "
                        f"attempt {attempt + 1}: {error_type}: {error_msg}"
                    )
                elif "permission" in error_msg.lower() or "access denied" in error_msg.lower():
                    log.error(
                        f"Tool {self._inner.name} failed due to permission issue on "
                        f"attempt {attempt + 1}: {error_type}: {error_msg}"
                    )
                elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    log.error(
                        f"Tool {self._inner.name} failed due to connectivity issue on "
                        f"attempt {attempt + 1}: {error_type}: {error_msg}"
                    )
                else:
                    log.error(
                        f"Tool {self._inner.name} failed on "
                        f"attempt {attempt + 1}: {error_type}: {error_msg}"
                    )
                
                # Only show full traceback on debug level to avoid clutter
                if log.isEnabledFor(logging.DEBUG):
                    import traceback
                    log.debug(f"Full traceback: {traceback.format_exc()}")
                
                last_exc = e
        log.error(
            f"Tool {self._inner.name} failed after {self._retries + 1} "
            f"attempts. Last error: {last_exc}"
        )
        raise last_exc or RuntimeError("Inner tool failed with unknown error")

 
def _expand_env_vars(env_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Expand environment variables in format ${VAR_NAME} or $VAR_NAME.
    Also handles direct environment variable references.
    """
    expanded = {}
    for key, value in env_dict.items():
        if not isinstance(value, str):
            expanded[key] = value
            continue
            
        # Handle ${VAR} format
        def replace_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        
        # Replace ${VAR} patterns
        expanded_value = re.sub(r'\$\{([^}]+)\}', replace_var, value)
        
        # Replace $VAR patterns (word boundary)
        expanded_value = re.sub(r'\$(\w+)', lambda m: os.getenv(m.group(1), m.group(0)), expanded_value)
        
        expanded[key] = expanded_value
        
        # Log if variable was expanded (helpful for debugging)
        if expanded_value != value:
            log.debug(f"Expanded env var {key}: {value} -> {expanded_value[:20]}...")
    
    return expanded


async def load_mcp_tools(
    servers_cfg: Dict[str, Any],
    tool_timeout: float = 60.0,
    tool_retries: int = 1,
) -> Tuple[Optional[MultiServerMCPClient], List[BaseTool]]:
    if not servers_cfg:
        return None, []

    client_cfg: Dict[str, Any] = {}
    for name, spec in servers_cfg.items():
        # Convert Pydantic model to dict if needed
        if hasattr(spec, 'model_dump'):
            spec = spec.model_dump()
        elif hasattr(spec, 'dict'):
            spec = spec.dict()
        
        transport = spec.get("transport", "stdio")
        if transport == "stdio":
            if "command" not in spec:
                raise ValueError(
                    f"stdio MCP server '{name}' requires 'command'"
                )
            
            # Expand environment variables in env dict
            raw_env = spec.get("env", {})
            expanded_env = _expand_env_vars(raw_env)
            
            # CRITICAL: Merge with current process environment
            # The MCP subprocess needs to inherit parent environment variables
            # Otherwise it won't have access to system PATH, Python paths, etc.
            merged_env = os.environ.copy()
            merged_env.update(expanded_env)
            # ROBUSTNESS FIX: Ensure ADO PAT is always passed if available in parent env
            # This prevents race conditions where the .env is loaded before this runs.
            if name == "azure_devops" and "AZURE_DEVOPS_EXT_PAT" in os.environ:
                ado_pat = os.getenv("AZURE_DEVOPS_EXT_PAT")
                if ado_pat and ado_pat != merged_env.get("AZURE_DEVOPS_EXT_PAT"):
                    log.info("Injecting AZURE_DEVOPS_EXT_PAT from parent environment into ADO MCP server.")
                    merged_env["AZURE_DEVOPS_EXT_PAT"] = ado_pat
            
            # Log environment for debugging (hide sensitive values)
            log.info(f"MCP server '{name}' environment variables being set:")
            for key in expanded_env.keys():
                value = expanded_env[key]
                masked_value = value[:10] + "..." if len(value) > 10 else value
                log.info(f"  {key}: {masked_value}")
            
            # Special check for Azure DevOps PAT token - verify it's actually set
            pat_from_expanded = expanded_env.get("AZURE_DEVOPS_EXT_PAT")
            pat_from_merged = merged_env.get("AZURE_DEVOPS_EXT_PAT")
            pat_from_os = os.getenv("AZURE_DEVOPS_EXT_PAT")
            
            log.info(f"🔍 Azure DevOps PAT token debug:")
            log.info(f"  - In expanded_env: {bool(pat_from_expanded)} (len: {len(pat_from_expanded) if pat_from_expanded else 0})")
            log.info(f"  - In merged_env: {bool(pat_from_merged)} (len: {len(pat_from_merged) if pat_from_merged else 0})")
            log.info(f"  - In os.environ: {bool(pat_from_os)} (len: {len(pat_from_os) if pat_from_os else 0})")
            
            if not pat_from_merged:
                log.error("⚠ AZURE_DEVOPS_EXT_PAT is NOT set in merged_env! MCP server will fail authentication!")
            else:
                log.info(f"✓ AZURE_DEVOPS_EXT_PAT will be passed to MCP server subprocess")
            
            client_cfg[name] = {
                "transport": "stdio",
                "command": spec["command"],
                "args": spec.get("args", []),
                "env": merged_env,  # Use merged environment
            }
        elif transport in ("sse", "streamable_http", "http"):
            if "url" not in spec:
                raise ValueError(
                    f"{transport} MCP server '{name}' requires 'url'"
                )
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
    # Wrap with timeout/retry so a single tool call
    # can't stall the step
        try:
            wrapped.append(
                TimeoutTool(
                    inner=t,
                    timeout=float(tool_timeout),
                    retries=int(tool_retries),
                )
            )
        except Exception:
            # If wrapping fails for any reason, fall back to the raw tool
            wrapped.append(t)
    if bad:
        raise RuntimeError(
            f"get_tools() returned unexpected objects: {set(bad)}"
        )

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

        async def _http_async(
            input: str,
            _method=method,
            _url=url,
            _headers=headers,
            _params_schema=params_schema,
            _response_path=response_path,
            _single_param=single_param,
        ):
            """Async HTTP call implementation."""
            payload: Dict[str, Any] = {}
            if input:
                try:
                    payload = (
                        json.loads(input)
                        if isinstance(input, str)
                        else input
                    )
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
                    value = payload[pname]
                    # Skip empty arrays and empty strings to avoid backend API issues
                    if (isinstance(value, list) and len(value) == 0) or (isinstance(value, str) and value == ""):
                        continue
                    if where == "query":
                        query[pname] = value
                    else:
                        if body is None:
                            body = {}
                        body[pname] = value

            timeout = aiohttp.ClientTimeout(
                total=20,
                connect=5,
                sock_read=15,
                sock_connect=5,
            )
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if _method == "GET":
                        resp = await session.get(
                            _url, params=query, headers=_headers
                        )
                    elif _method == "POST":
                        resp = await session.post(
                            _url, params=query, json=body, headers=_headers
                        )
                    else:
                        resp = await session.request(
                            _method,
                            _url,
                            params=query,
                            json=body,
                            headers=_headers,
                        )
                    async with resp:
                        txt = await resp.text()

                        # Check HTTP status code for errors
                        if resp.status >= 400:
                            return json.dumps({
                                "method": _method,
                                "timestamp": int(time.time() * 1000),
                                "body": body,
                                "baseUrl": _url.split('/api')[0] if '/api' in _url else _url,
                                "path": '/api' + _url.split('/api')[1] if '/api' in _url else _url,
                                "error": f"{resp.status} {resp.reason} from {_method} {_url}",
                                "response_body": txt[:500] + "..." if len(txt) > 500 else txt,
                                "hint": "Check backend API logs for detailed error information"
                            })

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                return json.dumps({
                    "error": "http_request_failed",
                    "message": str(e),
                    "url": _url,
                    "hint": (
                        "Ensure the service is running (e.g., python "
                        "examples/mcp_servers/math_server.py)"
                    ),
                })
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

        def _http_sync(
            input: str,
            _method=method,
            _url=url,
            _headers=headers,
            _params_schema=params_schema,
            _response_path=response_path,
            _single_param=single_param,
        ):
            """Sync HTTP call implementation for tool.run."""
            payload: Dict[str, Any] = {}
            if input:
                try:
                    payload = (
                        json.loads(input)
                        if isinstance(input, str)
                        else input
                    )
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
                    value = payload[pname]
                    # Skip empty arrays and empty strings to avoid backend API issues
                    if (isinstance(value, list) and len(value) == 0) or (isinstance(value, str) and value == ""):
                        continue
                    if where == "query":
                        query[pname] = value
                    else:
                        if body is None:
                            body = {}
                        body[pname] = value

            try:
                if _method == "GET":
                    r = requests.get(
                        _url, params=query, headers=_headers, timeout=15
                    )
                elif _method == "POST":
                    r = requests.post(
                        _url,
                        params=query,
                        json=body,
                        headers=_headers,
                        timeout=15,
                    )
                else:
                    r = requests.request(
                        _method,
                        _url,
                        params=query,
                        json=body,
                        headers=_headers,
                        timeout=15,
                    )
                txt = r.text

                # Check HTTP status code for errors
                if r.status_code >= 400:
                    return json.dumps({
                        "method": _method,
                        "timestamp": int(time.time() * 1000),
                        "body": body,
                        "baseUrl": _url.split('/api')[0] if '/api' in _url else _url,
                        "path": '/api' + _url.split('/api')[1] if '/api' in _url else _url,
                        "error": f"{r.status_code} {r.reason} from {_method} {_url}",
                        "response_body": txt[:500] + "..." if len(txt) > 500 else txt,
                        "hint": "Check backend API logs for detailed error information"
                    })

            except requests.exceptions.RequestException as e:
                return json.dumps({
                    "error": "http_request_failed",
                    "message": str(e),
                    "url": _url,
                    "hint": (
                        "Ensure the service is running (e.g., python "
                        "examples/mcp_servers/math_server.py)"
                    ),
                })
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
