# Fix Summary: Test Data Parser API Format Issue

## 🐛 Issue Identified

The curl command and test script were using incorrect API request format:

**❌ Incorrect (Original):**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "...",           # Wrong field name
    "config_name": "..."      # Wrong field name
  }'
```

**Error Response:**
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "request"],
            "msg": "Field required",
            "input": null
        }
    ]
}
```

## ✅ Root Cause

The jk-agents-core API uses different field names than expected:
- Expected: `input` (not `query`)
- Expected: `config_path` (not `config_name`)

Reference: `api.py` Line 634-636
```python
class QueryRequest(BaseModel):
    input: str = Field(..., description="User question or prompt")
    config_path: Optional[str] = Field(None, description="Optional path to config file")
```

## 🔧 Fixes Applied

### 1. Updated TEST_DATA_PARSER_README.md
Fixed 4 occurrences:
- Line 86-91: Basic example curl command
- Line 114-119: Fuzzy matching example
- Line 132-137: Multiple metrics example
- Line 288-294: Python integration example

### 2. Updated QUICKSTART_TEST_PARSER.md  
Fixed 3 occurrences:
- Line 36-41: Quick start curl command
- Line 233-235: API integration example #1
- Line 300-302: API integration example #2

### 3. Updated test_parser_system.py
Fixed 2 occurrences:
- Line 18-19: Changed CONFIG_NAME to CONFIG_PATH
- Line 47-51: Updated request JSON structure

## ✅ Correct Format

### Option 1: Use `/query/form` endpoint (Recommended)
```bash
curl -X POST "http://localhost:8000/query/form" \
  -F "input=create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100" \
  -F "config_path=config/test_data_parser.yaml"
```

### Option 2: Use `/query` endpoint with JSON
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100",
    "config_path": "config/test_data_parser.yaml"
  }'
```

### Python Integration (Correct):
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={
        "input": "your requirement here",
        "config_path": "config/test_data_parser.yaml"
    }
)

params = response.json()
```

## 📋 Files Modified

1. `/Users/A80997271/Documents/projects/jk-agents-core/TEST_DATA_PARSER_README.md`
2. `/Users/A80997271/Documents/projects/jk-agents-core/QUICKSTART_TEST_PARSER.md`
3. `/Users/A80997271/Documents/projects/jk-agents-core/test_parser_system.py`

## 🧪 Testing

### To test the system:

1. **Start the API server:**
   ```bash
   cd /Users/A80997271/Documents/projects/jk-agents-core
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Test with curl (Form method - recommended):**
   ```bash
   curl -X POST "http://localhost:8000/query/form" \
     -F "input=create 50 records for metric test, program MFG, sector PFNA, plant p1, values 0-100, uom count" \
     -F "config_path=config/test_data_parser.yaml"
   ```

3. **Run the test suite:**
   ```bash
   python test_parser_system.py
   ```

## ⚠️ Important Notes

1. **Config Path**: Always use `config/test_data_parser.yaml` (relative to project root)
2. **Endpoint Choice**: 
   - Use `/query/form` for form data (easier for testing)
   - Use `/query` for JSON (better for programmatic access)
3. **Field Names**: Always use `input` and `config_path`

## 🎯 Next Steps

1. Ensure API server is running
2. Test with the corrected curl command
3. Run the full test suite with `python test_parser_system.py`
4. Verify all 10 test cases pass

## 📚 Related Documentation

- **Full Documentation**: `TEST_DATA_PARSER_README.md`
- **Quick Start Guide**: `QUICKSTART_TEST_PARSER.md`
- **Test Suite**: `test_parser_system.py`
- **Configuration**: `config/test_data_parser.yaml`

##✨ Status

**All documentation and code have been corrected!** The system is ready to use once the API server is running.
