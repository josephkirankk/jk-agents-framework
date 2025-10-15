# Integration Tests - Quick Start Guide

## 🚀 Run Tests in 3 Steps

### Step 1: Verify Setup (30 seconds)

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core/integration_tests
python3 -c "from test_utils import *; print('✅ Ready!')"
```

If you see `✅ Ready!`, proceed to Step 2.

### Step 2: Run Quick Tests (1-3 minutes)

```bash
python3 run_all_tests.py --quick
```

This runs 3 quick tests:
- Test 1: Agent Types
- Test 4: Large Data Handling
- Test 5: LiteLLM Providers

### Step 3: Run All Tests (3-8 minutes)

```bash
python3 run_all_tests.py
```

This runs all 5 test suites covering all major features.

---

## 📋 Individual Test Commands

Run specific tests:

```bash
# Test 1: Agent Types (Normal & React) - 30-60 sec
python3 test_01_agent_types.py

# Test 2: Tool Calling and MCP - 60-90 sec
python3 test_02_tool_calling_mcp.py

# Test 3: ChromaDB Memory - 45-75 sec
python3 test_03_chromadb_memory.py

# Test 4: Large Data Handling - 10-20 sec
python3 test_04_large_data_handling.py

# Test 5: LiteLLM Providers - 30-90 sec
python3 test_05_litellm_providers.py
```

---

## 🎯 Run Specific Tests Only

```bash
# Run tests 1 and 2 only
python3 run_all_tests.py --test 1 2

# Run test 3 only
python3 run_all_tests.py --test 3
```

---

## ✅ Expected Output

### Success Output
```
================================================================================
  INTEGRATION TEST 1: Agent Types with Azure OpenAI
================================================================================

✓ Azure OpenAI credentials configured

... (test execution) ...

================================================================================
✅ PASS: Normal Agent with Azure OpenAI
Duration: 12.34s
================================================================================

... (more tests) ...

================================================================================
  FINAL INTEGRATION TEST SUMMARY
================================================================================

Completed: 2025-10-01 17:30:00
Duration: 45.67s

Total Tests: 3
✅ Passed: 3
❌ Failed: 0
Pass Rate: 100.0%

🎉 ALL TESTS PASSED!
```

### Failure Output
```
================================================================================
❌ FAIL: React Agent with Azure OpenAI
Duration: 8.12s
Error: Tool calling failed

Sub-tests:
  ✅ Agent Creation
  ❌ Tool Calling
================================================================================

⚠️  1 TEST(S) FAILED
```

---

## 🔧 Troubleshooting

### Issue: Import Error
```
ModuleNotFoundError: No module named 'test_utils'
```
**Fix:** Run from `integration_tests/` directory
```bash
cd integration_tests
python3 test_01_agent_types.py
```

### Issue: Credentials Not Found
```
❌ Azure OpenAI credentials not configured
```
**Fix:** Check `.env` file in parent directory has:
```
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT=...
AZURE_OPENAI_API_VERSION=...
```

### Issue: ChromaDB Not Available
```
⚠️  ChromaDB not available
```
**Fix:** Install ChromaDB
```bash
pip install chromadb
```

---

## 📊 Test Coverage Summary

| Test | Feature | Duration | Prerequisites |
|------|---------|----------|---------------|
| 1 | Agent Types | 30-60s | Azure OpenAI |
| 2 | Tool Calling & MCP | 60-90s | Azure OpenAI |
| 3 | ChromaDB Memory | 45-75s | Azure OpenAI, ChromaDB |
| 4 | Large Data | 10-20s | File system |
| 5 | LiteLLM Providers | 30-90s | Provider API keys |

---

## 🎓 What Tests Validate

✅ **Real System Integration** (NO MOCKING)
- Real Azure OpenAI API calls
- Real ChromaDB operations
- Real MCP server execution
- Real file system operations

✅ **Production Configurations**
- Actual YAML configs
- Real model providers
- Actual tool integrations

✅ **End-to-End Workflows**
- Agent creation → invocation → response
- Tool calling → execution → results
- Memory storage → retrieval → recall

---

## 💡 Tips

### For Development
```bash
# Run just the test you're working on
python3 test_01_agent_types.py

# Enable verbose logging
export LANGSMITH_TRACING=true
python3 test_01_agent_types.py
```

### For CI/CD
```bash
# Quick validation in CI pipeline
python3 run_all_tests.py --quick
```

### For Debugging
```bash
# Run with Python debugger
python3 -m pdb test_01_agent_types.py
```

---

## 📚 More Information

- **Full Documentation:** See `README.md`
- **Implementation Details:** See `../INTEGRATION_TESTS_SUMMARY.md`
- **Test Utilities:** See `test_utils.py`

---

## ✨ Quick Wins

**Want to see it work right now?**

```bash
cd integration_tests
python3 run_all_tests.py --test 4
```

Test 4 (Large Data) runs in ~10-20 seconds and doesn't require API calls!

---

**Happy Testing! 🎉**
