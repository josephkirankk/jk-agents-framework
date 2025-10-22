from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


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

    @field_validator("transport")
    @classmethod
    def check_transport(cls, v):
        if v not in ("stdio", "streamable_http", "sse", "http"):
            raise ValueError(
                "transport must be one of: stdio, streamable_http, sse, http"
            )
        return v

    @model_validator(mode='after')
    def validate_transport_requirements(self):
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio transport requires 'command'")
        if (
            self.transport in ("streamable_http", "sse", "http")
            and not self.url
        ):
            raise ValueError("HTTP-like transport requires 'url'")
        return self


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


class SubAgentConfig(BaseModel):
    """Configuration for DeepAgents subagents."""
    name: str = Field(
        ...,
        description="Unique name for the subagent"
    )
    description: str = Field(
        ...,
        description="Description of what this subagent does (used by main agent for routing)"
    )
    system_prompt: str = Field(
        ...,
        description="System prompt for the subagent"
    )
    model: Optional[str] = Field(
        None,
        description="Model to use for this subagent (if None, uses parent agent's model)"
    )
    tools: Optional[List[str]] = Field(
        default_factory=list,
        description="List of tool names available to this subagent (subset of parent tools)"
    )
    # Could extend with tool definitions if needed
    mcp_servers: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="MCP servers specific to this subagent"
    )


class DeepAgentConfig(BaseModel):
    """Configuration for DeepAgents-specific features."""
    enabled: bool = Field(
        default=True,
        description="Enable DeepAgents mode for this agent"
    )
    
    # Middleware configuration
    enable_filesystem: bool = Field(
        default=True,
        description="Enable virtual filesystem middleware for context management"
    )
    enable_todolist: bool = Field(
        default=True,
        description="Enable todo list middleware for task planning"
    )
    enable_longterm_memory: bool = Field(
        default=False,
        description="Enable long-term memory across conversation threads"
    )
    
    # Subagent configuration
    subagents: List[SubAgentConfig] = Field(
        default_factory=list,
        description="Subagents for hierarchical task decomposition"
    )
    
    # Human-in-the-loop configuration
    interrupt_on: Optional[Dict[str, Dict[str, Any]]] = Field(
        default=None,
        description="Tool names that require human approval before execution"
    )
    
    # Store configuration for long-term memory
    store_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for LangGraph Store (long-term memory)"
    )


class AgentConfig(BaseModel):
    name: str
    description: Optional[str] = ""
    model: Optional[str] = None
    prompt: Optional[str] = None
    prompt_file: Optional[str] = None
    # Agent type configuration - defaults to "react" for backward compatibility
    agent_type: Optional[str] = Field(
        default="react",
        description=(
            "Type of agent to create. Options: 'react' (ReAct agent with tools and reasoning), 'normal' (basic chat agent without tool calling), or 'deep' (DeepAgents with planning and subagents). Default is 'react' for backward compatibility."
        ),
    )
    
    # DeepAgents configuration (only used when agent_type="deep")
    deep_agent_config: Optional[DeepAgentConfig] = Field(
        default=None,
        description="Configuration for DeepAgents features (only applies when agent_type='deep')"
    )
    
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    # Optional simple HTTP tools configuration (non-MCP)
    # Each entry defines a callable HTTP endpoint exposed as a LangChain Tool
    http_tools: Dict[str, Dict] = Field(default_factory=dict)
    # Optional Python function tools configuration
    # Each entry defines Python functions to be loaded as LangChain Tools
    python_tools: Dict[str, PythonFunctionToolConfig] = Field(
        default_factory=dict
    )
    # Optional: control whether the LLM can call multiple tools in parallel
    # If None, the application-level default will be used. If still None, we
    # auto-detect based on provider (disabled for Google Gemini, enabled otherwise).
    parallel_tool_calls_enabled: Optional[bool] = Field(
        default=None,
        description=(
            "Enable or disable parallel tool calls for this agent. Overrides app-level setting when provided."
        ),
    )

    @field_validator("agent_type")
    @classmethod
    def check_agent_type(cls, v):
        """Validate agent_type is one of the supported options."""
        if v is not None and v not in ("react", "normal", "deep"):
            raise ValueError(
                "agent_type must be one of: 'react', 'normal', 'deep'"
            )
        return v

    @model_validator(mode='after')
    def validate_prompt_fields(self):
        """Ensure either prompt or prompt_file is provided, but not both."""
        if not self.prompt and not self.prompt_file:
            raise ValueError(
                "Either 'prompt' or 'prompt_file' must be provided"
            )

        return self


