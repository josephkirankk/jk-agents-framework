# JK-Agents Framework

A comprehensive multi-agent system framework with supervisor planning, MCP integration, and multi-provider LLM support.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (3.11+ recommended)
- API keys for at least one LLM provider (OpenAI, Azure OpenAI, Google Gemini, or Anthropic)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd jk-agents-framework

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage
```bash
# CLI with supervisor planning
python -m app.main "Analyze the benefits of renewable energy"

# Direct agent execution
python -m app.main "What is machine learning?" --agent research_agent

# Start API server
python -m api
```

## 🏗️ Architecture

### Core Components
- **Multi-Agent System**: Supervisor coordinates specialized worker agents
- **LLM Provider Support**: OpenAI, Azure OpenAI, Google Gemini, Anthropic
- **Tool Integration**: MCP servers, HTTP tools, Python function tools
- **Web API**: FastAPI server with REST endpoints
- **CLI Interface**: Direct command-line interaction

### Agent Types
- **Supervisor Agent**: Plans and coordinates multi-step workflows
- **Worker Agents**: Specialized agents for specific tasks (research, analysis, etc.)
- **Tool-Enabled Agents**: Agents with access to external tools and APIs

## 📚 Documentation

### Getting Started
- **[Setup Guide](docs/SETUP.md)** - Complete installation and configuration
- **[Usage Guide](docs/USAGE.md)** - Examples and common workflows

### Configuration
- **[Multi-Provider Setup](docs/MULTI_PROVIDER_SETUP.md)** - Configure multiple LLM providers
- **[Python Function Tools](docs/PYTHON_FUNCTION_TOOLS.md)** - Add custom Python tools
- **[MCP Integration](docs/mcp_integration_and_llm_logging.md)** - External tool integration

### API Reference
- **[API Documentation](docs/API_DOCUMENTATION.md)** - REST API endpoints
- **[File Upload API](docs/FILE_UPLOAD_API.md)** - File processing capabilities

### Provider-Specific Guides
- **[Azure OpenAI](docs/AZURE_OPENAI_REFERENCE_CONFIG.md)** - Azure OpenAI configuration
- **[Google Gemini](docs/GOOGLE_GEMINI_INTEGRATION.md)** - Google Gemini setup
- **[Claude Sonnet 4](docs/CLAUDE_SONNET_4_INTEGRATION.md)** - Anthropic Claude integration

## 🔧 Features

### Multi-Agent Orchestration
- Supervisor-based planning and execution
- Parallel agent execution
- Context sharing between agents
- Automatic task decomposition

### LLM Provider Support
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Azure OpenAI**: Enterprise-grade deployment
- **Google Gemini**: Multimodal capabilities
- **Anthropic Claude**: Advanced reasoning
- **Local Models**: LM Studio, Ollama support

### Tool Integration
- **MCP Servers**: Model Context Protocol for external tools
- **HTTP Tools**: REST API integration
- **Python Functions**: Custom Python tool development
- **File Processing**: CSV, images, documents

### API Capabilities
- RESTful HTTP endpoints
- File upload and processing
- Thread-based conversation management
- Raw and structured response formats

## 🛠️ Configuration Examples

### Basic Multi-Agent Setup
```yaml
models:
  default: "openai:gpt-4o-mini"
  supervisor: "openai:gpt-4o"

supervisor:
  name: "supervisor"
  prompt: "You are the Supervisor. Break down requests into tasks."

agents:
  - name: "researcher"
    description: "Research and information gathering"
    prompt: "You are a research specialist."
    
  - name: "analyst"
    description: "Data analysis and insights"
    prompt: "You are a data analyst."
```

### Agent with Tools
```yaml
agents:
  - name: "web_researcher"
    description: "Web research with search tools"
    mcp_servers:
      brave_search:
        transport: "sse"
        url: "http://localhost:8080/sse"
    python_tools:
      data_tools:
        module_path: "tools.python_function_tools"
        tool_names: ["calculate_percentage", "analyze_data"]
```

## 🌐 API Examples

### Query Endpoint
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"input": "Analyze market trends for renewable energy"}'
```

### Direct Agent Execution
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "research_agent",
    "input": "What are the latest AI developments?"
  }'
```

### File Upload
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=data_analyst" \
  -F "input=Analyze this dataset" \
  -F "files=@data.csv"
```

## 🔍 Monitoring and Logging

The framework provides comprehensive logging:
- **Application Logs**: Structured console output
- **LLM Payload Logs**: Detailed interaction tracking (`logs/llm_payload_*.json`)
- **Agent Execution Logs**: CLI execution details (`direct_agentlog_*.log`)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

- **Documentation**: Check the `docs/` folder for detailed guides
- **Issues**: Report bugs and feature requests via GitHub issues
- **Examples**: See `examples/` folder for integration examples

## 🔗 Related Projects

- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent workflows
- [Model Context Protocol](https://github.com/modelcontextprotocol) - Tool integration standard

---

**Quick Links:**
- [Setup Guide](docs/SETUP.md) | [Usage Guide](docs/USAGE.md) | [API Docs](docs/API_DOCUMENTATION.md)
- [Examples](examples/) | [Configuration](config/) | [Tools](tools/)
