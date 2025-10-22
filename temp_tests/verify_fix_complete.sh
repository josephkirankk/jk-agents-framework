#!/bin/bash
# Complete Verification Script for Serper API Fix

set -e

echo "=========================================="
echo "SERPER API FIX - COMPLETE VERIFICATION"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

# Test 1: Check .env file exists
echo "Test 1: Checking .env file..."
if [ -f .env ]; then
    echo -e "${GREEN}✓ PASS${NC}: .env file found"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗ FAIL${NC}: .env file not found"
    ((FAIL_COUNT++))
    exit 1
fi
echo ""

# Test 2: Check SERPER_API_KEY exists
echo "Test 2: Checking SERPER_API_KEY in .env..."
source .env 2>/dev/null || true
if [ -z "$SERPER_API_KEY" ]; then
    echo -e "${RED}✗ FAIL${NC}: SERPER_API_KEY not found in .env"
    echo "  Add: SERPER_API_KEY=your_key_here"
    ((FAIL_COUNT++))
    exit 1
else
    KEY_LEN=${#SERPER_API_KEY}
    echo -e "${GREEN}✓ PASS${NC}: SERPER_API_KEY found (${KEY_LEN} characters)"
    echo "  Key: ${SERPER_API_KEY:0:10}...${SERPER_API_KEY: -4}"
    ((PASS_COUNT++))
fi
echo ""

# Test 3: Check if placeholder
echo "Test 3: Checking if key is placeholder..."
if [ "$SERPER_API_KEY" = "your-serper-api-key-here" ]; then
    echo -e "${RED}✗ FAIL${NC}: Still using placeholder key"
    echo "  Get real key from: https://serper.dev"
    ((FAIL_COUNT++))
    exit 1
else
    echo -e "${GREEN}✓ PASS${NC}: Not using placeholder"
    ((PASS_COUNT++))
fi
echo ""

# Test 4: Validate key with Serper API
echo "Test 4: Testing key with Serper API..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"q":"test mcp server","num":1}' 2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC}: API key is valid (HTTP 200)"
    echo "  Serper API responded successfully"
    ((PASS_COUNT++))
elif [ "$HTTP_CODE" = "403" ]; then
    echo -e "${RED}✗ FAIL${NC}: Invalid API key (HTTP 403)"
    echo "  Get new key from: https://serper.dev"
    ((FAIL_COUNT++))
    exit 1
elif [ "$HTTP_CODE" = "429" ]; then
    echo -e "${YELLOW}⚠ WARN${NC}: Rate limited (HTTP 429)"
    echo "  Key is valid but quota exceeded"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠ WARN${NC}: Unexpected status (HTTP $HTTP_CODE)"
    echo "  Body: $BODY"
fi
echo ""

# Test 5: Check if API server is running
echo "Test 5: Checking if API server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC}: API server is running on port 8000"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠ WARN${NC}: API server not running on port 8000"
    echo "  Start with: source .venv/bin/activate && python api.py"
    echo "  (This is OK if you haven't started the server yet)"
fi
echo ""

# Test 6: Check config file
echo "Test 6: Checking config file..."
CONFIG="config/deep_agent_advanced_serpapi.yaml"
if [ -f "$CONFIG" ]; then
    echo -e "${GREEN}✓ PASS${NC}: Config file found: $CONFIG"
    ((PASS_COUNT++))
    
    # Check if SERPER_API_KEY is referenced
    if grep -q "SERPER_API_KEY" "$CONFIG"; then
        echo "  Config references SERPER_API_KEY ✓"
    fi
else
    echo -e "${RED}✗ FAIL${NC}: Config file not found: $CONFIG"
    ((FAIL_COUNT++))
fi
echo ""

# Summary
echo "=========================================="
echo "VERIFICATION SUMMARY"
echo "=========================================="
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}Failed: $FAIL_COUNT${NC}"
fi
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Your Serper API key is valid and ready to use."
    echo ""
    echo "Next steps:"
    echo "1. Make sure API server is running:"
    echo "   source .venv/bin/activate && python api.py"
    echo ""
    echo "2. Test with your query:"
    echo "   curl --location 'http://localhost:8000/query/form' \\"
    echo "   --form 'input=\"research on mcp server as of now\"' \\"
    echo "   --form 'config_path=\"config/deep_agent_advanced_serpapi.yaml\"' \\"
    echo "   --form 'raw_output=\"True\"' \\"
    echo "   --form 'thread_id=\"jk-deep-pep-003\"'"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please fix the issues above and run this script again."
    echo ""
    echo "Quick fix guide:"
    echo "1. Go to: https://serper.dev"
    echo "2. Sign up and get your API key"
    echo "3. Update .env: SERPER_API_KEY=your_key_here"
    echo "4. Run this script again"
    echo ""
    exit 1
fi
