# Multi-Provider OpenAI Configuration Guide

This guide explains how to configure and use multiple OpenAI providers simultaneously in the jk-agents system.

## Overview

The enhanced system supports using multiple OpenAI-compatible providers at the same time:

- **Regular OpenAI API** - Official OpenAI models via API
- **Azure OpenAI** - Enterprise OpenAI models via Azure
- **LM Studio** - Local models running on your machine
- **Other OpenAI-compatible services** - Ollama, LocalAI, etc.

## Model Naming Conventions

The system uses prefixes to determine which provider to use for each model:

| Prefix | Provider | Example | Usage |
|--------|----------|---------|-------|
| `openai:` | OpenAI API or Local (via OPENAI_BASE_URL) | `openai:gpt-4o-mini` | Standard OpenAI models or local models |
| `azure_openai:` | Azure OpenAI | `azure_openai:gpt-4o-mini` | Azure-hosted OpenAI models |

## Environment Configuration

### Basic Setup

Copy `.env.example` to `.env` and configure your providers:

```bash
cp .env.example .env
```

### Configuration Scenarios

#### Scenario 1: Azure OpenAI + LM Studio (Recommended)

Use Azure for production models and LM Studio for local development:

```env
# Azure OpenAI for production
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# LM Studio for local models
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
OPENAI_API_KEY=lm-studio
```

YAML Configuration:
```yaml
models:
  default: "azure_openai:gpt-4o-mini"      # Uses Azure
  supervisor: "azure_openai:gpt-4o"        # Uses Azure  
  local_dev: "openai:google/gemma-3n-e4b"  # Uses LM Studio
  local_test: "openai:llama-3.2-3b"        # Uses LM Studio
```

#### Scenario 2: Regular OpenAI + Azure OpenAI

Use both cloud providers:

```env
# Regular OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Azure OpenAI  
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

YAML Configuration:
```yaml
models:
  default: "openai:gpt-4o-mini"            # Uses regular OpenAI
  supervisor: "azure_openai:gpt-4o-mini"   # Uses Azure OpenAI
```

#### Scenario 3: All Three Providers

```env
# Regular OpenAI (not used due to OPENAI_BASE_URL override)
OPENAI_API_KEY=sk-your-openai-key

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# LM Studio (overrides regular OpenAI for openai: models)
OPENAI_BASE_URL=http://127.0.0.1:1234/v1
```

## Provider Selection Logic

The system determines which provider to use based on this logic:

1. **Azure OpenAI models** (`azure_openai:*`): Always use Azure OpenAI if configured
2. **OpenAI models** (`openai:*`):
   - If `OPENAI_BASE_URL` is set: Use local server (LM Studio, Ollama, etc.)
   - If only `OPENAI_API_KEY` is set: Use regular OpenAI API
   - If Azure vars are set AND no `OPENAI_BASE_URL`: Auto-convert to `azure_openai:`

## Best Practices

### 1. Model Selection Strategy

- **Production/Critical tasks**: Use Azure OpenAI models for reliability
- **Development/Testing**: Use local LM Studio models for speed and privacy
- **Cost optimization**: Use local models for simple tasks, cloud models for complex ones

### 2. Configuration Management

- Keep sensitive API keys in `.env` (never commit to git)
- Use different configurations for different environments
- Test your configuration with the `test_agent` before production use

### 3. Performance Optimization

- Use faster local models for simple tasks
- Reserve powerful cloud models for complex reasoning
- Consider model capabilities vs. cost for each use case

## Testing Your Configuration

1. **Test Azure OpenAI**:
```bash
python -m app.main --agent test_agent "Hello, test Azure OpenAI"
```

2. **Test LM Studio**:
```bash
# Make sure LM Studio is running on localhost:1234
python -m app.main --config config/multi_provider_example.yaml --agent dev_assistant_agent "Hello, test local model"
```

3. **Test Multi-Provider Setup**:
```bash
python -m app.main --config config/multi_provider_example.yaml "Compare the weather in Mumbai using both cloud and local models"
```

## Troubleshooting

### Common Issues

1. **Models not switching providers**:
   - Check your `.env` configuration
   - Verify model prefixes in YAML (`openai:` vs `azure_openai:`)
   - Ensure LM Studio is running if using local models

2. **Azure OpenAI connection errors**:
   - Verify endpoint URL format (no trailing slash)
   - Check API version compatibility
   - Confirm deployment name matches your Azure setup

3. **LM Studio connection errors**:
   - Ensure LM Studio server is running
   - Verify the correct port (default: 1234)
   - Check that a model is loaded in LM Studio

### Debug Mode

Enable detailed logging to troubleshoot issues:

```bash
export LANGCHAIN_VERBOSE=true
python -m app.main --config your-config.yaml "your query"
```

## Example Configurations

See the following example files:
- `config/multi_provider_example.yaml` - Complete multi-provider setup
- `config/brave_math_weather_LOCAL.yaml` - LM Studio focused setup
- `config/agents.yaml` - Standard single-provider setup

## Advanced Usage

### Custom OpenAI-Compatible Providers

For other providers like Ollama or LocalAI:

```env
# Ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama

# LocalAI  
OPENAI_BASE_URL=http://localhost:8080/v1
OPENAI_API_KEY=localai
```

### Dynamic Model Selection

You can create agents that intelligently choose models based on task complexity by using different model configurations for different agents in your YAML file.
