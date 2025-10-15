# AI Model Configuration Builder Instructions

## Overview

This document provides comprehensive instructions for AI models to build reliable, high-performance configuration files for the jk-agents-framework. These instructions are based on extensive analysis of production systems, performance testing, conversation continuity optimizations, and the latest enhancements to the framework's placeholder system and multi-provider integration.

## Core Principles

### 1. RELIABILITY FIRST
- **Always validate configuration syntax** before deployment
- **Test memory systems** with simple scenarios before complex ones  
- **Use proven model combinations** (Azure OpenAI GPT-4.1 is most stable)
- **Implement proper error handling** in all agent prompts

### 2. PERFORMANCE OPTIMIZATION
- **Enable preloading** for frequently used configurations
- **Use connection pooling** for ChromaDB when memory is enabled
- **Set appropriate timeouts** (60s for complex tasks, 30s for simple ones)
- **Optimize batch sizes** (max 200 items for external APIs)

### 3. CONVERSATION CONTINUITY
- **Place context instructions at the beginning** of each agent prompt
- **Use explicit prioritization language** (MUST, PRIORITIZE, BUILD UPON)
- **Maintain data consistency** across conversation turns
- **Never generate new data** when existing conversation data is available
- **Use turn tracking system** with `[Turn-X]` format for better context awareness

### 4. ENHANCED PLACEHOLDER SYSTEM
- **Leverage dynamic placeholders** for context-aware prompts
- **Use default values** with pipe syntax `{{placeholder|default("value")}}`
- **Apply placeholder providers** (System, Agent, Context, User)
- **Ensure placeholder validation** for all templates

## Step-by-Step Configuration Building

### STEP 1: Analyze User Requirements

Before building any configuration, analyze:

1. **Task Complexity**: 
   - Simple tasks: Use memory-disabled config for speed
   - Complex tasks: Enable memory for continuity
   - Multi-step tasks: Use supervisor with multiple agents

2. **Performance Requirements**:
   - Real-time responses: Disable memory, use preloading
   - Conversational AI: Enable memory with ChromaDB
   - Batch processing: Use high connection limits

3. **Data Sources**:
   - Python execution: Include python_exec_agent
   - Web search: Add web search tools
   - File operations: Include file handling agents
   - API integration: Configure MCP servers

### STEP 2: Select Base Template

Choose based on use case:

```yaml
# HIGH-PERFORMANCE (for speed-critical applications)
memory:
  enabled: false
models:
  default: "azure_openai:gpt-4.1"
  temperature: 0.1

# CONVERSATIONAL (for multi-turn interactions)  
memory:
  backend: "chromadb"
  chromadb:
    max_connections: 20
    l1_cache_size: 5000
    enable_batch_processing: true

# COMPLEX WORKFLOWS (for multi-agent orchestration)
supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
agents:
  - name: "specialized_agent"
  - name: "python_exec_agent" 
  - name: "human_response_agent"
```

### STEP 3: Configure Models Section

**CRITICAL: Always use proven model combinations**

```yaml
models:
  default: "azure_openai:gpt-4.1"      # Most reliable for production
  supervisor: "azure_openai:gpt-4.1"   # Consistent planning decisions
  temperature: 0.1                     # Lower for consistency, higher for creativity
  fallback: "openai:gpt-4o-mini"       # Optional fallback model
```

**Model Selection Guidelines:**
- **Azure OpenAI GPT-4.1**: Best reliability, performance, tool calling
- **Google Gemini 2.5-flash-lite**: Good for creative tasks, disable parallel_tool_calls
- **OpenAI GPT-4o**: Alternative to Azure, requires different configuration
- **Anthropic Claude**: Excellent for long-form content generation
- **LM Studio**: Local models for development and offline use
- **Temperature**: 0.1 for analytical tasks, 0.3-0.7 for creative tasks

### STEP 4: Configure Memory System

