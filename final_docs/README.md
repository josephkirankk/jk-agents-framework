# JK-Agents Framework Documentation

## Project Overview

The **JK-Agents Framework** is a sophisticated, production-ready multi-agent AI system built on Python/FastAPI that provides a flexible, configurable platform for orchestrating multiple AI agents with supervisor-based planning and execution. It is designed for enterprise-scale AI automation with support for multiple LLM providers, advanced memory management, and extensible tool integration.

## Tech Stack

### Core Technologies
- **Python 3.11+**: Primary language
- **FastAPI**: High-performance async web framework
- **LangChain/LangGraph**: Agent orchestration and workflow management
- **ChromaDB**: Vector database for memory and embeddings
- **Pydantic**: Data validation and configuration management

### LLM Providers
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI (Enterprise deployments)
- Google Gemini (2.0 Flash, Pro models)
- Anthropic Claude (Sonnet, Opus models)
- Local models via LM Studio

### Key Libraries
- **orjson**: High-performance JSON serialization
- **psutil**: System monitoring and metrics
- **sentence-transformers**: Text embeddings
- **tiktoken**: Token counting
- **Model Context Protocol (MCP)**: Extensible tool integration

## System Architecture

```
┌────────────────────────────────────────────┐
│              FastAPI Server                 │
│                (api.py)                     │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│         Main Application Layer              │
│              (app module)                   │
├──────────────────────────────────────────────┤
│ • Agent Builder & Supervisor                │
│ • Configuration Management                  │
│ • Memory Subsystem                          │
│ • Tool Integration                          │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│          Core Utilities Layer               │
│            (core module)                    │
├──────────────────────────────────────────────┤
│ • Large Data Storage                        │
│ • Memory Monitoring                         │
│ • Smart Tool Wrapper                        │
│ • Performance Optimization                  │
└──────────────────────────────────────────────┘
```

## Module Documentation

### Core Modules

1. **[App Module](./app_module_setup_design_usage.md)**
   - Main application infrastructure
   - Agent building and orchestration
   - Supervisor-based planning
   - Request routing and execution

2. **[Core Module](./core_module_setup_design_usage.md)**
   - Multi-tier data storage
   - Memory monitoring and optimization
   - Smart tool output handling
   - System utilities

3. **[Memory Subsystem](./memory_subsystem_setup_design_usage.md)**
   - ChromaDB integration
   - High-performance caching
   - Thread and state management
   - Persistent checkpointing

4. **[Tools Module](./tools_module_setup_design_usage.md)**
   - Python function execution
   - Memory performance testing
   - Large data utilities
   - Custom tool development

### Supporting Modules

5. **Config Module**
   - YAML-based agent configuration
   - Prompt template management
   - Model provider configuration
   - Environment setup

6. **Scripts Module**
   - Testing utilities
   - Deployment scripts
   - Maintenance tools
   - Performance benchmarks

7. **PepGenX OpenAI Wrapper**
   - OpenAI-compatible API wrapper
   - Production deployment support
   - Authentication and rate limiting
   - Docker containerization

## Entry Points

### Primary API Endpoints

```python
# Main supervisor endpoint
POST /query
{
    "query": "Your complex task",
    "config_name": "agent_config"
}

# Direct agent execution
POST /worker
{
    "agent_name": "data_analyst",
    "query": "Analyze this data"
}

# File upload with processing
POST /worker/upload

# Health check
GET /health

# Memory management
POST /memory/stats
POST /memory/clear/{thread_id}
POST /memory/reset
```

### Command-Line Interface

```bash
# Start the API server
uvicorn api:app --reload --port 8000

# Run direct agent
python -m app.main --agent data_analyst --query "Your query"

# Test configuration
python scripts/test_config.py config/agents.yaml

# Run performance tests
python tools/memory_performance_tools.py benchmark
```

## Quick Start Guide

### 1. Installation

```bash
# Clone repository
git clone https://github.com/your-org/jk-agents-framework.git
cd jk-agents-framework

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=your_key
# GOOGLE_API_KEY=your_key
# ANTHROPIC_API_KEY=your_key
```

### 3. Create Agent Configuration

