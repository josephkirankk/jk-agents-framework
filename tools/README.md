# Deep Agent Inspection Tools

This directory contains tools for inspecting and analyzing Deep Agent state data.

## Quick Start

**IMPORTANT:** Always use the `.venv` virtual environment when running these tools:

```bash
# Activate virtual environment
source .venv/bin/activate

# RECOMMENDED: Use the new ChromaDB checker (works with all versions)
python tools/check_chromadb_data.py

# View a specific thread
python tools/deep_agent_inspector.py --thread-id <thread_id>
```

**Quick Check:**
```bash
chmod +x tools/quick_check.sh
./tools/quick_check.sh
```

## Available Tools

### 1. **Diagnostic Tool** (`diagnose_deep_agent_storage.py`) ⭐ **START HERE**

Scans all memory directories and finds available threads.

**Usage:**
```bash
source .venv/bin/activate
python tools/diagnose_deep_agent_storage.py
```

**Output:**
- Lists all ChromaDB databases found
- Shows all available thread IDs
- Provides statistics about each database

### 2. Deep Agent Inspector (`deep_agent_inspector.py`)

A comprehensive tool with rich visualization and export options.

**Features:**
- View conversation history, todo list, and filesystem
- Export as HTML report with interactive tabs
- Export as CSV files for data analysis
- Multiple output formats (text, JSON, HTML, CSV)

**Usage:**
```bash
source .venv/bin/activate

# View state for a specific thread
python tools/deep_agent_inspector.py --thread-id <thread_id>

# List available threads (shows directories only, not actual thread IDs)
python tools/deep_agent_inspector.py --list-threads

# Export as HTML report
python tools/deep_agent_inspector.py --export-html <thread_id> --output report.html

# Export as CSV files
python tools/deep_agent_inspector.py --export-csv <thread_id> --output-dir ./exports

# Output as JSON
python tools/deep_agent_inspector.py --thread-id <thread_id> --format json

# Specify custom memory path
python tools/deep_agent_inspector.py --thread-id <thread_id> --memory-path ./custom_memory
```

### 3. Deep Agent State Viewer (`deep_agent_state_viewer.py`)

A simple command-line tool to view the state of a Deep Agent thread.

**Features:**
- View conversation history
- View todo list items
- View virtual filesystem contents
- Output in text or JSON format

**Usage:**
```bash
source .venv/bin/activate

# View state for a specific thread
python tools/deep_agent_state_viewer.py --thread-id <thread_id>

# List available threads
python tools/deep_agent_state_viewer.py --list-threads

# Specify custom memory path
python tools/deep_agent_state_viewer.py --thread-id <thread_id> --memory-path ./custom_memory

# Output as JSON
python tools/deep_agent_state_viewer.py --thread-id <thread_id> --output-format json
```

### 4. Find Threads (`find_threads.py`)

Searches all memory directories and lists thread IDs found in ChromaDB databases.

**Usage:**
```bash
source .venv/bin/activate
python tools/find_threads.py
```

## How It Works

These tools connect to the ChromaDB storage used by Deep Agents to persist conversation state. They retrieve and parse the checkpoint data, extracting:

1. **Conversation History**: All messages exchanged between the user and agent
2. **Todo List**: Task items created by the TodoListMiddleware
3. **Virtual Filesystem**: Files created by the FilesystemMiddleware
4. **Metadata**: Timestamp, version, and other state information

## Storage Location

By default, these tools look for Deep Agent state in `./serp_memory`. This can be customized with the `--memory-path` option.

The state is stored in thread-specific directories:
```
./serp_memory/
├── <thread-id-1>/
│   └── chroma.sqlite3
├── <thread-id-2>/
│   └── chroma.sqlite3
└── ...
```

## Requirements

- Python 3.8+
- LangChain
- ChromaDB
- HuggingFace Embeddings

Dependencies will be automatically installed if missing.

## Examples

### View Thread State

```bash
python deep_agent_inspector.py --thread-id research-quantum
```

### Generate HTML Report

```bash
python deep_agent_inspector.py --export-html research-quantum --output quantum_report.html
```

### Export All Data for Analysis

```bash
python deep_agent_inspector.py --export-csv research-quantum --output-dir ./analysis_data
```

### List All Available Threads

```bash
python deep_agent_inspector.py --list-threads
```

## Troubleshooting

If you encounter issues:

1. **No threads found**: Check that the memory path is correct with `--memory-path`
2. **Connection errors**: Ensure ChromaDB is installed (`pip install chromadb`)
3. **Missing dependencies**: The tools will attempt to install required packages automatically
