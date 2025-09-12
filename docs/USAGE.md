# JK-Agents Framework Usage Guide

## Overview

The JK-Agents Framework provides multiple ways to interact with your multi-agent system:
- **CLI Interface**: Direct command-line interaction
- **REST API**: HTTP endpoints for web applications
- **Python API**: Direct Python integration

## Quick Start

### 1. Basic CLI Usage

#### Run with Supervisor (Recommended)
The supervisor automatically plans and coordinates multiple agents:

```bash
# Basic query with default configuration
python -m app.main "Analyze the benefits of renewable energy"

# Using specific configuration file
python -m app.main "Research market trends" --config config/my_agents.yaml
```

#### Run Specific Agent Directly
Skip the supervisor and run a specific agent:

```bash
# Run specific agent
python -m app.main "What is machine learning?" --agent research_agent

# With custom configuration
python -m app.main "Analyze this data" --agent analysis_agent --config config/data_analysis.yaml
```

### 2. API Server Usage

#### Start the Server
```bash
# Start on default port 8000
python -m app.api

# Start on custom port
uvicorn app.api:app --host 0.0.0.0 --port 8001
```

#### API Endpoints

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Query with Supervisor:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Analyze market trends for renewable energy",
    "config_path": "config/my_agents.yaml"
  }'
```

**Direct Agent Execution:**
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "research_agent",
    "input": "What are the latest developments in AI?",
    "config_path": "config/my_agents.yaml"
  }'
```

## Configuration Examples

### Basic Agent Configuration

```yaml
models:
  default: "openai:gpt-4o-mini"
  supervisor: "openai:gpt-4o"

business_context: |
  We are a technology consulting company focusing on AI and data analytics.

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o"
  prompt: |
    You are the Supervisor. Break down complex requests into specific tasks.
    Return JSON with goal and plan structure.

agents:
  - name: "researcher"
    description: "Research and information gathering specialist"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a research specialist. Gather comprehensive information on topics.
      
  - name: "analyst"
    description: "Data analysis and insights specialist"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a data analyst. Analyze information and provide actionable insights.
```

### Agent with MCP Tools

```yaml
agents:
  - name: "web_researcher"
    description: "Web research agent with search capabilities"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a web research agent with access to search tools.
      Use the available tools to gather current information.
    mcp_servers:
      brave_search:
        description: "Brave search for web information"
        transport: "sse"
        url: "http://localhost:8080/sse"
        headers:
          Authorization: "Bearer your-api-key"
```

### Agent with Python Function Tools

```yaml
agents:
  - name: "data_processor"
    description: "Data processing agent with Python tools"
    model: "openai:gpt-4o-mini"
    prompt: |
      You have access to Python function tools for data processing.
      Use these tools to perform calculations and analysis.
    python_tools:
      math_tools:
        module_path: "tools.python_function_tools"
        tool_names: ["calculate_percentage", "generate_random_data"]
        description: "Mathematical calculation tools"
```

## Common Use Cases

### 1. Research and Analysis Workflow

```bash
# Multi-step research and analysis
python -m app.main "Research the impact of AI on healthcare, then analyze the key benefits and challenges"
```

This will:
1. Supervisor creates a plan with research and analysis steps
2. Research agent gathers information about AI in healthcare
3. Analysis agent processes the research and identifies benefits/challenges
4. Human response agent formats the final answer

### 2. Data Analysis with File Upload

```bash
# Using API with file upload
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analyst" \
  -F "input=Analyze the trends in this dataset" \
  -F "files=@data.csv"
```

### 3. Multi-Provider Model Usage

```yaml
# Use different models for different agents
models:
  default: "openai:gpt-4o-mini"
  
agents:
  - name: "creative_writer"
    model: "anthropic:claude-3-sonnet-20240229"
    # ... configuration
    
  - name: "code_analyzer"
    model: "google:gemini-2.0-flash-exp"
    # ... configuration
```

## Advanced Features

### 1. Thread Management
Maintain conversation context across multiple requests:

```python
import requests

# Start a conversation
response1 = requests.post("http://localhost:8000/query", json={
    "input": "Tell me about machine learning",
    "thread_id": "my-conversation-1"
})

# Continue the conversation
response2 = requests.post("http://localhost:8000/query", json={
    "input": "What are the main types?",
    "thread_id": "my-conversation-1"  # Same thread ID
})
```

### 2. Raw Output Mode
Get plain text responses without JSON wrapping:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain quantum computing",
    "raw_output": true
  }'
```

### 3. Custom Business Context
Inject domain-specific context into all agents:

```yaml
business_context: |
  We are a financial services company specializing in:
  - Investment analysis
  - Risk assessment
  - Regulatory compliance
  
  Always consider financial regulations and risk factors in responses.
```

## Python Integration

### Direct Python Usage

```python
import asyncio
from pathlib import Path
from app.main import load_app_config, run_supervised

async def main():
    # Load configuration
    config = load_app_config(Path("config/my_agents.yaml"))
    
    # Run query
    await run_supervised("Analyze market trends", config)

if __name__ == "__main__":
    asyncio.run(main())
```

### Custom Agent Integration

```python
from app.agent_builder import build_react_agent
from app.config import AgentConfig

# Create custom agent configuration
agent_config = AgentConfig(
    name="custom_agent",
    description="My custom agent",
    model="openai:gpt-4o-mini",
    prompt="You are a helpful assistant specialized in..."
)

# Build and use the agent
agent, mcp_client = await build_react_agent(
    agent_config,
    default_model="openai:gpt-4o-mini"
)
```

## Monitoring and Logging

### Log Files
The framework generates detailed logs:
- **Application logs**: Console output with structured logging
- **LLM payload logs**: `logs/llm_payload_*.json` - Detailed LLM interactions
- **Direct agent logs**: `direct_agentlog_*.log` - CLI execution logs

### Log Analysis
```bash
# View recent LLM interactions
ls -la logs/llm_payload_*.json | tail -5

