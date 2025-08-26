# TaskGroup Error Analysis and Fix

## Issue Summary

The jk-agents system was experiencing `TaskGroup error processing query: unhandled errors in a TaskGroup (1 sub-exception)` errors that were masking the actual underlying issues.

## Root Cause Analysis

### Initial Problem
The original issue was caused by an **invalid model configuration** in `config\brave_math_weather_hybrid.yaml`:

```yaml
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "openai:google/gemma-3n-e4b"  # ❌ INVALID MODEL
```

The supervisor model `"openai:google/gemma-3n-e4b"` was invalid because:
- It mixed OpenAI prefix with what appears to be a Google model name
- The model doesn't exist in OpenAI's model catalog
- This caused LangGraph initialization failures wrapped in TaskGroup exceptions

### Secondary Issues
After fixing the model configuration, the system revealed the actual underlying issues:
- **Connection failures** to external MCP servers and APIs
- Missing or unavailable services:
  - Brave MCP SSE server at `http://localhost:8080/sse`
  - Weather API server at `http://localhost:8002/weather`
  - Math calculation server at `http://localhost:8001/calculate`

## Solutions Implemented

### 1. Fixed Invalid Model Configuration

**File**: `config\brave_math_weather_hybrid.yaml`

```yaml
# Before (BROKEN)
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "openai:google/gemma-3n-e4b"  # Invalid model

# After (FIXED)
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"  # Valid model
```

### 2. Enhanced TaskGroup Error Handling

**File**: `app\api.py`

Added detailed error extraction and logging:

```python
except BaseExceptionGroup as e:
    # Handle Python 3.11+ TaskGroup exceptions
    log.error(f"TaskGroup error processing query: {e}")
    log.error(f"TaskGroup error type: {type(e)}")
    log.error(f"TaskGroup error args: {e.args}")
    
    # Extract underlying exceptions for better error messages
    underlying_errors = []
    if hasattr(e, 'exceptions'):
        log.error(f"TaskGroup has {len(e.exceptions)} underlying exceptions:")
        for i, exc in enumerate(e.exceptions):
            log.error(f"  Exception {i}: {type(exc).__name__}: {str(exc)}")
            underlying_errors.append(f"{type(exc).__name__}: {str(exc)}")

    if underlying_errors:
        error_msg = "Execution failed: " + "; ".join(underlying_errors)
    else:
        error_msg = f"Execution failed with TaskGroup error: {str(e)}"

    return QueryResponse(
        success=False,
        response="",
        error=error_msg
    )
```

### 3. Improved Error Visibility

The enhanced error handling now provides:
- **Detailed exception type information**
- **Complete error arguments**
- **Individual underlying exception details**
- **User-friendly error messages**

## Test Results

### Before Fix
```
[ERROR] app.api: TaskGroup error processing query: unhandled errors in a TaskGroup (1 sub-exception)
```
- Generic, unhelpful error message
- No indication of the actual problem
- Difficult to debug

### After Fix
```
[ERROR] app.api: TaskGroup error processing query: unhandled errors in a TaskGroup (1 sub-exception)
[ERROR] app.api: TaskGroup error type: <class 'ExceptionGroup'>
[ERROR] app.api: TaskGroup error args: ('unhandled errors in a TaskGroup', [ConnectError('All connection attempts failed')])
[ERROR] app.api: TaskGroup has 1 underlying exceptions:
[ERROR] app.api:   Exception 0: ConnectError: All connection attempts failed
```

**API Response**:
```json
{
  "success": false,
  "response": "",
  "error": "Execution failed: ConnectError: All connection attempts failed"
}
```

## Current Status

✅ **TaskGroup error handling**: Fixed and enhanced
✅ **Invalid model configuration**: Corrected
✅ **Error visibility**: Greatly improved
⚠️ **External service dependencies**: Still need to be addressed

## Next Steps

To fully resolve the system, the following external services need to be started:

1. **Brave MCP SSE Server** on `http://localhost:8080/sse`
2. **Weather API Server** on `http://localhost:8002/weather`
3. **Math Calculation Server** on `http://localhost:8001/calculate`

## Benefits

1. **Better Debugging**: Clear visibility into actual errors
2. **Faster Resolution**: No more guessing what's wrong
3. **Improved Reliability**: Proper error handling prevents crashes
4. **User Experience**: Meaningful error messages instead of cryptic TaskGroup errors
5. **Maintainability**: Easier to diagnose and fix issues

## Files Modified

1. `config\brave_math_weather_hybrid.yaml` - Fixed invalid model configuration
2. `app\api.py` - Enhanced TaskGroup error handling and logging
3. `config/azure_openai_reference.yaml` - **NEW**: Reference configuration with comprehensive testing
4. `docs/TASKGROUP_ERROR_ANALYSIS_AND_FIX.md` - This documentation

## Reference Configuration Created

A new reference configuration `config/azure_openai_reference.yaml` has been created and fully tested with:

### ✅ **Verified Components**
1. **Azure OpenAI GPT-4.1 Models**: All agents use consistent, valid model configuration
2. **Test Agent**: Basic functionality without external dependencies
3. **Python MCP Execution**: Full Python code execution via Deno MCP server
4. **Local HTTP Tools**: Math calculations via local HTTP service
5. **Multi-Agent Workflows**: Complex scenarios with multiple agent coordination
6. **Enhanced Error Handling**: Detailed error reporting and graceful fallbacks

### 🧪 **Test Results Summary**
- ✅ Basic functionality: `"Hello, test basic functionality"` → Success
- ✅ Simple math: `"What is 15 + 27?"` → `42` (correct)
- ✅ Python execution: `"Write Python code to calculate the factorial of 5"` → Shows code + result `120`
- ✅ HTTP tool: `"Calculate 25 * 8 using the math service"` → `200` (correct)
- ✅ Complex workflow: Multi-agent factorial calculation with verification → Success

### 📋 **Configuration Features**
- **Models**: All use `azure_openai:gpt-4.1` for consistency
- **MCP Integration**: Python execution via `@pydantic/mcp-run-python`
- **HTTP Tools**: Local math service integration
- **Verification**: Robust step verification with detailed error messages
- **Fallback Handling**: Graceful degradation when services are unavailable

## Compatibility

- **Python Version**: 3.11+ (TaskGroup support)
- **LangGraph Version**: 0.6.6+
- **Asyncio**: Modern asyncio TaskGroup functionality
- **MCP**: Deno-based Python execution server
- **HTTP Services**: Local calculation services