**For HIGH-PERFORMANCE scenarios (no memory):**
```yaml
memory:
  enabled: false
conversation_memory:
  enabled: false
```

**For CONVERSATIONAL scenarios (with memory):**
```yaml
memory:
  backend: "chromadb"
  chromadb:
    path: "./production_memory"
    host: "localhost"
    port: 8000
    # HIGH-PERFORMANCE SETTINGS
    max_connections: 20
    min_connections: 5
    connection_timeout: 30.0
    # CACHING OPTIMIZATION  
    l1_cache_size: 5000
    l1_cache_ttl: 1800  # 30 minutes
    # BATCH PROCESSING
    batch_size: 100
    batch_timeout: 0.1
    enable_batch_processing: true
    enable_metrics: true
    # COLLECTIONS
    checkpoint_collection: "main-session"
    context_collection: "main-context"
```

### STEP 5: Build Business Context

Create compelling context that drives behavior:

```yaml
business_context: |
  **SYSTEM IDENTITY**: [Define clear role and mission]
  
  **CRITICAL RULES**:
  - AUTHENTICITY: Never create fictional data or examples
  - ACCURACY: Always validate information before presenting
  - CONSISTENCY: Maintain context across conversation turns
  
  **CURRENT SESSION**: {{datetime}} ({{day_name}})
  
  **PERFORMANCE REQUIREMENTS**:
  - Response time target: [specify timeframe]
  - Data sources: [list approved sources]
  - Output format: [specify requirements]
```

### STEP 6: Configure Supervisor (for multi-agent systems)

**CRITICAL: Place conversation context instructions FIRST**

```yaml
supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: |
    **CONVERSATION CONTEXT PRIORITY**: 
    If the user input contains "Previous conversation context:" with data from earlier interactions, 
    you MUST prioritize that existing data in your planning. Use that data as the foundation for 
    your plan instead of generating new data. Build upon previous interactions to maintain continuity.
    
    Business context (do not reveal to user):
    {{business_context}}
    
    You are a supervisor that creates execution plans using available agents.
    Available agents: {{agents}}
    
    Create a JSON plan with steps that can run in parallel where possible.
    
    Return only JSON, with top-level object:
    {
      "goal": "<short restatement of user goal>",
      "plan": [
        {
          "id": "s1", 
          "agent": "appropriate_agent", 
          "task": "specific task description", 
          "depends_on": [], 
          "verify": "success criteria", 
          "timeout_seconds": 60, 
          "retry": 2
        }
      ]
    }
```

### STEP 7: Choose Agent Types (React vs Normal)

**CRITICAL: Select appropriate agent type based on functionality requirements**

The framework supports two agent types:

#### Agent Type Options

**React Agent (`agent_type: "react"`):**
- **Capabilities**: Full tool calling, ReAct reasoning pattern
- **Use Cases**: Computational tasks, API calls, code execution, data processing
- **Performance**: Variable (depends on tool usage)
- **Resource Usage**: Higher (tool loading, execution overhead)

**Normal Agent (`agent_type: "normal"`):**
- **Capabilities**: Pure conversational responses only
- **Use Cases**: Response formatting, conversation, knowledge queries
- **Performance**: Faster and more consistent
- **Resource Usage**: Lower (no tool overhead)

#### Agent Type Selection Guidelines

```yaml
# REACT AGENTS - Use for computational/action-oriented tasks
- name: "python_exec_agent"
  agent_type: "react"           # Needs tools for code execution
  description: "Execute Python code and calculations"
  
- name: "data_processor"
  agent_type: "react"           # Needs tools for data manipulation
  description: "Process and analyze datasets"
  
- name: "api_integrator"
  agent_type: "react"           # Needs tools for external API calls
  description: "Integrate with external services"

# NORMAL AGENTS - Use for conversational/formatting tasks
- name: "human_response_agent"
  agent_type: "normal"          # No tools needed, faster execution
  description: "Format final responses for users"
  
- name: "conversation_agent"
  agent_type: "normal"          # Pure conversation, no external actions
  description: "Handle user interactions and dialogue"
  
- name: "content_formatter"
  agent_type: "normal"          # Text processing only, no tools required
  description: "Format and structure content"
```

