from __future__ import annotations
import asyncio
import logging
import json
import os
import re
import time
import sys
import traceback
from typing import Any, Dict, List, Tuple, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool, Tool
import aiohttp
import requests

log = logging.getLogger("mcp_loader")

# Import MCP-specific exceptions for better error handling
try:
    from mcp.shared.exceptions import McpError
    MCP_ERROR_AVAILABLE = True
except ImportError:
    McpError = Exception
    MCP_ERROR_AVAILABLE = False
    log.warning("MCP exceptions not available, using generic Exception")


def _extract_exception_details(exc: Exception) -> tuple[str, str, str]:
    """
    Extract detailed information from an exception, including ExceptionGroup.
    
    Returns:
        Tuple of (error_type, error_message, traceback_str)
    """
    error_type = type(exc).__name__
    error_msg = str(exc)
    
    # Handle ExceptionGroup (Python 3.11+)
    if hasattr(exc, '__cause__') and exc.__cause__:
        cause = exc.__cause__
        error_type = f"{error_type} (caused by {type(cause).__name__})"
        error_msg = f"{error_msg} | Cause: {str(cause)}"
    
    # Try to extract from ExceptionGroup
    if sys.version_info >= (3, 11):
        try:
            from builtins import ExceptionGroup as BuiltinExceptionGroup
            if isinstance(exc, BuiltinExceptionGroup):
                # Extract first exception from the group
                if exc.exceptions:
                    first_exc = exc.exceptions[0]
                    error_type = type(first_exc).__name__
                    error_msg = str(first_exc)
                    # Get full traceback of the inner exception
                    tb_str = ''.join(traceback.format_exception(type(first_exc), first_exc, first_exc.__traceback__))
                    return error_type, error_msg, tb_str
        except (ImportError, AttributeError):
            pass
    
    # Fallback: get traceback from current exception
    tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    return error_type, error_msg, tb_str


