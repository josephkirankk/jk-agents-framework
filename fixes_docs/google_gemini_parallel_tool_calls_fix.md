# Google Gemini parallel_tool_calls Compatibility Fix

**Date:** September 27, 2025  
**Issue:** Supervisor workflows failing with Google Gemini models  
**Fix Applied:** Conditional parameter handling for model compatibility  

## Problem Description

The jk-agents-framework was experiencing failures when running supervisor workflows with Google Gemini models (e.g., `google:gemini-2.5-flash`). The error was:

```
TypeError: GenerativeServiceAsyncClient.generate_content() got an unexpected keyword argument 'parallel_tool_calls'
```

### Symptoms

- **Direct agent execution**: ✅ Working correctly
- **Supervisor workflows**: ❌ Failing with TypeError
- **Error location**: During LangGraph agent execution in planner_executor.py
- **Affected models**: All Google Gemini models (`google:*` or models containing "gemini")

### Root Cause Analysis

The issue was in `app/agent_builder.py` line 308, where the code was unconditionally passing `parallel_tool_calls=False` to the `bind_tools()` method:

```python
# PROBLEMATIC CODE
model_with_tools = actual_model.bind_tools(
    tools, parallel_tool_calls=False  # ❌ Not supported by Google Gemini
)
```

Google Gemini models in `langchain-google-genai` version 2.0.10 do not support the `parallel_tool_calls` parameter, which is specific to OpenAI-compatible models.

## Solution Implemented

Modified the tool binding logic to be model-aware and only pass the `parallel_tool_calls` parameter to models that support it:

```python
# FIXED CODE
if tools:
    # Check if the model is Google Gemini (doesn't support parallel_tool_calls parameter)
    if model_id.startswith("google:") or "gemini" in model_id.lower():
        # Google Gemini models don't support parallel_tool_calls parameter
        model_with_tools = actual_model.bind_tools(tools)
        log.info(
            "Bound tools for Google Gemini model %s (no parallel_tool_calls param)", agent_cfg.name
        )
    else:
        # Other models support parallel_tool_calls parameter
        model_with_tools = actual_model.bind_tools(
            tools, parallel_tool_calls=False
        )
        log.info(
            "Disabled parallel tool calls for agent %s", agent_cfg.name
        )
else:
    model_with_tools = actual_model
```

## Files Modified

- **File:** `app/agent_builder.py`
- **Lines:** 305-321
- **Change Type:** Conditional parameter handling based on model type

## Testing Results

### Before Fix
- Direct execution: ✅ `python -m app.main "Calculate 2 + 2" --agent python_exec_agent`
- Supervisor workflow: ❌ `python -m app.main "print a table..."`

### After Fix  
- Direct execution: ✅ `python -m app.main "Calculate 5 * 3" --agent python_exec_agent`
- Supervisor workflow: ✅ `python -m app.main "print a table with name and age for 5 records"`

## Compatibility Matrix

| Model Type | parallel_tool_calls Support | Fix Applied |
|------------|---------------------------|-------------|
| Google Gemini (`google:*`) | ❌ No | ✅ Parameter omitted |
| OpenAI (`openai:*`) | ✅ Yes | ✅ Parameter passed |
| Azure OpenAI (`azure_openai:*`) | ✅ Yes | ✅ Parameter passed |
| Anthropic (`anthropic:*`) | ✅ Yes | ✅ Parameter passed |

## Log Evidence

### Successful execution after fix:
```
[INFO] agent_builder: Bound tools for Google Gemini model python_exec_agent (no parallel_tool_calls param)
[INFO] planner_executor: Worker s1 attempt 1: ainvoke done in 2.44s
[INFO] planner_executor: Step s1 completed successfully
```

## Dependencies Affected

- **langchain-google-genai**: 2.0.10
- **langgraph**: 0.6.7
- **Google Gemini Models**: All variants (gemini-2.5-flash, gemini-1.5-pro, etc.)

## Prevention

This fix ensures future compatibility by:

1. **Model Detection**: Automatically detecting Google models by prefix or name
2. **Conditional Parameters**: Only passing supported parameters to each model type
3. **Graceful Degradation**: Maintaining functionality across different model providers
4. **Clear Logging**: Providing distinct log messages for different model handling paths

## Related Issues

- Google Gemini models not supporting OpenAI-specific parameters
- LangChain provider compatibility differences
- Parameter validation in LangGraph agent creation

## Future Considerations

- Monitor for updates to `langchain-google-genai` that might add `parallel_tool_calls` support
- Consider similar compatibility checks for other provider-specific parameters
- Implement automated testing for multi-provider compatibility