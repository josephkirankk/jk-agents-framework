#!/bin/bash
# Run all API tests and save output

cd "$(dirname "$0")"
echo "Running all API integration tests..."
echo "===================================="
../.venv/bin/pytest test_09_api_critical_flows.py -v --tb=line
