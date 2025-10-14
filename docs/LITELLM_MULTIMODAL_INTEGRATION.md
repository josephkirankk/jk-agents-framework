# LiteLLM Multimodal Integration Guide

This document provides comprehensive information about the LiteLLM Multimodal integration in the JK-Agents Framework, including setup, configuration, usage, and troubleshooting.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [API Usage](#api-usage)
5. [Direct Usage](#direct-usage)
6. [Model Provider Support](#model-provider-support)
7. [Environment Variables](#environment-variables)
8. [Troubleshooting](#troubleshooting)
9. [Testing](#testing)

## Overview

The LiteLLM Multimodal integration provides a unified interface for working with multimodal models from multiple providers, including OpenAI, Google Gemini, Anthropic, and Azure OpenAI. It enables:

- Text and image processing in a single request
- Document analysis and extraction
- Model capability detection
- Provider-specific optimizations
- Conversation memory and continuity

## Installation

### Prerequisites

- Python 3.8+ 
- Virtual environment (.venv)
- Access to at least one model provider API

### Required Packages

```bash
# Activate virtual environment
source .venv/bin/activate

# Install required packages
python -m pip install uv
uv pip install litellm langchain-core langchain Pillow python-dotenv
```

## Configuration

### YAML Configuration

Create or use one of the provided multimodal configuration files:

- `config/litellm_multimodal_demo.yaml` - General purpose multimodal config
- `config/gemini_multimodal_example.yaml` - Google Gemini-specific config

Example configuration:

```yaml
# Model Configuration - Uses enhanced LiteLLM wrapper
models:
  default: "openai/gpt-4o"  # LiteLLM format: provider/model
  supervisor: "openai/gpt-4o"
  temperature: 0.2

# LiteLLM Configuration
litellm:
  enabled: true
  multimodal_support: true
  capabilities_check: true
  timeout: 60

# Memory Configuration
memory:
  backend: "chromadb"
  chromadb:
    port: 8001
    persist_directory: "./chroma_db"
    collection_name: "litellm_conversations"

# Conversation Memory
conversation_memory:
  enabled: true
  max_conversations: 20
  max_context_length: 4000
  prepend_context: true
```

### Environment Variables

Create a `.env` file in the project root with API keys for your providers:

```bash
# OpenAI (for openai/gpt-4o)
OPENAI_API_KEY=sk-your-openai-api-key

# Azure OpenAI (for azure/gpt-4.1)
AZURE_API_KEY=your-azure-api-key
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2023-05-15

# Google Gemini (for gemini/gemini-2.5-flash-lite)
GOOGLE_API_KEY=your-google-api-key

# Anthropic (for anthropic/claude-3-5-sonnet)
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## API Usage

### Multimodal Endpoint

The framework provides a dedicated `/multimodal` endpoint for processing multimodal content:

```bash
curl -X POST http://localhost:8000/multimodal \
  -F "model=gemini/gemini-2.5-flash-lite" \
  -F "prompt=Analyze this image and tell me what you see." \
  -F "temperature=0.2" \
  -F "files=@/path/to/your/image.jpg" \
  -F "system_message=You are a helpful vision assistant."
```

### Request Parameters

- `model` (required): LiteLLM model identifier in format `provider/model`
- `prompt` (required): Text prompt for the model
- `temperature` (optional): Model temperature (0.0 to 1.0), default: 0.2
- `files` (optional): One or more files to upload (images, documents)
- `system_message` (optional): System message for the model, default: "You are a helpful assistant."
- `thread_id` (optional): Thread ID for conversation continuity

### Response Format

```json
{
  "success": true,
  "response": "The image contains three geometric shapes...",
  "model": "gemini/gemini-2.5-flash-lite",
  "thread_id": "5f5b5b5b-5b5b-5b5b-5b5b-5b5b5b5b5b5b",
  "processing_time": 1.23,
  "capabilities": {
    "supports_vision": true,
    "supports_files": false
  },
  "files_processed": 1,
  "file_info": [
    {
      "filename": "image.jpg",
      "type": "image",
      "mime_type": "image/jpeg",
      "size": 12345
    }
  ],
  "conversation_context_used": true
}
```

## Direct Usage

You can also use the enhanced LiteLLM wrapper directly in your Python code:

```python
from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat, create_litellm_model
from langchain_core.messages import SystemMessage

# Create model instance
model = create_litellm_model("gemini/gemini-2.5-flash-lite", temperature=0.2)

# Check model capabilities
capabilities = model.check_capabilities()
print(f"Model capabilities: {capabilities}")

# Create multimodal message
multimodal_message = model.create_multimodal_message(
    text="Analyze this image and describe what you see.",
    images=["/path/to/your/image.jpg"]
)

# Generate response
messages = [
    SystemMessage(content="You are a helpful vision assistant."),
    multimodal_message
]
result = await model._agenerate(messages)
response = result.generations[0].message.content
print(response)
```

## Model Provider Support

The framework supports the following model providers:

### OpenAI
- Format: `openai/model-name`
- Examples: `openai/gpt-4o`, `openai/gpt-4o-mini`
- Vision support: Yes (for vision-enabled models)
- File support: Yes (for newer models)
- Environment: `OPENAI_API_KEY`

### Azure OpenAI
- Format: `azure/model-name`
- Examples: `azure/gpt-4.1`, `azure/gpt-4`
- Vision support: Yes (if deployment supports it)
- File support: Yes (for newer models)
- Environment: `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION`

### Google Gemini
- Format: `gemini/model-name` or `google/model-name`
- Examples: `gemini/gemini-2.5-flash-lite`, `google/gemini-2.0-pro`
- Vision support: Yes
- File support: Limited
- Environment: `GOOGLE_API_KEY`

### Anthropic
- Format: `anthropic/model-name`
- Examples: `anthropic/claude-3-5-sonnet`, `anthropic/claude-3-opus`
- Vision support: Yes (for Claude 3 models)
- File support: Yes (for Claude 3 models)
- Environment: `ANTHROPIC_API_KEY`

## Environment Variables

The framework supports multiple environment variable formats for flexibility:

| Provider | Primary Variable | Alternative Variables |
|----------|-----------------|----------------------|
| OpenAI | `OPENAI_API_KEY` | - |
| Azure | `AZURE_API_KEY` | `AZURE_OPENAI_API_KEY` |
| Azure Endpoint | `AZURE_API_BASE` | `AZURE_OPENAI_ENDPOINT` |
| Google | `GOOGLE_API_KEY` | `GEMINI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` | - |

## Troubleshooting

### Common Issues

#### Missing API Keys
- Ensure API keys are set in the `.env` file or environment variables
- Check for typos in environment variable names
- Verify that keys are valid and not expired

#### Invalid Model Format
- Model ID should be in format `provider/model` (with forward slash)
- Common mistake: using `provider:model` (with colon) which is the wrong format
- Example correct format: `openai/gpt-4o`, not `openai:gpt-4o`

#### Model Capability Errors
- Not all models support vision or file processing
- Check the model's capabilities before trying to use these features
- Use `model.check_capabilities()` to verify support

#### File Format Issues
- Images should be in common formats (PNG, JPEG, GIF)
- For document processing, use text formats (TXT, MD, etc.)
- Check file permissions if accessing local files

#### ChromaDB Errors
- Make sure ChromaDB is installed: `pip install chromadb`
- Port conflict: Set ChromaDB to use port 8001 instead of 8000
- Memory initialization: Ensure conversation memory is enabled

### Error Messages

| Error Message | Possible Causes | Solution |
|---------------|----------------|----------|
| `Enhanced LiteLLM is not available` | Missing litellm package | Install with `pip install litellm` |
| `Invalid LiteLLM model format` | Incorrect model format | Use `provider/model` format |
| `Model does not support vision` | Using images with non-vision model | Check model capabilities or use a different model |
| `Error in multimodal endpoint` | Various causes | Check logs for specific error details |

## Testing

The framework includes several test scripts for verifying the multimodal integration:

### Basic Wrapper Tests

```bash
source .venv/bin/activate
python tests/test_enhanced_litellm_wrapper.py
```

### Configuration Tests

```bash
source .venv/bin/activate
python tests/test_litellm_config_loading.py
```

### API Endpoint Tests

```bash
# First start the API server
source .venv/bin/activate
python api.py

# In another terminal
source .venv/bin/activate
python tests/test_multimodal_endpoint.py
```

### Comprehensive Tests

```bash
source .venv/bin/activate
python tests/test_litellm_multimodal.py
```

## Advanced Configuration

### Fine-Tuning Model Parameters

```yaml
models:
  default: "openai/gpt-4o"
  supervisor: "azure/gpt-4.1"
  temperature: 0.2

litellm:
  enabled: true
  multimodal_support: true
  capabilities_check: true
  timeout: 60
  max_tokens: 1000
  top_p: 0.9
```

### Customizing Memory Settings

```yaml
memory:
  backend: "chromadb"
  chromadb:
    port: 8001
    persist_directory: "./custom_memory_db"
    collection_name: "custom_collection"
    embedding_function: "openai"

conversation_memory:
  enabled: true
  max_conversations: 50
  max_context_length: 8000
  prepend_context: true
  cleanup_days: 30
```
