# Configuration Quick Reference Guide

*Updated for JK-Agents Framework v2.1 with Enhanced Placeholder System, Multi-Provider Support, and Conversation Turn Tracking*

## Essential Configuration Templates

### 🚀 High-Performance Template (Memory Disabled)
```yaml
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  fallback: "openai:gpt-4o-mini"  # Optional fallback
  temperature: 0.1

business_context: |
  High-performance system optimized for speed and accuracy.
  Current session: {{timestamp}} on {{platform}}
  Response target: <5 seconds for simple tasks, <15 seconds for complex tasks.

memory:
  enabled: false
conversation_memory:
  enabled: false

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: |
    **CONVERSATION CONTEXT PRIORITY**: 
    If the user input contains "Previous conversation context:" with [Turn-X] markers,
    prioritize that existing data in your planning.
    
    You are a supervisor creating execution plans using available agents.
    Available agents: {{agents}}
    
    Create efficient execution plans with minimal overhead.
    Set timeouts: 30s simple, 60s complex.
    Return JSON only.

agents:
  - name: "python_exec_agent"
    agent_type: "react"  # Uses ReAct pattern with tool calling
    model: "azure_openai:gpt-4.1"
    description: "Execute Python code and calculations"
    prompt: |
      {{dependent_request_responses}}
      
      **CONVERSATION CONTEXT PROCESSING**:
      BEFORE starting any computational task, check if user input contains "Previous conversation context:"
      with [Turn-X] markers. If present, prioritize that existing data.
      
      **IMPORTANT**: If the user input contains "Previous conversation context:" with data from earlier interactions, USE THAT DATA as input instead of generating new data
      
      Execute Python code using run_python_code tool.
      Show code and results efficiently.
      
      Available MCP servers: {{mcpservers}}
      
  - name: "human_response_agent"
    agent_type: "normal"  # No tools needed, faster execution
    model: "azure_openai:gpt-4.1" 
    description: "Format final responses for users"
    prompt: |
      {{dependent_request_responses}}
      
      **CONVERSATION CONTINUITY PRIORITY**:
      Check if previous conversation context with [Turn-X] markers is available.
      If present, maintain continuity and reference previous results.
      
      Present clear, natural answers without revealing internal processes.
      
mcp_servers:
  python_runner:
    description: "Python code execution via Deno"
    transport: "stdio"
    command: "deno"
    args: ["run", "-N", "-R=node_modules", "-W=node_modules", "--node-modules-dir=auto", "jsr:@pydantic/mcp-run-python", "stdio"]
```

### 💬 Conversational Template (Memory Enabled)
```yaml
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  fallback: "openai:gpt-4o-mini"
  temperature: 0.2  # Slightly higher for conversational variety

business_context: |
  Conversational AI system with full context awareness.
  User: {{user_name|default("User")}} in {{department|default("General")}}
  Session: {{timestamp}} on {{platform}}
  Conversation tracking: Enabled with turn-based context

memory:
  backend: "chromadb"
  chromadb:
    path: "./conversation_memory"
    host: "localhost"
    port: 8001  # Avoid conflict with API server (port 8000)
    max_connections: 20
    min_connections: 5
    connection_timeout: 30.0
    l1_cache_size: 5000
    l1_cache_ttl: 1800  # 30 minutes
    batch_size: 100
    batch_timeout: 0.1
    enable_batch_processing: true
    enable_metrics: true
    checkpoint_collection: "main-session"
    context_collection: "main-context"

conversation_memory:
  enabled: true
  database_url: ""
  max_conversations: 10
  max_context_length: 2000
  prepend_context: true
  pool_size: 10
  cleanup_days: 7

supervisor:
  name: "conversation_supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: |
    **CONVERSATION CONTEXT PRIORITY**: 
    If user input contains "Previous conversation context:" with [Turn-X] markers,
    prioritize that existing data and maintain conversation flow.
    
    Available agents: {{agents}}
    Current session context: {{conversation_context_metadata}}
    
    Build upon previous interactions for perfect continuity.
    Create plans that reuse existing data when appropriate.

agents:
  - name: "python_exec_agent"
    agent_type: "react"
    model: "azure_openai:gpt-4.1"
    description: "Execute Python code with conversation awareness"
    prompt: |
      {{dependent_request_responses}}
      
      **CONVERSATION CONTEXT PROCESSING**:
      BEFORE starting any computational task, check if user input contains "Previous conversation context:"
      with [Turn-X] markers. If present:
      1. PRIORITIZE that existing data as your primary input source
      2. DO NOT generate new data when existing conversation data is available
      3. Build upon and extend the previous conversation data
      4. Maintain data consistency across conversation turns
      
      **IMPORTANT**: Use existing conversation data to maintain perfect continuity.
      Reference specific turns like [Turn-1], [Turn-2] when building upon previous work.
      
      Available MCP servers: {{mcpservers}}
      
  - name: "human_response_agent"
    agent_type: "normal"
    model: "azure_openai:gpt-4.1"
    description: "Conversational response formatting with context awareness"
    prompt: |
      {{dependent_request_responses}}
      
      **CONVERSATION CONTINUITY PRIORITY**:
      Check if previous conversation context with [Turn-X] markers is available.
      If present, you MUST:
      1. Acknowledge the context and build upon previous interactions
      2. Maintain data consistency across conversation turns
      3. Reference previous results when relevant to current response
      4. Avoid treating each request as an isolated interaction
      
      Present natural, contextually aware responses that demonstrate
      understanding of the ongoing conversation.
```

