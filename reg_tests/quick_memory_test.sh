#!/bin/bash
"""
Quick Memory System Test using Pure Curl Commands

Simple test script using only curl to validate memory system fixes.
Tests multi-turn conversations and big data handling.
"""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8000"
THREAD_ID="quick-test-$(date +%s)"
CONFIG="config/python_exec_agent_working.yaml"

echo -e "${YELLOW}Quick Memory System Test${NC}"
echo "======================="
echo "Thread ID: $THREAD_ID"
echo "Base URL: $BASE_URL"
echo ""

# Function to make curl request
make_request() {
    local input="$1"
    local turn="$2"
    
    echo -e "${BLUE}Turn $turn:${NC} $input"
    
    response=$(curl --silent --location "$BASE_URL/query/form" \
        --form "input=\"$input\"" \
        --form "config_path=\"$CONFIG\"" \
        --form "raw_output=\"True\"" \
        --form "thread_id=\"$THREAD_ID\"")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Response:${NC} $response"
        echo ""
        return 0
    else
        echo -e "${RED}Error: Request failed${NC}"
        echo ""
        return 1
    fi
}

# Test 1: Establish context
echo -e "${YELLOW}=== Test 1: Establishing Context ===${NC}"
make_request "My name is John and I'm working on a data science project analyzing customer behavior using Python and pandas" "1"

# Test 2: Add more context with big data
echo -e "${YELLOW}=== Test 2: Big Data Context ===${NC}"
big_data="I have a dataset with the following columns: customer_id, purchase_date, product_category, amount_spent, customer_age, customer_location, payment_method, discount_applied, review_rating, return_status, marketing_channel, session_duration, page_views, cart_abandonment, loyalty_points, referral_source. The dataset contains 50000 records spanning 3 years from 2021-2024."
make_request "$big_data" "2"

# Test 3: Reference previous context
echo -e "${YELLOW}=== Test 3: Memory Recall ===${NC}"
make_request "What did I tell you about my name and project? Also, how many records are in my dataset?" "3"

# Test 4: Complex follow-up
echo -e "${YELLOW}=== Test 4: Complex Context Usage ===${NC}"
make_request "Based on the dataset columns I mentioned earlier, what analysis would you recommend for understanding customer behavior patterns?" "4"

# Test 5: Rapid requests test (simulate concurrent load)
echo -e "${YELLOW}=== Test 5: Rapid Requests ===${NC}"
for i in {1..5}; do
    make_request "Rapid request #$i - remember this number!" "5.$i" &
done
wait

# Test 6: Memory verification after rapid requests
echo -e "${YELLOW}=== Test 6: Post-Rapid Memory Check ===${NC}"
make_request "How many rapid requests did I just send, and what was the pattern?" "6"

echo -e "${GREEN}Memory test completed!${NC}"
echo ""
echo -e "${YELLOW}Manual Verification Checklist:${NC}"
echo "□ Turn 3 should mention 'John' and reference the data science project"
echo "□ Turn 3 should mention '50000 records' or '50,000 records'"
echo "□ Turn 4 should reference specific columns mentioned in Turn 2"
echo "□ Turn 6 should mention '5 rapid requests' or similar count"
echo "□ No serialization errors should appear in server logs"
echo "□ No duplicate ID errors should appear in server logs"
