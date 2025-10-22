#!/bin/bash
# Quick Serper API Key Test

echo "Testing Serper API Key..."
echo ""

# Read key from .env
if [ -f .env ]; then
    SERPER_KEY=$(grep "^SERPER_API_KEY=" .env | cut -d'=' -f2 | tr -d ' "'"'"'')
    
    if [ -z "$SERPER_KEY" ]; then
        echo "❌ SERPER_API_KEY not found in .env"
        exit 1
    fi
    
    if [ "$SERPER_KEY" = "your-serper-api-key-here" ]; then
        echo "❌ Using placeholder key. Please update with real key from https://serper.dev"
        exit 1
    fi
    
    # Show partial key
    echo "Key found: ${SERPER_KEY:0:10}...${SERPER_KEY: -4} (${#SERPER_KEY} chars)"
    echo ""
    
    # Test API
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST 'https://google.serper.dev/search' \
      -H "X-API-KEY: $SERPER_KEY" \
      -H 'Content-Type: application/json' \
      -d '{"q":"test","num":1}')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ SUCCESS: Key is valid!"
    elif [ "$HTTP_CODE" = "403" ]; then
        echo "❌ FAILED: 403 Forbidden - Invalid key"
        echo "Get new key from: https://serper.dev"
        exit 1
    else
        echo "⚠️  Status: $HTTP_CODE"
    fi
else
    echo "❌ .env file not found"
    exit 1
fi
