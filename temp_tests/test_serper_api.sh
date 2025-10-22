#!/bin/bash
# Test Serper API Key Validity

echo "=========================================="
echo "SERPER API KEY VALIDATION TEST"
echo "=========================================="
echo ""

# Load .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ ERROR: .env file not found"
    exit 1
fi

# Check if key exists
if [ -z "$SERPER_API_KEY" ]; then
    echo "❌ ERROR: SERPER_API_KEY not found in .env"
    echo "   Please add: SERPER_API_KEY=your_key_here"
    exit 1
fi

# Check if it's placeholder
if [ "$SERPER_API_KEY" = "your-serper-api-key-here" ]; then
    echo "❌ ERROR: SERPER_API_KEY is still the placeholder"
    echo "   Get your key from: https://serper.dev"
    exit 1
fi

# Show partial key (first 10 and last 4 chars)
KEY_LEN=${#SERPER_API_KEY}
FIRST_10="${SERPER_API_KEY:0:10}"
LAST_4="${SERPER_API_KEY: -4}"
echo "✓ Found SERPER_API_KEY: ${FIRST_10}...${LAST_4}"
echo "  (Length: $KEY_LEN characters)"
echo ""

# Test the API
echo "Testing API key with Serper API..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST 'https://google.serper.dev/search' \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"q": "test query", "num": 1}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "Response Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS: API key is valid and working!"
    echo "   Your Serper API key is active and ready to use."
elif [ "$HTTP_CODE" = "403" ]; then
    echo "❌ FAILED: 403 Forbidden - Unauthorized"
    echo "   Your API key is invalid or expired."
    echo ""
    echo "   Response: $BODY"
    echo ""
    echo "To fix:"
    echo "1. Go to https://serper.dev"
    echo "2. Sign up or log in"
    echo "3. Get your API key from the dashboard"
    echo "4. Update .env file: SERPER_API_KEY=your_new_key"
    exit 1
elif [ "$HTTP_CODE" = "429" ]; then
    echo "⚠️  WARNING: 429 Too Many Requests"
    echo "   Your API key is valid but rate limit exceeded."
    echo "   This is not a key validity issue."
else
    echo "❌ FAILED: Unexpected status code $HTTP_CODE"
    echo "   Response: $BODY"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All checks passed!"
echo "=========================================="
