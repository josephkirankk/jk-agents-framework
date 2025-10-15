#!/bin/bash
# Verification script for validator agent fix

echo "=================================="
echo "Validator Agent Fix Verification"
echo "=================================="
echo ""

# Check if configs were updated
echo "1. Checking config files for fix patterns..."
if grep -q "ABSOLUTELY FORBIDDEN" config/json_schema_test_data_generator.yaml; then
    echo "✅ json_schema_test_data_generator.yaml updated"
else
    echo "❌ json_schema_test_data_generator.yaml NOT updated"
fi

if grep -q "ABSOLUTELY FORBIDDEN" config/json_schema_test_data_generator_v2.yaml; then
    echo "✅ json_schema_test_data_generator_v2.yaml updated"
else
    echo "❌ json_schema_test_data_generator_v2.yaml NOT updated"
fi

echo ""
echo "2. Checking database exists and has data..."
if [ -f "data/schema_test_data.db" ]; then
    COUNT=$(sqlite3 data/schema_test_data.db "SELECT COUNT(*) FROM large_tool_data;" 2>/dev/null)
    echo "✅ Database exists with $COUNT datasets"
    
    # Show most recent dataset
    echo ""
    echo "Most recent dataset:"
    sqlite3 data/schema_test_data.db "SELECT reference_id, tool_name, size_bytes, created_at FROM large_tool_data ORDER BY created_at DESC LIMIT 1;" 2>/dev/null
else
    echo "❌ Database not found"
fi

echo ""
echo "3. Test data retrieval directly..."
python3 -c "
import os
os.environ['LARGE_DATA_DB_PATH'] = './data/schema_test_data.db'
from app.memory.large_data_storage import LargeDataStorage
storage = LargeDataStorage()
data = storage.retrieve_large_data('ref_d39c163df3ff')
if data:
    print(f'✅ Retrieved {len(data) if isinstance(data, list) else \"unknown\"} items')
else:
    print('❌ Failed to retrieve data')
"

echo ""
echo "=================================="
echo "Fix verification complete!"
echo ""
echo "To test the full workflow, run:"
echo "  uvicorn api:app --host 0.0.0.0 --port 8000"
echo ""
echo "Then use the curl command from the documentation."
echo "=================================="
