from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class MCPServerConfig(BaseModel):
    description: Optional[str] = Field(
        "",
        description="Short description of what this MCP server provides",
    )
    transport: str = Field(..., description="stdio | streamable_http | sse")
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None

    @validator("transport")
    def check_transport(cls, v):
        if v not in ("stdio", "streamable_http", "sse", "http"):
            raise ValueError(
                "transport must be one of: stdio, streamable_http, sse, http"
            )
        return v

    @validator("command")
    def require_command_for_stdio(cls, v, values):
        if values.get("transport") == "stdio" and not v:
            raise ValueError("stdio transport requires 'command'")
        return v

    @validator("url")
    def require_url_for_http(cls, v, values):
        if (
            values.get("transport") in ("streamable_http", "sse", "http")
            and not v
        ):
            raise ValueError("HTTP-like transport requires 'url'")
        return v


class PythonFunctionToolConfig(BaseModel):
    """Configuration for Python function-based tools."""
    module_path: str = Field(
        ...,
        description="Python module path (e.g., 'tools.python_function_tools')"
    )
    function_name: Optional[str] = Field(
        None,
        description="Specific function name to load (if None, loads all)"
    )
    tool_names: Optional[List[str]] = Field(
        None,
        description="List of specific tool names to load from module"
    )
    description: Optional[str] = Field(
        "",
        description="Description of the tool or tool set"
    )


class AgentConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    model: Optional[str] = None
    prompt: str
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    # Optional simple HTTP tools configuration (non-MCP)
    # Each entry defines a callable HTTP endpoint exposed as a LangChain Tool
    http_tools: Dict[str, Dict] = Field(default_factory=dict)
    # Optional Python function tools configuration
    # Each entry defines Python functions to be loaded as LangChain Tools
    python_tools: Dict[str, PythonFunctionToolConfig] = Field(
        default_factory=dict
    )


class SupervisorConfig(BaseModel):
    name: str = "supervisor"
    model: Optional[str] = None
    prompt: str


class AppConfig(BaseModel):
    models: Dict[str, str] = Field(
        default_factory=lambda: {"default": "openai:gpt-4o-mini"}
    )
    business_context: Optional[str] = Field(
        "",
        description=(
            "Optional business context injected into supervisor prompt"
        ),
    )
    persistence: Dict[str, str] = Field(
        default_factory=lambda: {"type": "memory"}
    )
    supervisor: SupervisorConfig
    agents: List[AgentConfig] = Field(default_factory=list)
    temperature: float = 0.0
