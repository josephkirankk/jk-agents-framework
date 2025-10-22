#!/bin/bash
# Quick check of ChromaDB data - works without API server

echo "=========================================="
echo "Quick ChromaDB Data Check"
echo "=========================================="

# Activate venv
source .venv/bin/activate

# Check current data
python tools/check_chromadb_data.py --memory-path ./serp_memory

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "If no data found:"
echo "  1. Start your API server"
echo "  2. Run your curl command"
echo "  3. Run this script again"
echo ""
echo "If data found:"
echo "  Use the thread ID to view state:"
echo "  python tools/deep_agent_inspector.py --thread-id <thread_id>"
echo ""
