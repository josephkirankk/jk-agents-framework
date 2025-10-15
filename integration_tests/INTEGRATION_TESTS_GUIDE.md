# Integration Tests Guide

**Latest Addition**: `test_08_concurrency_integration.py` - Comprehensive concurrency tests with real API and data

## Overview

This is a comprehensive integration test suite for the jk-agents-core system. **NO MOCKING** - all tests use real systems:
- Real LLM APIs (Azure OpenAI, Google Gemini, Anthropic Claude)
- Real ChromaDB database
- Real file system operations
- Real HTTP API endpoints

## Architecture

```
integration_tests/
├── conftest.py                          # Pytest fixtures (DB, LLM, env setup)
├── helpers/
│   ├── __init__.py
│   ├── db.py                           # Real database operations (SQLite)
│   ├── llm_client.py                   # Live LLM client wrapper
│   └── utils.py                        # Utility functions (retry, validation)
├── test_01_basic_flow.py               # Basic agent creation and execution
├── test_02_api_to_llm_flow.py          # Complete API request flow
├── test_03_worker_end_to_end.py        # Job processing workflow
├── test_04_memory_multi_turn.py        # Memory persistence and multi-turn
├── test_05_error_handling_recovery.py  # Error handling and recovery
└── INTEGRATION_TESTS_GUIDE.md          # This file
```

## Test Coverage

### ✅ Test 01: Basic Flow
**File:** `test_01_basic_flow.py`

Tests fundamental agent operations:
- Configuration loading from YAML
- Agent building with real LLM
- Simple query execution
- Deterministic responses (temperature=0)
- Multi-query sequences
- System prompts
- Performance metrics

**Scenarios:** 9 tests  
**Duration:** ~3-5 minutes  
**Requires:** Azure OpenAI credentials

### ✅ Test 02: API to LLM Flow
**File:** `test_02_api_to_llm_flow.py`

Tests complete HTTP API workflow:
- API health checks
- Simple queries via REST API
- Configuration-based routing
- Multi-turn conversations via API
- Error handling for invalid configs
- Response time monitoring
- Memory management endpoints
- Concurrent API requests

**Scenarios:** 9 tests  
**Duration:** ~4-6 minutes  
**Requires:** Azure OpenAI credentials + Running API server

### ✅ Test 03: Worker End-to-End
**File:** `test_03_worker_end_to_end.py`

Tests job processing pipeline:
- Job creation in database
- Worker execution simulation
- Result storage and verification
- Batch job processing
- Error handling in jobs
- Execution logging
- Timeout handling
- Conversation history storage

**Scenarios:** 8 tests  
**Duration:** ~5-7 minutes  
**Requires:** Azure OpenAI credentials

### ✅ Test 04: Memory Multi-Turn
**File:** `test_04_memory_multi_turn.py`

Tests memory persistence and continuity:
- ChromaDB initialization
- Single-turn memory storage
- Multi-turn context building
- Thread isolation
- Memory clear operations
- Long conversation memory
- Memory stats accuracy
- Concurrent memory access
- Memory performance metrics

**Scenarios:** 10 tests  
**Duration:** ~6-10 minutes  
**Requires:** Azure OpenAI + ChromaDB

### ✅ Test 05: Error Handling & Recovery
**File:** `test_05_error_handling_recovery.py`

Tests system resilience:
- Invalid configuration handling
- Retry mechanisms for transient failures
- Timeout enforcement
- Malformed input handling
- Concurrent error scenarios
- Database error recovery
- Memory error recovery
- Error logging verification
- Graceful degradation
- System recovery after failures

**Scenarios:** 11 tests  
**Duration:** ~5-8 minutes  
**Requires:** Azure OpenAI credentials

## Prerequisites

### 1. System Requirements
- Python 3.8+
- 4GB+ RAM
- Virtual environment (`.venv`)

### 2. Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install requirements
uv pip install -r requirements.txt
```

### 3. Environment Configuration

Create or update `.env` file in project root:

```bash
# Required for all tests
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15

# Optional: For Google Gemini tests
GOOGLE_API_KEY=your-google-api-key

