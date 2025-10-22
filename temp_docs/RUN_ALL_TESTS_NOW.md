# Run All Integration Tests - Complete Guide

**Date**: 2025-01-21  
**Status**: READY TO EXECUTE  
**Updated**: run_all_tests.py now includes ALL tests ✅

---

## What Was Done

### ✅ Complete Code Review
- Reviewed all 23 test files in integration_tests/
- Analyzed test structure (async vs pytest)
- Verified no mocking - all real systems
- Documented dependencies and requirements

### ✅ Updated Test Runner
- **Before**: Only 6 tests configured
- **After**: 8 async tests + 14 pytest tests
- Added Test 10 (Serper - already passing!)
- Added Test 0 (Super Integrated)
- Added `--list` and `--include-optional` flags

### ✅ Created Documentation
- `ALL_INTEGRATION_TESTS_COMPREHENSIVE.md` - Complete inventory
- `RUN_ALL_TESTS_NOW.md` (this file) - Execution guide

---

## Quick Start - Run Tests Now

### Step 1: List All Available Tests
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
python integration_tests/run_all_tests.py --list
```

**Expected output**:
```
================================================================================
  AVAILABLE INTEGRATION TESTS
================================================================================

Async-based tests (run with this script):
   0. Super Integrated Test (Comprehensive) [OPTIONAL]
      Comprehensive end-to-end test
   1. Agent Types (Normal & React) [QUICK]
      Basic agent creation and invocation
   2. Tool Calling and MCP
      Python code execution via MCP
   3. ChromaDB Memory
      Multi-turn conversation memory
   4. Large Data Handling [QUICK]
      SQLite storage and compression
   5. LiteLLM Multi-Provider [QUICK]
      Azure, Google, Anthropic providers
   6. Large Data MCP Demo - Multi-Turn
      4-turn multi-agent workflow
  10. Serper Search Integration [OPTIONAL]
      Google search via Serper MCP (requires SERPER_API_KEY)

Pytest-based tests (run with 'pytest integration_tests/'):
  - test_00_env_verification.py
  - test_01_basic_flow.py
  - test_01_ado_mcp_connection.py
  ... (14 tests total)
```

### Step 2: Run Quick Tests (Recommended First)
```bash
python integration_tests/run_all_tests.py --quick
```

**Runs**: Tests 1, 4, 5  
**Duration**: 5-10 minutes  
**Cost**: ~$0.03-0.05

### Step 3: Run All Standard Tests
```bash
python integration_tests/run_all_tests.py
```

**Runs**: Tests 1, 2, 3, 4, 5, 6  
**Duration**: 15-25 minutes  
**Cost**: ~$0.10-0.15

### Step 4: Run Including Optional Tests
```bash
python integration_tests/run_all_tests.py --include-optional
```

**Runs**: Tests 0, 1, 2, 3, 4, 5, 6, 10  
**Duration**: 30-40 minutes  
**Cost**: ~$0.30-0.50

---

## Individual Test Execution

### Run Specific Async Tests
```bash
# Run just test 1 (Agent Types - fastest)
python integration_tests/test_01_agent_types.py

# Run test 10 (Serper - you already ran this successfully!)
python integration_tests/test_10_serper_search_integration.py

# Run test 4 (Large Data - no API calls)
python integration_tests/test_04_large_data_handling.py

# Run multiple specific tests
python integration_tests/run_all_tests.py --test 1 4 5
```

### Run Pytest Tests
```bash
# Environment verification first (recommended)
pytest integration_tests/test_00_env_verification.py -v

# All pytest tests (requires API server running)
pytest integration_tests/ -v

# Specific pytest test
pytest integration_tests/test_09_api_critical_flows.py -v
```

---

## Expected Test Results

### Test 1: Agent Types (2-3 min)
```
================================================================================
  INTEGRATION TEST 1: Agent Types with Azure OpenAI
================================================================================

✓ Azure OpenAI credentials configured

--------------------------------------------------------------------------------
  Testing Normal Agent Creation
--------------------------------------------------------------------------------
✓ Config loaded: 1 agent(s)
✓ Agent built: CompiledGraph
✓ Response received (2.34s)

================================================================================
✅ PASS: Normal Agent with Azure OpenAI
Duration: 3.45s
================================================================================

TEST 1 SUMMARY: 3/3 passed
```

### Test 10: Serper (You Already Ran This!)
```
================================================================================
  INTEGRATION TEST 10: Serper Search MCP Integration
================================================================================

✓ Azure OpenAI credentials configured
✓ Serper API key configured

✓ Tool calls made: 1
✓ Google search calls: 1
✓ Got 10 organic search results

================================================================================
✅ PASS: Serper Google Search via MCP
Duration: 11.65s
================================================================================

TEST 10 SUMMARY: 2/2 passed

✅ All Serper search tests passed!
   The 'undefined' query parameter bug is FIXED!
```

---

## Test Execution Commands Reference

### Commands You Can Copy-Paste

```bash
# Navigate to project
cd /Users/A80997271/Documents/projects/jk-agents-core

# Activate virtual environment (if needed)
source .venv/bin/activate

# ===========================================
# OPTION 1: List all tests
# ===========================================
python integration_tests/run_all_tests.py --list

# ===========================================
# OPTION 2: Run quick tests (5-10 min)
# ===========================================
python integration_tests/run_all_tests.py --quick

# ===========================================
# OPTION 3: Run all standard tests (15-25 min)
# ===========================================
python integration_tests/run_all_tests.py

# ===========================================
# OPTION 4: Run with optional tests (30-40 min)
# ===========================================
python integration_tests/run_all_tests.py --include-optional

# ===========================================
# OPTION 5: Run specific tests
# ===========================================
# Tests 1, 4, and 5 only
python integration_tests/run_all_tests.py --test 1 4 5

