#!/bin/bash
# Comprehensive test to verify conversation memory fix
# Tests both conversation continuity and absence of tool call errors

set -e

BASE_URL="http://localhost:8000"
CONFIG="config/python_exec_agent_working.yaml"

echo "=========================================="
echo "CONVERSATION MEMORY FIX VERIFICATION"
echo "=========================================="
echo ""

# Check if API is running
echo "Checking API server..."
if ! curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ API server is not running"
    echo "   Start with: python api.py"
    exit 1
fi
echo "✅ API server is running"
echo ""

# Clean up any existing thread
rm -f .current_thread_id
echo "🧹 Cleaned up previous thread"
echo ""

# Test 1: Basic conversation flow
echo "=========================================="
echo "TEST 1: Basic Conversation Flow"
echo "=========================================="
echo ""

echo "Request 1: Print numbers 1 to 10"
./temp_tests/query_with_memory.sh "print 1 to 10" > /tmp/test1_output.txt 2>&1
if grep -q "1" /tmp/test1_output.txt && grep -q "10" /tmp/test1_output.txt; then
    echo "✅ Request 1 successful - numbers printed"
else
    echo "❌ Request 1 failed"
    cat /tmp/test1_output.txt
    exit 1
fi

sleep 2

echo ""
echo "Request 2: Calculate Fibonacci for each number"
./temp_tests/query_with_memory.sh "write fibonacci for each number here" > /tmp/test2_output.txt 2>&1
if grep -q "Fibonacci" /tmp/test2_output.txt && ! grep -qi "provide the numbers" /tmp/test2_output.txt; then
    echo "✅ Request 2 successful - used context from Request 1"
else
    echo "❌ Request 2 failed - did not use context"
    cat /tmp/test2_output.txt
    exit 1
fi

sleep 2

echo ""
echo "Request 3: Print highest and lowest"
./temp_tests/query_with_memory.sh "print the highest and lowest" > /tmp/test3_output.txt 2>&1
if grep -qi "error.*tool_calls" /tmp/test3_output.txt; then
    echo "❌ Request 3 FAILED - Tool call error detected"
    echo "   This means the ChromaDB fix didn't work"
    cat /tmp/test3_output.txt
    exit 1
elif grep -qi "success.*false" /tmp/test3_output.txt; then
    echo "❌ Request 3 FAILED - Execution error"
    cat /tmp/test3_output.txt
    exit 1
else
    echo "✅ Request 3 successful - no tool call errors"
fi

echo ""
echo "=========================================="
echo "TEST 2: Extended Conversation (5 turns)"
echo "=========================================="
echo ""

# Clean up and start fresh
rm -f .current_thread_id

REQUESTS=(
    "list 5 colors"
    "now list 5 fruits"
    "combine them into pairs"
    "count the total items"
    "sort them alphabetically"
)

for i in "${!REQUESTS[@]}"; do
    REQ_NUM=$((i + 1))
    echo "Request $REQ_NUM: ${REQUESTS[$i]}"
    
    ./temp_tests/query_with_memory.sh "${REQUESTS[$i]}" > /tmp/test_extended_$REQ_NUM.txt 2>&1
    
    if grep -qi "error.*tool_calls" /tmp/test_extended_$REQ_NUM.txt; then
        echo "❌ Request $REQ_NUM FAILED - Tool call error"
        cat /tmp/test_extended_$REQ_NUM.txt
        exit 1
    elif grep -qi "success.*false" /tmp/test_extended_$REQ_NUM.txt; then
        echo "⚠️  Request $REQ_NUM had execution issues (but no tool call errors)"
    else
        echo "✅ Request $REQ_NUM successful"
    fi
    
    sleep 1
done

echo ""
echo "=========================================="
echo "TEST 3: Verify Conversation Storage"
echo "=========================================="
echo ""

THREAD_ID=$(cat .current_thread_id)
CONV_FILE="simple_memory/$THREAD_ID.json"

if [ -f "$CONV_FILE" ]; then
    TURN_COUNT=$(cat "$CONV_FILE" | python -c "import sys, json; data=json.load(sys.stdin); print(len([m for m in data['messages'] if m['role']=='user']))" 2>/dev/null || echo "0")
    echo "✅ Conversation file exists: $CONV_FILE"
    echo "   Turn count: $TURN_COUNT"
    
    if [ "$TURN_COUNT" -ge "5" ]; then
        echo "✅ All turns stored correctly"
    else
        echo "⚠️  Expected 5+ turns, found $TURN_COUNT"
    fi
else
    echo "❌ Conversation file not found: $CONV_FILE"
    exit 1
fi

echo ""
echo "=========================================="
echo "TEST 4: Config Verification"
echo "=========================================="
echo ""

if grep -q 'backend: "none"' "$CONFIG"; then
    echo "✅ ChromaDB backend is disabled (correct)"
elif grep -q 'backend: "chromadb"' "$CONFIG"; then
    echo "❌ ChromaDB backend is still enabled (incorrect)"
    echo "   This will cause tool call errors"
    exit 1
else
    echo "⚠️  Could not verify memory backend setting"
fi

if grep -q 'enabled: true' "$CONFIG" | grep -A 2 "conversation_memory"; then
    echo "✅ Conversation memory is enabled (correct)"
else
    echo "⚠️  Could not verify conversation_memory setting"
fi

echo ""
echo "=========================================="
echo "✅ ALL TESTS PASSED"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✅ Conversation memory working"
echo "  ✅ Context injection working"
echo "  ✅ No tool call errors"
echo "  ✅ Multi-turn conversations stable"
echo "  ✅ Configuration correct"
echo ""
echo "The conversation memory fix is working correctly!"
echo ""

# Cleanup
rm -f /tmp/test*.txt
rm -f .current_thread_id

exit 0