# Monitor real-time logs
tail -f direct_agentlog_*.log
```

## Troubleshooting

### Common Issues

#### 1. Agent Not Found
```
Error: Agent 'my_agent' not found in config
```
**Solution**: Check agent name spelling and ensure it's defined in your configuration file.

#### 2. Model Access Issues
```
Error: Invalid API key or model access denied
```
**Solution**: Verify API keys in `.env` file and check model availability/permissions.

#### 3. MCP Server Connection Failed
```
Error: Failed to connect to MCP server
```
**Solution**: Ensure MCP server is running and accessible at the specified URL.

#### 4. Memory Issues with Large Requests
**Solution**: 
- Use smaller context windows
- Break large requests into smaller parts
- Use streaming responses where available

### Performance Optimization

1. **Model Selection**: Use smaller models for simple tasks
2. **Parallel Processing**: The framework automatically handles parallel agent execution
3. **Caching**: Enable response caching for repeated queries
4. **Resource Monitoring**: Monitor CPU and memory usage during execution

## Best Practices

1. **Configuration Management**: Keep different configurations for different use cases
2. **Error Handling**: Always check response status in API calls
3. **Security**: Never commit API keys to version control
4. **Testing**: Test configurations with simple queries before complex workflows
5. **Monitoring**: Regularly check log files for issues and performance metrics

## File Upload and Processing

### Supported File Types
- **CSV files**: Processed locally and included in agent context
- **Images**: Uploaded to OpenAI/Azure OpenAI for vision analysis
- **Documents**: Various formats supported through OpenAI file API

### File Upload Examples

#### CSV Data Analysis
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analyst" \
  -F "input=Analyze the sales trends in this CSV file" \
  -F "files=@sales_data.csv"
```

#### Image Analysis
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=vision_analyst" \
  -F "input=Describe what you see in this image" \
  -F "files=@image.jpg"
```

#### Multiple Files
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=document_analyzer" \
  -F "input=Compare these documents and summarize key differences" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf"
```

## Environment Variables Reference

### Core Configuration
```env
# Required: At least one LLM provider
OPENAI_API_KEY=sk-...
AZURE_OPENAI_API_KEY=...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# Azure OpenAI Specific
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21

# Optional: Custom endpoints
OPENAI_BASE_URL=http://localhost:1234/v1  # For local models
OPENAI_API_BASE=http://localhost:1234/v1  # Alternative name
```

### Advanced Configuration
```env
# Logging levels
LOG_LEVEL=INFO
LANGCHAIN_VERBOSE=true

# Timeouts and retries
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# Development settings
DEBUG=false
DEVELOPMENT_MODE=false
```

## API Response Examples

### Successful Query Response
```json
{
  "success": true,
  "response": "Based on my analysis of renewable energy trends...",
  "metadata": {
    "total_steps": 3,
    "execution_time": "12.5s",
    "model_used": "openai:gpt-4o-mini"
  },
  "thread_id": "thread_abc123"
}
```

### Error Response
```json
{
  "success": false,
  "response": "",
  "error": "Agent 'unknown_agent' not found in config",
  "thread_id": "thread_abc123"
}
```

### Worker Response with Files
```json
{
  "success": true,
  "response": "Analysis of the uploaded CSV shows...",
  "agent_name": "data_analyst",
  "metadata": {
    "files_uploaded": 1,
    "file_info": [
      {
        "filename": "data.csv",
        "mime_type": "text/csv",
        "purpose": "local_processing",
        "size": 1024
      }
    ]
  }
}
```

## Configuration Validation

### Validate Configuration
```bash
# Test configuration syntax
python -c "
from app.main import load_app_config
from pathlib import Path
try:
    config = load_app_config(Path('config/my_agents.yaml'))
    print('Configuration is valid!')
    print(f'Found {len(config.agents)} agents')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

### List Available Agents
```bash
curl http://localhost:8000/ | jq '.available_agents'
```

## Integration Examples

### Web Application Integration
```javascript
// JavaScript example for web applications
async function queryAgents(input, configPath = null) {
  const response = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: input,
      config_path: configPath,
      raw_output: false
    })
  });

  return await response.json();
}

// Usage
const result = await queryAgents("Analyze market trends");
console.log(result.response);
```

### Python Client Example
```python
import requests
from typing import Optional, Dict, Any

class JKAgentsClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')

    def query(self, input_text: str, config_path: Optional[str] = None,
              raw_output: bool = False) -> Dict[str, Any]:
        """Send a query to the multi-agent system."""
        response = requests.post(
            f"{self.base_url}/query",
            json={
                "input": input_text,
                "config_path": config_path,
                "raw_output": raw_output
            }
        )
        response.raise_for_status()
        return response.json()

    def run_agent(self, agent_name: str, input_text: str,
                  config_path: Optional[str] = None) -> Dict[str, Any]:
        """Run a specific agent directly."""
        response = requests.post(
            f"{self.base_url}/worker",
            json={
                "agent_name": agent_name,
                "input": input_text,
                "config_path": config_path
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = JKAgentsClient()
result = client.query("What are the benefits of renewable energy?")
print(result['response'])
```

## Next Steps

- Explore specific integrations: [MCP Integration](mcp_integration_and_llm_logging.md)
- Set up Python function tools: [Python Function Tools](PYTHON_FUNCTION_TOOLS.md)
- Configure multiple providers: [Multi-Provider Setup](MULTI_PROVIDER_SETUP.md)
- API reference: [API Documentation](API_DOCUMENTATION.md)
- File upload capabilities: [File Upload API](FILE_UPLOAD_API.md)
