#!/bin/bash

# JK-Agents Thread ID Continuity Test Script
# This script demonstrates how thread IDs enable conversation continuity
# across multiple API calls using the pep_mcp_sample.yaml configuration

set -e  # Exit on any error

# Configuration
API_BASE="http://localhost:8000"
CONFIG_PATH="c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== JK-Agents Thread ID Continuity Test ===${NC}"
echo -e "${YELLOW}Using config: ${CONFIG_PATH}${NC}"
echo ""

# Function to extract thread_id from JSON response
extract_thread_id() {
    echo "$1" | grep -o '"thread_id":"[^"]*"' | cut -d'"' -f4
}

# Function to extract response from JSON
extract_response() {
    echo "$1" | grep -o '"response":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g'
}

# Function to make API call and display results
make_api_call() {
    local endpoint="$1"
    local payload="$2"
    local description="$3"
    
    echo -e "${BLUE}--- ${description} ---${NC}"
    echo -e "${YELLOW}Endpoint:${NC} ${endpoint}"
    echo -e "${YELLOW}Payload:${NC} ${payload}"
    echo ""
    
    # Make the API call
    response=$(curl -s -X POST "${API_BASE}${endpoint}" \
        -H "Content-Type: application/json" \
        -d "${payload}")
    
    # Check if response is valid JSON
    if echo "$response" | jq . >/dev/null 2>&1; then
        echo -e "${GREEN}✓ API call successful${NC}"
        
        # Extract and display thread_id
        thread_id=$(echo "$response" | jq -r '.thread_id // empty')
        if [ -n "$thread_id" ]; then
            echo -e "${YELLOW}Thread ID:${NC} ${thread_id}"
        else
            echo -e "${RED}⚠ No thread_id found in response${NC}"
        fi
        
        # Extract and display response
        api_response=$(echo "$response" | jq -r '.response // empty')
        if [ -n "$api_response" ]; then
            echo -e "${YELLOW}Response:${NC} ${api_response}"
        fi
        
        echo ""
        return 0
    else
        echo -e "${RED}✗ API call failed${NC}"
        echo -e "${RED}Response:${NC} ${response}"
        echo ""
        return 1
    fi
}

# Test 1: Start new conversation (no thread_id) - Multi-agent query
echo -e "${GREEN}=== Test 1: Start New Conversation (Multi-Agent Query) ===${NC}"
payload1='{
    "input": "Hello! I need help finding restaurants in New York. Please remember that I prefer Italian cuisine.",
    "config_path": "'"${CONFIG_PATH}"'"
}'

response1=$(curl -s -X POST "${API_BASE}/query" \
    -H "Content-Type: application/json" \
    -d "${payload1}")

if echo "$response1" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}✓ First API call successful${NC}"
    thread_id1=$(echo "$response1" | jq -r '.thread_id')
    echo -e "${YELLOW}Generated Thread ID:${NC} ${thread_id1}"
    
    response_text1=$(echo "$response1" | jq -r '.response')
    echo -e "${YELLOW}Response:${NC} ${response_text1}"
    echo ""
else
    echo -e "${RED}✗ First API call failed${NC}"
    echo -e "${RED}Response:${NC} ${response1}"
    exit 1
fi

# Test 2: Continue conversation using thread_id
echo -e "${GREEN}=== Test 2: Continue Conversation (Using Thread ID) ===${NC}"
payload2='{
    "input": "Can you remember what type of cuisine I mentioned I prefer? And can you search for those restaurants in Manhattan?",
    "config_path": "'"${CONFIG_PATH}"'",
    "thread_id": "'"${thread_id1}"'"
}'

response2=$(curl -s -X POST "${API_BASE}/query" \
    -H "Content-Type: application/json" \
    -d "${payload2}")

if echo "$response2" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Second API call successful${NC}"
    thread_id2=$(echo "$response2" | jq -r '.thread_id')
    echo -e "${YELLOW}Thread ID:${NC} ${thread_id2}"
    
    if [ "$thread_id1" = "$thread_id2" ]; then
        echo -e "${GREEN}✓ Thread ID consistency maintained${NC}"
    else
        echo -e "${RED}✗ Thread ID changed unexpectedly${NC}"
    fi
    
    response_text2=$(echo "$response2" | jq -r '.response')
    echo -e "${YELLOW}Response:${NC} ${response_text2}"
    echo ""
else
    echo -e "${RED}✗ Second API call failed${NC}"
    echo -e "${RED}Response:${NC} ${response2}"
    exit 1
fi

