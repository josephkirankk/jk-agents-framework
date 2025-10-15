#!/bin/bash
# Test script for the v1/query endpoint with file uploads

echo "Testing v1/query endpoint with visiting card extractor"
echo "========================================================"

# Replace these paths with actual image files you want to test with
IMAGE_PATH1="/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"
IMAGE_PATH2="/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"

# Ensure the API server is running before executing this script
curl --location 'http://localhost:8000/v1/query' \
  --form 'question="Extract complete data including company research"' \
  --form 'config_name="visiting_card_extractor.yaml"' \
  --form "file=@\"$IMAGE_PATH1\"" \
  --form "file=@\"$IMAGE_PATH2\""

echo ""
echo "Test complete"
