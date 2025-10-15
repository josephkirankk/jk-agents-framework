# LiteLLM Integration Guide for JK-Agents Framework

## Overview

This guide documents the integration of LiteLLM with the JK-Agents Framework, enabling seamless usage of multiple LLM providers including Azure OpenAI, Google Gemini, OpenAI, and Anthropic.

The integration provides:

- Multi-provider support with unified interface
- Multimodal capabilities (images, files)
- Synchronous and asynchronous operations
- LangChain compatibility
- Conversation memory integration

## Supported Providers

The following LLM providers are supported through LiteLLM:

| Provider      | Format                           | Example Models                    | Multimodal |
|---------------|----------------------------------|---------------------------------|------------|
| Azure OpenAI  | `azure/model-name`               | `azure/gpt-4.1`                  | ✅ Yes      |
| Google Gemini | `gemini/model-name`              | `gemini/gemini-2.5-flash-lite`   | ✅ Yes      |
| OpenAI        | `openai/model-name`              | `openai/gpt-4o`, `openai/gpt-4o-mini` | ✅ Yes |
| Anthropic     | `anthropic/model-name`           | `anthropic/claude-3-5-sonnet`    | ✅ Yes      |
| Cohere        | `cohere/model-name`              | `cohere/command-r`              | ❌ No       |
| Others        | See LiteLLM documentation        | Various                          | Varies     |

## Setup & Configuration

### 1. Environment Setup

Create a `.env` file with your API keys:

```env
# Azure OpenAI
AZURE_API_KEY=your-azure-api-key
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2023-05-15

# Google Gemini
GOOGLE_API_KEY=your-google-api-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 2. Framework Configuration

Update your YAML configuration files to use LiteLLM format:

```yaml
models:
  default: "azure/gpt-4.1"  # Or any other provider
  supervisor: "azure/gpt-4.1"
  temperature: 0.2
```

For Google Gemini:

```yaml
models:
  default: "gemini/gemini-2.5-flash-lite"
  supervisor: "gemini/gemini-2.5-flash-lite"
  temperature: 0.2
```

## Usage Examples

### Basic Usage

```python
from app.enhanced_litellm_wrapper import create_litellm_model
from langchain_core.messages import SystemMessage, HumanMessage

# Create model instance
model = create_litellm_model(
    model_id="azure/gpt-4.1",  # Or any other supported model
    temperature=0.2
)

# Create messages
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Calculate 2+2 and explain your answer.")
]

# Synchronous call
result = model._generate(messages)
response = result.generations[0].message.content
print(response)

# Asynchronous call
async def get_async_response():
    result = await model._agenerate(messages)
    return result.generations[0].message.content

# Check model capabilities
capabilities = model.check_capabilities()
print(f"Supports vision: {capabilities['supports_vision']}")
print(f"Supports files: {capabilities['supports_files']}")
```

### Multimodal Usage

```python
from app.enhanced_litellm_wrapper import create_litellm_model
from langchain_core.messages import SystemMessage

# Create model instance
model = create_litellm_model(model_id="azure/gpt-4.1")

# Check if model supports vision
if model.check_capabilities().get("supports_vision", False):
    # Create multimodal message with image
    multimodal_message = model.create_multimodal_message(
        text="What do you see in this image?",
        images=["path/to/image.png"]
    )
    
    # Generate response
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        multimodal_message
    ]
    
    result = model._generate(messages)
    response = result.generations[0].message.content
    print(response)
```

## Framework Integration

The LiteLLM wrapper is fully integrated with the JK-Agents Framework:

- **Agent Building**: Used automatically when LiteLLM format models specified
- **Memory System**: Works with conversation memory system
- **Multi-turn Conversations**: Maintains context across turns
- **Configuration**: Recognized in all framework YAML configurations

## Testing

The integration includes a comprehensive test suite:

```bash
# Run the LiteLLM integration test
python tests/run_litellm_tests.py
```

The test validates:

- Basic text processing with multiple providers

- Multimodal capabilities

- Synchronous and asynchronous operations

- Environment configuration

## Provider-Specific Notes

### Azure OpenAI

- Uses `AZURE_API_KEY`, `AZURE_API_BASE`, and `AZURE_API_VERSION` environment variables

- Automatically maps `azure/gpt-4.1` to the correct deployment

- Supports vision and file inputs

### Google Gemini

- Uses `GOOGLE_API_KEY` environment variable

- Supports `gemini/gemini-2.5-flash-lite` and similar models

- Supports vision but not file inputs

- Alternative format: `google/gemini-2.5-flash-lite` also supported

### OpenAI

- Uses `OPENAI_API_KEY` environment variable

- Supports all OpenAI models including GPT-4o

- Supports both vision and file inputs

## Troubleshooting

### Common Issues

1. **API Key Not Found**:

   - Ensure your `.env` file has the correct API keys
   - Check environment variable names match provider expectations

2. **Model Not Available**:

   - Check model name format (`provider/model-name`)
   - Verify model exists and is available in your subscription

3. **Vision Features Not Working**:

   - Verify model supports vision (`model.check_capabilities()`)
   - Check image path is valid and accessible
   - Ensure image format is supported (PNG, JPG, etc.)

4. **Memory System Issues**:

   - Ensure conversation memory is enabled in configuration
   - Verify ChromaDB is properly set up (port 8001)

## Implementation Details

The integration is built on:

- **EnhancedLiteLLMChat**: Custom LangChain-compatible wrapper

- **LiteLLM Library**: For multi-provider support

- **Multimodal Support**: Properly formatted image/file inputs

- **Framework Components**: Integrated with agent system and memory

## File Structure

- `/app/enhanced_litellm_wrapper.py`: Main wrapper implementation

- `/tests/test_litellm_wrapper_integration.py`: Integration test

- `/tests/run_litellm_tests.py`: Test runner

## Version Compatibility

- **LiteLLM**: 1.17.5+

- **LangChain**: 0.0.335+

- **Python**: 3.10+

---

Last Updated: September 29, 2025
