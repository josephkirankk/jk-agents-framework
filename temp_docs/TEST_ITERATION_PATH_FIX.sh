#!/bin/bash
# Test script for iteration path fix
# Usage: ./TEST_ITERATION_PATH_FIX.sh

echo "=== Testing Iteration Path Fix ==="
echo "Date: $(date)"
echo ""

# Test 1: Iteration path query (should use wit_get_work_items_for_iteration)
echo "Test 1: Iteration Path Query"
echo "Expected: Should use wit_get_work_items_for_iteration() tool"
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="give workitem stats for iteration path Global_Data_Project\\\\SE\\\\SE-R360\\\\R360-PI8"' \
--form 'config_path="config/ado_working_v2.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-iteration-test-001"'

echo ""
echo "---"
echo ""

# Test 2: Area path query (should use search_workitem with areaPath)
echo "Test 2: Area Path Query"
echo "Expected: Should use search_workitem() with areaPath parameter"
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="give workitem stats for area path Global_Data_Project\\\\JBP\\\\JBP Retail 360 MVP 1.0"' \
--form 'config_path="config/ado_working_v2.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-area-test-001"'

echo ""
echo "---"
echo ""

# Test 3: Sprint query (should recognize as iteration path)
echo "Test 3: Sprint Query"
echo "Expected: Should recognize 'sprint' keyword and use wit_get_work_items_for_iteration()"
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="show me work items in sprint R360-PI8"' \
--form 'config_path="config/ado_working_v2.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-sprint-test-001"'

echo ""
echo "=== Test Complete ==="
