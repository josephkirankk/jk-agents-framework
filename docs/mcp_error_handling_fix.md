# MCP Server Error Handling Fix

## Problem Description

The MCP server was experiencing intermittent failures when the backend API returned HTTP error status codes (like 500 Internal Server Error). The issue was that the MCP server was not properly checking HTTP status codes before processing responses, leading to:

1. **Silent Failures**: 500 errors were being processed as if they were successful responses
2. **Poor Error Messages**: Users received generic "temporary technical issue" messages
3. **No Retry Logic**: Failed requests were not retried automatically
4. **Inconsistent Behavior**: Same CURL commands would sometimes work and sometimes fail

## Root Cause Analysis

### Issue 1: Missing HTTP Status Code Validation

**Location**: `app/mcp_loader.py` lines 357-381 (async) and 456-480 (sync)

**Problem**: The code was not checking `resp.status` or `r.status_code` before processing the response.

```python
# BEFORE (problematic code)
async with resp:
    txt = await resp.text()
# Process txt without checking if resp.status >= 400
```

**Impact**: 500 errors from the backend API were being processed as successful responses, causing JSON parsing errors or returning error HTML as if it were valid data.

### Issue 2: Inadequate Error Response Format

**Problem**: When errors occurred, the MCP server wasn't providing structured error information that matched the expected format from successful calls.

**Impact**: The agent couldn't distinguish between different types of errors or provide meaningful feedback to users.

### Issue 3: No Retry Mechanism

**Problem**: Transient backend API issues (like temporary 500 errors) weren't being retried.

**Impact**: Users experienced failures even when a simple retry would have succeeded.

## Solution Implementation

### 1. HTTP Status Code Validation

Added proper HTTP status code checking in both async and sync HTTP handlers:

```python
# AFTER (fixed code)
async with resp:
    txt = await resp.text()
    
    # Check HTTP status code for errors
    if resp.status >= 400:
        return json.dumps({
            "method": _method,
            "timestamp": int(time.time() * 1000),
            "body": body,
            "baseUrl": _url.split('/api')[0] if '/api' in _url else _url,
            "path": '/api' + _url.split('/api')[1] if '/api' in _url else _url,
            "error": f"{resp.status} {resp.reason} from {_method} {_url}",
            "response_body": txt[:500] + "..." if len(txt) > 500 else txt,
            "hint": "Check backend API logs for detailed error information"
        })
```

### 2. Improved Agent Error Handling

Updated the agent configuration to provide better error messages to users:

```yaml
# Added to agent prompt
9. ERROR HANDLING: If a tool call returns an error (containing "error" field), check if it's a backend API issue:
   - If error contains "500 Internal Server Error", inform user that the restaurant database is temporarily unavailable
   - If error contains "http_request_failed", inform user that the restaurant service is not responding
   - Suggest trying again in a few minutes or contacting support if the issue persists
   - Do not expose technical details like URLs or stack traces to the user
```

### 3. Structured Error Response

The new error response format provides:
- **method**: HTTP method used
- **timestamp**: When the error occurred
- **body**: Request payload (for debugging)
- **baseUrl**: Base URL of the API
- **path**: API endpoint path
- **error**: Human-readable error message
- **response_body**: First 500 characters of error response
- **hint**: Guidance for troubleshooting

## Testing the Fix

### Test Script

Created `test_mcp_error_handling.py` to verify the fix:

```bash
python test_mcp_error_handling.py
```

This script:
1. Tests direct API calls to the agent
2. Checks MCP server accessibility
3. Analyzes log files for error patterns
4. Verifies backend API status

### Manual Testing

Test the same CURL command that was failing:

```bash
curl --location 'http://localhost:8000/worker/upload' \
--form 'agent_name="restaurants_agent"' \
--form 'input="list top 10 restaurants having good menu score selling pizza in new york. include the scores as well"' \
--form 'config_path="config/pep_mcp_sample.yaml"' \
--form 'raw_output="True"'
```

### Expected Behavior After Fix

1. **Clear Error Messages**: Users will receive informative messages about backend API issues
2. **Consistent Responses**: The same request will always return the same type of response (success or structured error)
3. **Better Debugging**: Error responses include enough information for developers to diagnose issues
4. **Graceful Degradation**: The system handles errors gracefully without crashing

## Files Modified

1. **`app/mcp_loader.py`**:
   - Added `import time`
   - Added HTTP status code validation in async handler (lines 357-381)
   - Added HTTP status code validation in sync handler (lines 456-480)

2. **`config/pep_mcp_sample.yaml`**:
   - Enhanced agent prompt with error handling instructions

3. **`test_mcp_error_handling.py`** (new):
   - Comprehensive test script for error handling

4. **`docs/mcp_error_handling_fix.md`** (new):
   - This documentation file

## Monitoring and Maintenance

### Log Analysis

Monitor these log patterns to detect issues:
- `500 Internal Server Error from POST`
- `http_request_failed`
- `Backend API not accessible`

### Health Checks

Consider implementing:
1. **Backend API Health Check**: Periodic checks of backend API availability
2. **MCP Server Health Check**: Verify MCP server is responding
3. **End-to-End Testing**: Regular automated tests of the full flow

### Future Improvements

1. **Retry Logic**: Implement exponential backoff for transient errors
2. **Circuit Breaker**: Temporarily disable failing backend APIs
3. **Caching**: Cache successful responses to serve during outages
4. **Metrics**: Track error rates and response times
5. **Alerting**: Notify administrators of persistent issues

## Troubleshooting

### Common Issues

1. **Backend API Returns 500**: Check backend API logs and service status
2. **MCP Server Not Responding**: Verify MCP server is running on port 8082
3. **Authentication Errors**: Check if API tokens are valid and not expired
4. **Network Issues**: Verify connectivity between MCP server and backend API

### Debug Commands

```bash
# Check MCP server status
curl http://localhost:8082/test/sse

# Check backend API directly (requires valid auth token)
curl -H "Authorization: Bearer <token>" \
  https://apim-na.dev.mypepsico.com/cgf/afhmenupro/v1/afh-menupro-search-api/api/v2/search/dashboard

# View recent logs
ls -la logs/ | head -10
tail -f logs/direct_agentlog_*.log
```
