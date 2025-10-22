# Quick Test Commands Reference Card

**Last Updated**: 2025-01-21

---

## 🚀 Quick Start (Copy-Paste Ready)

```bash
# Setup (first time only)
cd /Users/A80997271/Documents/projects/jk-agents-core
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Verify setup
python verify_test_setup.py

# Run tests
python integration_tests/run_all_tests.py --quick
```

---

## 📋 Common Commands

### Setup Commands
```bash
# Create virtual environment
uv venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Check setup
python verify_test_setup.py
```

### Run All Tests
```bash
# Activate venv first
source .venv/bin/activate

# All tests (~15-25 min)
python integration_tests/run_all_tests.py

# Quick tests only (~5-10 min)
python integration_tests/run_all_tests.py --quick

# Specific tests (e.g., 1, 3, and 5)
python integration_tests/run_all_tests.py --test 1 3 5
```

### Run Individual Tests
```bash
source .venv/bin/activate

# Test 1: Agent Types
python integration_tests/test_01_agent_types.py

# Test 2: Tool Calling
python integration_tests/test_02_tool_calling_mcp.py

# Test 3: ChromaDB Memory
python integration_tests/test_03_chromadb_memory.py

# Test 4: Large Data
python integration_tests/test_04_large_data_handling.py

# Test 5: Providers
python integration_tests/test_05_litellm_providers.py

# Test 6: Multi-Turn
python integration_tests/test_06_large_data_mcp_demo_multi_turn.py
```

### Using Shell Script
```bash
# Make executable (first time)
chmod +x run_integration_tests_full.sh

# Run all tests
./run_integration_tests_full.sh

# Run quick tests
./run_integration_tests_full.sh --quick

# Run specific tests
./run_integration_tests_full.sh --test 1 2 3
```

---

## 🔍 Verification Commands

```bash
# Check Python version
python --version  # Should be 3.10+

# Verify in virtual environment
which python  # Should show .venv path

# Check installed packages
python -c "import langchain; import chromadb; import litellm; print('✅ All packages OK')"

# Test Azure credentials
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Endpoint:', os.getenv('AZURE_OPENAI_ENDPOINT'))
print('Deployment:', os.getenv('AZURE_OPENAI_DEPLOYMENT'))
"

# Check Deno
deno --version

# Full setup check
python verify_test_setup.py
```

---

## 🛠️ Troubleshooting Commands

```bash
# Recreate virtual environment
rm -rf .venv
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Check .env file
cat .env | grep AZURE

# Test Azure connection
python -c "
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import os

load_dotenv()
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION')
)
print('✅ Azure connection OK')
"

# Clean test data
rm -rf test_memory_chromadb/
rm -rf test_isolation_chromadb/
rm -rf data/test_large_data.db
rm -rf integration_tests/temp/
```

---

## 📊 Test Categories

### Quick Tests (5-10 min, ~$0.03-0.05)
```bash
python integration_tests/run_all_tests.py --quick
# Runs: Test 1, 4, 5
```

### Memory Tests (4-6 min each)
```bash
python integration_tests/test_03_chromadb_memory.py
```

### MCP Tests (3-5 min, requires Deno)
```bash
python integration_tests/test_02_tool_calling_mcp.py
```

### Multi-Agent Tests (8-12 min)
```bash
python integration_tests/test_06_large_data_mcp_demo_multi_turn.py
```

---

## 🎯 One-Liner Quick Tests

```bash
# Complete setup and run quick tests
cd /Users/A80997271/Documents/projects/jk-agents-core && \
source .venv/bin/activate && \
python integration_tests/run_all_tests.py --quick

# Just run test 1 (fastest)
cd /Users/A80997271/Documents/projects/jk-agents-core && \
source .venv/bin/activate && \
python integration_tests/test_01_agent_types.py

# Verify setup and run all tests
cd /Users/A80997271/Documents/projects/jk-agents-core && \
source .venv/bin/activate && \
python verify_test_setup.py && \
python integration_tests/run_all_tests.py
```

---

## 📝 Essential .env Variables

```bash
# Copy to your .env file
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15

# Optional for Test 5
GOOGLE_API_KEY=your-google-key
ANTHROPIC_API_KEY=your-anthropic-key
```

---

## 🔢 Test Numbers Quick Reference

| # | Test Name | Duration | Requires |
|---|-----------|----------|----------|
| 1 | Agent Types | 2-3 min | Azure |
| 2 | Tool Calling | 3-5 min | Azure + Deno |
| 3 | ChromaDB Memory | 4-6 min | Azure + ChromaDB |
| 4 | Large Data | 1-2 min | None (local) |
| 5 | Providers | 2-4 min | Azure (others optional) |
| 6 | Multi-Turn | 8-12 min | Azure |

---

## ⚡ Ultra-Quick Test

Run only Test 4 (no API calls, fastest):
```bash
source .venv/bin/activate
python integration_tests/test_04_large_data_handling.py
```

---

## 📚 Documentation Quick Links

- **Complete Review**: `temp_docs/INTEGRATION_TESTS_REVIEW.md`
- **Execution Guide**: `temp_docs/RUN_INTEGRATION_TESTS_GUIDE.md`
- **Summary**: `temp_docs/INTEGRATION_TESTS_EXECUTION_SUMMARY.md`
- **This File**: `temp_docs/QUICK_TEST_COMMANDS.md`

---

## 🎓 Most Common Workflow

```bash
# 1. Navigate and activate
cd /Users/A80997271/Documents/projects/jk-agents-core
source .venv/bin/activate

# 2. Quick check
python verify_test_setup.py

# 3. Run quick tests first (safer, cheaper)
python integration_tests/run_all_tests.py --quick

# 4. If all pass, run full suite
python integration_tests/run_all_tests.py
```

---

## ⚠️ Common Errors & Quick Fixes

**Error**: `ModuleNotFoundError: No module named 'langchain'`
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

**Error**: `Azure OpenAI credentials not configured`
```bash
cat .env | grep AZURE_OPENAI
# If empty, edit .env file
```

**Error**: `Deno command not found`
```bash
curl -fsSL https://deno.land/x/install/install.sh | sh
export PATH="$HOME/.deno/bin:$PATH"
```

**Error**: `Permission denied`
```bash
chmod +x run_integration_tests_full.sh
```

---

## 📞 Quick Help

**Check what's running**:
```bash
ps aux | grep python
```

**Kill stuck tests**:
```bash
pkill -f "python integration_tests"
```

**See test logs**:
```bash
ls -la integration_tests/*.log 2>/dev/null || echo "No log files"
```

---

**Save this file for quick reference!**

**Pro tip**: Bookmark this file or keep it open in your editor for instant command access.