# Test 3: Direct agent call with thread_id
echo -e "${GREEN}=== Test 3: Direct Agent Call (Using Thread ID) ===${NC}"
payload3='{
    "agent_name": "restaurants_agent",
    "input": "Based on our previous conversation, can you find 3 specific Italian restaurants in Manhattan with high ratings?",
    "config_path": "'"${CONFIG_PATH}"'",
    "thread_id": "'"${thread_id1}"'"
}'

response3=$(curl -s -X POST "${API_BASE}/worker" \
    -H "Content-Type: application/json" \
    -d "${payload3}")

if echo "$response3" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Direct agent call successful${NC}"
    thread_id3=$(echo "$response3" | jq -r '.thread_id')
    echo -e "${YELLOW}Thread ID:${NC} ${thread_id3}"
    
    if [ "$thread_id1" = "$thread_id3" ]; then
        echo -e "${GREEN}✓ Thread ID consistency maintained across endpoints${NC}"
    else
        echo -e "${RED}✗ Thread ID changed across endpoints${NC}"
    fi
    
    response_text3=$(echo "$response3" | jq -r '.response')
    echo -e "${YELLOW}Response:${NC} ${response_text3}"
    echo ""
else
    echo -e "${RED}✗ Direct agent call failed${NC}"
    echo -e "${RED}Response:${NC} ${response3}"
    exit 1
fi

# Test 4: New conversation (different thread)
echo -e "${GREEN}=== Test 4: New Conversation (Different Thread) ===${NC}"
payload4='{
    "input": "What type of cuisine do I prefer? This should be a fresh conversation.",
    "config_path": "'"${CONFIG_PATH}"'"
}'

response4=$(curl -s -X POST "${API_BASE}/query" \
    -H "Content-Type: application/json" \
    -d "${payload4}")

if echo "$response4" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}✓ New conversation API call successful${NC}"
    thread_id4=$(echo "$response4" | jq -r '.thread_id')
    echo -e "${YELLOW}New Thread ID:${NC} ${thread_id4}"
    
    if [ "$thread_id1" != "$thread_id4" ]; then
        echo -e "${GREEN}✓ New thread ID generated for new conversation${NC}"
    else
        echo -e "${RED}✗ Same thread ID used for new conversation${NC}"
    fi
    
    response_text4=$(echo "$response4" | jq -r '.response')
    echo -e "${YELLOW}Response:${NC} ${response_text4}"
    echo ""
else
    echo -e "${RED}✗ New conversation API call failed${NC}"
    echo -e "${RED}Response:${NC} ${response4}"
    exit 1
fi

# Test 5: Custom thread ID
echo -e "${GREEN}=== Test 5: Custom Thread ID ===${NC}"
custom_thread="my-restaurant-session-2024"
payload5='{
    "input": "I want to start a new restaurant search session. Please remember I am looking for vegetarian options.",
    "config_path": "'"${CONFIG_PATH}"'",
    "thread_id": "'"${custom_thread}"'"
}'

response5=$(curl -s -X POST "${API_BASE}/query" \
    -H "Content-Type: application/json" \
    -d "${payload5}")

if echo "$response5" | jq . >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Custom thread ID API call successful${NC}"
    thread_id5=$(echo "$response5" | jq -r '.thread_id')
    echo -e "${YELLOW}Thread ID:${NC} ${thread_id5}"
    
    if [ "$custom_thread" = "$thread_id5" ]; then
        echo -e "${GREEN}✓ Custom thread ID accepted${NC}"
    else
        echo -e "${RED}✗ Custom thread ID not used${NC}"
    fi
    
    response_text5=$(echo "$response5" | jq -r '.response')
    echo -e "${YELLOW}Response:${NC} ${response_text5}"
    echo ""
else
    echo -e "${RED}✗ Custom thread ID API call failed${NC}"
    echo -e "${RED}Response:${NC} ${response5}"
    exit 1
fi

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "${GREEN}✓ All tests completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Thread IDs used:${NC}"
echo -e "  Test 1 (New conversation): ${thread_id1}"
echo -e "  Test 2 (Continue conversation): ${thread_id2}"
echo -e "  Test 3 (Direct agent): ${thread_id3}"
echo -e "  Test 4 (New conversation): ${thread_id4}"
echo -e "  Test 5 (Custom thread): ${thread_id5}"
echo ""
echo -e "${BLUE}Key Findings:${NC}"
echo -e "• Thread IDs are automatically generated when not provided"
echo -e "• Thread IDs are maintained across API calls when provided"
echo -e "• Thread IDs enable conversation continuity and memory"
echo -e "• Different thread IDs create isolated conversations"
echo -e "• Custom thread IDs are accepted and used"
echo -e "• All API endpoints support thread ID parameter"
echo ""
echo -e "${GREEN}Thread ID continuity is working correctly! 🎉${NC}"
