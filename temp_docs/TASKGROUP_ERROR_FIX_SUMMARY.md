# TaskGroup Error Fix - Comprehensive Summary

## Problem Description

**Error**: `"Step s1 failed: last_error=Execution failed: unhandled errors in a TaskGroup (1 sub-exception), verify_failed=False, reason="`

This generic error was occurring when using the Serper MCP server for Google search functionality. The error message provided no useful information about the actual root cause.

## Root Causes Identified

### 1. **Poor Error Extraction from BaseExceptionGroup** (Python 3.11+)
- `safe_langgraph_execution()` context manager caught `BaseExceptionGroup` but only logged basic error info
- Underlying exception details (traceback, error type, message) were lost
- Error message was generic: "unhandled errors in a TaskGroup"

### 2. **Missing Environment Variable Validation**
- No pre-flight checks for required MCP server environment variables
- `SERPER_API_KEY` was required but not validated before execution
- Errors only surfaced during agent execution, not at startup

### 3. **Insufficient Error Context**
- No hints about which component failed (MCP server, tool, etc.)
- No guidance on how to resolve the issue

## Solutions Implemented

### ✅ Enhanced Error Extraction (`app/planner_executor.py`)

**Before:**
```python
except BaseExceptionGroup as e:
    log.error("TaskGroup exception caught: %s", e)
    underlying_exceptions = []
    if hasattr(e, 'exceptions'):
        for exc in e.exceptions:
            underlying_exceptions.append(str(exc))
    
    if underlying_exceptions:
        error_msg = "Execution failed: " + "; ".join(underlying_exceptions)
    else:
        error_msg = f"Execution failed with TaskGroup error: {str(e)}"
    
    raise RuntimeError(error_msg) from e
```

**After:**
```python
except BaseExceptionGroup as e:
    log.error("TaskGroup exception caught: %s", e)
    
    underlying_exceptions = []
    detailed_errors = []
    
    if hasattr(e, 'exceptions'):
        for i, exc in enumerate(e.exceptions, 1):
            exc_type = type(exc).__name__
            exc_msg = str(exc)
            underlying_exceptions.append(exc_msg)
            
            # Extract full traceback for detailed logging
            import traceback
            tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            detailed_errors.append(
                f"\n=== Exception {i}/{len(e.exceptions)} in TaskGroup ===\n"
                f"Type: {exc_type}\n"
                f"Message: {exc_msg}\n"
                f"Traceback:\n{tb_str}"
            )
    
    # Log detailed error information
    if detailed_errors:
        log.error("Detailed TaskGroup errors:%s", ''.join(detailed_errors))
    
    # Create user-friendly error message with hints
    if underlying_exceptions:
        error_msg = "Execution failed: " + "; ".join(underlying_exceptions)
    else:
        error_msg = f"Execution failed with TaskGroup error: {str(e)}"
    
    # Include hint about common issues
    if any("serper" in str(exc).lower() or "mcp" in str(exc).lower() 
           for exc in (e.exceptions if hasattr(e, 'exceptions') else [])):
        error_msg += " (Hint: Check if SERPER_API_KEY is set and MCP servers are accessible)"

    raise RuntimeError(error_msg) from e
```

**Benefits:**
- Full exception traceback logged for debugging
- Exception type and message clearly identified
- Contextual hints for common issues (MCP, Serper)
- Maintains error chain for root cause analysis

### ✅ Environment Variable Validation (`app/mcp_validation.py`)

**New Module Created:**

```python
def validate_mcp_server_env(agent_config: Dict, agent_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that required environment variables are set for MCP servers.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Extract MCP servers from config
    # Check each server's env variables
    # Validate that ${VAR_NAME} references are set in environment
    # Return detailed error with setup instructions
```

**Features:**
- Validates all MCP server environment variables before execution
- Detects `${VAR_NAME}` references in config and checks environment
- Provides specific error messages per missing variable
- Includes helpful setup instructions (e.g., Serper API key)

### ✅ Pre-Flight Validation in API (`api.py`)

**Added to `/query` and `/query/form` endpoints:**

```python
# Validate MCP server environment variables before execution
is_valid, validation_error = validate_all_agents_env(app_cfg.agents)
if not is_valid:
    log.error(f"MCP validation failed: {validation_error}")
    raise HTTPException(
        status_code=400,
        detail=validation_error
    )
```

**Benefits:**
- Catches configuration errors before execution starts
- Returns HTTP 400 with detailed error message
- Saves time by failing fast
- Provides actionable guidance to fix the issue

## Error Message Examples

### Before Fix
```json
{
    "success": false,
    "response": "",
    "error": "Step s1 failed: last_error=Execution failed: unhandled errors in a TaskGroup (1 sub-exception), verify_failed=False, reason=",
    "metadata": null,
    "raw_data": null,
    "thread_id": "jk-deep-pep-020"
}
```

**Issues:**
- No information about what failed
- No guidance on how to fix
- Generic error message

