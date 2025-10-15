# Integration Test Guide for Schema Creator V2

## Overview

Comprehensive end-to-end integration tests that verify:
- ✅ Both workflows (plain English & existing schema)
- ✅ Database record creation and storage
- ✅ Data validity against JSON Schema
- ✅ Data quality metrics
- ✅ Field coverage and statistics

---

## Test Files

### 1. **test_schema_creator_v2_integration.py**
Comprehensive E2E test covering both workflows with database verification.

**Features:**
- Tests plain English → JSON Schema → data workflow
- Tests existing schema → data workflow  
- Verifies database records exist
- Validates data against schemas
- Analyzes data quality metrics
- Extracts reference IDs from results

### 2. **verify_database.py**
Database inspection and verification utility.

**Features:**
- Checks database file and structure
- Lists all stored datasets
- Inspects individual datasets
- Shows storage statistics
- Validates data structure
- Displays sample records

---

## Prerequisites

### 1. Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify dependencies
pip list | grep -E "(jsonschema|pydantic|langchain)"
```

### 2. Database Directory
```bash
# Ensure data directory exists
mkdir -p data

# Check if database already exists
ls -lh data/schema_test_data.db
```

### 3. Configuration
```bash
# Verify config file exists
ls -lh config/json_schema_test_data_generator_v2.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/json_schema_test_data_generator_v2.yaml'))"
```

### 4. Environment Variables
```bash
# Ensure .env file has required keys
grep -E "AZURE_OPENAI|OPENAI_API" .env
```

---

## Running Tests

### Quick Test Validation

Check test syntax before running:

```bash
# Syntax check
python -m py_compile temp_tests/test_schema_creator_v2_integration.py
python -m py_compile temp_tests/verify_database.py

# Import check
python -c "import sys; sys.path.insert(0, '.'); from temp_tests import test_schema_creator_v2_integration"
```

### Run Integration Tests

**Option 1: Full Test Suite**
```bash
# Run comprehensive integration tests
python temp_tests/test_schema_creator_v2_integration.py
```

**Expected Output:**
```
================================================================================
  JSON SCHEMA CREATOR V2 - COMPREHENSIVE INTEGRATION TEST
================================================================================

  Timestamp: 2025-10-12 19:00:00
  Database: ./data/schema_test_data.db
  Config: config/json_schema_test_data_generator_v2.yaml

================================================================================
  PRE-FLIGHT CHECK
================================================================================
...

================================================================================
  TEST 1: Plain English → JSON Schema → Test Data
================================================================================
...

================================================================================
  TEST 2: Existing Schema → Test Data
================================================================================
...

================================================================================
  FINAL TEST SUMMARY
================================================================================

📊 Test Results:

  Database Health: ✅ PASS
  Plain English Workflow: ✅ SUCCESS
  Existing Schema Workflow: ✅ SUCCESS
  
  Test 1 Data:
    - Records: 30 (expected: 30)
    - Fields: 6
    
  Test 2 Validation:
    - Total: 30
    - Valid: 30
    - Invalid: 0
    - Success rate: 100.00%

================================================================================
  🎉 INTEGRATION TESTS PASSED
================================================================================
```

**Option 2: Database Verification Only**
```bash
# Verify database contents without running workflows
python temp_tests/verify_database.py
```

**Expected Output:**
```
================================================================================
  DATABASE VERIFICATION UTILITY
  For: schema_test_data.db
================================================================================

================================================================================
  DATABASE FILE VERIFICATION
================================================================================

✅ Database found: ./data/schema_test_data.db
   Size: 45,678 bytes (44.61 KB, 0.04 MB)
   Modified: 2025-10-12 18:55:23

================================================================================
  DATABASE STRUCTURE
================================================================================

[1] Tables:
   ✅ large_tool_data

[2] large_tool_data schema:
   - reference_id        TEXT            PRIMARY KEY
   - tool_name           TEXT            NOT NULL
   - storage_type        TEXT            NOT NULL
   ...

[3] Indexes:
   ✅ idx_tool_name
   ✅ idx_size_category
   ✅ idx_expires_at

================================================================================
  STORED DATASETS
================================================================================

📊 Total datasets: 2

#    Reference ID       Tool                 Size         Type     Created
────────────────────────────────────────────────────────────────────────────────
1    ref_a1b2c3d4e5f6   data_generator       🗜️ 12,345B   json     2025-10-12...
2    ref_f6e5d4c3b2a1   data_generator       🗜️ 13,456B   json     2025-10-12...

