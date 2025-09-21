# Defect Analysis API - Missing Parameters Fix

## Issue Summary

The defect analysis API endpoint `/defect-analysis/form` was failing with Pydantic validation errors for missing required fields in the `IntentData` model:

```
5 validation errors for IntentData
interpreted_meaning
  Field required [type=missing, input_value={}, input_type=dict]
component
  Field required [type=missing, input_value={}, input_type=dict]
sub_component
  Field required [type=missing, input_value={}, input_type=dict]
related_component
  Field required [type=missing, input_value={}, input_type=dict]
issue
  Field required [type=missing, input_value={}, input_type=dict]
```

## Root Cause Analysis

### The Problem
The issue was in the `invoke_agent_async()` function in `gemba_agents/defect_analysis/utils/agent_utils.py`. The function was not properly extracting the content from LangGraph response objects.

### What Was Happening
1. The `jk_pilger_extract_intent_agent` was correctly generating JSON responses like:
   ```json
   {
     "interpreted_meaning": "The motor bearing is overheating and requires immediate attention.",
     "component": "Motor",
     "sub_component": "Bearing", 
     "related_component": "Unknown",
     "issue": "Overheating"
   }
   ```

2. However, the response was wrapped in a complex LangChain message object structure:
   ```
   content='```json\n{...}\n```' additional_kwargs={} response_metadata={...} name='...' id='...' usage_metadata={...}
   ```

3. The existing response extraction logic only handled dictionary-based messages but not LangChain message objects with `.content` attributes.

4. This caused `parse_json_response()` to receive the entire object string instead of just the JSON content, leading to parsing failures and returning an empty dictionary `{}`.

5. The empty dictionary then failed Pydantic validation for all required fields.

## The Fix

Updated the response extraction logic in `invoke_agent_async()` to handle LangChain message objects:

```python
# Extract the response
if "messages" in result and result["messages"]:
    last_message = result["messages"][-1]
    if isinstance(last_message, dict) and "content" in last_message:
        response = last_message["content"]
    elif hasattr(last_message, 'content'):
        # Handle LangChain message objects
        response = last_message.content
    else:
        response = str(last_message)
else:
    response = str(result)
```

## Verification

### Before Fix
```bash
curl --location 'http://localhost:8000/defect-analysis/form' \
--form 'user_input="Motor bearing overheating"' \
--form 'top_n="5"' \
--form 'min_score="0.7"'
```

Result: Pydantic validation errors for missing fields

### After Fix
Same curl command now returns:
```json
{
  "success": true,
  "original_input": "Motor bearing overheating",
  "intent_data": {
    "component": "Motor",
    "sub_component": "Bearing",
    "related_component": "Unknown", 
    "issue": "Overheating"
  },
  "total_unique_results": 5,
  "defects": [...],
  "root_causes": [...],
  "corrective_actions": [...],
  "processing_time_ms": 0.0,
  "error": null,
  "metadata": {...}
}
```

## Files Modified

- `gemba_agents/defect_analysis/utils/agent_utils.py`: Fixed response extraction logic in `invoke_agent_async()` function

## Impact

- ✅ Defect analysis API now works correctly
- ✅ Intent extraction properly extracts structured data
- ✅ Vector search and result aggregation proceed normally
- ✅ No breaking changes to existing functionality
- ✅ Maintains backward compatibility

## Testing

The fix has been tested with:
- Direct agent invocation
- Full pipeline execution via API endpoint
- Various input formats (English, multilingual)

All tests pass successfully.