# Optional: For Anthropic Claude tests
ANTHROPIC_API_KEY=your-anthropic-key
```

### 4. Verify Setup

```bash
cd integration_tests
python -c "import sys; sys.path.insert(0, '..'); from helpers import *; print('✓ Setup OK')"
```

## Running Tests

### Option 1: Run All Tests

```bash
cd integration_tests
pytest -v -s
```

### Option 2: Run Specific Test File

```bash
# Run basic flow tests
pytest test_01_basic_flow.py -v -s

# Run API tests (requires running server)
pytest test_02_api_to_llm_flow.py -v -s

# Run memory tests
pytest test_04_memory_multi_turn.py -v -s
```

### Option 3: Run by Marker

```bash
# Run only integration tests
pytest -m integration -v -s

# Run only tests that require Azure
pytest -m azure -v -s

# Run only tests that require ChromaDB
pytest -m chromadb -v -s

# Run only slow tests
pytest -m slow -v -s
```

### Option 4: Run Specific Scenario

```bash
# Run specific test function
pytest test_01_basic_flow.py::TestBasicFlow::test_simple_query_execution -v -s
```

### Option 5: Parallel Execution

```bash
# Install pytest-xdist
uv pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest -n 4 -v
```

## Test Fixtures

### Session Fixtures (Setup Once)

- `event_loop` - Async event loop
- `test_root_dir` - Project root directory
- `config_dir` - Configuration directory
- `data_dir` - Data directory for test databases
- `temp_dir` - Temporary directory (cleaned up)
- `env_config` - Environment configuration
- `llm_config` - LLM configuration

### Function Fixtures (Per Test)

- `test_thread_id` - Unique thread ID
- `test_env` - Test environment with cleanup
- `chromadb_memory` - ChromaDB memory backend
- `clean_memory` - Clean memory before test
- `test_config` - Loaded configuration
- `test_agent` - Built agent with real LLM
- `file_storage` - File storage manager
- `performance_tracker` - Performance metrics

## Helper Modules

### helpers/db.py - TestDB

Real SQLite database for testing:

```python
from helpers.db import TestDB

# Create and setup database
db = TestDB("test.db")
db.prepare_schema()

# Create job
job_id = db.create_job({"input": "test query"})

# Update job
db.update_job_status(job_id, "completed", "result")

# Cleanup
db.teardown_schema()
```

### helpers/llm_client.py - LiveLLMClient

Real LLM API client:

```python
from helpers.llm_client import LiveLLMClient

# Create client
client = LiveLLMClient(
    provider="azure_openai",
    model="azure_openai:gpt-4.1",
    temperature=0
)

# Generate response
response = await client.generate(
    prompt="What is 2+2?",
    system_prompt="You are a helpful assistant."
)

print(response.content)  # "4"
```

### helpers/utils.py - Utilities

Utility functions:

```python
from helpers.utils import (
    retry_on_failure,
    validate_json_schema,
    extract_json_from_text,
    contains_keywords,
    wait_for_condition
)

# Retry with exponential backoff
result = await retry_on_failure(
    async_func,
    max_retries=3,
    initial_delay=1.0
)

# Validate JSON schema
is_valid, error = validate_json_schema(data, schema)

# Extract JSON from text
json_obj = extract_json_from_text(response_text)

# Check keywords
has_all = contains_keywords(text, ["python", "programming"])

# Wait for condition
await wait_for_condition(
    lambda: job.status == "completed",
    timeout=30.0
)
```

## API Testing

Tests in `test_02_api_to_llm_flow.py` require the API server to be running.

### Start API Server

```bash
# Terminal 1: Start API server
cd /Users/A80997271/Documents/projects/jk-agents-core
source .venv/bin/activate
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Run API Tests

```bash
# Terminal 2: Run tests
cd integration_tests
source ../.venv/bin/activate
pytest test_02_api_to_llm_flow.py -v -s
```

## Performance Expectations

| Test Suite | Duration | LLM Calls | DB Ops |
|------------|----------|-----------|---------|
| Basic Flow | 3-5 min  | 15-20     | 0       |
| API Flow   | 4-6 min  | 10-15     | 0       |
| Worker E2E | 5-7 min  | 10-15     | 50+     |
| Memory     | 6-10 min | 20-30     | 30+     |
| Error Handling | 5-8 min | 10-15  | 20+     |
| **Total**  | **23-36 min** | **65-95** | **100+** |