```yaml
# config/agents.yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "google:gemini-1.5-pro"

supervisor:
  name: "supervisor"
  prompt_file: "prompts/supervisor.md"

agents:
  - name: "assistant"
    model: "google:gemini-2.0-flash-lite-001"
    prompt_file: "prompts/assistant.md"
```

### 4. Start the Server

```bash
uvicorn api:app --reload
```

### 5. Test the System

```bash
# Test supervisor endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, what can you do?"}'
```

## Key Features

### Multi-Agent Orchestration
- **Supervisor Pattern**: Intelligent task decomposition and agent assignment
- **Specialized Agents**: Domain-specific agents with custom capabilities
- **Dynamic Routing**: Automatic selection of appropriate agents
- **Dependency Management**: Handles inter-step dependencies

### Advanced Memory Management
- **Persistent Storage**: ChromaDB-backed conversation history
- **Multi-Level Caching**: Sub-millisecond retrieval times
- **Thread Isolation**: Separate memory spaces per conversation
- **Automatic Optimization**: Self-tuning based on usage patterns

### Flexible Tool Integration
- **Model Context Protocol**: Standardized tool interface
- **Python Functions**: Native Python function execution
- **HTTP/REST APIs**: External service integration
- **Dynamic Tools**: Runtime tool generation

### Production Features
- **High Performance**: Async/await architecture with connection pooling
- **Scalability**: Horizontal scaling support with distributed backends
- **Monitoring**: Real-time metrics and performance tracking
- **Security**: User isolation, rate limiting, authentication hooks

## Use Cases

### Enterprise AI Automation
- Complex business process automation
- Multi-step document processing
- Customer support orchestration
- Data analysis pipelines

### Research & Development
- Multi-modal AI experimentation
- LLM provider comparison
- Custom tool development
- Performance benchmarking

### Application Development
- AI-powered applications
- Conversational interfaces
- Workflow automation
- Integration platforms

## Performance Characteristics

### Throughput
- **Requests/Second**: 100-500 (depending on model and complexity)
- **Concurrent Users**: 1000+ with proper scaling
- **Memory Retrieval**: <10ms with cache hits

### Resource Usage
- **Memory**: 512MB - 2GB per instance
- **CPU**: 2-4 cores recommended
- **Storage**: 10GB+ for persistent memory

### Scalability
- Horizontal scaling via load balancing
- Distributed ChromaDB support
- Connection pooling for efficiency
- Auto-scaling based on metrics

## Development Guidelines

### Code Organization
```
jk-agents-framework/
├── app/                 # Main application
│   ├── memory/         # Memory subsystem
│   └── placeholder/    # Template system
├── core/               # Core utilities
├── tools/              # Tool implementations
├── config/             # Configurations
│   └── prompts/       # Prompt templates
├── scripts/            # Utility scripts
├── tests/              # Test suites
└── docs/              # Documentation
```

### Best Practices
1. Use type hints and docstrings
2. Follow PEP 8 style guidelines
3. Write comprehensive tests
4. Document configuration changes
5. Monitor performance metrics

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Verify environment variables
   - Check key permissions
   - Monitor rate limits

2. **Memory Issues**
   - Check ChromaDB status
   - Review cache configuration
   - Monitor disk space

3. **Performance Problems**
   - Enable caching
   - Optimize prompts
   - Use appropriate models

4. **Configuration Errors**
   - Validate YAML syntax
   - Check file paths
   - Review logs

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Run tests before committing
5. Submit pull request

### Testing
```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/test_memory.py

# Run with coverage
pytest --cov=app --cov=core
```

## License

[Specify your license here]

## Support

- Documentation: This folder
- Issues: GitHub Issues
- Email: support@your-org.com

## Roadmap

### Upcoming Features
- GraphQL API support
- Additional LLM providers
- Enhanced monitoring dashboard
- Kubernetes deployment manifests
- WebSocket real-time updates

### Version History
- v1.0.0 - Initial release with core functionality
- v1.1.0 - Added memory subsystem
- v1.2.0 - Multi-provider support
- v1.3.0 - Performance optimizations
- v1.4.0 - Production enhancements

---

*Last Updated: December 2024*