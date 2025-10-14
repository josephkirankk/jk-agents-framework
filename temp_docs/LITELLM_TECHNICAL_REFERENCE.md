# LiteLLM Technical Reference

## Overview

The Enhanced LiteLLM Wrapper provides a unified interface for multiple LLM providers in the JK-Agents Framework with LangChain compatibility and multimodal support.

## Key Components

### EnhancedLiteLLMChat Class

```python
from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat

# Create instance directly
model = EnhancedLiteLLMChat(
    model="azure/gpt-4.1",
    temperature=0.2,
    max_tokens=None,  # Optional
    timeout=60        # Optional
)
```

### Factory Function

```python
from app.enhanced_litellm_wrapper import create_litellm_model

# Recommended way to create instances
model = create_litellm_model(
    model_id="azure/gpt-4.1",
    temperature=0.2,
    timeout=60  # Optional
)
```

### Model Format

All models follow the format `provider/model-name`:

- Azure OpenAI: `azure/gpt-4.1`
- Google Gemini: `gemini/gemini-2.5-flash-lite`
- OpenAI: `openai/gpt-4o`
- Anthropic: `anthropic/claude-3-5-sonnet`

### Utility Functions

```python
from app.enhanced_litellm_wrapper import is_litellm_model

# Check if model ID uses LiteLLM format
is_litellm = is_litellm_model("azure/gpt-4.1")  # Returns True
is_litellm = is_litellm_model("gpt-4")  # Returns False
```

## Environment Variables

| Provider | Variables |
|----------|-----------|
| Azure OpenAI | `AZURE_API_KEY`, `AZURE_API_BASE`, `AZURE_API_VERSION` |
| Google Gemini | `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) |
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

## Methods

### Synchronous Generation

```python
from langchain_core.messages import SystemMessage, HumanMessage

# Create messages
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Calculate 2+2")
]

# Generate response
result = model._generate(messages)
response = result.generations[0].message.content
```

### Asynchronous Generation

```python
# Generate response asynchronously
result = await model._agenerate(messages)
response = result.generations[0].message.content
```

### Multimodal Content

```python
# Create multimodal message
multimodal_message = model.create_multimodal_message(
    text="Describe this image:",
    images=["path/to/image.png"]  # Optional
)

# Generate with multimodal content
messages = [SystemMessage(content="You are a visual assistant."), multimodal_message]
result = model._generate(messages)
```

### Capability Checking

```python
# Check model capabilities
capabilities = model.check_capabilities()
supports_vision = capabilities.get("supports_vision", False)
supports_files = capabilities.get("supports_files", False)
```

## Integration Testing

```bash
# Run integration test
python tests/test_litellm_wrapper_integration.py

# Run with test runner
python tests/run_litellm_tests.py
```

## Implementation Notes

1. The wrapper automatically handles environment variables for each provider
2. Multimodal support is based on model capabilities detection
3. Full LangChain compatibility for LangGraph and agent integrations
4. API timeout handling and proper error management included

## Example Config for Framework

```yaml
models:
  default: "azure/gpt-4.1"
  supervisor: "azure/gpt-4.1"
  temperature: 0.2
  
conversation_memory:
  enabled: true
  max_context_length: 2000
  prepend_context: true
```

---

Last Updated: September 29, 2025
