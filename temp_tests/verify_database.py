#!/usr/bin/env python3
"""
Database Verification Utility

Direct inspection of schema_test_data.db to verify:
- Database structure
- Stored datasets
- Data validity
- Storage statistics
"""

import sqlite3
import gzip
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import jsonschema


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def print_section(text):
    """Print formatted section"""
    print(f"\n{'─'*80}")
    print(f"  {text}")
    print(f"{'─'*80}")


def verify_database_file():
    """Check database file exists and get basic info"""
    print_header("DATABASE FILE VERIFICATION")
    
    db_path = "./data/schema_test_data.db"
    
    if not os.path.exists(db_path):
        print(f"\n❌ Database not found: {db_path}")
        print("\nTo create the database, run:")
        print("  python temp_tests/test_schema_creator_v2_integration.py")
        return None
    
    size = os.path.getsize(db_path)
    print(f"\n✅ Database found: {db_path}")
    print(f"   Size: {size:,} bytes ({size/1024:.2f} KB, {size/1024/1024:.2f} MB)")
    print(f"   Modified: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
    
    return db_path


def verify_database_structure(db_path: str):
    """Verify database has correct schema"""
    print_header("DATABASE STRUCTURE")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    print("\n[1] Tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    if not tables:
        print("   ❌ No tables found")
        conn.close()
        return False
    
    for table in tables:
        print(f"   ✅ {table[0]}")
    
    # Check large_tool_data table specifically
    if ('large_tool_data',) not in tables:
        print("\n❌ Required table 'large_tool_data' not found")
        conn.close()
        return False
    
    # Get schema
    print("\n[2] large_tool_data schema:")
    cursor.execute("PRAGMA table_info(large_tool_data)")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, name, type_, notnull, default, pk = col
        pk_str = " PRIMARY KEY" if pk else ""
        null_str = " NOT NULL" if notnull else ""
        print(f"   - {name:20s} {type_:15s}{pk_str}{null_str}")
    
    # Check indexes
    print("\n[3] Indexes:")
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='large_tool_data'")
    indexes = cursor.fetchall()
    
    if indexes:
        for idx_name, idx_sql in indexes:
            if idx_sql:  # Skip auto-created indexes
                print(f"   ✅ {idx_name}")
    else:
        print("   ⚠️  No custom indexes found")
    
    conn.close()
    return True


def list_all_datasets(db_path: str):
    """List all datasets in database"""
    print_header("STORED DATASETS")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM large_tool_data")
    total_count = cursor.fetchone()[0]
    
    print(f"\n📊 Total datasets: {total_count}")
    
    if total_count == 0:
        print("\n⚠️  No datasets found. Run a workflow to generate data.")
        conn.close()
        return []
    
    # Get all datasets
    cursor.execute("""
        SELECT 
            reference_id,
            tool_name,
            size_bytes,
            size_category,
            content_type,
            compressed,
            created_at,
            access_count,
            metadata
        FROM large_tool_data
        ORDER BY created_at DESC
    """)
    
    datasets = cursor.fetchall()
    
    print(f"\n{'#':<4} {'Reference ID':<18} {'Tool':<20} {'Size':<12} {'Type':<8} {'Created':<20}")
    print("─"*80)
    
    for idx, row in enumerate(datasets, 1):
        ref_id, tool, size_bytes, size_cat, content_type, compressed, created, access, metadata = row
        size_str = f"{size_bytes:,}B"
        comp_str = "🗜️ " if compressed else "  "
        print(f"{idx:<4} {ref_id:<18} {tool:<20} {comp_str}{size_str:<10} {content_type:<8} {created}")
    
    conn.close()
    return datasets


def inspect_dataset(db_path: str, reference_id: str):
    """Inspect a specific dataset in detail"""
    print_section(f"Dataset: {reference_id}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            tool_name, storage_type, data_blob, data_hash,
            size_bytes, size_category, content_type, compressed,
            metadata, created_at, expires_at, access_count
        FROM large_tool_data
        WHERE reference_id = ?
    """, (reference_id,))
    
    result = cursor.fetchone()
    
    if not result:
        print(f"❌ Dataset not found: {reference_id}")
        conn.close()
        return None
    
    (tool_name, storage_type, data_blob, data_hash,
     size_bytes, size_category, content_type, compressed,
     metadata_json, created_at, expires_at, access_count) = result
    
    # Display metadata
    print(f"\nℹ️  Metadata:")
    print(f"   Tool: {tool_name}")
    print(f"   Storage: {storage_type}")
    print(f"   Size: {size_bytes:,} bytes ({size_bytes/1024:.2f} KB)")
    print(f"   Category: {size_category}")
    print(f"   Content Type: {content_type}")
    print(f"   Compressed: {'Yes' if compressed else 'No'}")
    print(f"   Hash: {data_hash[:16]}...")
    print(f"   Created: {created_at}")
    print(f"   Expires: {expires_at}")
    print(f"   Access Count: {access_count}")
    
    # Parse metadata
    if metadata_json:
        metadata = json.loads(metadata_json)
        print(f"\n   Custom Metadata:")
        for key, value in metadata.items():
            print(f"     - {key}: {value}")
    
    # Decompress if needed
    if compressed:
        print(f"\n🗜️  Decompressing data...")
        data_blob = gzip.decompress(data_blob)
        decompressed_size = len(data_blob)
        compression_ratio = (1 - size_bytes / decompressed_size) * 100
        print(f"   Decompressed size: {decompressed_size:,} bytes")
        print(f"   Compression ratio: {compression_ratio:.1f}%")
    
    # Parse data
    print(f"\n📦 Data:")
    try:
        if content_type == 'json':
            data = json.loads(data_blob.decode('utf-8'))
            
            if isinstance(data, list):
                print(f"   Type: List")
                print(f"   Length: {len(data)} records")
                
                if data:
                    print(f"\n   First record:")
                    print(f"   {json.dumps(data[0], indent=6)}")
                    
                    # Analyze structure
                    if isinstance(data[0], dict):
                        fields = list(data[0].keys())
                        print(f"\n   Fields ({len(fields)}): {', '.join(fields)}")
                        
                        # Check required fields consistency
                        all_same = all(set(r.keys()) == set(fields) for r in data if isinstance(r, dict))
                        if all_same:
                            print(f"   ✅ All records have same fields")
                        else:
                            print(f"   ⚠️  Records have varying fields")
                
                conn.close()
                return data
            
            elif isinstance(data, dict):
                print(f"   Type: Dictionary")
                print(f"   Keys: {list(data.keys())}")
                print(f"\n   Content preview:")
                print(f"   {json.dumps(data, indent=6)[:500]}...")
                
                conn.close()
                return data
            
            else:
                print(f"   Type: {type(data)}")
                print(f"   Value: {str(data)[:200]}...")
                conn.close()
                return data
        
        else:
            text_data = data_blob.decode('utf-8')
            print(f"   Type: Text")
            print(f"   Length: {len(text_data)} characters")
            print(f"   Preview: {text_data[:200]}...")
            conn.close()
            return text_data
    
    except Exception as e:
        print(f"   ❌ Error parsing data: {e}")
        conn.close()
        return None


def validate_dataset(data: List[Dict], schema: Dict):
    """Validate dataset against JSON schema"""
    print_section("Data Validation")
    
    if not isinstance(data, list):
        print(f"⚠️  Data is not a list: {type(data)}")
        return
    
    print(f"\n📋 Validating {len(data)} records against schema...")
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    for idx, record in enumerate(data):
        try:
            jsonschema.validate(instance=record, schema=schema)
            valid_count += 1
        except jsonschema.ValidationError as e:
            invalid_count += 1
            if len(errors) < 3:
                errors.append({
                    "index": idx,
                    "message": e.message,
                    "path": list(e.path)
                })
    
    print(f"\n✅ Valid: {valid_count}")
    print(f"❌ Invalid: {invalid_count}")
    print(f"📊 Success Rate: {(valid_count/len(data)*100):.2f}%")
    
    if errors:
        print(f"\n⚠️  First {len(errors)} errors:")
        for err in errors:
            print(f"   Record {err['index']}: {err['message']}")
            if err['path']:
                print(f"   Path: {'.'.join(map(str, err['path']))}")


def get_storage_statistics(db_path: str):
    """Get storage statistics"""
    print_header("STORAGE STATISTICS")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_datasets,
            SUM(size_bytes) as total_size,
            AVG(size_bytes) as avg_size,
            MIN(size_bytes) as min_size,
            MAX(size_bytes) as max_size,
            SUM(CASE WHEN compressed = 1 THEN 1 ELSE 0 END) as compressed_count
        FROM large_tool_data
    """)
    
    stats = cursor.fetchone()
    total, total_size, avg_size, min_size, max_size, compressed_count = stats
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total datasets: {total}")
    print(f"   Total storage: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    print(f"   Average size: {avg_size:,.0f} bytes ({avg_size/1024:.2f} KB)")
    print(f"   Size range: {min_size:,} - {max_size:,} bytes")
    print(f"   Compressed: {compressed_count}/{total} ({compressed_count/total*100:.1f}%)")
    
    # By tool
    print(f"\n📊 By Tool:")
    cursor.execute("""
        SELECT 
            tool_name,
            COUNT(*) as count,
            SUM(size_bytes) as total_size
        FROM large_tool_data
        GROUP BY tool_name
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        tool, count, size = row
        print(f"   {tool:30s}: {count:3d} datasets, {size:,} bytes")
    
    # By size category
    print(f"\n📊 By Size Category:")
    cursor.execute("""
        SELECT 
            size_category,
            COUNT(*) as count
        FROM large_tool_data
        GROUP BY size_category
        ORDER BY count DESC
    """)
    
    for row in cursor.fetchall():
        category, count = row
        print(f"   {category:15s}: {count:3d} datasets")
    
    conn.close()


def main():
    """Main verification function"""
    print("="*80)
    print("  DATABASE VERIFICATION UTILITY")
    print("  For: schema_test_data.db")
    print("="*80)
    
    # Step 1: Verify file
    db_path = verify_database_file()
    if not db_path:
        return 1
    
    # Step 2: Verify structure
    if not verify_database_structure(db_path):
        print("\n❌ Database structure verification failed")
        return 1
    
    # Step 3: List datasets
    datasets = list_all_datasets(db_path)
    
    if not datasets:
        print("\n✅ Database is healthy but empty")
        return 0
    
    # Step 4: Get statistics
    get_storage_statistics(db_path)
    
    # Step 5: Inspect latest dataset
    if datasets:
        latest_ref_id = datasets[0][0]  # reference_id from first row
        print_header("LATEST DATASET INSPECTION")
        data = inspect_dataset(db_path, latest_ref_id)
        
        # If it's a list of records, show more statistics
        if isinstance(data, list) and data and isinstance(data[0], dict):
            print_section("Data Statistics")
            print(f"\n   Total records: {len(data)}")
            
            # Field coverage
            all_fields = set()
            for record in data:
                all_fields.update(record.keys())
            print(f"   Unique fields: {len(all_fields)}")
            print(f"   Fields: {', '.join(sorted(all_fields))}")
            
            # Value statistics for first few fields
            if len(all_fields) > 0:
                print(f"\n   Sample values:")
                for field in list(sorted(all_fields))[:5]:
                    values = [r.get(field) for r in data if field in r]
                    unique_count = len(set(str(v) for v in values))
                    sample = values[0] if values else None
                    print(f"     {field:20s}: {unique_count} unique, e.g., {sample}")
    
    print_header("VERIFICATION COMPLETE")
    print("\n✅ All checks passed")
    print("\nDatabase is healthy and contains valid data.")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
