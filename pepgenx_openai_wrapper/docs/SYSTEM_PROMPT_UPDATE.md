# System Prompt Default Update

## Overview

The PepGenX OpenAI Wrapper has been updated to default to **system prompt 0** (no system prompt) instead of system prompt 2 (Adobe Firefly Image Optimizer). This change provides more direct, factual answers by default while maintaining full backward compatibility.

## What Changed

### Before (v1.0.0)
- **Default system prompt**: 2 (Adobe Firefly Image Optimizer)
- **Behavior**: All requests without explicit system messages used image generation optimization
- **Result**: Questions like "What is 2+2?" returned image descriptions instead of direct answers

### After (v1.1.0)
- **Default system prompt**: 0 (No system prompt - direct response mode)
- **Behavior**: Requests without explicit system messages get direct, factual responses
- **Result**: Questions like "What is 2+2?" return "2 + 2 = 4" directly

## Configuration

### Environment Variable
```bash
# Set in .env file
PEPGENX_DEFAULT_SYSTEM_PROMPT=0  # Default: direct answers
# PEPGENX_DEFAULT_SYSTEM_PROMPT=2  # Use this for old behavior
```

### Available System Prompt Options
| ID | Name | Purpose | Best For |
|----|------|---------|----------|
| **0** | No System Prompt | Direct response mode | **Math, facts, general Q&A** |
| 1 | Content Safety Analyzer | Analyzes content against guidelines | Content moderation |
| 2 | Adobe Firefly Image Optimizer | Optimizes for image generation | Image prompts |
| 3 | PepsiCo ESG Assistant | ESG-focused responses | Corporate sustainability |
| 4 | System Prompt Generator | Creates system prompts | Meta-prompting |
| 5 | Prompt Enhancer | Improves prompt quality | Prompt optimization |
| 6 | Tool-Aware Assistant | General assistant with tools | General Q&A |
| 7 | Prompt Adaptation Expert | Adapts between models | Cross-model compatibility |

## Impact on OpenAI API Compatibility

### ✅ No Breaking Changes
- **OpenAI API format**: Unchanged - still accepts standard OpenAI requests
- **Response format**: Unchanged - still returns OpenAI-compatible responses
- **Existing integrations**: Continue to work without modification

### 🎯 Improved User Experience
- **Direct answers**: Math and factual questions get direct responses
- **Better defaults**: More intuitive behavior for most use cases
- **Configurable**: Can be changed via environment variable

## Examples

### Simple Math Question
```bash
# Request (OpenAI format)
POST /v1/chat/completions
{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "What is 2+2?"}
  ]
}

# Response (Before - System Prompt 2)
{
  "choices": [{
    "message": {
      "content": "A minimalist design featuring geometric shapes representing 'four'..."
    }
  }]
}

# Response (After - System Prompt 0)
{
  "choices": [{
    "message": {
      "content": "2 + 2 = 4"
    }
  }]
}
```

### With Explicit System Message
```bash
# Request with system message
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a creative writer"},
    {"role": "user", "content": "Write a story about AI"}
  ]
}

# Behavior: System message mapping still works as before
# Maps to appropriate system prompt ID based on content
```

## Migration Guide

### For New Deployments
- No action required - new default provides better experience

### For Existing Deployments
- **Option 1**: Keep new default (recommended) - users get better responses
- **Option 2**: Restore old behavior by setting `PEPGENX_DEFAULT_SYSTEM_PROMPT=2`

### For Applications Expecting Image Descriptions
If your application specifically expects image-optimized responses:
```bash
# Set in .env to restore old behavior
PEPGENX_DEFAULT_SYSTEM_PROMPT=2
```

Or send explicit system messages:
```json
{
  "messages": [
    {"role": "system", "content": "Optimize this prompt for image generation"},
    {"role": "user", "content": "A sunset over mountains"}
  ]
}
```

## Technical Implementation

### Code Changes
1. **Configuration**: Added `PEPGENX_DEFAULT_SYSTEM_PROMPT` setting
2. **Models**: Updated `PepGenXRequest` to support configurable defaults
3. **Translation**: Enhanced message translation to handle system_prompt=0
4. **Client**: Modified to exclude system_prompt field when value is 0

### Backward Compatibility
- **Existing code**: Continues to work unchanged
- **Explicit system prompts**: Still mapped correctly
- **API contracts**: No changes to request/response formats

## Testing

### Verify New Behavior
```bash
# Test direct answer
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key1" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'

# Expected: Direct mathematical answer
```

### Verify Configuration Override
```bash
# Set PEPGENX_DEFAULT_SYSTEM_PROMPT=2 in .env
# Restart service
# Test same request - should get image-optimized response
```

## Support

For questions or issues related to this update:
1. Check the configuration in your `.env` file
2. Review the system prompt mapping in the logs
3. Test with different system prompt values
4. Consult the API documentation for system prompt details

## Version History

- **v1.1.0**: Changed default system prompt from 2 to 0
- **v1.0.0**: Initial release with system prompt 2 default