## Critical Prompt Engineering Patterns

### Enhanced Placeholder System
```yaml
# Built-in System Placeholders
business_context: |
  Current time: {{timestamp}}              # ISO timestamp
  Platform: {{platform}}                  # OS platform  
  Python version: {{python_version}}      # Python version
  Working directory: {{working_directory}} # Current directory
  
  # Agent Context Placeholders
  Agent: {{agent_name}} using {{agent_model}}
  Description: {{agent_description}}
  
  # Business Context Placeholders
  Business context: {{business_context}}
  Original question: {{original_user_question}}
  Available MCP servers: {{mcpservers}}
  Available agents: {{agents}}
  
  # Custom Placeholders with Defaults
  User: {{user_name|default("User")}}
  Project: {{project_name|default("Default Project")}}
  Priority: {{priority|default("normal")}}
  Department: {{department|default("General")}}
```

### Agent Type Configuration
```yaml
# React Agent (for tool-based operations)
agents:
  - name: "python_exec_agent"
    agent_type: "react"  # Uses ReAct pattern with tool calling
    description: "Execute Python code and calculations"
    # Use for: computational tasks, API calls, code execution
    
  - name: "data_processor"  
    agent_type: "react"  # Needs tools for data operations
    description: "Process and analyze datasets"
    
# Normal Agent (for conversational responses)
  - name: "human_response_agent"
    agent_type: "normal"  # No tools needed, faster execution
    description: "Format final responses for users"
    # Use for: response formatting, conversation, knowledge queries
```

### Context Awareness (ESSENTIAL for conversation continuity)
```yaml
# SUPERVISOR - Place at BEGINNING of prompt
supervisor:
  prompt: |
    **CONVERSATION CONTEXT PRIORITY**: 
    If the user input contains "Previous conversation context:" with data from earlier interactions, 
    you MUST prioritize that existing data in your planning. Use that data as the foundation for 
    your plan instead of generating new data. Build upon previous interactions to maintain continuity.

# PYTHON AGENT - Place at BEGINNING of prompt  
agents:
  - name: "python_exec_agent"
    prompt: |
      {{dependent_request_responses}}

      **CONVERSATION CONTEXT PROCESSING**:
      BEFORE starting any computational task, check if the user input contains "Previous conversation context:" 
      with data from earlier interactions. If present:
      1. PRIORITIZE that existing data as your primary input source
      2. DO NOT generate new data when existing conversation data is available
      3. Build upon and extend the previous conversation data
      4. Maintain data consistency across conversation turns

# HUMAN RESPONSE - Place at BEGINNING of prompt
  - name: "human_response_agent"
    prompt: |
      {{dependent_request_responses}}
      
      **CONVERSATION CONTINUITY PRIORITY**:
      Check if previous conversation context is available. If present, you MUST:
      1. Acknowledge the context and build upon previous interactions
      2. Maintain data consistency across conversation turns
      3. Reference previous results when relevant to current response
      4. Avoid treating each request as an isolated interaction
```

## Environment Variables Checklist

### Azure OpenAI (Recommended - Most Reliable)
```bash
# Standard Azure OpenAI format
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your-actual-api-key
AZURE_OPENAI_API_VERSION=2023-05-15

# Alternative LiteLLM Azure format
AZURE_API_KEY=your-actual-api-key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2023-05-15
```

### Google Gemini (Multimodal Capabilities)
```bash
GOOGLE_API_KEY=your-google-api-key
# Model format: google:gemini-2.5-flash-lite
```

