# Azure OpenAI Reference Configuration

## Overview

The `config/azure_openai_reference.yaml` file provides a comprehensive, fully-tested reference configuration for the jk-agents system using Azure OpenAI GPT-4.1 models with various agent types and integrations.

## Configuration Details

### Models
- **Primary Model**: `azure_openai:gpt-4.1`
- **Supervisor Model**: `azure_openai:gpt-4.1`
- **Temperature**: `0.0` (deterministic responses)

### Agent Architecture

#### 1. Test Agent (`test_agent`)
- **Purpose**: Basic validation and simple tasks without external dependencies
- **Capabilities**: Direct question answering, basic math with step-by-step explanations
- **Dependencies**: None
- **Use Case**: Fallback agent and basic functionality testing

#### 2. Python Execution Agent (`python_exec_agent`)
- **Purpose**: Execute Python code using MCP (Model Context Protocol) server
- **Capabilities**: 
  - Write and execute Python code
  - Show both code and execution results
  - Handle computational tasks
  - Error handling and retry logic
- **Dependencies**: Deno-based MCP Python runner
- **MCP Server**: `@pydantic/mcp-run-python` via stdio transport

#### 3. Math Agent (`math_agent`)
- **Purpose**: Precise arithmetic calculations using local HTTP service
- **Capabilities**:
  - Extract numbers from previous responses
  - Perform calculations via HTTP API
  - Graceful fallback to manual calculation
  - Structured result formatting
- **Dependencies**: Local HTTP service at `http://localhost:8001/calculate`
- **HTTP Tool**: GET request with expression parameter

#### 4. Human Response Agent (`human_response_agent`)
- **Purpose**: Final response synthesis and presentation
- **Capabilities**:
  - Natural language response formatting
  - Code and result preservation
  - Multi-step synthesis
  - Citation handling
- **Dependencies**: None

### Supervisor Configuration

The supervisor uses intelligent task decomposition with:
- **Goal-oriented planning**: Clear objective identification
- **Dependency management**: Proper task sequencing
- **Verification steps**: Quality assurance for each step
- **Agent selection**: Optimal agent matching for tasks

## Test Results

### ✅ Verified Functionality

#### Basic Operations
```bash
# Test: Basic functionality
curl --location 'http://localhost:8000/query/form' \
--form 'input="Hello, test basic functionality"' \
--form 'config_path="config\\azure_openai_reference.yaml"'

# Result: ✅ Success - System responds correctly
```

#### Mathematical Calculations
```bash
# Test: Simple arithmetic
curl --location 'http://localhost:8000/query/form' \
--form 'input="What is 15 + 27?"' \
--form 'config_path="config\\azure_openai_reference.yaml"'

# Result: ✅ Success - Returns "42" with proper explanation
```

#### Python Code Execution
```bash
# Test: Python MCP execution
curl --location 'http://localhost:8000/query/form' \
--form 'input="Write Python code to calculate the factorial of 5"' \
--form 'config_path="config\\azure_openai_reference.yaml"'

# Result: ✅ Success - Shows code and execution result (120)
```

#### HTTP Tool Integration
```bash
# Test: Local HTTP service
curl --location 'http://localhost:8000/query/form' \
--form 'input="Calculate 25 * 8 using the math service"' \
--form 'config_path="config\\azure_openai_reference.yaml"'

# Result: ✅ Success - Returns "200" via HTTP service
```

#### Complex Multi-Agent Workflows
```bash
# Test: Multi-agent coordination
curl --location 'http://localhost:8000/query/form' \
--form 'input="Write Python code to calculate 7 factorial, then verify the result using the math service"' \
--form 'config_path="config\\azure_openai_reference.yaml"'

# Result: ✅ Success - Coordinates Python execution and HTTP verification
```

## Dependencies

### Required Services

1. **Azure OpenAI Service**
   - Endpoint configured in environment
   - GPT-4.1 model deployment
   - Valid API credentials

2. **Deno Runtime** (for Python MCP)
   - Deno installed and accessible
   - Network access for JSR packages
   - Node modules directory permissions

3. **Local Math Service** (optional)
   - HTTP service at `http://localhost:8001/calculate`
   - GET endpoint accepting `expression` parameter
   - JSON response with `result` field

### Environment Setup

```bash
# Install Deno (if not already installed)
# Windows: 
# iwr https://deno.land/install.ps1 -useb | iex

# Verify Deno installation
deno --version

# Test MCP Python runner
deno run -N -R=node_modules -W=node_modules --node-modules-dir=auto jsr:@pydantic/mcp-run-python stdio
```

## Usage Examples

### Simple Query
```python
import requests

response = requests.post('http://localhost:8000/query/form', data={
    'input': 'What is 12 * 15?',
    'config_path': 'config\\azure_openai_reference.yaml'
})
print(response.json())
```

### Python Execution
```python
response = requests.post('http://localhost:8000/query/form', data={
    'input': 'Write Python code to find the sum of squares from 1 to 10',
    'config_path': 'config\\azure_openai_reference.yaml'
})
print(response.json()['response'])
```

### Complex Analysis
```python
response = requests.post('http://localhost:8000/query/form', data={
    'input': 'Calculate the compound interest for $1000 at 5% for 3 years using Python, then verify the final amount',
    'config_path': 'config\\azure_openai_reference.yaml'
})
print(response.json()['response'])
```

## Troubleshooting

### Common Issues

1. **MCP Connection Failures**
   - Ensure Deno is installed and accessible
   - Check network permissions for JSR package access
   - Verify node_modules directory permissions

2. **HTTP Tool Failures**
   - Confirm local math service is running on port 8001
   - Test service directly: `curl "http://localhost:8001/calculate?expression=2+2"`
   - Check firewall settings

3. **Azure OpenAI Errors**
   - Verify API credentials and endpoint configuration
   - Check model deployment status
   - Confirm rate limits and quotas

### Error Messages

- **"All connection attempts failed"**: External service unavailable
- **"Invalid model configuration"**: Check model names in YAML
- **"MCP server not responding"**: Deno or network issues
- **"HTTP tool timeout"**: Local service not running

## Best Practices

1. **Model Consistency**: Use the same model across all agents for predictable behavior
2. **Error Handling**: Always include verification steps and fallback mechanisms
3. **Resource Management**: Monitor external service dependencies
4. **Testing**: Validate each agent type individually before complex workflows
5. **Documentation**: Keep configuration comments up-to-date

## Next Steps

1. **Scale Testing**: Test with larger, more complex workflows
2. **Performance Optimization**: Monitor response times and optimize prompts
3. **Additional Integrations**: Add more MCP servers and HTTP tools
4. **Error Recovery**: Implement more sophisticated retry and fallback logic
5. **Monitoring**: Add comprehensive logging and metrics collection
