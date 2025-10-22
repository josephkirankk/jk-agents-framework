#!/bin/bash
# Quick API Test - Minimal setup to verify API integration tests

echo "🔍 Quick API Test Setup"
echo "======================="
echo ""

# Check if API is running
echo "Checking if API server is running..."
if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server is running"
    echo ""
    echo "Running tests..."
    cd "$(dirname "$0")"
    python -m pytest test_09_api_critical_flows.py -v
else
    echo "❌ API server is NOT running"
    echo ""
    echo "To run these tests:"
    echo "  1. Start API in terminal 1:"
    echo "     cd /Users/A80997271/Documents/projects/jk-agents-core"
    echo "     source .venv/bin/activate"
    echo "     python api.py"
    echo ""
    echo "  2. Run tests in terminal 2:"
    echo "     cd /Users/A80997271/Documents/projects/jk-agents-core"
    echo "     source .venv/bin/activate"
    echo "     bash integration_tests/quick_api_test.sh"
    echo ""
    echo "Or use the automated runner:"
    echo "     bash integration_tests/run_api_tests.sh"
fi
