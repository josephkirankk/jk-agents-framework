#!/usr/bin/env python
"""
Deep Agent State Viewer

This tool retrieves and displays all information stored for a Deep Agent thread,
including conversation history, todo list, virtual filesystem, and other state data.

Usage:
    python deep_agent_state_viewer.py --thread-id <thread_id> [--memory-path <path>] [--output-format json|text]

Example:
    python deep_agent_state_viewer.py --thread-id user-session-123
    python deep_agent_state_viewer.py --thread-id research-quantum --memory-path ./custom_memory
    python deep_agent_state_viewer.py --thread-id analysis-123 --output-format json > analysis_state.json
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import pprint

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_core.documents import Document
except ImportError:
    print("Required packages not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "langchain", "langchain_community", "chromadb", 
                          "sentence-transformers"])
    
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_core.documents import Document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deep_agent_state_viewer")

class DeepAgentStateViewer:
    """Tool to view Deep Agent state from ChromaDB checkpoints"""
    
    def __init__(self, memory_path: str = "./serp_memory", collection_name: str = "serp-checkpoints"):
        """
        Initialize the state viewer.
        
        Args:
            memory_path: Path to ChromaDB storage directory
            collection_name: Name of the checkpoint collection
        """
        self.memory_path = memory_path
        self.collection_name = collection_name
        self.embedding_function = None
        self.vector_store = None
        
        logger.info(f"Initializing state viewer with memory path: {memory_path}")
        
    def connect(self) -> bool:
        """
        Connect to the ChromaDB store.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Check if directory exists
            if not os.path.exists(self.memory_path):
                logger.error(f"Memory path not found: {self.memory_path}")
                return False
                
            # Initialize embedding function
            self.embedding_function = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Initialize vector store
            thread_path = self.memory_path
            
            # Check if we need to look in thread-specific directory
            if not os.path.exists(os.path.join(thread_path, "chroma.sqlite3")):
                logger.info("No chroma.sqlite3 found in root path, will search in thread subdirectories")
            
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=thread_path
            )
            
            logger.info(f"Connected to ChromaDB at {thread_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            return False
    
    def get_thread_path(self, thread_id: str) -> str:
        """
        Get the path for a specific thread.
        
        Args:
            thread_id: Thread ID to look for
            
        Returns:
            str: Path to the thread's ChromaDB directory
        """
        # Check if thread directory exists directly
        thread_dir = os.path.join(self.memory_path, thread_id)
        if os.path.exists(thread_dir) and os.path.isdir(thread_dir):
            return thread_dir
            
        # If not found, return base path (for older configurations)
        return self.memory_path
    
    def get_state(self, thread_id: str) -> Dict[str, Any]:
        """
        Get the full state for a thread.
        
        Args:
            thread_id: Thread ID to retrieve
            
        Returns:
            Dict containing the thread state
        """
        try:
            # Update path to thread-specific directory if it exists
            thread_path = self.get_thread_path(thread_id)
            
            # Reconnect to the correct path
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=thread_path
            )
            
            # Create query for the thread ID
            config_str = json.dumps({"configurable": {"thread_id": thread_id}})
            
            # Search for the checkpoint
            results = self.vector_store.similarity_search(
                config_str,
                k=1,
                filter={"config": config_str}
            )
            
            if not results:
                logger.warning(f"No checkpoint found for thread_id: {thread_id}")
                return {}
                
            # Extract checkpoint data
            checkpoint_doc = results[0]
            checkpoint_data = json.loads(checkpoint_doc.page_content)
            
            # Process and return the state
            return self.process_state(checkpoint_data)
            
        except Exception as e:
            logger.error(f"Error retrieving state: {e}")
            return {"error": str(e)}
    
    def process_state(self, checkpoint_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and structure the checkpoint data.
        
        Args:
            checkpoint_data: Raw checkpoint data
            
        Returns:
            Dict: Structured state information
        """
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
    
    def list_threads(self) -> List[str]:
        """
        List all available thread IDs.
        
        Returns:
            List of thread IDs
        """
        threads = []
        
        # Check for thread directories
        if os.path.exists(self.memory_path):
            for item in os.listdir(self.memory_path):
                item_path = os.path.join(self.memory_path, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "chroma.sqlite3")):
                    threads.append(item)
        
        return threads
    
    def format_state_as_text(self, state: Dict[str, Any], thread_id: str) -> str:
        """
        Format state as human-readable text.
        
        Args:
            state: State dictionary
            thread_id: Thread ID
            
        Returns:
            str: Formatted text
        """
        if "error" in state:
            return f"Error retrieving state for thread '{thread_id}': {state['error']}"
        
        output = []
        output.append("=" * 80)
        output.append(f"DEEP AGENT STATE: {thread_id}")
        output.append("=" * 80)
        
        # Metadata
        output.append("\n## METADATA")
        output.append(f"Timestamp: {state['metadata']['timestamp']}")
        output.append(f"Version: {state['metadata']['version']}")
        
        # Conversation
        output.append("\n## CONVERSATION HISTORY")
        if state["conversation"]:
            for i, msg in enumerate(state["conversation"]):
                output.append(f"\n[{i+1}] {msg['role'].upper()}:")
                output.append(f"{msg['content']}")
        else:
            output.append("No conversation history found.")
        
        # Todo List
        output.append("\n## TODO LIST")
        if state["todos"]:
            for todo in state["todos"]:
                status = todo.get("status", "unknown")
                content = todo.get("content", "No description")
                todo_id = todo.get("id", "unknown")
                output.append(f"- [{status}] {content} (ID: {todo_id})")
        else:
            output.append("No todo items found.")
        
        # Files
        output.append("\n## VIRTUAL FILESYSTEM")
        if state["files"]:
            for path, content in state["files"].items():
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
    parser = argparse.ArgumentParser(description="Deep Agent State Viewer")
    parser.add_argument("--thread-id", type=str, help="Thread ID to retrieve")
    parser.add_argument("--memory-path", type=str, default="./serp_memory", 
                        help="Path to ChromaDB memory directory")
    parser.add_argument("--collection", type=str, default="serp-checkpoints",
                        help="ChromaDB collection name")
    parser.add_argument("--output-format", type=str, choices=["json", "text"], 
                        default="text", help="Output format")
    parser.add_argument("--list-threads", action="store_true", 
                        help="List available threads")
    
    args = parser.parse_args()
    
    # Initialize viewer
    viewer = DeepAgentStateViewer(
        memory_path=args.memory_path,
        collection_name=args.collection
    )
    
    # Connect to ChromaDB
    if not viewer.connect():
        print("Failed to connect to ChromaDB. Check the memory path.")
        return 1
    
    # List threads if requested
    if args.list_threads:
        threads = viewer.list_threads()
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
    
    # Get state for the thread
    state = viewer.get_state(args.thread_id)
    
    # Output based on format
    if args.output_format == "json":
        print(json.dumps(state, indent=2))
    else:
        print(viewer.format_state_as_text(state, args.thread_id))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
