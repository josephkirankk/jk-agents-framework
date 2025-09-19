# PepGenX Function Calling - Quick Reference

## TL;DR

✅ **PepGenX wrapper function calling is IMPLEMENTED and WORKING**  
⚠️ **PepGenX gpt-4o model behavior is INCONSISTENT**  
🎯 **Use Azure OpenAI for production, PepGenX for testing**

## Quick Setup

### 1. Start PepGenX Wrapper
```bash
cd pepgenx_openai_wrapper
python start.py
# Runs on http://127.0.0.1:8080
```

### 2. Configure JK-Agents

**For Production (Reliable):**
```yaml
# config/python_agents.yaml
python_exec_agent:
  llm:
    model: "azure_openai:gpt-4.1"
```

**For Testing (Inconsistent):**
```yaml
# config/python_agents.yaml  
python_exec_agent:
  llm:
    model: "openai:gpt-4o"  # Uses PepGenX wrapper
```

### 3. Environment Setup
```bash
# .env file
OPENAI_BASE_URL=http://127.0.0.1:8080/v1  # Routes to PepGenX wrapper
AZURE_OPENAI_ENDPOINT=https://your-azure-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
```

## Test Commands

### Direct HTTP Test (Simple Tool)
```bash
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-test-key1" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Calculate 2 + 2 using the calculate tool"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "calculate",
          "description": "Perform basic arithmetic calculations",
          "parameters": {
            "type": "object",
            "properties": {
              "expression": {"type": "string", "description": "Math expression"}
            },
            "required": ["expression"]
          }
        }
      }
    ],
    "tool_choice": "auto"
  }'
```

### JK-Agents Test (Complex Tool)
```bash
curl --location 'http://localhost:8000/worker/upload' \
  --form 'agent_name="python_exec_agent"' \
  --form 'input="Calculate fibonacci sum"' \
  --form 'config_path="config\\python_agents.yaml"' \
  --form 'raw_output="True"'
```

## Expected Results

| Test Type | PepGenX gpt-4o | Azure OpenAI |
|-----------|----------------|---------------|
| Simple Math | ✅ Works | ✅ Works |
| Python Execution | ❌ Inconsistent | ✅ Works |
| MCP Tools | ❌ Inconsistent | ✅ Works |

## Troubleshooting

### Issue: "HTTP 422" Error
**Cause**: LangChain sending `"parameters": null`  
**Solution**: Use direct HTTP calls or wait for LangChain fix

### Issue: No Tool Calls Made
**Cause**: PepGenX model ignoring tool instructions  
**Solution**: Switch to Azure OpenAI or try `"tool_choice": "required"`

### Issue: Wrapper Not Starting
**Cause**: Missing dependencies or token issues  
**Solution**: Check `pepgenx_openai_wrapper/okta_token.json` and run `pip install -r requirements.txt`

## Key Files Modified

```
pepgenx_openai_wrapper/
├── app/models/openai_models.py     # Added ToolCall, Function, Tool classes
├── app/models/pepgenx_models.py    # Added tools/tool_choice fields
└── app/services/translator.py     # Added tool call parsing

config/
└── python_agents.yaml             # Model configuration

.env                                # API endpoints and keys
```

## Status Summary

- ✅ **Wrapper Implementation**: Complete
- ✅ **Authentication**: Working  
- ✅ **Request Translation**: Working
- ✅ **Response Parsing**: Working
- ✅ **Simple Tools**: Working
- ⚠️ **Complex Tools**: Model inconsistency
- ✅ **Documentation**: Complete

## Next Steps

1. **Production**: Use `azure_openai:gpt-4.1`
2. **Testing**: Monitor PepGenX model improvements
3. **Development**: Test other PepGenX models when available

---
**Last Updated**: September 18, 2025  
**Implementation Status**: ✅ Complete
