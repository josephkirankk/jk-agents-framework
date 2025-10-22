#!/usr/bin/env python
"""
Diagnostic Script for Deep Agent Storage

This script helps diagnose issues with Deep Agent storage and finds all available threads.

Usage:
    python diagnose_deep_agent_storage.py
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Tuple


def check_chromadb_file(db_path: str) -> Dict:
    """Check a ChromaDB file and return diagnostic information."""
    result = {
        "path": db_path,
        "exists": os.path.exists(db_path),
        "size": 0,
        "tables": [],
        "embeddings_count": 0,
        "threads": [],
        "error": None
    }
    
    if not result["exists"]:
        return result
    
    result["size"] = os.path.getsize(db_path)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        result["tables"] = [row[0] for row in cursor.fetchall()]
        
        # Count embeddings
        if "embeddings" in result["tables"]:
            cursor.execute("SELECT COUNT(*) FROM embeddings;")
            result["embeddings_count"] = cursor.fetchone()[0]
            
            # Try to find thread IDs
            cursor.execute("SELECT document, metadata FROM embeddings LIMIT 100;")
            
            threads_found = set()
            
            for row in cursor.fetchall():
                try:
                    # Parse document
                    doc = json.loads(row[0]) if row[0] else {}
                    metadata = json.loads(row[1]) if row[1] else {}
                    
                    # Extract thread_id from various locations
                    thread_id = None
                    
                    # Method 1: From metadata
                    if isinstance(metadata, dict):
                        if 'thread_id' in metadata:
                            thread_id = metadata['thread_id']
                        elif 'config' in metadata:
                            try:
                                config_str = metadata['config']
                                if isinstance(config_str, str):
                                    config = json.loads(config_str)
                                else:
                                    config = config_str
                                    
                                if isinstance(config, dict) and 'configurable' in config:
                                    thread_id = config['configurable'].get('thread_id')
                            except:
                                pass
                    
                    # Method 2: From document
                    if not thread_id and isinstance(doc, dict):
                        if 'thread_id' in doc:
                            thread_id = doc['thread_id']
                        elif 'config' in doc:
                            try:
                                config_str = doc['config']
                                if isinstance(config_str, str):
                                    config = json.loads(config_str)
                                else:
                                    config = config_str
                                    
                                if isinstance(config, dict) and 'configurable' in config:
                                    thread_id = config['configurable'].get('thread_id')
                            except:
                                pass
                    
                    # Method 3: Look for thread_id in nested structures
                    if not thread_id:
                        def find_thread_id(obj, depth=0):
                            if depth > 5:  # Prevent infinite recursion
                                return None
                            if isinstance(obj, dict):
                                if 'thread_id' in obj:
                                    return obj['thread_id']
                                for value in obj.values():
                                    result = find_thread_id(value, depth + 1)
                                    if result:
                                        return result
                            elif isinstance(obj, list):
                                for item in obj:
                                    result = find_thread_id(item, depth + 1)
                                    if result:
                                        return result
                            return None
                        
                        thread_id = find_thread_id(doc) or find_thread_id(metadata)
                    
                    if thread_id:
                        threads_found.add(str(thread_id))
                        
                except Exception as e:
                    continue
            
            result["threads"] = sorted(list(threads_found))
        
        conn.close()
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def scan_memory_directories(base_dir: Path) -> Dict[str, List[Dict]]:
    """Scan all memory directories for ChromaDB files."""
    memory_dirs = [
        'serp_memory',
        'jk_agents_memory',
        'chroma_memory',
        'youtube_memory',
        'simple_memory',
        'test_memory',
        'advanced_agent_memory',
        'advanced_memory_test',
        'test_chromadb_memory',
        'test_jk_agents_memory',
        'integration_tests/serp_memory',
        'integration_tests/youtube_memory',
        'integration_tests/simple_memory',
        'integration_tests/test_memory',
        'integration_tests/jk_agents_memory',
    ]
    
    results = {}
    
    for memory_dir in memory_dirs:
        dir_path = base_dir / memory_dir
        if not dir_path.exists():
            continue
        
        chromadb_files = []
        
        # Search for chroma.sqlite3 files
        for root, dirs, files in os.walk(dir_path):
            if 'chroma.sqlite3' in files:
                db_path = os.path.join(root, 'chroma.sqlite3')
                db_info = check_chromadb_file(db_path)
                chromadb_files.append(db_info)
        
        if chromadb_files:
            results[memory_dir] = chromadb_files
    
    return results


def main():
    """Main diagnostic function."""
    print("=" * 80)
    print("DEEP AGENT STORAGE DIAGNOSTIC")
    print("=" * 80)
    
    base_dir = Path(__file__).parent.parent
    print(f"\nBase directory: {base_dir}")
    print(f"\nScanning for ChromaDB databases...\n")
    
    results = scan_memory_directories(base_dir)
    
    if not results:
        print("❌ No ChromaDB databases found!")
        return 1
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_dbs = sum(len(dbs) for dbs in results.values())
    total_threads = set()
    
    print(f"\n📊 Found {total_dbs} ChromaDB database(s) in {len(results)} directory/directories\n")
    
    # Print detailed results
    for memory_dir, db_files in results.items():
        print(f"\n📁 {memory_dir}/")
        print("-" * 80)
        
        for db_info in db_files:
            rel_path = os.path.relpath(os.path.dirname(db_info['path']), base_dir)
            
            print(f"\n  Location: {rel_path}/")
            print(f"  Size: {db_info['size']:,} bytes")
            print(f"  Tables: {', '.join(db_info['tables'])}")
            print(f"  Embeddings: {db_info['embeddings_count']}")
            
            if db_info['error']:
                print(f"  ❌ Error: {db_info['error']}")
            
            if db_info['threads']:
                print(f"  ✅ Threads found: {len(db_info['threads'])}")
                for thread_id in db_info['threads'][:10]:  # Show first 10
                    print(f"     - {thread_id}")
                    total_threads.add(thread_id)
                if len(db_info['threads']) > 10:
                    print(f"     ... and {len(db_info['threads']) - 10} more")
            else:
                print(f"  ⚠️  No threads found (or thread IDs not extractable)")
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nTotal unique threads found: {len(total_threads)}")
    
    if total_threads:
        print("\nAll unique thread IDs:")
        for thread_id in sorted(total_threads):
            print(f"  - {thread_id}")
    
    print("\n" + "=" * 80)
    print("\nTo view a specific thread, use:")
    print("  python tools/deep_agent_inspector.py --thread-id <thread_id> --memory-path <path>")
    print("\nExample:")
    print("  python tools/deep_agent_inspector.py --thread-id your-thread-id --memory-path ./serp_memory")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
