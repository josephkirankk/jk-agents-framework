# Temperature Configuration

This document describes how to configure temperature settings for AI models in the JK-Agents system.

## Overview

Temperature controls the randomness of AI model responses. Lower values (closer to 0) make responses more deterministic and focused, while higher values (closer to 1) make responses more creative and varied.

## Configuration Methods

### 1. Global Temperature Setting

Set a default temperature for all models in your YAML configuration:

```yaml
models:
  default: "google:gemini-2.5-flash-lite"
  supervisor: "google:gemini-2.0-flash-lite-001"
  temperature: 0.2  # Global default temperature
```

### 2. Per-Model Temperature Setting

Specify temperature directly in the model string using the format `provider:model:temperature`:

```yaml
models:
  default: "google:gemini-2.5-flash-lite:0.2"
  supervisor: "google:gemini-2.0-flash-lite-001:0.1"
  temperature: 0.3  # Fallback for models without explicit temperature

agents:
  - name: "creative_agent"
    model: "google:gemini-2.5-flash-lite:0.8"  # High creativity
    description: "Agent for creative tasks"
    
  - name: "analytical_agent"
    model: "google:gemini-2.5-flash-lite:0.1"  # Low randomness
    description: "Agent for analytical tasks"
```

## Supported Formats

### With Temperature
- `google:gemini-2.5-flash-lite:0.2`
- `google:gemini-2.0-flash-exp:0.1`
- `openai:gpt-4o:0.5`
- `azure_openai:gpt-4.1:0.3`

### Without Temperature (uses global default)
- `google:gemini-2.5-flash-lite`
- `openai:gpt-4o`
- `azure_openai:gpt-4.1`

## Temperature Ranges

- **0.0 - 0.3**: Highly focused, deterministic responses
- **0.3 - 0.7**: Balanced creativity and consistency
- **0.7 - 1.0**: High creativity, more varied responses

## Provider Support

### Google Gemini Models
✅ **Full Support**: Temperature is applied directly to the model instance.

Examples:
```yaml
models:
  creative: "google:gemini-2.5-flash-lite:0.8"
  focused: "google:gemini-2.0-flash-exp:0.1"
```

### OpenAI and Azure OpenAI Models
⚠️ **Partial Support**: Temperature parsing is implemented but application depends on LangGraph/LangChain handling.

Examples:
```yaml
models:
  openai_creative: "openai:gpt-4o:0.7"
  azure_focused: "azure_openai:gpt-4.1:0.2"
```

### Other Providers
⚠️ **Limited Support**: Temperature parsing works but application depends on provider implementation.

## Backward Compatibility

The system maintains full backward compatibility:

- Existing configurations without temperature specifications continue to work
- Global temperature setting is used as fallback
- Default temperature is 0.2 if not specified

## Examples

### Basic Configuration
```yaml
models:
  default: "google:gemini-2.5-flash-lite"
  temperature: 0.2
```

### Advanced Configuration
```yaml
models:
  default: "google:gemini-2.5-flash-lite:0.2"
  supervisor: "google:gemini-2.0-flash-lite-001:0.1"
  temperature: 0.3  # Fallback

agents:
  - name: "data_analyst"
    model: "google:gemini-2.5-flash-lite:0.1"
    description: "Precise data analysis"
    
  - name: "creative_writer"
    model: "google:gemini-2.5-flash-lite:0.8"
    description: "Creative content generation"
    
  - name: "balanced_assistant"
    model: "google:gemini-2.5-flash-lite"  # Uses global default
    description: "General purpose assistant"
```

## Testing

Use the provided test script to verify temperature configuration:

```bash
python test_temperature_config.py
```

This will test:
- Temperature parsing from model strings
- Default temperature fallback
- Configuration loading
- Model instance creation

## Troubleshooting

### Temperature Not Applied
- Verify the model string format: `provider:model:temperature`
- Check that the temperature value is a valid float (0.0 - 1.0)
- For Google models, ensure `GOOGLE_API_KEY` is set

### Invalid Temperature Values
- Temperature must be between 0.0 and 1.0
- Use decimal notation (0.2, not .2)
- Avoid spaces in the model string

### Backward Compatibility Issues
- Old configurations should work without changes
- If issues occur, add explicit temperature values
- Check logs for parsing warnings
