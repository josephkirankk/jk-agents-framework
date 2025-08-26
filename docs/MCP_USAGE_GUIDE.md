# MCP Server Usage Guide

## Quick Start

### 1. Running MCP Servers

#### Math Server
```bash
# As MCP server (stdio)
python examples/mcp_servers/math_server.py stdio

# As HTTP server
python examples/mcp_servers/math_server.py
# or
MATH_PORT=8001 python examples/mcp_servers/math_server.py

# As SSE server
python examples/mcp_servers/math_server.py sse
```

#### Weather Server
```bash
# As MCP server (stdio)
python examples/mcp_servers/weather_server.py stdio

# As HTTP server
python examples/mcp_servers/weather_server.py
# or
WEATHER_PORT=8002 python examples/mcp_servers/weather_server.py

# As SSE server
python examples/mcp_servers/weather_server.py sse
```

### 2. Testing MCP Servers

#### Simple Test
```bash
cd tests
python test_mcp_simple.py
```

#### Comprehensive Tests
```bash
cd tests
python test_mcp_basic.py          # Basic functionality
python test_mcp_agents.py         # Agent integration
python test_mcp_performance.py    # Performance tests
python run_mcp_tests.py           # All tests
```

## Configuration Examples

### Agent with MCP Math Server

```yaml
# config/math_agent_example.yaml
models:
  default: "openai:gpt-4o-mini"

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o-mini"
  prompt: "You are a supervisor agent."

agents:
  - name: "math_agent"
    description: "Mathematical computation agent"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a math agent with access to powerful calculation tools.
      Available MCP servers: {{mcpservers}}
      
      Use the available tools to perform accurate calculations.
      Always show your work and explain the steps.
    mcp_servers:
      math:
        description: "Mathematical operations server"
        transport: "stdio"
        command: "python"
        args: ["examples/mcp_servers/math_server.py", "stdio"]
        env: {}
```

### Agent with MCP Weather Server

```yaml
# config/weather_agent_example.yaml
models:
  default: "openai:gpt-4o-mini"

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o-mini"
  prompt: "You are a supervisor agent."

agents:
  - name: "weather_agent"
    description: "Weather information agent"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a weather agent with access to weather information.
      Available MCP servers: {{mcpservers}}
      
      Provide accurate weather information for requested cities.
      If a city is not available, suggest similar cities.
    mcp_servers:
      weather:
        description: "Weather information server"
        transport: "stdio"
        command: "python"
        args: ["examples/mcp_servers/weather_server.py", "stdio"]
        env: {}
```

### Multi-Agent with Different MCP Servers

```yaml
# config/multi_mcp_example.yaml
models:
  default: "openai:gpt-4o-mini"

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o-mini"
  prompt: |
    You are a supervisor coordinating multiple specialized agents.
    Delegate tasks to the appropriate agent based on the request type.

agents:
  - name: "math_agent"
    description: "Handles mathematical calculations"
    model: "openai:gpt-4o-mini"
    prompt: "You are a math specialist. Available MCP servers: {{mcpservers}}"
    mcp_servers:
      math:
        transport: "stdio"
        command: "python"
        args: ["examples/mcp_servers/math_server.py", "stdio"]

  - name: "weather_agent"
    description: "Provides weather information"
    model: "openai:gpt-4o-mini"
    prompt: "You are a weather specialist. Available MCP servers: {{mcpservers}}"
    mcp_servers:
      weather:
        transport: "stdio"
        command: "python"
        args: ["examples/mcp_servers/weather_server.py", "stdio"]

  - name: "code_agent"
    description: "Executes Python code"
    model: "openai:gpt-4o-mini"
    prompt: "You are a Python code execution specialist. Available MCP servers: {{mcpservers}}"
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args: [
          "run", "-N", "-R=node_modules", "-W=node_modules",
          "--node-modules-dir=auto", 
          "jsr:@pydantic/mcp-run-python", 
          "stdio"
        ]
```

## API Usage Examples

### Direct MCP Tool Usage