================================================================================
  STORAGE STATISTICS
================================================================================

📊 Overall Statistics:
   Total datasets: 2
   Total storage: 25,801 bytes (0.02 MB)
   Average size: 12,901 bytes (12.60 KB)
   ...
```

---

## Test Scenarios

### Scenario 1: Plain English Input

**Test Input:**
```
Data Structure:

product_id: unique ID format PROD-XXXXXX
product_name: product name 5-50 characters
category: Electronics, Clothing, Food
price: 10.00 to 1000.00
stock: 0 to 500
in_stock: yes or no

Requirements: Generate 30 products with 10 in each category
```

**Verification Steps:**
1. ✅ schema_creator generates valid JSON Schema
2. ✅ requirement_parser extracts "30 records"
3. ✅ data_generator creates 30 records
4. ✅ schema_validator validates all records
5. ✅ Database stores data with reference ID
6. ✅ All records have required fields
7. ✅ Data matches constraints (price range, etc.)

**Expected Results:**
- 30 records total
- 10 in each category (Electronics, Clothing, Food)
- All product_ids match pattern `PROD-XXXXXX`
- All prices between 10.00 and 1000.00
- All stock values between 0 and 500

### Scenario 2: Existing Schema

**Test Input:**
- Complete JSON Schema for EmployeeRecord
- Requirements: "Generate 30 employee records with 10 in each department"

**Verification Steps:**
1. ✅ schema_analyzer extracts schema metadata
2. ✅ requirement_parser extracts "30 records, 10 per department"
3. ✅ data_generator creates 30 records
4. ✅ schema_validator validates against original schema
5. ✅ Database stores data
6. ✅ 100% validation success rate

**Expected Results:**
- 30 records total
- 10 in each department (Engineering, Sales, HR)
- All employee_ids match pattern `EMP-NNNNN`
- All salaries between 30,000 and 200,000
- All records have required fields

---

## Understanding Test Output

### Success Indicators

**✅ Green Checkmarks:**
- Configuration loaded correctly
- Agents built successfully
- Workflow executed without errors
- Database records created
- Data validation passed

**📊 Statistics:**
- Record counts match expectations
- Field coverage is complete
- Validation success rate is 100%

### Warning Indicators

**⚠️ Yellow Warnings:**
- Reference ID not found in result (checks database instead)
- Schema extraction from result incomplete
- Partial test success (some steps passed)

**What to do:**
- Check logs for details
- Verify database has records
- Run database verification utility

### Error Indicators

**❌ Red X Marks:**
- Configuration failed to load
- Agent build errors
- Workflow execution errors
- Database access errors
- Validation failures

**What to do:**
- Check error messages
- Verify environment setup
- Check API keys in .env
- Review agent logs in agentlogs/

---

## Interpreting Results

### Data Quality Metrics

```python
{
  "record_count": 30,
  "expected_count": 30,
  "count_match": True,
  "field_coverage": {
    "total_fields": 6,
    "fields": ["product_id", "product_name", "category", "price", "stock", "in_stock"],
    "field_presence": {
      "product_id": {"count": 30, "percentage": 100.0},
      "product_name": {"count": 30, "percentage": 100.0},
      ...
    }
  }
}
```

**What it means:**
- `record_count`: Actual number of records generated
- `expected_count`: Number requested in requirements
- `count_match`: True if counts match
- `field_coverage`: Shows which fields exist in data
- `field_presence`: Percentage of records with each field

### Validation Results

```python
{
  "total": 30,
  "valid": 30,
  "invalid": 0,
  "success_rate": 100.0,
  "errors": []
}
```

**What it means:**
- `total`: Number of records validated
- `valid`: Records that passed validation
- `invalid`: Records that failed validation
- `success_rate`: Percentage of valid records
- `errors`: List of validation errors (if any)

---

## Troubleshooting

### Issue: "Database not found"

**Symptom:**
```
❌ Database not found: ./data/schema_test_data.db
```

**Solution:**
```bash
# Create data directory
mkdir -p data

