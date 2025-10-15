# Integration Tests Guide

## Overview

The JK Agents Core framework includes a comprehensive integration test suite that validates all major components working together in real-world scenarios. These tests use **NO MOCKING** - they interact with real systems (Azure OpenAI, ChromaDB, file system, etc.) to ensure the framework works correctly in production-like environments.

## Test Suite Location

All integration tests are located in the `integration_tests/` directory:

```
integration_tests/
├── run_all_tests.py                          # Master test runner
├── test_utils.py                             # Shared utilities
├── test_01_agent_types.py                    # Agent creation and types
├── test_02_tool_calling_mcp.py               # Tool calling and MCP integration
├── test_03_chromadb_memory.py                # Memory and multi-turn conversations
├── test_04_large_data_handling.py            # Large data storage and retrieval
├── test_05_litellm_providers.py              # Multi-provider LLM support
└── test_06_large_data_mcp_demo_multi_turn.py # Multi-turn large data workflows
```

## Prerequisites

### Required Environment Variables

The tests require Azure OpenAI credentials to be configured:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4.1"  # or your deployment name
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"
```

### Optional Environment Variables

For additional provider tests:

```bash
export GOOGLE_API_KEY="your-google-api-key"          # For Gemini tests
export ANTHROPIC_API_KEY="your-anthropic-api-key"    # For Claude tests
```

### Virtual Environment

Always use the local virtual environment when running tests:

```bash
# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

## Running Tests

### Run All Tests

```bash
cd integration_tests
python run_all_tests.py
```

### Run Quick Tests Only

Quick tests are faster and suitable for rapid iteration:

```bash
python run_all_tests.py --quick
```

Quick tests include:
- Test 1: Agent Types (Normal & React)
- Test 4: Large Data Handling
- Test 5: LiteLLM Multi-Provider

### Run Specific Tests

Run one or more specific tests by ID:

```bash
# Run a single test
python run_all_tests.py --test 6

# Run multiple tests
python run_all_tests.py --test 1 4 5
```

### Run Individual Test Files

You can also run individual test files directly:

```bash
python test_06_large_data_mcp_demo_multi_turn.py
```

## Test Descriptions

### Test 1: Agent Types (Normal & React)

**File:** `test_01_agent_types.py`  
**Duration:** ~8 seconds  
**Quick Test:** Yes

Tests basic agent creation and invocation:
- Normal conversational agents
- React agents with tool calling
- Agent configuration options (temperature, model selection)
- Multi-turn interactions

**What it validates:**
- Agent builder functionality
- Model instance creation
- Basic conversation flow
- Configuration parsing

### Test 2: Tool Calling and MCP

**File:** `test_02_tool_calling_mcp.py`  
**Duration:** ~15 seconds  
**Quick Test:** No

Tests MCP (Model Context Protocol) server integration:
- Python code execution via MCP
- Tool discovery and registration
- Tool invocation and response handling
- Multiple tool calls in sequence

**What it validates:**
- MCP server connectivity
- Tool registration and discovery
- Python code execution
- Tool response parsing

### Test 3: ChromaDB Memory

**File:** `test_03_chromadb_memory.py`  
**Duration:** ~20 seconds  
**Quick Test:** No

Tests memory persistence and multi-turn conversations:
- ChromaDB initialization and storage
- Multi-turn conversation memory
- Thread-based conversation isolation
- Memory retrieval across sessions

**What it validates:**
- ChromaDB backend functionality
- Conversation context preservation
- Thread isolation
- Memory recall accuracy

### Test 4: Large Data Handling

**File:** `test_04_large_data_handling.py`  
**Duration:** ~2 seconds  
**Quick Test:** Yes

Tests large data storage and retrieval:
- SQLite-based data storage
- Data reference creation
- Token threshold configuration
- Smart wrapper functionality

**What it validates:**
- Large data storage system
- Reference-based data retrieval
- Token optimization
- Data compression

### Test 5: LiteLLM Multi-Provider

**File:** `test_05_litellm_providers.py`  
**Duration:** ~6 seconds  
**Quick Test:** Yes

Tests multi-provider LLM support:
- Azure OpenAI integration
- Google Gemini integration
- Anthropic Claude integration
- Provider switching and fallback

**What it validates:**
- LiteLLM integration
- Multiple provider support
- Model instance creation for different providers
- Provider-specific configuration

### Test 6: Large Data MCP Demo - Multi-Turn

**File:** `test_06_large_data_mcp_demo_multi_turn.py`  
**Duration:** ~60 seconds  
**Quick Test:** No

**NEW TEST** - Tests multi-turn workflows with data generation and analysis:

#### What it Tests

1. **Turn 1: Data Generation**
   - Generates a dataset of 100 customer records
   - Validates dataset creation
   - Checks for reference ID generation

2. **Turn 2: Data Analysis**
   - Analyzes the generated dataset
   - Calculates average purchase amount
   - Identifies top 5 customers
   - Validates statistical analysis

3. **Turn 3: Context-Aware Analysis**
   - Performs analysis based on previous context
   - Counts customers above average
   - Validates context preservation

