# Deep Agents Advanced Features and Best Practices

**Version:** 1.0  
**Last Updated:** October 2025

---

## Table of Contents

1. [Best Practices](#best-practices)
2. [Performance Optimization](#performance-optimization)
3. [Complex Scenarios](#complex-scenarios)
4. [Extension Patterns](#extension-patterns)
5. [Troubleshooting](#troubleshooting)
6. [Production Deployment](#production-deployment)

---

## Best Practices

### 1. Prompt Engineering for Deep Agents

#### Main Agent Prompts

**DO:**
```yaml
prompt: |
  You are a research orchestrator with specialized capabilities.
  
  Available Tools:
  - google_search(query, gl="region", hl="language"): Search the web
  - scrape(url): Extract page content
  
  Available Subagents:
  - web-researcher: For online information gathering
  - data-analyzer: For statistical analysis
  
  Workflow:
  1. Break down complex tasks using your todo list
  2. Delegate specialized work to subagents
  3. Store findings in organized files:
     - /research.md: Web research findings
     - /analysis.md: Data analysis results
     - /final_report.md: Polished summary
  4. Provide comprehensive, well-structured responses
  
  IMPORTANT:
  - Take ACTION immediately, don't ask for clarification
  - Use appropriate region codes (gl="in" for India, gl="us" for USA)
  - Provide complete information including prices, specs, URLs
```

**DON'T:**
```yaml
# ❌ Too vague
prompt: "You are a helpful assistant."

# ❌ No clear workflow
prompt: "Answer questions about topics."

# ❌ Missing tool instructions
prompt: "You have tools. Use them wisely."
```

#### Subagent Prompts

**DO:**
```yaml
subagents:
  - name: "web-researcher"
    system_prompt: |
      You are a web research specialist. PRIMARY TASK: Take ACTION immediately.
      
      TOOLS:
      - google_search(query, gl="region", hl="language")
      
      WORKFLOW:
      1. Use google_search IMMEDIATELY (don't explain first)
      2. For India: gl="in", hl="en"
      3. Conduct multiple searches for comprehensive data
      4. Return structured findings with sources
      
      OUTPUT FORMAT:
      - Product/Topic Name
      - Key Specifications/Facts
      - Price Information (if relevant)
      - Buy URLs/Sources
      - Summary
      
      DO NOT ask permission. DO NOT explain what you'll do. JUST SEARCH.
```

**DON'T:**
```yaml
# ❌ Too generic
system_prompt: "You do web research."

# ❌ No action directive
system_prompt: "You can search if needed."
```

### 2. Task Decomposition Strategy

#### Effective Task Planning

```python
# Agent prompt for good task decomposition:
"""
When given a complex task:

1. ANALYZE: Break into logical subtasks
   - Identify dependencies
   - Estimate complexity
   - Determine which subagents needed

2. PLAN: Create todo list
   - add_todo("Research topic A")
   - add_todo("Analyze data from A")
   - add_todo("Research topic B")
   - add_todo("Synthesize A and B")

3. EXECUTE: Work through systematically
   - Complete one task at a time
   - Mark done: mark_todo_done(task_id)
   - Store results in files
   - Track progress with list_todos()

4. SYNTHESIZE: Combine results
   - Read all research files
   - Create comprehensive report
   - Provide final summary
"""
```

#### Task Granularity

**Good Granularity:**
```
✅ Research AI applications in healthcare
✅ Analyze market size data
✅ Identify top 3 competitors
✅ Compile findings into report
```

**Poor Granularity:**
```
❌ Do everything                    (Too broad)
❌ Search for "AI"                 (Too vague)
❌ Read character 1 of file        (Too granular)
```

### 3. Context Management

#### File Organization

**Good Structure:**
```
/
├── research/
│   ├── web_findings.md         # Web research results
│   ├── sources.txt             # Source URLs
│   └── raw_data.json           # Raw data
├── analysis/
│   ├── trends.md               # Trend analysis
│   └── statistics.csv          # Numerical data
├── synthesis/
│   └── final_report.md         # Polished output
└── metadata.txt                # Tracking info
```

**Poor Structure:**
```
/
├── file1.txt                   # ❌ No organization
├── data.txt                    # ❌ Unclear purpose
├── temp123.md                  # ❌ Poor naming
└── output.txt                  # ❌ Generic name
```

#### Memory Usage Patterns

```yaml
# Session files (thread-scoped)
prompt: |
  Use regular files for current work:
  - write_file("/research.md", data)
  - read_file("/research.md")
  Files persist in this conversation only.

# Long-term memory (cross-thread)
deep_agent_config:
  enable_longterm_memory: true

prompt: |
  Use /memories/ prefix for persistent data:
  - write_file("/memories/user_prefs.txt", prefs)
  - read_file("/memories/user_prefs.txt")
  Memory files persist across all conversations.
```

### 4. Subagent Usage Guidelines

#### When to Use Subagents

**USE subagents for:**
- ✅ Specialized expertise (research, analysis, synthesis)
- ✅ Context isolation (prevent main agent overload)
- ✅ Parallel execution (multiple tasks simultaneously)
- ✅ Model differentiation (cheaper model for simple tasks)

**DON'T use subagents for:**
- ❌ Simple, single-step tasks
- ❌ Tasks requiring main context
- ❌ Quick tool calls
- ❌ Final response generation

#### Delegation Pattern

```python
# Main agent prompt:
"""
DELEGATION RULES:

1. Research Tasks → web-researcher
   - "Use web-researcher to find information about X"
   - Subagent searches, returns summary
   - Main agent doesn't see search details

2. Data Analysis → data-analyzer
   - "Use data-analyzer to analyze these numbers: [data]"
   - Subagent processes, returns insights
   - Main agent doesn't see intermediate calculations

3. Synthesis → synthesizer
   - "Use synthesizer to combine findings from /research.md and /analysis.md"
   - Subagent reads files, creates report
   - Main agent receives polished output

4. Direct Execution → Main Agent
   - Simple Q&A
   - File operations
   - Final user responses
"""
```

---

## Performance Optimization

### 1. Model Selection Strategy

```yaml
# Cost-effective configuration:
models:
  default: "openai:gpt-4o"  # Strong orchestration

agents:
  - name: "orchestrator"
    model: "openai:gpt-4o"  # Better model for main reasoning
    
    deep_agent_config:
      subagents:
        - name: "worker-1"
          model: "openai:gpt-4o-mini"  # Cheaper for simple tasks
        
        - name: "worker-2"
          model: "openai:gpt-4o-mini"
        
        - name: "synthesizer"
          model: "openai:gpt-4o"  # Better model for final synthesis
```

**Cost Impact:**
- Main agent (few calls): $$$
- Worker subagents (many calls): $
- Synthesis (1-2 calls): $$

**Performance vs Cost Matrix:**

| Agent Role | Recommended Model | Rationale |
|------------|-------------------|-----------|
| Main Orchestrator | GPT-4o, Claude Opus | Complex reasoning needed |
| Research Subagents | GPT-4o-mini, Claude Haiku | Simple information gathering |
| Analysis Subagents | GPT-4o-mini | Pattern recognition |
| Synthesis Subagents | GPT-4o, Claude Sonnet | Quality writing needed |

### 2. Memory Optimization

#### ChromaDB Configuration

```yaml
memory:
  chromadb:
    # Performance tuning:
    l1_cache_size: 10000        # Larger = faster reads, more memory
    l1_cache_ttl: 3600          # 1 hour cache
    batch_size: 200             # Larger batches = fewer DB calls
    enable_batch_processing: true
    
    # Connection pool:
    max_connections: 30         # Handle concurrent requests
    min_connections: 10         # Maintain ready connections
    connection_timeout: 60.0    # Longer timeout for complex queries
```

#### File Size Management

```python
# Agent prompt for large data:
"""
For large data outputs:

1. Store raw data in files (not in messages)
   - write_file("/data/results.json", large_json)
   - Message: "Stored 10,000 records in /data/results.json"

2. Provide summaries in responses
   - Don't return all 10,000 records
   - Return: "Found 10,000 records. Top 10: [...]"

3. Use pagination for large lists
   - Page 1: Items 1-100
   - Page 2: Items 101-200
   - Stored in /data/page_N.txt
"""
```

### 3. Parallel Execution

#### Concurrent Subagent Calls

```python
# Main agent can spawn multiple subagents in parallel:
"""
For independent research tasks:

1. Delegate in parallel:
   - "Use web-researcher to research Topic A"
   - "Use web-researcher to research Topic B"
   - "Use data-analyzer to analyze Dataset C"
   
2. All subagents execute concurrently

3. Main agent waits for all to complete

4. Synthesize results from all subagents
"""
```

#### Performance Comparison

**Sequential:**
```
Research A (30s) → Research B (30s) → Analyze C (20s) = 80s total
```

**Parallel:**
```
Research A (30s) ┐
Research B (30s) ├→ (max 30s) → Analyze C (20s) = 50s total
Analyze C (20s)  ┘
```

---

## Complex Scenarios

### Scenario 1: Multi-Stage Research Pipeline

**Configuration:**

```yaml
agents:
  - name: "research_pipeline"
    agent_type: "deep"
    model: "openai:gpt-4o"
    
    prompt: |
      You orchestrate a multi-stage research pipeline:
      
      STAGE 1: DISCOVERY
      - Use web-researcher to find relevant sources
      - Store URLs in /stage1_sources.txt
      - Initial assessment of information quality
      
      STAGE 2: DEEP DIVE
      - For each high-quality source:
        * Use scraper subagent to extract content
        * Store in /stage2_content/{source_id}.md
      - Parallel execution for speed
      
      STAGE 3: ANALYSIS
      - Use data-analyzer for quantitative data
      - Use sentiment-analyzer for qualitative data
      - Store in /stage3_analysis/{type}.md
      
      STAGE 4: SYNTHESIS
      - Use synthesizer to combine all findings
      - Create /final_report.md
      - Include citations and recommendations
      
      STAGE 5: VALIDATION
      - Use fact-checker to verify claims
      - Flag any inconsistencies
      - Update report if needed
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      
      subagents:
        - name: "web-researcher"
          description: "Finds relevant sources"
          system_prompt: "Search and evaluate sources for relevance and quality."
          model: "openai:gpt-4o-mini"
        
        - name: "scraper"
          description: "Extracts content from URLs"
          system_prompt: "Scrape and clean content from web pages."
          model: "openai:gpt-4o-mini"
        
        - name: "data-analyzer"
          description: "Analyzes quantitative data"
          system_prompt: "Process numbers, identify trends, create insights."
          model: "openai:gpt-4o-mini"
        
        - name: "sentiment-analyzer"
          description: "Analyzes qualitative data"
          system_prompt: "Analyze sentiment, themes, and opinions."
          model: "openai:gpt-4o-mini"
        
        - name: "synthesizer"
          description: "Creates comprehensive reports"
          system_prompt: "Combine findings into coherent, well-structured reports."
          model: "openai:gpt-4o"
        
        - name: "fact-checker"
          description: "Verifies factual accuracy"
          system_prompt: "Verify claims, cross-reference sources, flag issues."
          model: "openai:gpt-4o"
```

### Scenario 2: Adaptive Workflow

```python
"""
Adaptive workflow that changes based on intermediate results:

IF initial research finds comprehensive sources:
  → Deep dive into top 3 sources
  → Detailed analysis
  
ELSE IF initial research finds limited sources:
  → Broader search with different queries
  → Search related topics
  → Synthesize from multiple angles

ELSE IF initial research finds no sources:
  → Generate synthetic analysis
  → State limitations clearly
  → Suggest alternative approaches
"""
```

**Implementation:**

```yaml
prompt: |
  You adapt your workflow based on findings:
  
  Step 1: Initial search
    - search_quality = evaluate_results()
  
  Step 2: Branch based on quality
    IF search_quality == "high":
      - Execute deep_dive_workflow()
    ELIF search_quality == "medium":
      - Execute broader_search_workflow()
    ELSE:
      - Execute alternative_approach_workflow()
  
  Use todolist to track current branch.
  Store decision rationale in /workflow_log.md
```

### Scenario 3: Human-in-the-Loop Research

```yaml
agents:
  - name: "guided_researcher"
    agent_type: "deep"
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      
      # Require approval for certain operations
      interrupt_on:
        google_search:
          allowed_decisions: ["approve", "edit", "reject"]
        scrape:
          allowed_decisions: ["approve", "edit", "reject"]
```

**Usage:**

```python
async def guided_research():
    """Research with human oversight"""
    
    # Start research
    for event in agent.stream(
        {"messages": [("user", "Research quantum computing")]},
        config={"configurable": {"thread_id": "guided-1"}},
        stream_mode="values"
    ):
        # Check for interrupts
        if "__interrupt__" in event:
            tool_name = event["tool_name"]
            tool_args = event["tool_args"]
            
            print(f"\n🛑 Agent wants to call: {tool_name}")
            print(f"Arguments: {tool_args}")
            
            # Human review
            decision = input("Approve? (approve/edit/reject): ")
            
            if decision == "edit":
                new_args = input("Enter new arguments (JSON): ")
                agent.update_state(config, {
                    "decision": "approve",
                    "edited_args": json.loads(new_args)
                })
            else:
                agent.update_state(config, {"decision": decision})
```

---

## Extension Patterns

### 1. Custom Middleware

```python
"""Create custom middleware for specialized functionality"""
from deepagents.middleware import AgentMiddleware
from langchain_core.tools import tool


@tool
def custom_analysis(data: str) -> str:
    """Perform custom analysis"""
    # Your custom logic here
    return f"Analysis of {data}"


class CustomAnalysisMiddleware(AgentMiddleware):
    """Custom middleware for specialized analysis"""
    
    tools = [custom_analysis]
    
    system_prompt = """
    You have access to custom_analysis tool.
    Use it for specialized data processing.
    """
    
    def preprocess_state(self, state):
        """Modify state before agent execution"""
        # Add custom preprocessing
        return state
    
    def postprocess_state(self, state):
        """Modify state after agent execution"""
        # Add custom postprocessing
        return state


# Use in Deep Agent
from deepagents import create_deep_agent

agent = create_deep_agent(
    middleware=[CustomAnalysisMiddleware()],
    system_prompt="You are an agent with custom analysis capabilities."
)
```

### 2. Custom MCP Server

```python
"""
Create custom MCP server for business logic
File: mcp_servers/business_logic_server.py
"""
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Initialize server
app = Server("business-logic-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_customer_data",
            description="Retrieve customer information",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"}
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="process_order",
            description="Process a customer order",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "items": {"type": "array"}
                },
                "required": ["customer_id", "items"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute tool"""
    
    if name == "get_customer_data":
        customer_id = arguments["customer_id"]
        # Your business logic here
        data = {"id": customer_id, "name": "John Doe", "tier": "Gold"}
        return [TextContent(type="text", text=str(data))]
    
    elif name == "process_order":
        # Your order processing logic
        result = {"order_id": "ORD-123", "status": "processed"}
        return [TextContent(type="text", text=str(result))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
```

**Configuration:**

```yaml
mcp_servers:
  business-logic:
    description: "Custom business logic server"
    transport: "stdio"
    command: "python"
    args:
      - "mcp_servers/business_logic_server.py"
    env:
      DATABASE_URL: "${DATABASE_URL}"
```

### 3. Custom Checkpointer

```python
"""Custom checkpointer for specialized storage"""
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing import Optional, Iterator, Tuple


class CustomCheckpointer(BaseCheckpointSaver):
    """Custom checkpointer with your storage backend"""
    
    def __init__(self, connection_string: str):
        super().__init__()
        self.connection_string = connection_string
        # Initialize your storage backend
    
    def put(self, config, checkpoint, metadata) -> dict:
        """Save checkpoint"""
        # Your save logic
        pass
    
    def get_tuple(self, config) -> Optional[tuple]:
        """Retrieve checkpoint"""
        # Your retrieval logic
        pass
    
    def list(self, config) -> Iterator[tuple]:
        """List checkpoints"""
        # Your listing logic
        pass


# Use in agent
from app.agent_builder import build_agent

checkpointer = CustomCheckpointer("your-connection-string")

agent, _ = await build_agent(
    agent_cfg=config,
    default_model="openai:gpt-4o",
    checkpointer=checkpointer  # Use custom checkpointer
)
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Context Window Exceeded

**Symptoms:**
```
Error: Context length exceeded (max: 128000 tokens)
```

**Solutions:**

1. **Use Filesystem More Aggressively:**
```yaml
prompt: |
  CRITICAL: Store large data in files immediately.
  - After search: write_file("/search_results.txt", results)
  - Message: "Stored 500 results in file" (not actual results)
```

2. **Summarize Before Storing:**
```python
"""
Instead of storing raw data:
write_file("/raw.txt", all_10000_records)  # ❌ Too large

Summarize first:
summary = "Found 10,000 records. Top trends: ..."
write_file("/summary.txt", summary)  # ✅ Manageable
write_file("/sample.txt", first_100_records)  # ✅ Representative sample
"""
```

3. **Use More Subagents:**
```yaml
# Break work into smaller isolated contexts
subagents:
  - name: "processor-1"  # Handles subset 1
  - name: "processor-2"  # Handles subset 2
  - name: "aggregator"   # Combines summaries
```

#### Issue 2: Subagent Not Called

**Symptoms:**
- Main agent doesn't delegate to subagents
- Tries to do everything itself

**Solutions:**

1. **Make Descriptions Clear:**
```yaml
# ❌ Vague
- name: "helper"
  description: "Helps with stuff"

# ✅ Specific
- name: "web-researcher"
  description: "Conducts web research - USE THIS for any web search tasks"
```

2. **Add Explicit Instructions:**
```yaml
prompt: |
  DELEGATION RULES - FOLLOW EXACTLY:
  
  - For web search → MUST use web-researcher subagent
  - For data analysis → MUST use data-analyzer subagent
  - For synthesis → MUST use synthesizer subagent
  
  Do NOT try to do these tasks yourself.
```

3. **Check Model Capability:**
```yaml
# Some models better at delegation
model: "openai:gpt-4o"  # ✅ Good at delegation
# vs
model: "openai:gpt-3.5-turbo"  # ❌ May struggle
```

#### Issue 3: MCP Server Connection Failed

**Symptoms:**
```
Error: Failed to connect to MCP server
```

**Solutions:**

1. **Verify Environment Variables:**
```bash
# Check .env file
cat .env | grep SERPER_API_KEY

# Test manually
echo $SERPER_API_KEY
```

2. **Test MCP Server Directly:**
```bash
# Test stdio server
npx -y serper-search-scrape-mcp-server

# Should not error immediately
```

3. **Check Command Path:**
```yaml
# Ensure command is in PATH
command: "npx"  # ✅ Usually in PATH

# Or use absolute path
command: "/usr/local/bin/npx"  # ✅ Explicit

# Check with:
# which npx
```

4. **Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Issue 4: Memory Not Persisting

**Symptoms:**
- Conversation history lost between sessions
- Files disappear

**Solutions:**

1. **Verify ChromaDB Configuration:**
```yaml
memory:
  backend: "chromadb"  # Not "memory"
  chromadb:
    path: "./my_memory"  # Absolute path better: /path/to/memory
```

2. **Check Directory Permissions:**
```bash
# Ensure directory exists and is writable
ls -la ./my_memory
chmod 755 ./my_memory
```

3. **Consistent thread_id:**
```python
# ❌ Different thread_id each time
config = {"configurable": {"thread_id": f"session-{random()}"}}

# ✅ Same thread_id for continuation
config = {"configurable": {"thread_id": "user-123-session"}}
```

---

## Production Deployment

### 1. Configuration Management

```yaml
# config/production.yaml
models:
  default: "azure_openai:gpt-4o"  # Use Azure for reliability

temperature: 0.2

# Production-grade memory
memory:
  backend: "chromadb"
  chromadb:
    path: "/var/lib/deepagents/memory"  # Persistent volume
    max_connections: 50
    connection_timeout: 120.0
    enable_metrics: true
    checkpoint_collection: "prod-checkpoints"

# Conversation memory with PostgreSQL
conversation_memory:
  enabled: true
  database_url: "${POSTGRES_URL}"
  max_conversations: 20
  max_context_length: 5000

agents:
  - name: "production_agent"
    agent_type: "deep"
    model: "azure_openai:gpt-4o"
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
      enable_longterm_memory: true
      
      store_config:
        type: "postgres"
        connection_string: "${POSTGRES_URL}"
```

### 2. Monitoring and Logging

```python
"""Production monitoring setup"""
import logging
from app.logging_config import configure_logging

# Configure structured logging
configure_logging(
    level=logging.INFO,
    log_file="/var/log/deepagents/app.log",
    enable_json=True  # JSON logs for parsing
)

# Add metrics
from prometheus_client import Counter, Histogram

agent_requests = Counter(
    'deepagent_requests_total',
    'Total agent requests',
    ['agent_name', 'status']
)

agent_duration = Histogram(
    'deepagent_duration_seconds',
    'Agent execution duration',
    ['agent_name']
)

# Wrap agent calls
async def monitored_invoke(agent, messages, config):
    start_time = time.time()
    try:
        result = await agent.ainvoke(
            {"messages": messages},
            config=config
        )
        agent_requests.labels(
            agent_name=config['agent_name'],
            status='success'
        ).inc()
        return result
    except Exception as e:
        agent_requests.labels(
            agent_name=config['agent_name'],
            status='error'
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        agent_duration.labels(
            agent_name=config['agent_name']
        ).observe(duration)
```

### 3. Error Handling

```python
"""Robust error handling"""
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
async def resilient_agent_call(agent, messages, config):
    """Agent call with retries"""
    try:
        result = await asyncio.wait_for(
            agent.ainvoke({"messages": messages}, config=config),
            timeout=300.0  # 5 minute timeout
        )
        return result
        
    except asyncio.TimeoutError:
        logging.error(f"Agent timeout for thread {config['thread_id']}")
        raise
    
    except Exception as e:
        logging.error(f"Agent error: {e}", exc_info=True)
        raise


# Use in production
try:
    result = await resilient_agent_call(agent, messages, config)
except Exception as e:
    # Fallback or error response
    return {"error": "Service temporarily unavailable"}
```

### 4. Rate Limiting

```python
"""Rate limiting for API protection"""
from aiolimiter import AsyncLimiter


class RateLimitedAgent:
    def __init__(self, agent, requests_per_minute=60):
        self.agent = agent
        self.limiter = AsyncLimiter(requests_per_minute, 60)
    
    async def ainvoke(self, messages, config):
        async with self.limiter:
            return await self.agent.ainvoke(messages, config)


# Use in production
rate_limited_agent = RateLimitedAgent(agent, requests_per_minute=30)
result = await rate_limited_agent.ainvoke(messages, config)
```

### 5. Health Checks

```python
"""Health check endpoint"""
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check agent
    try:
        await agent.ainvoke(
            {"messages": [("user", "ping")]},
            config={"configurable": {"thread_id": "health-check"}}
        )
        health["checks"]["agent"] = "ok"
    except Exception as e:
        health["checks"]["agent"] = f"error: {e}"
        health["status"] = "unhealthy"
    
    # Check ChromaDB
    try:
        checkpointer.get_tuple({"configurable": {"thread_id": "health"}})
        health["checks"]["chromadb"] = "ok"
    except Exception as e:
        health["checks"]["chromadb"] = f"error: {e}"
        health["status"] = "unhealthy"
    
    # Check MCP servers
    if mcp_client:
        try:
            tools = await mcp_client.list_tools()
            health["checks"]["mcp"] = f"ok ({len(tools)} tools)"
        except Exception as e:
            health["checks"]["mcp"] = f"error: {e}"
            health["status"] = "degraded"
    
    return health
```

---

**Related Documentation:**
- [Overview](./30_deep_agents_overview.md)
- [Configuration](./31_deep_agents_configuration.md)
- [Examples](./32_deep_agents_examples.md)