#### Backward Compatibility

```yaml
# AUTOMATIC DEFAULTING - If agent_type is not specified
- name: "legacy_agent"
  # No agent_type specified - automatically defaults to "react"
  description: "Existing configurations continue to work unchanged"
```

### STEP 8: Configure Agents with Context Awareness

**For Python Execution Agent (React Type):**
```yaml
agents:
  - name: "python_exec_agent"
    description: "Execute Python code with guaranteed tool calling support"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"  # Uses ReAct pattern with tool calling capabilities
    prompt: |
      {{dependent_request_responses}}

      **CONVERSATION CONTEXT PROCESSING**:
      BEFORE starting any computational task, check if the user input contains "Previous conversation context:" 
      with data from earlier interactions. If present:
      1. PRIORITIZE that existing data as your primary input source
      2. DO NOT generate new data when existing conversation data is available
      3. Build upon and extend the previous conversation data
      4. Maintain data consistency across conversation turns

      You are CodeRunner. You MUST write and execute Python code using the run_python_code tool.

      **IMPORTANT**: If the user input contains "Previous conversation context:" with data from earlier interactions, USE THAT DATA as input instead of generating new data

      EXECUTION RULES:
      - ALWAYS use the run_python_code tool - never just describe
      - Write the code first, then execute using the tool
      - Show both code and execution result
      - Use previous step data when appropriate
      - If execution fails, fix and retry once

      Available MCP servers: {{mcpservers}}
```

**For Human Response Agent (Normal Type):**
```yaml
  - name: "human_response_agent"
    description: "Final response formatter"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"  # Uses normal conversational pattern without tool calling
    prompt: |
      {{dependent_request_responses}}
      
      **CONVERSATION CONTINUITY PRIORITY**:
      Check if previous conversation context is available. If present, you MUST:
      1. Acknowledge the context and build upon previous interactions
      2. Maintain data consistency across conversation turns
      3. Reference previous results when relevant to current response
      4. Avoid treating each request as an isolated interaction
      
      **IMPORTANT**: If the user input contains "Previous conversation context:" with data from earlier interactions, USE THAT DATA as input instead of generating new data
      
      Present a clear, natural answer based on previous agent responses.
      Format information in a user-friendly way without revealing internal processes.
```

### STEP 9: Add Tool Integration (MCP Servers, Python Tools, HTTP Tools)

#### MCP Servers Configuration

MCP (Model Context Protocol) servers provide external tool capabilities. Configure based on transport type:

**STDIO Transport (Local Commands):**
```yaml
    mcp_servers:
      python_runner:
        description: "Run Python code via Deno + @pydantic/mcp-run-python (stdio)"
        transport: "stdio"
        command: "deno"
        args:
          - "run"
          - "-N"
          - "-R=node_modules"
          - "-W=node_modules"
          - "--node-modules-dir=auto"
          - "jsr:@pydantic/mcp-run-python"
          - "stdio"
      
      git_operations:
        description: "Git repository operations"
        transport: "stdio"
        command: "uvx"
        args:
          - "mcp-server-git"
          - "--repository"
          - "/path/to/repo"
```

**HTTP Transport (Remote Services):**
```yaml
    mcp_servers:
      brave_search:
        description: "Web search via Brave Search API"
        transport: "http"
        url: "http://localhost:3001"
        
      weather_service:
        description: "Weather data API"
        transport: "http"
        url: "http://localhost:3002"
        headers:
          Authorization: "Bearer ${WEATHER_API_KEY}"
```

