#!/bin/bash

echo "================================================================"
echo "File Reference System - Complete Test"
echo "================================================================"
echo ""

# Check if API server is running
echo "Step 1: Checking if API server is running..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ API server is running"
else
    echo "❌ API server is NOT running"
    echo ""
    echo "Please start the API server in another terminal:"
    echo "   python api.py"
    echo ""
    exit 1
fi

echo ""
echo "Step 2: Testing file upload with visiting card extraction..."
echo "================================================================"

# Image paths
IMAGE1="/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"
IMAGE2="/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"

# Check if files exist
if [ ! -f "$IMAGE1" ]; then
    echo "❌ Image 1 not found: $IMAGE1"
    exit 1
fi

if [ ! -f "$IMAGE2" ]; then
    echo "⚠️  Image 2 not found: $IMAGE2"
    echo "   Using only first image"
    IMAGE2=""
fi

echo "📤 Uploading files to v1/query endpoint..."
echo "   - Image 1: $(basename "$IMAGE1")"
if [ -n "$IMAGE2" ]; then
    echo "   - Image 2: $(basename "$IMAGE2")"
fi
echo ""

# Build curl command
CURL_CMD=(
    curl --location 'http://localhost:8000/v1/query'
    --form 'question="Extract complete data including company research"'
    --form 'config_name="visiting_card_extractor.yaml"'
    --form "file=@\"$IMAGE1\""
)

if [ -n "$IMAGE2" ]; then
    CURL_CMD+=(--form "file=@\"$IMAGE2\"")
fi

# Add output options
CURL_CMD+=(
    --write-out "\n\n📊 HTTP Status: %{http_code}\n⏱️  Total Time: %{time_total}s\n"
    --silent
    --show-error
)

# Execute request
echo "🚀 Sending request..."
echo ""

RESPONSE=$("${CURL_CMD[@]}" 2>&1)
HTTP_CODE=$?

if [ $HTTP_CODE -ne 0 ]; then
    echo "❌ Curl failed with exit code: $HTTP_CODE"
    echo "Response: $RESPONSE"
    exit 1
fi

echo "Response:"
echo "================================================================"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo "================================================================"

# Check if response contains expected data
if echo "$RESPONSE" | grep -q '"success": *true'; then
    echo ""
    echo "✅ Request successful!"
    
    # Check if files were processed
    if echo "$RESPONSE" | grep -q '"files_uploaded"'; then
        FILES_COUNT=$(echo "$RESPONSE" | jq -r '.metadata.files_uploaded // 0' 2>/dev/null)
        echo "   Files uploaded: $FILES_COUNT"
    fi
    
    # Check if OCR agent accessed files
    if echo "$RESPONSE" | grep -q '"file_info"'; then
        echo "   ✅ File reference system working!"
        echo "$RESPONSE" | jq -r '.metadata.file_info[] | "   - \(.filename) (ref: \(.reference_id))"' 2>/dev/null
    fi
    
    # Check response content
    if echo "$RESPONSE" | grep -q -i "please provide"; then
        echo ""
        echo "⚠️  WARNING: OCR agent asked for file upload"
        echo "   This means files were not retrieved via reference IDs"
    elif echo "$RESPONSE" | grep -q -i "no company name\|no contact"; then
        echo ""
        echo "⚠️  WARNING: No data extracted"
        echo "   OCR agent may not have accessed files"
    else
        echo ""
        echo "✅ OCR agent successfully processed files!"
    fi
else
    echo ""
    echo "❌ Request failed"
    if echo "$RESPONSE" | grep -q '"error"'; then
        ERROR=$(echo "$RESPONSE" | jq -r '.error // "Unknown error"' 2>/dev/null)
        echo "   Error: $ERROR"
    fi
fi

echo ""
echo "================================================================"
echo "Test complete!"
echo "================================================================"
