#!/bin/bash
# Test the two-agent pipeline: parser → generator

echo "🧪 Testing Two-Agent Pipeline"
echo "=============================="
echo ""
echo "Pipeline: requirement_parser → data_generator"
echo ""

# Test 1: Small dataset
echo "Test 1: Generate 10 records for single metric"
echo "----------------------------------------------"
curl -s --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric test"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="False"' \
  --max-time 60 > /tmp/test1.json

RECORDS=$(jq -r 'if type=="object" then (.. | objects | select(has("record_id")) | .record_id) else empty end' /tmp/test1.json 2>/dev/null | wc -l | tr -d ' ')
echo "✅ Records generated: $RECORDS"
echo ""

# Test 2: Multiple metrics
echo "Test 2: Generate 20 records for multiple metrics"
echo "-------------------------------------------------"
curl -s --location 'http://localhost:8000/query/form' \
  --form 'input="create 20 records for metric abcd, xyz, program MFG, sector PFNA"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="False"' \
  --max-time 60 > /tmp/test2.json

echo "Response preview:"
head -30 /tmp/test2.json
echo ""

# Test 3: With negative values
echo "Test 3: Generate records with negative values"
echo "----------------------------------------------"
curl -s --location 'http://localhost:8000/query/form' \
  --form 'input="create 10 records for metric sales, values 100 to 1000, 20% negative from -50 to -10"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="False"' \
  --max-time 60 > /tmp/test3.json

echo "Response preview:"
head -30 /tmp/test3.json
echo ""

echo "=============================="
echo "✅ Tests completed"
echo ""
echo "Full outputs saved to:"
echo "  /tmp/test1.json"
echo "  /tmp/test2.json"
echo "  /tmp/test3.json"
