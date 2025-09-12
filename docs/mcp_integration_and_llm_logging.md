# MCP Server Integration and LLM Payload Logging

This document explains how MCP (Model Context Protocol) servers are integrated with React agents in the JK-Agents framework and details the enhanced logging system that captures complete LLM payloads.

## Table of Contents

1. [MCP Server Integration Overview](#mcp-server-integration-overview)
2. [Configuration](#configuration)
3. [Integration Flow](#integration-flow)
4. [LLM Payload Logging](#llm-payload-logging)
5. [Usage Examples](#usage-examples)
6. [Log File Structure](#log-file-structure)
7. [Troubleshooting](#troubleshooting)

## MCP Server Integration Overview

MCP servers provide external tools and capabilities to React agents. The integration process involves:

1. **Configuration**: MCP servers are defined in YAML configuration files
2. **Loading**: Tools are loaded from MCP servers during agent initialization
3. **Binding**: Tools are bound to the LLM model for function calling
4. **Execution**: The React agent can call MCP tools during conversation flow
5. **Logging**: Complete interactions are logged for debugging and analysis

## Configuration

### Basic MCP Server Configuration

```yaml
agents:
  - name: "restaurants_agent"
    description: "A restaurants agent to get restaurant information"
    model: "azure_openai:gpt-4.1"
    prompt: |
      You are a helpful restaurant search agent.
      Available MCP servers: {{mcpservers}}
    mcp_servers:
      restaurant_search:
        description: "MCP server for searching Restaurants."
        transport: "sse"  # or "stdio", "streamable_http"
        url: "http://localhost:8082/test/sse"
        headers:
          Authorization: "Bearer <token>"
        env: {}
```

### Supported Transport Types

1. **SSE (Server-Sent Events)**: HTTP-based streaming transport
2. **stdio**: Standard input/output for local processes
3. **streamable_http**: HTTP-based request/response transport

### Configuration Parameters

- `description`: Human-readable description of the MCP server
- `transport`: Communication protocol (sse, stdio, streamable_http)
- `url`: Server endpoint (for HTTP-based transports)
- `command`: Command to execute (for stdio transport)
- `args`: Command arguments (for stdio transport)
- `headers`: HTTP headers (for HTTP-based transports)
- `env`: Environment variables

## Integration Flow

### 1. Agent Building Process

```python
async def build_react_agent(agent_cfg, default_model, ...):
    # Extract MCP server configurations
    servers_raw = {
        k: v.model_dump(exclude_none=True)
        for k, v in agent_cfg.mcp_servers.items()
    }
    
    # Load MCP tools from configured servers
    mcp_client, tools = await load_mcp_tools(servers_raw)
    
    # Create model instance
    actual_model = init_chat_model(model_instance)
    
    # Wrap with logging if enabled
    if enable_llm_payload_logging:
        actual_model = LoggingModelWrapper(actual_model, llm_payload_logger)
    
    # Bind tools to model
    model_with_tools = actual_model.bind_tools(tools, parallel_tool_calls=False)
    
    # Create React agent
    agent = create_react_agent(
        model=model_with_tools,
        tools=tools,
        prompt=prompt_filled,
        name=agent_cfg.name
    )
```

### 2. Tool Loading and Wrapping

```python
async def load_mcp_tools(servers_cfg):
    # Create MCP client
    mcp_client = MultiServerMCPClient(client_cfg)
    
    # Get tools from all servers
    tools = await mcp_client.get_tools()
    
    # Wrap tools with timeout/retry functionality
    wrapped_tools = []
    for tool in tools:
        wrapped_tools.append(TimeoutTool(
            inner=tool,
            timeout=30.0,
            retries=0
        ))
    
    return mcp_client, wrapped_tools
```

### 3. Prompt Template Integration

MCP server information is injected into agent prompts via Jinja2 templates:

```python
# Create summary of MCP servers for prompt
summary = _build_mcp_summary(servers_raw, tools)

# Render prompt with MCP server context
ctx = {
    "mcpservers": summary,
    "businessContext": business_context,
    "original_user_question": original_user_question,
    "agent_name": agent_cfg.name,
}
prompt_filled = render_prompt(prompt_content, ctx)
```

## LLM Payload Logging

The enhanced logging system captures complete LLM interactions including:

- **Request Messages**: Full message history sent to the LLM
- **Tool Definitions**: Complete tool schemas and descriptions
- **Model Parameters**: Temperature, max tokens, model configuration
- **Response Content**: Full response from the LLM
- **Usage Information**: Token counts and billing information
- **Error Details**: Complete error information if calls fail

### Key Components

#### 1. LLMPayloadLogger

```python
class LLMPayloadLogger:
    def log_llm_interaction(
        self,
        interaction_type: str,
        messages: List[Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        model_params: Optional[Dict[str, Any]] = None,
        response: Optional[Any] = None,
        usage: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        # Logs complete interaction to JSON file
```

#### 2. LoggingModelWrapper

```python
class LoggingModelWrapper(BaseChatModel):
    def invoke(self, input, config=None, **kwargs):
        # Log request
        self._payload_logger.log_llm_interaction(...)
        
        # Call wrapped model
        response = self._wrapped_model.invoke(input, config=config, **kwargs)
        
        # Log response
        self._payload_logger.log_llm_interaction(...)
        
        return response
```

#### 3. DirectAgentLogger Integration

```python
class DirectAgentLogger:
    def __init__(self, agent_name: str, user_input: str, business_context: str = ""):
        # Initialize LLM payload logger
        self.llm_payload_logger = LLMPayloadLogger(agent_name)
    
    def get_llm_payload_logger(self) -> LLMPayloadLogger:
        return self.llm_payload_logger
```

## Usage Examples

### 1. Running Agent with Enhanced Logging

```python
# Create logger
logger = create_direct_agent_logger(
    agent_name="restaurants_agent",
    user_input="Find pizza restaurants",
    business_context="Restaurant search system"
)

# Build agent with logging enabled
compiled, mcp_client = await build_react_agent(
    target_agent,
    default_model,
    enable_llm_payload_logging=True,
    llm_payload_logger=logger.get_llm_payload_logger(),
)

# Execute agent
result = await compiled.ainvoke(state, config=config)

# Access log files
standard_log = logger.get_log_file_path()
payload_log = logger.get_llm_payload_log_path()
```

### 2. API Response with Log Paths

```json
{
  "success": true,
  "response": "Found 5 pizza restaurants...",
  "agent_name": "restaurants_agent",
  "log_file": "logs/direct_agent_restaurants_agent_20240115_103000.log",
  "llm_payload_log_file": "logs/llm_payload_restaurants_agent_20240115_103000.json"
}
```

## Log File Structure

### Standard Log File (.log)

```
--- Direct Agent Request (agent=restaurants_agent) ---
Model: azure_openai:gpt-4.1
Agent Prompt: You are a helpful restaurant search agent...
System Context: Business context: Restaurant search system...
User: Find pizza restaurants with menu score 80-100

--- Direct Agent Response (agent=restaurants_agent) ---
I'll search for pizza restaurants with high menu scores...

Tool Calls:
  1. restaurant_search(cuisine=["pizza"], menu_score_min=80, menu_score_max=100)
     → Found 5 restaurants matching criteria

--- Usage Information ---
Input tokens: 245
Output tokens: 156
Total tokens: 401
```

### LLM Payload Log File (.json)

```json
{
  "log_type": "llm_payload_log",
  "agent_name": "restaurants_agent",
  "created_at": "2024-01-15T10:30:00.000Z",
  "entries": [
    {
      "timestamp": "2024-01-15T10:30:01.123Z",
      "interaction_type": "invoke",
      "request": {
        "messages": [
          {
            "type": "SystemMessage",
            "content": "Business context:\nRestaurant search system...",
            "role": "system"
          },
          {
            "type": "HumanMessage",
            "content": "Find pizza restaurants with menu score 80-100",
            "role": "user"
          }
        ],
        "tools": [
          {
            "name": "restaurant_search",
            "description": "Search for restaurants based on criteria",
            "args_schema": {
              "type": "object",
              "properties": {
                "cuisine": {
                  "type": "array",
                  "items": {"type": "string"}
                },
                "menu_score_min": {"type": "integer"},
                "menu_score_max": {"type": "integer"}
              }
            }
          }
        ],
        "model_params": {
          "model_name": "gpt-4",
          "temperature": 0.0,
          "max_tokens": null
        }
      },
      "response": {
        "type": "AIMessage",
        "content": "I'll search for pizza restaurants...",
        "tool_calls": [
          {
            "id": "call_123",
            "name": "restaurant_search",
            "args": {
              "cuisine": ["pizza"],
              "menu_score_min": 80,
              "menu_score_max": 100
            }
          }
        ],
        "usage_metadata": {
          "input_tokens": 245,
          "output_tokens": 156,
          "total_tokens": 401
        }
      }
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   - Check server URL and port
   - Verify authentication headers
   - Ensure server is running

2. **Tool Loading Errors**
   - Check MCP server configuration
   - Verify tool schemas
   - Review server logs

3. **Logging Issues**
   - Check file permissions in logs directory
   - Verify disk space
   - Review logger initialization

### Debug Commands

```bash
# Test MCP server connectivity
curl -H "Authorization: Bearer <token>" http://localhost:8082/test/sse

# Check log files
ls -la logs/
tail -f logs/llm_payload_*.json

# Run test script
python test_llm_payload_logging.py
```

### Environment Variables

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Set custom log directory
export LOG_DIR=./custom_logs

# MCP server timeouts
export MCP_TOOL_TIMEOUT=30
export MCP_TOOL_RETRIES=2
```

## Benefits of Enhanced Logging

1. **Complete Visibility**: See exactly what's sent to and received from the LLM
2. **Debugging**: Identify issues with tool calls and responses
3. **Cost Tracking**: Monitor token usage across interactions
4. **Audit Trail**: Maintain complete records of agent interactions
5. **Performance Analysis**: Analyze response times and success rates
6. **Compliance**: Meet regulatory requirements for AI system logging