## Troubleshooting

### Issue: Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'app'
# Solution: Run from integration_tests directory
cd integration_tests
pytest test_01_basic_flow.py -v -s
```

### Issue: Azure Credentials Not Found

```bash
# Error: Azure OpenAI credentials not configured
# Solution: Check .env file in project root
cat ../.env | grep AZURE_OPENAI

# Verify credentials loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print(os.getenv('AZURE_OPENAI_ENDPOINT'))"
```

### Issue: ChromaDB Not Available

```bash
# Error: ChromaDB not available
# Solution: Install ChromaDB
uv pip install chromadb>=1.0.0

# Verify installation
python -c "import chromadb; print('ChromaDB OK')"
```

### Issue: API Server Not Running

```bash
# Error: Connection refused on localhost:8000
# Solution: Start API server in separate terminal
cd ..
uvicorn api:app --reload
```

### Issue: Tests Timeout

```bash
# Error: asyncio.TimeoutError
# Possible causes:
# 1. Slow LLM response - increase timeout
# 2. Network issues - check internet connection
# 3. API rate limiting - add delays between tests

# Run tests sequentially with delays
pytest -v -s --tb=short
```

### Issue: Memory Tests Fail

```bash
# Error: Memory recall tests fail
# Possible causes:
# 1. Thread not cleared from previous run
# 2. ChromaDB persistence issues

# Solution: Clear test data
rm -rf integration_tests/data/*.db
rm -rf test_checkpoints/*

# Restart tests
pytest test_04_memory_multi_turn.py -v -s
```

## Best Practices

### 1. Test Isolation
- Each test uses unique thread IDs
- Cleanup fixtures run automatically
- Database operations are isolated

### 2. Deterministic Testing
- Use `temperature=0` for predictable responses
- Use keyword matching, not exact string matching
- Verify semantic correctness, not exact wording

### 3. Error Handling
- All tests have proper try/except/finally
- Cleanup happens even on failure
- Errors are logged for debugging

### 4. Performance
- Monitor response times with `performance_tracker`
- Set reasonable timeouts (30s for simple queries)
- Use concurrent execution where appropriate

### 5. Maintenance
- Keep tests independent
- Update expected responses if LLM behavior changes
- Document any provider-specific quirks

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Create venv and install dependencies
        run: |
          uv venv .venv
          source .venv/bin/activate
          uv pip install -r requirements.txt
      
      - name: Run integration tests
        env:
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
          AZURE_OPENAI_DEPLOYMENT: ${{ secrets.AZURE_OPENAI_DEPLOYMENT }}
          AZURE_OPENAI_API_VERSION: "2023-05-15"
        run: |
          source .venv/bin/activate
          cd integration_tests
          pytest -v --tb=short
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: integration_tests/test-results/
```

## Contributing

### Adding New Tests

1. Create test file: `test_06_new_feature.py`
2. Follow existing patterns
3. Use NO MOCKING principle
4. Add proper docstrings
5. Update this guide

### Test Template

```python
"""
Integration Test XX: Feature Name
Description of what this tests.

NO MOCKING - Uses real systems.

Scenarios:
1. Scenario description
2. Another scenario
"""

import pytest
from langchain_core.messages import HumanMessage

@pytest.mark.integration
@pytest.mark.azure
class TestNewFeature:
    """Test new feature."""
    
    @pytest.mark.asyncio
    async def test_scenario(self, test_agent, test_thread_id):
        """
        Scenario: Description
        
        Steps:
        1. Step one
        2. Step two
        3. Verify result
        """
        # Test implementation
        pass
```

## Summary

✅ **No Mocking** - Real LLMs, real databases, real systems  
✅ **Comprehensive** - 47+ test scenarios covering all major flows  
✅ **Isolated** - Each test is independent with proper cleanup  
✅ **Deterministic** - Temperature=0, keyword matching  
✅ **Production-Ready** - Tests real configurations and workflows  
✅ **Maintainable** - Clear structure, fixtures, and helpers  
✅ **CI-Ready** - Can run in automated pipelines  

---

**Last Updated:** 2025-10-13  
**Test Count:** 47 scenarios across 5 test suites  
**Total Coverage:** Config loading, agent building, API endpoints, memory persistence, job processing, error handling
