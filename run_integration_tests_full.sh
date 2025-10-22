#!/bin/bash
# Integration Tests Runner Script
# This script sets up the environment and runs all integration tests

set -e  # Exit on error

echo "================================"
echo "Integration Tests Setup & Runner"
echo "================================"
echo ""

# Navigate to project root
cd "$(dirname "$0")"

echo "✓ Project root: $(pwd)"
echo ""

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    uv venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Verify Python
echo "✓ Python version: $(python --version)"
echo ""

# Check if requirements are installed
echo "Checking dependencies..."
if ! python -c "import langchain" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing from requirements.txt..."
    uv pip install -r requirements.txt
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Please create .env file from .env.example and add your credentials."
    echo "   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT"
    exit 1
fi
echo "✓ .env file found"
echo ""

# Check Azure OpenAI credentials
echo "Verifying Azure OpenAI credentials..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = [
    'AZURE_OPENAI_ENDPOINT',
    'AZURE_OPENAI_API_KEY',
    'AZURE_OPENAI_DEPLOYMENT',
    'AZURE_OPENAI_API_VERSION'
]

missing = [var for var in required if not os.getenv(var)]

if missing:
    print('❌ Missing credentials:', ', '.join(missing))
    exit(1)
else:
    print('✓ Azure OpenAI credentials configured')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Please set the missing credentials in your .env file"
    exit 1
fi
echo ""

# Check for Deno (required for MCP Python server)
echo "Checking Deno runtime..."
if command -v deno &> /dev/null; then
    echo "✓ Deno found: $(deno --version | head -n 1)"
else
    echo "⚠️  Deno not found (required for Test 2: MCP Python tools)"
    echo "   Install from: https://deno.land/"
    echo "   Test 2 may fail without Deno"
fi
echo ""

# Run tests
echo "================================"
echo "Starting Integration Tests"
echo "================================"
echo ""

# Parse arguments
if [ "$1" == "--quick" ]; then
    echo "Running QUICK tests only..."
    python integration_tests/run_all_tests.py --quick
elif [ "$1" == "--test" ]; then
    shift
    echo "Running specific tests: $@"
    python integration_tests/run_all_tests.py --test "$@"
else
    echo "Running ALL tests..."
    python integration_tests/run_all_tests.py
fi

exit_code=$?

echo ""
echo "================================"
echo "Tests completed with exit code: $exit_code"
echo "================================"

exit $exit_code