class SerperToolWrapper(BaseTool):
    """
    Wrapper for Serper MCP tools (google_search, scrape) that injects default parameters.
    
    The Serper API requires certain parameters that LLMs might not always provide:
    - google_search: requires query, gl (region), hl (language)
    - scrape: requires url
    """
    name: str = "serper_wrapper"
    description: str = ""
    
    def __init__(self, inner: BaseTool, **kwargs):
        super().__init__(**kwargs)
        self._inner = inner
        self.name = getattr(inner, "name", "unknown_tool")
        self.description = getattr(inner, "description", "")
        
        # Determine default region and language
        self._default_gl = "us"  # Default region code (can be overridden)
        self._default_hl = "en"  # Default language (can be overridden)
    
    def _inject_defaults(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inject default parameters for Serper tools."""
        # For google_search tool
        if self.name == "google_search":
            # CRITICAL: Serper MCP server expects 'q' not 'query'
            # Convert 'query' to 'q' for compatibility
            if "query" in params and "q" not in params:
                query_value = params.pop("query")
                # Filter out invalid values
                if query_value and str(query_value).strip() and str(query_value).lower() != "undefined":
                    params["q"] = query_value
            
            # CRITICAL FIX: Filter out 'undefined' and empty strings from 'q' parameter
            if "q" in params:
                q_value = params["q"]
                # Check if q is invalid (undefined, empty, or None)
                if not q_value or str(q_value).strip() == "" or str(q_value).lower() == "undefined":
                    log.error(f"google_search called with invalid 'q' parameter: {repr(q_value)}")
                    # Remove the invalid parameter
                    params.pop("q")
            
            # Ensure required parameters exist
            if "gl" not in params or not params.get("gl"):
                params["gl"] = self._default_gl
            if "hl" not in params or not params.get("hl"):
                params["hl"] = self._default_hl
            
            # Final validation: ensure we have a valid query
            if "q" not in params or not params.get("q"):
                error_msg = "google_search requires a valid 'q' or 'query' parameter. Cannot search with empty or 'undefined' query."
                log.error(error_msg)
                # Raise an error instead of proceeding with invalid parameters
                raise ValueError(error_msg)
        
        return params
    
    def _run(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError("Use async arun")
    
    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        """Async run with parameter injection.
        
        Args:
            *args: Tool parameters passed as positional argument (typically a dict)
            **kwargs: Tool parameters passed as keyword arguments (e.g., query="...", gl="...", hl="...")
        
        Returns:
            Tool execution result as string
        """
        # Extract parameters from either args or kwargs
        # Prefer kwargs if provided, otherwise use first positional arg
        if kwargs:
            params = dict(kwargs)
        elif args:
            # Handle different argument formats:
            # - args[0] is a dict: use it directly
            # - args[0] is a list containing a dict: unwrap it  
            # - args[0] is something else: convert to query param
            first_arg = args[0]
            if isinstance(first_arg, dict):
                params = first_arg
            elif isinstance(first_arg, list) and len(first_arg) > 0 and isinstance(first_arg[0], dict):
                # Handle args=[[{...}]] format
                params = first_arg[0]
            else:
                # CRITICAL FIX: Validate the string before using it as query
                arg_str = str(first_arg).strip()
                # Don't accept "undefined", "None", or empty strings
                if arg_str and arg_str.lower() not in ("undefined", "none", "null"):
                    params = {"query": arg_str}
                else:
                    log.warning(f"Received invalid string argument: {repr(first_arg)}. Treating as empty params.")
                    params = {}
        else:
            params = {}
        
        # Inject default parameters and convert 'query' to 'q' for Serper tools
        params = self._inject_defaults(params)
        
        # Call inner tool with parameters
        # BaseTool.arun() expects: arun(tool_input, **kwargs)
        # So we pass the entire params dict as the first positional argument
        if hasattr(self._inner, "arun") and callable(self._inner.arun):
            return await self._inner.arun(params)  # Pass params as positional arg
        elif hasattr(self._inner, "run") and callable(self._inner.run):
            return self._inner.run(params)  # Pass params as positional arg
        else:
            raise RuntimeError(f"Tool {self.name} has no run/arun method")


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
                # Extract detailed error information, handling ExceptionGroup
                error_type, error_msg, tb_str = _extract_exception_details(e)
                
                # Check if this is a known MCP error that should gracefully degrade
                is_scrape_failure = "scrape" in error_msg.lower() or "scraping failed" in error_msg.lower()
                is_mcp_server_error = "500" in error_msg or "Internal Server Error" in error_msg
                is_param_error = "required" in error_msg.lower() and ("parameter" in error_msg.lower() or "region" in error_msg.lower() or "language" in error_msg.lower())
                is_broken_resource = "BrokenResourceError" in error_type
                
                # For scrape failures with 500 errors, provide graceful degradation
                if is_scrape_failure and is_mcp_server_error and self._inner.name == "scrape":
                    log.warning(
                        f"Tool {self._inner.name} failed on attempt {attempt + 1} (non-fatal):\n"
                        f"  Error Type: {error_type}\n"
                        f"  Error Message: {error_msg}\n"
                        f"  Note: Scrape tool is experiencing issues. Agent can still use search results."
                    )
                    # Return a graceful error message instead of failing
                    if attempt >= self._retries:
                        return json.dumps({
                            "error": "scrape_unavailable",
                            "message": "Web scraping is temporarily unavailable. Using search results only.",
                            "suggestion": "The search tool can still provide relevant information."
                        })
                    last_exc = e
                    continue
                
                # Handle missing parameter errors for google_search
                if is_param_error and self._inner.name == "google_search":
                    log.error(
                        f"Tool {self._inner.name} failed on attempt {attempt + 1}:\n"
                        f"  Error Type: {error_type}\n"
                        f"  Error Message: {error_msg}\n"
                        f"  Issue: Missing required parameters (query, gl, hl)"
                    )
                    # Don't retry parameter errors - they won't succeed
                    raise ValueError(
                        f"google_search tool requires parameters: 'query' (search text), "
                        f"'gl' (region code like 'us' or 'in'), 'hl' (language like 'en'). "
                        f"Error: {error_msg}"
                    )
                
                # Handle BrokenResourceError (connection issues)
                if is_broken_resource:
                    log.warning(
                        f"Tool {self._inner.name} failed on attempt {attempt + 1}:\n"
                        f"  Error Type: {error_type} (MCP connection broken)\n"
                        f"  This usually happens after a previous error."
                    )
                    # Don't retry broken connections immediately
                    if attempt >= self._retries:
                        raise RuntimeError(
                            f"MCP connection broken for tool {self._inner.name}. "
                            f"This may be caused by a previous error. Check logs for root cause."
                        )
                    last_exc = e
                    continue
                
                # Log with detailed information for other errors
                log.error(
                    f"Tool {self._inner.name} failed on attempt {attempt + 1}:\n"
                    f"  Error Type: {error_type}\n"
                    f"  Error Message: {error_msg}"
                )
                
                # Log full traceback at DEBUG level to reduce noise
                log.debug(f"Full traceback for {self._inner.name}:\n{tb_str}")
                
                # Categorize common error patterns for user-friendly hints
                hint = None
                if is_param_error:
                    hint = "Missing required parameters - check tool schema and ensure all required fields are provided"
                elif "parameter" in error_msg.lower() and ("conflict" in error_msg.lower() or "cannot" in error_msg.lower()):
                    hint = "Check tool parameters - there may be a parameter conflict"
                elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                    hint = "Check API key or authentication credentials"
                elif "permission" in error_msg.lower() or "access denied" in error_msg.lower():
                    hint = "Check access permissions for the API or service"
                elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    hint = "Check network connectivity or increase timeout"
                elif "rate limit" in error_msg.lower():
                    hint = "API rate limit reached - wait before retrying"
                elif is_broken_resource:
                    hint = "MCP connection broken - likely caused by a previous error"
                elif is_mcp_server_error:
                    hint = "External service error - the service provider may be experiencing issues"
                
                if hint:
                    log.error(f"  Hint: {hint}")
                
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
        
        # Apply Serper-specific wrapper first (for parameter injection)
        tool_name = getattr(t, "name", "")
        if tool_name in ("google_search", "scrape"):
            try:
                t = SerperToolWrapper(inner=t)
                log.info(f"Applied SerperToolWrapper to {tool_name}")
            except Exception as e:
                log.warning(f"Failed to wrap {tool_name} with SerperToolWrapper: {e}")
        
        # Then wrap with timeout/retry so a single tool call can't stall the step
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
