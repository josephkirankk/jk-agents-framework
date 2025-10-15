#!/bin/bash
# Test the simplified test data parser configuration

echo "🧪 Testing simplified parser configuration..."
echo ""

# Test with the original query
echo "📝 Test Query: create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100"
echo ""

curl --location 'http://localhost:8000/query/form' \
  --form 'input="create 100 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 100 to 10000, uom count, 10% negative from -10 to -100"' \
  --form 'config_path="config/test_data_parser_simple.yaml"' \
  --form 'raw_output="True"' \
  --silent | jq '.' || echo "❌ Request failed or returned non-JSON"

echo ""
echo "✅ Test completed"
