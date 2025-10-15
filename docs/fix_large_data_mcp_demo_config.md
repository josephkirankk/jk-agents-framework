# Fix: Large Data MCP Demo Configuration Issue

## Problem Summary

The `/query/form` API endpoint was failing with the error:
```
{
    "success": false,
    "response": "",
    "error": "'str' object has no attribute 'invoke'",
    "metadata": null,
    "raw_data": null,
    "thread_id": "jk-pep-10"
}
```

## Root Cause Analysis

### Step-by-Step Investigation

1. **Error Location**: The error occurred in `app/react_agent_compat.py` at line 83:
   ```python
   response = model.invoke(messages)
   ```

2. **Model Creation Failure**: The config file `config/large_data_mcp_demo.yaml` specified:
   ```yaml
   models:
     default: "openai:gpt-4o-mini"
     supervisor: "openai:gpt-4o-mini"
   ```

3. **Missing API Key**: The system tried to create an OpenAI model but failed because `OPENAI_API_KEY` was not set in the environment:
   ```
   ERROR:agent_builder:Failed to create OpenAI model openai:gpt-4o-mini: 
   The api_key client option must be set either by passing api_key to the client 
   or by setting the OPENAI_API_KEY environment variable
   ```

4. **Fallback Logic Issue**: In `app/agent_builder.py`, the `create_model_instance()` function has a fallback mechanism that returns the model_id string when model creation fails:
   ```python
   # Line 344-345
   except Exception as e:
       log.error("Failed to create OpenAI model %s: %s", model_id, e)
       return model_id_without_temp  # Returns a string instead of a model instance!
   ```

5. **String Propagation**: This string was then passed through the system:
   - Returned from `create_model_instance()` → string
   - Used in `build_agent()` → string passed to `create_react_agent()`
   - Stored in agents_map → string stored as "model"
   - Eventually called with `.invoke()` → **AttributeError: 'str' object has no attribute 'invoke'**

## Solution

### What Was Fixed

Updated `config/large_data_mcp_demo.yaml` to use Azure OpenAI (which has proper credentials configured) instead of regular OpenAI:

**Before:**
```yaml
models:
  default: "openai:gpt-4o-mini"
  supervisor: "openai:gpt-4o-mini"

agents:
  - name: "data_generator"
    model: "openai:gpt-4o-mini"
  - name: "data_analyzer"
    model: "openai:gpt-4o-mini"
  - name: "data_manager"
    model: "openai:gpt-4o-mini"
```

**After:**
```yaml
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

agents:
  - name: "data_generator"
    model: "azure_openai:gpt-4.1"
  - name: "data_analyzer"
    model: "azure_openai:gpt-4.1"
  - name: "data_manager"
    model: "azure_openai:gpt-4.1"
```

### Why This Works

The `.env` file has Azure OpenAI credentials configured:
```bash
AZURE_OPENAI_ENDPOINT=https://pep-aisp-hackathon.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=xxx
AZURE_OPENAI_API_VERSION=2023-05-15
```

But does NOT have OpenAI API key:
```bash
# OPENAI_API_KEY=sk-your-openai-api-key-here  # Commented out
```

## Verification

### Test 1: Original Request (Raw Output)
```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="create test data for orders in a cart for 100 customers. each customer should have 50 orders"' \
--form 'config_path="config/large_data_mcp_demo.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-pep-10"'
```

**Result:** ✅ Success
```
Test data for orders in a cart for 100 customers (each with 50 orders) has been generated and stored efficiently.

Preview of the first 5 orders:
1. Order for CUST001 on 2024-11-19 with 4 items
2. Order for CUST001 on 2025-04-14 with 1 item
...

The full dataset is stored and can be retrieved using this reference ID:
ref_5d07a4a32c73
```

### Test 2: Different Request (JSON Output)
```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="create test data for 50 products with prices between 10 and 100"' \
--form 'config_path="config/large_data_mcp_demo.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-thread-123"'
```

**Result:** ✅ Success
```json
{
  "success": true,
  "response": "✅ Test data for 50 products with prices between 10 and 100 has been created...",
  "error": null,
  "metadata": {
    "total_steps": 1,
    "execution_time": null,
    "model_used": "azure_openai:gpt-4.1",
    "files_uploaded": 0,
    "file_info": null
  },
  "thread_id": "test-thread-123"
}
```

## Recommendations for Future

### 1. Improve Error Handling in `create_model_instance()`

Instead of returning a string when model creation fails, the function should:
- Raise a clear exception with actionable error message
- Or return a default/fallback model instance
- Never return a string that will be used as a model

**Suggested Fix:**
```python
# In app/agent_builder.py, line 344-345
except Exception as e:
    log.error("Failed to create OpenAI model %s: %s", model_id, e)
    raise ValueError(
        f"Failed to create model '{model_id}'. "
        f"Please ensure OPENAI_API_KEY is set in your environment, "
        f"or use a different model provider (e.g., azure_openai:, google:, anthropic:)"
    ) from e
```

### 2. Add Configuration Validation

Add a startup validation that checks:
- All configured models can be created successfully
- Required API keys are present for configured models
- Fail fast with clear error messages

### 3. Update Documentation

Add a note in config file templates about model provider requirements:
```yaml
# Model Configuration
# Supported formats:
#   - openai:model-name (requires OPENAI_API_KEY)
#   - azure_openai:deployment-name (requires AZURE_OPENAI_* vars)
#   - google:model-name (requires GOOGLE_API_KEY)
#   - anthropic:model-name (requires ANTHROPIC_API_KEY)
models:
  default: "azure_openai:gpt-4.1"  # Using Azure OpenAI
```

## Files Modified

1. `config/large_data_mcp_demo.yaml` - Updated all model references from `openai:gpt-4o-mini` to `azure_openai:gpt-4.1`

## Related Files

- `app/agent_builder.py` - Contains `create_model_instance()` function with fallback logic
- `app/react_agent_compat.py` - Where the actual `.invoke()` call fails
- `.env` - Contains API key configuration

