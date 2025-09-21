# JK-Agents FastAPI Documentation

## Overview

The JK-Agents system now provides a FastAPI web interface that allows you to interact with the multi-agent system via HTTP endpoints. The API accepts user questions and returns the final response from the human responder agent.

## Quick Start

### 1. Start the API Server

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Start the FastAPI server
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start Required MCP Servers

```bash
# Terminal 1: Math server
python examples/mcp_servers/math_server.py

# Terminal 2: Weather server  
python examples/mcp_servers/weather_server.py
```

### 3. Test the API

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Simple query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"input": "what is the temperature in mumbai"}'
```

## API Endpoints

### Endpoint Overview

The API provides two main approaches for interacting with the multi-agent system:

1. **`/query`** - **Supervised Multi-Agent Execution**
   - Uses the supervisor to create a plan with multiple agents
   - Automatically coordinates between different agents
   - Best for complex tasks requiring multiple steps
   - Returns the final human responder's synthesized answer

2. **`/worker`** - **Direct Single Agent Execution**
   - Executes a specific agent directly without planning
   - Faster for simple, single-agent tasks
   - Returns the raw agent response
   - Useful for testing individual agents or simple queries

### Health Check

**GET** `/health`

Returns the health status of the API server.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Query Endpoint

**POST** `/query`

Main endpoint for processing user queries through the multi-agent system.

**Request Body:**
```json
{
  "input": "your question here",
  "config_path": "config/your-config.yaml"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "response": "The human responder's final answer",
  "error": null,
  "metadata": {
    "total_steps": 4,
    "execution_time": null,
    "model_used": "azure_openai:gpt-4.1"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "response": "",
  "error": "Error message describing what went wrong"
}
```

### Worker Endpoint

**POST** `/worker`

Direct worker endpoint that executes a specific agent without going through the supervisor planning process.

**Request Body:**
```json
{
  "agent_name": "weather_agent",
  "input": "what is the temperature in mumbai",
  "config_path": "config/your-config.yaml"  // optional
}
```

**Response:**
```json
{
  "success": true,
  "response": "Mumbai: 30°C, sunny",
  "agent_name": "weather_agent",
  "error": null,
  "metadata": {
    "agent_name": "weather_agent",
    "model_used": "azure_openai:gpt-4.1",
    "business_context": true
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "response": "",
  "agent_name": "weather_agent",
  "error": "Agent execution failed: specific error message"
}
```

### Legacy Endpoint

**POST** `/plan_and_run`

Legacy endpoint that redirects to `/query` for backward compatibility.

## Configuration

### Default Configuration

The API loads the default configuration from `config/agents.yaml` on startup. If this file is not found, you must provide a `config_path` in your requests.

### Custom Configuration

You can specify a custom configuration file for each request:

```json
{
  "input": "your question",
  "config_path": "config/brave_math_weather_hybrid.yaml"
}
```

## Usage Examples

### Python Client

```python
import requests

# Simple query
response = requests.post(
    "http://localhost:8000/query",
    json={"input": "what is 2+2"}
)
result = response.json()
print(f"Answer: {result['response']}")

# Query with custom config
response = requests.post(
    "http://localhost:8000/query",
    json={
        "input": "what is the temperature in mumbai and delhi",
        "config_path": "config/brave_math_weather_hybrid.yaml"
    }
)
result = response.json()
print(f"Answer: {result['response']}")

# Direct worker execution
response = requests.post(
    "http://localhost:8000/worker",
    json={
        "agent_name": "weather_agent",
        "input": "what is the temperature in mumbai",
        "config_path": "config/brave_math_weather_hybrid.yaml"
    }
)
result = response.json()
print(f"Agent Response: {result['response']}")
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

async function queryAgent(question, configPath = null) {
  try {
    const payload = { input: question };
    if (configPath) payload.config_path = configPath;
    
    const response = await axios.post(
      'http://localhost:8000/query',
      payload
    );
    
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    return null;
  }
}

// Usage
queryAgent("what is the weather in mumbai")
  .then(result => console.log(result.response));
```

### cURL Examples

```bash
# Simple math query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"input": "what is 5 + 3"}'

# Weather query with specific config
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "what is the temperature in mumbai", 
    "config_path": "config/brave_math_weather_hybrid.yaml"
  }'

# Complex multi-step query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "get the temperature in mumbai and delhi, then add them together",
    "config_path": "config/brave_math_weather_hybrid.yaml"
  }'

# Direct worker execution - Weather agent
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "weather_agent",
    "input": "what is the temperature in mumbai",
    "config_path": "config/brave_math_weather_hybrid.yaml"
  }'

# Direct worker execution - Math agent
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "math_agent",
    "input": "calculate 15 + 27",
    "config_path": "config/brave_math_weather_hybrid.yaml"
  }'
```

## Response Format

### Successful Response

- `success`: Boolean indicating if the query was processed successfully
- `response`: The final answer from the human responder agent
- `error`: null for successful requests
- `metadata`: Additional information about the execution
  - `total_steps`: Number of steps executed in the plan
  - `execution_time`: Time taken (currently null)
  - `model_used`: The default model used for the execution

### Error Response

- `success`: false
- `response`: Empty string
- `error`: Description of what went wrong
- `metadata`: null

## Error Handling

The API handles various error scenarios:

1. **Configuration Errors**: Invalid or missing config files
2. **Execution Errors**: Failures during multi-agent execution
3. **Validation Errors**: Invalid request format or missing required fields
4. **System Errors**: Internal server errors

All errors are returned with appropriate HTTP status codes and descriptive error messages.

## Performance Considerations

- The API processes requests sequentially
- Complex queries with multiple agents may take 10-30 seconds
- Consider implementing request timeouts on the client side
- Monitor server logs for performance insights

## Security Notes

- The API currently allows all origins (CORS: `*`)
- Configure CORS appropriately for production use
- Consider adding authentication for production deployments
- Validate and sanitize user inputs as needed

## Monitoring and Logging

The API provides detailed logging:
- Request processing logs
- Agent execution logs  
- Error logs with stack traces
- Performance metrics

Check the console output or configure logging to files as needed.