**Azure DevOps MCP Server:**
```yaml
    mcp_servers:
      ado_server:
        description: "Azure DevOps API integration"
        transport: "stdio"
        command: "node"
        args:
          - "ado-mcp-server/index.js"
        env:
          ADO_ORG_URL: "https://dev.azure.com/yourorg"
          ADO_PAT: "${ADO_PERSONAL_ACCESS_TOKEN}"
```

#### Python Tools Configuration

Python function tools allow direct Python function integration:

```yaml
    python_tools:
      - module: "custom_tools.math_utils"
        functions: ["calculate_compound_interest", "statistical_analysis"]
        description: "Advanced mathematical calculations"
        
      - module: "data_processing.transformers"
        functions: ["clean_dataset", "normalize_data"]
        description: "Data cleaning and transformation utilities"
        
      - file: "./tools/business_logic.py"
        functions: ["validate_business_rules", "generate_report"]
        description: "Business-specific validation and reporting"
```

**Python Tool File Structure:**
```python
# ./tools/business_logic.py
def validate_business_rules(data: dict) -> dict:
    """Validate data against business rules."""
    # Implementation here
    return {"valid": True, "errors": []}

def generate_report(data: list) -> str:
    """Generate formatted business report."""
    # Implementation here
    return "Report content"
```

#### HTTP Tools Configuration

HTTP tools provide direct REST API integration:

```yaml
    http_tools:
      - name: "get_user_profile"
        method: "GET"
        url: "https://api.example.com/users/{user_id}"
        headers:
          Authorization: "Bearer ${API_TOKEN}"
          Content-Type: "application/json"
        description: "Retrieve user profile information"
        
      - name: "create_ticket"
        method: "POST"
        url: "https://ticketing.example.com/api/tickets"
        headers:
          Authorization: "Bearer ${TICKET_API_KEY}"
        body_template: |
          {
            "title": "{title}",
            "description": "{description}",
            "priority": "{priority}"
          }
        description: "Create support ticket"
        
      - name: "send_notification"
        method: "POST"
        url: "https://notifications.example.com/send"
        headers:
          X-API-Key: "${NOTIFICATION_API_KEY}"
        description: "Send push notification"
```

#### Tool Selection Guidelines

**Use MCP Servers when:**
- Need complex, stateful operations
- Require process isolation
- External service integration
- Need persistent connections

**Use Python Tools when:**
- Simple, stateless functions
- Direct Python library access needed
- Custom business logic
- High-performance local operations

**Use HTTP Tools when:**
- Simple REST API calls
- One-off external requests
- No complex authentication flows
- Stateless operations only

## Performance Optimization Patterns

### High-Performance Configuration Template

```yaml
# OPTIMIZED FOR SPEED - Use for production APIs
models:
  default: "azure_openai:gpt-4.1"
  temperature: 0.1

# DISABLE MEMORY FOR MAXIMUM SPEED
memory:
  enabled: false
conversation_memory:
  enabled: false

business_context: |
  You are a high-performance AI system optimized for speed and accuracy.
  Response time target: <5 seconds for simple tasks, <15 seconds for complex tasks.

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: |
    Create efficient execution plans with minimal overhead.
    Prioritize parallel execution where possible.
    Set timeouts: 30s for simple tasks, 60s for complex tasks.

agents:
  - name: "python_exec_agent"
    model: "azure_openai:gpt-4.1"
    # CRITICAL: Streamlined prompt for speed
    prompt: |
      {{dependent_request_responses}}
      
      **IMPORTANT**: If the user input contains "Previous conversation context:" with data from earlier interactions, USE THAT DATA as input instead of generating new data
      
      Execute Python code efficiently using run_python_code tool.
      Write concise, optimized code. Show code and results.
```

### Memory-Enabled Configuration Template

