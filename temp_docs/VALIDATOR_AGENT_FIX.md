# Schema Validator Agent Fix - Data Loading Issue

## Problem Identified

The schema validator agent was **trying to load data from non-existent file paths** instead of using the already-injected `data` variable.

### Error Encountered
```
FileNotFoundError: [Errno 2] No such file or directory: '/mnt/data/ref_d39c163df3ff.json'
```

### Root Cause Analysis

1. **Data retrieval was working perfectly**: 
   - The `mcp_python_wrapper` successfully retrieved the dataset from the database
   - The data was properly injected into the `data` variable
   - Logs showed: "✅ Successfully retrieved dataset ref_d39c163df3ff" (1200 items)

2. **The LLM-generated code was incorrect**:
   - Despite clear instructions, the validator agent generated Python code that tried to load data from file paths like `/mnt/data/ref_xxx.json`
   - This is a common LLM hallucination - it assumes data is stored in files

3. **Prompt was not explicit enough**:
   - The warnings about not loading from files were buried in the middle of the prompt
   - The LLM didn't understand that the `data` variable was already populated

## Solution Applied

### Changes Made to Both Config Files
- `config/json_schema_test_data_generator.yaml`
- `config/json_schema_test_data_generator_v2.yaml`

### 1. Added Critical Warning Header

Added a prominent warning section at the very top of the validator agent's prompt:

```yaml
⚠️ CRITICAL: YOU MUST USE THE run_python_code TOOL. TEXT RESPONSES ARE FORBIDDEN. ⚠️

YOU ARE A TOOL-ONLY AGENT. YOUR ONLY JOB IS TO CALL THE run_python_code TOOL.

❌ ABSOLUTELY FORBIDDEN (DO NOT DO THESE):
- DO NOT try to load data from /mnt/data/ paths
- DO NOT try to load data from /tmp/ paths  
- DO NOT try to open any files (open(), with open(), etc.)
- DO NOT call retrieve_large_dataset tool
- DO NOT import functions module
- The data is ALREADY in the 'data' variable - DO NOT try to load it!

✅ REQUIRED ACTION (DO THIS):
1. IMMEDIATELY call run_python_code tool with dataset_reference_id parameter
2. The 'data' variable will be automatically populated with the full dataset
3. Use the 'data' variable directly in your validation code
4. Return ONLY the tool's output
```

### 2. Strengthened Example Code Comments

Updated the CORRECT WAY example to emphasize data is pre-loaded:

```python
# ✅ CORRECT: The 'data' variable is ALREADY POPULATED with the full dataset!
# The data is automatically loaded when you use dataset_reference_id parameter.
# DO NOT try to load, import, open, or retrieve the data yourself!
# Just use 'data' directly - it's already there!
```

### 3. Expanded WRONG WAYS Section

Added explicit examples of the exact error pattern that occurred:

```python
# ❌ WRONG: Do not try to load from /mnt/data/ paths
with open('/mnt/data/ref_xxx.json') as f:  # This will FAIL! File doesn't exist!
    data = json.load(f)

# ❌ WRONG: Do not try to load from /tmp/ paths
with open('/tmp/data.json') as f:  # This will FAIL!
    data = json.load(f)

# ❌ WRONG: Do not try to load from relative paths
with open('ref_xxx.json') as f:  # This will FAIL!
    data = json.load(f)
```

## Technical Details

### How Data Loading Works

1. **MCP Server Subprocess**:
   - Each agent has its own MCP server subprocess
   - Environment variables (LARGE_DATA_DB_PATH) are passed from YAML config
   - Storage initialized with correct database path

2. **Data Storage** (data_generator agent):
   ```
   Python code generates data → 
   MCP wrapper detects large dataset → 
   Stores in ./data/schema_test_data.db → 
   Returns reference ID (ref_xxx)
   ```

3. **Data Retrieval** (schema_validator agent):
   ```
   run_python_code(dataset_reference_id="ref_xxx") → 
   MCP wrapper retrieves from ./data/schema_test_data.db → 
   Injects into 'data' variable → 
   Python code executes with pre-loaded data
   ```

