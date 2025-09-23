# Configuration System Guide

## Overview

The jk-agents-framework uses YAML configuration files to define agents, models, and system behavior. The configuration system is highly flexible, supporting multiple LLM providers, specialized agents, and complex orchestration scenarios.

## Configuration File Structure

```yaml
models:              # Model definitions and mappings
business_context:    # Shared context for all agents
persistence:         # Memory and checkpointing settings
supervisor:          # Supervisor agent configuration
agents:              # List of specialized agents
```

## Model Configuration

### Model Providers

The framework supports multiple LLM providers that can be used simultaneously:

#### OpenAI
```yaml
models:
  default: "openai:gpt-4o-mini"
  reasoning: "openai:gpt-4o"
  fast: "openai:gpt-3.5-turbo"
```

#### Azure OpenAI
```yaml
models:
  default: "azure_openai:gpt-4o-mini"
  supervisor: "azure_openai:gpt-4"
  production: "azure_openai:deployment-name"
```

#### Google Gemini
```yaml
models:
  default: "google:gemini-2.0-flash-exp"
  multimodal: "google:gemini-2.0-flash-lite-001"
  pro: "google:gemini-1.5-pro"
```

#### Anthropic Claude
```yaml
models:
  default: "anthropic:claude-sonnet-4-20250514"
  opus: "anthropic:claude-opus-4-20250514"
```

#### Local LM Studio
```yaml
models:
  local_dev: "openai:llama-3.2-3b"
  experimental: "openai:microsoft/phi-3.5-mini"
```

### Temperature Configuration

Temperature can be set globally or per model:

```yaml
models:
  default: "google:gemini-2.0-flash-exp"
  temperature: 0.1  # Global temperature

  # Or embedded in model ID
  creative: "google:gemini-2.0-flash-exp:0.8"
  precise: "azure_openai:gpt-4o:0.0"
```

### Multi-Provider Setup

Example configuration using multiple providers:

```yaml
models:
  # Production: Azure OpenAI
  default: "azure_openai:gpt-4o-mini"
  supervisor: "azure_openai:gpt-4o"
  
  # Development: Local LM Studio
  local_dev: "openai:google/gemma-3n-e4b"
  local_test: "openai:llama-3.2-3b"
  
  # Multimodal: Google Gemini
  vision: "google:gemini-2.0-flash-exp"
  
  # Advanced reasoning: Anthropic
  analysis: "anthropic:claude-sonnet-4"
```

## Business Context

Shared context injected into all agent prompts:

```yaml
business_context: |
  You are part of an industrial automation system for manufacturing quality control.
  Focus on accuracy, safety, and regulatory compliance in all responses.
  Use technical terminology appropriate for manufacturing engineers.
```

## Persistence Configuration

Memory and checkpointing settings:

```yaml
persistence:
  type: "memory"           # Current supported type
  # Future: sqlite, redis, etc.
```

## Supervisor Configuration

The supervisor agent orchestrates task execution:

```yaml
supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4o"         # Override default model
  prompt: |                            # Inline prompt
    Business context: {{business_context}}
    Available agents: {{agents}}
    
    Create execution plans by breaking tasks into steps.
    Assign steps to appropriate specialized agents.
    
    Return JSON plan with:
    {
      "goal": "user goal summary",
      "plan": [
        {"id": "s1", "agent": "agent_name", "task": "specific task", 
         "depends_on": [], "timeout_seconds": 60, "retry": 2}
      ]
    }
  
  # Alternative: External prompt file
  prompt_file: "config/prompts/supervisor_prompt.txt"
```

## Agent Configuration

Agents are specialized for specific tasks and domains:

### Basic Agent Structure

```yaml
agents:
  - name: "agent_name"
    description: "Brief description of agent capabilities"
    model: "google:gemini-2.0-flash-exp"  # Override default model
    prompt: |
      Agent-specific prompt with specialized instructions
    
    # Tool integration (optional)
    mcp_servers: {}
    http_tools: {}
    python_tools: {}
```

### Agent Types and Examples

#### 1. Data Analysis Agent