```yaml
# OPTIMIZED FOR CONVERSATION CONTINUITY
models:
  default: "azure_openai:gpt-4.1"
  temperature: 0.1

# ADVANCED MEMORY CONFIGURATION
memory:
  backend: "chromadb"
  chromadb:
    path: "./conversation_memory"
    max_connections: 20
    l1_cache_size: 5000
    enable_batch_processing: true

# CONTEXT-AWARE SUPERVISOR
supervisor:
  prompt: |
    **CONVERSATION CONTEXT PRIORITY**: 
    If the user input contains "Previous conversation context:" with data from earlier interactions, 
    prioritize that existing data in your planning.
    
    [rest of supervisor prompt]

# CONTEXT-AWARE AGENTS
agents:
  - name: "python_exec_agent"
    prompt: |
      **CONVERSATION CONTEXT PROCESSING**:
      Check for "Previous conversation context:" before starting tasks.
      If present: 1) Prioritize existing data 2) Build upon it 3) Maintain consistency
      
      [rest of agent prompt]
```

## Reliability Best Practices

### 1. Error Handling Patterns

```yaml
supervisor:
  prompt: |
    If any step fails:
    1. Analyze the error cause
    2. Attempt automatic recovery where possible
    3. Provide clear error messages to user
    4. Never leave tasks in incomplete state
    
    Timeout handling:
    - Simple tasks: 30 seconds
    - Complex tasks: 60 seconds  
    - External API calls: 45 seconds
```

### 2. Model Fallback Configuration

```yaml
models:
  default: "azure_openai:gpt-4.1"
  fallback: "azure_openai:gpt-4o-mini"  # Cost-effective backup
  temperature: 0.1
```

### 3. Resource Management

```yaml
# CONNECTION LIMITS
memory:
  chromadb:
    max_connections: 20      # Prevent connection exhaustion
    connection_timeout: 30.0 # Prevent hanging connections
    
# BATCH PROCESSING LIMITS  
supervisor:
  prompt: |
    BATCH PROCESSING RULES:
    - Maximum 200 items per external API call
    - Implement 2-second delays between consecutive API calls
    - Use pagination for large datasets
```

## Placeholder System Integration

### 1. Built-in Placeholder Providers

The framework includes several placeholder providers that you can use in your configurations:

```yaml
# System Information Placeholders
- Current time: {{timestamp}}            # Current ISO timestamp
- Platform: {{platform}}                # OS platform (Windows/macOS/Linux)
- Python version: {{python_version}}    # Python interpreter version
- Working directory: {{working_directory}}   # Current working directory

# Agent Information Placeholders
- Agent name: {{agent_name}}            # Current agent name
- Agent description: {{agent_description}}   # Agent description
- Model: {{agent_model}}                # AI model being used

# Context Information Placeholders
- Business context: {{business_context}}         # Business context string
- Original question: {{original_user_question}}  # User's original query
- Available MCP servers: {{mcpservers}}          # Available MCP servers list
- Available agents: {{agents}}                   # List of all available agents with descriptions
- Conversation metadata: {{conversation_context_metadata}}  # Dynamic conversation analysis

# Custom Placeholders with Defaults
- User name: {{user_name|default("Not specified")}}
- Project name: {{project_name|default("Default Project")}}
- Priority level: {{priority|default("normal")}}
- Department: {{department|default("General")}}
```

### 2. Placeholder Resolution Flow

Placeholders are resolved in this sequence:

```text
Template Request → PlaceholderContext → Registry Lookup → Provider Resolution → Value Substitution
       ↓                ↓                    ↓                   ↓                    ↓
User Input → Context Building → Provider Selection → Value Generation → Rendered Template
```

## Common Configuration Patterns

### Pattern 1: Simple Python Execution (High Performance)
**Use case**: API endpoints, quick calculations, single-turn interactions

```yaml
models:
  default: "azure_openai:gpt-4.1"
  temperature: 0.1

memory:
  enabled: false

agents:
  - name: "python_exec_agent"
    agent_type: "react"  # Needs tools for code execution
    prompt: |
      Execute Python code using run_python_code tool.
      Provide concise, accurate results.
  - name: "human_response_agent"
    agent_type: "normal"  # No tools needed, faster response formatting
    prompt: |
      Format results clearly for the user.
```

