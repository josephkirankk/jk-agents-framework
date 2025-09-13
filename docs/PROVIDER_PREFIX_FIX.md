# Provider Prefix Fix - Troubleshooting Guide

## Problem Diagnosed

The original issue was a **configuration mismatch** between model prefixes and provider routing:

### Original Problem
- Configuration used `openai:gpt-4o` models
- Environment had `OPENAI_BASE_URL=http://127.0.0.1:1234/v1` (LM Studio)
- LM Studio was not running → Connection failed
- No dedicated prefixes for PepGenX or LM Studio

### Root Cause
The system was trying to route `openai:` prefixed models to LM Studio (localhost:1234), but LM Studio wasn't running, causing the connection error.

## Solution Implemented

### 1. Added Custom Model Prefixes

Extended `app/agent_builder.py` to support dedicated prefixes:

- **`pepgenx:`** → Routes to PepGenX wrapper (http://127.0.0.1:8000/v1)
- **`lmstudio:`** → Routes to LM Studio (http://127.0.0.1:1234/v1)
- **`azure_openai:`** → Routes to Azure OpenAI (existing)
- **`anthropic:`** → Routes to Anthropic Claude (existing)
- **`google:`** → Routes to Google Gemini (existing)
- **`openai:`** → Routes to regular OpenAI API (existing)

### 2. Updated Environment Configuration

Modified `.env` file to support multiple providers:

```bash
# PepGenX Wrapper
PEPGENX_WRAPPER_BASE_URL=http://127.0.0.1:8000/v1
PEPGENX_WRAPPER_API_KEY=sk-test-key1

# LM Studio
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_API_KEY=lm-studio

# Regular OpenAI API (optional)
# OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Updated Configuration Files

Changed `config/pepgenx_simple_test.yaml` to use proper prefixes:

```yaml
models:
  default: "pepgenx:gpt-4o"      # Was: "openai:gpt-4o"
  supervisor: "pepgenx:gpt-4o"   # Was: "openai:gpt-4o"
```

### 4. Fixed Model Instance Handling

Updated `app/planner_executor.py` to handle custom prefixes in verification steps.

## Test Results

✅ **PepGenX (`pepgenx:gpt-4o`)** - Working perfectly
✅ **Azure OpenAI (`azure_openai:gpt-4.1`)** - Working perfectly  
✅ **Anthropic (`anthropic:claude-sonnet-4`)** - Working perfectly
✅ **Google Gemini (`google:gemini-2.0-flash-exp`)** - Working perfectly
❌ **LM Studio (`lmstudio:llama-3.2-3b`)** - Connection failed (LM Studio not running)

## Usage Examples

### Simple PepGenX Test
```bash
python -m app.main "Hello, how are you?" --config config/pepgenx_simple_test.yaml
```

### Multi-Provider Test
```bash
python -m app.main "Test different AI providers" --config config/multi_provider_fixed.yaml
```

### Configuration Examples

#### PepGenX Only
```yaml
models:
  default: "pepgenx:gpt-4o"
  supervisor: "pepgenx:gpt-4o"
```

#### Multi-Provider Setup
```yaml
models:
  # Enterprise compliance
  default: "pepgenx:gpt-4o"
  supervisor: "pepgenx:gpt-4o"
  
  # Local development
  local_dev: "lmstudio:llama-3.2-3b"
  
  # Production reliability
  azure_prod: "azure_openai:gpt-4.1"
  
  # Advanced reasoning
  claude_reasoning: "anthropic:claude-sonnet-4-20250514"
  
  # Multimodal tasks
  gemini_multimodal: "google:gemini-2.0-flash-exp"
```

## Provider Requirements

### PepGenX Wrapper
- **Status**: ✅ Running on port 8000
- **Requirement**: PepGenX wrapper service must be running
- **Start**: `cd pepgenx_openai_wrapper && python start.py`

### LM Studio
- **Status**: ❌ Not running
- **Requirement**: LM Studio application running on port 1234
- **Start**: Launch LM Studio application and start local server

### Azure OpenAI
- **Status**: ✅ Configured
- **Requirement**: Valid Azure OpenAI credentials in .env

### Anthropic Claude
- **Status**: ✅ Configured  
- **Requirement**: Valid Anthropic API key in .env

### Google Gemini
- **Status**: ✅ Configured
- **Requirement**: Valid Google API key in .env

## Key Benefits

1. **Clear Separation**: Each provider has its own dedicated prefix
2. **No Conflicts**: No more routing conflicts between providers
3. **Explicit Control**: Developers can explicitly choose which provider to use
4. **Easy Debugging**: Clear logs show which provider is being used
5. **Flexible Configuration**: Mix and match providers as needed

## Next Steps

1. **Start LM Studio** if you want to test local models
2. **Use the new prefixes** in your configuration files
3. **Test different providers** using the multi-provider configuration
4. **Update existing configs** to use the new prefix system

The fix ensures that each AI provider has its own dedicated routing path, eliminating the connection conflicts that were causing the original error.
