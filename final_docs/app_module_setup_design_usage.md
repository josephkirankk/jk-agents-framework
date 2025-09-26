# App Module Documentation

## Module Overview

The `app` module is the core application layer of the JK-Agents Framework, providing the primary infrastructure for building, managing, and orchestrating multi-agent AI systems. This module implements the supervisor-agent architecture, handles LLM provider integration, manages memory and state persistence, and provides the runtime environment for agent execution.

## Setup Instructions

### Prerequisites

1. **Python 3.11+** installed
2. **API Keys** for LLM providers (stored in `.env` file):
   ```bash
   # OpenAI
   OPENAI_API_KEY=your_openai_key
   
   # Azure OpenAI (optional)
   AZURE_OPENAI_API_KEY=your_azure_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_API_VERSION=2024-10-21
   AZURE_OPENAI_DEPLOYMENT=your_deployment_name
   
   # Google Gemini
   GOOGLE_API_KEY=your_google_key
   
   # Anthropic Claude
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. **Dependencies Installation**:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration Setup

1. Create a configuration directory structure:
   ```bash
   mkdir -p config/prompts
   ```

2. Create an `agents.yaml` configuration file in `config/`:
   ```yaml
   models:
     default: "google:gemini-2.0-flash-exp"
     supervisor: "google:gemini-1.5-pro"
   
   business_context: |
     Your organization context and rules
   
   supervisor:
     name: "supervisor"
     prompt_file: "prompts/supervisor_prompt.md"
   
   agents:
     - name: "data_analyst"
       model: "google:gemini-2.0-flash-lite-001"
       prompt_file: "prompts/data_analyst_prompt.md"
       mcp_servers:
         python_tool:
           transport: "stdio"
           command: "python"
           args: ["tools/python_server.py"]
   ```

3. Set up memory persistence (optional):
   ```yaml
   persistence:
     type: "chromadb"  # or "memory" for in-memory storage
     path: "./chroma_memory"
   ```

### Module Initialization

```python
from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled

# Load configuration
app_cfg = load_app_config()

# Build agents
agents_map, mcp_clients = await build_agents_map(app_cfg, user_input="User query")

# Build supervisor
supervisor = build_supervisor_compiled(
    app_cfg.supervisor,
    app_cfg.agents,
    app_cfg.models.get("default"),
    business_context=app_cfg.business_context
)
```

## Design Overview

### Architecture Pattern: Supervisor-Agent Model

```
┌─────────────────────────────────────────────┐
│                FastAPI Server                │
│                  (api.py)                    │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│            Main Application                  │
│              (app/main.py)                   │
├──────────────────────────────────────────────┤
│  • Config Loading (AppConfig)                │
│  • Agent/Supervisor Initialization           │
│  • Request Routing                           │
└────────┬──────────────┬─────────────────────┘
         │              │
┌────────▼────┐  ┌──────▼──────────────────┐
│ Supervisor  │  │    Agent Builder        │
│  Builder    │  │  (agent_builder.py)     │
└─────────────┘  └───────────────────────────┘
         │              │
         ▼              ▼
┌─────────────────────────────────────────────┐
│         Agent Execution Layer               │
├─────────────────────────────────────────────┤
│  • React Agents (LangGraph)                 │
│  • Tool Integration (MCP/HTTP/Python)       │
│  • Memory Management (ChromaDB)             │
└─────────────────────────────────────────────┘
```

### Core Components

#### 1. **Configuration System** (`config.py`)
- **AppConfig**: Root configuration model
- **AgentConfig**: Individual agent configurations
- **SupervisorConfig**: Supervisor agent configuration
- **MCPServerConfig**: Tool server configurations
- Pydantic models for validation and type safety

#### 2. **Agent Builder** (`agent_builder.py`)
- Creates React agents using LangGraph
- Integrates multiple tool types (MCP, HTTP, Python functions)
- Handles multi-provider LLM initialization
- Manages prompt rendering with placeholders
- Implements Gemini schema filtering for compatibility

#### 3. **Supervisor Builder** (`supervisor_builder.py`)
- Constructs the planning and orchestration agent
- Manages task decomposition and agent assignment
- Handles business context injection
- Supports dynamic prompt templates

#### 4. **Planner Executor** (`planner_executor.py`)
- Executes supervisor-generated plans
- Routes tasks to appropriate agents
- Manages execution flow and dependencies
- Handles retries and error recovery

#### 5. **Memory Subsystem** (`app/memory/`)
- **ChromaDB Backend**: Persistent vector storage
- **Checkpointer Manager**: State persistence across sessions
- **Enhanced Tool Node**: Tool execution with memory
- **Smart Tool Wrapper**: Automatic large data handling
- **LangGraph Adapter**: Integration with LangGraph framework

#### 6. **Tool Integration**
- **MCP Loader** (`mcp_loader.py`): Model Context Protocol tools
- **Python Tool Loader** (`python_tool_loader.py`): Python function tools
- **HTTP Tools**: RESTful API integration
- Dynamic tool discovery and registration

#### 7. **Utility Systems**
- **Thread Manager** (`thread_manager.py`): Conversation state management
- **Template Utils** (`template_utils.py`): Jinja2 template rendering
- **Placeholder System** (`placeholder_system/`): Dynamic content injection
- **LLM Payload Logger** (`llm_payload_logger.py`): Request/response logging
- **Markdown Formatter** (`markdown_formatter.py`): Output formatting

### Data Flow

1. **Request Reception**: FastAPI endpoint receives user query
2. **Configuration Loading**: System loads agent configurations
3. **Supervisor Planning**: Supervisor decomposes task into steps
4. **Agent Assignment**: Each step assigned to appropriate agent
5. **Tool Execution**: Agents execute tools to complete tasks
6. **Memory Persistence**: Results stored in memory system
7. **Response Formatting**: Results formatted and returned

## Usage Guide

### Basic Usage: Direct Agent Execution

```python
from app.main import run_direct_agent, load_app_config

