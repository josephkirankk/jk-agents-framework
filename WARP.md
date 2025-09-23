# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (CRITICAL: Always use .venv)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys (OpenAI, Azure OpenAI, Anthropic, Google, etc.)
```

### Running the System
```bash
# CLI mode with supervisor planning
python -m app.main "Your query here"

# Direct agent execution (bypass supervisor)
python -m app.main "Your query here" --agent agent_name

# Start API server (multiple ways)
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
python -m api
python api.py

# Start with custom endpoint/config
python scripts/start_with_custom_endpoint.py
```

### Testing Framework
```bash
# Core system tests
python test_agent_unicode.py          # Unicode/encoding tests
python test_api_unicode.py            # API unicode handling
python test_consolidated_responses.py # Response consolidation
python test_format_compliance.py      # Output format validation

# Multi-provider testing
python scripts/test_multi_provider.py     # Multi-LLM provider setup
python scripts/test_gemini_api.py         # Google Gemini integration
python scripts/test_custom_endpoint_integration.py  # Custom endpoints

# Specialized pipeline testing
python gemba_agents/defect_analysis/test_pipeline.py    # Defect analysis
python gemba_agents/pilger_processing/test_pipeline.py  # Pilger processing
python gemba_agents/tsdefects_pipeline/test_pipeline.py # Time series defects

# Integration and consistency testing
python final_consistency_test.py      # End-to-end consistency
python test_langchain_integration.py  # LangChain compatibility
python test_thread_continuity.ps1     # Thread memory persistence (Windows)

# API testing (comprehensive)
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"input": "test query"}'
curl -X POST "http://localhost:8000/worker" -H "Content-Type: application/json" -d '{"agent_name": "agent_name", "input": "test query"}'
curl -X POST "http://localhost:8000/worker/upload" -F "agent_name=data_agent" -F "input=analyze this" -F "files=@data.csv"

# VectorDB testing
python test_vectordb_wrapper.py       # Vector database operations
python -m vectordb_wrapper.cli        # Interactive VectorDB CLI

# Memory system testing
python basic_memory_test.bat          # Windows batch test
python simple_memory_test.ps1         # PowerShell memory test
```

### Configuration Management
```bash
# Test with specific configuration
python -m app.main "Your query" --config config/your-config.yaml

