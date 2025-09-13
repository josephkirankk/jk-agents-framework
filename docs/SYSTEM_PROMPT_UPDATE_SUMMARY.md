# System Prompt Update Summary

## Overview

Updated the `pepgenx_cli.py` and `pepgenx_openai_wrapper` framework to properly default to system prompt 0 and ensure OpenAI API specification compliance.

## Changes Made

### 1. CLI Help Text Update (`scripts/pepgenx_cli.py`)

**Before:**
```python
help='System prompt ID (default: 2 - Adobe Firefly Image Optimizer, use 0 for no system prompt)'
```

**After:**
```python
help='System prompt ID (default: 0 - No system prompt for direct responses, '
     'use other numbers for specific prompts)'
```

**Impact:** The help text now correctly reflects that the default is 0 (no system prompt) rather than 2.

### 2. Translator Logic Improvement (`pepgenx_openai_wrapper/app/services/translator.py`)

**Before:**
```python
# Apply default system prompt if None
if system_prompt is None:
    system_prompt = get_default_system_prompt()

# Handle system_prompt=0 (no system prompt) by setting to None
if system_prompt == 0:
    system_prompt = None
```

**After:**
```python
# Handle system prompt logic:
# - If system_prompt is None (no system messages in OpenAI request), 
#   apply the configured default
# - If system_prompt is 0, set to None (no system prompt)
# - Otherwise, use the provided system_prompt value
if system_prompt is None:
    # No system messages provided, use configured default
    default_prompt = get_default_system_prompt()
    system_prompt = default_prompt if default_prompt != 0 else None
elif system_prompt == 0:
    # Explicit request for no system prompt
    system_prompt = None
```

**Impact:** 
- Clearer logic flow and better comments
- Proper handling of default system prompt 0
- More OpenAI API compliant behavior

### 3. Configuration Comment Update (`pepgenx_openai_wrapper/app/core/config.py`)

**Before:**
```python
description="Default system prompt ID (0=no system prompt for direct answers, 2=Adobe Firefly)"
```

**After:**
```python
description="Default system prompt ID (0=no system prompt for direct "
           "answers, other numbers for specific prompts like "
           "2=Adobe Firefly)"
```

**Impact:** More descriptive and accurate configuration documentation.

### 4. Pydantic Deprecation Fix

**Before:**
```python
messages_dict = [msg.dict() for msg in request.messages]
```

**After:**
```python
messages_dict = [msg.model_dump() for msg in request.messages]
```

**Impact:** Fixed deprecation warning by using the modern Pydantic method.

## Verification

### CLI Testing
```bash
$ python scripts/pepgenx_cli.py test --model gpt-5 --system-prompt 0 --user-prompt "What is 2+2?"
Testing model: gpt-5 (standard)
Provider: openai
Endpoint: generate-response
URL: https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/openai/generate-response
System prompt: None (direct response mode)
User prompt: What is 2+2?
------------------------------------------------------------
Status Code: 200
✅ Response: 4
```

### Framework Testing
All existing tests pass:
```bash
$ cd pepgenx_openai_wrapper && python -m pytest tests/test_translator.py -v
========================================================================= test session starts ==========================================================================
...
========================================================================== 11 passed in 0.26s ==========================================================================
```

## OpenAI API Compliance

The framework now properly follows OpenAI API specification:

1. **No System Messages**: When an OpenAI request contains no system messages, the framework defaults to system prompt 0 (no system prompt), resulting in direct responses.

2. **System Messages Present**: When system messages are provided, they are mapped to appropriate PepGenX system prompt IDs.

3. **Request Serialization**: System prompt values of `None` are properly excluded from the PepGenX API request using `exclude_none=True`.

## Behavior Summary

| Scenario | OpenAI Request | PepGenX system_prompt | Result |
|----------|----------------|----------------------|---------|
| No system messages | `[{"role": "user", "content": "Hello"}]` | `None` (excluded) | Direct response |
| System prompt 0 explicitly | CLI `--system-prompt 0` | `None` (excluded) | Direct response |
| System message provided | `[{"role": "system", "content": "You are helpful"}, ...]` | `2` (helpful assistant) | Formatted response |
| Other system prompt IDs | CLI `--system-prompt 1` | `1` | Specific prompt behavior |

## Breaking Changes

None. All changes are backward compatible and improve the existing behavior without breaking existing functionality.

## Files Modified

1. `scripts/pepgenx_cli.py` - Updated help text and formatting
2. `pepgenx_openai_wrapper/app/services/translator.py` - Improved logic and fixed deprecation
3. `pepgenx_openai_wrapper/app/core/config.py` - Updated configuration comments

## Testing Recommendations

1. Test CLI with various system prompt values (0, 1, 2, etc.)
2. Test OpenAI wrapper with different message patterns
3. Verify that system prompt 0 produces direct responses
4. Confirm other system prompts still work as expected
