# Deep Agent Inspection Guide

## Issue Summary

**Problem:** The thread ID `jk-deep-pep-027` was not found in the ChromaDB storage.

**Root Cause:** The thread either:
1. Doesn't exist in the database
2. Is stored with a different thread ID format (e.g., UUID)
3. Is in a different memory directory than expected

## Solution

I've created comprehensive tools to help you find and inspect Deep Agent threads.

---

## Step-by-Step Guide

### Step 1: Activate Virtual Environment

**ALWAYS** use the `.venv` virtual environment:

```bash
source .venv/bin/activate
```

### Step 2: Find All Available Threads

Run the diagnostic tool to scan all memory directories:

```bash
python tools/diagnose_deep_agent_storage.py
```

This will:
- Scan all memory directories (`serp_memory`, `jk_agents_memory`, etc.)
- List all ChromaDB databases found
- Extract and display all thread IDs
- Show statistics about each database

### Step 3: Inspect a Specific Thread

Once you have the thread ID from Step 2, view its state:

```bash
# Text output
python tools/deep_agent_inspector.py --thread-id <actual-thread-id>

# HTML report
python tools/deep_agent_inspector.py --export-html <actual-thread-id> --output report.html

# CSV export
python tools/deep_agent_inspector.py --export-csv <actual-thread-id> --output-dir ./exports
```

---

## Tools Overview

### 1. `diagnose_deep_agent_storage.py` ⭐ **RECOMMENDED**

**Purpose:** Find all threads across all memory directories

**Usage:**
```bash
source .venv/bin/activate
python tools/diagnose_deep_agent_storage.py
```

**Output Example:**
```
================================================================================
DEEP AGENT STORAGE DIAGNOSTIC
================================================================================

Base directory: /Users/.../jk-agents-core

Scanning for ChromaDB databases...

================================================================================
SUMMARY
================================================================================

📊 Found 3 ChromaDB database(s) in 2 directory/directories

📁 serp_memory/
--------------------------------------------------------------------------------

  Location: serp_memory/
  Size: 937,984 bytes
  Tables: embeddings, collections, segments
  Embeddings: 156
  ✅ Threads found: 2
     - 6de24e7a-997b-4f2e-9023-0c08b8e05e9d
     - user-session-123

================================================================================
FINAL SUMMARY
================================================================================

Total unique threads found: 2

All unique thread IDs:
  - 6de24e7a-997b-4f2e-9023-0c08b8e05e9d
  - user-session-123
```

### 2. `deep_agent_inspector.py`

**Purpose:** View and export Deep Agent state in various formats

**Features:**
- 📊 View conversation history, todo lists, and virtual filesystem
- 📄 Export as HTML report with interactive tabs
- 📁 Export as CSV files for analysis
- 🔍 Multiple output formats (text, JSON, HTML, CSV)

**Usage:**
```bash
source .venv/bin/activate

# View state
python tools/deep_agent_inspector.py --thread-id <thread_id>

# Export HTML report
python tools/deep_agent_inspector.py --export-html <thread_id> --output report.html

# Export CSV
python tools/deep_agent_inspector.py --export-csv <thread_id> --output-dir ./exports
```

### 3. `deep_agent_state_viewer.py`

**Purpose:** Simple text viewer for Deep Agent state

**Usage:**
```bash
source .venv/bin/activate
python tools/deep_agent_state_viewer.py --thread-id <thread_id>
```

### 4. `find_threads.py`

**Purpose:** Alternative thread finder with simpler output

**Usage:**
```bash
source .venv/bin/activate
python tools/find_threads.py
```

---

## Common Issues and Solutions

### Issue 1: "No checkpoint found for thread_id"

**Cause:** The thread ID doesn't exist or is incorrect

**Solution:**
1. Run `diagnose_deep_agent_storage.py` to find actual thread IDs
2. Use the exact thread ID from the diagnostic output
3. Check if you're using the correct memory path

### Issue 2: Import errors (`ModuleNotFoundError`)

**Cause:** Not using the virtual environment or missing dependencies

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install missing dependencies if needed
uv pip install langchain langchain_community chromadb sentence-transformers
```

### Issue 3: "No threads found"

**Cause:** No Deep Agent sessions have been created yet, or they're in a different location

**Solution:**
1. Check other memory directories: `jk_agents_memory/`, `youtube_memory/`, etc.
2. Run a Deep Agent session first to create checkpoint data
3. Verify the memory path in your Deep Agent configuration

---

## Memory Storage Locations

Deep Agent checkpoints are stored in ChromaDB databases located in:

```
./serp_memory/chroma.sqlite3           # Default for Serper-based agents
./jk_agents_memory/chroma.sqlite3       # General purpose agents
./youtube_memory/chroma.sqlite3         # YouTube-related agents
./chroma_memory/chroma.sqlite3          # Alternative location
./test_memory/chroma.sqlite3            # Test sessions
```

Each database contains:
- **Conversation history**: All messages between user and agent
- **Todo lists**: Task items with status tracking
- **Virtual filesystem**: Files created during agent execution
- **Metadata**: Timestamps, versions, and configuration

---

## Thread ID Formats

Deep Agents can use different thread ID formats:

1. **Human-readable**: `user-session-123`, `research-quantum`, `jk-deep-pep-027`
2. **UUID format**: `6de24e7a-997b-4f2e-9023-0c08b8e05e9d`
3. **Custom format**: Any string you specify when creating a session

**Important:** The thread ID must be *exactly* as stored in the database. Use the diagnostic tool to find the correct format.

---

## Example Workflow

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Find all available threads
python tools/diagnose_deep_agent_storage.py

# Output shows:
#   - 6de24e7a-997b-4f2e-9023-0c08b8e05e9d
#   - user-session-123

# 3. View a specific thread
python tools/deep_agent_inspector.py --thread-id 6de24e7a-997b-4f2e-9023-0c08b8e05e9d

# 4. Export as HTML for easy viewing
python tools/deep_agent_inspector.py --export-html 6de24e7a-997b-4f2e-9023-0c08b8e05e9d --output analysis.html

# 5. Open the HTML report in your browser
open analysis.html
```

---

## What Was Fixed

1. **Import Issues**: Updated import statements to use `langchain_community` instead of deprecated `langchain.vectorstores`

2. **Error Handling**: Added robust handling for:
   - Empty or missing states
   - Missing thread IDs
   - Database connection errors

3. **Thread Discovery**: Created diagnostic tools to:
   - Scan all memory directories
   - Extract thread IDs from various locations in the database
   - Handle different thread ID formats

4. **User Experience**: Added:
   - Clear error messages
   - Helpful diagnostic output
   - Multiple export formats
   - Comprehensive documentation

---

## Next Steps

1. **Run the diagnostic tool** to find your actual thread IDs
2. **Use the correct thread ID** when inspecting state
3. **Check the HTML reports** for easy visualization
4. **Refer to this guide** if you encounter issues

---

## Support

If you continue to have issues:

1. Check that you're using `.venv`: `which python` should show `.venv/bin/python`
2. Verify dependencies are installed: `pip list | grep langchain`
3. Check the diagnostic output for errors
4. Ensure the memory directory path is correct

---

**Created:** October 22, 2025  
**Tools Location:** `tools/` directory  
**Documentation:** `tools/README.md`
