#!/bin/bash

# Test script for the consolidated responses API endpoint using curl
# This script tests the new /consolidated-responses endpoint with various scenarios

BASE_URL="http://127.0.0.1:8000"
ENDPOINT="/consolidated-responses"
FULL_URL="${BASE_URL}${ENDPOINT}"

echo "🚀 Starting Consolidated Responses API Tests with curl"
echo "============================================================"
echo "Testing endpoint: $FULL_URL"
echo ""

# Function to make curl request and format output
test_curl() {
    local test_name="$1"
    local payload="$2"
    
    echo "🔍 Test: $test_name"
    echo "📝 Payload: $payload"
    echo "📊 Response:"
    
    curl -X POST "$FULL_URL" \
         -H "Content-Type: application/json" \
         -H "Accept: application/json" \
         -d "$payload" \
         -w "\n📈 Status Code: %{http_code}\n⏱️  Response Time: %{time_total}s\n" \
         -s --max-time 30 | jq '.' 2>/dev/null || echo "Failed to parse JSON response"
    
    echo ""
    echo "----------------------------------------"
    echo ""
}

# Test 1: Get all submissions (no date filters)
test_curl "Get all submissions (no filters)" "{}"

# Test 2: Get submissions from today
TODAY=$(date -u +"%Y-%m-%dT00:00:00Z")
test_curl "Get submissions from today" "{\"start_date\": \"$TODAY\"}"

# Test 3: Get submissions from a specific date
SPECIFIC_DATE="2025-09-20T00:00:00Z"
test_curl "Get submissions from specific date" "{\"start_date\": \"$SPECIFIC_DATE\"}"

# Test 4: Get submissions for a specific date range
START_DATE="2025-09-20T00:00:00Z"
END_DATE="2025-09-20T23:59:59Z"
test_curl "Get submissions for date range" "{\"start_date\": \"$START_DATE\", \"end_date\": \"$END_DATE\"}"

# Test 5: Test invalid date format
test_curl "Test invalid date format" "{\"start_date\": \"invalid-date\"}"

# Test 6: Test invalid date range (start > end)
test_curl "Test invalid date range" "{\"start_date\": \"2025-09-21T00:00:00Z\", \"end_date\": \"2025-09-20T00:00:00Z\"}"

# Test 7: Get submissions from last 7 days
WEEK_AGO=$(date -u -d '7 days ago' +"%Y-%m-%dT00:00:00Z" 2>/dev/null || date -u -v-7d +"%Y-%m-%dT00:00:00Z" 2>/dev/null || echo "2025-09-13T00:00:00Z")
test_curl "Get submissions from last 7 days" "{\"start_date\": \"$WEEK_AGO\"}"

echo "🏁 All curl tests completed!"
echo "============================================================"
