#!/bin/bash
# Test script for Deep Agent inspection tools
# This script tests all the tools to ensure they work correctly

set -e  # Exit on error

echo "=========================================="
echo "Deep Agent Tools Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: .venv directory not found${NC}"
    echo "Please create virtual environment first:"
    echo "  uv venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Check Python version
echo -e "${YELLOW}Python version:${NC}"
python --version

# Test 1: Run diagnostic tool
echo ""
echo "=========================================="
echo "Test 1: Diagnostic Tool"
echo "=========================================="
echo -e "${YELLOW}Running: python tools/diagnose_deep_agent_storage.py${NC}"
echo ""

if python tools/diagnose_deep_agent_storage.py; then
    echo -e "${GREEN}✓ Diagnostic tool ran successfully${NC}"
else
    echo -e "${RED}✗ Diagnostic tool failed${NC}"
    exit 1
fi

# Test 2: Run find threads tool
echo ""
echo "=========================================="
echo "Test 2: Find Threads Tool"
echo "=========================================="
echo -e "${YELLOW}Running: python tools/find_threads.py${NC}"
echo ""

if python tools/find_threads.py; then
    echo -e "${GREEN}✓ Find threads tool ran successfully${NC}"
else
    echo -e "${RED}✗ Find threads tool failed${NC}"
    exit 1
fi

# Test 3: Try listing threads with inspector
echo ""
echo "=========================================="
echo "Test 3: List Threads (Inspector)"
echo "=========================================="
echo -e "${YELLOW}Running: python tools/deep_agent_inspector.py --list-threads${NC}"
echo ""

if python tools/deep_agent_inspector.py --list-threads 2>&1 | head -20; then
    echo -e "${GREEN}✓ Inspector list-threads ran successfully${NC}"
else
    echo -e "${RED}✗ Inspector list-threads failed${NC}"
fi

# Test 4: Try listing threads with state viewer
echo ""
echo "=========================================="
echo "Test 4: List Threads (State Viewer)"
echo "=========================================="
echo -e "${YELLOW}Running: python tools/deep_agent_state_viewer.py --list-threads${NC}"
echo ""

if python tools/deep_agent_state_viewer.py --list-threads 2>&1 | head -20; then
    echo -e "${GREEN}✓ State viewer list-threads ran successfully${NC}"
else
    echo -e "${RED}✗ State viewer list-threads failed${NC}"
fi

# Final summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo -e "${GREEN}All tests completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Check the output above for thread IDs"
echo "2. Use a thread ID to view state:"
echo "   python tools/deep_agent_inspector.py --thread-id <thread_id>"
echo ""
echo "3. Export as HTML:"
echo "   python tools/deep_agent_inspector.py --export-html <thread_id> --output report.html"
echo ""
echo "=========================================="
