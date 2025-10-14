# Multi-Provider Support with File Attachments

## Overview

This document describes the implementation of multi-provider support in the JK-Agents framework, allowing seamless integration with multiple LLM providers including:

- OpenAI (GPT-4o, etc.)
- Anthropic (Claude 3.5 Sonnet, etc.)
- Google Gemini (Gemini 1.5 Pro, etc.)

The implementation leverages LiteLLM to provide a unified interface for these providers and adds support for handling file attachments including images, documents, and other file types.

## Key Features

### 1. Multi-Provider Support

- Unified interface through LiteLLM
- Support for OpenAI, Anthropic, and Google Gemini models
- Provider-specific configuration options
- Easy switching between providers

### 2. File Attachment Support

- Multiple file upload capability
- Support for various file types:
  - Images (jpg, png, webp, etc.)
  - Documents (PDF, txt, etc.)
  - Data files (CSV, JSON, etc.)
- Intelligent routing based on file type

### 3. Conversation Continuity

- Maintains context across conversation turns
- Works with different providers in the same conversation
- Preserves file attachment context

## Implementation Details

### Integration with LiteLLM

The framework uses LiteLLM to provide a consistent interface for different LLM providers. The integration is implemented in `app/litellm_provider.py` and includes:

- Model instantiation based on provider/model format (e.g., "openai/gpt-4o")
- API key management from environment variables
- File attachment handling for each provider
- Provider-specific capabilities detection

### File Attachment Processing

File attachments are processed differently based on their type:

1. **Images**: Converted to base64 data URIs or passed as URLs
2. **Text-based files**: Content extracted and included in the prompt
3. **CSV files**: Processed as structured data
4. **JSON files**: Parsed and included as structured data

### Configuration Format

Multi-provider support is configured in YAML configuration files with the following structure:

```yaml
models:
  default: "openai/gpt-4o"  # Default model
  openai: "openai/gpt-4o"   # OpenAI default model
  anthropic: "anthropic/claude-3-5-sonnet-20240620"  # Anthropic default model
  gemini: "gemini/gemini-1.5-pro"  # Google Gemini default model
  temperature: 0.2  # Default temperature

litellm:
  enabled: true
  providers:
    - openai
    - anthropic
    - gemini
```

## Environment Variables

The following environment variables must be set for the respective providers:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Google Gemini
export GEMINI_API_KEY="AIza..."
```

## Usage Examples

### Using a Specific Provider

```yaml
supervisor:
  model: "openai/gpt-4o"  # Use OpenAI

agents:
  - name: "text_processor"
    model: "anthropic/claude-3-5-sonnet-20240620"  # Use Anthropic
    
  - name: "image_analyzer"
    model: "gemini/gemini-1.5-pro"  # Use Google Gemini
```

### Working with File Attachments

```python
# API call with file attachments
response = await run_direct_agent_with_files(
    agent_name="multimodal_agent",
    user_input="Analyze this document and image together",
    app_cfg=app_cfg,
    file_ids=file_ids,
    file_info=file_info,
    config_path=config_path,
    thread_id=thread_id
)
```

## Conversation Context and Memory

The multi-provider implementation works seamlessly with the existing conversation memory system:

1. Context is preserved across turns regardless of provider
2. File information is included in the conversation context
3. Turn tracking works with all providers
4. Memory system stores provider-specific responses

## Testing

Test the multi-provider implementation using the provided test scripts:

```bash
# Test all providers
python tests/test_multi_provider_agent.py

# Test Google Gemini with conversation continuity
python tests/test_agent_continuity_google.py
```

## Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure environment variables are set correctly
   - Check API key format and validity

2. **Provider-Specific Errors**:
   - OpenAI: Check rate limits and quotas
   - Anthropic: Verify API key permissions
   - Google Gemini: Ensure API is enabled in Google AI Studio

3. **File Attachment Issues**:
   - Check file size limits
   - Verify file format is supported
   - Use URLs for large files instead of base64 encoding

## References

- [LiteLLM Documentation](https://github.com/BerriAI/litellm)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic Claude API Reference](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [Google Gemini API Reference](https://ai.google.dev/docs/gemini_api)