4. **Turn 4: Multi-Dataset Memory**
   - Generates a new product dataset
   - Tests memory of multiple datasets
   - Validates cross-turn context

#### What it Validates

- **Multi-turn conversation flow:** Ensures context is maintained across multiple interactions
- **Supervisor coordination:** Tests the supervisor's ability to route tasks to appropriate agents
- **Agent collaboration:** Validates data_generator and data_analyzer working together
- **Memory persistence:** Confirms conversation history is preserved
- **Thread isolation:** Ensures each test run has isolated memory

#### Configuration

The test uses a simplified configuration without MCP servers for reliability:
- 2 agents: `data_generator` and `data_analyzer`
- Supervisor-based task routing
- Azure OpenAI GPT-4.1 model
- Temperature: 0.1 for deterministic results

## Test Results and Reporting

### Success Criteria

A test passes if:
- All sub-tests complete successfully
- No exceptions are raised
- Expected outputs are validated
- Response times are reasonable

### Test Output

Each test provides detailed output:

```
================================================================================
✅ PASS: Multi-Turn Data Generation and Analysis
Duration: 58.54s

Details:
  thread_id: test_large_data_9a4cf837
  total_turns: 4
  total_duration: 58.05s
  avg_turn_duration: 14.51s
  agents_used: ["data_generator", "data_analyzer"]

Sub-tests:
  ✅ Turn 1: Data Generation
      duration: 24.37s
      has_dataset_info: True
  ✅ Turn 2: Data Analysis
      duration: 12.17s
      has_average: True
      has_top_customers: True
  ✅ Turn 3: Context-Aware Analysis
      duration: 7.11s
      has_count: True
      has_context: True
  ✅ Turn 4: Multi-Dataset Memory
      duration: 14.39s
      has_new_dataset: True
================================================================================
```

### Final Summary

After all tests complete, a summary is displayed:

```
================================================================================
  FINAL INTEGRATION TEST SUMMARY
================================================================================

Completed: 2025-10-07 23:48:07
Duration: 66.16s

Total Tests: 6
✅ Passed: 6
❌ Failed: 0
Pass Rate: 100.0%

Test Results:
  ✅ PASS - Test 1: Agent Types (Normal & React)
  ✅ PASS - Test 2: Tool Calling and MCP
  ✅ PASS - Test 3: ChromaDB Memory
  ✅ PASS - Test 4: Large Data Handling
  ✅ PASS - Test 5: LiteLLM Multi-Provider
  ✅ PASS - Test 6: Large Data MCP Demo - Multi-Turn

================================================================================

🎉 ALL TESTS PASSED!
```

## Platform Compatibility

All tests are designed to work on both macOS and Windows:

- **macOS:** Uses bash shell and Unix-style paths
- **Windows:** Uses cmd/PowerShell and Windows-style paths

The test framework automatically detects the platform and adjusts accordingly.

## Troubleshooting

### Common Issues

#### 1. Missing Azure Credentials

**Error:** `❌ Azure OpenAI credentials not configured!`

**Solution:** Set the required environment variables:
```bash
export AZURE_OPENAI_ENDPOINT="..."
export AZURE_OPENAI_API_KEY="..."
export AZURE_OPENAI_DEPLOYMENT="..."
export AZURE_OPENAI_API_VERSION="..."
```

#### 2. ChromaDB Not Available

**Error:** `❌ ChromaDB not available!`

**Solution:** Install ChromaDB:
```bash
uv pip install chromadb
```

#### 3. Content Filter Triggered

**Error:** `Azure has not provided the response due to a content filter being triggered`

**Solution:** This is usually caused by sensitive keywords in prompts. The tests have been designed to avoid this, but if it occurs, check the Azure OpenAI content filter settings.

#### 4. MCP Server Connection Failed

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:** Ensure you're running tests from the correct directory and the virtual environment is activated.

## Best Practices

1. **Always use the virtual environment** - Ensures consistent dependencies
2. **Run quick tests first** - Faster feedback during development
3. **Check credentials before running** - Saves time on failed tests
4. **Review test output** - Detailed logs help diagnose issues
5. **Run full suite before commits** - Ensures no regressions

## Adding New Tests

To add a new integration test:

1. Create a new file: `test_XX_description.py`
2. Follow the existing test structure:
   - Import from `test_utils`
   - Create test functions with `TestResult`
   - Use `print_section` for clear output
   - Add cleanup in `finally` blocks
3. Add to `run_all_tests.py`:
   ```python
   {
       "id": 7,
       "name": "Your Test Name",
       "module": "test_07_your_test",
       "quick": False  # or True for quick tests
   }
   ```
4. Document in this guide

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Integration Tests
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
    AZURE_OPENAI_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_DEPLOYMENT }}
    AZURE_OPENAI_API_VERSION: ${{ secrets.AZURE_OPENAI_API_VERSION }}
  run: |
    source .venv/bin/activate
    cd integration_tests
    python run_all_tests.py --quick
```

## Support

For issues or questions:
1. Check this guide first
2. Review test output for detailed error messages
3. Check the main project documentation
4. Open an issue on the project repository

