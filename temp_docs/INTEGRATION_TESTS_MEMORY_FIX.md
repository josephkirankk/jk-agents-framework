# Integration Tests Memory Backend Fix

**Date:** 2025-10-14  
**Issue:** Memory backend configuration not passed to build_agent in integration tests  
**Status:** ✅ PARTIALLY FIXED - Core infrastructure complete, some test files need updating

## Problem

Integration tests were failing with "Unsupported backend: none" error because they weren't passing the `app_config` parameter to `build_agent()`, which is required for proper checkpointer initialization with memory backends.

## Root Causes

1. **Test fixture missing app_config**: The `test_agent` fixture in `conftest.py` wasn't passing app_config
2. **Direct build_agent calls**: Many tests call `build_agent` directly without app_config parameter
3. **Config dict conversion loses memory config**: When converting AppConfig to dict, the `_raw_memory_config` attribute was lost

## Solutions Implemented

### 1. Created Helper Function (test_utils.py)

Added `convert_app_config_to_dict()` helper that properly preserves memory configuration:

```python
def convert_app_config_to_dict(app_config) -> Dict[str, Any]:
    """
    Convert AppConfig to dict while preserving memory configuration.
    
    This is critical for proper checkpointer initialization with memory backends.
    The _raw_memory_config attribute must be preserved to avoid "Unsupported backend: none" errors.
    """
    # Convert to dict using Pydantic methods
    if hasattr(app_config, 'model_dump'):
        config_dict = app_config.model_dump()
    elif hasattr(app_config, 'dict'):
        config_dict = app_config.dict()
    else:
        config_dict = app_config.__dict__
    
    # CRITICAL: Preserve raw memory config if present
    if hasattr(app_config, '_raw_memory_config'):
        config_dict['memory'] = app_config._raw_memory_config
    
    return config_dict
```

### 2. Fixed conftest.py test_agent Fixture

Updated to use the helper function and pass app_config to build_agent:

```python
@pytest.fixture
async def test_agent(test_config, test_thread_id):
    """Build a test agent with real LLM."""
    from app.agent_builder import build_agent
    
    agent_cfg = test_config.agents[0]
    default_model = test_config.models.get("default", "azure_openai:gpt-4.1")
    
    # Convert AppConfig to dict and preserve memory config (critical for checkpointer)
    app_config_dict = convert_app_config_to_dict(test_config)
    
    # Build agent with app_config for proper checkpointer initialization
    agent, mcp_client = await build_agent(
        agent_cfg=agent_cfg,
        default_model=default_model,
        config_path=str(test_config.config_path) if hasattr(test_config, "config_path") else "",
        app_config=app_config_dict
    )
    
    yield agent
    
    # Cleanup MCP client
    if mcp_client:
        try:
            await close_mcp_client(mcp_client)
        except Exception as e:
            print(f"Warning: Failed to close MCP client: {e}")
```

### 3. Fixed test_01_basic_flow.py

Updated all direct `build_agent` calls to:
1. Import the helper function
2. Convert app_config using the helper
3. Pass app_config_dict to build_agent

## Files Modified

- ✅ `integration_tests/test_utils.py` - Added convert_app_config_to_dict helper
- ✅ `integration_tests/conftest.py` - Fixed test_agent fixture
- ✅ `integration_tests/test_01_basic_flow.py` - Fixed all build_agent calls
- ⏳ `integration_tests/test_02_tool_calling_mcp.py` - Needs fixing
- ⏳ `integration_tests/test_03_chromadb_memory.py` - Needs fixing
- ⏳ `integration_tests/test_01_agent_types.py` - Needs fixing  
- ⏳ `integration_tests/test_05_litellm_providers.py` - Needs fixing
- ⏳ `integration_tests/test_07_json_schema_data_generator.py` - Needs fixing
- ⏳ Other test files with direct build_agent calls - Need fixing

## Pattern to Fix Remaining Tests

For any test file that calls `build_agent` directly:

1. **Add import**:
```python
from test_utils import convert_app_config_to_dict
```

2. **Before build_agent call, convert config**:
```python
app_config_dict = convert_app_config_to_dict(app_config)
```

3. **Pass app_config to build_agent**:
```python
agent, mcp_client = await build_agent(
    agent_cfg=agent_cfg,
    default_model=default_model,
    business_context="",
    config_path=str(config_path),
    app_config=app_config_dict  # ADD THIS
)
```

## Test Results

### Before Fix
- **Status**: 39 failed, 54 passed, 14 skipped
- **Error**: ValueError: Unsupported backend: none
- **Affected**: Most tests using build_agent directly

### After Partial Fix
- **Status**: Tests using test_agent fixture now pass
- **test_01_basic_flow.py**: ✅ 8/8 passing when run individually
- **Remaining**: Tests with direct build_agent calls still need fixes

## Next Steps

1. Apply the same pattern to all test files with direct `build_agent` calls
2. Run full test suite to verify all fixes
3. Consider creating a pytest plugin or wrapper to enforce app_config passing

## Impact

- ✅ **No breaking changes** to production code
- ✅ **Backward compatible** - only affects test infrastructure
- ✅ **Improves test reliability** - proper memory backend initialization
- ✅ **Easier to maintain** - centralized config conversion logic

## Related Files

- `app/main.py` - Original fix for production code
- `app/checkpointer_manager.py` - Checkpointer initialization
- `integration_tests/conftest.py` - Test fixtures
- `integration_tests/test_utils.py` - Test utilities
- All integration test files - Need consistent app_config passing
