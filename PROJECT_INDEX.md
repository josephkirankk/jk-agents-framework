# JK-Agents Framework - Project Index

## Overview

The **jk-agents-framework** is a sophisticated multi-agent AI system built on Python/FastAPI that provides a flexible, configurable platform for orchestrating multiple AI agents with supervisor-based planning and execution. The framework supports multiple LLM providers (OpenAI, Azure OpenAI, Google Gemini, Anthropic Claude) and integrates with the Model Context Protocol (MCP) for extensible tool capabilities.

## Core Architecture

### Multi-Agent System Design
- **Supervisor Agent**: Plans and orchestrates tasks by breaking them down into steps and assigning them to specialized agents
- **Specialized Agents**: Each agent is configured with specific prompts, models, and capabilities for different tasks
- **Agent Builder**: Dynamically builds React agents with tools and memory capabilities
- **Thread Management**: Handles conversation threads and memory persistence across interactions

### Key Components

```
jk-agents-framework/
├── app/                          # Core application modules
│   ├── agent_builder.py         # Agent construction and configuration
│   ├── supervisor_builder.py    # Supervisor agent construction
│   ├── planner_executor.py      # Plan execution and orchestration
│   ├── mcp_loader.py            # Model Context Protocol integration
│   ├── config.py               # Configuration models (Pydantic)
│   ├── thread_manager.py       # Thread and memory management
│   └── placeholder_system/     # Placeholder replacement system
├── api.py                      # FastAPI web server and endpoints
├── config/                     # Agent configurations and prompts
├── tools/                     # Custom tool implementations
├── pepgenx_openai_wrapper/    # OpenAI-compatible API wrapper
├── scripts/                   # Testing and utility scripts
└── tools/                     # Custom tool implementations
```

## Multi-Provider LLM Support

The framework supports multiple AI providers simultaneously through a flexible configuration system:

- **OpenAI API**: Standard OpenAI models (`openai:gpt-4o`, `openai:gpt-3.5-turbo`)
- **Azure OpenAI**: Enterprise Azure deployments (`azure_openai:deployment-name`)
- **Google Gemini**: Multimodal capabilities (`google:gemini-2.0-flash-exp`)
- **Anthropic Claude**: Claude models (`anthropic:claude-sonnet-4`)
- **Local LM Studio**: Local model serving via OpenAI-compatible API

## Agent Configuration System

Agents are configured through YAML files with the following structure:

```yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "google:gemini-1.5-pro"

business_context: |
  Context shared across all agents

supervisor:
  name: "supervisor"
  prompt: |
    Supervisor planning prompt template

agents:
  - name: "specialized_agent"
    description: "Agent description"
    model: "google:gemini-2.0-flash-lite-001"
    prompt: |
      Agent-specific prompt
    mcp_servers:
      tool_name:
        transport: "stdio"
        command: "python"
        args: ["tool_script.py"]
```

## Core Features

### 1. Supervisor-Based Planning
- Breaks complex tasks into executable steps
- Assigns steps to appropriate specialized agents
- Handles dependencies and sequential execution
- Supports retry logic and timeout management

### 2. Model Context Protocol (MCP) Integration
- Extensible tool system through MCP servers
- Supports stdio, HTTP, and SSE transports
- Built-in tools: Python execution, web scraping, file operations
- Custom tool development capabilities

### 3. Memory and Thread Management
- Persistent conversation threads
- Memory checkpointing and restoration
- Thread-specific agent state management
- Memory statistics and cleanup utilities

### 4. Multimodal Capabilities
- File upload and processing (CSV, images, documents)
- Image analysis with Google Gemini vision models
- Document parsing and content extraction
- Multimodal agent responses

## Specialized Agent Pipelines

### Example Specialized Pipelines
- **Data Processing Pipeline**: Handles structured data analysis and transformation
- **Multi-Modal Pipeline**: Processes text, images, and documents together
- **Workflow Orchestration**: Coordinates multiple agents for complex tasks

### PepGenX OpenAI Wrapper
- OpenAI-compatible API wrapper for PepGenX platform
- Production-ready with authentication, rate limiting, and monitoring
- Docker containerization support
- Health checks and metrics endpoints

## API Endpoints

### Core Endpoints
- `POST /query` - Supervisor-orchestrated multi-agent queries
- `POST /worker` - Direct agent execution
- `POST /worker/upload` - File upload with agent processing
- `GET /health` - System health checks
- `POST /memory/*` - Memory management operations

### Specialized Endpoints
- `POST /consolidated-responses` - Batch processing capabilities
- Custom pipeline endpoints for domain-specific workflows
- Extensible API architecture for new processing types

## Installation and Setup

### Prerequisites
- Python 3.11+
- One or more LLM provider API keys
- Optional: Docker for containerized deployment

### Configuration
1. Copy `.env.example` to `.env`
2. Configure API keys for desired providers
3. Create agent configuration YAML files
4. Start the FastAPI server: `uvicorn api:app --reload`
## Key Technologies

- **FastAPI**: High-performance async web framework
- **LangChain**: LLM integration and agent orchestration
- **Pydantic**: Data validation and configuration management
- **Model Context Protocol**: Extensible tool integration

## Testing and Validation Documentation
- [Framework Demo Guide](docs/FRAMEWORK_DEMO.md) - Step-by-step guide for running framework demos
- [Memory Performance Analysis](docs/MEMORY_PERFORMANCE_ANALYSIS.md) - Detailed analysis of jk-agents memory system performance
- [Test Results Documentation](TEST_RESULTS.md) - Comprehensive test results and analysis
- [**Advanced Memory Agent Test Documentation**](docs/ADVANCED_MEMORY_AGENT_TEST_DOCUMENTATION.md) - Complete test suite documentation
- [Test Suite Quick Reference](docs/TEST_SUITE_QUICK_REFERENCE.md) - Quick reference for test execution and results
- [Test Results Template](docs/TEST_RESULTS_TEMPLATE.md) - Template for documenting test runs
- Customer support workflow orchestration

### Business Process Automation
- Document processing and analysis workflows
- Multi-step data transformation pipelines

### Research and Development
- Multi-modal AI experimentation
- Custom tool and agent development
- LLM provider comparison and testing

## Development and Extension

### Adding New Agents
1. Define agent configuration in YAML
2. Create specialized prompts for the agent's domain
3. Configure required MCP servers or tools
4. Test through API endpoints

### Custom Tool Development
1. Implement MCP server for new capabilities
2. Add tool configuration to agent YAML
3. Test integration through agent execution

### Provider Integration
1. Configure environment variables for new provider
2. Add model mappings in configuration
3. Test agent functionality with new models

## Project Status

This is an active development framework with comprehensive documentation, testing scripts, and production deployment capabilities. The modular architecture supports easy extension and customization for various AI automation use cases.