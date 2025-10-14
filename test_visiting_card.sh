#!/bin/bash

# Test script for visiting card extractor
# Usage: ./test_visiting_card.sh path/to/card1.jpg path/to/card2.jpg

set -e

API_URL="http://localhost:8000/v1/query"
CONFIG="visiting_card_extractor.yaml"

# Check if files are provided
if [ $# -eq 0 ]; then
    echo "ERROR: No files provided!"
    echo ""
    echo "Usage: $0 <image1> [image2] [image3] ..."
    echo ""
    echo "Example:"
    echo "  $0 card_front.jpg card_back.jpg"
    echo ""
    echo "Note: Place your visiting card images in the project directory first,"
    echo "      or provide full paths to the images."
    exit 1
fi

# Check if files exist
for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: File not found: $file"
        exit 1
    fi
    echo "✓ Found: $file ($(du -h "$file" | cut -f1))"
done

echo ""
echo "Testing Visiting Card Extractor"
echo "================================"
echo "API URL: $API_URL"
echo "Config: $CONFIG"
echo "Files: $#"
echo ""

# Build curl command
CURL_CMD="curl -X POST \"$API_URL\""
CURL_CMD="$CURL_CMD -F \"question=Extract complete data including company research\""
CURL_CMD="$CURL_CMD -F \"config_name=$CONFIG\""

# Add each file
for file in "$@"; do
    CURL_CMD="$CURL_CMD -F \"file=@$file\""
done

echo "Executing request..."
echo ""

# Execute
eval $CURL_CMD 2>&1 | python3 -m json.tool || echo "(Response was not valid JSON, showing raw output above)"

echo ""
echo "Done!"