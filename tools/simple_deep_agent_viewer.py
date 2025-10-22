#!/usr/bin/env python
"""
Simple Deep Agent State Viewer

A simplified version that doesn't rely on external libraries.
This script reads ChromaDB files directly and extracts state information.

Usage:
    python simple_deep_agent_viewer.py --thread-id <thread_id> --memory-path <path>
"""

import os
import sys
import json
import argparse
import sqlite3
from pathlib import Path


def get_thread_path(memory_path, thread_id):
    """Get the path for a specific thread."""
    # Check if thread directory exists directly
    thread_dir = os.path.join(memory_path, thread_id)
    if os.path.exists(thread_dir) and os.path.isdir(thread_dir):
        return thread_dir
        
    # If not found, return base path (for older configurations)
    return memory_path


def list_threads(memory_path):
    """List all available thread IDs."""
    threads = []
    
    # Check for thread directories
    if os.path.exists(memory_path):
        for item in os.listdir(memory_path):
            item_path = os.path.join(memory_path, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "chroma.sqlite3")):
                threads.append(item)
    
    return threads


def read_state_from_sqlite(db_path, thread_id, collection_name="serp-checkpoints"):
    """Read state directly from SQLite database."""
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create query for the thread ID
        config_str = json.dumps({"configurable": {"thread_id": thread_id}})
        
        # Query for the checkpoint
        cursor.execute(
            "SELECT embedding_id, document FROM embeddings WHERE collection_id = ? AND metadata LIKE ?",
            (collection_name, f"%{config_str}%")
        )
        
        result = cursor.fetchone()
        
        if not result:
            print(f"No checkpoint found for thread_id: {thread_id}")
            return {}
            
        # Extract checkpoint data
        document = result[1]
        checkpoint_data = json.loads(document)
        
        # Process and return the state
        return process_state(checkpoint_data)
        
    except Exception as e:
        print(f"Error reading from database: {e}")
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()


def process_state(checkpoint_data):
    """Process and structure the checkpoint data."""
    state = {
        "metadata": {
            "timestamp": checkpoint_data.get("metadata", {}).get("timestamp", "Unknown"),
            "version": checkpoint_data.get("metadata", {}).get("version", "Unknown"),
        },
        "conversation": [],
        "todos": [],
        "files": {},
        "raw_state": checkpoint_data.get("state", {})
    }
    
    # Extract state values
    values = checkpoint_data.get("state", {}).get("values", {})
    
    # Extract conversation history
    if "messages" in values:
        messages = values["messages"]
        if isinstance(messages, list):
            state["conversation"] = [
                {
                    "role": msg.get("type", "unknown"),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("additional_kwargs", {}).get("timestamp", "")
                }
                for msg in messages
            ]
    
    # Extract todo list
    if "todos" in values:
        todos = values["todos"]
        if isinstance(todos, list):
            state["todos"] = todos
    
    # Extract filesystem
    if "files" in values:
        files = values["files"]
        if isinstance(files, dict):
            state["files"] = files
    
    return state


def format_state_as_text(state, thread_id):
    """Format state as human-readable text."""
    if "error" in state:
        return f"Error retrieving state for thread '{thread_id}': {state['error']}"
    
    if not state:
        return f"No checkpoint data found for thread ID: {thread_id}"
    
    # Initialize state with default values
    state_with_defaults = {
        "metadata": state.get("metadata", {"timestamp": "Unknown", "version": "Unknown"}),
        "conversation": state.get("conversation", []),
        "todos": state.get("todos", []),
        "files": state.get("files", {}),
    }
    
    output = []
    output.append("=" * 80)
    output.append(f"DEEP AGENT STATE: {thread_id}")
    output.append("=" * 80)
    
    # Metadata
    output.append("\n## METADATA")
    output.append(f"Timestamp: {state_with_defaults['metadata'].get('timestamp', 'Unknown')}")
    output.append(f"Version: {state_with_defaults['metadata'].get('version', 'Unknown')}")
    
    # Conversation
    output.append("\n## CONVERSATION HISTORY")
    if state_with_defaults["conversation"]:
        for i, msg in enumerate(state_with_defaults["conversation"]):
            output.append(f"\n[{i+1}] {msg['role'].upper()}:")
            output.append(f"{msg['content']}")
    else:
        output.append("No conversation history found.")
    
    # Todo List
    output.append("\n## TODO LIST")
    if state_with_defaults["todos"]:
        for todo in state_with_defaults["todos"]:
            status = todo.get("status", "unknown")
            content = todo.get("content", "No description")
            todo_id = todo.get("id", "unknown")
            output.append(f"- [{status}] {content} (ID: {todo_id})")
    else:
        output.append("No todo items found.")
    
    # Files
    output.append("\n## VIRTUAL FILESYSTEM")
    if state_with_defaults["files"]:
        for path, content in state_with_defaults["files"].items():
            output.append(f"\n### File: {path}")
            output.append(f"Size: {len(content)} characters")
            
            # Show preview for text files
            if len(content) > 500:
                output.append("Content (first 500 chars):")
                output.append(f"{content[:500]}...")
            else:
                output.append("Content:")
                output.append(f"{content}")
    else:
        output.append("No files found.")
    
    return "\n".join(output)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Simple Deep Agent State Viewer")
    parser.add_argument("--thread-id", type=str, help="Thread ID to retrieve")
    parser.add_argument("--memory-path", type=str, default="./serp_memory", 
                        help="Path to ChromaDB memory directory")
    parser.add_argument("--collection", type=str, default="serp-checkpoints",
                        help="ChromaDB collection name")
    parser.add_argument("--list-threads", action="store_true", 
                        help="List available threads")
    parser.add_argument("--output", type=str, help="Output file")
    
    args = parser.parse_args()
    
    # List threads if requested
    if args.list_threads:
        threads = list_threads(args.memory_path)
        if threads:
            print("Available threads:")
            for thread in threads:
                print(f"- {thread}")
        else:
            print("No threads found.")
        return 0
    
    # Check if thread ID is provided
    if not args.thread_id:
        print("Error: Thread ID is required. Use --thread-id <id> or --list-threads to see available threads.")
        return 1
    
    # Get thread path
    thread_path = get_thread_path(args.memory_path, args.thread_id)
    db_path = os.path.join(thread_path, "chroma.sqlite3")
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: ChromaDB database not found at {db_path}")
        return 1
    
    # Get state for the thread
    state = read_state_from_sqlite(db_path, args.thread_id, args.collection)
    
    # Format state as text
    output = format_state_as_text(state, args.thread_id)
    
    # Write to file or stdout
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
