# Test 06: MCP Python Tools - Quick Reference

## Quick Start

```bash
# Navigate to integration tests
cd integration_tests

# Run all MCP Python tests
pytest test_06_mcp_python_tools.py -v -s

# Run single test
pytest test_06_mcp_python_tools.py::TestMCPPythonTools::test_simple_python_execution -v -s
```

## Prerequisites

### 1. Deno Installation
```bash
# Check if Deno is installed
which deno

# Install Deno (if needed)
curl -fsSL https://deno.land/install.sh | sh

# Verify installation
deno --version
```

### 2. Azure OpenAI Credentials
```bash
# Check .env file
cat ../.env | grep AZURE_OPENAI

# Required variables:
# AZURE_OPENAI_ENDPOINT
# AZURE_OPENAI_API_KEY
# AZURE_OPENAI_DEPLOYMENT
# AZURE_OPENAI_API_VERSION
```

### 3. Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux

# Verify packages
python -c "import chromadb, litellm; print('✓ Dependencies OK')"
```

## Test Scenarios

### Basic Tests (7 tests)
1. **Simple Python execution** - Basic calculations
2. **List operations** - Create and sum lists
3. **Error handling** - Division operations
4. **Factorial calculation** - Recursive logic
5. **String manipulation** - String reversal
6. **Data structures** - Dictionary operations
7. **Multi-step calculations** - Complex expressions

### Multi-Turn Tests (4 tests)
8. **Calculation workflow** - Build on previous results
9. **Data accumulation** - Accumulate data across turns
10. **Variable persistence** - Variables persist across turns
11. **Complex workflow** - Data transformation pipeline

## Common Commands

### Run Tests by Category
```bash
# Run only basic tests (1-7)
pytest test_06_mcp_python_tools.py -k "not multi_turn" -v

# Run only multi-turn tests (8-11)
pytest test_06_mcp_python_tools.py -k "multi_turn" -v

# Run with detailed output
pytest test_06_mcp_python_tools.py -v -s --tb=long
```

### Debug Mode
```bash
# Run with debug output
pytest test_06_mcp_python_tools.py -v -s --log-cli-level=DEBUG

# Run single test with full traceback
pytest test_06_mcp_python_tools.py::TestMCPPythonTools::test_simple_python_execution -v -s --tb=long
```

## Expected Output

### Success
```
test_06_mcp_python_tools.py::TestMCPPythonTools::test_simple_python_execution PASSED
test_06_mcp_python_tools.py::TestMCPPythonTools::test_python_list_operations PASSED
...
=== 11 passed in 84.32s ===
```

### Skip (when Deno not installed)
```
SKIPPED [11] test_06_mcp_python_tools.py: Deno is not installed or not in PATH
```

## Troubleshooting

### Issue: Tests Skipped
```bash
# Check Deno installation
which deno
# If not found, install Deno

# Verify PATH
echo $PATH | grep .deno
```

### Issue: MCP Server Connection Failed
```bash
# Check Deno can access MCP package
deno info jsr:@pydantic/mcp-run-python

# Test Deno manually
deno run -N -R=node_modules -W=node_modules --node-modules-dir=auto jsr:@pydantic/mcp-run-python stdio
```

### Issue: Azure OpenAI Errors
```bash
# Verify credentials
python -c "import os; from dotenv import load_dotenv; load_dotenv('../.env'); print(os.getenv('AZURE_OPENAI_ENDPOINT'))"

# Check API connectivity
curl -H "api-key: $AZURE_OPENAI_API_KEY" "$AZURE_OPENAI_ENDPOINT/openai/deployments?api-version=2023-05-15"
```

### Issue: ChromaDB Errors
```bash
# Clear test data
rm -rf test_checkpoints/*
rm -rf ../youtube_memory/*

# Reinstall ChromaDB
uv pip install --upgrade chromadb
```

## Performance Benchmarks

| Test | Duration | LLM Calls | MCP Calls |
|------|----------|-----------|-----------|
| Simple execution | ~6s | 2 | 1 |
| List operations | ~6s | 2 | 1 |
| Error handling | ~6s | 2 | 1 |
| Factorial | ~6s | 2 | 1 |
| String manipulation | ~6s | 2 | 1 |
| Data structure | ~6s | 2 | 1 |
| Multi-step calc | ~6s | 2 | 1 |
| Multi-turn workflow | ~12s | 4-6 | 3 |
| Data accumulation | ~12s | 4-6 | 3 |
| Variable persistence | ~12s | 4-6 | 3 |
| Complex workflow | ~12s | 4-6 | 3 |
| **Total** | **~85s** | **~30** | **~15** |

## Configuration Files

### Primary Config
```yaml
# config/python_exec_agent_working.yaml
agents:
  - name: "python_exec_agent"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args:
          - "run"
          - "-N"
          - "-R=node_modules"
          - "-W=node_modules"
          - "--node-modules-dir=auto"
          - "jsr:@pydantic/mcp-run-python"
          - "stdio"
```

### Alternative Configs
- `python_exec_agent_working_google.yaml` - Google Gemini
- `python_exec_agent_working_litellm.yaml` - LiteLLM proxy

## Test Markers

```bash
# Run by marker
pytest -m integration  # All integration tests
pytest -m azure        # Tests requiring Azure
pytest -m "not slow"   # Skip slow tests
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run MCP Python Tests
  env:
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
  run: |
    # Install Deno
    curl -fsSL https://deno.land/install.sh | sh
    export PATH="$HOME/.deno/bin:$PATH"
    
    # Run tests
    cd integration_tests
    pytest test_06_mcp_python_tools.py -v
```

## Key Files

- **Test File:** `integration_tests/test_06_mcp_python_tools.py`
- **Config:** `config/python_exec_agent_working.yaml`
- **Fixtures:** `integration_tests/conftest.py`
- **Utilities:** `integration_tests/test_utils.py`
- **Helpers:** `integration_tests/helpers/utils.py`

## Success Criteria

✅ All 11 tests pass  
✅ No errors or failures  
✅ Total duration < 120 seconds  
✅ Tool calls successful  
✅ Memory persistence working  

---

**Last Updated:** October 14, 2025  
**Status:** ✅ Production Ready
