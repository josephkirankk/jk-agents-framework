# Manual Test Instructions for Schema-Agnostic Test Data Generator

## Current Status

✅ **Fixes Applied**: All agent prompts have been updated with explicit warnings
✅ **Verification Added**: Record count and type checks added to data generator
✅ **Tests Created**: Integration test script ready

❌ **Not Yet Tested**: The updated configuration needs to be tested with actual execution

## How to Run the Test

### Option 1: Using the Supervisor CLI (Recommended)

1. **Start the supervisor**:
   ```bash
   cd /Users/A80997271/Documents/projects/jk-agents-core
   source .venv/bin/activate
   python -m app.cli
   ```

2. **Select the workflow**:
   - Choose: `json_schema_test_data_generator`

3. **Provide the schema**:
   ```
   schema :
   {
     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "title": "StudentExamRecord",
     "description": "Schema for storing student exam data",
     "type": "object",
     "properties": {
       "student_name": {
         "type": "string",
         "description": "Full name of the student"
       },
       "student_id": {
         "type": "string",
         "description": "Unique identifier for the student"
       },
       "student_class": {
         "type": "integer",
         "description": "Class of the student from 1 to 10",
         "minimum": 1,
         "maximum": 10,
         "default": 1
       },
       "subject": {
         "type": "string",
         "description": "Subject name",
         "enum": ["Maths", "Physics", "Chemistry"],
         "default": "Maths"
       },
       "marks": {
         "type": "integer",
         "description": "Marks scored in the subject (1–100)",
         "minimum": 1,
         "maximum": 100,
         "default": 50
       },
       "exam_quarter": {
         "type": "string",
         "description": "Exam quarter",
         "enum": ["Q1", "Q2", "Q3", "Q4"],
         "default": "Q1"
       },
       "exam_year": {
         "type": "integer",
         "description": "Year of the exam in YYYY format",
         "minimum": 2000,
         "maximum": 2100,
         "default": 2025
       }
     },
     "required": [
       "student_name",
       "student_id",
       "student_class",
       "subject",
       "marks",
       "exam_quarter",
       "exam_year"
     ],
     "additionalProperties": false
   }

   Request : create records for 100 students for class 5 for all the subjects per student for years 2023,2024,2025. ensure it looks real
   ```

4. **Monitor the execution**:
   - Watch for agents calling `run_python_code` tool
   - Check that NO agents return text/markdown responses
   - Look for the reference ID in the output (format: `ref_xxxxxxxxxxxx`)

5. **Verify the result**:
   - The final output should include a reference ID
   - Message should say "Large dataset automatically stored"
   - Record count should be mentioned (900 records)

### Option 2: Check the Log File

If the test was already run, check the latest log file:

```bash
ls -lt agentlogs/ | head -5
cat agentlogs/agentlog_YYYYMMDDHHMMSS.log
```

Look for:
- ✅ Schema analyzer calling `run_python_code` (NOT returning markdown tables)
- ✅ Requirement parser calling `run_python_code` (NOT returning markdown tables)
- ✅ Data generator calling `run_python_code` and generating 900 records
- ✅ Reference ID generated (e.g., `ref_abc123def456`)

### Option 3: Verify Database Directly

Check the database for the latest dataset:

```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('./data/large_data_storage.db')
cursor = conn.cursor()

# Get latest dataset
cursor.execute('SELECT reference_id, metadata, data_blob, compressed, created_at FROM large_tool_data ORDER BY created_at DESC LIMIT 1')
ref_id, metadata_json, data_blob, compressed, created_at = cursor.fetchone()

# Parse metadata
metadata = json.loads(metadata_json)
print(f'Reference ID: {ref_id}')
print(f'Created: {created_at}')
print(f'Metadata: {json.dumps(metadata, indent=2)}')

# Decompress if needed
if compressed:
    import gzip
    data_blob = gzip.decompress(data_blob)

# Parse data
data = json.loads(data_blob)
print(f'Data type: {type(data)}')
print(f'Record count: {len(data) if isinstance(data, list) else \"N/A (not a list)\"}')

if isinstance(data, list) and len(data) > 0:
    print(f'First record: {json.dumps(data[0], indent=2)}')

conn.close()
"
```

**Expected Output**:
```
Reference ID: ref_xxxxxxxxxxxx
Created: 2025-10-12 XX:XX:XX
Metadata: {
  "description": "Auto-stored from Python execution",
  "record_count": 900,
  "data_type": "list",
  ...
}
Data type: <class 'list'>
Record count: 900
First record: {
  "student_name": "...",
  "student_id": "STU0001",
  "student_class": 5,
  "subject": "Maths",
  "marks": 67,
  "exam_quarter": "Q1",
  "exam_year": 2023
}
```

### Option 4: Run Integration Test

After running the generator, verify with the integration test:

```bash
python tests/integration_test_schema_generator.py
```

**Expected Output**:
```
================================================================================
  ✅ ALL TESTS PASSED!
================================================================================

Summary:
  Reference ID: ref_xxxxxxxxxxxx
  Total records: 900
  Unique students: 100
  Records per student: 9
  All constraints satisfied: ✅
```

## Success Criteria

✅ **Schema Analyzer (s1)**:
- Calls `run_python_code` tool
- Returns JSON (not markdown table)
- No text descriptions or manual analysis

✅ **Requirement Parser (s2)**:
- Calls `run_python_code` tool
- Returns JSON with `record_count: 900`
- No text descriptions or manual parsing

✅ **Data Generator (s3)**:
- Calls `run_python_code` tool
- Generates exactly 900 records
- Returns a list (array), not a single dict
- Auto-storage creates reference ID

✅ **Database Storage**:
- Reference ID created (format: `ref_xxxxxxxxxxxx`)
- Metadata shows `record_count: 900`
- Data is stored as a list of 900 dicts
- Each record has all required fields

✅ **Schema Validator (s4)**:
- Validates all 900 records
- Reports 100% success rate
- No validation errors

✅ **Integration Test**:
- All tests pass
- 100 unique students
- 9 records per student (3 subjects × 3 years)
- All constraints satisfied

## Troubleshooting

### If agents still return text responses:

1. Check that the configuration file was saved correctly:
   ```bash
   grep -A 5 "CRITICAL: YOU MUST USE" config/json_schema_test_data_generator.yaml
   ```

2. Verify the prompts have the updated warnings

3. Check the log file to see exact agent responses

### If record count is wrong:

1. Check the requirement parser output - does it calculate 900?
2. Check the data generator code - is it using the correct record_count?
3. Look for errors in the log file

### If database storage fails:

1. Check MCP server initialization
2. Verify database path is correct
3. Check for errors in the log file

## Next Steps After Successful Test

1. ✅ Verify all 900 records are generated
2. ✅ Run integration test to confirm
3. ✅ Document the reference ID
4. ✅ Update documentation with results
5. ✅ Mark the issue as resolved

## Files to Check

- **Configuration**: `config/json_schema_test_data_generator.yaml`
- **Log File**: `agentlogs/agentlog_YYYYMMDDHHMMSS.log`
- **Database**: `./data/large_data_storage.db`
- **Integration Test**: `tests/integration_test_schema_generator.py`
- **Documentation**: `docs/FIXES_APPLIED_SUMMARY.md`

