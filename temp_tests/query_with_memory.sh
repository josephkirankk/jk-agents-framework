#!/bin/bash
# Helper script to maintain conversation memory across requests
# Usage: ./query_with_memory.sh "your question here" [config_path]

set -e

# Configuration
THREAD_FILE=".current_thread_id"
DEFAULT_CONFIG="config/python_exec_agent_working.yaml"
BASE_URL="http://localhost:8000"

# Get config path from argument or use default
CONFIG_PATH="${2:-$DEFAULT_CONFIG}"

# Check if input is provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"your question\" [config_path]"
    echo ""
    echo "Examples:"
    echo "  $0 \"print 1 to 10\""
    echo "  $0 \"write fibonacci for each number here\""
    echo "  $0 \"your question\" \"config/youtube_creative_team.yaml\""
    echo ""
    echo "To start a new conversation:"
    echo "  rm $THREAD_FILE"
    exit 1
fi

INPUT="$1"

# Get or create thread_id
if [ -f "$THREAD_FILE" ]; then
    THREAD_ID=$(cat "$THREAD_FILE")
    echo "📝 Using existing conversation: $THREAD_ID"
else
    THREAD_ID="session-$(date +%s)"
    echo "$THREAD_ID" > "$THREAD_FILE"
    echo "🆕 Started new conversation: $THREAD_ID"
fi

echo "📤 Sending: $INPUT"
echo "⚙️  Config: $CONFIG_PATH"
echo ""

# Make request
RESPONSE=$(curl -s --location "$BASE_URL/query/form" \
  --form "input=\"$INPUT\"" \
  --form "config_path=\"$CONFIG_PATH\"" \
  --form 'raw_output="True"' \
  --form "thread_id=\"$THREAD_ID\"")

# Display response
echo "📥 Response:"
echo "----------------------------------------"
echo "$RESPONSE"
echo "----------------------------------------"
echo ""

# Show conversation file info
CONV_FILE="simple_memory/$THREAD_ID.json"
if [ -f "$CONV_FILE" ]; then
    TURN_COUNT=$(cat "$CONV_FILE" | python -c "import sys, json; data=json.load(sys.stdin); print(len([m for m in data['messages'] if m['role']=='user']))")
    echo "💾 Conversation saved: $TURN_COUNT turn(s) in memory"
    echo "📂 File: $CONV_FILE"
else
    echo "⚠️  Warning: Conversation file not found at $CONV_FILE"
fi

echo ""
echo "💡 Tip: Run 'rm $THREAD_FILE' to start a new conversation"
