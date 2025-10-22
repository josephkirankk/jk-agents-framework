#!/usr/bin/env python
"""
Check ChromaDB Data Using Chroma API

This tool properly queries ChromaDB using the langchain_chroma API,
which works with all ChromaDB versions.

Usage:
    python check_chromadb_data.py [--memory-path ./serp_memory]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from langchain_chroma import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError:
    print("Error: Required packages not found.")
    print("Please install: pip install langchain-chroma langchain-community")
    sys.exit(1)


def check_chromadb(memory_path: str, collection_name: str = "checkpoints") -> Dict[str, Any]:
    """Check ChromaDB using the Chroma API."""
    result = {
        "path": memory_path,
        "exists": os.path.exists(memory_path),
        "collection": collection_name,
        "documents_found": 0,
        "thread_ids": set(),
        "checkpoints": [],
        "error": None
    }
    
    if not result["exists"]:
        result["error"] = f"Directory not found: {memory_path}"
        return result
    
    try:
        print(f"\n🔍 Connecting to ChromaDB at {memory_path}...")
        
        # Initialize embedding function
        embedding_function = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize vector store
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_function,
            persist_directory=memory_path
        )
        
        print("✅ Connected successfully!")
        
        # Get the underlying collection
        collection = vector_store._collection
        
        # Get all documents
        print(f"\n📊 Fetching documents from collection '{collection_name}'...")
        all_docs = collection.get(include=['metadatas', 'documents'])
        
        result["documents_found"] = len(all_docs['ids']) if 'ids' in all_docs else 0
        
        print(f"   Found {result['documents_found']} document(s)")
        
        if result["documents_found"] > 0:
            # Process each document
            for i, doc_id in enumerate(all_docs['ids']):
                metadata = all_docs['metadatas'][i] if 'metadatas' in all_docs else {}
                document = all_docs['documents'][i] if 'documents' in all_docs else None
                
                # Extract thread_id
                thread_id = metadata.get('thread_id')
                if thread_id:
                    result['thread_ids'].add(thread_id)
                
                # Store checkpoint info
                checkpoint_info = {
                    "id": doc_id,
                    "thread_id": thread_id,
                    "checkpoint_id": metadata.get('checkpoint_id'),
                    "timestamp": metadata.get('timestamp'),
                    "type": metadata.get('type'),
                    "has_document": document is not None,
                    "document_length": len(document) if document else 0
                }
                
                result['checkpoints'].append(checkpoint_info)
                
                # Try to parse the document to extract state info
                if document:
                    try:
                        parsed = json.loads(document)
                        checkpoint_info['has_checkpoint'] = 'checkpoint' in parsed
                        checkpoint_info['has_metadata'] = 'metadata' in parsed
                        checkpoint_info['version'] = parsed.get('version')
                        checkpoint_info['timestamp_stored'] = parsed.get('timestamp')
                        
                        # Check for state data
                        if 'checkpoint' in parsed:
                            checkpoint_data = parsed['checkpoint']
                            if 'channel_values' in checkpoint_data:
                                values = checkpoint_data['channel_values']
                                checkpoint_info['has_messages'] = 'messages' in values
                                checkpoint_info['has_files'] = 'files' in values
                                checkpoint_info['has_todos'] = 'todos' in values
                                
                                if 'messages' in values:
                                    checkpoint_info['message_count'] = len(values['messages'])
                                if 'files' in values:
                                    checkpoint_info['file_count'] = len(values['files'])
                                if 'todos' in values:
                                    checkpoint_info['todo_count'] = len(values['todos'])
                    except json.JSONDecodeError:
                        checkpoint_info['parse_error'] = "Not valid JSON"
                    except Exception as e:
                        checkpoint_info['parse_error'] = str(e)
        
    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
    
    return result


def print_results(result: Dict[str, Any]):
    """Print formatted results."""
    print("\n" + "=" * 80)
    print("CHROMADB DATA CHECK RESULTS")
    print("=" * 80)
    
    print(f"\n📁 Path: {result['path']}")
    print(f"📦 Collection: {result['collection']}")
    
    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")
        if result.get('traceback'):
            print(f"\nTraceback:\n{result['traceback']}")
        return
    
    print(f"\n📊 Documents found: {result['documents_found']}")
    print(f"🔑 Unique thread IDs: {len(result['thread_ids'])}")
    
    if result['thread_ids']:
        print("\nThread IDs:")
        for thread_id in sorted(result['thread_ids']):
            print(f"  ✓ {thread_id}")
    
    if result['checkpoints']:
        print(f"\n📝 Checkpoints ({len(result['checkpoints'])}):")
        print("-" * 80)
        
        for checkpoint in result['checkpoints']:
            print(f"\n  ID: {checkpoint['id']}")
            print(f"  Thread ID: {checkpoint['thread_id']}")
            print(f"  Checkpoint ID: {checkpoint['checkpoint_id']}")
            print(f"  Type: {checkpoint['type']}")
            print(f"  Timestamp: {checkpoint.get('timestamp_stored', checkpoint.get('timestamp'))}")
            print(f"  Document size: {checkpoint['document_length']} bytes")
            
            if checkpoint.get('has_checkpoint'):
                print("  ✓ Contains checkpoint data")
                if checkpoint.get('message_count') is not None:
                    print(f"    - Messages: {checkpoint['message_count']}")
                if checkpoint.get('file_count') is not None:
                    print(f"    - Files: {checkpoint['file_count']}")
                if checkpoint.get('todo_count') is not None:
                    print(f"    - Todos: {checkpoint['todo_count']}")
            
            if checkpoint.get('parse_error'):
                print(f"  ⚠️  Parse error: {checkpoint['parse_error']}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check ChromaDB Data")
    parser.add_argument("--memory-path", type=str, default="./serp_memory",
                        help="Path to ChromaDB memory directory")
    parser.add_argument("--collection", type=str, default="checkpoints",
                        help="Collection name (default: checkpoints)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("CHROMADB DATA CHECKER")
    print("=" * 80)
    
    result = check_chromadb(args.memory_path, args.collection)
    print_results(result)
    
    print("\n" + "=" * 80)
    
    if result['thread_ids']:
        print("\n✅ Found thread data!")
        print("\nTo view a thread, use:")
        for thread_id in list(result['thread_ids'])[:3]:
            print(f"  python tools/deep_agent_inspector.py --thread-id {thread_id}")
    else:
        print("\n⚠️  No thread data found.")
        print("\nPossible reasons:")
        print("  1. No Deep Agent sessions have been run yet")
        print("  2. The API server needs to be running")
        print("  3. Try running your curl command to create a session")
    
    print("=" * 80)
    
    return 0 if not result.get('error') else 1


if __name__ == "__main__":
    sys.exit(main())