# List available configurations
dir config\*.yaml  # Windows
ls config/*.yaml   # Linux/Mac

# Test specific config patterns
python -m app.main "test" --config config/multi_provider_example.yaml    # Multi-provider
python -m app.main "test" --config config/gemini-test.yaml               # Google Gemini
python -m app.main "test" --config config/claude-sonnet-4-demo.yaml      # Anthropic Claude
python -m app.main "test" --config config/azure_openai_reference.yaml    # Azure OpenAI
```

### Specialized Tool Commands
```bash
# PepGenX wrapper (OpenAI-compatible API)
cd pepgenx_openai_wrapper
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
python scripts/pepgenx_cli.py         # CLI interface

# VectorDB operations
python -m vectordb_wrapper.cli        # Interactive VectorDB CLI
python start_vectordb_cli.bat         # Windows batch starter
python start_vectordb_cli.sh          # Linux/Mac starter

# Model debugging and verification
python debug_model_initialization.py  # Model setup debugging
python check_llm_payload.py          # LLM interaction logging
```

## Architecture Overview

### Core System Design
- **Supervisor-Worker Pattern**: A supervisor agent creates execution plans that coordinate multiple specialized worker agents
- **Multi-Provider LLM Support**: OpenAI, Azure OpenAI, Google Gemini, Anthropic Claude, and local/custom endpoints (LM Studio, etc.)
- **Tool Integration**: MCP (Model Context Protocol) servers, HTTP tools, Python function tools, VectorDB integrations
- **Memory Management**: Persistent conversation threads with checkpointing and attribute storage
- **API & CLI Interfaces**: FastAPI web server and command-line interfaces with comprehensive logging
- **Placeholders System**: Advanced dynamic template substitution with validation and error handling
- **Unicode Support**: Cross-platform UTF-8 handling for multilingual systems

### Key Components
- **`app/main.py`**: Entry point for CLI execution, handles both supervised and direct agent execution
- **`api.py`**: FastAPI web server providing REST endpoints (`/query`, `/worker`, file upload, specialized pipelines)
- **`app/supervisor_builder.py`**: Builds supervisor agents that create and coordinate execution plans
- **`app/agent_builder.py`**: Builds worker agents with tool integration (MCP, HTTP, Python functions)
- **`app/planner_executor.py`**: Executes multi-step plans created by supervisor agents
- **`app/config.py`**: Pydantic configuration models for agents, tools, and system settings
- **`app/checkpointer_manager.py`**: Thread-based memory persistence and retrieval
- **`app/placeholder_system/`**: Enhanced system for dynamic template interpolation
- **`app/mcp_loader.py`**: MCP server integration and communication
- **`app/llm_payload_logger.py`**: Comprehensive LLM interaction logging
- **`app/direct_agent_logger.py`**: Individual agent execution logging
- **`app/thread_manager.py`**: Thread management for conversation continuity

### Agent System Architecture
1. **Supervisor Agent**: Analyzes user requests and creates JSON execution plans with parallel/sequential steps
2. **Worker Agents**: Specialized agents with specific capabilities (research, analysis, computation, formatting)
3. **Tool Integration**: Agents can be equipped with:
   - MCP servers (external tools via Model Context Protocol)
   - HTTP tools (REST API integrations)
   - Python function tools (custom Python code as tools)
   - VectorDB searches (semantic retrieval)
4. **Memory System**: Thread-based conversation persistence with multiple storage options:
   - In-memory checkpointing for short-term persistence
   - Attribute storage for structured data retention
   - Thread continuity management for conversation context
5. **LLM Provider Management**:
   - Provider-specific client initialization and configuration
   - Model mapping and normalization
   - Fallback mechanisms between providers
   - Dynamic provider selection based on availability

### Configuration System
- **YAML-based**: All agent configurations defined in `config/*.yaml` files
- **Multi-Provider Models**: Use prefixes like `openai:`, `azure_openai:`, `google:`, `anthropic:`, with automatic mapping
- **Template Support**: Jinja2 templates with advanced placeholder system for business context, user questions, agent lists
- **Tool Configuration**: Declarative configuration for MCP servers, HTTP endpoints, Python tools
- **Prompt Management**: Supports inline prompts and external prompt files in `config/prompts/`
- **Environment Integration**: Intelligent handling of environment variables for credentials and endpoints
- **Temperature Control**: Global and per-agent temperature configuration

### Specialized Pipelines and Components

#### Manufacturing-Focused Pipelines
- **Defect Analysis Pipeline** (`gemba_agents/defect_analysis/`): Manufacturing defect analysis with structured outputs
- **Pilger Processing Pipeline** (`gemba_agents/pilger_processing/`): Industrial process optimization and fault detection
- **TSDefects Pipeline** (`gemba_agents/tsdefects_pipeline/`): Time series defect detection and analysis

#### Integration Components
- **PepGenX OpenAI Wrapper** (`pepgenx_openai_wrapper/`): OpenAI-compatible API for PepGenX platform
- **VectorDB Wrapper** (`vectordb_wrapper/`): Vector database client for semantic search integrations
- **Python Function Tools** (`tools/python_function_tools.py`): Custom Python functions as agent tools

#### Testing and Utilities
- **Multiplatform Scripts**: Cross-platform compatibility for Windows/Linux/Mac
- **Comprehensive Testing**: Unit, integration, and end-to-end testing for all components
- **Debug Utilities**: Model initialization debugging, LLM payload inspection, encoding verification

## Development Patterns

### Adding New Agents
1. Create agent configuration in `config/*.yaml`:
   ```yaml
   agents:
     - name: "my_new_agent"
       description: "Purpose and capabilities"
       model: "openai:gpt-4o-mini"  # or provider:model format
       prompt: |
         Your system prompt here
         {{business_context}}  # Use placeholders
         {{dependent_request_responses}}  # For supervisor chains
       mcp_servers:  # Optional tools
         tool_name:
           transport: "stdio"  # or "sse", "http"
           command: "python server.py"
   ```
2. Test with CLI: `python -m app.main "test" --agent my_new_agent --config config/my-config.yaml`
3. Test with API: `POST /worker` with `agent_name` parameter
4. Add to documentation in `docs/` folder

### Tool Integration Patterns

#### MCP Server Integration (Recommended)
```yaml
mcp_servers:
  # stdio transport (most common)
  python_runner:
    transport: "stdio"
    command: "deno"
    args: ["run", "-N", "jsr:@pydantic/mcp-run-python", "stdio"]
    
  # HTTP/SSE transport
  web_search:
    transport: "sse"
    url: "http://localhost:8080/sse"
    headers:
      Authorization: "Bearer token"
      
  # Environment variables for MCP
  server_with_env:
    transport: "stdio"
    command: "python"
    args: ["server.py"]
    env:
      API_KEY: "${EXTERNAL_API_KEY}"
```

#### Python Function Tools
```yaml
# In agent configuration
python_tools:
  data_tools:
    module_path: "tools.python_function_tools"
    tool_names: ["calculate_percentage", "analyze_data", "count_csv_rows"]
  
  custom_tools:
    module_path: "my_custom_tools"
    # tool_names: [] omitted means load all functions with @tool decorator
```

#### HTTP Tools (Simple REST APIs)
```yaml
http_tools:
  api_endpoint:
    url: "https://api.example.com/data"
    method: "POST"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
```

### Multi-Provider Model Configuration

#### Provider Prefixes and Auto-Mapping
```yaml
models:
  # Azure OpenAI (auto-detects from env vars)
  default: "azure_openai:gpt-4o-mini"
  supervisor: "azure_openai:gpt-4o"
  
  # Google Gemini
  multimodal: "google:gemini-2.0-flash-exp"
  text_only: "google:gemini-1.5-pro"
  
  # Anthropic Claude
  reasoning: "anthropic:claude-sonnet-4-20250514"
  
  # Local LM Studio (uses OPENAI_BASE_URL)
  local: "openai:llama-3.2-3b"
  experimental: "openai:google/gemma-3n-e4b"
  
  # Regular OpenAI
  openai_direct: "openai:gpt-4o-mini"
  
temperature: 0.2  # Global default
```

#### Environment Variable Patterns
```bash
# Azure OpenAI (preferred for enterprise)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# LM Studio or custom OpenAI-compatible
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio

# Google Gemini
GOOGLE_API_KEY=your-google-key

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-key
```

### Advanced Configuration Patterns

#### Prompt Files and Templates
```yaml
# External prompt file
agents:
  - name: "complex_agent"
    prompt_file: "prompts/specialized_prompt.txt"  # relative to config dir
    
# Jinja2 templates with placeholders
prompt: |
  Business context: {{business_context}}
  Original question: {{original_user_question}}
  Previous responses: {{dependent_request_responses}}
  Available tools: {{mcpservers}}
  
  You are {{agent_name}} with expertise in {{domain}}.
```

#### Conditional Model Selection
```yaml
# Different models for different agents
agents:
  - name: "fast_agent"
    model: "openai:gpt-4o-mini"  # Fast, cost-effective
    
  - name: "reasoning_agent"
    model: "anthropic:claude-sonnet-4-20250514"  # Best reasoning
    
  - name: "multimodal_agent"
    model: "google:gemini-2.0-flash-exp"  # Images, videos, etc.
    
  - name: "local_dev_agent"
    model: "openai:llama-3.2-3b"  # Privacy, development
```

### Error Handling and Logging

#### Logging System Architecture
- **LLM Payload Logs**: Detailed request/response logs in `logs/llm_payload_*.json`
- **Agent Execution Logs**: CLI execution details in `direct_agentlog_*.log`
- **Vector Logs**: VectorDB operations in `vectorlogs/`
- **Archive Logs**: Historical logs in `archive_logs/`
- **Demo Logs**: Testing logs in `demo_logs/`

#### Error Patterns and Handling
```python
# MCP server error filtering (app/mcp_loader.py)
# Filters out empty arrays and strings that cause API errors
if isinstance(payload, dict):
    filtered_payload = {}
    for key, value in payload.items():
        if isinstance(value, list) and len(value) == 0:
            continue  # Skip empty arrays
        if isinstance(value, str) and value == "":
            continue  # Skip empty strings
        filtered_payload[key] = value
```

#### Unicode and Cross-Platform Support
- **UTF-8 Encoding**: Proper handling of multilingual text (Hindi, Chinese, etc.)
- **Windows/Mac/Linux**: Cross-platform file paths and commands
- **PowerShell/Bash**: Platform-specific scripts with fallbacks

## API Endpoints Reference

### Core Endpoints
- `GET /health` - Basic health check
- `POST /query` - Supervised multi-agent execution with planning
- `POST /worker` - Direct single agent execution
- `POST /worker/upload` - File upload with agent processing (multimodal)
- `GET /models` - List available models

### Specialized Pipeline Endpoints
- `POST /defect-analysis` - Manufacturing defect analysis (JSON)
- `POST /defect-analysis-with-pilger` - Enhanced defect analysis with Pilger ontology
- `POST /defect-analysis-with-pilger/form` - Form-based defect analysis
- `POST /pilger-processing` - Industrial process optimization
- `POST /tsdefects-pipeline` - Time series defect detection

### Memory and Thread Management
- `GET /memory/stats` - Memory usage statistics
- `DELETE /memory/thread/{thread_id}` - Clear specific thread memory
- `DELETE /memory/reset` - Reset all memory (use with caution)
- `GET /threads` - List active threads
- `GET /threads/{thread_id}` - Get thread details

### File Upload and Processing
- **Supported Formats**: Images (PNG, JPG, WebP), Documents (CSV, TXT, PDF)
- **Multimodal Processing**: Combined text + image analysis
- **Batch Processing**: Multiple files in single request
- **OpenAI File Integration**: Automatic file upload to OpenAI for compatible models

### Request/Response Patterns
```bash
# Supervised execution
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"input": "analyze market trends", "config_path": "config/gemini-test.yaml"}'

# Direct agent execution
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "research_agent", "input": "research topic"}'

# File upload with processing
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analyst" \
  -F "input=Analyze this data" \
  -F "files=@data.csv" \
  -F "files=@chart.png"

# Manufacturing defect analysis
curl -X POST "http://localhost:8000/defect-analysis-with-pilger/form" \
  -F "user_input=rack पट्टी के बोल्ट लूज हो गए हैं" \
  -F "top_n=5" \
  -F "min_score=0.6"
```

## Specialized Components Deep Dive

### VectorDB Wrapper (`vectordb_wrapper/`)
- **Purpose**: Semantic search and vector operations for defect analysis
- **CLI**: `python -m vectordb_wrapper.cli` - Interactive vector database operations
- **Client**: Async/sync clients for search, upsert, health checks
- **Models**: Pydantic models for requests/responses with validation
- **Typesense Integration**: Specialized Typesense search client (`ts_client.py`) for hybrid/keyword/vector search
- **Logging**: Comprehensive vector operation logging in `vectorlogs/`

### PepGenX OpenAI Wrapper (`pepgenx_openai_wrapper/`)
- **Purpose**: OpenAI-compatible API wrapper for PepGenX platform integration
- **Features**: Full OpenAI Chat Completions API compatibility, OKTA authentication, Docker support
- **Models**: Support for GPT-4, Claude, custom models through PepGenX
- **Production Ready**: Monitoring, health checks, rate limiting, CORS support

### Manufacturing Pipelines (`gemba_agents/`)
- **Defect Analysis Pipeline**: Multilingual defect interpretation with vector search
- **Pilger Processing Pipeline**: Industrial process optimization with specialized ontology
- **TSDefects Pipeline**: Time series defect pattern detection and correlation

### Memory and Persistence Systems
- **Thread Management** (`app/thread_manager.py`): Conversation continuity across sessions
- **Checkpointer System** (`app/checkpointer_manager.py`): Global memory persistence
- **Placeholder System** (`app/placeholder_system/`): Advanced dynamic template processing

## Key Environment Variables

### LLM Provider Configuration
```bash
# Azure OpenAI (Enterprise)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# OpenAI Direct / Custom Endpoints
OPENAI_API_KEY=sk-your-openai-key
OPENAI_BASE_URL=http://127.0.0.1:1234/v1  # For LM Studio, etc.

# Google Gemini
GOOGLE_API_KEY=your-google-api-key

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-api-key
```

### External Service Integration
```bash
# PepGenX Integration
PEPGENX_API_URL=your-pepgenx-endpoint
PEPGENX_PROJECT_ID=your-project-id

# VectorDB Integration
VECTORDB_BASE_URL=http://localhost:8010

# OKTA Authentication
OKTA_DOMAIN=https://your-domain.oktapreview.com
OKTA_CLIENT_ID=your-client-id
OKTA_TOKEN_FILE=okta_token.json

# LangSmith Tracing (Optional)
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=jk-agents-production
```

## Critical Development Notes

### Always Follow These Patterns
1. **Use Virtual Environment**: Always activate `.venv` before running any code
2. **Cross-Platform Compatibility**: Code must work on Windows, macOS, and Linux
3. **UTF-8 Encoding**: Handle Unicode properly (Hindi, Chinese, special characters)
4. **Error Handling**: Implement comprehensive error handling with proper logging
5. **Documentation**: Document all changes in `docs/` folder, fixes in `fixes_docs/`
6. **Testing**: Test extensively with multiple providers and configurations
7. **Memory Management**: Clean up threads and checkpointers appropriately
8. **Security**: Never commit API keys or sensitive data

### Common Troubleshooting

#### Unicode Issues (Windows)
```python
# Always specify UTF-8 encoding
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
# For API responses
response = requests.post(url, json=data)
response.encoding = 'utf-8'
```

#### MCP Server Connection Issues
```bash
# Test MCP server connectivity
python app/mcp_test.py
# Check MCP server logs for errors
# Verify transport type (stdio/sse/http) matches configuration
```

#### Memory/Threading Issues  
```bash
# Check memory statistics
curl -X GET "http://localhost:8000/memory/stats"
# Reset memory if needed (development only)
curl -X DELETE "http://localhost:8000/memory/reset"
```

## Working with Degirum
When working with Degirum-related functionality, always refer to the Degirum documentation located at `C:\JK\dev\docs.degirum.com` before implementing or fixing any Degirum-specific code.

## Project Structure Summary
```
jk-agents/
├── .augment/               # Augment rules and configuration
├── .github/                # GitHub workflow configurations
├── .vscode/                # VS Code workspace settings
├── agentlog/               # Agent execution logs
├── app/                    # Core framework (main application)
├── archive_logs/           # Historical log files
├── code-storage/           # Code storage and examples
├── config/                 # Agent configurations (YAML files)
├── curl_scripts/           # cURL testing scripts
├── demo_logs/              # Demo and testing logs
├── docs/                   # Comprehensive documentation
├── examples/               # Usage examples and sample code
├── fixes_docs/             # Bug fix documentation
├── gemba_agents/           # Manufacturing-focused pipelines
├── logs/                   # Runtime logs
├── node_modules/           # Node.js dependencies (for MCP servers)
├── pepgenx_openai_wrapper/ # PepGenX OpenAI-compatible API wrapper
├── scripts/                # Testing and utility scripts
├── tests/                  # Test files (some in root, some in subdirs)
├── tools/                  # Python function tools
├── user_responses/         # User response storage
├── vectordb_wrapper/       # Vector database client and CLI
├── api.py                  # FastAPI web server (main entry point)
├── WARP.md                 # This file (Warp guidance)
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── test_*.py               # Root-level test files (40+ testing scripts)
```

