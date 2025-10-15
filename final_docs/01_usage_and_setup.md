# JK-Agents Framework - Usage and Setup Guide

## Prerequisites

### System Requirements
**Evidence**: `requirements.txt:1-72` - Python dependencies with specific version requirements.

- Python 3.8+ (inferred from async/await usage and type hints)
- Virtual environment support (`.venv/` recommended per `.gitignore:10`)
- 4GB+ RAM (inferred from ChromaDB and LangGraph memory requirements)

### Required Dependencies
**Evidence**: `requirements.txt:2-47` - Core framework dependencies.

```bash
# Core framework
fastapi==0.111.0
uvicorn==0.30.0
pydantic>=2.11.9
pyyaml>=6.0

# AI/ML framework
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-anthropic>=0.3.0
langchain-google-genai>=2.1.0
langgraph>=0.2.70

# Memory backend
chromadb>=1.0.0
langchain-chroma>=0.2.4

# Multi-provider support
litellm>=1.43.0
```

## Environment Setup

### 1. Virtual Environment Creation
**Evidence**: `.gitignore:9-15` - Virtual environment patterns and user memory indicating `.venv` usage.

```bash
# Create virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

### 2. Install Dependencies
**Evidence**: `requirements.txt:1-72` - Complete dependency specification.

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify ChromaDB installation (per memory f21a75d7)
python -c "import chromadb; print('ChromaDB installed successfully')"
```

### 3. Environment Configuration
**Evidence**: `.env.example:1-147` - Comprehensive multi-provider configuration template.

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required for Azure OpenAI (recommended provider per memories)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your-actual-api-key
AZURE_OPENAI_API_VERSION=2023-05-15

# Optional: Enable memory transaction logging
MEMORY_LOGGING_ENABLED=true
MEMORY_LOGGING_DIRECTORY=memory_logs
```

## Configuration Setup

### 1. Model Provider Configuration
**Evidence**: `.env.example:21-70` - Multi-provider setup options.

#### Option A: Azure OpenAI (Recommended)
```bash
# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT=https://pep-aisp-hackathon.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2023-05-15

# LiteLLM Azure format
AZURE_API_KEY=your-api-key
AZURE_API_BASE=https://pep-aisp-hackathon.openai.azure.com/
AZURE_API_VERSION=2023-05-15
```

#### Option B: Local LM Studio
```bash
# LM Studio local server
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
```

#### Option C: Google Gemini
**Evidence**: Memory `205f5861` - Google Gemini integration with correct model names.
```bash
# Google Gemini configuration
GOOGLE_API_KEY=your-google-api-key
```

### 2. Configuration Preloading
**Evidence**: `.env.example:146` - Configuration preloading for performance.

```bash
# Preload configurations at startup
PRELOAD_CONFIGS=config/python_exec_agent_working.yaml,config/multi_provider_agent.yaml
```

## Running the System

### 1. Start the API Server
**Evidence**: `api.py:97-100` - FastAPI application setup.

```bash
# Development server
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Verify Server Status
**Evidence**: `api.py` includes health endpoints for monitoring.

```bash
# Check server health
curl http://localhost:8000/health

# Check memory statistics
curl http://localhost:8000/memory/stats

# Check performance metrics
curl http://localhost:8000/performance/stats
```

### 3. Test Basic Functionality
**Evidence**: Memory `aaa9e3ee` - Successful test patterns for Azure OpenAI integration.

```bash
# Test basic query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate 2+2", "config_name": "python_exec_agent_working"}'

# Test with file upload
curl -X POST "http://localhost:8000/query" \
  -F "query=Analyze this data" \
  -F "config_name=python_exec_agent_working" \
  -F "files=@test_data.txt"
```

## Configuration Files

### 1. Working Configurations
**Evidence**: Memory `f21a75d7` - Validated working configurations.

- `config/python_exec_agent_working.yaml` - Main production configuration
- `config/multi_provider_agent.yaml` - Multi-provider setup
- `config/azure_openai_test.yaml` - Azure OpenAI testing

### 2. Configuration Structure
**Evidence**: `app/main.py:84-126` - Configuration loading and validation.

```yaml
# Basic configuration structure
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  temperature: 0.2

conversation_memory:
  enabled: true
  database_url: ""
  max_conversations: 10
  max_context_length: 2000

memory:
  backend: "chromadb"
  chromadb:
    port: 8001
    max_connections: 20
```

## Development Setup

### 1. Testing Environment
**Evidence**: `tests/` directory with 34 test files and `requirements.txt:59-61` - Testing dependencies.

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_agent_continuity.py -v
python -m pytest tests/test_multi_turn_conversation.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### 2. Code Quality Tools
**Evidence**: `requirements.txt:62-63` - Code formatting and linting tools.

```bash
# Format code
black app/ tests/
isort app/ tests/

# Type checking (if mypy is installed)
mypy app/
```

### 3. Documentation Generation
**Evidence**: `requirements.txt:66-67` - Documentation tools.

```bash
# Generate documentation
mkdocs serve

# Build documentation
mkdocs build
```

## Troubleshooting

### 1. Common Issues

#### DateTime UTC Error
**Evidence**: Memory `0eb9d5e9` - DateTime import fix.
```bash
# If you see: AttributeError: type object 'datetime.datetime' has no attribute 'UTC'
# This is fixed in the current codebase (api.py:16)
```

#### ChromaDB Connection Issues
**Evidence**: Memory `f21a75d7` - ChromaDB installation and configuration fixes.
```bash
# Install ChromaDB if missing
pip install chromadb>=1.1.0

# Check ChromaDB installation
python -c "import chromadb; print('ChromaDB OK')"
```

#### Memory System Issues
**Evidence**: Memory `e88960ea` - Multi-turn memory system fixes.
```bash
# Verify memory configuration
curl http://localhost:8000/memory/stats

# Check memory logs
tail -f memory_logs/memory_*.log
```

### 2. Performance Optimization
**Evidence**: Memory `655b9a86` - Performance optimization patterns.

```bash
# Enable configuration preloading
export PRELOAD_CONFIGS=config/python_exec_agent_working.yaml

# Monitor memory usage
curl http://localhost:8000/performance/stats

# Check agent logs
tail -f agentlogs/agentlog_*.log
```

### 3. Configuration Validation
**Evidence**: `app/config.py:8109 bytes` - Configuration validation system.

```bash
# Validate configuration
python -c "from app.main import load_app_config; load_app_config()"

# Test specific configuration
python -c "
from pathlib import Path
from app.main import load_app_config
config = load_app_config(Path('config/python_exec_agent_working.yaml'))
print('Configuration loaded successfully')
"
```

## Production Deployment

### 1. Environment Variables
**Evidence**: `.env.example:1-147` - Production environment configuration.

```bash
# Production environment setup
export AZURE_OPENAI_API_KEY=your-production-key
export MEMORY_LOGGING_ENABLED=true
export PRELOAD_CONFIGS=config/python_exec_agent_working.yaml
```

### 2. Server Configuration
**Evidence**: `api.py:97-100` - FastAPI production setup.

```bash
# Production server with multiple workers
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4 --access-log

# With SSL (if certificates available)
uvicorn api:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

### 3. Monitoring
**Evidence**: `api.py:86-93` - Performance metrics and monitoring.

```bash
# Monitor performance metrics
watch -n 5 'curl -s http://localhost:8000/performance/stats | jq'

# Monitor memory usage
watch -n 10 'curl -s http://localhost:8000/memory/stats | jq'
```

This setup guide provides comprehensive instructions for getting the JK-Agents Framework running in both development and production environments.
