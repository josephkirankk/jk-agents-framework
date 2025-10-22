# Integration Tests Execution Guide

**Created**: 2025-01-21  
**Purpose**: Step-by-step guide to run all integration tests

---

## Quick Start

```bash
# 1. Verify setup
python verify_test_setup.py

# 2. Run all tests
./run_integration_tests_full.sh

# OR run with Python directly
source .venv/bin/activate
python integration_tests/run_all_tests.py
```

---

## Step-by-Step Setup

### 1. Check Prerequisites

**System Requirements:**
- macOS (current system)
- Python 3.10 or higher
- Internet connection for API calls

**Optional:**
- Deno runtime (for MCP Python tools in Test 2)
- uv package manager (faster than pip)

### 2. Install System Dependencies

```bash
# Install Deno (if not already installed)
curl -fsSL https://deno.land/x/install/install.sh | sh

# Install uv (optional but recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create Virtual Environment

```bash
# Navigate to project root
cd /Users/A80997271/Documents/projects/jk-agents-core

# Create virtual environment with uv
uv venv .venv

# OR with Python venv
python3 -m venv .venv

# Activate
source .venv/bin/activate
```

### 4. Install Python Dependencies

```bash
# With uv (faster)
uv pip install -r requirements.txt

# OR with pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Required credentials in .env:**
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15
```

**Optional credentials (for Test 5):**
```bash
GOOGLE_API_KEY=your-google-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### 6. Verify Setup

```bash
# Run verification script
python verify_test_setup.py
```

This will check:
- ✅ Python version
- ✅ Installed packages
- ✅ .env file
- ✅ Azure credentials
- ✅ System commands (deno, uv)
- ✅ File permissions
- ✅ Azure OpenAI connection

---

## Running Tests

### Option 1: Using Shell Script (Recommended)

```bash
# Make script executable (first time only)
chmod +x run_integration_tests_full.sh

# Run all tests
./run_integration_tests_full.sh

# Run quick tests only
./run_integration_tests_full.sh --quick

# Run specific tests (e.g., test 1 and 3)
./run_integration_tests_full.sh --test 1 3
```

### Option 2: Direct Python Execution

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
python integration_tests/run_all_tests.py

# Run quick tests only
python integration_tests/run_all_tests.py --quick

# Run specific tests
python integration_tests/run_all_tests.py --test 1 2 3
```

### Option 3: Individual Test Modules

```bash
# Activate virtual environment
source .venv/bin/activate

# Run individual tests
python integration_tests/test_01_agent_types.py
python integration_tests/test_02_tool_calling_mcp.py
python integration_tests/test_03_chromadb_memory.py
python integration_tests/test_04_large_data_handling.py
python integration_tests/test_05_litellm_providers.py
python integration_tests/test_06_large_data_mcp_demo_multi_turn.py
```

---

## Test Categories

### Quick Tests (5-10 minutes)
- **Test 1**: Agent Types - Normal and React agents
- **Test 4**: Large Data Handling - Storage and compression
- **Test 5**: LiteLLM Providers - Multi-provider support

```bash
python integration_tests/run_all_tests.py --quick
```

### Full Test Suite (15-25 minutes)
All 6 tests including:
- Multi-turn conversations
- ChromaDB persistence
- Complex multi-agent workflows

```bash
python integration_tests/run_all_tests.py
```

---

## Understanding Test Output

### Successful Test Run
```
================================================================================
  Running Test 1: Agent Types (Normal & React)
================================================================================

--------------------------------------------------------------------------------
  Testing Normal Agent Creation
--------------------------------------------------------------------------------
✓ Config loaded: 1 agent(s)
✓ Agent built: CompiledGraph
✓ Response received (2.34s)
  Response: I am a normal conversational agent...
  Messages: 2

================================================================================
✅ PASS: Normal Agent with Azure OpenAI
Duration: 3.45s
...
================================================================================
```

### Failed Test
```
================================================================================
❌ FAIL: Test Name
Duration: 1.23s
Error: Azure OpenAI credentials not configured
================================================================================
```

### Final Summary
```
================================================================================
  FINAL INTEGRATION TEST SUMMARY
================================================================================

Completed: 2025-01-21 14:30:45
Duration: 245.67s

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
================================================================================
```

---

## Common Issues & Solutions

### Issue 1: "Azure OpenAI credentials not configured"

**Cause**: Missing or incorrect environment variables

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify credentials are set
grep AZURE_OPENAI .env

# Test connection
python verify_test_setup.py
```

### Issue 2: "ModuleNotFoundError: No module named 'langchain'"

**Cause**: Dependencies not installed or wrong Python environment

**Solution**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify you're in the venv
which python  # Should show .venv path

# Reinstall dependencies
uv pip install -r requirements.txt
```

### Issue 3: "Deno command not found"

**Cause**: Deno not installed (required for Test 2)

**Solution**:
```bash
# Install Deno
curl -fsSL https://deno.land/x/install/install.sh | sh

# Add to PATH (add to ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/.deno/bin:$PATH"

# Verify installation
deno --version
```

### Issue 4: "ChromaDB not available"

**Cause**: ChromaDB package not installed

**Solution**:
```bash
source .venv/bin/activate
uv pip install chromadb>=1.0.0
```

### Issue 5: "Permission denied" on directories

**Cause**: Insufficient write permissions

**Solution**:
```bash
# Create required directories
mkdir -p integration_tests/temp data test_data

# Set permissions
chmod -R u+w integration_tests/temp data test_data
```

### Issue 6: Test hangs or times out

**Cause**: Network issues or API rate limits

**Solution**:
- Check internet connection
- Verify Azure OpenAI endpoint is accessible
- Check Azure subscription hasn't hit rate limits
- Try running individual tests instead of full suite

### Issue 7: "Tool calls not detected" in Test 2

**Cause**: MCP Python server not working

**Solution**:
```bash
# Verify Deno is installed
deno --version

