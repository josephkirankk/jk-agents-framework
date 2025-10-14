# JK-Agents Framework - Usage Guide and Examples

*Generated on: 2025-09-29*

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Installation and Setup](#installation-and-setup)
3. [Configuration Guide](#configuration-guide)
4. [Basic Usage Examples](#basic-usage-examples)
5. [Advanced Usage Patterns](#advanced-usage-patterns)
6. [Multi-Provider Configuration](#multi-provider-configuration)
7. [Tool Integration Examples](#tool-integration-examples)
8. [Memory and Persistence](#memory-and-persistence)
9. [API Usage Examples](#api-usage-examples)
10. [Troubleshooting and Best Practices](#troubleshooting-and-best-practices)

---

## Quick Start Guide

### Minimum Viable Setup

1. **Clone and Install**:
   ```bash
   git clone <repository-url> jk-agents-framework
   cd jk-agents-framework
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Basic Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the Framework**:
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Test Basic Functionality**:
   ```bash
   curl -X POST "http://localhost:8000/query" \
        -H "Content-Type: application/json" \
        -d '{"query": "Hello, can you help me with a simple task?"}'
   ```

---

## Installation and Setup

### Prerequisites

- **Python 3.11+** (required for modern type hints and performance optimizations)
- **One or more LLM provider API keys** (OpenAI, Azure OpenAI, Google Gemini, or Anthropic Claude)
- **Deno runtime** (optional, for MCP Python execution tools)

### Environment Configuration

#### Basic .env Setup
```bash
# Copy the example environment file
cp .env.example .env

# Required: Choose at least one provider
OPENAI_API_KEY=sk-your-openai-api-key-here
# OR
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
# OR
GOOGLE_API_KEY=AIza-your-google-api-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Optional: Enable advanced features
LANGSMITH_API_KEY=your-langsmith-key
MEMORY_LOGGING_ENABLED=true
```

#### Cross-Platform Compatibility

**macOS/Linux**:
```bash
source .venv/bin/activate
./run_api_server.sh
```

**Windows**:
```powershell
.venv\Scripts\activate
.\run_api_server.ps1
```

### Environment-Specific Deployment

#### Development Environment
```bash
python run_with_env.py local uvicorn api:app --reload
```

#### Staging Environment
```bash
python run_with_env.py staging uvicorn api:app --host 0.0.0.0
```

#### Production Environment
```bash
python run_with_env.py production uvicorn api:app --host 0.0.0.0 --workers 4
```

---

## Configuration Guide

### Basic Agent Configuration

#### Simple Single Agent Setup
```yaml
# config/simple_agent.yaml
models:
  default: "openai:gpt-4o-mini"
  
business_context: |
  You are part of a helpful AI assistant system.
  
supervisor:
  name: "supervisor"
  prompt: |
    You are the Supervisor. Create simple plans using available agents.
    Available agents: {{agents}}
    
    Return JSON only:
    {
      "goal": "brief description",
      "plan": [
        {"id": "s1", "agent": "helper", "task": "specific task"}
      ]
    }

agents:
  - name: "helper"
    description: "General purpose helpful assistant"
    prompt: |
      You are a helpful assistant. Answer questions clearly and concisely.
      Provide accurate information and be honest if you don't know something.
```

#### Multi-Agent Specialized Setup
```yaml
# config/specialized_agents.yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "azure_openai:gpt-4o"
  
business_context: |
  Professional data analysis and reporting system.
  Focus on accuracy, clarity, and actionable insights.

supervisor:
  name: "supervisor"
  prompt: |
    You are a Data Analysis Supervisor. Break down requests into specialized tasks.
    
    Available agents: {{agents}}
    Business context: {{business_context}}
    
    Create plans with appropriate agent assignments:
    {
      "goal": "user objective",
      "plan": [
        {"id": "s1", "agent": "data_analyst", "task": "analyze data", "depends_on": []},
        {"id": "s2", "agent": "report_writer", "task": "create report", "depends_on": ["s1"]}
      ]
    }

agents:
  - name: "data_analyst"
    description: "Analyzes datasets and identifies patterns"
    model: "google:gemini-2.0-flash-exp"
    prompt: |
      You are a Data Analyst. Examine data files and identify:
      - Key patterns and trends
      - Statistical insights
      - Anomalies or outliers
      - Actionable recommendations
      
      Provide clear, data-driven analysis with supporting evidence.
    
  - name: "report_writer"
    description: "Creates professional reports from analysis"
    model: "azure_openai:gpt-4o"
    prompt: |
      You are a Report Writer. Create professional reports that:
      - Summarize key findings clearly
      - Include visualizations when helpful
      - Provide actionable recommendations
      - Use business-appropriate language
```

### Advanced Configuration Options

#### Agent Types and Behaviors
```yaml
agents:
  # React agent with tools (default)
  - name: "tool_user"
    agent_type: "react"
    description: "Uses tools to accomplish tasks"
    
  # Simple chat agent without tools
  - name: "chat_only"
    agent_type: "normal"
    description: "Provides information without external tools"
    
  # Custom parallel tool calling control
  - name: "sequential_agent"
    parallel_tool_calls_enabled: false
    description: "Uses tools one at a time for careful execution"
```

#### Temperature and Model Parameters
```yaml
models:
  # With temperature control
  default: "google:gemini-2.0-flash-exp:0.3"
  creative: "openai:gpt-4o:0.8"
  analytical: "azure_openai:gpt-4o:0.1"

# Global default temperature
temperature: 0.2
```

#### Prompt File Organization
```yaml
# config/agents_with_files.yaml
agents:
  - name: "specialist"
    description: "Domain expert with detailed prompts"
    prompt_file: "prompts/specialist_instructions.txt"
    
  - name: "analyst" 
    prompt_file: "prompts/data_analyst_prompt.md"
```

File structure:
```
config/
├── agents_with_files.yaml
└── prompts/
    ├── specialist_instructions.txt
    └── data_analyst_prompt.md
```

---

## Basic Usage Examples

### Example 1: Simple Question Answering

**Request**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main benefits of renewable energy?",
    "thread_id": "renewable-discussion"
  }'
```

**Response**:
```json
{
  "response": "Based on the analysis, here are the main benefits of renewable energy:\n\n1. **Environmental Benefits**:\n   - Reduced greenhouse gas emissions\n   - Lower air and water pollution\n   - Minimal environmental impact\n\n2. **Economic Advantages**:\n   - Long-term cost savings\n   - Job creation in new industries\n   - Energy independence\n\n3. **Sustainability**:\n   - Inexhaustible energy sources\n   - Reduced dependence on fossil fuels\n   - Future energy security",
  "thread_id": "renewable-discussion",
  "execution_time": 2.1,
  "steps_executed": 1
}
```

### Example 2: Multi-Step Data Analysis

**Configuration**:
```yaml
# config/data_analysis_workflow.yaml
models:
  default: "google:gemini-2.0-flash-exp"
  
agents:
  - name: "csv_analyzer"
    description: "Analyzes CSV data files"
    prompt: |
      You are a CSV Data Analyzer. When given CSV data:
      1. Examine the structure and columns
      2. Identify data types and patterns
      3. Calculate basic statistics
      4. Note any data quality issues
      5. Provide key insights
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args: ["run", "-N", "jsr:@pydantic/mcp-run-python"]
        
  - name: "insight_generator"
    description: "Generates business insights from analysis"
    prompt: |
      You are an Insight Generator. Transform data analysis into:
      - Executive summary of findings
      - Key business implications
      - Actionable recommendations
      - Risk assessments
```

**Request**:
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "file=@sales_data.csv" \
  -F "query=Analyze this sales data and provide business insights" \
  -F "agent_name=csv_analyzer"
```

### Example 3: Conversation with Memory

**Initial Request**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I need help planning a marketing campaign for a new product",
    "thread_id": "campaign-planning-session"
  }'
```

**Follow-up Request** (same thread):
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What budget range should I consider for the campaign we just discussed?",
    "thread_id": "campaign-planning-session"
  }'
```

The second request will include context from the first conversation.

---

## Advanced Usage Patterns

### Pattern 1: Conditional Workflow Execution

**Configuration**:
```yaml
# config/conditional_workflow.yaml
supervisor:
  prompt: |
    Analyze the user request and create conditional workflows.
    
    For data analysis requests:
    - First validate the data
    - Then perform analysis
    - Finally generate insights
    
    For creative requests:
    - Brainstorm ideas
    - Develop concepts
    - Create final output
    
    Return JSON plan with appropriate agent assignments based on request type.

agents:
  - name: "data_validator"
    description: "Validates data quality and structure"
    
  - name: "data_analyzer"  
    description: "Performs statistical analysis"
    
  - name: "creative_brainstormer"
    description: "Generates creative ideas"
    
  - name: "content_creator"
    description: "Creates final creative content"
```

### Pattern 2: Error Handling and Recovery

**Configuration with Verification**:
```yaml
supervisor:
  prompt: |
    Create plans with verification steps for critical operations.
    Include retry logic for important tasks.
    
    Example plan with verification:
    {
      "goal": "Process financial data",
      "plan": [
        {
          "id": "s1", 
          "agent": "data_processor",
          "task": "Process the financial data",
          "verify": "Were all financial calculations completed correctly?",
          "retry": 2,
          "timeout_seconds": 300
        }
      ]
    }
```

### Pattern 3: Parallel Processing Workflow

**Configuration**:
```yaml
# config/parallel_processing.yaml
models:
  default: "google:gemini-2.0-flash-exp"

# Enable parallel tool calls for faster execution  
parallel_tool_calls_enabled: true

supervisor:
  prompt: |
    Create plans that can execute multiple independent tasks in parallel.
    Only use dependencies when tasks actually depend on each other.
    
    Example parallel plan:
    {
      "plan": [
        {"id": "s1", "agent": "analyzer1", "task": "Analyze dataset 1", "depends_on": []},
        {"id": "s2", "agent": "analyzer2", "task": "Analyze dataset 2", "depends_on": []},
        {"id": "s3", "agent": "synthesizer", "task": "Combine analyses", "depends_on": ["s1", "s2"]}
      ]
    }

agents:
  - name: "analyzer1"
    parallel_tool_calls_enabled: true
  - name: "analyzer2" 
    parallel_tool_calls_enabled: true
  - name: "synthesizer"
    parallel_tool_calls_enabled: false  # Sequential processing for synthesis
```

---

## Multi-Provider Configuration

### Scenario 1: Azure + OpenAI Hybrid

**Environment Configuration**:
```bash
# .env
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-org.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

OPENAI_API_KEY=sk-your-openai-key
```

**Agent Configuration**:
```yaml
# config/hybrid_providers.yaml
models:
  default: "azure_openai:gpt-4o"        # Use Azure for main processing
  supervisor: "openai:gpt-4o"           # Use OpenAI for planning
  creative: "openai:gpt-4o:0.8"         # OpenAI with high creativity
  analytical: "azure_openai:gpt-4o:0.1" # Azure with low temperature

agents:
  - name: "data_analyst"
    model: "azure_openai:gpt-4o:0.2"    # Precise analysis
    
  - name: "creative_writer"
    model: "openai:gpt-4o:0.7"          # Creative writing
    
  - name: "fact_checker"
    model: "azure_openai:gpt-4o:0.0"    # Maximum precision
```

### Scenario 2: Google Gemini + Local LM Studio

**Environment Configuration**:
```bash
# .env
GOOGLE_API_KEY=AIza-your-google-key

# LM Studio configuration
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
```

**Agent Configuration**:
```yaml
# config/gemini_local_hybrid.yaml
models:
  default: "google:gemini-2.0-flash-exp"    # Google for advanced tasks
  supervisor: "google:gemini-1.5-pro"       # Google for planning
  local: "openai:llama-3.2-3b"              # Local model via LM Studio

agents:
  - name: "multimodal_processor"
    model: "google:gemini-2.0-flash-exp"
    description: "Handles images, documents, and complex analysis"
    
  - name: "simple_responder"  
    model: "openai:llama-3.2-3b"
    description: "Fast responses for simple queries"
    
  - name: "supervisor"
    model: "google:gemini-1.5-pro"
```

### Scenario 3: All Providers with LiteLLM

**Environment Configuration**:
```bash
# .env - LiteLLM format
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=AIza-your-google-key

# Azure for LiteLLM
AZURE_API_KEY=your-azure-key
AZURE_API_BASE=https://your-org.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview
```

**Agent Configuration**:
```yaml
# config/multi_provider_litellm.yaml
models:
  default: "openai/gpt-4o-mini"           # OpenAI via LiteLLM
  supervisor: "anthropic/claude-3-5-sonnet" # Claude for planning
  creative: "gemini/gemini-1.5-pro"      # Gemini for creativity
  enterprise: "azure/gpt-4o"             # Azure for enterprise

agents:
  - name: "fast_responder"
    model: "openai/gpt-4o-mini"
    
  - name: "deep_thinker"
    model: "anthropic/claude-3-5-sonnet"
    
  - name: "creative_generator"
    model: "gemini/gemini-1.5-pro"
```

---

## Tool Integration Examples

### MCP Tool Integration

#### Python Code Execution
```yaml
# config/python_tools.yaml
agents:
  - name: "code_executor"
    description: "Executes Python code for data analysis"
    mcp_servers:
      python_runner:
        description: "Python code execution environment"
        transport: "stdio"
        command: "deno"
        args: ["run", "-N", "jsr:@pydantic/mcp-run-python"]
        env:
          PYTHONPATH: "/app/tools:/app/libraries"
```

#### HTTP API Integration
```yaml
# config/api_integration.yaml
agents:
  - name: "api_client"
    description: "Interacts with external APIs"
    mcp_servers:
      weather_api:
        description: "Weather data API"
        transport: "http"
        url: "https://api.weatherapi.com/mcp"
        headers:
          Authorization: "Bearer {{WEATHER_API_KEY}}"
          Content-Type: "application/json"
```

### Python Function Tools

#### Custom Business Logic
```python
# tools/business_tools.py
from langchain.tools.base import BaseTool
from typing import Dict, Any

class SalesCalculator(BaseTool):
    name = "calculate_commission"
    description = "Calculate sales commission based on revenue and rate"
    
    def _run(self, revenue: float, commission_rate: float) -> Dict[str, Any]:
        commission = revenue * commission_rate
        return {
            "revenue": revenue,
            "rate": commission_rate,
            "commission": commission,
            "net_profit": revenue - commission
        }

class ROIAnalyzer(BaseTool):
    name = "analyze_roi"
    description = "Analyze return on investment for marketing campaigns"
    
    def _run(self, cost: float, revenue: float, timeframe_days: int) -> Dict[str, Any]:
        roi = ((revenue - cost) / cost) * 100
        daily_roi = roi / timeframe_days
        return {
            "cost": cost,
            "revenue": revenue,
            "roi_percentage": roi,
            "daily_roi": daily_roi,
            "break_even_days": cost / (revenue / timeframe_days) if revenue > 0 else None
        }

# Tool registry for easy loading
TOOL_REGISTRY = {
    "calculate_commission": SalesCalculator(),
    "analyze_roi": ROIAnalyzer()
}

def get_all_function_tools():
    return list(TOOL_REGISTRY.values())
```

**Configuration**:
```yaml
# config/business_agents.yaml
agents:
  - name: "sales_analyst"
    description: "Analyzes sales data and calculates commissions"
    python_tools:
      business_calculations:
        module_path: "tools.business_tools"
        tool_names: ["calculate_commission", "analyze_roi"]
        description: "Business calculation tools"
```

### HTTP Tools (Non-MCP)

```yaml
# config/http_tools.yaml  
agents:
  - name: "api_integrator"
    description: "Integrates with various HTTP APIs"
    http_tools:
      slack_webhook:
        url: "https://hooks.slack.com/services/{{SLACK_WEBHOOK_PATH}}"
        method: "POST"
        headers:
          Content-Type: "application/json"
          
      database_api:
        url: "https://api.company.com/data/query"
        method: "POST"
        headers:
          Authorization: "Bearer {{DB_API_TOKEN}}"
          X-API-Version: "2024-01"
```

---

## Memory and Persistence

### Basic Memory Configuration

```yaml
# config/memory_enabled.yaml
# Enable memory persistence for multi-turn conversations
persistence:
  type: "memory"

# Optional: Conversation memory settings
conversation_memory:
  enabled: true
  max_conversations: 10
  max_context_length: 3000
  prepend_context: false

# Memory logging for debugging
memory_logging:
  enabled: true
  log_directory: "memory_logs"
  include_content: true
  max_content_length: 1000
```

### Advanced Memory Features

#### ChromaDB Integration
```yaml
# config/chromadb_memory.yaml
persistence:
  type: "chromadb"
  chromadb:
    persist_directory: "./chroma_db"
    collection_name: "conversation_memory"
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"

memory_integration:
  enabled: true
  search_type: "semantic"
  max_results: 5
  similarity_threshold: 0.7
```

#### Large Data Storage
```yaml
# config/large_data_memory.yaml
large_data_storage:
  enabled: true
  sqlite_path: "./data/large_tool_data.db"
  file_path: "./data/large_files/"
  compression: true
  max_sqlite_size_mb: 50
  cleanup_days: 7
```

### Memory Usage Examples

#### Conversation Continuity
```bash
# First interaction
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I am working on a machine learning project with customer data",
    "thread_id": "ml-project-thread"
  }'

# Later interaction - framework remembers context
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What preprocessing steps should I apply to the data we discussed?",
    "thread_id": "ml-project-thread"
  }'
```

#### Memory Management Operations
```bash
# Get memory statistics
curl -X GET "http://localhost:8000/memory/stats"

# Clear specific thread memory
curl -X DELETE "http://localhost:8000/memory/threads/ml-project-thread"

# Reset all memory (use with caution)
curl -X POST "http://localhost:8000/memory/reset"
```

---

## API Usage Examples

### Core Endpoints

#### Supervisor-Orchestrated Query
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze the quarterly sales report and identify trends",
    "thread_id": "sales-analysis-q4",
    "config_path": "config/sales_analysis.yaml"
  }'
```

#### Direct Agent Execution
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize the key points from this document",
    "agent_name": "document_summarizer", 
    "thread_id": "doc-summary-session"
  }'
```

#### File Upload with Processing
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "file=@financial_report.pdf" \
  -F "query=Extract key financial metrics and trends" \
  -F "agent_name=financial_analyzer" \
  -F "thread_id=financial-review"
```

### Advanced API Features

#### Consolidated Multi-Response
```bash
curl -X POST "http://localhost:8000/consolidated-responses" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      {"query": "Market analysis", "agent": "market_analyst"},
      {"query": "Financial projections", "agent": "financial_planner"},
      {"query": "Risk assessment", "agent": "risk_analyzer"}
    ],
    "thread_id": "business-planning"
  }'
```

#### Health and Status Monitoring
```bash
# System health check
curl -X GET "http://localhost:8000/health"

# Performance metrics
curl -X GET "http://localhost:8000/metrics"

# Memory statistics  
curl -X GET "http://localhost:8000/memory/stats"
```

### Python Client Examples

#### Basic Python Client
```python
import requests
import json

class JKAgentsClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def query(self, query: str, thread_id: str = None, config_path: str = None):
        payload = {"query": query}
        if thread_id:
            payload["thread_id"] = thread_id
        if config_path:
            payload["config_path"] = config_path
            
        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    
    def upload_and_process(self, file_path: str, query: str, agent_name: str):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'query': query,
                'agent_name': agent_name
            }
            response = requests.post(
                f"{self.base_url}/worker/upload",
                files=files,
                data=data
            )
        return response.json()

# Usage example
client = JKAgentsClient()

# Simple query
result = client.query(
    "Help me create a marketing strategy for a new product",
    thread_id="marketing-strategy-session"
)
print(result['response'])

# File processing
analysis = client.upload_and_process(
    "sales_data.csv",
    "Analyze this sales data and identify trends",
    "data_analyst"
)
print(analysis['response'])
```

#### Async Python Client
```python
import aiohttp
import asyncio
import json

class AsyncJKAgentsClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def query(self, session, query: str, thread_id: str = None):
        payload = {"query": query}
        if thread_id:
            payload["thread_id"] = thread_id
            
        async with session.post(
            f"{self.base_url}/query",
            json=payload
        ) as response:
            return await response.json()
    
    async def batch_queries(self, queries_and_threads):
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.query(session, query, thread_id) 
                for query, thread_id in queries_and_threads
            ]
            return await asyncio.gather(*tasks)

# Usage example
async def main():
    client = AsyncJKAgentsClient()
    
    queries = [
        ("Analyze market trends", "market-analysis"),
        ("Create financial projections", "financial-planning"),
        ("Assess competitive landscape", "competitive-analysis")
    ]
    
    results = await client.batch_queries(queries)
    for i, result in enumerate(results):
        print(f"Query {i+1} result: {result['response'][:100]}...")

asyncio.run(main())
```

---

## Troubleshooting and Best Practices

### Common Issues and Solutions

#### Issue 1: Configuration Loading Errors
**Symptoms**: `FileNotFoundError` or `ValidationError` on startup

**Solutions**:
```bash
# Check configuration file exists and is valid YAML
python -c "import yaml; yaml.safe_load(open('config/agents.yaml'))"

# Validate configuration structure
python test_config_variables.py

# Check environment variables
python -c "import os; print('OPENAI_API_KEY' in os.environ)"
```

#### Issue 2: Model Provider Authentication
**Symptoms**: `401 Unauthorized` or `403 Forbidden` errors

**Solutions**:
```bash
# Test OpenAI API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Test Azure OpenAI
curl -H "api-key: $AZURE_OPENAI_API_KEY" \
     "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=$AZURE_OPENAI_API_VERSION"

# Test Google Gemini
curl -H "x-goog-api-key: $GOOGLE_API_KEY" \
     "https://generativelanguage.googleapis.com/v1/models"
```

#### Issue 3: Tool Integration Failures
**Symptoms**: Tools not loading or execution timeouts

**Solutions**:
```bash
# Test MCP server connectivity
deno run -N jsr:@pydantic/mcp-run-python

# Check Python tool imports
python -c "from tools.python_function_tools import get_all_function_tools; print(get_all_function_tools())"

# Verify HTTP tool endpoints
curl -X GET "https://api.example.com/health"
```

#### Issue 4: Memory and Performance Issues
**Symptoms**: High memory usage or slow responses

**Solutions**:
```python
# Monitor memory usage
from app.memory_monitor import get_memory_stats
print(get_memory_stats())

# Clean up inactive threads
from app.checkpointer_manager import clear_thread_memory
clear_thread_memory("old-thread-id")

# Reset all memory if needed (caution!)
from app.checkpointer_manager import reset_all_memory
reset_all_memory()
```

### Best Practices

#### Configuration Best Practices

1. **Environment-Specific Configs**:
   ```bash
   config/
   ├── vars.local.yaml      # Development settings
   ├── vars.staging.yaml    # Staging environment  
   ├── vars.production.yaml # Production settings
   └── agents.yaml          # Base agent configuration
   ```

2. **Model Selection Strategy**:
   ```yaml
   models:
     # Fast and cost-effective for simple tasks
     default: "openai:gpt-4o-mini"
     
     # More capable for complex planning
     supervisor: "anthropic:claude-3-5-sonnet"
     
     # Multimodal capabilities when needed
     multimodal: "google:gemini-2.0-flash-exp"
     
     # High precision for critical tasks
     analytical: "azure_openai:gpt-4o:0.1"
   ```

3. **Prompt Engineering**:
   ```yaml
   agents:
     - name: "data_analyst"
       prompt: |
         You are a Data Analyst with expertise in:
         - Statistical analysis and interpretation
         - Data visualization and reporting
         - Business intelligence and insights
         
         Always:
         1. Validate data quality first
         2. Show your analytical reasoning
         3. Provide confidence levels for conclusions
         4. Suggest actionable next steps
   ```

#### Performance Best Practices

1. **Memory Management**:
   ```python
   # Enable memory logging in development
   MEMORY_LOGGING_ENABLED=true
   
   # Monitor memory usage regularly
   def monitor_memory():
       stats = get_memory_stats()
       if stats['total_memory_mb'] > 1000:  # 1GB limit
           clear_old_threads()
   ```

2. **Tool Configuration**:
   ```yaml
   agents:
     - name: "efficient_agent"
       mcp_servers:
         python_runner:
           # Reduce timeout for faster failures
           timeout: 30
           # Enable retries for transient issues
           retries: 2
   ```

3. **Concurrent Request Handling**:
   ```bash
   # Use multiple workers in production
   uvicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   
   # Configure request limits
   export MAX_CONCURRENT_REQUESTS=50
   ```

#### Security Best Practices

1. **API Key Management**:
   ```bash
   # Never commit API keys to version control
   echo ".env" >> .gitignore
   
   # Use environment-specific key management
   export OPENAI_API_KEY=$(vault kv get -field=api_key secret/openai)
   ```

2. **Input Validation**:
   ```python
   # Implement request size limits
   MAX_QUERY_LENGTH = 10000
   MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
   
   # Sanitize user inputs
   def sanitize_query(query: str) -> str:
       # Remove potential injection patterns
       return query.strip()[:MAX_QUERY_LENGTH]
   ```

3. **Error Handling**:
   ```python
   # Never expose internal errors to users
   try:
       result = process_query(query)
   except InternalError as e:
       log.error(f"Internal error: {e}")
       return {"error": "An internal error occurred"}
   ```

#### Monitoring and Observability

1. **Structured Logging**:
   ```python
   import structlog
   
   logger = structlog.get_logger("jk_agents")
   
   logger.info(
       "Query processed",
       thread_id=thread_id,
       agent_count=len(agents),
       execution_time=duration,
       success=True
   )
   ```

2. **Health Monitoring**:
   ```bash
   # Set up health check monitoring
   curl -f http://localhost:8000/health || exit 1
   
   # Monitor key metrics
   curl -s http://localhost:8000/metrics | jq '.response_times[-10:]'
   ```

3. **Performance Tracking**:
   ```python
   # Track performance metrics
   metrics = {
       "avg_response_time": sum(times) / len(times),
       "success_rate": successful_requests / total_requests,
       "memory_usage_mb": get_memory_usage(),
       "active_threads": len(active_threads)
   }
   ```

### Development Workflow

1. **Local Development Setup**:
   ```bash
   # Use development environment
   cp vars.local.yaml.example vars.local.yaml
   python run_with_env.py local uvicorn api:app --reload
   ```

2. **Testing Strategy**:
   ```bash
   # Run comprehensive tests
   python -m pytest tests/ -v --cov=app
   
   # Test specific configurations
   python test_config_variables.py config/your_agents.yaml
   
   # Performance testing
   python -m pytest tests/performance/ -v
   ```

3. **Deployment Checklist**:
   - [ ] Environment variables configured
   - [ ] Configuration files validated
   - [ ] API keys tested
   - [ ] Health checks passing
   - [ ] Memory limits configured
   - [ ] Logging configured
   - [ ] Monitoring setup
   - [ ] Backup strategy in place

This comprehensive usage guide provides practical examples and best practices for effectively using the JK-Agents Framework in various scenarios, from simple setups to complex enterprise deployments.