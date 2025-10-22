#!/usr/bin/env python
"""Find all threads in ChromaDB databases"""

import os
import sqlite3
import json
from pathlib import Path


def find_threads_in_db(db_path):
    """Find all threads in a ChromaDB database."""
    threads = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all documents
        cursor.execute("SELECT document, metadata FROM embeddings")
        
        for row in cursor.fetchall():
            try:
                doc = json.loads(row[0])
                metadata = json.loads(row[1]) if row[1] else {}
                
                # Try to extract thread_id from different locations
                thread_id = None
                
                # Check in metadata
                if isinstance(metadata, dict):
                    if 'thread_id' in metadata:
                        thread_id = metadata['thread_id']
                    elif 'config' in metadata:
                        try:
                            config = json.loads(metadata['config']) if isinstance(metadata['config'], str) else metadata['config']
                            if isinstance(config, dict) and 'configurable' in config:
                                thread_id = config['configurable'].get('thread_id')
                        except:
                            pass
                
                # Check in document
                if not thread_id and isinstance(doc, dict):
                    if 'thread_id' in doc:
                        thread_id = doc['thread_id']
                    elif 'config' in doc:
                        try:
                            config = json.loads(doc['config']) if isinstance(doc['config'], str) else doc['config']
                            if isinstance(config, dict) and 'configurable' in config:
                                thread_id = config['configurable'].get('thread_id')
                        except:
                            pass
                
                if thread_id and thread_id not in threads:
                    threads.append(thread_id)
            except Exception as e:
                continue
        
        conn.close()
    except Exception as e:
        print(f"Error reading {db_path}: {e}")
    
    return threads


def scan_directory(base_dir):
    """Scan directory for ChromaDB databases."""
    results = {}
    
    for root, dirs, files in os.walk(base_dir):
        if 'chroma.sqlite3' in files:
            db_path = os.path.join(root, 'chroma.sqlite3')
            threads = find_threads_in_db(db_path)
            if threads:
                rel_path = os.path.relpath(root, base_dir)
                results[rel_path] = threads
    
    return results


def main():
    base_dir = Path(__file__).parent.parent
    
    # Memory directories to check
    memory_dirs = [
        'serp_memory',
        'jk_agents_memory',
        'chroma_memory',
        'youtube_memory',
        'simple_memory',
        'test_memory',
        'advanced_agent_memory',
    ]
    
    print("Scanning for Deep Agent threads...\n")
    
    all_threads = {}
    
    for memory_dir in memory_dirs:
        dir_path = base_dir / memory_dir
        if dir_path.exists():
            print(f"Checking {memory_dir}...")
            results = scan_directory(str(dir_path))
            if results:
                all_threads[memory_dir] = results
    
    # Print results
    print("\n" + "=" * 80)
    print("THREADS FOUND")
    print("=" * 80)
    
    if not all_threads:
        print("No threads found in any memory directory.")
    else:
        for memory_dir, locations in all_threads.items():
            print(f"\n{memory_dir}/")
            for location, threads in locations.items():
                print(f"  {location}/")
                for thread in threads:
                    print(f"    - {thread}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
