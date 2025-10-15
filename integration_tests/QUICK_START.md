# Integration Tests - Quick Start

## 1. Setup (One Time)

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Configure credentials in .env
cat > .env << EOF
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1
AZURE_OPENAI_API_VERSION=2023-05-15
EOF
```

## 2. Run Tests

```bash
cd integration_tests

# Run all tests
pytest -v -s

# Run specific test file
pytest test_01_basic_flow.py -v -s

# Run with convenience script
python run_integration_tests.py

# Run quick tests only
python run_integration_tests.py --quick

# Run specific tests
python run_integration_tests.py --test 1 2 4
```

## 3. Test Files

| File | Description | Scenarios | Duration |
|------|-------------|-----------|----------|
| test_01 | Basic agent operations | 9 | 3-5 min |
| test_02 | API endpoints | 9 | 4-6 min |
| test_03 | Job processing | 8 | 5-7 min |
| test_04 | Memory & multi-turn | 10 | 6-10 min |
| test_05 | Error handling | 11 | 5-8 min |

## 4. Common Commands

```bash
# Run by marker
pytest -m azure -v -s          # Azure tests only
pytest -m chromadb -v -s       # Memory tests only
pytest -m "not slow" -v -s     # Skip slow tests

# Run specific scenario
pytest test_01_basic_flow.py::TestBasicFlow::test_simple_query_execution -v -s

# Run with coverage
pytest --cov=../app --cov-report=html -v

# Run in parallel
pytest -n 4 -v
```

## 5. For API Tests

```bash
# Terminal 1: Start server
uvicorn api:app --reload

# Terminal 2: Run tests
cd integration_tests
pytest test_02_api_to_llm_flow.py -v -s
```

## 6. Troubleshooting

**Import Error:**
```bash
cd integration_tests  # Must run from this directory
```

**Credentials Error:**
```bash
# Verify .env file
cat ../.env | grep AZURE_OPENAI

# Test credentials
python -c "from test_utils import check_azure_credentials; print(check_azure_credentials())"
```

**ChromaDB Error:**
```bash
uv pip install chromadb>=1.0.0
```

## 7. Documentation

- **INTEGRATION_TESTS_GUIDE.md** - Complete guide
- **conftest.py** - Available fixtures
- **helpers/** - Helper modules

## 8. Test Output

```
✅ PASS: test_simple_query_execution
Duration: 5.23s

Sub-tests:
  ✅ Agent Creation
  ✅ Query Execution
  ✅ Response Verification
```

---

**Read INTEGRATION_TESTS_GUIDE.md for detailed information**
