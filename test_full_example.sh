#!/bin/bash
# Comprehensive test of the fixed configuration

echo "🧪 Testing test_data_parser_simple.yaml"
echo "========================================"
echo ""

# Test 1: Simple query
echo "Test 1: Simple query"
echo "Query: 'create 10 records for metric test'"
echo ""
RESULT=$(curl -s --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric test"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="True"')
echo "$RESULT" | jq -r '.record_count // "ERROR"' | grep -q "10" && echo "✅ PASS: Record count extracted" || echo "❌ FAIL"
echo ""

# Test 2: Complex query with all parameters
echo "Test 2: Complex query"
echo "Query: 'create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100'"
echo ""
RESULT=$(curl -s --location 'http://localhost:8000/query/form' \
  --form 'input="create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="True"')

echo "$RESULT" | jq -r '.record_count // "ERROR"' | grep -q "100" && echo "✅ PASS: Record count = 100" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.program_code // "ERROR"' | grep -q "MFG" && echo "✅ PASS: Program code = MFG" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.sector // "ERROR"' | grep -q "PFNA" && echo "✅ PASS: Sector = PFNA" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.plant_code // "ERROR"' | grep -q "p1" && echo "✅ PASS: Plant code = p1" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.value_range.min // "ERROR"' | grep -q "100" && echo "✅ PASS: Min value = 100" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.value_range.max // "ERROR"' | grep -q "10000" && echo "✅ PASS: Max value = 10000" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.uom // "ERROR"' | grep -q "count" && echo "✅ PASS: UOM = count" || echo "❌ FAIL"
echo "$RESULT" | jq -r '.negative_percentage // "ERROR"' | grep -q "0.1" && echo "✅ PASS: Negative % = 0.1" || echo "❌ FAIL"

echo ""
echo "Full JSON output:"
echo "$RESULT" | jq '.'
echo ""
echo "========================================"
echo "✅ All tests completed"