# Test 10 (Serper) only
python integration_tests/run_all_tests.py --test 10

# ===========================================
# OPTION 6: Run individual test files
# ===========================================
python integration_tests/test_01_agent_types.py
python integration_tests/test_10_serper_search_integration.py
python integration_tests/test_04_large_data_handling.py

# ===========================================
# OPTION 7: Pytest tests (requires API server)
# ===========================================
# Start API server first
./restart_api.sh

# Then run pytest tests
pytest integration_tests/ -v
pytest integration_tests/test_00_env_verification.py -v
pytest integration_tests/test_09_api_critical_flows.py -v
```

---

## Test Categories

### Quick Tests (5-10 min, ~$0.05)
```bash
python integration_tests/run_all_tests.py --quick
```
**Includes**: 
- Test 1: Agent Types
- Test 4: Large Data Handling  
- Test 5: LiteLLM Providers

### Standard Tests (15-25 min, ~$0.15)
```bash
python integration_tests/run_all_tests.py
```
**Includes**: Tests 1, 2, 3, 4, 5, 6

### Optional Tests (additional 20-30 min, ~$0.30)
```bash
python integration_tests/run_all_tests.py --include-optional
```
**Adds**: 
- Test 0: Super Integrated
- Test 10: Serper Search

### Pytest Tests (30-45 min, ~$0.25)
```bash
pytest integration_tests/ -v
```
**Includes**: All 14 pytest-based tests

---

## Troubleshooting

### Issue: "Azure OpenAI credentials not configured"
```bash
# Check .env file
cat .env | grep AZURE_OPENAI

# If missing, copy from example
cp .env.example .env
# Then edit .env with your credentials
```

### Issue: "No module named 'langchain'"
```bash
# Activate venv
source .venv/bin/activate

# Verify activation
which python  # Should show .venv path

# Reinstall if needed
pip install -r requirements.txt
```

### Issue: "Serper API key not configured" (Test 10)
```bash
# Add to .env file
echo "SERPER_API_KEY=your-key-here" >> .env
```

### Issue: "API server not running" (Pytest tests)
```bash
# Start API server
./restart_api.sh

# Verify it's running
curl http://localhost:8000/health
```

---

## What Each Test Does - Quick Reference

| ID | Test | What It Does | Time | Cost |
|----|------|--------------|------|------|
| 0 | Super Integrated | Full system E2E | 20-30m | $0.30 |
| 1 | Agent Types | Basic agents | 2-3m | $0.02 |
| 2 | Tool Calling | MCP Python execution | 3-5m | $0.03 |
| 3 | ChromaDB Memory | Multi-turn memory | 4-6m | $0.02 |
| 4 | Large Data | SQLite storage | 1-2m | $0.00 |
| 5 | LiteLLM | Multi-provider | 2-4m | $0.01 |
| 6 | Multi-Turn | 4-turn workflow | 8-12m | $0.08 |
| 10 | Serper | Google search | 10-15m | $0.04 |

---

## Recommended Execution Order

For first-time comprehensive testing:

### Phase 1: Verification (1 min)
```bash
pytest integration_tests/test_00_env_verification.py -v
```

### Phase 2: Quick Tests (5-10 min)
```bash
python integration_tests/run_all_tests.py --quick
```

### Phase 3: Standard Tests (15-25 min)
```bash
python integration_tests/run_all_tests.py
```

### Phase 4: Optional Tests (as needed)
```bash
# Test 10 if you have Serper key
python integration_tests/run_all_tests.py --test 10

# Test 0 for comprehensive check (takes longest)
python integration_tests/run_all_tests.py --test 0
```

### Phase 5: Pytest Tests (30-45 min)
```bash
# Start API first
./restart_api.sh

# Run all pytest tests
pytest integration_tests/ -v
```

**Total Time**: 50-80 minutes  
**Total Cost**: $0.50-1.00

---

## Current Test Status

Based on your recent execution:

✅ **Test 10 (Serper)**: PASSED  
- Query parameter bug FIXED
- Search results validated
- MCP integration working

🔄 **Other Tests**: Ready to run

---

## Files Updated

1. ✅ `integration_tests/run_all_tests.py` - Updated with all tests
2. ✅ `temp_docs/ALL_INTEGRATION_TESTS_COMPREHENSIVE.md` - Complete inventory
3. ✅ `temp_docs/RUN_ALL_TESTS_NOW.md` - This file
4. ✅ `run_tests_now.sh` - Quick runner script

---

## Next Steps

**Option A: Run Quick Tests (Recommended)**
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
python integration_tests/run_all_tests.py --quick
```

**Option B: Run All Standard Tests**
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
python integration_tests/run_all_tests.py
```

**Option C: Run Everything (Full Suite)**
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
python integration_tests/run_all_tests.py --include-optional
./restart_api.sh
pytest integration_tests/ -v
```

---

## Summary

### What's Ready
- ✅ 8 async tests configured
- ✅ 14 pytest tests documented
- ✅ Test 10 validated (already passing!)
- ✅ run_all_tests.py updated
- ✅ All documentation complete

### To Execute
Just run the commands above! Start with:
```bash
python integration_tests/run_all_tests.py --list
python integration_tests/run_all_tests.py --quick
```

---

**Last Updated**: 2025-01-21  
**Status**: READY TO RUN ✅  
**Action Required**: Execute commands above to run tests

---

## One-Liner Quick Test

If you want the absolute fastest way to test:

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core && python integration_tests/test_04_large_data_handling.py
```

This runs Test 4 (Large Data) which:
- Takes 1-2 minutes
- Makes NO API calls (free!)
- Tests local SQLite storage
- Good smoke test to verify setup