### Verification from Logs

```
2025-10-12 20:31:42 - Dataset stored with reference ID: ref_d39c163df3ff
2025-10-12 20:31:52 - 🔍 Retrieving dataset ref_d39c163df3ff for Python execution...
2025-10-12 20:31:52 - ✅ Successfully retrieved dataset ref_d39c163df3ff
2025-10-12 20:31:52 - ✅ Injected retrieved dataset into 'data' variable
```

The data was successfully retrieved and injected, but the LLM's generated code ignored it and tried to load from files.

## Files Modified

1. **`config/json_schema_test_data_generator.yaml`**
   - Updated schema_validator agent prompt (lines 1134-1246)
   - Added critical warnings at top
   - Strengthened examples

2. **`config/json_schema_test_data_generator_v2.yaml`**
   - Updated schema_validator agent prompt (lines 1375-1520)
   - Same changes as above

3. **`app/mcp_python_wrapper.py`**
   - Added environment variable logging on startup
   - Added database path logging during retrieval
   - These help debug future issues

4. **`temp_docs/DATABASE_CONFIGURATION_FIX.md`**
   - Previous fix documentation (already completed)

## Testing Instructions

### Test 1: Quick Validation Test

```bash
# Start the API server
uvicorn api:app --host 0.0.0.0 --port 8000

# Run the same request that failed before
curl --location 'http://localhost:8000/query/form' \
--form 'input="create a test data with json schema : student name : name student id : id student class : class - 1 to 10 subject : maths, physics and chemistry marks : 1 to 100 exam quarter : Q1 to Q4 exam year : YYYY format

request : create 100 students records for 2024. make it such that every quarter the marks are improving for around 90% students. keep it realistic"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-validation-fix"'
```

Expected result: Validation should complete successfully now!

### Test 2: Check Logs

```bash
# Check MCP server logs for proper data loading
tail -f agentlogs/mcp_server_logs/python_wrapper.log | grep -A5 "Retrieving dataset\|ALREADY POPULATED"
```

Should see successful retrieval and no file loading attempts.

### Test 3: Verify Database Consistency

```bash
# Confirm data is in the correct database
sqlite3 data/schema_test_data.db "SELECT COUNT(*) FROM large_tool_data;"
```

## Expected Behavior After Fix

1. **Data Generator Agent (s3)**:
   - Generates data
   - Stores in `./data/schema_test_data.db`
   - Returns reference ID

2. **Schema Validator Agent (s4)**:
   - Receives reference ID
   - Calls `run_python_code(dataset_reference_id="ref_xxx")`
   - MCP wrapper loads data into `data` variable
   - Validation code uses `data` variable directly
   - **Does NOT try to load from files**
   - Returns validation report

## Success Criteria

✅ Validator agent does not try to load from `/mnt/data/` or `/tmp/data/`
✅ Validator uses the pre-loaded `data` variable
✅ Validation completes successfully
✅ Returns proper validation report with statistics
✅ No FileNotFoundError exceptions

## Related Issues

- Database configuration mismatch (FIXED in DATABASE_CONFIGURATION_FIX.md)
- This issue was purely about LLM prompt engineering

## Lessons Learned

1. **Put critical instructions at the TOP** of prompts, not buried in the middle
2. **Use strong, explicit warnings** (⚠️ symbols, CAPITAL LETTERS, repeated prohibitions)
3. **Show exact anti-patterns** that the LLM should avoid
4. **Test with real data** - logs showed retrieval worked, problem was in code generation
5. **LLMs hallucinate file paths** - need to explicitly forbid common patterns like /mnt/data/, /tmp/

## Next Steps

1. ✅ Update config files (DONE)
2. ⏭️ Run test request to verify fix
3. ⏭️ Monitor logs to confirm no file loading attempts
4. ⏭️ Consider adding runtime validation to detect and reject code with file loading