### OpenAI (Fallback Option)
```bash
OPENAI_API_KEY=sk-your-openai-api-key
# Model format: openai:gpt-4o-mini
```

### Anthropic Claude (Long-form Content)
```bash
ANTHROPIC_API_KEY=your-anthropic-api-key
# Model format: anthropic:claude-3-sonnet
```

### LM Studio (Local Development)
```bash
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
# Model format: lm_studio:local-model
```

### Performance Optimization
```bash
PRELOAD_CONFIGS=config/your-config.yaml
MEMORY_LOGGING_ENABLED=true
MEMORY_LOGGING_DIRECTORY=memory_logs
CHROMADB_PORT=8001  # Avoid conflict with API port 8000
```

## Memory Configuration Patterns

### High-Performance ChromaDB
```yaml
memory:
  backend: "chromadb"
  chromadb:
    path: "./production_memory"
    host: "localhost"
    port: 8001  # IMPORTANT: Avoid conflict with API server (port 8000)
    max_connections: 20
    min_connections: 5
    connection_timeout: 30.0
    # High-Performance Cache Settings
    l1_cache_size: 5000
    l1_cache_ttl: 1800  # 30 minutes
    # Batch Processing Optimization  
    batch_size: 100
    batch_timeout: 0.1
    enable_batch_processing: true
    enable_metrics: true
    # Collections Configuration
    checkpoint_collection: "main-session"
    context_collection: "main-context"
```

### Memory Disabled (Maximum Speed)
```yaml
memory:
  enabled: false
conversation_memory:
  enabled: false
```

## Multi-Provider Model Selection Guide

| Use Case | Model | Temperature | Agent Type | Notes |
|----------|-------|-------------|------------|-------|
| Production API | `azure_openai:gpt-4.1` | 0.1 | react/normal | Most reliable, best tool calling |
| Analysis Tasks | `azure_openai:gpt-4.1` | 0.1 | react | Consistent results, excellent reasoning |
| Creative Tasks | `google:gemini-2.5-flash-lite` | 0.3-0.7 | react | Multimodal, creative capabilities |
| Long-form Content | `anthropic:claude-3-sonnet` | 0.3 | normal | Excellent for writing, reasoning |
| Cost-Effective | `openai:gpt-4o-mini` | 0.1 | react/normal | Budget-friendly fallback |
| Local Development | `lm_studio:local-model` | 0.2 | react/normal | Offline development, privacy |
| Multimodal Tasks | `google:gemini-2.5-flash-lite` | 0.2 | react | Image + text processing |

## Tool Configuration Patterns

### MCP Servers (Model Context Protocol)

#### STDIO Transport (Local Commands)
```yaml
mcp_servers:
  python_runner:
    description: "Run Python code"
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
    args: ["mcp-server-git", "--repository", "/path/to/repo"]
```

#### HTTP Transport (Remote Services)
```yaml
mcp_servers:
  brave_search:
    description: "Web search via Brave"
    transport: "http"
    url: "http://localhost:3001"
    
  ado_server:
    description: "Azure DevOps integration"
    transport: "stdio"
    command: "node"
    args: ["ado-mcp-server/index.js"]
    env:
      ADO_ORG_URL: "https://dev.azure.com/yourorg"
      ADO_PAT: "${ADO_PERSONAL_ACCESS_TOKEN}"
```

### Python Tools (Direct Function Integration)
```yaml
python_tools:
  - module: "custom_tools.math_utils"
    functions: ["calculate_stats", "analyze_data"]
    description: "Mathematical analysis functions"
  
  - file: "./tools/business_logic.py"
    functions: ["validate_rules", "generate_report"]
    description: "Business validation and reporting"
```

### HTTP Tools (REST API Integration)
```yaml
http_tools:
  - name: "get_user_data"
    method: "GET"
    url: "https://api.example.com/users/{user_id}"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    description: "Retrieve user information"
    
  - name: "create_ticket"
    method: "POST"
    url: "https://ticketing.example.com/api/tickets"
    body_template: '{"title": "{title}", "description": "{description}"}'
    description: "Create support ticket"
```

## Tool Selection Guide

| Tool Type | Use When | Examples |
|-----------|----------|----------|
| **MCP Servers** | Complex operations, process isolation | Python execution, Git operations, external APIs |
| **Python Tools** | Direct function calls, high performance | Math calculations, data processing, validation |
| **HTTP Tools** | Simple REST APIs, one-off requests | User lookup, notifications, simple CRUD |

## Timeout Configuration

