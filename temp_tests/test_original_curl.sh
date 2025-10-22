#!/bin/bash

echo "Running original curl command to verify fix..."
echo "================================================"

curl --location 'http://localhost:8000/query/form' \
  --form 'input="top smartphones under ₹20,000 in India (as of Oct 21st, 2025) with good battery life and minimal heating issues. Each entry should include the current price, weight, real-time stock status, and buy URL"' \
  --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="jk-deep-pep-verify-fix"' \
  -w "\n\nHTTP Status: %{http_code}\n" \
  -s

echo ""
echo "================================================"
echo "Check the latest log file in agentlogs/ for details"
