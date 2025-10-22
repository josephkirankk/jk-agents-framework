# API Integration Tests - Complete Guide

## Overview

The `test_09_api_critical_flows.py` test suite validates critical end-to-end API workflows through the FastAPI server. These tests ensure that the API correctly handles:

- Multi-turn conversations with context persistence
- Large dataset storage and retrieval
- Worker endpoint execution with tools
- Memory management operations
- Complex multi-turn workflows
- Performance monitoring
- Error handling and recovery

## Prerequisites

1. **Virtual Environment**: `.venv` with all dependencies installed
2. **Environment Variables**: `.env` file with API keys configured
3. **API Server**: FastAPI server running on `http://localhost:8000`

## Quick Start

### Method 1: Automated Test Runner (Recommended)

The automated test runner handles API server lifecycle management:

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
bash integration_tests/run_api_tests.sh
```

This script will:
1. ✅ Check for virtual environment and .env file
2. 🛑 Stop any existing API server on port 8000
3. 🚀 Start the API server in background
4. ⏳ Wait for server to be ready (up to 60 seconds)
5. 🧪 Run the integration tests
6. 🧹 Clean up and stop the server

### Method 2: Manual Setup

If you prefer manual control:

```bash
# Terminal 1: Start the API server
cd /Users/A80997271/Documents/projects/jk-agents-core
source .venv/bin/activate
python api.py

# Terminal 2: Run the tests
cd /Users/A80997271/Documents/projects/jk-agents-core/integration_tests
source ../.venv/bin/activate
pytest test_09_api_critical_flows.py -v -s
```

## Test Suite Structure

### Test 1: Multi-Turn Conversation
**Purpose**: Validate conversation context persistence across multiple turns

**Flow**:
1. Turn 1: Store information (number 42)
2. Turn 2: Recall the information
3. Turn 3: Use the information in calculations

**Expected**: Agent remembers context and performs calculations correctly

---

### Test 2: Large Dataset Storage
**Purpose**: Validate large data storage and retrieval through API

**Flow**:
1. Create large dataset via query
2. Verify storage in backend
3. List datasets via API endpoint
4. Verify data integrity

**Expected**: Data stored and retrievable correctly

---

### Test 3: Worker Endpoint
**Purpose**: Validate direct worker execution with tools

**Flow**:
1. Call `/worker` endpoint with specific agent
2. Agent executes with tool calling
3. Verify tool execution results

**Expected**: Worker endpoint functional (200, 404, or 500 acceptable)

---

### Test 4: Memory Management
**Purpose**: Validate memory operations through API

**Flow**:
1. Get initial memory statistics
2. Create conversation that generates memory
3. Verify memory tracking updated

**Expected**: Memory stats accessible and updated correctly

---

### Test 5: Multi-Turn Data Accumulation
**Purpose**: Validate progressive data accumulation across turns

**Flow**:
1. Turn 1: Add initial items (apple, banana, cherry)
2. Turn 2: Add more items (date, elderberry)
3. Turn 3: Add final items (fig, grape)
4. Turn 4: Query total count (should be 7)

**Expected**: All data accumulated and counted correctly

---

### Test 6: Performance Monitoring
**Purpose**: Validate API health and performance tracking

**Flow**:
1. Check `/health` endpoint
2. Get performance statistics
3. Make multiple requests
4. Verify performance tracking

**Expected**: Health checks pass, stats tracked correctly

---

### Test 7: Complex Multi-Turn Workflow
**Purpose**: Validate complex workflow with calculations

**Flow**:
1. Initialize: Set budget to $10,000
2. Add expenses: $2,500 + $1,500
3. Calculate: Should have $6,000 remaining
4. Add more: $1,000 marketing
5. Final: Should have $5,000 remaining

**Expected**: All calculations correct with context maintained

---

### Test 8: Error Recovery
**Purpose**: Validate API error handling and recovery

**Flow**:
1. Send invalid request (empty input)
2. Verify error handling (400/422/500)
3. Send valid request
4. Verify system recovered

**Expected**: Graceful error handling, system continues working

---

## Debugging Failed Tests

### Status Code 422 (Unprocessable Entity)

**Cause**: Request validation failed

**Solutions**:
- Check request payload structure matches `QueryRequest` model
- Ensure `input` field is non-empty string
- Verify JSON encoding is correct

**Debug Output**:
```
❌ Request failed with status 422
   Request payload: {...}
   Response: {"detail": [...]}