# Load configuration
app_cfg = load_app_config()

# Execute agent directly
result = await run_direct_agent(
    agent_name="data_analyst",
    user_input="Analyze the sales data",
    app_cfg=app_cfg
)
```

### Advanced Usage: Supervisor-Orchestrated Execution

```python
from app.planner_executor import execute_plan
from app.supervisor_builder import build_supervisor_compiled

# Build supervisor
supervisor = build_supervisor_compiled(
    app_cfg.supervisor,
    app_cfg.agents,
    default_model="google:gemini-2.0-flash-exp"
)

# Execute complex task through supervisor
result = await execute_plan(
    user_query="Create a comprehensive market analysis report",
    supervisor_agent=supervisor,
    agents_map=agents_map,
    config={"configurable": {"thread_id": "session_123"}}
)
```

### Memory Management

```python
from app.checkpointer_manager import (
    get_memory_stats,
    clear_thread_memory,
    reset_all_memory
)

# Get memory statistics
stats = await get_memory_stats()

# Clear specific thread memory
await clear_thread_memory("thread_123")

# Reset all memory (caution!)
await reset_all_memory()
```

### Custom Tool Integration

```python
# Define Python function tool
def analyze_data(data: List[float]) -> Dict[str, float]:
    """Analyze numerical data."""
    return {
        "mean": sum(data) / len(data),
        "min": min(data),
        "max": max(data)
    }

# Register in agent configuration
agent_config = {
    "name": "analyst",
    "python_tools": {
        "data_tools": {
            "module_path": "tools.custom_tools",
            "function_name": "analyze_data"
        }
    }
}
```

### Multi-Provider Model Usage

```python
# OpenAI
model = "openai:gpt-4o"

# Azure OpenAI
model = "azure_openai:gpt-4-deployment"

# Google Gemini with temperature
model = "google:gemini-2.0-flash-exp:0.7"

# Anthropic Claude
model = "anthropic:claude-3-sonnet"

# Local LM Studio
model = "openai:local-model"  # With OPENAI_BASE_URL set
```

### Error Handling

```python
try:
    result = await execute_plan(query, supervisor, agents_map)
except TimeoutError:
    # Handle execution timeout
    pass
except ValidationError:
    # Handle configuration validation errors
    pass
except Exception as e:
    # Generic error handling
    logger.error(f"Execution failed: {e}")
```

## Key Features

### 1. **Multi-Provider LLM Support**
- Seamless switching between OpenAI, Azure OpenAI, Google Gemini, Anthropic Claude
- Automatic provider detection based on environment variables
- Model-specific optimizations (e.g., Gemini schema filtering)

### 2. **Flexible Tool System**
- Model Context Protocol (MCP) servers
- HTTP/REST API tools
- Python function tools
- Dynamic tool creation at runtime

### 3. **Advanced Memory Management**
- ChromaDB for vector storage
- Thread-based conversation persistence
- Automatic memory optimization
- Large data handling with compression

### 4. **Supervisor Intelligence**
- Task decomposition and planning
- Dynamic agent assignment
- Dependency management
- Retry and error recovery

### 5. **Production Features**
- Comprehensive logging and monitoring
- Health checks and metrics
- Rate limiting and throttling
- Authentication and authorization hooks

## Best Practices

### Configuration Management
1. Use environment variables for sensitive data
2. Separate prompts into individual files
3. Version control configuration files
4. Use descriptive agent names and descriptions

### Performance Optimization
1. Enable memory caching for frequently accessed data
2. Use connection pooling for database operations
3. Implement lazy loading for large datasets
4. Set appropriate model temperature values

### Security Considerations
1. Never hardcode API keys
2. Validate all user inputs
3. Implement rate limiting for API endpoints
4. Use secure communication protocols

### Error Handling
1. Implement comprehensive try-catch blocks
2. Log errors with appropriate context
3. Provide graceful degradation
4. Set reasonable timeout values

## Troubleshooting

### Common Issues

1. **Agent Not Found Error**
   - Verify agent name in configuration
   - Check YAML syntax and indentation
   - Ensure configuration file is loaded

2. **MCP Server Connection Failed**
   - Verify command and arguments
   - Check file permissions
   - Ensure required dependencies installed

3. **Memory Persistence Issues**
   - Check ChromaDB initialization
   - Verify storage path permissions
   - Monitor disk space availability

4. **Model Provider Errors**
   - Verify API keys in environment
   - Check rate limits and quotas
   - Ensure network connectivity

## Module Dependencies

- **LangChain/LangGraph**: Agent orchestration framework
- **Pydantic**: Configuration validation
- **ChromaDB**: Vector database for memory
- **FastAPI**: Web server framework
- **Jinja2**: Template rendering
- **psutil**: System monitoring

## Extension Points

1. **Custom Agent Types**: Extend `AgentConfig` for specialized agents
2. **Tool Providers**: Implement new tool loading mechanisms
3. **Memory Backends**: Add alternative storage systems
4. **Model Providers**: Integrate additional LLM providers
5. **Prompt Templates**: Create domain-specific prompt systems