```yaml
- name: "data_analyst"
  description: "Analyzes CSV data and generates business insights"
  model: "google:gemini-2.0-flash-lite-001"
  prompt: |
    You are a data analysis expert specializing in CSV data processing.
    
    Capabilities:
    - Statistical analysis and pattern recognition
    - Data quality assessment
    - Business insight generation
    - Visualization recommendations
    
    Always provide actionable recommendations based on data findings.
  
  mcp_servers:
    python_runner:
      transport: "stdio"
      command: "deno"
      args: ["run", "-N", "jsr:@pydantic/mcp-run-python"]
```

#### 2. Web Research Agent

```yaml
- name: "web_researcher"
  description: "Performs web research and information gathering"
  model: "azure_openai:gpt-4o-mini"
  prompt: |
    You are a web research specialist with access to search capabilities.
    
    Research Process:
    1. Search for current, authoritative sources
    2. Cross-reference information across multiple sources
    3. Summarize findings with proper citations
    4. Identify knowledge gaps or conflicting information
    
    Always cite sources and indicate information freshness.
  
  mcp_servers:
    websearch:
      transport: "streamable_http"
      url: "http://localhost:8000/mcp"
```

#### 3. Code Execution Agent

```yaml
- name: "python_executor"
  description: "Executes Python code for computational tasks"
  model: "azure_openai:gpt-4.1"
  prompt: |
    You are CodeRunner with Python execution capabilities.
    
    CRITICAL RULES:
    - ALWAYS use the run_python_code tool for computational tasks
    - Write clear, well-documented code
    - Handle errors gracefully and retry once if needed
    - Show both code and execution results
    
    Available tools: {{mcpservers}}
  
  mcp_servers:
    python_runner:
      description: "Python code execution environment"
      transport: "stdio"
      command: "deno"
      args: ["run", "-N", "jsr:@pydantic/mcp-run-python", "stdio"]
```

#### 4. Multimodal Analysis Agent

```yaml
- name: "multimodal_analyzer"
  description: "Processes text, images, and documents"
  model: "google:gemini-2.0-flash-exp"
  prompt: |
    You are a multimodal AI with vision and document analysis capabilities.
    
    Analysis Process:
    1. Identify content types (text, images, charts, documents)
    2. Extract and process information from each modality
    3. Synthesize insights across different content types
    4. Provide comprehensive analysis with specific details
    
    Be thorough and cite specific elements from visual content.
  
  mcp_servers: {}
```

#### 5. Industrial Domain Agent

```yaml
- name: "factory_maintenance_expert"
  description: "Processes factory maintenance reports and equipment issues"
  model: "google:gemini-2.0-flash-lite-001"
  prompt: |
    You are a factory maintenance expert specializing in industrial equipment.
    
    Expertise:
    - Machinery diagnostics (motors, cranes, cutting equipment)
    - Root cause analysis for equipment failures
    - Corrective action recommendations
    - Maintenance scheduling and planning
    
    Process Hindi-English maintenance reports, correcting grammar and
    transliteration issues while preserving technical accuracy.
    
    Input format: CSV with maintenance records
    Output: Structured analysis with corrected descriptions
```

## Tool Integration

### MCP Servers

Model Context Protocol servers provide extensible tool capabilities:

```yaml
mcp_servers:
  server_name:
    description: "What this server provides"
    transport: "stdio"          # stdio | streamable_http | sse
    command: "python"           # For stdio
    args: ["script.py"]         # Command arguments
    env:                        # Environment variables
      API_KEY: "{{secret}}"
    
    # For HTTP/SSE servers
    url: "http://localhost:8000/mcp"
    headers:
      Authorization: "Bearer {{token}}"
```

#### Popular MCP Servers

```yaml
# Python execution
python_runner:
  transport: "stdio"
  command: "deno"
  args: ["run", "-N", "jsr:@pydantic/mcp-run-python", "stdio"]

# Web search (Brave)
websearch:
  transport: "streamable_http"
  url: "http://localhost:8000/mcp"

# File operations
filesystem:
  transport: "stdio"
  command: "mcp-server-filesystem"
  args: ["--root", "/workspace"]

# Database access
database:
  transport: "stdio"
  command: "mcp-server-sqlite"
  args: ["--db", "data/database.sqlite"]
```

### HTTP Tools

Simple HTTP endpoints as tools:

```yaml
http_tools:
  api_call:
    url: "https://api.example.com/endpoint"
    method: "POST"
    headers:
      Authorization: "Bearer {{token}}"
      Content-Type: "application/json"
```

### Python Function Tools

Load custom Python functions as tools:

```yaml
python_tools:
  custom_functions:
    module_path: "tools.custom_tools"
    function_name: "specific_function"  # Optional
    tool_names: ["tool1", "tool2"]     # Optional list
    description: "Custom tool set for specialized processing"
```

## Advanced Configuration Patterns

### Environment-Based Configuration

Use different configurations for different environments:

```yaml
# config/development.yaml
models:
  default: "openai:gpt-4o-mini"
  local_test: "openai:llama-3.2-3b"

# config/production.yaml  
models:
  default: "azure_openai:gpt-4o"
  supervisor: "azure_openai:gpt-4"
```

### Prompt File References

Store prompts in separate files for maintainability:

```yaml
supervisor:
  name: "supervisor"
  prompt_file: "config/prompts/supervisor_v2.txt"

agents:
  - name: "specialist"
    prompt_file: "config/prompts/domain_expert.md"
```

### Template Variables in Prompts

Use Jinja2 templating for dynamic prompts:

```yaml
business_context: |
  Company: {{company_name}}
  Department: {{department}}
  Date: {{current_date}}

agents:
  - name: "agent"
    prompt: |
      Business context: {{business_context}}
      Original question: {{original_user_question}}
      Previous responses: {{dependent_request_responses}}
      Available tools: {{mcpservers}}
```

### Conditional Agent Selection

Configure agents for different scenarios:

```yaml
agents:
  # Fast response for simple queries
  - name: "quick_responder"
    model: "openai:gpt-3.5-turbo:0.0"
    description: "Fast responses for simple questions"
    
  # Deep analysis for complex queries  
  - name: "deep_analyzer"
    model: "anthropic:claude-sonnet-4:0.1"
    description: "Comprehensive analysis for complex problems"
    
  # Multimodal for image/document processing
  - name: "vision_processor"
    model: "google:gemini-2.0-flash-exp"
    description: "Processes images, documents, and multimodal content"
```

## Validation and Best Practices

### Configuration Validation

The framework validates configurations at startup:

- Required fields (prompt or prompt_file)
- Model ID format validation
- MCP server transport requirements
- Tool configuration completeness

### Best Practices

1. **Model Selection**:
   - Use appropriate models for task complexity
   - Consider cost vs. performance trade-offs
   - Test with different providers for comparison

2. **Prompt Engineering**:
   - Be specific about agent roles and capabilities
   - Include examples for complex tasks
   - Use templates for consistent formatting

3. **Tool Integration**:
   - Start with simple MCP servers
   - Test tool functionality independently
   - Handle tool failures gracefully

4. **Performance Optimization**:
   - Use faster models for simple tasks
   - Cache frequently used information
   - Monitor execution times and adjust timeouts

5. **Security**:
   - Use environment variables for secrets
   - Validate tool inputs and outputs
   - Implement proper error handling

## Configuration Examples

### Simple Configuration
```yaml
models:
  default: "openai:gpt-4o-mini"

business_context: "You are a helpful AI assistant."

supervisor:
  name: "supervisor"
  prompt: |
    Create simple plans using available agents: {{agents}}
    Return JSON format only.

agents:
  - name: "general_assistant"
    description: "General purpose assistant"
    prompt: "You are a helpful assistant. Answer questions clearly and accurately."
    mcp_servers: {}
```

### Production Configuration
See the `config/multi_provider_example.yaml` file for a complete production-ready configuration with multiple providers, specialized agents, and comprehensive tool integration.

## Troubleshooting

### Common Issues

1. **Model Not Found**: Check model ID format and provider configuration
2. **MCP Server Failed**: Verify command paths and permissions
3. **Prompt Rendering Error**: Check template syntax and variable names
4. **Tool Execution Timeout**: Increase timeout values or optimize tools
5. **Memory Issues**: Configure checkpointer and cleanup strategies

### Debug Configuration

Enable verbose logging for configuration debugging:

```yaml
# In .env file
LANGCHAIN_VERBOSE=true
LOG_LEVEL=DEBUG
```