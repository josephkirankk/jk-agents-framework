#!/usr/bin/env python3
"""
Script to extract and examine compressed data stored in the Large Data Optimization System
"""
import sqlite3
import json
import gzip
import sys
from pathlib import Path

def decompress_data(blob_data):
    """Decompress gzipped blob data"""
    try:
        return gzip.decompress(blob_data).decode('utf-8')
    except Exception as e:
        return f"Error decompressing: {str(e)}"

def examine_database(db_path):
    """Examine the contents of the database"""
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n=== Examining Database: {db_path} ===")
    
    # Get all records
    cursor.execute("""
        SELECT reference_id, data_type, size_bytes, compressed, 
               created_at, metadata, data_blob 
        FROM data_references 
        ORDER BY size_bytes DESC
    """)
    
    records = cursor.fetchall()
    
    for i, (ref_id, data_type, size_bytes, compressed, created_at, metadata, data_blob) in enumerate(records):
        print(f"\n--- Record {i+1}: {ref_id} ---")
        print(f"Data Type: {data_type}")
        print(f"Size: {size_bytes:,} bytes ({size_bytes/1024/1024:.2f} MB)")
        print(f"Compressed: {'Yes' if compressed else 'No'}")
        print(f"Created: {created_at}")
        print(f"Metadata: {metadata}")
        
        if data_blob:
            print(f"Blob size: {len(data_blob):,} bytes")
            
            if compressed:
                try:
                    decompressed = decompress_data(data_blob)
                    print(f"Decompressed size: {len(decompressed):,} characters")
                    
                    # Try to parse as JSON to understand structure
                    try:
                        data_json = json.loads(decompressed)
                        print("Content type: JSON")
                        print(f"Keys: {list(data_json.keys()) if isinstance(data_json, dict) else 'List/Other'}")
                        
                        # Show sample content (first 500 chars)
                        sample = str(data_json)[:500]
                        print(f"Sample content:\n{sample}...")
                        
                    except json.JSONDecodeError:
                        # Not JSON, show raw sample
                        print("Content type: Text/Other")
                        print(f"Sample content:\n{decompressed[:500]}...")
                        
                except Exception as e:
                    print(f"Error examining blob: {e}")
            else:
                # Uncompressed data
                try:
                    content = data_blob.decode('utf-8')
                    print(f"Sample content:\n{content[:500]}...")
                except:
                    print("Binary data (cannot decode as text)")
        
        print("-" * 50)
    
    conn.close()
    print(f"\nTotal records examined: {len(records)}")

def main():
    """Main function"""
    print("Large Data Optimization System - Content Examiner")
    print("=" * 60)
    
    # Examine both databases
    databases = [
        "demo_data/large_data_storage.db",
        "data/large_data_storage.db"
    ]
    
    for db_path in databases:
        examine_database(db_path)

if __name__ == "__main__":
    main()