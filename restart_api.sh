#!/bin/bash
# Restart API script
# Stops the API if running and starts it again, then waits for it to be ready

echo "🔄 Restarting API server on port 8000..."

# Function to check if server is ready
check_server_ready() {
    if curl -s --max-time 5 http://localhost:8000/docs > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Stop the API if it's running
echo "🛑 Stopping existing API server..."
PID=$(lsof -ti :8000)
if [ -n "$PID" ]; then
    echo "Found process $PID on port 8000, killing it..."
    kill $PID
    # Wait a bit for it to stop
    sleep 2
    # Force kill if still running
    if kill -0 $PID 2>/dev/null; then
        echo "Force killing process $PID..."
        kill -9 $PID
    fi
    echo "✅ API server stopped"
else
    echo "ℹ️ No API server found running on port 8000"
fi

# Start the API server in background
echo "🚀 Starting API server..."
bash run_api_server.sh &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
MAX_WAIT=60  # 60 seconds timeout
WAIT_COUNT=0

while ! check_server_ready; do
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo "❌ Server failed to start within $MAX_WAIT seconds"
        exit 1
    fi
    echo "   Waiting... ($((WAIT_COUNT + 1))/$MAX_WAIT)"
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

echo "✅ API server is ready and running on port 8000!"
echo "🌐 Server PID: $SERVER_PID"
echo "📚 API docs available at: http://localhost:8000/docs"
