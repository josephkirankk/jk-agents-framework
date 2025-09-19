# PepGenX Function Calling - Troubleshooting Guide

## Common Issues and Solutions

### 1. HTTP 422 - Validation Error

**Error Message:**
```json
{"detail": "PepGenX API error: HTTP 422"}
```

**Root Cause:**
- Invalid `system_prompt` value (must be 1-7, not 0)
- Missing or malformed tool parameters
- LangChain sending `"parameters": null`

**Solutions:**

#### Fix System Prompt
```python
# pepgenx_openai_wrapper/app/models/pepgenx_models.py
def get_default_system_prompt() -> int:
    # PepGenX API requires system_prompt to be 1-7, not 0
    if default_prompt == 0:
        return 1  # Use system prompt 1 instead of 0
    return default_prompt
```

#### Fix Tool Parameters
```python
# Ensure tools have proper parameter schema
"tools": [
  {
    "type": "function",
    "function": {
      "name": "calculate",
      "parameters": {  # Must not be null
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"]
      }
    }
  }
]
```

### 2. No Tool Calls Made (Model Ignores Tools)

**Symptoms:**
- Model generates text instead of using tools
- `"tool_calls": []` in response
- `"finish_reason": "stop"` instead of `"tool_calls"`

**Root Cause:**
PepGenX gpt-4o model inconsistently follows tool calling instructions

**Solutions:**

#### Use More Explicit Instructions
```python
system_message = """
You MUST use the provided tools. NEVER just describe what you would do.
ALWAYS call the appropriate tool for any computational task.
"""
```

#### Try Required Tool Choice
```json
{
  "tool_choice": "required"  // Instead of "auto"
}
```

#### Switch to Reliable Model
```yaml
# config/python_agents.yaml
model: "azure_openai:gpt-4.1"  # Proven reliable
```

### 3. Wrapper Not Starting

**Error Messages:**
```
ModuleNotFoundError: No module named 'fastapi'
FileNotFoundError: okta_token.json not found
```

**Solutions:**

#### Install Dependencies
```bash
cd pepgenx_openai_wrapper
pip install -r requirements.txt
```

#### Check Token File
```bash
# Verify token file exists and is valid
ls -la pepgenx_openai_wrapper/okta_token.json
python -c "import json; print(json.load(open('pepgenx_openai_wrapper/okta_token.json'))['expires_at'])"
```

#### Check Environment Variables
```bash
# Windows
echo %PEPGENX_API_KEY%
echo %PEPGENX_PROJECT_ID%

# Linux/Mac
echo $PEPGENX_API_KEY
echo $PEPGENX_PROJECT_ID
```

### 4. Authentication Failures

**Error Messages:**
```
HTTP 401 - Unauthorized
HTTP 403 - Forbidden
```

**Solutions:**

#### Refresh OKTA Token
```bash
# Get new token from OKTA and update okta_token.json
# Token expires every hour
```

#### Verify API Keys
```python
# Check .env file
PEPGENX_API_KEY=7079e28e-0...
PEPGENX_PROJECT_ID=1d72f25f-d1db-4f2c-a295-412aae4fce2c
PEPGENX_TEAM_ID=6ad0c340-ce99-477c-9bff-d7e63bfa1104
```

### 5. Connection Refused

**Error Messages:**
```
Connection refused to 127.0.0.1:8080
curl: (7) Failed to connect to 127.0.0.1 port 8080
```

**Solutions:**

#### Check Wrapper Status
```bash
# Check if wrapper is running
netstat -an | findstr :8080  # Windows
netstat -an | grep :8080     # Linux/Mac

# Start wrapper if not running
cd pepgenx_openai_wrapper
python start.py
```

#### Check Port Conflicts
```bash
# Kill existing process on port 8080
taskkill /PID <PID> /F  # Windows
kill -9 <PID>           # Linux/Mac
```

### 6. Tool Call Parsing Errors

**Error Messages:**
```
Failed to parse OpenAI tool call: ...
Unexpected tool call format: ...
```

**Root Cause:**
PepGenX API returning unexpected response format

**Solutions:**

#### Check Raw Response
```python
# Enable debug logging in wrapper
{"raw_response": {...}, "event": "PepGenX raw response structure"}
```

#### Verify Response Format
Expected format:
```json
{
  "choices": [
    {
      "message": {
        "tool_calls": [
          {
            "id": "call_123",
            "type": "function", 
            "function": {"name": "tool_name", "arguments": "{}"}
          }
        ]
      }
    }
  ]
}
```

## Diagnostic Commands

### Check Wrapper Health
```bash
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/
```

### Test Direct API Call
```bash
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-test-key1" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Check Logs
```bash
# Wrapper logs (real-time)
cd pepgenx_openai_wrapper
python start.py  # Watch console output

# JK-Agents logs
ls -la agentlog/
cat agentlog/direct_agentlog_*.log

# LLM payload logs  
ls -la logs/
cat logs/llm_payload_*.json
```

### Verify Environment
```python
# Test script: debug_environment.py
import os
from dotenv import load_dotenv

load_dotenv()

print("Environment Check:")
print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
print(f"PEPGENX_API_URL: {os.getenv('PEPGENX_API_URL')}")

# Check token file
import json
try:
    with open('pepgenx_openai_wrapper/okta_token.json') as f:
        token = json.load(f)
    print(f"Token expires: {token.get('expires_at')}")
except Exception as e:
    print(f"Token error: {e}")
```

## Performance Monitoring

### Success Rate Tracking
```python
# Monitor tool calling success rate
successful_calls = 0
total_calls = 0

# Track in wrapper logs:
# "event": "Parsed X tool calls from OpenAI format"
```

### Response Time Analysis
```python
# Monitor API response times
# Look for: "duration_ms": X in wrapper logs
```

## Recovery Procedures

### Complete Reset
```bash
# 1. Stop all services
taskkill /F /IM python.exe  # Windows (careful!)
pkill -f python             # Linux/Mac (careful!)

# 2. Restart wrapper
cd pepgenx_openai_wrapper
python start.py

# 3. Test basic functionality
curl -s http://127.0.0.1:8080/health

# 4. Test tool calling
python test_pepgenx_direct.py
```

### Fallback to Azure OpenAI
```yaml
# config/python_agents.yaml
python_exec_agent:
  llm:
    model: "azure_openai:gpt-4.1"  # Reliable fallback
```

## Contact and Support

### Internal Resources
- **Implementation Documentation**: `docs/pepgenx-function-calling-implementation.md`
- **Quick Reference**: `docs/pepgenx-quick-reference.md`
- **Test Scripts**: `test_pepgenx_*.py`

### External Resources
- **PepGenX API Documentation**: Internal PepsiCo resources
- **OpenAI API Reference**: https://platform.openai.com/docs/api-reference
- **LangChain Documentation**: https://python.langchain.com/docs/

---
**Last Updated**: September 18, 2025  
**Troubleshooting Status**: ✅ Complete