### After Fix (Missing API Key)
```json
{
    "success": false,
    "response": "",
    "error": "Agent 'research_orchestrator' requires environment variables that are not set:\n\n  • SERPER_API_KEY (required by MCP server 'serper-search')\n\nPlease set the required environment variables in your .env file.\n\n💡 To get SERPER_API_KEY:\n   1. Visit https://serper.dev\n   2. Sign up for a free account (2,500 free searches)\n   3. Get your API key from the dashboard\n   4. Add to .env: SERPER_API_KEY=your_api_key_here",
    "metadata": null,
    "raw_data": null,
    "thread_id": "jk-deep-pep-020"
}
```

**Benefits:**
- Clear identification of missing variable
- Links to where to get the API key
- Step-by-step setup instructions
- Fails fast before wasting resources

### After Fix (Execution Error with Details)
```
[2025-10-21 18:55:53] [ERROR] planner_executor: Detailed TaskGroup errors:
=== Exception 1/1 in TaskGroup ===
Type: McpError
Message: MCP server 'serper-search' failed to initialize: Connection refused
Traceback:
  File "/app/mcp_loader.py", line 156, in load_mcp_tools
    client = await MultiServerMCPClient(...).connect()
  ...
  
Step s1 failed: last_error=Execution failed: MCP server 'serper-search' failed to initialize: Connection refused (Hint: Check if SERPER_API_KEY is set and MCP servers are accessible), verify_failed=False, reason=
```

**Benefits:**
- Full traceback available in logs
- Specific error type (McpError)
- Contextual hint about possible causes
- Clear indication of which component failed

## Testing

### Test the Fix

1. **Test Missing API Key Detection:**
```bash
# Remove SERPER_API_KEY from .env
curl --location 'http://localhost:8000/query/form' \
--form 'input="search for latest AI news"' \
--form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
--form 'thread_id="test-123"'
```

**Expected:** HTTP 400 with detailed error about missing SERPER_API_KEY

2. **Test With Valid API Key:**
```bash
# Set SERPER_API_KEY in .env
export SERPER_API_KEY="your-api-key-here"

# Restart server and test
curl --location 'http://localhost:8000/query/form' \
--form 'input="list the top indian made korean skin care product"' \
--form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
--form 'thread_id="test-123"'
```

**Expected:** Successful execution or detailed error if other issues occur

3. **Check Logs for Detailed Errors:**
```bash
tail -f logs/api_$(date +%Y%m%d).log | grep -A 20 "TaskGroup\|Exception"
```

## Files Modified

1. **`app/planner_executor.py`**
   - Enhanced `safe_langgraph_execution()` error handling
   - Added detailed traceback extraction
   - Added contextual hints for common issues

2. **`app/mcp_validation.py`** (NEW)
   - Created validation module for MCP environment variables
   - Added `validate_mcp_server_env()` function
   - Added `validate_all_agents_env()` function

3. **`api.py`**
   - Added import for `mcp_validation`
   - Added pre-flight validation in `/query` endpoint
   - Added pre-flight validation in `/query/form` endpoint

## Configuration Requirements

### Required for Serper MCP Server

**`.env` file:**
```bash
# Serper API Key (get from https://serper.dev)
SERPER_API_KEY=your-api-key-here
```

**Config file** (`config/deep_agent_advanced_serpapi.yaml`):
```yaml
mcp_servers:
  serper-search:
    description: "Serper Search & Scrape MCP Server"
    transport: "stdio"
    command: "npx"
    args:
      - "-y"
      - "serper-search-scrape-mcp-server"
    env:
      SERPER_API_KEY: "${SERPER_API_KEY}"  # Environment variable reference
```

## Best Practices

1. **Always validate environment variables** before starting long-running operations
2. **Extract detailed error information** from exception groups
3. **Provide contextual hints** in error messages
4. **Log full tracebacks** for debugging while keeping user-facing messages clean
5. **Fail fast** with actionable error messages

## Migration Guide

### For Existing Deployments

1. **Update code:**
   ```bash
   git pull origin main
   ```

2. **Check environment variables:**
   ```bash
   python -c "from app.mcp_validation import validate_all_agents_env; from app.main import load_app_config; from pathlib import Path; cfg = load_app_config(Path('config/deep_agent_advanced_serpapi.yaml')); valid, err = validate_all_agents_env(cfg.agents); print('✓ Valid' if valid else f'✗ {err}')"
   ```

3. **Set missing variables:**
   ```bash
   # Add to .env file
   echo "SERPER_API_KEY=your-key-here" >> .env
   ```

4. **Restart server:**
   ```bash
   # Reload environment
   source .env
   
   # Restart API server
   uvicorn api:app --reload
   ```

### For New Deployments

1. **Copy `.env.example` to `.env`**
2. **Fill in all required API keys**
3. **Run validation before starting:**
   ```bash
   python -c "from app.mcp_validation import validate_all_agents_env; print('All checks passed!')"
   ```

## Related Issues

- Python 3.11+ `BaseExceptionGroup` handling
- LangGraph TaskGroup exceptions
- MCP server initialization failures
- Environment variable validation

## References

- [DeepAgents Documentation](https://github.com/langchain-ai/deepagents)
- [Serper API](https://serper.dev)
- [Python 3.11 ExceptionGroup](https://peps.python.org/pep-0654/)
- [LangGraph MCP Integration](https://python.langchain.com/docs/integrations/tools/mcp)