### Pattern 2: Conversational AI (Memory Enabled)
**Use case**: Multi-turn conversations, context building, learning systems

```yaml
models:
  default: "azure_openai:gpt-4.1"
  temperature: 0.2

memory:
  backend: "chromadb"
  chromadb:
    max_connections: 20
    l1_cache_size: 5000

# CONTEXT-AWARE PROMPTS (see Step 6-7 above)
```

### Pattern 3: Complex Multi-Agent Workflows
**Use case**: Research tasks, data analysis, multi-step problems

```yaml
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  temperature: 0.1

memory:
  backend: "chromadb"
  chromadb:
    path: "./production_memory"
    max_connections: 20
    l1_cache_size: 5000
    enable_batch_processing: true

supervisor:
  name: "workflow_supervisor"
  prompt: |
    **CONVERSATION CONTEXT PRIORITY**: 
    If the user input contains "Previous conversation context:" with data from earlier interactions, 
    prioritize that existing data in your planning.
    
    You are a supervisor that creates execution plans using available agents.
    Available agents: {{agents}}
    
    Create a JSON plan with steps that can run in parallel where possible.

agents:
  - name: "data_collector_agent"
    agent_type: "react"  # Needs tools for data collection
    description: "Collects data from various sources"
  - name: "analysis_agent"
    agent_type: "react"  # Needs tools for analysis operations
    description: "Analyzes collected data and generates insights"
  - name: "python_exec_agent"
    agent_type: "react"  # Needs tools for code execution
    description: "Executes Python code for data processing"
  - name: "report_generator_agent"
    agent_type: "react"  # Needs tools for report generation
    description: "Generates comprehensive reports from analysis"
  - name: "human_response_agent"
    agent_type: "normal"  # No tools needed for final formatting
    description: "Formats final responses for human consumption"
```

### Pattern 4: Multimodal Processing
**Use case**: Image and text processing, document analysis, creative content

```yaml
models:
  default: "google:gemini-2.5-flash-lite"  # Multimodal capabilities
  supervisor: "azure_openai:gpt-4.1"      # Reliable planning
  temperature: 0.3                        # Balanced creativity/precision

memory:
  backend: "chromadb"
  chromadb:
    max_connections: 15

agents:
  - name: "multimodal_agent"
    description: "Processes both text and images"
    model: "google:gemini-2.5-flash-lite"
    agent_type: "react"  # Needs tools for file processing
    prompt: |
      **CONVERSATION CONTEXT PROCESSING**:
      Check if previous conversation context is available before starting.
      
      You can process both text and images. When analyzing uploaded files:
      1. Identify the file type and content
      2. Extract relevant information
      3. Provide comprehensive analysis
  
  - name: "human_response_agent"
    agent_type: "normal"
    description: "Formats responses for users"
    prompt: |
      **CONVERSATION CONTINUITY PRIORITY**:
      Maintain continuity with previous interactions.
      
      Present results in a clear, engaging format.
```

## Multi-Provider Integration

### 1. Provider Configuration Formats

The framework supports multiple AI providers through a unified interface:

```yaml
models:
  # Azure OpenAI Configuration
  default: "azure_openai:gpt-4.1"
  
  # Google Gemini Configuration
  supervisor: "google:gemini-2.5-flash-lite"
  
  # OpenAI Configuration
  writer: "openai:gpt-4o-mini"
  
  # Anthropic Configuration
  creative: "anthropic:claude-3-sonnet"
  
  # LM Studio Local Configuration
  development: "lm_studio:local-model"
  
  # Optional fallback model
  fallback: "azure_openai:gpt-35-turbo"
  
  # Global temperature (can be overridden per agent)
  temperature: 0.2
```

### 2. Environment Variable Setup

