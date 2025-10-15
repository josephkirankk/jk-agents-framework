#!/bin/bash

# Startup script for OCR API
# Runs the lightweight OCR API on port 8001

echo "🚀 Starting OCR API..."
echo "📍 Port: 8001"
echo "📝 Docs: http://localhost:8001/docs"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create it with necessary API keys."
    echo ""
fi

# Run OCR API
uvicorn ocr_api:app --reload --host 0.0.0.0 --port 8001
