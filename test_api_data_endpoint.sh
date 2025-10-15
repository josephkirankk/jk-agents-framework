#!/bin/bash
# Test the /api/data endpoint

echo "=================================="
echo "Testing /api/data Endpoints"
echo "=================================="
echo ""

# Test 1: List all datasets
echo "1. Testing GET /api/data (list all datasets)..."
curl -s http://localhost:8000/api/data | jq '.status, .total, .datasets[0].reference_id' 2>/dev/null || echo "Server not running or endpoint not available"

echo ""
echo ""

# Test 2: Get specific dataset
echo "2. Testing GET /api/data/ref_c9014aef6663..."
curl -s http://localhost:8000/api/data/ref_c9014aef6663 | jq '.status, .reference_id, .metadata.size_bytes' 2>/dev/null || echo "Failed to retrieve data"

echo ""
echo ""

# Test 3: Check if data exists in database
echo "3. Checking database for ref_c9014aef6663..."
sqlite3 data/schema_test_data.db "SELECT reference_id, size_bytes, created_at FROM large_tool_data WHERE reference_id='ref_c9014aef6663';" 2>/dev/null || echo "Database query failed"

echo ""
echo "=================================="
echo "Test complete!"
echo "=================================="
