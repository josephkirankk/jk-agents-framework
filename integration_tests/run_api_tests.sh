#!/bin/bash
# Comprehensive API Integration Test Runner
# This script manages the API server lifecycle and runs integration tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}API Integration Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the project root directory (parent of integration_tests)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📂 Project root: $PROJECT_ROOT${NC}"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found at .venv${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m pip install uv
    uv venv -p python .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
else
    echo -e "${GREEN}✓ Virtual environment found${NC}"
    source .venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi

# Function to check if server is ready
check_server_ready() {
    if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to stop API server
stop_api_server() {
    echo -e "${YELLOW}🛑 Stopping API server...${NC}"
    PID=$(lsof -ti :8000 2>/dev/null || echo "")
    if [ -n "$PID" ]; then
        echo -e "${YELLOW}   Found process $PID on port 8000, killing it...${NC}"
        kill $PID 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if kill -0 $PID 2>/dev/null; then
            echo -e "${YELLOW}   Force killing process $PID...${NC}"
            kill -9 $PID 2>/dev/null || true
        fi
        echo -e "${GREEN}   ✓ API server stopped${NC}"
    else
        echo -e "${YELLOW}   ℹ️  No API server found running on port 8000${NC}"
    fi
}

# Cleanup on exit
cleanup() {
    EXIT_CODE=$?
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    stop_api_server
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ Tests completed successfully!${NC}"
        echo -e "${GREEN}========================================${NC}"
    else
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}❌ Tests failed with exit code $EXIT_CODE${NC}"
        echo -e "${RED}========================================${NC}"
    fi
    
    exit $EXIT_CODE
}

trap cleanup EXIT INT TERM

# Stop any existing API server
stop_api_server

# Start the API server in background
echo ""
echo -e "${BLUE}🚀 Starting API server...${NC}"
python api.py > logs/api_test.log 2>&1 &
API_PID=$!
echo -e "${YELLOW}   API PID: $API_PID${NC}"

# Wait for server to be ready
echo -e "${YELLOW}⏳ Waiting for server to be ready...${NC}"
MAX_WAIT=60  # 60 seconds timeout
WAIT_COUNT=0

while ! check_server_ready; do
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo -e "${RED}❌ Server failed to start within $MAX_WAIT seconds${NC}"
        echo -e "${RED}   Check logs/api_test.log for details${NC}"
        echo ""
        echo -e "${YELLOW}Last 20 lines of API log:${NC}"
        tail -n 20 logs/api_test.log
        exit 1
    fi
    
    # Check if process is still running
    if ! kill -0 $API_PID 2>/dev/null; then
        echo -e "${RED}❌ API server process died${NC}"
        echo -e "${RED}   Check logs/api_test.log for details${NC}"
        echo ""
        echo -e "${YELLOW}Last 30 lines of API log:${NC}"
        tail -n 30 logs/api_test.log
        exit 1
    fi
    
    echo -e "${YELLOW}   Waiting... ($((WAIT_COUNT + 1))/$MAX_WAIT)${NC}"
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

echo -e "${GREEN}✅ API server is ready and running!${NC}"
echo -e "${GREEN}   Health check: http://localhost:8000/health${NC}"
echo -e "${GREEN}   API docs: http://localhost:8000/docs${NC}"

# Give it an extra moment to fully initialize
sleep 2

# Run the integration tests
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🧪 Running API Integration Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd integration_tests

# Run pytest with detailed output
python -m pytest test_09_api_critical_flows.py \
    -v \
    --tb=short \
    --color=yes \
    -s \
    "$@"

TEST_EXIT_CODE=$?

# Exit with test result code
exit $TEST_EXIT_CODE
