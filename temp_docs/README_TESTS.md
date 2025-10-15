# How to Run Integration Tests

## Quick Start

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run comprehensive integration tests
python temp_tests/test_schema_creator_v2_integration.py

# 3. Verify database contents
python temp_tests/verify_database.py
```

## What Gets Tested

### Test 1: Plain English → JSON Schema → Test Data
- ✅ Schema creation from plain English
- ✅ 30 product records generated
- ✅ Data stored in database
- ✅ Field coverage verified

### Test 2: Existing Schema → Test Data
- ✅ Schema analysis
- ✅ 30 employee records generated  
- ✅ 100% validation success
- ✅ All constraints respected

## Expected Output

```
================================================================================
  JSON SCHEMA CREATOR V2 - COMPREHENSIVE INTEGRATION TEST
================================================================================

✅ Database Health: PASS
✅ Plain English Workflow: SUCCESS
✅ Existing Schema Workflow: SUCCESS

📊 Test Results:
  Test 1 Data: 30 records (expected: 30)
  Test 2 Validation: 100.00% success rate

================================================================================
  🎉 INTEGRATION TESTS PASSED
================================================================================
```

## Verify Database

```bash
python temp_tests/verify_database.py
```

Shows:
- Database file info
- Table structure
- All stored datasets
- Storage statistics
- Sample data

## Troubleshooting

If tests fail:
1. Check `.env` has API keys
2. Ensure `data/` directory exists
3. Verify config: `python -c "import yaml; yaml.safe_load(open('config/json_schema_test_data_generator_v2.yaml'))"`
4. Review logs in `agentlogs/`

## Documentation

- **Full Guide**: `temp_docs/INTEGRATION_TEST_GUIDE.md`
- **Quick Start**: `temp_docs/SCHEMA_CREATOR_QUICK_START.md`
- **Status**: `temp_docs/FINAL_IMPLEMENTATION_STATUS.md`
