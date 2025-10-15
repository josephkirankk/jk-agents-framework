#!/bin/bash
# Test script to demonstrate conversation memory with thread_id

set -e

BASE_URL="http://localhost:8000"
CONFIG="config/python_exec_agent_working.yaml"
THREAD_ID="test-conversation-$(date +%s)"

echo "=========================================="
echo "CONVERSATION MEMORY TEST"
echo "=========================================="
echo "Thread ID: $THREAD_ID"
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

# Request 1: Print numbers 1 to 10
echo "=========================================="
echo "REQUEST 1: Print numbers 1 to 10"
echo "=========================================="

RESPONSE1=$(curl -s -X POST "$BASE_URL/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"print 1 to 10\",
    \"config_path\": \"$CONFIG\",
    \"thread_id\": \"$THREAD_ID\"
  }")

echo "Response 1:"
echo "$RESPONSE1" | jq -r '.response' | head -20
echo ""

# Wait a moment
echo "Waiting 2 seconds..."
sleep 2
echo ""

# Request 2: Write Fibonacci for each number
echo "=========================================="
echo "REQUEST 2: Write Fibonacci for each number"
echo "=========================================="
echo "Expected: Should use numbers from Request 1"
echo ""

RESPONSE2=$(curl -s -X POST "$BASE_URL/query" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"write fibonacci for each number here\",
    \"config_path\": \"$CONFIG\",
    \"thread_id\": \"$THREAD_ID\"
  }")

echo "Response 2:"
echo "$RESPONSE2" | jq -r '.response'
echo ""

# Check if response contains Fibonacci numbers
if echo "$RESPONSE2" | grep -q -E "(1.*1.*2.*3.*5.*8|fibonacci)"; then
    echo "✅ SUCCESS: Response contains Fibonacci numbers"
    echo "✅ Conversation memory is WORKING!"
else
    echo "❌ FAILURE: Response doesn't contain expected Fibonacci numbers"
    echo "⚠️  Check if agent asked for numbers (indicates no context)"
fi

echo ""
echo "=========================================="
echo "TEST COMPLETE"
echo "=========================================="
