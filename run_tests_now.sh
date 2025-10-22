#!/bin/bash
# Quick test runner script
cd "$(dirname "$0")"

echo "================================"
echo "Running Integration Tests"
echo "================================"
echo ""

# Use the venv Python directly
PYTHON=".venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found at .venv/"
    echo "   Please run: uv venv .venv"
    exit 1
fi

echo "✓ Using Python: $PYTHON"
echo ""

# List tests
echo "--- Available Tests ---"
$PYTHON integration_tests/run_all_tests.py --list
echo ""

# Run quick tests
echo "================================"
echo "Running QUICK Tests"
echo "================================"
$PYTHON integration_tests/run_all_tests.py --quick

exit_code=$?
echo ""
echo "================================"
echo "Exit code: $exit_code"
echo "================================"
exit $exit_code
