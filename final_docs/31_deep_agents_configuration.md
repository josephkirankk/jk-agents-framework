# Deep Agents Configuration Guide

**Version:** 1.0  
**Last Updated:** October 2025

---

## Table of Contents

1. [Configuration Structure](#configuration-structure)
2. [Basic Configuration](#basic-configuration)
3. [Memory Configuration](#memory-configuration)
4. [Subagent Configuration](#subagent-configuration)
5. [MCP Server Integration](#mcp-server-integration)
6. [Complete Examples](#complete-examples)

---

## Configuration Structure

Deep Agents are configured via YAML files with the following structure:

```yaml
models:                    # Model configuration
  default: "model-name"
  
temperature: 0.0           # Response temperature

memory:                    # Memory backend configuration
  backend: "chromadb"
  chromadb:
    path: "./memory_path"
    checkpoint_collection: "checkpoints"
    
conversation_memory:       # Optional conversation context
  enabled: true
  max_conversations: 10

supervisor:                # Task planning supervisor
  name: "supervisor"
  model: "model-name"
  prompt: "..."

agents:                    # Agent definitions
  - name: "agent-name"
    agent_type: "deep"     # Critical: Must be "deep"
    model: "model-name"
    description: "..."
    prompt: "..."
    
    deep_agent_config:     # Deep agent specific config
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      enable_longterm_memory: false
      subagents: []
    
    mcp_servers: {}        # External tool servers
    http_tools: {}         # HTTP-based tools
    python_tools: {}       # Python function tools
```

---

## Basic Configuration

### Minimal Deep Agent

**File:** `config/deep_agent_minimal.yaml`

```yaml
models:
  default: "openai:gpt-4o-mini"

temperature: 0.2

persistence:
  type: "memory"  # In-memory (no persistence across restarts)

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o-mini"
  prompt: |
    You are a task planning supervisor. Create execution plans.
    
    Available agents: {{agents}}
    
    Return JSON:
    {
      "goal": "Task description",
      "plan": [
        {
          "id": "s1",
          "agent": "research_agent",
          "task": "Specific task",
          "depends_on": [],
          "timeout_seconds": 120,
          "retry": 1
        }
      ]
    }

agents:
  - name: "research_agent"
    agent_type: "deep"              # Enable Deep Agent
    model: "openai:gpt-4o-mini"
    description: "Research assistant with planning capabilities"
    
    prompt: |
      You are a research assistant.
      
      Capabilities:
      - Virtual filesystem for organization
      - Task planning via todo list
      
      When given a task:
      1. Break it into manageable steps
      2. Store findings in files
      3. Provide clear summaries
    
    deep_agent_config:
      enabled: true                 # Enable Deep Agent features
      enable_filesystem: true       # Enable file operations
      enable_todolist: true         # Enable task planning
      enable_longterm_memory: false # Disable cross-thread memory
      subagents: []                 # No subagents
    
    mcp_servers: {}
    http_tools: {}
    python_tools: {}
```

### Configuration with Azure OpenAI

```yaml
models:
  default: "azure_openai:gpt-4o"

temperature: 0.2

# Set environment variables:
# AZURE_OPENAI_API_KEY=your-key
# AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
# AZURE_OPENAI_DEPLOYMENT=gpt-4o

agents:
  - name: "azure_agent"
    agent_type: "deep"
    model: "azure_openai:gpt-4o"  # Uses Azure deployment
    # ... rest of config
```

---

## Memory Configuration

### In-Memory (Development/Testing)

```yaml
persistence:
  type: "memory"

# Characteristics:
# - No disk persistence
# - Lost on restart
# - Fast performance
# - Good for development
```

### ChromaDB Persistent Memory (Production)

```yaml
memory:
  backend: "chromadb"
  chromadb:
    path: "./production_memory"           # Storage directory
    host: "localhost"                     # ChromaDB host
    port: 8001                            # ChromaDB port
    max_connections: 20                   # Connection pool size
    min_connections: 5                    # Minimum connections
    connection_timeout: 30.0              # Timeout in seconds
    l1_cache_size: 5000                   # Cache size
    l1_cache_ttl: 1800                    # Cache TTL (seconds)
    batch_size: 100                       # Batch processing size
    enable_batch_processing: true         # Enable batching
    enable_metrics: true                  # Enable metrics
    checkpoint_collection: "checkpoints"  # Checkpoint collection name
    context_collection: "context"         # Context collection name

# Memory stored in:
# ./production_memory/
#   ├── checkpoints/          # Conversation state
#   ├── context/              # Context data
#   └── chroma.sqlite3        # ChromaDB database
```

### Conversation Memory Context

```yaml
conversation_memory:
  enabled: true                    # Enable context injection
  database_url: ""                 # Optional PostgreSQL URL
  max_conversations: 10            # Recent conversations to include
  max_context_length: 3000         # Max context characters
  prepend_context: false           # Append vs prepend context
```

### Long-Term Memory (Cross-Thread)

```yaml
agents:
  - name: "agent_with_memory"
    agent_type: "deep"
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      enable_longterm_memory: true     # Enable cross-thread memory
      
      store_config:
        type: "inmemory"               # Options: inmemory, chromadb, postgres
        # For ChromaDB:
        # path: "./longterm_store"
        # collection: "longterm_memory"
```

**Usage:**
```python
# In agent prompt:
"""
Long-term memory files (persist across threads):
- write_file("/memories/user_prefs.txt", "data")
- read_file("/memories/user_prefs.txt")

Regular files (thread-scoped only):
- write_file("/temp_data.txt", "data")
"""
```

### Memory Storage Locations

```
Project Root/
├── serp_memory/                    # Default ChromaDB path
│   ├── <thread-id-1>/
│   │   ├── chroma.sqlite3
│   │   └── data/
│   ├── <thread-id-2>/
│   └── ...
│
├── longterm_store/                 # Long-term memory (if enabled)
│   ├── chroma.sqlite3
│   └── collections/
│       └── longterm_memory/
│
└── agent_workspace/                # Optional workspace
    └── memories/
```

---

## Subagent Configuration

### Single Subagent

```yaml
agents:
  - name: "orchestrator"
    agent_type: "deep"
    model: "openai:gpt-4o"
    
    prompt: |
      You have a specialized subagent:
      - analyzer: For data analysis tasks
      
      Delegate analysis tasks to the analyzer subagent.
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      
      subagents:
        - name: "analyzer"
          description: "Analyzes data and provides insights"
          system_prompt: |
            You are a data analysis specialist.
            Analyze the provided data and return insights.
          model: "openai:gpt-4o-mini"  # Can use different model
          tools: []  # Empty = inherits parent tools
```

### Multiple Specialized Subagents

```yaml
deep_agent_config:
  enabled: true
  enable_filesystem: true
  enable_todolist: true
  
  subagents:
    - name: "web-researcher"
      description: "Conducts web research - use for gathering online information"
      system_prompt: |
        You are a web research specialist.
        - Conduct thorough searches
        - Cite sources
        - Return structured findings
      model: "openai:gpt-4o-mini"
      tools: []
    
    - name: "data-analyzer"
      description: "Analyzes statistics and trends - use for numerical analysis"
      system_prompt: |
        You are a data analysis specialist.
        - Process numerical data
        - Identify trends
        - Provide evidence-based insights
      model: "openai:gpt-4o-mini"
      tools: []
    
    - name: "synthesizer"
      description: "Synthesizes information - use for combining multiple sources"
      system_prompt: |
        You are an information synthesis expert.
        - Read files containing research
        - Identify connections and themes
        - Create coherent reports
      model: "openai:gpt-4o"  # Use better model for synthesis
      tools: []
    
    - name: "validator"
      description: "Validates facts and checks accuracy"
      system_prompt: |
        You are a fact-checking specialist.
        - Verify claims
        - Check sources
        - Flag inconsistencies
      model: "openai:gpt-4o-mini"
      tools: []
```

### Subagent with Specific Tools

```yaml
subagents:
  - name: "calculator"
    description: "Performs mathematical calculations"
    system_prompt: "You solve math problems using the calculate tool."
    model: "openai:gpt-4o-mini"
    tools: ["calculate", "plot_graph"]  # Specific tool names
```

**Note:** Tool names must match actual tools available in parent agent's tool list.

---

## MCP Server Integration

### Serper Search (Google Search & Scrape)

```yaml
agents:
  - name: "search_agent"
    agent_type: "deep"
    
    prompt: |
      You have access to search tools:
      - google_search(query, gl="region", hl="language")
      - scrape(url)
      
      Examples:
      google_search(query="AI developments", gl="us", hl="en")
      google_search(query="smartphones India", gl="in", hl="en")
    
    mcp_servers:
      serper-search:
        description: "Serper Search & Scrape MCP Server"
        transport: "stdio"
        command: "npx"
        args:
          - "-y"
          - "serper-search-scrape-mcp-server"
        env:
          SERPER_API_KEY: "${SERPER_API_KEY}"

# Set in .env:
# SERPER_API_KEY=your-key-from-serper.dev
```

### Brave Search

```yaml
mcp_servers:
  brave_search:
    description: "Brave Search API"
    transport: "streamable_http"
    url: "http://localhost:8080/mcp"
    env:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"
    headers:
      Content-Type: "application/json"
```

### Filesystem MCP

```yaml
mcp_servers:
  filesystem:
    description: "Filesystem access via MCP"
    transport: "stdio"
    command: "npx"
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "/workspace"  # Root directory
    env: {}
```

### Custom MCP Server

```yaml
mcp_servers:
  custom_server:
    description: "Custom business logic server"
    transport: "stdio"
    command: "python"
    args:
      - "mcp_servers/custom_server.py"
    env:
      DATABASE_URL: "${DATABASE_URL}"
      API_KEY: "${CUSTOM_API_KEY}"
```

---

## Complete Examples

### Example 1: Basic Research Agent

**File:** `config/research_agent_basic.yaml`

```yaml
models:
  default: "openai:gpt-4o-mini"

temperature: 0.2

persistence:
  type: "memory"

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o-mini"
  prompt: |
    Create execution plans for user requests.
    Available agents: {{agents}}
    Return JSON plan with goal and steps.

agents:
  - name: "research_assistant"
    agent_type: "deep"
    model: "openai:gpt-4o-mini"
    description: "Research assistant with filesystem and planning"
    
    prompt: |
      You are a research assistant.
      
      When researching:
      1. Create todo list of steps
      2. Store findings in /research.md
      3. Organize information clearly
      4. Provide comprehensive summary
      
      Use filesystem to manage context efficiently.
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      enable_longterm_memory: false
      subagents: []
    
    mcp_servers: {}
    http_tools: {}
    python_tools: {}
```

### Example 2: Advanced Multi-Agent System

**File:** `config/research_system_advanced.yaml`

```yaml
models:
  default: "azure_openai:gpt-4o"

temperature: 0.2

memory:
  backend: "chromadb"
  chromadb:
    path: "./research_memory"
    checkpoint_collection: "research-checkpoints"
    context_collection: "research-context"

conversation_memory:
  enabled: true
  max_conversations: 10
  max_context_length: 3000

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4o"
  prompt: |
    You are an intelligent task planning supervisor.
    Analyze requests and create detailed execution plans.
    
    Available agents: {{agents}}

agents:
  - name: "master_researcher"
    agent_type: "deep"
    model: "azure_openai:gpt-4o"
    description: "Master research orchestrator with specialized subagents"
    
    prompt: |
      You are a master research orchestrator with advanced capabilities.
      
      Available Subagents:
      - web-researcher: For online research and information gathering
      - data-analyzer: For statistical analysis and trend identification
      - synthesizer: For combining information into reports
      - validator: For fact-checking and verification
      
      Available Tools:
      - google_search: Search the web
      - scrape: Extract web page content
      
      Workflow:
      1. Break down research into focused subtasks
      2. Delegate to specialized subagents
      3. Store intermediate findings in organized files
      4. Use synthesizer for final report creation
      5. Validate facts before presenting
      
      Context Management:
      - Use /web_research.md for online findings
      - Use /analysis.md for statistical insights
      - Use /final_report.md for polished output
      - Use todo list to track progress
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      enable_longterm_memory: false
      
      subagents:
        - name: "web-researcher"
          description: "Web research specialist - use for gathering online information"
          system_prompt: |
            You are a web research specialist.
            
            PRIMARY TASK: Use google_search immediately to find information.
            
            For region-specific queries:
            - India: gl="in", hl="en"
            - USA: gl="us", hl="en"
            - UK: gl="uk", hl="en"
            
            Return structured findings with:
            - Key information
            - Sources
            - Relevant URLs
          model: "azure_openai:gpt-4o-mini"
          tools: []
        
        - name: "data-analyzer"
          description: "Statistical analysis specialist - use for numerical data"
          system_prompt: |
            You are a data analysis specialist.
            - Analyze numerical data and statistics
            - Identify trends and patterns
            - Create visualizations (describe them)
            - Provide evidence-based insights
          model: "azure_openai:gpt-4o-mini"
          tools: []
        
        - name: "synthesizer"
          description: "Information synthesis specialist - combines multiple sources"
          system_prompt: |
            You are an information synthesis expert.
            - Read findings from multiple files
            - Identify key themes
            - Create coherent, well-structured reports
            - Ensure all claims are supported
          model: "azure_openai:gpt-4o"
          tools: []
        
        - name: "validator"
          description: "Fact-checking specialist - verifies accuracy"
          system_prompt: |
            You are a fact-checking specialist.
            - Verify claims using google_search
            - Cross-reference information
            - Flag inconsistencies
            - Rate confidence levels
          model: "azure_openai:gpt-4o-mini"
          tools: []
    
    mcp_servers:
      serper-search:
        description: "Google Search & Web Scraping"
        transport: "stdio"
        command: "npx"
        args:
          - "-y"
          - "serper-search-scrape-mcp-server"
        env:
          SERPER_API_KEY: "${SERPER_API_KEY}"
    
    http_tools: {}
    python_tools: {}
```

### Example 3: Human-in-the-Loop Configuration

```yaml
agents:
  - name: "safe_executor"
    agent_type: "deep"
    
    prompt: |
      You can execute tasks, but some require human approval.
      Proceed with caution for sensitive operations.
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      
      # Tools requiring human approval
      interrupt_on:
        delete_file:
          allowed_decisions: ["approve", "edit", "reject"]
        send_email:
          allowed_decisions: ["approve", "reject"]
        execute_code:
          allowed_decisions: ["approve", "edit", "reject"]
      
      subagents: []
```

**Usage:**
```python
# Agent will pause before executing sensitive tools
for event in agent.stream({"messages": [...]}, config, stream_mode="values"):
    if "__interrupt__" in event:
        print("Tool requires approval:", event["tool_name"])
        decision = input("Approve? (approve/reject): ")
        agent.update_state(config, {"decision": decision})
```

---

## Configuration Best Practices

### 1. Model Selection

```yaml
# Use stronger models for main orchestration
agents:
  - name: "orchestrator"
    model: "openai:gpt-4o"  # Better reasoning
    
    deep_agent_config:
      subagents:
        # Use lighter models for specialized tasks
        - name: "worker"
          model: "openai:gpt-4o-mini"  # Cost-effective
```

### 2. Temperature Settings

```yaml
# Research/factual tasks
temperature: 0.2

# Creative tasks
temperature: 0.7

# Deterministic execution
temperature: 0.0
```

### 3. Memory Optimization

```yaml
memory:
  chromadb:
    l1_cache_size: 5000      # Larger for better performance
    l1_cache_ttl: 1800       # 30 minutes
    batch_size: 100          # Balance speed/memory
    enable_batch_processing: true
```

### 4. Environment Variable Management

**`.env` file:**
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Search APIs
SERPER_API_KEY=...
BRAVE_API_KEY=...

# Database
DATABASE_URL=postgresql://...
```

**YAML references:**
```yaml
env:
  SERPER_API_KEY: "${SERPER_API_KEY}"
```

---

**Next:** See [Usage Examples](./32_deep_agents_examples.md) for code examples and implementation patterns.
