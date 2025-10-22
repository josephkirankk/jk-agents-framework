#!/usr/bin/env python
"""
Deep Agent Inspector

A comprehensive tool for inspecting and exporting Deep Agent state data.
Provides rich visualization and export options for conversation history,
todo lists, virtual filesystem, and other state information.

Usage:
    python deep_agent_inspector.py --thread-id <thread_id> [options]
    python deep_agent_inspector.py --list-threads
    python deep_agent_inspector.py --export-html <thread_id> --output report.html

Options:
    --thread-id ID         Thread ID to inspect
    --memory-path PATH     Path to ChromaDB memory (default: ./serp_memory)
    --collection NAME      Collection name (default: serp-checkpoints)
    --format FORMAT        Output format: text, json, csv, html (default: text)
    --output FILE          Output file for export (default: stdout)
    --list-threads         List available threads
    --export-html ID       Export thread state as HTML report
    --export-csv ID        Export thread state as CSV files
"""

import os
import sys
import json
import csv
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
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
logger = logging.getLogger("deep_agent_inspector")

# HTML template for reports
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deep Agent State: {thread_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .conversation {{
            margin-bottom: 30px;
        }}
        .message {{
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 5px;
        }}
        .user {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
        }}
        .assistant {{
            background-color: #f0f7f0;
            border-left: 4px solid #2ecc71;
        }}
        .system {{
            background-color: #f5f5f5;
            border-left: 4px solid #95a5a6;
        }}
        .todo-list {{
            margin-bottom: 30px;
        }}
        .todo-item {{
            padding: 8px 15px;
            margin-bottom: 5px;
            border-radius: 3px;
        }}
        .todo-pending {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .todo-in_progress {{
            background-color: #cce5ff;
            border-left: 4px solid #007bff;
        }}
        .todo-completed {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            text-decoration: line-through;
        }}
        .filesystem {{
            margin-bottom: 30px;
        }}
        .file {{
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }}
        .file-header {{
            background-color: #f8f9fa;
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
        }}
        .file-content {{
            padding: 15px;
            background-color: #fff;
            overflow-x: auto;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }}
        .code {{
            font-family: 'Courier New', Courier, monospace;
            background-color: #f7f7f7;
        }}
        .markdown {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.85em;
        }}
        .tab {{
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
            border-radius: 5px 5px 0 0;
        }}
        .tab button {{
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 10px 16px;
            transition: 0.3s;
            font-size: 16px;
        }}
        .tab button:hover {{
            background-color: #ddd;
        }}
        .tab button.active {{
            background-color: #3498db;
            color: white;
        }}
        .tabcontent {{
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
            border-radius: 0 0 5px 5px;
            animation: fadeEffect 1s;
        }}
        @keyframes fadeEffect {{
            from {{opacity: 0;}}
            to {{opacity: 1;}}
        }}
    </style>
</head>
<body>
    <h1>Deep Agent State: {thread_id}</h1>
    
    <div class="metadata">
        <p><strong>Timestamp:</strong> {timestamp}</p>
        <p><strong>Version:</strong> {version}</p>
    </div>
    
    <div class="tab">
        <button class="tablinks active" onclick="openTab(event, 'Conversation')">Conversation</button>
        <button class="tablinks" onclick="openTab(event, 'TodoList')">Todo List</button>
        <button class="tablinks" onclick="openTab(event, 'Filesystem')">Filesystem</button>
    </div>
    
    <div id="Conversation" class="tabcontent" style="display: block;">
        <h2>Conversation History</h2>
        <div class="conversation">
            {conversation_html}
        </div>
    </div>
    
    <div id="TodoList" class="tabcontent">
        <h2>Todo List</h2>
        <div class="todo-list">
            {todo_html}
        </div>
    </div>
    
    <div id="Filesystem" class="tabcontent">
        <h2>Virtual Filesystem</h2>
        <div class="filesystem">
            {filesystem_html}
        </div>
    </div>
    
    <script>
    function openTab(evt, tabName) {{
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {{
            tabcontent[i].style.display = "none";
        }}
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {{
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }}
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
    }}
    </script>
