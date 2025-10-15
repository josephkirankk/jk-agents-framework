#!/bin/bash

# Test Token Optimization - Compare Original vs Optimized Configs
# Usage: ./test_token_optimization.sh

echo "========================================="
echo "Token Optimization Comparison Test"
echo "========================================="
echo ""

TEST_QUERY="create 5 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 10 to 100, uom should be count. values in metric should have 5% negative from -10 to 0"

echo "1. Testing ORIGINAL config (test_data_parser_simple.yaml)..."
echo "------------------------------------------------------"
RESPONSE1=$(curl -s --location 'http://localhost:8000/query/form' \
  --form "input=\"${TEST_QUERY}\"" \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="compare-orig"')

echo "$RESPONSE1" | tail -30
echo ""
echo "Check logs for token count (grep for 'Token' in terminal output)"
echo ""

sleep 2

echo "2. Testing OPTIMIZED config (test_data_parser_optimized_v2.yaml)..."
echo "------------------------------------------------------"
RESPONSE2=$(curl -s --location 'http://localhost:8000/query/form' \
  --form "input=\"${TEST_QUERY}\"" \
  --form 'config_path="config/test_data_parser_optimized_v2.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="compare-opt"')

echo "$RESPONSE2" | tail -30
echo ""
echo "Check logs for token count (grep for 'Token' in terminal output)"
echo ""

echo "========================================="
echo "Comparison Summary"
echo "========================================="
echo ""
echo "Original output length: $(echo "$RESPONSE1" | wc -c) characters"
echo "Optimized output length: $(echo "$RESPONSE2" | wc -c) characters"
echo ""
echo "Original response (formatted):"
echo "$RESPONSE1" | python3 -m json.tool 2>/dev/null | head -20
echo ""
echo "Optimized response (compact):"
echo "$RESPONSE2" | head -5
echo ""
echo "NOTE: Check server logs for actual token counts"
echo "Expected savings: 60-70% for small datasets, 90%+ for large datasets"