# Run a workflow to create database
python temp_tests/test_schema_creator_v2_integration.py
```

### Issue: "No reference ID found"

**Symptom:**
```
⚠️  No reference ID found in result
```

**Solution:**
This is often expected. The test will check the database for the latest dataset:
```bash
# Verify database has records
python temp_tests/verify_database.py
```

### Issue: "Config failed to load"

**Symptom:**
```
❌ Error: Config file not found
```

**Solution:**
```bash
# Verify config path
ls -lh config/json_schema_test_data_generator_v2.yaml

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/json_schema_test_data_generator_v2.yaml'))"
```

### Issue: "Agent build failed"

**Symptom:**
```
❌ Error building agents
```

**Solution:**
```bash
# Check environment variables
source .venv/bin/activate
python -c "import os; print('AZURE_OPENAI_API_KEY:', 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET')"

# Verify imports
python -c "from app.main import load_app_config, build_agents_map"
```

### Issue: "Validation failures"

**Symptom:**
```
Invalid: 5
Success rate: 83.33%
```

**Solution:**
1. Check validation errors in output
2. Verify schema constraints are reasonable
3. Check if data_generator is respecting constraints
4. Review sample invalid records

```bash
# Inspect specific dataset
python -c "
from temp_tests.verify_database import inspect_dataset
inspect_dataset('./data/schema_test_data.db', 'ref_XXXXXXXXXXXX')
"
```

---

## Advanced Usage

### Test Specific Reference ID

```python
from temp_tests.test_schema_creator_v2_integration import (
    retrieve_dataset_by_reference,
    validate_dataset_against_schema,
    analyze_data_quality
)

# Retrieve specific dataset
dataset = retrieve_dataset_by_reference("ref_a1b2c3d4e5f6")

# Analyze quality
quality = analyze_data_quality(dataset['data'], expected_count=30)
print(quality)

# Validate against schema
validation = validate_dataset_against_schema(dataset['data'], my_schema)
print(validation)
```

### Query Database Directly

```python
import sqlite3
import json
import gzip

conn = sqlite3.connect("./data/schema_test_data.db")
cursor = conn.cursor()

# Get latest dataset
cursor.execute("""
    SELECT reference_id, data_blob, compressed
    FROM large_tool_data
    ORDER BY created_at DESC
    LIMIT 1
""")

ref_id, data_blob, compressed = cursor.fetchone()

# Decompress and parse
if compressed:
    data_blob = gzip.decompress(data_blob)

data = json.loads(data_blob.decode('utf-8'))
print(f"Records: {len(data)}")
print(f"First record: {data[0]}")
```

---

## Performance Benchmarks

### Expected Performance

| Workflow | Records | Time | Database Size |
|----------|---------|------|---------------|
| Plain English | 30 | ~30s | ~10-15 KB |
| Existing Schema | 30 | ~25s | ~10-15 KB |
| Plain English | 100 | ~45s | ~30-40 KB |
| Existing Schema | 100 | ~40s | ~30-40 KB |

*Times are approximate and depend on LLM response times*

### Database Growth

- Small datasets (< 50 records): Stored in SQLite with compression
- Medium datasets (50-500 records): Compressed SQLite
- Large datasets (> 500 records): File system storage

---

## Continuous Integration

### CI/CD Pipeline

```yaml
# .github/workflows/test-schema-creator.yml
name: Schema Creator V2 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run integration tests
        env:
          AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}
        run: |
          python temp_tests/test_schema_creator_v2_integration.py
      
      - name: Verify database
        run: |
          python temp_tests/verify_database.py
```

---

## Summary

### Quick Start Commands

```bash
# 1. Setup
source .venv/bin/activate
mkdir -p data

# 2. Run tests
python temp_tests/test_schema_creator_v2_integration.py

# 3. Verify database
python temp_tests/verify_database.py

# 4. Check specific dataset
python -c "from temp_tests.verify_database import inspect_dataset; inspect_dataset('./data/schema_test_data.db', 'ref_XXXXXXXXXXXX')"
```

### Success Criteria

✅ **Tests Pass When:**
- Database file created and accessible
- All workflow steps complete without errors
- Record counts match expectations
- 100% validation success rate
- All required fields present in data
- Data conforms to schema constraints

---

## Support

**Test Files:**
- `temp_tests/test_schema_creator_v2_integration.py`
- `temp_tests/verify_database.py`

**Documentation:**
- `temp_docs/JSON_SCHEMA_CREATOR_V2_README.md`
- `temp_docs/SCHEMA_CREATOR_QUICK_START.md`
- `temp_docs/IMPLEMENTATION_SUMMARY.md`

**Issues:**
1. Check error messages in test output
2. Review logs in `agentlogs/` directory
3. Verify environment setup
4. Run database verification utility
