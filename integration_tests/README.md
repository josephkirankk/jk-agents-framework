# Integration Tests - JK-Agents-Core

## Overview

Comprehensive integration test suite with **NO MOCKING**. All tests interact with real systems:
- Azure OpenAI API (real API calls)
- ChromaDB (real database operations)
- MCP Servers (real tool execution)
- File system (real storage)
- LiteLLM providers (real multi-provider calls)

## Test Suite

### Test 1: Agent Types with Azure OpenAI
**File:** `test_01_agent_types.py`

Tests:
- ✅ Normal agent creation and invocation
- ✅ React agent creation with tool support
- ✅ Agent configuration options
- ✅ Model selection and temperature settings
- ✅ Multi-query interactions

**Duration:** ~30-60 seconds  
**Prerequisites:** Azure OpenAI credentials

### Test 2: Tool Calling and MCP Servers
**File:** `test_02_tool_calling_mcp.py`

Tests:
- ✅ Python code execution via MCP
- ✅ Tool calling workflow
- ✅ Multiple sequential tool calls
- ✅ Factorial, list processing, string manipulation
- ✅ Multi-step calculations

**Duration:** ~60-90 seconds  
**Prerequisites:** Azure OpenAI credentials

### Test 3: ChromaDB Memory and Multi-turn
**File:** `test_03_chromadb_memory.py`

Tests:
- ✅ ChromaDB initialization
- ✅ Multi-turn conversation persistence
- ✅ Memory recall across turns
- ✅ Thread-based conversation isolation
- ✅ Cross-session memory retrieval

**Duration:** ~45-75 seconds  
**Prerequisites:** Azure OpenAI credentials, ChromaDB installed

### Test 4: Large Data Handling
**File:** `test_04_large_data_handling.py`

Tests:
- ✅ SQLite large data storage
- ✅ Data reference creation
- ✅ Token threshold configuration
- ✅ Smart wrapper (direct vs reference)
- ✅ Data retrieval and verification

**Duration:** ~10-20 seconds  
**Prerequisites:** File system access

### Test 5: LiteLLM Multi-Provider Support
**File:** `test_05_litellm_providers.py`

Tests:
- ✅ Azure OpenAI provider
- ✅ Google Gemini (if credentials available)
- ✅ Anthropic Claude (if credentials available)
- ✅ Provider switching
- ✅ Model configuration

**Duration:** ~30-90 seconds (depends on providers)  
**Prerequisites:** Provider-specific API credentials

## Setup

### 1. Install Dependencies

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update `.env` file with required credentials:

```bash
# Required for all tests
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15

# Optional: For Google Gemini tests
GOOGLE_API_KEY=your-google-api-key

# Optional: For Anthropic Claude tests
ANTHROPIC_API_KEY=your-anthropic-key
```

### 3. Verify Setup

```bash
python -c "from test_utils import *; print('✓ Test utils loaded')"
```

## Running Tests

### Run All Tests

```bash
cd integration_tests
python run_all_tests.py
```

### Run Quick Tests Only

```bash
python run_all_tests.py --quick
```

Quick tests include:
- Test 1: Agent Types
- Test 4: Large Data Handling
- Test 5: LiteLLM Providers

### Run Specific Tests

```bash
# Run tests 1 and 2 only
python run_all_tests.py --test 1 2

# Run test 3 only
python run_all_tests.py --test 3
```

### Run Individual Test

```bash
python test_01_agent_types.py
python test_02_tool_calling_mcp.py
python test_03_chromadb_memory.py
python test_04_large_data_handling.py
python test_05_litellm_providers.py
```

## Test Output

### Success Example

```
================================================================================
  INTEGRATION TEST 1: Agent Types with Azure OpenAI
================================================================================

✓ Azure OpenAI credentials configured

--------------------------------------------------------------------------------
  Testing Normal Agent Creation
--------------------------------------------------------------------------------
✓ Config loaded: 1 agent(s)
✓ Agent built: CompiledStateGraph

...

================================================================================
✅ PASS: Normal Agent with Azure OpenAI
Duration: 12.34s

Details:
  agent_type: normal
  model: azure_openai:gpt-4.1
  total_queries: 2

Sub-tests:
  ✅ Agent Creation
      agent_type: CompiledStateGraph
  ✅ Agent Response
      response_length: 156
      duration: 5.23
  ✅ Math Question
      response: The answer is 4.
================================================================================
```

### Failure Example

```
================================================================================
❌ FAIL: React Agent with Azure OpenAI
Duration: 8.12s
Error: Tool calling failed: 'NoneType' object has no attribute 'tool_calls'

Sub-tests:
  ✅ Agent Creation
  ❌ Tool Calling
      tool_calls_count: 0
      correct_answer: False
================================================================================
```

