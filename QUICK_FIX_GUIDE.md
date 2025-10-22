# Quick Fix Guide - DeepAgents Integration Tests

## 🔥 Issues Fixed

### ✅ Issue #1: Async Fixture Error - FIXED
- **Error**: `'coroutine' object has no attribute 'model'`
- **Fix**: Changed fixtures from `async def` to regular `def`
- **Status**: ✅ Already applied

### ✅ Issue #2: No .env Loading - FIXED
- **Error**: Azure API keys not loaded
- **Fix**: Added `load_dotenv()` at top of test file
- **Status**: ✅ Already applied

### ✅ Issue #3: Hardcoded OpenAI - FIXED
- **Error**: Tests used OpenAI instead of Azure
- **Fix**: Dynamically use Azure when available
- **Status**: ✅ Already applied

### ⚠️ Issue #4: Subagent API Version - USER ACTION NEEDED
- **Error**: `Must provide OPENAI_API_VERSION environment variable`
- **Fix**: Add one line to .env file
- **Status**: ⚠️ **YOU NEED TO DO THIS**

---

## 🚀 Quick Fix (30 seconds)

### Step 1: Add Missing Environment Variable
```bash
# Open your .env file and add this line:
OPENAI_API_VERSION=2023-05-15
```

Or run this command:
```bash
echo "OPENAI_API_VERSION=2023-05-15" >> .env
```

### Step 2: Verify Your .env Has These Variables
```bash
# Required for Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://pep-aisp-hackathon.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_API_VERSION=2023-05-15

# Required for DeepAgents subagents (ADD THIS)
OPENAI_API_VERSION=2023-05-15
```

### Step 3: Run Tests
```bash
pytest temp_tests/test_deep_agent_comprehensive.py -v
```

---

## 📊 Expected Results After Fix

### Should Pass (8 tests):
✅ All 5 Configuration tests  
✅ Basic DeepAgent creation  
✅ DeepAgent with subagents  ← Should now work  
✅ Both Backward compatibility tests  

### Skipped (1 test):
⏭️ Test for missing deepagents package (not applicable)

### May Need API Credits (9 tests):
⏭️ Execution tests (2)  
⏭️ Multi-turn tests (2)  
⏭️ Subagent delegation (1)  
⏭️ MCP integration (1)  
⏭️ Error handling (1)  
⏭️ Performance (1)  

---

## 🎯 Quick Verification

Run this to verify the fix:
```bash
# Test just the subagent creation (the one that was failing)
pytest temp_tests/test_deep_agent_comprehensive.py::TestDeepAgentCreation::test_deep_agent_with_subagents_creation -v -s
```

Expected output:
```
test_deep_agent_with_subagents_creation PASSED ✅
```

---

## 🐛 If Tests Still Fail

### Check Environment Variables
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('AZURE_OPENAI_API_KEY:', 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'MISSING')
print('AZURE_OPENAI_DEPLOYMENT:', os.getenv('AZURE_OPENAI_DEPLOYMENT', 'MISSING'))
print('OPENAI_API_VERSION:', os.getenv('OPENAI_API_VERSION', 'MISSING'))
"
```

Expected output:
```
AZURE_OPENAI_API_KEY: SET
AZURE_OPENAI_DEPLOYMENT: gpt-4.1
OPENAI_API_VERSION: 2023-05-15
```

### Check .env File Location
```bash
# Ensure .env is in project root
ls -la .env
```

---

## 📝 Summary

**Fixed Already** (You don't need to do anything):
- ✅ Async fixture issues
- ✅ .env loading
- ✅ Azure OpenAI configuration

**You Need To Do** (1 step):
- ⚠️ Add `OPENAI_API_VERSION=2023-05-15` to your .env file

**That's it!** After adding that one line, 8/18 tests should pass.

The remaining 9 tests require actual API calls and will consume API credits, so run them only when you're ready to test execution.