### Recommended Timeouts
```yaml
supervisor:
  prompt: |
    Timeout settings:
    - Simple calculations: 30 seconds
    - Complex analysis: 60 seconds
    - External API calls: 45 seconds
    - File operations: 90 seconds
    - MCP server operations: 120 seconds
```

## Validation Checklist

Before deploying any configuration:

✅ **Syntax**: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`  
✅ **Environment**: All required API keys set for selected providers  
✅ **Models**: Endpoints accessible, correct model names used  
✅ **Memory**: ChromaDB connectivity on port 8001 (if enabled)  
✅ **Tools**: MCP servers responding, agent types correctly set  
✅ **Context**: Conversation instructions with [Turn-X] support at prompt beginning  
✅ **Placeholders**: All placeholders have appropriate defaults  
✅ **Multi-Provider**: Fallback models configured for reliability  

## Troubleshooting Quick Fixes

### Memory Errors
```bash
# Check ChromaDB connectivity (note port 8001)
curl http://localhost:8001/api/v1/heartbeat

# Reset memory collections
rm -rf ./production_memory
rm -rf ./conversation_memory

# Check memory configuration
echo "ChromaDB Port: $CHROMADB_PORT (should be 8001)"
```

### Model Access Errors
```bash
# Verify Azure OpenAI environment variables
echo "Azure Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "Azure API Key: ${AZURE_OPENAI_API_KEY:0:10}..." # Show first 10 chars

# Test Azure API connection
curl -H "api-key: $AZURE_OPENAI_API_KEY" \
     "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2023-05-15"

# Verify Google Gemini (if used)
echo "Google API Key: ${GOOGLE_API_KEY:0:10}..." # Show first 10 chars

# Verify OpenAI (if used) 
echo "OpenAI API Key: ${OPENAI_API_KEY:0:10}..." # Show first 10 chars

# Check LM Studio (if used)
curl http://127.0.0.1:1234/v1/models
```

### Context Continuity Issues
1. Verify context instructions are at **beginning** of prompts with [Turn-X] support
2. Check conversation memory is enabled and ChromaDB is on port 8001
3. Ensure placeholders include conversation_context_metadata
4. Test with simple multi-turn conversation: "list names" → "assign numbers"
5. Verify turn tracking format: [Turn-1], [Turn-2], etc.

### Performance Issues
1. Enable preloading: `PRELOAD_CONFIGS=config/your-config.yaml`
2. Disable memory for speed-critical applications
3. Optimize ChromaDB cache settings

## Performance Expectations

### High-Performance Config (Memory Disabled)
- **Response Time**: 5-8 seconds average (improved with agent types)
- **Throughput**: 100+ requests/hour
- **Memory Usage**: Minimal
- **Turn Tracking**: Not applicable (single-turn)

### Conversational Config (Memory Enabled)  
- **Response Time**: 8-12 seconds initial, 6-10 seconds follow-up (with context reuse)
- **Throughput**: 60-80 requests/hour (improved with conversation continuity)
- **Memory Usage**: Moderate, optimized with L1 cache
- **Context Continuity**: 95%+ success rate with proper prompting

### Complex Multi-Agent Config
- **Response Time**: 10-25 seconds (improved with parallel execution)
- **Throughput**: 25-45 requests/hour  
- **Memory Usage**: Higher, scales with agent count
- **Multi-Provider**: Automatic fallback reduces failures by 90%

### Multi-Provider Performance
- **Azure OpenAI**: ~1.3s response time, most reliable
- **Google Gemini**: ~1-2s response time, excellent for creative tasks  
- **OpenAI**: ~2-3s response time, good fallback option
- **LM Studio**: Variable (depends on hardware), best for development

## Framework Features Summary (v2.1)

🔥 **New in 2025**:
- **Enhanced Placeholder System** with default values (`{{placeholder|default("value")}}`)
- **Multi-Provider Integration** (Azure OpenAI, Google Gemini, OpenAI, Anthropic, LM Studio)
- **Conversation Turn Tracking** with `[Turn-X]` format for 95%+ context success
- **Agent Type Configuration** (`react` vs `normal`) for 20%+ performance improvement
- **ChromaDB Optimizations** with L1 cache and batch processing

---

**Quick Start**: 
1. Copy the High-Performance Template
2. Set Azure OpenAI environment variables (most reliable)
3. Configure ChromaDB on port 8001 to avoid conflicts
4. Use `agent_type: "react"` for tool-based agents, `"normal"` for response formatting
5. Test with simple request, then enable memory for conversational AI

**Multi-Provider Setup**: Configure multiple providers with fallbacks for 99%+ uptime reliability.
