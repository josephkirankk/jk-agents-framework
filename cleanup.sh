#!/bin/bash
# JK-Agents Framework Cleanup Script
# Based on cleanup_suggestions.md recommendations

echo "🧹 Cleaning JK-Agents Framework temporary files..."
echo "This will remove logs, cache files, test artifacts, and demo data."
echo ""

# Function to get directory size
get_size() {
    if [ -e "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# Show current repo size
echo "📊 Current repository size:"
echo "Total: $(du -sh . 2>/dev/null | cut -f1)"
echo ""

# High Priority - Safe to delete without confirmation
echo "🔥 High Priority Cleanup (safe to delete)..."

echo "  Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name "*.pyo" -delete 2>/dev/null
echo "    ✓ Python cache files removed"

echo "  Removing macOS system files..."
find . -name ".DS_Store" -delete 2>/dev/null
echo "    ✓ .DS_Store files removed"

echo "  Removing log files..."
if [ -d "logs" ]; then
    rm -rf logs/*
    echo "    ✓ logs/ directory cleaned"
fi
rm -f agentlog_*.log 2>/dev/null
rm -f server.log 2>/dev/null
echo "    ✓ Log files removed"

echo "  Removing test artifacts..."
if [ -d "test_checkpoints" ]; then
    rm -rf test_checkpoints/*
    echo "    ✓ test_checkpoints/ cleaned"
fi
if [ -d "test_chroma_db" ]; then
    rm -rf test_chroma_db/*
    echo "    ✓ test_chroma_db/ cleaned"
fi
rm -f test_results*.json 2>/dev/null
rm -f multistep_supervisor_test_results.json 2>/dev/null
rm -f *_test_results.json 2>/dev/null
echo "    ✓ Test artifacts removed"

# Medium Priority - Confirm before deleting
echo ""
echo "📋 Medium Priority Cleanup (requires confirmation)..."

# Demo data cleanup
if [ -d "demo_data" ] || [ -d "demo_core_flow" ] || [ -d "demo_multi_agent" ]; then
    echo "  Demo data directories found:"
    [ -d "demo_data" ] && echo "    - demo_data/ ($(get_size demo_data))"
    [ -d "demo_core_flow" ] && echo "    - demo_core_flow/ ($(get_size demo_core_flow))"
    [ -d "demo_multi_agent" ] && echo "    - demo_multi_agent/ ($(get_size demo_multi_agent))"
    
    read -p "  Remove demo data folders? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        [ -d "demo_data/large_files" ] && rm -rf demo_data/large_files/*
        [ -d "demo_core_flow/large_files" ] && rm -rf demo_core_flow/large_files/*
        [ -d "demo_multi_agent/large_files" ] && rm -rf demo_multi_agent/large_files/*
        [ -d "demo_data" ] && rm -rf demo_data/*
        [ -d "demo_core_flow" ] && rm -rf demo_core_flow/*
        [ -d "demo_multi_agent" ] && rm -rf demo_multi_agent/*
        echo "    ✓ Demo data removed"
    else
        echo "    ⏭ Demo data kept"
    fi
fi

# ChromaDB development data
if [ -d "chroma_memory" ] || [ -d "advanced_agent_memory" ]; then
    echo "  Development ChromaDB data found:"
    [ -d "chroma_memory" ] && echo "    - chroma_memory/ ($(get_size chroma_memory))"
    [ -d "advanced_agent_memory" ] && echo "    - advanced_agent_memory/ ($(get_size advanced_agent_memory))"
    
    read -p "  Remove development ChromaDB data? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        [ -d "chroma_memory" ] && rm -rf chroma_memory/*
        [ -d "advanced_agent_memory" ] && rm -rf advanced_agent_memory/*
        echo "    ✓ ChromaDB data removed"
    else
        echo "    ⏭ ChromaDB data kept"
    fi
fi

# Backup files
if [ -f ".env.backup" ]; then
    echo "  Found .env.backup file"
    read -p "  Remove .env.backup? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f .env.backup
        echo "    ✓ .env.backup removed"
    else
        echo "    ⏭ .env.backup kept"
    fi
fi

# Validation reports
if ls validation_report_*.md 1> /dev/null 2>&1; then
    echo "  Found validation report files"
    read -p "  Remove validation reports? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f validation_report_*.md
        echo "    ✓ Validation reports removed"
    else
        echo "    ⏭ Validation reports kept"
    fi
fi

# Optional: Virtual environment (dangerous)
if [ -d ".venv" ]; then
    echo ""
    echo "⚠️  Virtual environment found (.venv/)"
    echo "    Size: $(get_size .venv)"
    echo "    WARNING: You'll need to recreate it with 'python -m venv .venv'"
    read -p "  Remove virtual environment? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        echo "    ✓ Virtual environment removed"
        echo "    ⚠️  Remember to recreate: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    else
        echo "    ⏭ Virtual environment kept"
    fi
fi

# Node modules (if present)
if [ -d "node_modules" ]; then
    echo ""
    echo "📦 Node modules found ($(get_size node_modules))"
    echo "    Note: These may be needed for MCP servers"
    read -p "  Remove node_modules? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf node_modules
        echo "    ✓ node_modules removed"
        echo "    ⚠️  If needed for MCP, reinstall with 'npm install'"
    else
        echo "    ⏭ node_modules kept"
    fi
fi

echo ""
echo "✨ Cleanup complete!"
echo "📊 New repository size: $(du -sh . 2>/dev/null | cut -f1)"
echo ""
echo "💡 Next steps:"
echo "  1. Check that your application still works"
echo "  2. Consider adding a 'make clean' target for regular cleanup"
echo "  3. Review .gitignore to prevent future accumulation"
echo ""