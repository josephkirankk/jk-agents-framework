#!/bin/bash
# Test script for jk-agents-core with large_data_handling
# Fixed for zsh compatibility

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║              JK-AGENTS SYSTEM TEST                                         ║"
echo "║              Testing Fixed Configuration                                   ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

# Function to check server
check_server() {
    echo -e "${BLUE}📡 Checking API server...${NC}"
    if curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Server is NOT running${NC}"
        echo ""
        echo "Please start the server in another terminal:"
        echo "  uvicorn api:app --reload --host 0.0.0.0 --port 8000"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
}

# Function to run test
run_test() {
    local test_num=$1
    local test_name=$2
    local query=$3
    local expected=$4
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "TEST $test_num: $test_name"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    
    echo "Query: $query"
    echo ""
    echo "Sending request..."
    
    # Create temporary file for the request
    local tmpfile=$(mktemp)
    cat > "$tmpfile" << EOF
{
  "query": "$query",
  "config_name": "test_data_parser_enterprise.yaml"
}
EOF
    
    # Send request
    local response=$(curl -s -X POST "$API_URL/query" \
        -H "Content-Type: application/json" \
        -d @"$tmpfile")
    
    rm "$tmpfile"
    
    # Check for errors
    if echo "$response" | grep -q '"error"'; then
        echo -e "${RED}❌ Test $test_num FAILED${NC}"
        echo ""
        echo "Error details:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        return 1
    else
        echo -e "${GREEN}✅ Test $test_num PASSED${NC}"
        
        # Check for large data optimization
        if echo "$response" | grep -q "Large Data Reference"; then
            echo -e "${GREEN}✓ Large data optimization TRIGGERED${NC}"
            
            # Try to extract reference ID
            local ref_id=$(echo "$response" | jq -r '.response' 2>/dev/null | grep -o 'Reference ID.*`[^`]*`' | grep -o '`[^`]*`' | tr -d '`' || echo "")
            if [ -n "$ref_id" ]; then
                echo "  Reference ID: $ref_id"
            fi
            
            # Extract tokens saved
            local tokens_saved=$(echo "$response" | jq -r '.response' 2>/dev/null | grep -o 'Tokens saved: [0-9,]*' || echo "")
            if [ -n "$tokens_saved" ]; then
                echo "  $tokens_saved"
            fi
        else
            if [ "$expected" = "optimized" ]; then
                echo -e "${YELLOW}⚠️  Large data optimization NOT triggered${NC}"
                echo "  (Data might be smaller than 500 token threshold)"
            else
                echo -e "${GREEN}✓ Direct response (no optimization needed)${NC}"
            fi
        fi
        
        return 0
    fi
}

# Main test flow
main() {
    check_server
    
    echo ""
    echo "Starting tests..."
    echo ""
    
    # Test 1: Small dataset
    run_test "1" "Small Dataset (10 records)" \
        "create 10 records for metric test, program MFG, sector PFNA, values 10 to 50" \
        "direct"
    
    sleep 2
    
    # Test 2: Medium dataset - should trigger optimization
    run_test "2" "Medium Dataset (1,000 records)" \
        "create 1000 records for metric revenue, cost, program MFG, sector PFNA, plant p1, values 100 to 500, uom count" \
        "optimized"
    
    sleep 2
    
    # Test 3: Large dataset - definitely should trigger
    run_test "3" "Large Dataset (5,000 records)" \
        "create 5000 records for metric abcd, xyz, program MFG, sector PFNA, plant p1, values 10 to 100, uom count, 5% negative from -10 to 1" \
        "optimized"
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "STORAGE INSPECTION"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    
    python3 inspect_storage_systems.py
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}ALL TESTS COMPLETED${NC}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Summary:"
    echo "  • Configuration: test_data_parser_enterprise.yaml"
    echo "  • Model: azure_openai:gpt-4.1"
    echo "  • Large data handling: ENABLED (threshold: 500 tokens)"
    echo ""
    echo "Documentation:"
    echo "  • Quick reference: LARGE_DATA_QUICK_REF.md"
    echo "  • Deep dive: LARGE_DATA_HANDLING_DEEP_DIVE.md"
    echo ""
}

# Run main
main
