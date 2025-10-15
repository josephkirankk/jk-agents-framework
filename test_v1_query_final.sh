#!/bin/bash

# Test script for v1/query endpoint with visiting card extractor
# This should work with your exact file paths

echo "🚀 Testing v1/query endpoint with visiting card extractor"
echo "========================================================"

# Your exact file paths
IMAGE_PATH1="/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"
IMAGE_PATH2="/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"

# Check if files exist
if [[ ! -f "$IMAGE_PATH1" ]]; then
    echo "❌ First image file not found: $IMAGE_PATH1"
    exit 1
fi

if [[ ! -f "$IMAGE_PATH2" ]]; then
    echo "❌ Second image file not found: $IMAGE_PATH2"
    exit 1
fi

echo "✅ Both image files found"
echo "📁 File 1: $(basename "$IMAGE_PATH1")"
echo "📁 File 2: $(basename "$IMAGE_PATH2")"
echo ""

# Test the API endpoint
echo "🌐 Making request to v1/query endpoint..."
echo ""

curl --location 'http://localhost:8000/v1/query' \
  --form 'question="Extract complete data including company research"' \
  --form 'config_name="visiting_card_extractor.yaml"' \
  --form "file=@\"$IMAGE_PATH1\"" \
  --form "file=@\"$IMAGE_PATH2\"" \
  --write-out "\n📊 HTTP Status: %{http_code}\n⏱️  Total Time: %{time_total}s\n" \
  --verbose

echo ""
echo "✅ Test completed!"
echo ""
echo "Expected results:"
echo "- HTTP Status: 200 (success)"
echo "- Response: JSON with extracted visiting card data"
echo "- Processing time: 25-40 seconds for full extraction"
