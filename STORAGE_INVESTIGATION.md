# Deep Agent Storage Investigation

## Problem Analysis

### What Went Wrong

1. **ChromaDB Schema Changed**: The diagnostic tools were using SQL queries with a `document` column that doesn't exist in newer ChromaDB versions.

2. **Wrong Approach**: The tools were trying to query SQL directly instead of using the Chroma API.

3. **No Data Found**: The thread `jk-deep-pep-027` wasn't found because:
   - No session has been run yet with that thread_id
   - OR the API server isn't running
   - OR the checkpointer isn't saving data properly

### How Deep Agent Storage Works

```
User Request (curl)
    ↓
API Server (localhost:8000)
    ↓
Deep Agent Execution
    ↓
ChromaDB Checkpointer (app/memory/chromadb_checkpointer.py)
    ↓
Chroma.add_texts() - Stores serialized JSON
    ↓
ChromaDB Storage (./serp_memory/chroma.sqlite3)
    ↓
Contains: conversations, todos, files, metadata
```

### Storage Location

Data is stored in: **`./serp_memory/chroma.sqlite3`**

The checkpointer stores:
- **Checkpoint ID**: `thread_{thread_id}`
- **Document**: Serialized JSON containing:
  - `checkpoint`: State data (messages, todos, files)
  - `metadata`: Thread information
  - `timestamp`: When stored
  - `version`: Checkpointer version

### Why SQL Queries Failed

Newer ChromaDB versions (v0.4+) changed the schema:
- ❌ OLD: `embeddings` table with `document` column
- ✅ NEW: `embeddings` table with different structure
- Must use Chroma API instead of direct SQL

---

## Solution: New Tools

### 1. **check_chromadb_data.py** ⭐ PRIMARY TOOL

Uses the Chroma API properly to check data.

**Usage:**
```bash
source .venv/bin/activate
python tools/check_chromadb_data.py --memory-path ./serp_memory
```

**What it does:**
- ✅ Uses Chroma API (works with all versions)
- ✅ Lists all documents and thread IDs
- ✅ Shows checkpoint metadata
- ✅ Parses and displays state information

### 2. **test_deep_agent_storage.sh** - END-TO-END TEST

Runs your curl command and verifies storage.

**Usage:**
```bash
chmod +x tools/test_deep_agent_storage.sh
./tools/test_deep_agent_storage.sh
```

**What it does:**
1. ✅ Checks if API server is running
2. ✅ Shows current state BEFORE
3. ✅ Runs your curl command
4. ✅ Shows current state AFTER
5. ✅ Verifies thread was stored
6. ✅ Displays the stored data

---

## Step-by-Step Testing Guide

### Prerequisites

1. **Start the API Server**
```bash
source .venv/bin/activate
python your_api_server.py  # Replace with your actual server command
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### Test 1: Check Current State

```bash
source .venv/bin/activate
python tools/check_chromadb_data.py
```

**Expected output:**
- Shows number of documents
- Lists thread IDs (if any exist)
- Shows checkpoint details

### Test 2: Run Your Curl Command

```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="i am talking about intense version. give me the correct clone in india"' \
  --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="jk-deep-pep-027"'
```

**Wait for response** - This creates a Deep Agent session

### Test 3: Check State Again

```bash
python tools/check_chromadb_data.py
```

**Expected:**
- Number of documents should increase
- Should see `jk-deep-pep-027` in thread IDs
- Should show checkpoint with messages, files, todos

### Test 4: View the Stored State

```bash
python tools/deep_agent_inspector.py --thread-id jk-deep-pep-027
```

**Or generate HTML report:**
```bash
python tools/deep_agent_inspector.py --export-html jk-deep-pep-027 --output report.html
open report.html
```

---

## Automated End-to-End Test

Run everything automatically:

```bash
chmod +x tools/test_deep_agent_storage.sh
./tools/test_deep_agent_storage.sh
```

This script will:
1. Check API server is running
2. Show current state
3. Run your curl command
4. Show new state
5. Verify thread was stored
6. Display the data

---

## Troubleshooting

### Issue 1: "API server is not running"

**Solution:**
```bash
# Find and start your API server
# Example:
python app/api.py
# or
python main.py
# or
uvicorn app.main:app --reload --port 8000
```

### Issue 2: "No thread data found" after curl

**Possible causes:**

1. **Checkpointer not configured**
   - Check `config/deep_agent_advanced_serpapi.yaml`
   - Ensure memory backend is set to "chromadb"
   - Verify path is correct

2. **Different memory path**
   - Agent might be using a different directory
   - Check: `./jk_agents_memory/`, `./youtube_memory/`, etc.

3. **Checkpointer not enabled**
   - Deep Agent needs a checkpointer passed to it
   - Check your `agent_builder.py` configuration

### Issue 3: "No checkpoint found for thread_id"

**Solution:**
1. Run `check_chromadb_data.py` to see actual thread IDs
2. Use the exact thread ID from the output
3. Thread IDs are case-sensitive

---

## Configuration Check

### Verify Deep Agent Configuration

Check your `config/deep_agent_advanced_serpapi.yaml`:

```yaml
memory:
  backend: "chromadb"  # Must be chromadb, not "memory"
  chromadb:
    path: "./serp_memory"  # Storage location
    checkpoint_collection: "checkpoints"
```

### Verify Agent Builder

Check `app/agent_builder.py` ensures checkpointer is passed:

```python
# Should have something like:
checkpointer = ChromaDBCheckpointer(
    persist_directory=memory_config['chromadb']['path'],
    collection_name=memory_config['chromadb'].get('checkpoint_collection', 'checkpoints')
)

# And passed to Deep Agent:
agent = create_deep_agent(
    checkpointer=checkpointer,  # This is critical!
    ...
)
```

---

## What to Expect

### Successful Storage

When everything works, `check_chromadb_data.py` shows:

```
================================================================================
CHROMADB DATA CHECK RESULTS
================================================================================

📁 Path: ./serp_memory
📦 Collection: checkpoints

📊 Documents found: 3
🔑 Unique thread IDs: 1

Thread IDs:
  ✓ jk-deep-pep-027

📝 Checkpoints (3):
--------------------------------------------------------------------------------

  ID: thread_jk-deep-pep-027
  Thread ID: jk-deep-pep-027
  Type: checkpoint
  Document size: 15240 bytes
  ✓ Contains checkpoint data
    - Messages: 4
    - Files: 2
    - Todos: 3
```

### No Storage (Problem)

If nothing is stored:

```
📊 Documents found: 0
🔑 Unique thread IDs: 0

⚠️  No thread data found.
```

**This means:**
- Agent execution didn't create a checkpoint
- OR checkpointer isn't configured
- OR using wrong memory path

---

## Quick Reference Commands

```bash
# Check what's stored
source .venv/bin/activate
python tools/check_chromadb_data.py

# Run your curl (in another terminal, API must be running)
curl --location 'http://localhost:8000/query/form' \
  --form 'input="test query"' \
  --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="jk-deep-pep-027"'

# Check again
python tools/check_chromadb_data.py

# View the thread
python tools/deep_agent_inspector.py --thread-id jk-deep-pep-027

# Or run full test
./tools/test_deep_agent_storage.sh
```

---

## Summary

1. ✅ **Fixed**: ChromaDB schema issues - now using Chroma API
2. ✅ **Created**: `check_chromadb_data.py` - proper data checker
3. ✅ **Created**: `test_deep_agent_storage.sh` - end-to-end test
4. ⚠️ **Action needed**: Run API server and test with curl command

**Next step:** Run `./tools/test_deep_agent_storage.sh` to test everything!
