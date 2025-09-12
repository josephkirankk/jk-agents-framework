# Raw Output Functionality Fix Summary

## Problem Description

The `raw_output` functionality in `app/api.py` was not working as intended. When `raw_output=True` was specified, the API endpoints were still returning structured JSON responses with metadata, success flags, and wrapper structures, instead of returning only the raw response content from the agent as plain text.

## Root Cause

The issue was in three API endpoints:

1. **`/query` endpoint** (lines 556-574): Returned a `QueryResponse` object with raw data in the `raw_data` field
2. **`/worker` endpoint** (lines 827-835): Returned a `WorkerResponse` object with raw data in the `raw_data` field  
3. **`/worker/upload` endpoint** (lines 746-754): Returned a dictionary with raw data in the `raw_data` field

All endpoints were wrapping the raw content in JSON structures with additional metadata.

## Solution Implemented

### 1. Modified Response Behavior

When `raw_output=True`, all three endpoints now return:
- **Plain text responses** using `PlainTextResponse` from FastAPI
- **No JSON wrapping** - just the raw agent response content
- **No metadata, success flags, or other API response formatting**
- **Content-Type: text/plain** instead of application/json

### 2. Specific Changes Made

#### `/query` endpoint (lines 556-564):
```python
if request.raw_output:
    # Return raw text content only - no JSON wrapping
    log.info("Returning raw text content without JSON wrapping")
    human_response = await extract_human_response(result)
    # Return plain text response directly
    return PlainTextResponse(
        content=human_response, media_type="text/plain"
    )
```

#### `/worker` endpoint (lines 825-831):
```python
if request.raw_output:
    # Return raw text content only - no JSON wrapping
    log.info("Returning raw text content without JSON wrapping")
    # For direct agents, return the response text directly
    agent_response_text = result.get("response", "")
    return PlainTextResponse(
        content=agent_response_text, media_type="text/plain"
    )
```

#### `/worker/upload` endpoint (lines 744-751):
```python
if raw_output:
    # Return raw text content only - no JSON wrapping
    log.info("Returning raw text content without JSON wrapping")
    # For direct agents, return the response text directly
    agent_response_text = result.get("response", "")
    return PlainTextResponse(
        content=agent_response_text, media_type="text/plain"
    )
```

### 3. Updated Documentation

Updated the `raw_output` field descriptions in request models:
- **QueryRequest**: "If True, returns only the raw agent response content as plain text with no JSON wrapping or metadata"
- **WorkerRequest**: "If True, returns only the raw agent response content as plain text with no JSON wrapping or metadata"
- **worker/upload Form field**: "If True, returns only raw agent response as plain text"

### 4. Added Import

Added `PlainTextResponse` import at the top of the file:
```python
from fastapi.responses import PlainTextResponse
```

## Expected Behavior After Fix

### When `raw_output=True`:
- **Response Type**: Plain text (Content-Type: text/plain)
- **Content**: Only the agent's final response text
- **No JSON structure, metadata, success flags, or wrapper objects**

### When `raw_output=False` (default):
- **Response Type**: JSON (Content-Type: application/json)
- **Content**: Structured response with success, response, metadata, etc.
- **Maintains backward compatibility**

## Raw Content Sources

- **For `/query` endpoint**: Uses `extract_human_response()` to get the final human response from supervised execution
- **For `/worker` and `/worker/upload` endpoints**: Uses `result.get("response", "")` to get the direct agent response text

## Testing

Created `test_raw_output_fix.py` to verify:
1. `/query` endpoint returns plain text when `raw_output=True`
2. `/worker` endpoint returns plain text when `raw_output=True`
3. Formatted output still works correctly when `raw_output=False`
4. Responses have correct Content-Type headers
5. Raw responses are not valid JSON (confirming no wrapper structure)

## Benefits

1. **True raw output**: API consumers get exactly what the agent generated
2. **No parsing required**: Plain text can be used directly without JSON parsing
3. **Reduced payload size**: No metadata or wrapper structures
4. **Backward compatibility**: Formatted responses unchanged when `raw_output=False`
5. **Clear intent**: `raw_output=True` now truly means "raw output only"

## Files Modified

- `app/api.py`: Main implementation changes
- `test_raw_output_fix.py`: Test script to verify functionality
- `RAW_OUTPUT_FIX_SUMMARY.md`: This documentation

The fix ensures that `raw_output=True` returns only the raw response content from the agent with no additional formatting, metadata, or wrapper structures, exactly as requested.