</body>
</html>
"""

class DeepAgentInspector:
    """Comprehensive tool for inspecting Deep Agent state"""
    
    def __init__(self, memory_path: str = "./serp_memory", collection_name: str = "serp-checkpoints"):
        """
        Initialize the inspector.
        
        Args:
            memory_path: Path to ChromaDB storage directory
            collection_name: Name of the checkpoint collection
        """
        self.memory_path = memory_path
        self.collection_name = collection_name
        self.embedding_function = None
        self.vector_store = None
        
        logger.info(f"Initializing inspector with memory path: {memory_path}")
        
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
    
    def export_as_html(self, state: Dict[str, Any], thread_id: str) -> str:
        """
        Export state as HTML report.
        
        Args:
            state: State dictionary
            thread_id: Thread ID
            
        Returns:
            str: HTML report
        """
        if "error" in state:
            return f"<html><body><h1>Error</h1><p>{state['error']}</p></body></html>"
        
        # Handle empty state
        if not state:
            return f"<html><body><h1>No Data Found</h1><p>No checkpoint data found for thread ID: {thread_id}</p></body></html>"
        
        # Initialize state with default values if keys are missing
        state_with_defaults = {
            "metadata": state.get("metadata", {"timestamp": "Unknown", "version": "Unknown"}),
            "conversation": state.get("conversation", []),
            "todos": state.get("todos", []),
            "files": state.get("files", {}),
        }
        
        # Format conversation
        conversation_html = ""
        if state_with_defaults["conversation"]:
            for msg in state_with_defaults["conversation"]:
                role = msg["role"]
                content = msg["content"].replace("\n", "<br>")
                timestamp = msg.get("timestamp", "")
                
                conversation_html += f'<div class="message {role}">'
                conversation_html += f'<strong>{role.upper()}</strong>'
                if timestamp:
                    conversation_html += f' <span class="timestamp">{timestamp}</span>'
                conversation_html += f'<div>{content}</div></div>\n'
        else:
            conversation_html = "<p>No conversation history found.</p>"
        
        # Format todo list
        todo_html = ""
        if state_with_defaults["todos"]:
            for todo in state_with_defaults["todos"]:
                status = todo.get("status", "unknown")
                content = todo.get("content", "No description")
                todo_id = todo.get("id", "unknown")
                priority = todo.get("priority", "medium")
                
                todo_html += f'<div class="todo-item todo-{status}">'
                todo_html += f'<strong>{content}</strong> (Priority: {priority})'
                todo_html += f'<br><span class="timestamp">ID: {todo_id} | Status: {status}</span>'
                todo_html += '</div>\n'
        else:
            todo_html = "<p>No todo items found.</p>"
        
        # Format filesystem
        filesystem_html = ""
        if state_with_defaults["files"]:
            for path, content in state_with_defaults["files"].items():
                file_class = "code"
                if path.endswith(".md"):
                    file_class = "markdown"
                
                filesystem_html += f'<div class="file">'
                filesystem_html += f'<div class="file-header">'
                filesystem_html += f'<span>{path}</span>'
                filesystem_html += f'<span>{len(content)} characters</span>'
                filesystem_html += '</div>'
                filesystem_html += f'<div class="file-content {file_class}">'
                
                # Escape HTML characters
                content_escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                filesystem_html += content_escaped
                
                filesystem_html += '</div></div>\n'
        else:
            filesystem_html = "<p>No files found.</p>"
        
        # Fill template
        html = HTML_TEMPLATE.format(
            thread_id=thread_id,
            timestamp=state_with_defaults["metadata"].get("timestamp", "Unknown"),
            version=state_with_defaults["metadata"].get("version", "Unknown"),
            conversation_html=conversation_html,
            todo_html=todo_html,
            filesystem_html=filesystem_html
        )
        
        return html
    
    def export_as_csv(self, state: Dict[str, Any], thread_id: str, output_dir: str) -> List[str]:
        """
        Export state as CSV files.
        
        Args:
            state: State dictionary
            thread_id: Thread ID
            output_dir: Directory to save CSV files
            
        Returns:
            List of created files
        """
        if "error" in state or not state:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Create an error file if there's an error
            error_file = os.path.join(output_dir, f"{thread_id}_error.csv")
            with open(error_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Thread ID", "Status"])
                if "error" in state:
                    writer.writerow([thread_id, f"Error: {state['error']}"])
                else:
                    writer.writerow([thread_id, "No data found"])
            return [error_file]
        
        # Initialize state with default values
        state_with_defaults = {
            "metadata": state.get("metadata", {"timestamp": "Unknown", "version": "Unknown"}),
            "conversation": state.get("conversation", []),
            "todos": state.get("todos", []),
            "files": state.get("files", {}),
        }
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        created_files = []
        
        # Export metadata
        metadata_file = os.path.join(output_dir, f"{thread_id}_metadata.csv")
        with open(metadata_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Key", "Value"])
            writer.writerow(["Thread ID", thread_id])
            writer.writerow(["Timestamp", state_with_defaults["metadata"].get("timestamp", "Unknown")])
            writer.writerow(["Version", state_with_defaults["metadata"].get("version", "Unknown")])
        created_files.append(metadata_file)
        
        # Export conversation
        if state_with_defaults["conversation"]:
            conversation_file = os.path.join(output_dir, f"{thread_id}_conversation.csv")
            with open(conversation_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Index", "Role", "Timestamp", "Content"])
                for i, msg in enumerate(state_with_defaults["conversation"]):
                    writer.writerow([
                        i+1,
                        msg["role"],
                        msg.get("timestamp", ""),
                        msg["content"]
                    ])
            created_files.append(conversation_file)
        
        # Export todos
        if state_with_defaults["todos"]:
            todos_file = os.path.join(output_dir, f"{thread_id}_todos.csv")
            with open(todos_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Content", "Status", "Priority"])
                for todo in state_with_defaults["todos"]:
                    writer.writerow([
                        todo.get("id", ""),
                        todo.get("content", ""),
                        todo.get("status", ""),
                        todo.get("priority", "")
                    ])
            created_files.append(todos_file)
        
        # Export files
        if state_with_defaults["files"]:
            files_file = os.path.join(output_dir, f"{thread_id}_files.csv")
            with open(files_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Path", "Size", "Content"])
                for path, content in state_with_defaults["files"].items():
                    writer.writerow([path, len(content), content])
            created_files.append(files_file)
            
            # Also export individual files
            files_dir = os.path.join(output_dir, f"{thread_id}_files")
            os.makedirs(files_dir, exist_ok=True)
            
            for path, content in state_with_defaults["files"].items():
                # Clean path for filesystem
                clean_path = path.replace("/", "_").lstrip("_")
                file_path = os.path.join(files_dir, clean_path)
                
                with open(file_path, 'w') as f:
                    f.write(content)
                created_files.append(file_path)
        
        return created_files

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Deep Agent Inspector")
    parser.add_argument("--thread-id", type=str, help="Thread ID to inspect")
    parser.add_argument("--memory-path", type=str, default="./serp_memory", 
                        help="Path to ChromaDB memory directory")
    parser.add_argument("--collection", type=str, default="serp-checkpoints",
                        help="ChromaDB collection name")
    parser.add_argument("--format", type=str, choices=["text", "json", "csv", "html"], 
                        default="text", help="Output format")
    parser.add_argument("--output", type=str, help="Output file for export")
    parser.add_argument("--list-threads", action="store_true", 
                        help="List available threads")
    parser.add_argument("--export-html", type=str, metavar="THREAD_ID",
                        help="Export thread state as HTML report")
    parser.add_argument("--export-csv", type=str, metavar="THREAD_ID",
                        help="Export thread state as CSV files")
    parser.add_argument("--output-dir", type=str, default="./exports",
                        help="Directory for CSV exports")
    
    args = parser.parse_args()
    
    # Initialize inspector
    inspector = DeepAgentInspector(
        memory_path=args.memory_path,
        collection_name=args.collection
    )
    
    # Connect to ChromaDB
    if not inspector.connect():
        print("Failed to connect to ChromaDB. Check the memory path.")
        return 1
    
    # List threads if requested
    if args.list_threads:
        threads = inspector.list_threads()
        if threads:
            print("Available threads:")
            for thread in threads:
                print(f"- {thread}")
        else:
            print("No threads found.")
        return 0
    
    # Export as HTML if requested
    if args.export_html:
        thread_id = args.export_html
        state = inspector.get_state(thread_id)
        
        if "error" in state:
            print(f"Error retrieving state: {state['error']}")
            return 1
        
        html = inspector.export_as_html(state, thread_id)
        
        output_file = args.output or f"{thread_id}_report.html"
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"HTML report exported to {output_file}")
        return 0
    
    # Export as CSV if requested
    if args.export_csv:
        thread_id = args.export_csv
        state = inspector.get_state(thread_id)
        
        if "error" in state:
            print(f"Error retrieving state: {state['error']}")
            return 1
        
        output_dir = args.output_dir
        files = inspector.export_as_csv(state, thread_id, output_dir)
        
        print(f"CSV files exported to {output_dir}:")
        for file in files:
            print(f"- {os.path.basename(file)}")
        return 0
    
    # Check if thread ID is provided
    if not args.thread_id:
        print("Error: Thread ID is required. Use --thread-id <id> or --list-threads to see available threads.")
        return 1
    
    # Get state for the thread
    state = inspector.get_state(args.thread_id)
    
    if "error" in state:
        print(f"Error retrieving state: {state['error']}")
        return 1
    
    # Output based on format
    if args.format == "json":
        output = json.dumps(state, indent=2)
    elif args.format == "text":
        output = inspector.format_state_as_text(state, args.thread_id)
    elif args.format == "html":
        output = inspector.export_as_html(state, args.thread_id)
    elif args.format == "csv":
        # CSV format requires output directory
        output_dir = args.output_dir
        files = inspector.export_as_csv(state, args.thread_id, output_dir)
        print(f"CSV files exported to {output_dir}:")
        for file in files:
            print(f"- {os.path.basename(file)}")
        return 0
    
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