```python
import asyncio
from app.mcp_loader import load_mcp_tools, close_mcp_client

async def use_math_server():
    servers_cfg = {
        "math": {
            "transport": "stdio",
            "command": "python",
            "args": ["examples/mcp_servers/math_server.py", "stdio"]
        }
    }
    
    mcp_client, tools = await load_mcp_tools(servers_cfg)
    
    try:
        # Find the add tool
        add_tool = next((t for t in tools if t.name == 'add'), None)
        if add_tool:
            result = await add_tool.arun({"a": 15, "b": 27})
            print(f"15 + 27 = {result}")
        
        # Find the calculate tool
        calc_tool = next((t for t in tools if t.name == 'calculate'), None)
        if calc_tool:
            result = await calc_tool.arun({"expression": "2 * 3 + 5"})
            print(f"2 * 3 + 5 = {result}")
            
    finally:
        await close_mcp_client(mcp_client)

# Run the example
asyncio.run(use_math_server())
```

### Agent API Usage

```python
import requests

# Start the API server first
# uvicorn app.api:app --reload

# Use math agent
response = requests.post("http://localhost:8000/worker", json={
    "agent_name": "math_agent",
    "input": "Calculate the area of a circle with radius 5",
    "config_path": "config/math_agent_example.yaml"
})

print(response.json())
```

## Available MCP Tools

### Math Server Tools

| Tool | Description | Parameters | Example |
|------|-------------|------------|---------|
| `add` | Add two numbers | `a: float, b: float` | `{"a": 5, "b": 3}` |
| `subtract` | Subtract b from a | `a: float, b: float` | `{"a": 10, "b": 3}` |
| `multiply` | Multiply two numbers | `a: float, b: float` | `{"a": 4, "b": 7}` |
| `divide` | Divide a by b | `a: float, b: float` | `{"a": 15, "b": 3}` |
| `calculate` | Evaluate expression | `expression: str` | `{"expression": "2*3+5"}` |
| `operation` | Named operation | `op: str, a: float, b: float` | `{"op": "add", "a": 5, "b": 3}` |

### Weather Server Tools

| Tool | Description | Parameters | Example |
|------|-------------|------------|---------|
| `get_weather` | Complete weather info | `city: str` | `{"city": "Mumbai"}` |
| `get_temperature` | Temperature only | `city: str` | `{"city": "London"}` |
| `get_condition` | Weather condition | `city: str` | `{"city": "Tokyo"}` |
| `list_cities` | Available cities | None | `{}` |

### Python Runner Tools

| Tool | Description | Parameters | Example |
|------|-------------|------------|---------|
| `run_python_code` | Execute Python code | `code: str` | `{"code": "print(2+3)"}` |

## Troubleshooting

### Common Issues

1. **"Math server file not found"**
   - Ensure you're running from the correct directory
   - Check that `examples/mcp_servers/math_server.py` exists

2. **"String tool inputs are not allowed"**
   - Use structured JSON arguments: `{"a": 5, "b": 3}`
   - Don't use string arguments: `'{"a": 5, "b": 3}'`

3. **"Deno not available"**
   - Install Deno: `curl -fsSL https://deno.land/install.sh | sh`
   - Or skip Python runner tests

4. **Port already in use**
   - Change port: `WEATHER_PORT=8003 python weather_server.py`
   - Or stop conflicting processes

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Check if servers are running:
```bash
# Math server (HTTP mode)
curl http://localhost:8001/health

# Weather server (HTTP mode)  
curl http://localhost:8002/health
```

## Best Practices

1. **Always use structured arguments** for MCP tools
2. **Set appropriate timeouts** for different server types
3. **Handle errors gracefully** with try-catch blocks
4. **Clean up resources** with proper client closure
5. **Test with real servers** rather than mocks
6. **Monitor server health** in production environments
7. **Use environment variables** for configuration
8. **Implement retry logic** for transient failures

## Next Steps

1. Create custom MCP servers for your specific needs
2. Integrate with external APIs and services
3. Implement caching and performance optimizations
4. Add monitoring and alerting for production use
5. Explore advanced MCP features like resources and prompts
