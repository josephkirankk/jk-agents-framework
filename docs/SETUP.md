# JK-Agents Framework Setup Guide

## Overview

The JK-Agents Framework is a comprehensive multi-agent system that provides:
- Multi-agent orchestration with supervisor planning
- Support for multiple LLM providers (OpenAI, Azure OpenAI, Google Gemini, Anthropic)
- MCP (Model Context Protocol) integration for external tools
- Python function tools integration
- FastAPI web server with REST API endpoints
- CLI interface for direct agent execution

## Prerequisites

### System Requirements
- **Python**: 3.9 or higher (3.11+ recommended)
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Memory**: Minimum 4GB RAM (8GB+ recommended for complex workflows)
- **Storage**: At least 2GB free space for dependencies and logs

### Required Accounts/API Keys
You'll need API keys for at least one of the following LLM providers:
- **OpenAI**: API key from [OpenAI Platform](https://platform.openai.com/)
- **Azure OpenAI**: Azure subscription with OpenAI service deployed
- **Google Gemini**: API key from [Google AI Studio](https://makersuite.google.com/)
- **Anthropic**: API key from [Anthropic Console](https://console.anthropic.com/)

## Installation

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd jk-agents-framework
```

### Step 2: Create Virtual Environment

#### On Windows:
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### On macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration

Create a `.env` file in the project root directory:

```bash
# Copy the example environment file
cp .env.example .env  # On Windows: copy .env.example .env
```

Edit the `.env` file with your configuration:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Azure OpenAI Configuration (if using Azure)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-10-21

# Google Gemini Configuration (if using Google)
GOOGLE_API_KEY=your_google_api_key_here

# Anthropic Configuration (if using Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Custom OpenAI-compatible endpoint (e.g., LM Studio)
# OPENAI_BASE_URL=http://localhost:1234/v1
```

## Configuration

### Agent Configuration
The framework uses YAML configuration files located in the `config/` directory. 

#### Basic Configuration Example
Create or modify a configuration file (e.g., `config/my_agents.yaml`):

```yaml
models:
  default: "openai:gpt-4o-mini"
  supervisor: "openai:gpt-4o"
  temperature: 0.0

business_context: |
  Your business context and domain-specific information here.

persistence:
  type: "memory"

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o"
  prompt: |
    You are the Supervisor. Break down requests into minimal atomic tasks.
    Return JSON ONLY with goal and plan structure.

agents:
  - name: "research_agent"
    description: "Performs research and information gathering"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a research agent. Gather and analyze information to answer questions.
    
  - name: "analysis_agent"
    description: "Analyzes data and provides insights"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are an analysis agent. Analyze data and provide detailed insights.
```

### Multi-Provider Setup
For detailed multi-provider configuration, see [MULTI_PROVIDER_SETUP.md](MULTI_PROVIDER_SETUP.md).

## Verification

### Test Installation
```bash
# Test CLI interface
python -m app.main "Hello, test the system" --config config/simple_test.yaml

# Test API server
python -m app.api
# In another terminal: curl http://localhost:8000/health
```

### Run Example
```bash
# Using CLI with a specific agent
python -m app.main "What is machine learning?" --agent research_agent

# Using CLI with supervisor mode
python -m app.main "Analyze the current market trends"
```

## Platform-Specific Notes

### Windows
- Use Command Prompt or PowerShell
- Ensure Python is added to PATH
- Some antivirus software may interfere with virtual environments
- Use UTF-8 encoding for configuration files

### macOS
- May need to install Xcode Command Line Tools: `xcode-select --install`
- Use Terminal or iTerm2
- Python 3 might be available as `python3` command

### Linux
- Install Python development headers: `sudo apt-get install python3-dev` (Ubuntu/Debian)
- Ensure pip is up to date: `python3 -m pip install --upgrade pip`

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# If you get import errors, ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

#### 2. API Key Issues
- Verify API keys are correctly set in `.env` file
- Check API key permissions and quotas
- Ensure no extra spaces or quotes around API keys

#### 3. Port Already in Use
```bash
# If port 8000 is in use, specify a different port
python -m app.api --port 8001
```

#### 4. Memory Issues
- Reduce batch sizes in configuration
- Use smaller models for testing
- Monitor system resources

### Getting Help
- Check existing documentation in the `docs/` folder
- Review configuration examples in the `config/` folder
- Check logs in the `logs/` directory for detailed error information

## Next Steps
After successful setup, see [USAGE.md](USAGE.md) for detailed usage instructions and examples.