class SupervisorConfig(BaseModel):
    name: str = "supervisor"
    model: Optional[str] = None
    prompt: Optional[str] = None
    prompt_file: Optional[str] = None

    @model_validator(mode='after')
    def validate_prompt_fields(self):
        """Ensure either prompt or prompt_file is provided, but not both."""
        if not self.prompt and not self.prompt_file:
            raise ValueError(
                "Either 'prompt' or 'prompt_file' must be provided"
            )

        return self


class ConversationMemoryConfig(BaseModel):
    """Configuration for conversation memory storage."""
    enabled: bool = Field(
        default=False,
        description="Enable conversation memory storage and context injection"
    )
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database URL for conversation storage"
    )
    max_conversations: int = Field(
        default=5,
        description="Maximum number of recent conversations to include in context"
    )
    max_context_length: int = Field(
        default=2000,
        description="Maximum length of conversation context in characters"
    )
    pool_size: int = Field(
        default=10,
        description="Database connection pool size"
    )
    cleanup_days: int = Field(
        default=30,
        description="Days to keep conversations before cleanup (0 = no cleanup)"
    )
    prepend_context: bool = Field(
        default=False,
        description="If True, prepend conversation context to system message; otherwise append"
    )


class MemoryLoggingConfig(BaseModel):
    """Configuration for memory transaction logging."""
    enabled: bool = Field(
        default=False,
        description="Enable memory transaction logging for debugging"
    )
    log_directory: str = Field(
        default="memory_logs",
        description="Directory where memory transaction logs will be stored"
    )
    include_content: bool = Field(
        default=True,
        description="Include actual message content in logs (disable for sensitive data)"
    )
    max_content_length: int = Field(
        default=1000,
        description="Maximum content length to log (truncated if longer)"
    )
    
    @classmethod
    def from_env(cls) -> 'MemoryLoggingConfig':
        """Create MemoryLoggingConfig from environment variables."""
        return cls(
            enabled=os.getenv('MEMORY_LOGGING_ENABLED', 'false').lower() == 'true',
            log_directory=os.getenv('MEMORY_LOGGING_DIRECTORY', 'memory_logs'),
            include_content=os.getenv('MEMORY_LOGGING_INCLUDE_CONTENT', 'true').lower() == 'true',
            max_content_length=int(os.getenv('MEMORY_LOGGING_MAX_CONTENT_LENGTH', '1000'))
        )


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
    conversation_memory: ConversationMemoryConfig = Field(
        default_factory=ConversationMemoryConfig,
        description="Configuration for conversation memory storage"
    )
    memory_logging: MemoryLoggingConfig = Field(
        default_factory=MemoryLoggingConfig.from_env,
        description="Configuration for memory transaction logging"
    )
    # Large data handling configuration for tools that generate large outputs
    large_data_handling: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for handling large tool outputs (storage, summarization)"
    )
    supervisor: SupervisorConfig
    agents: List[AgentConfig] = Field(default_factory=list)
    temperature: float = 0.0
    # Optional: App-wide control for parallel tool calls. If None, provider-based
    # autodetection is used (disabled for Google Gemini, enabled otherwise).
    parallel_tool_calls_enabled: Optional[bool] = Field(
        default=None,
        description=(
            "Global default for parallel tool calls. Individual agents can override."
        ),
    )
