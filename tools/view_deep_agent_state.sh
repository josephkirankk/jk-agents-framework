#!/bin/bash
# Script to view Deep Agent state
# Usage: ./view_deep_agent_state.sh <thread_id> [memory_path]

# Default values
THREAD_ID=$1
MEMORY_PATH=${2:-"./serp_memory"}
COLLECTION="serp-checkpoints"

# Check if thread ID is provided
if [ -z "$THREAD_ID" ]; then
    echo "Error: Thread ID is required."
    echo "Usage: ./view_deep_agent_state.sh <thread_id> [memory_path]"
    exit 1
fi

# Get thread path
THREAD_PATH="$MEMORY_PATH/$THREAD_ID"
if [ ! -d "$THREAD_PATH" ]; then
    THREAD_PATH="$MEMORY_PATH"
fi

# Check if database exists
DB_PATH="$THREAD_PATH/chroma.sqlite3"
if [ ! -f "$DB_PATH" ]; then
    echo "Error: ChromaDB database not found at $DB_PATH"
    exit 1
fi

# Use sqlite3 to query the database
echo "Querying database at $DB_PATH for thread $THREAD_ID..."
echo "SELECT document FROM embeddings WHERE collection_id = '$COLLECTION' AND metadata LIKE '%\"thread_id\":\"$THREAD_ID\"%' LIMIT 1;" | sqlite3 "$DB_PATH"

echo "Done."
