#!/bin/bash
# Google Models Listing Program - Linux/Mac Shell Script
# This script sets up the environment and runs the Google models listing program

echo "========================================"
echo "Google Models Listing Program"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        echo "Make sure Python 3 is installed"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if Google API key is set
if [ -z "$GOOGLE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo
    echo "WARNING: No API key found!"
    echo "Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable"
    echo
    echo "Example:"
    echo "  export GOOGLE_API_KEY=your_api_key_here"
    echo
    echo "Or get an API key from: https://aistudio.google.com/"
    echo
    echo "Running demo version instead..."
    echo
    python test_google_models_demo.py
    exit 0
fi

# Install required packages
echo "Installing required packages..."
pip install -q google-genai aiohttp requests python-dotenv

# Run the main program
echo
echo "Running Google Models Listing Program..."
echo
python list_google_models.py

echo
echo "Program completed. Check the generated files:"
echo "- JSON file: google_models_*.json"
echo "- Log file: google_models_list_*.log"
echo
