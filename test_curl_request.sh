#!/bin/bash

# Test script for JSON Schema Test Data Generator
# This script tests the corrected curl request

echo "=========================================="
echo "JSON Schema Test Data Generator - Test"
echo "=========================================="
echo ""

# Check if API is running
echo "Checking if API is running on port 8000..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ ERROR: API is not running on port 8000"
    echo "Please start the API first:"
    echo "  python api.py --config config/json_schema_test_data_generator.yaml"
    exit 1
fi
echo "✅ API is running"
echo ""

# Test 1: Simplified request (recommended)
echo "=========================================="
echo "Test 1: Simplified Natural Language Request"
echo "=========================================="
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="Generate 20 ProgramMetrics test records with the following requirements:
- Programs: prg1 and prg2 (mix of both)
- Sector: retail
- Plants: PLT-01 and PLT-02 (mix of both)
- All records must be schema-compliant

Use the ProgramMetrics_Simple schema from the configuration."' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-simple-'$(date +%s)'"'

echo ""
echo ""
echo "=========================================="
echo "Test 1 Complete"
echo "=========================================="
echo ""
echo "Press Enter to continue to Test 2..."
read

# Test 2: Detailed request with schema
echo "=========================================="
echo "Test 2: Detailed Request with Embedded Schema"
echo "=========================================="
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="Generate 20 test records for ProgramMetrics_Simple schema.

Requirements:
- Record count: 20
- Program names: Use prg1 and prg2 (distribute evenly, 10 each)
- Sector: retail (all records)
- Plant codes: Use PLT-01 and PLT-02 (distribute evenly, 10 each)
- Ensure all required fields are present: program_name, record_count, window
- Generate realistic values for optional fields
- Validate all records against the schema"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="False"' \
--form 'thread_id="test-detailed-'$(date +%s)'"'

echo ""
echo ""
echo "=========================================="
echo "Test 2 Complete"
echo "=========================================="
echo ""

# Test 3: Minimal request
echo "=========================================="
echo "Test 3: Minimal Request"
echo "=========================================="
echo ""

curl --location 'http://localhost:8000/query/form' \
--form 'input="Create 20 records with program prg1 and prg2 in retail sector for plants PLT-01 and PLT-02"' \
--form 'config_path="config/json_schema_test_data_generator.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="test-minimal-'$(date +%s)'"'

echo ""
echo ""
echo "=========================================="
echo "Test 3 Complete"
echo "=========================================="
echo ""

echo "All tests complete!"
echo ""
echo "Check the agentlogs/ directory for detailed execution logs"
echo "Check the data/ directory for generated datasets"

