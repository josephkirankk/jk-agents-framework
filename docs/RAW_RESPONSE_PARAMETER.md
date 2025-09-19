# Raw Response Parameter Implementation

## Overview

The PepGenX OpenAI Wrapper now includes support for the `raw_response=true` parameter in all API requests sent to the PepGenX API. This parameter ensures that the wrapper receives the complete, unprocessed response from the PepGenX API.

## Implementation Details

### Changes Made

1. **Added `raw_response` parameter to `PepGenXRequest` model**:
   - Location: `pepgenx_openai_wrapper/app/models/pepgenx_models.py`
   - Default value: `True`
   - Type: `Optional[bool]`
   - Description: "Whether to return raw response from PepGenX API"

2. **Automatic inclusion in API requests**:
   - The parameter is automatically included in all PepGenX API requests
   - Uses Pydantic's `model_dump(exclude_none=True)` to serialize the request
   - No changes needed to existing translation logic

### Code Example

```python
from app.models.pepgenx_models import PepGenXRequest

# Default behavior (raw_response=True)
request = PepGenXRequest(
    generation_model="gpt-4",
    custom_prompt="Hello, world!"
)
print(request.raw_response)  # True

# Explicit setting
request_explicit = PepGenXRequest(
    generation_model="gpt-4",
    custom_prompt="Hello, world!",
    raw_response=True
)

# Can be disabled if needed
request_disabled = PepGenXRequest(
    generation_model="gpt-4",
    custom_prompt="Hello, world!",
    raw_response=False
)
```

### API Request Payload

When serialized, the request payload will include:

```json
{
    "generation_model": "gpt-4",
    "custom_prompt": "Hello, world!",
    "raw_response": true,
    // ... other parameters
}
```

## Integration with OpenAI Wrapper

The `raw_response=true` parameter is automatically included when translating OpenAI chat completion requests to PepGenX format:

```python
from app.services.translator import RequestTranslator
from app.models.openai_models import ChatCompletionRequest, ChatMessage, MessageRole

# Create OpenAI request
openai_request = ChatCompletionRequest(
    model="gpt-4",
    messages=[
        ChatMessage(role=MessageRole.USER, content="Hello!")
    ]
)

# Translate to PepGenX format (raw_response=true automatically included)
pepgenx_request = RequestTranslator.translate_chat_completion(openai_request)
print(pepgenx_request.raw_response)  # True
```

## Testing

A comprehensive test suite has been created to verify the implementation:

- **File**: `pepgenx_openai_wrapper/test_raw_response_parameter.py`
- **Tests**:
  - Default value behavior
  - Explicit True/False values
  - Parameter inclusion in serialized payload
  - Integration with RequestTranslator

Run the test with:
```bash
cd pepgenx_openai_wrapper
python test_raw_response_parameter.py
```

## Backward Compatibility

This change is fully backward compatible:

- Existing code will continue to work without modifications
- The parameter defaults to `True`, ensuring raw responses are requested by default
- Can be explicitly set to `False` if needed for specific use cases

## Benefits

1. **Complete Response Data**: Ensures all response data from PepGenX API is preserved
2. **Better Debugging**: Raw responses provide more detailed information for troubleshooting
3. **Future-Proof**: Handles unknown response formats gracefully
4. **Configurable**: Can be disabled if raw responses are not needed

## Configuration

The parameter is set at the request level and defaults to `True`. No additional configuration is required.

## Related Files

- `pepgenx_openai_wrapper/app/models/pepgenx_models.py` - Model definition
- `pepgenx_openai_wrapper/app/services/translator.py` - Request translation
- `pepgenx_openai_wrapper/app/services/pepgenx_client.py` - API client
- `pepgenx_openai_wrapper/test_raw_response_parameter.py` - Test suite
