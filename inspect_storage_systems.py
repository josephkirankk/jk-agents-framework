#!/usr/bin/env python3
"""
Comprehensive Storage Systems Inspector
Inspects both Large Data Storage (SQLite) and ChromaDB (Vector Store)
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import sys

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def inspect_large_data_storage(db_path="./data/large_tool_data.db"):
    """Comprehensive inspection of large data storage"""
    
    print_header("LARGE DATA STORAGE INSPECTION")
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print("   This means no large data has been stored yet.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS large_tool_data (
            reference_id TEXT PRIMARY KEY,
            tool_name TEXT NOT NULL,
            storage_type TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            size_category TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            access_count INTEGER DEFAULT 0,
            compressed INTEGER DEFAULT 0
        );
    """)
    conn.commit()
    
    # Total references
    cursor.execute("SELECT COUNT(*) FROM large_tool_data")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total References: {total}")
    
    if total == 0:
        print("   No data references stored yet.")
        conn.close()
        return
    
    # Storage breakdown
    cursor.execute("""
        SELECT 
            storage_type,
            size_category,
            COUNT(*) as count,
            SUM(size_bytes) as total_bytes,
            AVG(size_bytes) as avg_bytes
        FROM large_tool_data
        GROUP BY storage_type, size_category
    """)
    
    print("\n📦 Storage Breakdown:")
    print(f"  {'Storage Type':<15} | {'Category':<10} | {'Count':<7} | {'Total MB':<12} | {'Avg MB':<10}")
    print("  " + "-" * 75)
    for row in cursor.fetchall():
        storage_type, size_cat, count, total_bytes, avg_bytes = row
        total_mb = (total_bytes or 0) / (1024 * 1024)
        avg_mb = (avg_bytes or 0) / (1024 * 1024)
        print(f"  {storage_type:<15} | {size_cat:<10} | {count:<7} | {total_mb:>10.2f} MB | {avg_mb:>8.2f} MB")
    
    # Tool usage
    cursor.execute("""
        SELECT tool_name, COUNT(*) as count, 
               ROUND(SUM(size_bytes) / 1048576.0, 2) as total_mb
        FROM large_tool_data
        GROUP BY tool_name
        ORDER BY count DESC
    """)
    
    print("\n🔧 Tool Usage Statistics:")
    print(f"  {'Tool Name':<40} | {'Count':<7} | {'Total MB':<10}")
    print("  " + "-" * 65)
    for tool_name, count, total_mb in cursor.fetchall():
        print(f"  {tool_name:<40} | {count:<7} | {total_mb:>8.2f} MB")
    
    # Recent activity
    cursor.execute("""
        SELECT 
            reference_id,
            tool_name,
            size_category,
            ROUND(size_bytes / 1048576.0, 2) as size_mb,
            datetime(created_at) as created,
            access_count
        FROM large_tool_data
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    print("\n⏰ Recent References (Last 10):")
    print(f"  {'Ref ID':<15} | {'Tool':<25} | {'Category':<8} | {'Size MB':<10} | {'Accesses':<10}")
    print("  " + "-" * 85)
    for row in cursor.fetchall():
        ref_id, tool, size_cat, size_mb, created, access = row
        print(f"  {ref_id:<15} | {tool:<25} | {size_cat:<8} | {size_mb:>8.2f} MB | {access:>8}")
    
    # Expired references
    cursor.execute("""
        SELECT COUNT(*) 
        FROM large_tool_data 
        WHERE expires_at < datetime('now')
    """)
    expired = cursor.fetchone()[0]
    if expired > 0:
        print(f"\n⚠️  Expired References: {expired} (need cleanup)")
        print("   Run cleanup with: curl -X POST http://localhost:8000/cleanup/large-data")
    
    # Compression analysis
    cursor.execute("""
        SELECT 
            compressed,
            COUNT(*) as count,
            AVG(size_bytes) as avg_size
        FROM large_tool_data
        GROUP BY compressed
    """)
    
    print("\n🗜️  Compression Analysis:")
    for compressed, count, avg_size in cursor.fetchall():
        status = "Compressed" if compressed else "Uncompressed"
        avg_mb = (avg_size or 0) / (1024 * 1024)
        print(f"  {status:<15} | {count:>6} refs | {avg_mb:>8.2f} MB avg")
    
    conn.close()
    
    # File system check
    file_path = Path("./data/large_tool_data_files")
    if file_path.exists():
        files = list(file_path.glob("*"))
        if files:
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            total_size_mb = total_size / (1024 * 1024)
            print(f"\n💾 File System Storage: {len(files)} files, {total_size_mb:.2f} MB")
            
            # Show largest files
            file_sizes = [(f.name, f.stat().st_size / (1024 * 1024)) for f in files if f.is_file()]
            file_sizes.sort(key=lambda x: x[1], reverse=True)
            
            if len(file_sizes) > 0:
                print("\n   Largest Files:")
                for fname, size_mb in file_sizes[:5]:
                    print(f"   - {fname}: {size_mb:.2f} MB")

def inspect_chromadb(chroma_path="./chroma_data"):
    """Inspect ChromaDB collections and contents"""
    
    print_header("CHROMADB INSPECTION")
    
    if not Path(chroma_path).exists():
        print(f"❌ ChromaDB directory not found: {chroma_path}")
        print("   ChromaDB has not been initialized yet.")
        return
    
    try:
        import chromadb
    except ImportError:
        print("❌ chromadb package not installed. Install with: pip install chromadb")
        return
    
    try:
        client = chromadb.PersistentClient(path=chroma_path)
        
        # List collections
        collections = client.list_collections()
        
        if not collections:
            print("\n📂 No collections found in ChromaDB")
            return
        
        print(f"\n📂 Collections: {len(collections)} found")
        print(f"  {'Collection Name':<40} | {'Item Count':<12} | {'Purpose':<30}")
        print("  " + "-" * 90)
        
        for collection in collections:
            count = collection.count()
            
            # Determine purpose based on name
            if "conversation" in collection.name.lower():
                purpose = "Conversation Memory"
            elif "checkpoint" in collection.name.lower():
                purpose = "LangGraph Checkpointing"
            elif "memory" in collection.name.lower():
                purpose = "Agent Memory"
            else:
                purpose = "Unknown"
            
            print(f"  {collection.name:<40} | {count:>10} | {purpose:<30}")
            
            # Show sample metadata if items exist
            if count > 0 and count <= 5:
                try:
                    results = collection.get(limit=3, include=["metadatas", "documents"])
                    if results['metadatas']:
                        print(f"\n  Sample items from '{collection.name}':")
                        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
                            doc_preview = doc[:100] + "..." if len(doc) > 100 else doc
                            print(f"    {i}. Doc: {doc_preview}")
                            if meta:
                                print(f"       Meta: {json.dumps(meta, default=str)[:150]}")
                except Exception as e:
                    print(f"  Could not fetch sample: {e}")
        
        # Storage size estimate
        try:
            import os
            total_size = 0
            for root, dirs, files in os.walk(chroma_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    total_size += os.path.getsize(filepath)
            
            total_size_mb = total_size / (1024 * 1024)
            print(f"\n💾 Total ChromaDB Storage: {total_size_mb:.2f} MB")
        except Exception as e:
            print(f"\n⚠️  Could not calculate storage size: {e}")
            
    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {e}")
        import traceback
        traceback.print_exc()

def inspect_sqlite_checkpoints(chroma_path="./chroma_data"):
    """Inspect SQLite-based checkpoints if they exist"""
    
    print_header("SQLITE CHECKPOINTS INSPECTION")
    
    # Look for SQLite checkpoint database
    checkpoint_paths = [
        "./checkpoints.db",
        "./data/checkpoints.db",
        f"{chroma_path}/checkpoints.db"
    ]
    
    found = False
    for db_path in checkpoint_paths:
        if Path(db_path).exists():
            found = True
            print(f"\n📊 Found checkpoint database: {db_path}")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"\n📋 Tables: {len(tables)}")
                for table_name, in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} records")
                    
                    # Show sample for small tables
                    if count > 0 and count <= 10:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                        rows = cursor.fetchall()
                        if rows:
                            print(f"    Sample records: {len(rows)}")
                
                conn.close()
            except Exception as e:
                print(f"  ⚠️  Error reading database: {e}")
    
    if not found:
        print("\n  No SQLite checkpoint databases found.")
        print("  Checkpoints may be stored in ChromaDB instead.")

def print_summary():
    """Print summary and helpful commands"""
    
    print_header("SUMMARY & USEFUL COMMANDS")
    
    print("\n📝 Quick Reference:")
    print("\n  Large Data Storage Commands:")
    print("    - View all: sqlite3 ./data/large_tool_data.db 'SELECT * FROM large_tool_data'")
    print("    - Count: sqlite3 ./data/large_tool_data.db 'SELECT COUNT(*) FROM large_tool_data'")
    print("    - Cleanup: curl -X POST http://localhost:8000/cleanup/large-data")
    
    print("\n  ChromaDB Commands:")
    print("    - Python script: python3 -c 'import chromadb; ...'")
    print("    - Clear all: rm -rf ./chroma_data  (⚠️  Use with caution!)")
    
    print("\n  File Storage Commands:")
    print("    - List files: ls -lh ./data/large_tool_data_files/")
    print("    - Total size: du -sh ./data/large_tool_data_files/")
    print("    - View file: zcat ./data/large_tool_data_files/<ref_id>.json.gz | jq")
    
    print("\n  API Endpoints (if server running):")
    print("    - Memory stats: curl http://localhost:8000/memory/stats")
    print("    - Storage stats: curl http://localhost:8000/storage/stats")
    
    print("\n" + "=" * 80 + "\n")

def main():
    """Main inspection routine"""
    
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║              JK-AGENTS STORAGE SYSTEMS INSPECTOR                          ║")
    print("║              Comprehensive Storage Analysis Tool                           ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print(f"\nInspection Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Inspect all storage systems
    inspect_large_data_storage()
    inspect_chromadb()
    inspect_sqlite_checkpoints()
    print_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Inspection interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
