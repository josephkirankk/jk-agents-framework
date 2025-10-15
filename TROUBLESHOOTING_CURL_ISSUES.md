# Troubleshooting Guide: JSON Schema Test Data Generator

## 🔍 Issue Analysis from Log: `agentlog_20251008091251.log`

### **Root Cause Summary**

The curl request failed due to **multiple cascading issues**:

1. **Typo in user request**: `"rpgram"` instead of `"program"`
2. **Data generation failure**: Python import error in the MCP wrapper
3. **Validation failure**: No data was generated, so validation couldn't proceed
4. **Wrong dataset retrieved**: Validator found a different dataset (call records)

---

## ❌ **Problems Identified**

### **Problem 1: Typo in Request**
```
Line 191: "Create 20 record with rpgram prg1 and prg2 in retail sector in Plat PLT-01 and PLT-02"
                                  ^^^^^^                                    ^^^^
                                  TYPO                                      TYPO
```

**Impact**: The requirement parser may misinterpret the request.

**Fix**: Use correct spelling:
```
"Create 20 records with program prg1 and prg2 in retail sector for plants PLT-01 and PLT-02"
```

---

### **Problem 2: Data Generation Failed**

**Log Evidence** (Lines 1866-1887):
```
There was a repeated error in the Python code due to the order of imports for `timedelta`.
```

**Impact**: No dataset was created, causing downstream failures.

**Root Cause**: The MCP Python wrapper had issues executing the data generation code.

**Fix Options**:

#### Option A: Simplify the Request (Recommended)
Don't embed the entire schema in the curl request. Let the system load it from the config:

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="Generate 20 ProgramMetrics test records:
- Programs: prg1 and prg2
- Sector: retail
- Plants: PLT-01 and PLT-02"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'thread_id="test-001"'
```

#### Option B: Use Python SDK Instead
```python
import asyncio
import json
from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan

async def generate_data():
    config_path = "config/json_schema_test_data_generator.yaml"
    app_config = load_app_config(config_path)
    
    query = """
    Generate 20 ProgramMetrics test records with:
    - Programs: prg1 and prg2 (mix of both)
    - Sector: retail
    - Plants: PLT-01 and PLT-02 (mix of both)
    """
    
    thread_id = "test-001"
    default_model = app_config.models.get('default')
    
    supervisor = build_supervisor_compiled(
        app_config.supervisor,
        app_config.agents,
        default_model,
        app_config.business_context or "",
        original_user_question=query,
        config_path=config_path,
        thread_id=thread_id,
    )
    
    agents_map, _ = await build_agents_map(
        app_config,
        user_input=query,
        config_path=config_path
    )
    
    result = await execute_plan(
        supervisor_compiled=supervisor,
        agents_map=agents_map,
        user_input=query,
        thread_id=thread_id,
        default_model_for_verifier=default_model
    )
    
    print(result.get("final_result", ""))

asyncio.run(generate_data())
```

---

### **Problem 3: Validation Failed - No Data Found**

**Log Evidence** (Lines 2590-2606):
```
The dataset retrieved under reference_id ref_3fb274ea8f8d contains call records, 
not the 20 ProgramMetrics records generated for your schema.

Error: "name 'data' is not defined"
```

**Impact**: Validation step couldn't complete.

**Root Cause**: Data generation failed in step 3, so step 4 had nothing to validate.

**Fix**: Ensure data generation succeeds first (see Problem 2 fixes).

---

## ✅ **Corrected Curl Requests**

### **Option 1: Simplified (Recommended)**

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="Generate 20 ProgramMetrics test records with the following requirements:
- Programs: prg1 and prg2 (mix of both)
- Sector: retail
- Plants: PLT-01 and PLT-02 (mix of both)
- All records must be schema-compliant"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-simple-001"'
```

**Advantages**:
- ✅ Cleaner, more readable
- ✅ Avoids schema embedding issues
- ✅ Relies on configuration file
- ✅ Better error handling

---

### **Option 2: Detailed Requirements**

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="Generate 20 test records for ProgramMetrics_Simple schema.

Requirements:
- Record count: 20
- Program names: Use prg1 and prg2 (distribute evenly, 10 each)
- Sector: retail (all records)
- Plant codes: Use PLT-01 and PLT-02 (distribute evenly, 10 each)
- Ensure all required fields are present: program_name, record_count, window
- Generate realistic values for optional fields
- Validate all records against the schema"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-detailed-001"'
```

---

### **Option 3: Minimal (Fixed Typos)**

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="Create 20 records with program prg1 and prg2 in retail sector for plants PLT-01 and PLT-02"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="test-minimal-001"'
```