Each provider requires specific environment variables:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2023-05-15

# Alternative Azure OpenAI format for LiteLLM
AZURE_API_KEY=your-api-key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2023-05-15

# Google Gemini Configuration
GOOGLE_API_KEY=your-google-api-key

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Anthropic Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key

# LM Studio Local Server
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
```

### 3. Provider Selection Logic

The framework uses this detection flow:

```text
Model String → Provider Detection → Configuration Loading → Model Instantiation
     ↓              ↓                    ↓                    ↓
"azure/gpt-4.1" → Azure Provider → Azure Config → AzureLiteLLMChat
"google:gemini" → Google Provider → Google Config → GoogleGenerativeAI
"openai:gpt-4" → OpenAI Provider → OpenAI Config → ChatOpenAI
```

## Testing and Validation

### Configuration Validation Checklist

Before deploying any configuration:

1. **Syntax Validation**:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

2. **Model Accessibility Test**:
   - Verify API keys are set
   - Test model endpoints respond
   - Confirm deployment names match

3. **Memory System Test** (if enabled):
   - Verify ChromaDB connectivity
   - Test checkpoint storage/retrieval
   - Validate conversation context injection

4. **Agent Type Validation**:
   - Verify react agents have appropriate tools configured
   - Confirm normal agents use `agent_type: "normal"` for performance optimization
   - Test that agent types match their intended use cases

5. **Tool Integration Test**:
   - Test MCP server connections
   - Verify tool execution works
   - Check error handling for failed tools

6. **Performance Baseline**:
   - Measure response times for typical requests
   - Test concurrent request handling
   - Monitor memory usage patterns

### Environment Variables

Always ensure these are properly set:

```bash
# AZURE OPENAI (most reliable)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2023-05-15

# GOOGLE GEMINI
GOOGLE_API_KEY=your-google-api-key

# PERFORMANCE OPTIMIZATION
PRELOAD_CONFIGS=config/your-config.yaml

# MEMORY CONFIGURATION
MEMORY_LOGGING_ENABLED=true
MEMORY_LOGGING_DIRECTORY=memory_logs

# CHROMADB CONFIGURATION
CHROMADB_PORT=8001  # Ensure this doesn't conflict with API port (8000)
```

## Troubleshooting Guide

### Common Issues and Solutions

1. **Memory System Errors**:
   - Check ChromaDB connectivity
   - Verify collection names are unique
   - Ensure sufficient disk space

2. **Model Access Errors**:
   - Validate API keys and endpoints
   - Check deployment names match exactly
   - Verify rate limits not exceeded

3. **Context Continuity Issues**:
   - Ensure context instructions are at prompt beginning
   - Verify conversation memory is enabled
   - Check context injection is working

4. **Performance Issues**:
   - Enable preloading for frequently used configs
   - Optimize memory cache settings
   - Review timeout configurations

5. **Tool Execution Failures**:
   - Verify MCP server connectivity
   - Check tool dependencies are installed
   - Review error logs for specific failures

## Final Configuration Validation

Before considering any configuration complete, verify:

✅ **Reliability**: Error handling, fallbacks, timeouts configured  
✅ **Performance**: Optimized for target use case, preloading enabled if needed  
✅ **Context Continuity**: Context instructions properly placed and worded with turn tracking support  
✅ **Agent Types**: React vs Normal agents selected appropriately for performance  
✅ **Placeholder System**: Dynamic placeholders with proper defaults and validation  
✅ **Multi-Provider**: Provider configuration with appropriate credentials  
✅ **Testing**: Basic functionality validated, performance baseline established  
✅ **Documentation**: Configuration purpose and usage clearly documented  

---

**Last Updated**: 2025-09-30  
**Framework Version**: jk-agents-framework v2.1  
**New Features**: Enhanced Placeholder System, Multi-Provider Integration, Conversation Turn Tracking  
**Validation Status**: Production Ready ✅