```

### Status Code 400 (Bad Request)

**Cause**: Invalid request format or missing required data

**Solutions**:
- Check API endpoint exists
- Verify request method (POST vs GET)
- Check content-type headers

### Connection Refused

**Cause**: API server not running

**Solutions**:
```bash
# Option 1: Use test runner
bash integration_tests/run_api_tests.sh

# Option 2: Start manually
bash restart_api.sh

# Option 3: Direct start
source .venv/bin/activate
python api.py
```

### Timeout Errors

**Cause**: API server slow to respond or processing issue

**Solutions**:
- Check API server logs: `logs/api_test.log`
- Increase timeout in test (currently 30-60 seconds)
- Check LLM provider connectivity
- Verify .env has valid API keys

---

## Environment Variables Required

```bash
# Azure OpenAI (Primary)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15

# Optional: Google Gemini
GOOGLE_API_KEY=your-key

# Optional: Anthropic Claude
ANTHROPIC_API_KEY=your-key
```

---

## Test Results Interpretation

### ✅ All Tests Passing
```
8 passed in X.XXs
```
All critical API flows working correctly.

### ⏭️ Tests Skipped
```
8 skipped in 0.XX
```
API server not running. Use test runner script.

### ❌ Tests Failed
```
X failed, Y passed
```
Check debug output for specific failures. Common issues:
- API configuration missing
- LLM provider connectivity
- Database initialization

---

## Logs and Debugging

### API Server Logs
```bash
# Test runner logs
tail -f logs/api_test.log

# Regular API logs
tail -f logs/api_YYYYMMDD.log
```

### Test Output
Use `-s` flag to see print statements:
```bash
pytest test_09_api_critical_flows.py -v -s
```

### Verbose Debugging
```bash
pytest test_09_api_critical_flows.py -v -s --tb=long
```

---

## Performance Expectations

| Test | Expected Duration | Complexity |
|------|------------------|------------|
| Test 1: Multi-Turn | 10-20s | High |
| Test 2: Storage | 5-15s | Medium |
| Test 3: Worker | 5-10s | Medium |
| Test 4: Memory | 5-10s | Low |
| Test 5: Accumulation | 15-25s | High |
| Test 6: Performance | 10-15s | Medium |
| Test 7: Complex | 20-30s | High |
| Test 8: Error Recovery | 5-10s | Low |
| **Total** | **75-135s** | - |

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: API Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install uv
          uv venv .venv
          source .venv/bin/activate
          uv pip install -r requirements.txt
      
      - name: Run API tests
        env:
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        run: |
          bash integration_tests/run_api_tests.sh
```

---

## Troubleshooting

### Port 8000 Already in Use

```bash
# Find process using port 8000
lsof -ti :8000

# Kill the process
kill $(lsof -ti :8000)

# Or use the restart script
bash restart_api.sh
```

### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv
python -m pip install uv
uv venv -p python .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### .env File Missing

```bash
# Copy from example
cp .env.example .env

# Edit with your API keys
nano .env  # or your preferred editor
```

---

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review test output with `-v -s` flags
3. Verify environment variables in `.env`
4. Check API server health: `curl http://localhost:8000/health`
5. Review API docs: `http://localhost:8000/docs`

---

**Last Updated**: 2025-10-16
**Test Suite Version**: 1.0
**Python Version**: 3.12+
**Framework**: pytest, FastAPI, LangChain
