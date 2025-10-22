#!/bin/bash
# Verification script for integration test fixes
# Run this to verify all fixes are working

cd "$(dirname "$0")"

echo "========================================"
echo "Integration Tests - Fix Verification"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found at .venv/"
    echo "   Please create it first: uv venv .venv"
    exit 1
fi

PYTHON=".venv/bin/python"
echo "Using Python: $PYTHON"
echo ""

# Function to run a test and check result
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo "========================================" 
    echo "Testing: $test_name"
    echo "========================================" 
    
    $PYTHON "$test_file"
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ PASS: $test_name"
    else
        echo "❌ FAIL: $test_name (exit code: $exit_code)"
        return 1
    fi
    echo ""
}

# Test individual fixed tests
echo "Phase 1: Individual Test Verification"
echo "========================================"
echo ""

run_test "integration_tests/test_01_agent_types.py" "Test 1: Agent Types"
test1=$?

run_test "integration_tests/test_05_litellm_providers.py" "Test 5: LiteLLM Providers"
test5=$?

echo ""
echo "Phase 2: Quick Tests Suite"
echo "========================================"
echo ""

$PYTHON integration_tests/run_all_tests.py --quick
quick_exit=$?

echo ""
echo "========================================"
echo "Verification Summary"
echo "========================================"
echo ""

if [ $test1 -eq 0 ] && [ $test5 -eq 0 ] && [ $quick_exit -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED!"
    echo ""
    echo "✅ Test 1 (Agent Types): FIXED"
    echo "✅ Test 5 (LiteLLM): FIXED"
    echo "✅ Quick Test Suite: PASSING"
    echo ""
    echo "Ready to run full test suite:"
    echo "  python integration_tests/run_all_tests.py"
    exit 0
else
    echo "⚠️  SOME TESTS FAILED"
    echo ""
    echo "Test 1 (Agent Types): $([ $test1 -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
    echo "Test 5 (LiteLLM): $([ $test5 -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
    echo "Quick Suite: $([ $quick_exit -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')"
    echo ""
    echo "Please check the error messages above."
    exit 1
fi