**Changes from original**:
- ✅ `"rpgram"` → `"program"`
- ✅ `"Plat"` → `"plants"`
- ✅ `"20 record"` → `"20 records"`
- ✅ New thread_id to avoid conflicts

---

## 🧪 **Testing the Fix**

### **Step 1: Start the API**

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
python api.py --config config/json_schema_test_data_generator.yaml
```

### **Step 2: Run the Test Script**

```bash
chmod +x test_curl_request.sh
./test_curl_request.sh
```

### **Step 3: Check the Logs**

```bash
# View the latest log
ls -lt agentlogs/ | head -5
cat agentlogs/agentlog_<timestamp>.log
```

### **Step 4: Verify Generated Data**

```bash
# Check if data was stored
ls -lt data/ | head -5

# Or check via API
curl http://localhost:8000/datasets
```

---

## 🔧 **Common Issues and Solutions**

### **Issue: "API is not running"**

**Solution**:
```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill existing process if needed
lsof -ti:8000 | xargs kill -9

# Start API
python api.py --config config/json_schema_test_data_generator.yaml
```

---

### **Issue: "ModuleNotFoundError: No module named 'app'"**

**Solution**:
```bash
# Ensure you're in the project root
cd /Users/A80997271/Documents/projects/jk-agents-core

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### **Issue: "Azure OpenAI API Error"**

**Solution**:
```bash
# Check .env file
cat .env | grep AZURE

# Ensure these are set:
# AZURE_OPENAI_API_KEY=your_key
# AZURE_OPENAI_ENDPOINT=your_endpoint
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

---

### **Issue: "Data generation failed - Python import error"**

**Solution**:

Check the MCP Python wrapper configuration:

```bash
# Verify Python environment
python -c "from datetime import datetime, timedelta; print('OK')"

# Check MCP server status
curl http://localhost:8000/mcp/status
```

If the issue persists, the data_generator agent may need to use a more robust Python code structure. The configuration already has the correct imports, so this is likely a runtime environment issue.

---

### **Issue: "name 'jsonschema' is not defined"** ⚠️ **COMMON**

**Error Message**:
```json
{"error": "Wrapper error: name 'jsonschema' is not defined"}
```

**Root Cause**: Missing `jsonschema` package in Python environment.

**Solution**:

```bash
# Install missing packages
uv pip install jsonschema>=4.20.0 rstr>=3.2.0

# Verify installation
uv pip list | grep -E "jsonschema|rstr"

# Expected output:
# jsonschema                               4.25.1
# jsonschema-specifications                2025.9.1
# rstr                                     3.2.2

# Restart the API
lsof -ti:8000 | xargs kill -9
python api.py --config config/json_schema_test_data_generator.yaml
```

**Why These Packages Are Needed**:
- `jsonschema>=4.20.0`: Validates JSON data against JSON Schema (Draft 2020-12)
- `rstr>=3.2.0`: Generates random strings matching regex patterns

**Note**: These packages are now included in `requirements.txt` and should be installed automatically.

---

## 📊 **Expected Successful Output**

When the request succeeds, you should see:

```json
{
  "status": "success",
  "final_result": "Successfully generated and validated 20 ProgramMetrics records...",
  "dataset_reference_id": "ref_abc123...",
  "validation_summary": {
    "total_records": 20,
    "valid_records": 20,
    "invalid_records": 0,
    "validation_rate": "100%"
  }
}
```

---

## 📝 **Summary of Fixes**

| Issue | Original | Fixed |
|-------|----------|-------|
| Typo 1 | `"rpgram"` | `"program"` |
| Typo 2 | `"Plat"` | `"plants"` |
| Grammar | `"20 record"` | `"20 records"` |
| Request Style | Embedded schema | Natural language |
| Thread ID | `"jk-pep-19"` | `"test-001"` (unique) |

---

## 🎯 **Next Steps**

1. ✅ Use one of the corrected curl requests above
2. ✅ Run the test script: `./test_curl_request.sh`
3. ✅ Check the logs for successful execution
4. ✅ Verify the generated data
5. ✅ If issues persist, use the Python SDK approach instead

---

## 📚 **Additional Resources**

- Configuration: `config/json_schema_test_data_generator.yaml`
- Documentation: `docs/JSON_SCHEMA_TEST_DATA_GENERATOR.md`
- Quick Start: `JSON_SCHEMA_DATA_GENERATOR_README.md`
- Test Suite: `integration_tests/test_07_json_schema_data_generator.py`

---

**Last Updated**: 2025-10-08
**Status**: Ready for testing

