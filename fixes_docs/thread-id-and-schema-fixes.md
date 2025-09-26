# Thread ID and Schema Filtering Fixes

## Issue Summary
Two main issues were identified and fixed:

1. **Thread ID Validation**: Thread IDs like "qas" were being rejected due to overly restrictive validation
2. **Google Gemini Schema Filtering**: MCP tools were causing warnings about unsupported schema properties

## Thread ID Validation Fix

### Problem
The `validate_thread_id` function in `app/thread_manager.py` was too restrictive:
- Required minimum length of 5 characters 
- Simple thread IDs like "qas" were rejected and replaced with auto-generated UUIDs
- Users couldn't use simple, memorable thread IDs for conversation continuity

### Solution
Modified the validation logic to be more permissive:
- Minimum length reduced from 5 to 1 character
- Maximum length increased from 100 to 200 characters
- Added support for dots (.) in thread IDs
- Now accepts simple IDs like "qas", "test", "session1", etc.

### Files Changed
- `app/thread_manager.py`: Updated `validate_thread_id()` function

### Testing
Created comprehensive test suite covering:
- Simple short IDs (✓ now accepted)
- IDs with various valid characters
- Invalid IDs (spaces, special chars) still rejected
- Boundary conditions (empty, too long)

## Google Gemini Schema Filtering Fix

### Problem
The Gemini schema filter was failing on MCP tools:
- Trying to call `.model_json_schema()` on MCP tools that don't have this method
- Causing warnings about unsupported schema properties like `additionalProperties` and `$schema`

### Solution  
Enhanced `app/gemini_schema_filter.py` to handle different tool types:
- Added graceful handling for MCP tools that don't have schema methods
- Improved error handling with debug-level logging
- Better detection of schema extraction methods
- Falls back to using tools as-is if schema filtering fails

### Files Changed
- `app/gemini_schema_filter.py`: 
  - Updated `filter_tool_schemas_for_gemini()` function
  - Updated `GeminiCompatibleTool` class constructor

### Additional Fix
Updated the config file to use Azure OpenAI instead of Google Gemini:
- `config/python_exec_agent_working.yaml`: Changed `python_exec_agent` model from `google:gemini-2.5-flash` to `azure_openai:gpt-4.1`

## Benefits
1. **Thread Continuity**: Users can now use simple, memorable thread IDs like "qas" for conversation continuity
2. **Cleaner Logs**: No more schema filtering warnings when using Gemini models with MCP tools  
3. **Better Error Handling**: More graceful handling of different tool types and schema formats
4. **Consistent Model Usage**: All agents now use Azure OpenAI as requested

## Testing Verification
Both fixes were tested and confirmed working:
- Thread ID "qas" is now properly accepted and preserved across API calls
- No more schema filtering warnings in console output
- API functionality remains intact with improved reliability

## Impact
These fixes ensure the system works smoothly with both simple thread IDs and mixed tool types, providing a better user experience without functional regressions.