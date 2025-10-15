#!/bin/bash
# Quick Test Command for Database Fix

echo "======================================"
echo "  Testing Database Path Fix"
echo "======================================"
echo ""

# Ensure server is running
echo "Make sure API server is running:"
echo "  uvicorn api:app --host 0.0.0.0 --port 8000"
echo ""
read -p "Press Enter when server is ready..."

echo ""
echo "Sending test request..."
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="create a test data with json schema : student name : name student id : id student class : class - 1 to 10 subject : maths, physics and chemistry marks : 1 to 100 exam quarter : Q1 to Q4 exam year : YYYY format

request : create 100 students records for 2024. make it such that every quarter the marks are improving for around 90% students. keep it realistic"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-test-db-fix-001"'

echo ""
echo ""
echo "======================================"
echo "  Checking Results"
echo "======================================"
echo ""

# Check if database exists
if [ -f "./data/schema_test_data.db" ]; then
    echo "✅ Database created at correct path: ./data/schema_test_data.db"
    
    # Show database info
    db_size=$(du -h ./data/schema_test_data.db | cut -f1)
    echo "   Size: $db_size"
    
    # Count records
    record_count=$(sqlite3 ./data/schema_test_data.db "SELECT COUNT(*) FROM large_tool_data;" 2>/dev/null)
    echo "   Datasets stored: $record_count"
    
    # Show latest reference ID
    latest_ref=$(sqlite3 ./data/schema_test_data.db "SELECT reference_id FROM large_tool_data ORDER BY created_at DESC LIMIT 1;" 2>/dev/null)
    if [ -n "$latest_ref" ]; then
        echo "   Latest reference: $latest_ref"
    fi
else
    echo "⚠️  Database not found at ./data/schema_test_data.db"
    echo "   Check API logs for errors"
fi

echo ""
echo "✅ Test complete!"
echo ""
echo "Expected in response:"
echo "  - Validation statistics (e.g., 'Valid: 100, Invalid: 0')"
echo "  - NO error about 'dataset could not be loaded'"
echo "  - Reference ID (e.g., ref_XXXXXXXXXXXX)"
echo ""
