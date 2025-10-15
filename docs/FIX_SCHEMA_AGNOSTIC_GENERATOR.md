# Fix for Schema-Agnostic Test Data Generator

## Problem Summary

The test data generator failed to generate 900 records as requested. Instead, it generated only 1 record.

### Root Cause
**Agents are NOT following instructions to use the `run_python_code` tool.**

### Evidence from Log Analysis

1. **Schema Analyzer (s1)**:
   - Expected: Call `run_python_code` with Python code
   - Actual: Returned markdown table with text description
   - Impact: No structured JSON output for next step

2. **Requirement Parser (s2)**:
   - Expected: Call `run_python_code` with Python code
   - Actual: Returned markdown table with text description
   - Impact: No structured JSON output for next step

3. **Data Generator (s3)**:
   - Expected: Generate 900 records (100 students × 3 subjects × 3 years)
   - Actual: Generated 1 record (a single dict)
   - Reason: Couldn't parse text responses from s1 and s2
   - Tool calls:
     - Attempt 1: Tried to use `faker` library (not installed) - FAILED
     - Attempt 2: Generated 1 record, stored as `ref_2b9dc591de9b`

4. **Database Verification**:
   - Database: `./data/large_data_storage.db` (3.1 MB)
   - Reference ID: `ref_2b9dc591de9b`
   - Stored data: Single dict (1 record), not array of 900
   - Size: 154 bytes
   - Metadata claims: "record_count": 7 (INCORRECT - actually 1)

### Actual Stored Data
```json
{
  "student_name": "Sneha Gupta",
  "student_id": "STU0100",
  "student_class": 5,
  "subject": "Chemistry",
  "marks": 78,
  "exam_quarter": "Q4",
  "exam_year": 2025
}
```

## Fixes Required

### Fix 1: Make Agent Prompts Absolutely Explicit (CRITICAL)

The current prompts say "IMMEDIATELY call run_python_code" but agents ignore this.

**Solution**: Update prompts to be even more explicit with:
1. Stronger imperative language
2. Clear examples of what NOT to do
3. Explicit failure conditions
4. Tool-only mode enforcement

### Fix 2: Add Output Format Validation (HIGH)

**Problem**: Agents return text when JSON is expected

**Solution**: Add validation that checks:
- Schema analyzer returns valid JSON with expected structure
- Requirement parser returns valid JSON with record_count
- Data generator returns array of records

### Fix 3: Fix Data Generation Logic (CRITICAL)

**Problem**: Agent generated 1 record instead of 900

**Solution**: Ensure the data generator:
1. Properly parses requirements (even from text)
2. Generates correct number of records
3. Creates proper structure (100 students × 3 subjects × 3 years)
4. Returns an array, not a single dict

### Fix 4: Add Record Count Verification (HIGH)

**Problem**: System didn't detect that only 1 record was generated

**Solution**: Add checks that verify:
- Generated record count matches requirement
- Validator reports if count is wrong
- System fails if count mismatch is detected

## Implementation Plan

### Step 1: Update Schema Analyzer Prompt

Add to the beginning of the prompt:
```
YOU MUST USE THE run_python_code TOOL. DO NOT WRITE TEXT RESPONSES.

WRONG (DO NOT DO THIS):
- Writing markdown tables
- Providing text descriptions
- Manual analysis

RIGHT (DO THIS):
- Call run_python_code tool
- Execute Python code
- Return JSON output from the tool
```

### Step 2: Update Requirement Parser Prompt

Same approach - make it crystal clear that text responses are not acceptable.

### Step 3: Update Data Generator Prompt

Add explicit handling for text inputs:
```python
# If previous steps returned text instead of JSON, parse it
if isinstance(schema_metadata, str) and not schema_metadata.strip().startswith('{'):
    # Extract information from text
    # Look for field names, types, enums, etc.
    pass
```

### Step 4: Add Validation Layer

Create a validation function that checks:
- s1 output is valid JSON
- s2 output has record_count field
- s3 output is an array with correct length

### Step 5: Test End-to-End

Run the complete workflow and verify:
- 900 records are generated
- All records are valid
- Database contains all 900 records
- Validation passes

## Testing Commands

### 1. Check Database
```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('./data/large_data_storage.db')
cursor = conn.cursor()
cursor.execute('SELECT reference_id, metadata FROM large_tool_data ORDER BY created_at DESC LIMIT 1')
ref_id, metadata = cursor.fetchone()
meta = json.loads(metadata)
print(f'Latest: {ref_id}, Count: {meta.get(\"record_count\")}')
conn.close()
"
```

### 2. Verify Record Count
```bash
python tests/test_schema_agnostic_fix.py
```

### 3. Check Data Structure
```bash
python -c "
import sqlite3, json
conn = sqlite3.connect('./data/large_data_storage.db')
cursor = conn.cursor()
cursor.execute('SELECT data_blob FROM large_tool_data WHERE reference_id = ?', ('ref_XXXXX',))
data = json.loads(cursor.fetchone()[0])
print(f'Type: {type(data)}, Length: {len(data) if isinstance(data, list) else \"N/A\"}')
conn.close()
"
```

## Success Criteria

✅ Schema analyzer uses `run_python_code` tool
✅ Requirement parser uses `run_python_code` tool
✅ Data generator creates exactly 900 records
✅ Database contains 900 records
✅ All records are valid per schema
✅ 100 unique students
✅ Each student has 9 records (3 subjects × 3 years)
✅ All records have student_class = 5
✅ All records have exam_year in [2023, 2024, 2025]
✅ All records have subject in ['Maths', 'Physics', 'Chemistry']

## Next Steps

1. Update agent prompts (schema_analyzer, requirement_parser, data_generator)
2. Add output validation
3. Test with the same schema and requirements
4. Verify 900 records are generated and stored
5. Run comprehensive validation tests
6. Document the fix

