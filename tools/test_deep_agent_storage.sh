#!/bin/bash
# Test Deep Agent Storage End-to-End
# This script:
# 1. Checks if the API server is running
# 2. Runs a test query with a known thread_id
# 3. Checks if the state was stored in ChromaDB
# 4. Displays the stored state

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Deep Agent Storage End-to-End Test"
echo "=========================================="

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}Error: .venv not found${NC}"
    exit 1
fi

# Step 1: Check if API server is running
echo ""
echo "=========================================="
echo "Step 1: Checking API Server"
echo "=========================================="

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo -e "${GREEN}✓ API server is running${NC}"
else
    echo -e "${RED}✗ API server is not running on localhost:8000${NC}"
    echo ""
    echo "Please start the API server first:"
    echo "  python api_server.py  # or your server start command"
    echo ""
    exit 1
fi

# Step 2: Check current state BEFORE running curl
echo ""
echo "=========================================="
echo "Step 2: Current State (BEFORE)"
echo "=========================================="

echo -e "${YELLOW}Checking existing data...${NC}"
python tools/check_chromadb_data.py --memory-path ./serp_memory

# Step 3: Run the curl command
echo ""
echo "=========================================="
echo "Step 3: Running Deep Agent Query"
echo "=========================================="

THREAD_ID="jk-deep-pep-027"
echo -e "${YELLOW}Thread ID: $THREAD_ID${NC}"
echo -e "${YELLOW}Sending request to API...${NC}"
echo ""

# Run curl and capture response
RESPONSE=$(curl -s --location 'http://localhost:8000/query/form' \
  --form 'input="i am talking about intense version. give me the correct clone in india"' \
  --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="jk-deep-pep-027"')

CURL_EXIT_CODE=$?

if [ $CURL_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Request completed${NC}"
    echo ""
    echo "Response preview (first 500 chars):"
    echo "$RESPONSE" | head -c 500
    echo ""
    echo "..."
else
    echo -e "${RED}✗ Request failed with exit code $CURL_EXIT_CODE${NC}"
    exit 1
fi

# Wait a moment for data to be persisted
echo ""
echo -e "${YELLOW}Waiting 2 seconds for data to persist...${NC}"
sleep 2

# Step 4: Check state AFTER running curl
echo ""
echo "=========================================="
echo "Step 4: Current State (AFTER)"
echo "=========================================="

echo -e "${YELLOW}Checking for new data...${NC}"
python tools/check_chromadb_data.py --memory-path ./serp_memory

# Step 5: Try to retrieve the specific thread
echo ""
echo "=========================================="
echo "Step 5: Retrieving Thread State"
echo "=========================================="

echo -e "${YELLOW}Attempting to retrieve thread: $THREAD_ID${NC}"
echo ""

if python tools/deep_agent_inspector.py --thread-id "$THREAD_ID" --memory-path ./serp_memory 2>&1 | grep -q "No checkpoint found"; then
    echo -e "${RED}✗ Thread not found in database${NC}"
    echo ""
    echo "Possible issues:"
    echo "  1. The checkpointer may not be configured correctly"
    echo "  2. The config file may not enable persistence"
    echo "  3. The thread_id format may be different"
    echo ""
    echo "Let's check what thread IDs actually exist:"
    python tools/check_chromadb_data.py --memory-path ./serp_memory | grep -A 10 "Thread IDs:"
else
    echo -e "${GREEN}✓ Thread found!${NC}"
    echo ""
    python tools/deep_agent_inspector.py --thread-id "$THREAD_ID" --memory-path ./serp_memory
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
