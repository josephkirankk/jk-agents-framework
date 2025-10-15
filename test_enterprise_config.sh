#!/bin/bash

# ============================================================================
# Enterprise Config Test Suite
# Tests reliability, accuracy, performance, and cost optimization
# ============================================================================

set -e

echo "========================================="
echo "ENTERPRISE CONFIG TEST SUITE"
echo "========================================="
echo ""
echo "Testing: config/test_data_parser_enterprise.yaml"
echo ""

API_URL="http://localhost:8000/query/form"
CONFIG="config/test_data_parser_enterprise.yaml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to test and measure
test_scenario() {
    local name="$1"
    local query="$2"
    local thread_id="$3"
    
    echo "----------------------------------------"
    echo "TEST: $name"
    echo "----------------------------------------"
    echo "Query: $query"
    echo ""
    
    START=$(date +%s)
    
    RESPONSE=$(curl -s --location "$API_URL" \
        --form "input=\"$query\"" \
        --form "config_path=\"$CONFIG\"" \
        --form "raw_output=\"True\"" \
        --form "thread_id=\"$thread_id\"" 2>&1)
    
    END=$(date +%s)
    DURATION=$((END - START))
    
    echo "Duration: ${DURATION}s"
    echo ""
    
    # Check if response contains error
    if echo "$RESPONSE" | grep -qi "error\|fail"; then
        echo -e "${RED}❌ FAILED${NC}"
        echo "$RESPONSE" | head -20
    else
        echo -e "${GREEN}✅ SUCCESS${NC}"
        
        # Show response preview
        echo "Response preview:"
        echo "$RESPONSE" | head -10
        
        # Try to count records if JSON array
        if echo "$RESPONSE" | grep -q "^\["; then
            RECORD_COUNT=$(echo "$RESPONSE" | grep -o "{" | wc -l)
            echo ""
            echo "Records generated: $RECORD_COUNT"
        fi
        
        # Check for large data reference
        if echo "$RESPONSE" | grep -qi "reference\|summary"; then
            echo ""
            echo -e "${YELLOW}📦 Large data optimization active${NC}"
        fi
    fi
    
    echo ""
    sleep 2  # Rate limiting
}

# ============================================================================
# Test Suite
# ============================================================================

echo "Starting tests..."
echo ""

# Test 1: Small dataset (should return direct data)
test_scenario \
    "Small Dataset (5 records)" \
    "create 5 records for metric test1, program MFG, sector PFNA, plant p1, values 10 to 100" \
    "ent-test-001"

# Test 2: Medium dataset (should trigger optimization)
test_scenario \
    "Medium Dataset (100 records)" \
    "create 100 records for metric revenue, cost, program MFG, sector PFNA, plant p1, values 100 to 1000" \
    "ent-test-002"

# Test 3: Large dataset with multiple metrics
test_scenario \
    "Large Dataset (1000 records, 3 metrics)" \
    "create 1000 records for metric revenue, cost, profit, program MFG, sector PFNA, plant p1, values 1000 to 50000, uom count" \
    "ent-test-003"

# Test 4: Complex requirements
test_scenario \
    "Complex Requirements" \
    "create 500 records for metric sales, margin, program ADV, sector QSNA, plant p2, market UK, values 500 to 5000, uom kg, 10% negative values from -100 to -10, date range 60 days" \
    "ent-test-004"

# Test 5: Stress test (if server can handle)
# test_scenario \
#     "Stress Test (10000 records)" \
#     "create 10000 records for metric test, program MFG" \
#     "ent-test-005"

# ============================================================================
# Summary
# ============================================================================

echo "========================================="
echo "TEST SUITE COMPLETE"
echo "========================================="
echo ""
echo "Review results above for:"
echo "✅ Accuracy: Records match requirements"
echo "✅ Performance: Response times acceptable"
echo "✅ Cost: Token optimization working"
echo "✅ Reliability: No errors or failures"
echo ""
echo "Check server logs for detailed token usage:"
echo "  tail -f api.log | grep -i 'token\|usage'"
echo ""
