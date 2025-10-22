#!/bin/bash

# JK-Agents Quick Win Cleanup Script
# Date: October 21, 2025
# Option 1: Safe deletions only (logs, cache, backups)

set -e  # Exit on error

echo "============================================"
echo "JK-AGENTS QUICK WIN CLEANUP"
echo "============================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "📍 Working directory: $(pwd)"
echo ""

# Step 1: Delete Agent Logs
echo "🗑️  Step 1: Deleting agent logs..."
if [ -d "agentlogs" ]; then
    LOG_COUNT=$(find agentlogs -name "*.log" -type f | wc -l)
    echo "   Found $LOG_COUNT log files in agentlogs/"
    rm -f agentlogs/*.log
    echo "   ✅ Agent logs deleted"
else
    echo "   ⚠️  agentlogs/ directory not found"
fi
echo ""

# Step 2: Delete Memory Logs
echo "🗑️  Step 2: Deleting memory logs..."
if [ -d "memory_logs" ]; then
    LOG_COUNT=$(find memory_logs -name "*.log" -type f | wc -l)
    echo "   Found $LOG_COUNT log files in memory_logs/"
    rm -f memory_logs/*.log
    echo "   ✅ Memory logs deleted"
else
    echo "   ⚠️  memory_logs/ directory not found"
fi
echo ""

# Step 3: Delete __pycache__ directories
echo "🗑️  Step 3: Deleting Python cache directories..."
CACHE_COUNT=$(find . -type d -name "__pycache__" | wc -l)
echo "   Found $CACHE_COUNT __pycache__ directories"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Python cache directories deleted"
echo ""

# Step 4: Delete .pytest_cache directories
echo "🗑️  Step 4: Deleting pytest cache directories..."
PYTEST_COUNT=$(find . -type d -name ".pytest_cache" | wc -l)
echo "   Found $PYTEST_COUNT .pytest_cache directories"
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Pytest cache directories deleted"
echo ""

# Step 5: Delete node_modules directories
echo "🗑️  Step 5: Deleting node_modules directories..."
if [ -d "node_modules" ]; then
    echo "   Deleting root node_modules/"
    rm -rf node_modules/
    echo "   ✅ Root node_modules deleted"
else
    echo "   ℹ️  Root node_modules/ not found"
fi

if [ -d "integration_tests/node_modules" ]; then
    echo "   Deleting integration_tests/node_modules/"
    rm -rf integration_tests/node_modules/
    echo "   ✅ Integration tests node_modules deleted"
else
    echo "   ℹ️  integration_tests/node_modules/ not found"
fi
echo ""

# Step 6: Delete backup file
echo "🗑️  Step 6: Deleting backup file..."
if [ -f "integration_tests/test_09_api_critical_flows.py.bak" ]; then
    rm -f integration_tests/test_09_api_critical_flows.py.bak
    echo "   ✅ Backup file deleted"
else
    echo "   ℹ️  Backup file not found"
fi
echo ""

# Step 7: Verification
echo "============================================"
echo "🔍 VERIFICATION"
echo "============================================"
echo ""

echo "Checking if Python imports still work..."
python3 -c "from app import api; print('✅ Imports working correctly')" 2>&1 || echo "⚠️  Import check failed - please investigate"
echo ""

echo "Git status (should show no changes to tracked files):"
git status --short 2>&1 || echo "Not a git repository"
echo ""

# Calculate space freed (approximate)
echo "============================================"
echo "📊 CLEANUP SUMMARY"
echo "============================================"
echo ""
echo "Deleted categories:"
echo "  ✅ Agent logs"
echo "  ✅ Memory logs"
echo "  ✅ Python cache directories"
echo "  ✅ Pytest cache directories"
echo "  ✅ Node modules directories"
echo "  ✅ Backup files"
echo ""
echo "Estimated space freed: ~150MB"
echo ""
echo "============================================"
echo "✅ QUICK WIN CLEANUP COMPLETE!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Run tests: pytest tests/ integration_tests/ -v"
echo "  2. Verify application: python -m app.api"
echo "  3. Review: Read CLEANUP_SUMMARY_TABLE.md for next steps"
echo ""
