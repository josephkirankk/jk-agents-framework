# TaskGroup Error Fix Documentation

## Problem Description

The application was experiencing a critical error: `unhandled errors in a TaskGroup (1 sub-exception)` which was causing the server to crash and return incomplete responses. This error is specific to Python 3.11+ and occurs when using asyncio TaskGroup functionality, which is used internally by LangGraph.

## Root Cause Analysis

### Technical Details
- **Error Type**: `BaseExceptionGroup` (Python 3.11+ TaskGroup exception)
- **Location**: LangGraph's internal async execution pipeline
- **Python Version**: 3.13.3 with LangGraph 0.6.6
- **Trigger**: Unhandled exceptions within LangGraph's worker execution

### Error Manifestation
```
[ERROR] app.api: Error processing query: unhandled errors in a TaskGroup (1 sub-exception)
```

The error was occurring in two main execution paths:
1. Async path: `worker_compiled.ainvoke()`
2. Sync path: `asyncio.to_thread(worker_compiled.invoke, ...)`

## Solution Implementation

### 1. Enhanced Error Handling Wrapper

Created a comprehensive error handling system that catches `BaseExceptionGroup` exceptions and extracts meaningful error messages from the underlying exceptions.

**Location**: `app/planner_executor.py`

```python
# Enhanced error handling for LangGraph TaskGroup issues
try:
    # LangGraph execution code
    worker_out = await worker_compiled.ainvoke(worker_state, config=worker_config)
except BaseExceptionGroup as e:
    # Handle Python 3.11+ TaskGroup exceptions
    log.error("TaskGroup exception in step %s: %s", step.id, e)
    # Extract the underlying exception from the TaskGroup
    underlying_exceptions = []
    if hasattr(e, 'exceptions'):
        for exc in e.exceptions:
            underlying_exceptions.append(str(exc))
    
    if underlying_exceptions:
        error_msg = "TaskGroup error: " + "; ".join(underlying_exceptions)
    else:
        error_msg = f"TaskGroup error: {str(e)}"
    raise RuntimeError(error_msg) from e
```

### 2. Async Context Manager

Implemented a safe execution context manager to provide centralized TaskGroup error handling:

```python
@asynccontextmanager
async def safe_langgraph_execution():
    """
    Async context manager for safe LangGraph execution.
    
    This helps prevent TaskGroup exceptions from propagating unhandled
    by providing a controlled execution environment.
    """
    try:
        yield
    except BaseExceptionGroup as e:
        # Handle TaskGroup exceptions by extracting underlying errors
        log.error("TaskGroup exception caught in safe execution context: %s", e)
        underlying_exceptions = []
        if hasattr(e, 'exceptions'):
            for exc in e.exceptions:
                underlying_exceptions.append(str(exc))
        
        if underlying_exceptions:
            error_msg = "Execution failed: " + "; ".join(underlying_exceptions)
        else:
            error_msg = f"Execution failed with TaskGroup error: {str(e)}"
        
        raise RuntimeError(error_msg) from e
    except Exception as e:
        # Re-raise other exceptions normally
        log.error("Exception in safe execution context: %s", e)
        raise
```

### 3. API Layer Error Handling

Enhanced FastAPI error handling to properly catch and format TaskGroup exceptions:

**Location**: `app/api.py`

```python
except BaseExceptionGroup as e:
    # Handle Python 3.11+ TaskGroup exceptions
    log.error(f"TaskGroup error processing query: {e}")
    # Extract underlying exceptions for better error messages
    underlying_errors = []
    if hasattr(e, 'exceptions'):
        for exc in e.exceptions:
            underlying_errors.append(str(exc))
    
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

## Testing and Validation

### Test Commands
```bash
# Test the JSON endpoint
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"input": "print 1 to 10"}'

# Test the form endpoint
curl --location 'http://localhost:8000/query/form' \
  --form 'input="print 1 to 10"' \
  --form 'config_path="config\\brave_math_weather_hybrid.yaml"'
```

### Expected Results
- **Before Fix**: Server crash with unhandled TaskGroup exception
- **After Fix**: Proper JSON error response with meaningful error message

```json
{
  "success": false,
  "response": "",
  "error": "Execution failed: [specific error details]",
  "metadata": null,
  "raw_data": null
}
```

## Benefits

1. **Server Stability**: No more server crashes due to unhandled TaskGroup exceptions
2. **Better Error Messages**: Users receive meaningful error information instead of cryptic TaskGroup errors
3. **Graceful Degradation**: The system continues to operate even when individual requests fail
4. **Debugging Support**: Detailed logging of TaskGroup exceptions for troubleshooting
5. **Future-Proof**: Compatible with Python 3.11+ asyncio TaskGroup functionality

## Files Modified

1. `app/planner_executor.py` - Added TaskGroup error handling and async context manager
2. `app/api.py` - Enhanced API layer error handling for all endpoints

## Compatibility

- **Python Version**: 3.11+ (specifically tested with 3.13.3)
- **LangGraph Version**: 0.6.6+
- **Asyncio**: Compatible with modern asyncio TaskGroup functionality

## Monitoring

The fix includes comprehensive logging to monitor TaskGroup exceptions:
- Error details are logged at ERROR level
- Underlying exceptions are extracted and logged
- Request context is preserved for debugging

This fix ensures the application remains stable and provides meaningful feedback to users when TaskGroup exceptions occur.
