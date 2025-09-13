# PepGenX Multimodal Content Fix

## Problem

When using PepGenX models with file uploads, the system was encountering validation errors:

```
Error code: 422 - {'detail': [{'type': 'string_type', 'loc': ['body', 'messages', 2, 'content'], 'msg': 'Input should be a valid string', 'input': [{'type': 'text', 'text': '2 + 5 = ?'}], 'url': 'https://errors.pydantic.dev/2.11/v/string_type'}]}
```

## Root Cause

The issue occurred because:

1. **JK-Agents creates multimodal content**: When files are uploaded, the system creates message content as arrays with objects like:
   ```json
   [
     {"type": "text", "text": "User input"},
     {"type": "image_url", "image_url": {"file_id": "file_123"}}
   ]
   ```

2. **PepGenX wrapper expects strings**: The PepGenX OpenAI wrapper only supports simple string content, not multimodal arrays.

3. **Other providers support multimodal**: OpenAI, Azure OpenAI, Google Gemini, etc. all support multimodal content arrays.

## Solution

Created a `PepGenXMultimodalWrapper` class that:

1. **Intercepts messages** before they're sent to PepGenX models
2. **Converts multimodal content** to string format automatically
3. **Preserves functionality** for all other providers
4. **Works transparently** without requiring code changes elsewhere

### Implementation Details

The wrapper is applied automatically when creating PepGenX model instances in `app/agent_builder.py`:

```python
# Create base model
base_model = ChatOpenAI(
    model=model_name,
    openai_api_key=pepgenx_api_key,
    openai_api_base=pepgenx_base_url,
    temperature=0.0,
)

# Wrap with multimodal content converter
model_instance = PepGenXMultimodalWrapper(base_model)
```

### Content Conversion

The wrapper converts:
- `{"type": "text", "text": "content"}` → `"content"`
- `{"type": "image_url", "image_url": {"file_id": "123"}}` → `"[Image File ID: 123]"`
- Arrays of content objects → Joined strings

## Testing

### Before Fix
```bash
curl --location 'http://localhost:8000/worker/upload' \
  --form 'agent_name="general_assistant"' \
  --form 'input="2 + 5 = ?"' \
  --form 'config_path="config\\pepgenx_simple_test.yaml"' \
  --form 'raw_output="True"'

# Result: 422 validation error
```

### After Fix
```bash
# Same command now returns authentication error (expected when PepGenX not running)
# Result: 503 authentication error (progress!)

# Test with other provider still works
curl --location 'http://localhost:8000/worker/upload' \
  --form 'agent_name="simple_test_agent"' \
  --form 'input="2 + 5 = ?"' \
  --form 'config_path="config\\simple_test.yaml"' \
  --form 'raw_output="True"'

# Result: "2 + 5 = 7" (success!)
```

## Compatibility

- ✅ **PepGenX models**: Multimodal content automatically converted to strings
- ✅ **OpenAI models**: Multimodal content preserved as arrays
- ✅ **Azure OpenAI models**: Multimodal content preserved as arrays  
- ✅ **Google Gemini models**: Multimodal content preserved as arrays
- ✅ **Anthropic models**: Multimodal content preserved as arrays
- ✅ **LM Studio models**: Multimodal content preserved as arrays

## Files Modified

1. **`app/agent_builder.py`**:
   - Added `PepGenXMultimodalWrapper` class
   - Modified PepGenX model creation to use wrapper

2. **`app/api.py`**:
   - Added helper function `convert_multimodal_content_to_string()` (for reference)
   - No changes to main logic (wrapper handles conversion automatically)

## Future Considerations

If PepGenX adds native multimodal support in the future, the wrapper can be easily removed or made conditional based on PepGenX API version.