## Debugging

### Enable Verbose Logging

```bash
export LANGSMITH_TRACING=true
python run_all_tests.py
```

### Check Individual Components

```python
# Test Azure credentials
from test_utils import check_azure_credentials
print(check_azure_credentials())

# Test ChromaDB
from test_utils import verify_chromadb_available
print(verify_chromadb_available())

# Test agent building
from app.main import load_app_config
from app.agent_builder import build_agent
import asyncio

config = load_app_config("../config/python_exec_agent_working.yaml")
agent, mcp = asyncio.run(build_agent(
    config.agents[0],
    config.models['default'],
    "",
    "../config/python_exec_agent_working.yaml"
))
print(f"Agent built: {type(agent).__name__}")
```

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'test_utils'`
- **Fix:** Run tests from `integration_tests/` directory
- Or: `cd integration_tests && python test_01_agent_types.py`

**Issue:** `Azure OpenAI credentials not configured`
- **Fix:** Set all required environment variables in `.env`
- Check: `echo $AZURE_OPENAI_ENDPOINT`

**Issue:** `ChromaDB not available`
- **Fix:** `pip install chromadb`
- Verify: `python -c "import chromadb; print('OK')"`

**Issue:** Tool calling tests fail
- **Fix:** Verify MCP server modules exist in `app/tools/`
- Check: `python -m app.tools.python_runner --help`

## Test Architecture

### No Mocking Philosophy

All tests interact with real systems to ensure:
1. **Real-world validation**: Tests verify actual production behavior
2. **Integration verification**: Tests validate component interactions
3. **End-to-end coverage**: Tests cover full request/response cycles
4. **Configuration validation**: Tests verify YAML configs work correctly
5. **API compatibility**: Tests ensure provider APIs work as expected

### Test Structure

Each test follows this pattern:

```python
async def test_feature():
    result = TestResult("Feature Name")
    env = TestEnvironment("test_name")
    
    try:
        # Setup
        # Execute
        # Verify
        result.add_sub_test("Sub-feature", passed, **details)
        result.finish(True, **summary)
    except Exception as e:
        result.finish(False, error=str(e))
    finally:
        env.cleanup()
    
    return result
```

### Shared Utilities

`test_utils.py` provides:
- `TestResult`: Track test execution and results
- `TestEnvironment`: Manage test files and cleanup
- `TestStats`: Aggregate statistics across tests
- `invoke_agent()`: Helper to call agents
- `extract_tool_calls()`: Parse tool usage from messages
- `check_*_credentials()`: Verify API credentials

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run quick tests
        env:
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
          AZURE_OPENAI_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_DEPLOYMENT }}
          AZURE_OPENAI_API_VERSION: "2023-05-15"
        run: |
          cd integration_tests
          python run_all_tests.py --quick
```

## Test Coverage

### Features Tested

- ✅ Agent Types (Normal, React)
- ✅ Tool Calling
- ✅ MCP Server Integration
- ✅ Multi-turn Conversations
- ✅ Memory Persistence (ChromaDB)
- ✅ Thread Isolation
- ✅ Large Data Handling
- ✅ Token Threshold Configuration
- ✅ Multi-Provider Support (Azure, Google, Anthropic)
- ✅ Configuration Loading
- ✅ Model Selection
- ✅ Temperature Settings

### Not Tested (Unit Test Territory)

- ❌ Internal class methods
- ❌ Error handling edge cases
- ❌ Mock scenarios
- ❌ Performance benchmarks
- ❌ Load testing

## Maintenance

### Adding New Tests

1. Create new test file: `test_06_new_feature.py`
2. Use `test_utils` for consistency
3. Follow NO MOCKING principle
4. Add to `run_all_tests.py` TEST_MODULES
5. Update this README

### Updating Existing Tests

1. Maintain backward compatibility
2. Update sub-test names if changing behavior
3. Keep test duration reasonable (< 2 minutes per test)
4. Document any new prerequisites

## Support

For issues or questions:
1. Check "Common Issues" section above
2. Review individual test output for details
3. Enable verbose logging (`LANGSMITH_TRACING=true`)
4. Check logs in `memory_logs/` directory

## Summary

✅ **No Mocking** - Real system integration  
✅ **Comprehensive** - All major features covered  
✅ **Automated** - Single command execution  
✅ **Production-Ready** - Tests real configurations  
✅ **Maintainable** - Clear structure and utilities

---

**Last Updated:** 2025-10-01  
**Test Count:** 5 test suites, 15+ individual tests  
**Total Coverage:** Agent types, tools, memory, data handling, providers
