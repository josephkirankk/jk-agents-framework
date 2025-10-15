#!/bin/bash
# Run API server with proper environment
# This script activates the virtual environment and runs the API server

# Ensure script is run from the correct directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating new virtual environment with uv..."
    python -m pip install uv
    uv venv -p python .venv
    
    echo "Installing dependencies..."
    source .venv/bin/activate
    uv pip install -r requirements.txt
    uv pip install litellm python-dotenv Pillow
else
    echo "✅ Found virtual environment"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️ No .env file found. Creating from .env.example (please update with real API keys)..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
    else
        echo "❌ No .env.example file found. Creating minimal .env..."
        touch .env
        echo "# API Keys for LiteLLM providers" >> .env
        echo "# OPENAI_API_KEY=your-api-key" >> .env
        echo "# AZURE_API_KEY=your-api-key" >> .env
        echo "# AZURE_API_BASE=https://your-endpoint.openai.azure.com/" >> .env
        echo "# AZURE_API_VERSION=2023-05-15" >> .env
        echo "# GOOGLE_API_KEY=your-api-key" >> .env
    fi
    echo "⚠️ Please edit the .env file with your actual API keys before using"
fi

# Start the API server
echo "🚀 Starting API server..."
python api.py