# Check Deno permissions
deno cache jsr:@pydantic/mcp-run-python

# Run Test 2 separately for detailed output
python integration_tests/test_02_tool_calling_mcp.py
```

---

## Test-Specific Notes

### Test 1: Agent Types
- **Duration**: ~2-3 minutes
- **Requirements**: Azure OpenAI only
- **What it tests**: Basic agent creation, normal vs react agents
- **No external services**: Only Azure OpenAI

### Test 2: Tool Calling & MCP
- **Duration**: ~3-5 minutes
- **Requirements**: Azure OpenAI + Deno
- **What it tests**: Real Python code execution via MCP
- **Important**: First run may be slower (Deno caching)

### Test 3: ChromaDB Memory
- **Duration**: ~4-6 minutes
- **Requirements**: Azure OpenAI + ChromaDB
- **What it tests**: Multi-turn memory persistence
- **Creates**: ChromaDB files in `test_memory_chromadb/`

### Test 4: Large Data Handling
- **Duration**: ~1-2 minutes
- **Requirements**: None (local only)
- **What it tests**: SQLite storage, compression
- **Creates**: Database in `data/test_large_data.db`

### Test 5: LiteLLM Providers
- **Duration**: ~2-4 minutes
- **Requirements**: At least Azure OpenAI (others optional)
- **What it tests**: Multi-provider support
- **Skips**: Tests for providers without credentials

### Test 6: Multi-Turn Workflow
- **Duration**: ~8-12 minutes (longest test)
- **Requirements**: Azure OpenAI
- **What it tests**: Complex 4-turn multi-agent workflow
- **API calls**: Most expensive test (4 supervisor + agent calls)

---

## Cost Estimation

**API Usage** (approximate per full test run):

- **Test 1**: ~6 API calls
- **Test 2**: ~8 API calls
- **Test 3**: ~6 API calls
- **Test 4**: 0 API calls (local only)
- **Test 5**: ~3 API calls (Azure only, others optional)
- **Test 6**: ~12-16 API calls (4 turns with supervisor)

**Total**: ~35-40 Azure OpenAI API calls per full test run

**Estimated cost** (GPT-4 pricing):
- Input: ~5,000-8,000 tokens = $0.03-$0.05
- Output: ~2,000-3,000 tokens = $0.06-$0.09
- **Total per run**: ~$0.10-$0.15

---

## Best Practices

### Before Running Tests

1. ✅ Run `python verify_test_setup.py` first
2. ✅ Ensure Azure subscription has sufficient quota
3. ✅ Check internet connection is stable
4. ✅ Close other applications that may use Azure API
5. ✅ Consider running quick tests first

### During Test Execution

1. 📊 Monitor output for any errors
2. ⏱️  Be patient - some tests take several minutes
3. 🚫 Don't interrupt tests (Ctrl+C may leave resources)
4. 📝 Save test output for troubleshooting if needed

### After Test Completion

1. 📋 Review test summary for any failures
2. 🧹 Clean up test data if needed:
   ```bash
   rm -rf test_memory_chromadb/
   rm -rf data/test_large_data.db
   rm -rf integration_tests/temp/
   ```
3. 📊 Check Azure consumption if costs are a concern

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Create virtual environment
        run: uv venv .venv
      
      - name: Install dependencies
        run: |
          source .venv/bin/activate
          uv pip install -r requirements.txt
      
      - name: Setup environment
        run: |
          echo "AZURE_OPENAI_ENDPOINT=${{ secrets.AZURE_OPENAI_ENDPOINT }}" >> .env
          echo "AZURE_OPENAI_API_KEY=${{ secrets.AZURE_OPENAI_API_KEY }}" >> .env
          echo "AZURE_OPENAI_DEPLOYMENT=${{ secrets.AZURE_OPENAI_DEPLOYMENT }}" >> .env
          echo "AZURE_OPENAI_API_VERSION=2023-05-15" >> .env
      
      - name: Run quick tests
        run: |
          source .venv/bin/activate
          python integration_tests/run_all_tests.py --quick
```

---

## Maintenance

### Keeping Tests Updated

1. **Update dependencies regularly**:
   ```bash
   uv pip list --outdated
   uv pip install --upgrade -r requirements.txt
   ```

2. **Update API versions** when Azure releases new versions

3. **Review test configs** if system architecture changes

4. **Check LangChain/LangGraph compatibility** before major updates

---

## Support

### If Tests Fail

1. **Check the review document**: `temp_docs/INTEGRATION_TESTS_REVIEW.md`
2. **Run verification**: `python verify_test_setup.py`
3. **Check individual test**: Run failing test separately
4. **Review error logs**: Tests print detailed error traces
5. **Check Azure portal**: Verify deployment and quota

### For Additional Help

- Review test source code for detailed logic
- Check LangChain documentation for API changes
- Verify Azure OpenAI deployment status
- Test Azure connection separately

---

## Summary Checklist

Before running tests, ensure:

- [ ] Virtual environment created (`.venv/`)
- [ ] Dependencies installed (`requirements.txt`)
- [ ] `.env` file configured with Azure credentials
- [ ] Deno installed (for Test 2)
- [ ] Setup verification passed (`verify_test_setup.py`)
- [ ] Sufficient Azure API quota available
- [ ] Stable internet connection

Then run:
```bash
./run_integration_tests_full.sh
```

---

**Last Updated**: 2025-01-21  
**Test Suite Version**: 1.0  
**Total Tests**: 6  
**Estimated Duration**: 15-25 minutes (full suite)
