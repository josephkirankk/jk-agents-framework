#!/bin/bash

# Quick test script for OCR endpoint with your images

echo "🔍 Testing Fast OCR Endpoint"
echo "=============================="
echo ""

# Check if server is running
echo "Checking if server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running. Please start it with:"
    echo "   python -m uvicorn api:app --reload"
    exit 1
fi

echo ""
echo "📤 Sending OCR request with 2 images..."
echo ""

curl --location 'http://localhost:8000/ocr/fast' \
  --form 'files=@"/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 20.56.07.jpeg"' \
  --form 'files=@"/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 20.56.08.jpeg"' \
  | python -m json.tool

echo ""
echo "✅ Test complete!"
