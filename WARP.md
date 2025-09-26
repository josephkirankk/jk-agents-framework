# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Essential Commands

### Development Server
```bash
# Start the FastAPI server (main development command)
uvicorn api:app --reload --port 8000

# Alternative with specific host binding
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Direct Agent Execution (CLI)
```bash
# Run a specific agent directly without supervisor
python -m app.main "Your question here" --agent agent_name

# Example: Run python execution agent
python -m app.main "Calculate 2^8 + 15" --agent python_exec_agent

# Use custom configuration file
python -m app.main "Your question here" --config config/custom_agents.yaml
```

### Testing & Validation
```bash
# Test specific configurations
python scripts/test_config.py config/agents_test.yaml

# Test API endpoints
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, what can you do?"}'

# Test worker endpoints
curl -X POST http://localhost:8000/worker \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "python_exec_agent", "input": "Calculate 5 * 5"}'

# Run Gemini API tests
python scripts/test_gemini_api.py
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys

# Test different providers
python scripts/antropic_test.py  # Test Anthropic
python scripts/test_custom_endpoint_integration.py  # Test custom endpoints
```

## Architecture Overview

### Multi-Agent System Design
- **Supervisor Pattern**: The `supervisor_builder.py` creates planning agents that decompose complex tasks into executable steps
- **Specialized Agents**: Domain-specific agents built via `agent_builder.py` with custom prompts and tools
- **Execution Orchestration**: `planner_executor.py` manages step execution, dependencies, and data flow between agents

### Core Data Flow
1. **Request** → `api.py` (FastAPI endpoints)
2. **Configuration Loading** → `config.py` + YAML files
3. **Agent Building** → `agent_builder.py` + `supervisor_builder.py`
4. **Plan Execution** → `planner_executor.py`
5. **Memory Management** → `checkpointer_manager.py` + ChromaDB
6. **Response Formatting** → `markdown_formatter.py`

### Multi-Provider LLM Support
The system supports simultaneous use of multiple LLM providers through provider prefixes:
- `openai:model-name` - OpenAI API or custom OpenAI-compatible endpoints
- `azure_openai:deployment-name` - Azure OpenAI deployments
- `google:model-name` - Google Gemini models
- `anthropic:model-name` - Anthropic Claude models

Provider selection is automatic based on environment variables and model prefixes.

### Memory & Persistence
- **Thread Management**: Each conversation gets a unique thread ID for memory isolation
- **ChromaDB Integration**: Vector database for persistent memory and context retrieval
- **Multi-level Caching**: L1 cache + connection pooling for performance
- **Memory Metrics**: Built-in monitoring and cleanup utilities

### Tool Integration (MCP)
- **Model Context Protocol**: Extensible tool system through MCP servers
- **Built-in Tools**: Python execution, web scraping, file operations
- **Custom Tools**: Configure via `mcp_servers` in agent YAML configs
- **Transport Support**: stdio, HTTP, and SSE transports

## Configuration System

### Agent Configuration Structure
```yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "google:gemini-1.5-pro"

business_context: |
  Shared context across all agents

supervisor:
  name: "supervisor"
  prompt: "Supervisor planning prompt"

agents:
  - name: "specialized_agent"
    description: "Agent description"
    model: "google:gemini-2.0-flash-lite-001"
    prompt: "Agent-specific prompt template"
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args: ["run", "-N", "jsr:@pydantic/mcp-run-python", "stdio"]
```

### Key Configuration Files
- `config/agents_test.yaml` - Basic testing configuration
- `config/ado_*.yaml` - Production configurations for specific use cases
- `.env.example` - Complete environment variable reference

## Development Guidelines

### Adding New Agents
1. Define agent configuration in YAML with unique name
2. Create specialized prompt template with `{{dependent_request_responses}}` for multi-step workflows
3. Configure required MCP servers for tools
4. Test via `/worker` endpoint before integrating into supervisor workflows

### Memory System Usage
- Thread IDs are automatically generated for CLI usage
- API endpoints accept optional `thread_id` for conversation continuity
- Memory stats available at `/memory/stats` endpoint
- Clear specific thread memory via `/memory/clear/{thread_id}`

### Multi-Step Workflow Design
- Supervisors break tasks into steps with dependencies (`depends_on` array)
- Each step specifies `timeout_seconds` and `retry` counts
- Use `verify` field for step validation criteria
- Steps can run in parallel when no dependencies exist

### Provider-Specific Considerations
- **Azure OpenAI**: Requires endpoint, deployment name, and API version
- **Google Gemini**: Supports multimodal capabilities (text + images)
- **Custom Endpoints**: Use `OPENAI_BASE_URL` for LM Studio, Ollama, etc.
- **Local Development**: LM Studio integration via OpenAI-compatible API

### Performance Optimization
- Connection pooling is enabled by default
- ChromaDB batch processing for memory operations
- Async/await pattern throughout the codebase
- L1 caching with configurable TTL

### File Upload Support
- CSV files are processed locally and embedded in prompts
- Images and documents are uploaded to OpenAI/Azure for multimodal processing
- Use `/worker/upload` endpoint for file-based workflows

## Key Files to Understand

### Core Application
- `api.py` - Main FastAPI server with all endpoints
- `app/main.py` - CLI interface and core orchestration functions
- `app/config.py` - Pydantic models for configuration validation

### Agent System
- `app/agent_builder.py` - React agent construction with tools and memory
- `app/supervisor_builder.py` - Supervisor agent for task planning
- `app/planner_executor.py` - Multi-step plan execution engine

### Memory & Tools
- `app/checkpointer_manager.py` - Memory persistence and management
- `app/mcp_loader.py` - Model Context Protocol tool integration
- `app/thread_manager.py` - Conversation thread management

### Utilities
- `app/template_utils.py` - Jinja2 template rendering for prompts
- `app/markdown_formatter.py` - Response formatting for user presentation
- `app/direct_agent_logger.py` - Comprehensive execution logging

## Common Troubleshooting

### Configuration Issues
- Verify YAML syntax with `python -c "import yaml; yaml.safe_load(open('config/your_file.yaml'))"`
- Check environment variables match provider requirements
- Ensure agent names in config match those used in requests

### Memory Problems
- ChromaDB files in `*_memory/` and `chroma_memory/` directories
- Use `/memory/stats` to monitor memory usage
- Clear specific threads with `/memory/clear/{thread_id}`

### MCP Tool Issues
- Verify MCP server commands are executable in your environment
- Check stdio transport configuration for Python tools
- Test tools individually before integrating into agents

### Provider Authentication
- OpenAI: `OPENAI_API_KEY`
- Azure: `AZURE_OPENAI_*` environment variables
- Google: `GOOGLE_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`

## Production Considerations

### Resource Limits
- Memory usage: 512MB - 2GB per instance
- ChromaDB requires persistent storage
- Connection pooling configured per provider
- Async processing for concurrent requests

### Scaling Patterns
- Horizontal scaling via load balancer
- Distributed ChromaDB for shared memory
- Provider-specific rate limiting
- Thread-based memory isolation

### Security Notes  
- API keys stored in environment variables only
- User isolation through thread management
- Input validation on all endpoints
- CORS configured for production deployment