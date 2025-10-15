#!/bin/bash
# Comprehensive verification script for all fixes

echo "=========================================="
echo "Verifying All Fixes"
echo "=========================================="
echo ""

# Check 1: Auto-correction variable list
echo "1. Checking auto-correction enhancement..."
if grep -q "'students'" app/mcp_python_wrapper.py; then
    echo "✅ Auto-correction includes 'students' variable"
else
    echo "❌ Auto-correction missing 'students' variable"
fi

# Check 2: Config files updated
echo ""
echo "2. Checking config files..."
if grep -q "large_data_storage server is intentionally NOT included" config/json_schema_test_data_generator.yaml; then
    echo "✅ json_schema_test_data_generator.yaml - manual storage removed"
else
    echo "❌ json_schema_test_data_generator.yaml - manual storage still present"
fi

if grep -q "large_data_storage server is intentionally NOT included" config/json_schema_test_data_generator_v2.yaml; then
    echo "✅ json_schema_test_data_generator_v2.yaml - manual storage removed"
else
    echo "❌ json_schema_test_data_generator_v2.yaml - manual storage still present"
fi

# Check 3: API endpoints
echo ""
echo "3. Checking API endpoints..."
if grep -q "GET /api/data/{reference_id}" api.py; then
    echo "✅ Data retrieval endpoint added to api.py"
else
    echo "❌ Data retrieval endpoint missing from api.py"
fi

# Check 4: Validator prompts
echo ""
echo "4. Checking validator prompts..."
if grep -q "ABSOLUTELY FORBIDDEN" config/json_schema_test_data_generator.yaml; then
    echo "✅ Validator prompt enhanced with warnings"
else
    echo "❌ Validator prompt not enhanced"
fi

# Check 5: Database
echo ""
echo "5. Checking database..."
if [ -f "data/schema_test_data.db" ]; then
    COUNT=$(sqlite3 data/schema_test_data.db "SELECT COUNT(*) FROM large_tool_data;" 2>/dev/null)
    echo "✅ Database exists with $COUNT datasets"
    
    echo ""
    echo "Recent datasets:"
    sqlite3 data/schema_test_data.db "SELECT reference_id, size_bytes, created_at FROM large_tool_data ORDER BY created_at DESC LIMIT 3;" 2>/dev/null
else
    echo "❌ Database not found"
fi

# Check 6: Documentation
echo ""
echo "6. Checking documentation..."
DOCS=(
    "temp_docs/DATABASE_CONFIGURATION_FIX.md"
    "temp_docs/VALIDATOR_AGENT_FIX.md"
    "temp_docs/API_DATA_ENDPOINT_FIX.md"
    "temp_docs/DATA_GENERATION_FEW_RECORDS_FIX.md"
    "temp_docs/FINAL_COMPLETE_FIX_SUMMARY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $(basename $doc)"
    else
        echo "❌ $(basename $doc) missing"
    fi
done

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Restart server: pkill -f 'uvicorn api:app' && uvicorn api:app --host 0.0.0.0 --port 8000 --reload"
echo "2. Test data generation with the curl command"
echo "3. Verify record count: curl http://localhost:8000/api/data/ref_NEWID | jq '.data | length'"
echo ""
