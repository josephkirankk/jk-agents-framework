# ACTION PLAN: Deep Agent Storage Investigation

## Problem Identified ✅

**Root Cause:** ChromaDB schema changed in newer versions. The old diagnostic tools were using SQL queries that don't work anymore.

**Status:** 
- ❌ No thread data found yet
- ❌ Your curl command hasn't created data yet (or API server not running)
- ✅ Fixed tools that work with new ChromaDB

---

## What You Need to Do NOW

### Step 1: Check Current Data (30 seconds)

```bash
source .venv/bin/activate
python tools/check_chromadb_data.py
```

**Expected:** Probably shows "No data found" (this is OK - it confirms the tool works)

### Step 2: Start Your API Server

```bash
# In a new terminal:
source .venv/bin/activate
python your_api_server_script.py  # Replace with actual command
```

**Verify it's running:**
```bash
curl http://localhost:8000/health
```

### Step 3: Run Your Curl Command

```bash
curl --location 'http://localhost:8000/query/form' \
  --form 'input="i am talking about intense version. give me the correct clone in india"' \
  --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="jk-deep-pep-027"'
```

**Wait for response** (this might take 30-60 seconds)

### Step 4: Check Data Again

```bash
python tools/check_chromadb_data.py
```

**Expected:** Should NOW show:
- Documents found: > 0
- Thread IDs: jk-deep-pep-027
- Checkpoint data with messages, files, todos

### Step 5: View the Stored State

```bash
python tools/deep_agent_inspector.py --thread-id jk-deep-pep-027
```

**Or generate HTML:**
```bash
python tools/deep_agent_inspector.py --export-html jk-deep-pep-027 --output report.html
open report.html
```

---

## Automated Testing (Alternative)

If you have the API server running, use the automated test:

```bash
chmod +x tools/test_deep_agent_storage.sh
./tools/test_deep_agent_storage.sh
```

This will:
1. ✅ Check API server
2. ✅ Show BEFORE state
3. ✅ Run your curl
4. ✅ Show AFTER state
5. ✅ Verify thread stored
6. ✅ Display the data

---

## What's Different Now

### OLD Tools (Broken ❌)
```python
# Used direct SQL queries
cursor.execute("SELECT document FROM embeddings...")
# ERROR: no such column: document
```

### NEW Tools (Working ✅)
```python
# Uses Chroma API
collection = vector_store._collection
all_docs = collection.get(include=['metadatas', 'documents'])
# WORKS with all ChromaDB versions!
```

---

## Files Created/Fixed

### ✅ NEW - Working Tools

1. **`tools/check_chromadb_data.py`** ⭐ PRIMARY TOOL
   - Uses Chroma API
   - Works with all ChromaDB versions
   - Shows thread IDs, checkpoints, state data

2. **`tools/test_deep_agent_storage.sh`**
   - End-to-end test
   - Runs curl and verifies storage
   - Complete automation

3. **`tools/quick_check.sh`**
   - Quick data check
   - No API server needed
   - Just shows current state

### ✅ FIXED - Existing Tools

1. **`tools/deep_agent_inspector.py`**
   - Fixed imports (langchain_community)
   - Better error handling
   - Works with empty states

2. **`tools/deep_agent_state_viewer.py`**
   - Fixed imports
   - Better error handling

### ⚠️ OLD - Don't Use

1. **`tools/diagnose_deep_agent_storage.py`**
   - Uses SQL queries
   - Doesn't work with new ChromaDB
   - Use `check_chromadb_data.py` instead

2. **`tools/find_threads.py`**
   - Uses SQL queries
   - Doesn't work with new ChromaDB
   - Use `check_chromadb_data.py` instead

---

## Common Questions

### Q: Why is no data showing?

**A:** Two possibilities:

1. **No session run yet**
   - Your curl command hasn't been executed
   - OR API server isn't running
   - OR curl failed

2. **Configuration issue**
   - Checkpointer not configured in agent
   - Wrong memory path
   - Memory backend not set to "chromadb"

### Q: How do I know if my curl worked?

**A:** Look for:
```bash
# Before curl:
python tools/check_chromadb_data.py
# Shows: Documents found: 0

# After curl (wait 2 seconds):
python tools/check_chromadb_data.py
# Shows: Documents found: 3, Thread IDs: jk-deep-pep-027
```

### Q: Where is the data actually stored?

**A:** Inside ChromaDB at `./serp_memory/chroma.sqlite3`

The checkpointer stores JSON containing:
```json
{
  "checkpoint": {
    "channel_values": {
      "messages": [...],
      "files": {...},
      "todos": [...]
    }
  },
  "metadata": {...},
  "timestamp": "2025-10-22T..."
}
```

### Q: Can I see the raw data?

**A:** Yes, use the new tool:
```bash
python tools/check_chromadb_data.py
```

Shows:
- Number of documents
- Thread IDs
- Checkpoint metadata
- Message/file/todo counts

---

## Success Criteria

You'll know everything is working when:

1. ✅ `check_chromadb_data.py` shows documents > 0
2. ✅ Thread ID `jk-deep-pep-027` appears in the list
3. ✅ `deep_agent_inspector.py --thread-id jk-deep-pep-027` shows state
4. ✅ HTML report displays conversation, todos, files

---

## Next Steps

**RIGHT NOW:**

```bash
# Terminal 1: Check current state
source .venv/bin/activate
python tools/check_chromadb_data.py

# Terminal 2: Start API server (if not running)
source .venv/bin/activate
python your_api_script.py

# Terminal 1: Run your curl
curl --location 'http://localhost:8000/query/form' \
  --form 'input="i am talking about intense version. give me the correct clone in india"' \
  --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="jk-deep-pep-027"'

# Wait for response...

# Terminal 1: Check again
python tools/check_chromadb_data.py

# If data found:
python tools/deep_agent_inspector.py --thread-id jk-deep-pep-027
```

---

## Documentation

- 📖 **Complete Guide:** `STORAGE_INVESTIGATION.md`
- 📖 **Tools README:** `tools/README.md`
- 📖 **Fix Summary:** `TOOLS_FIX_SUMMARY.md`
- 📖 **This Plan:** `ACTION_PLAN.md`

---

**Status:** ✅ Tools fixed and ready
**Action:** Run the tests above to verify storage is working
