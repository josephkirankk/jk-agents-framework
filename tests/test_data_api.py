#!/usr/bin/env python3
"""
Test script for the Large Data Retrieval API

This script tests the REST API endpoints for retrieving stored JSON data
from the SQLite database.
"""

import sys
import os
import json
import sqlite3
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the API functions directly
from litellm_api import get_database_connection, validate_reference_id

def test_validate_reference_id():
    """Test reference ID validation"""
    print("\n" + "="*80)
    print("TEST 1: Reference ID Validation")
    print("="*80)
    
    # Valid reference IDs
    valid_ids = [
        "ref_fd05f4970f14",
        "ref_abc123def456",
        "ref_000000000000",
        "ref_ffffffffffffffff"[:16]  # ref_ffffffffffff
    ]
    
    for ref_id in valid_ids:
        result = validate_reference_id(ref_id)
        print(f"✓ {ref_id}: {result}")
        assert result == True, f"Expected True for {ref_id}"
    
    # Invalid reference IDs
    invalid_ids = [
        "ref_",
        "ref_123",
        "ref_ABCDEF123456",  # uppercase
        "ref_xyz123abc456",  # contains x, y, z
        "fd05f4970f14",  # missing ref_ prefix
        "ref_fd05f4970f14extra",  # too long
    ]
    
    for ref_id in invalid_ids:
        result = validate_reference_id(ref_id)
        print(f"✗ {ref_id}: {result}")
        assert result == False, f"Expected False for {ref_id}"
    
    print("\n✅ All validation tests passed!")


def test_database_connection():
    """Test database connection"""
    print("\n" + "="*80)
    print("TEST 2: Database Connection")
    print("="*80)
    
    try:
        conn = get_database_connection()
        print(f"✓ Database connection successful")
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM large_tool_data")
        count = cursor.fetchone()[0]
        print(f"✓ Total datasets in database: {count}")
        
        conn.close()
        print("\n✅ Database connection test passed!")
        return True
    except Exception as e:
        print(f"\n❌ Database connection test failed: {e}")
        return False


def test_retrieve_data():
    """Test data retrieval"""
    print("\n" + "="*80)
    print("TEST 3: Data Retrieval")
    print("="*80)
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get the most recent reference ID
        cursor.execute("""
            SELECT reference_id, metadata, size_bytes, compressed
            FROM large_tool_data
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            print("❌ No data found in database")
            conn.close()
            return False
        
        reference_id, metadata_json, size_bytes, compressed = row
        
        print(f"✓ Found reference ID: {reference_id}")
        print(f"  - Size: {size_bytes:,} bytes ({size_bytes / 1024 / 1024:.2f} MB)")
        print(f"  - Compressed: {bool(compressed)}")
        
        # Parse metadata
        metadata = json.loads(metadata_json) if metadata_json else {}
        print(f"  - Metadata: {json.dumps(metadata, indent=4)}")
        
        # Retrieve the actual data
        cursor.execute("""
            SELECT data_blob, compressed, content_type
            FROM large_tool_data
            WHERE reference_id = ?
        """, (reference_id,))
        
        data_row = cursor.fetchone()
        if not data_row:
            print(f"❌ Data not found for reference ID: {reference_id}")
            conn.close()
            return False
        
        data_blob, compressed, content_type = data_row
        
        # Decompress if needed
        if compressed:
            import gzip
            data_bytes = gzip.decompress(data_blob)
            print(f"  - Decompressed: {len(data_blob):,} → {len(data_bytes):,} bytes")
        else:
            data_bytes = data_blob
        
        # Deserialize
        if content_type == 'json':
            data_str = data_bytes.decode('utf-8')
            data = json.loads(data_str)
            
            if isinstance(data, list):
                print(f"  - Data type: list with {len(data)} records")
                print(f"  - First record: {json.dumps(data[0], indent=4)}")
            elif isinstance(data, dict):
                print(f"  - Data type: dict with {len(data)} keys")
                print(f"  - Keys: {list(data.keys())[:10]}")
            else:
                print(f"  - Data type: {type(data).__name__}")
        else:
            print(f"  - Content type: {content_type}")
            print(f"  - Data preview: {data_bytes[:100].decode('utf-8', errors='ignore')}")
        
        conn.close()
        print("\n✅ Data retrieval test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Data retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_simulation():
    """Simulate the API endpoint logic"""
    print("\n" + "="*80)
    print("TEST 4: API Endpoint Simulation")
    print("="*80)
    
    # Use the example reference ID from the user
    reference_id = "ref_fd05f4970f14"
    
    print(f"Testing with reference ID: {reference_id}")
    
    # Validate reference ID
    if not validate_reference_id(reference_id):
        print(f"❌ Invalid reference ID format: {reference_id}")
        return False
    
    print(f"✓ Reference ID format is valid")
    
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Query the database
        query = """
            SELECT 
                reference_id,
                tool_name,
                storage_type,
                data_blob,
                compressed,
                content_type,
                size_bytes,
                metadata,
                created_at,
                access_count
            FROM large_tool_data
            WHERE reference_id = ?
        """
        
        cursor.execute(query, (reference_id,))
        row = cursor.fetchone()
        
        if not row:
            print(f"❌ Reference ID '{reference_id}' not found in database")
            conn.close()
            return False
        
        print(f"✓ Reference ID found in database")
        
        # Extract row data
        (ref_id, tool_name, storage_type, data_blob, compressed, 
         content_type, size_bytes, metadata_json, created_at, access_count) = row
        
        # Parse metadata
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        print(f"\nMetadata:")
        print(f"  - Tool name: {tool_name}")
        print(f"  - Storage type: {storage_type}")
        print(f"  - Content type: {content_type}")
        print(f"  - Size: {size_bytes:,} bytes ({size_bytes / 1024 / 1024:.2f} MB)")
        print(f"  - Compressed: {bool(compressed)}")
        print(f"  - Created at: {created_at}")
        print(f"  - Access count: {access_count}")
        print(f"  - Metadata: {json.dumps(metadata, indent=4)}")
        
        # Decompress data if needed
        if compressed:
            import gzip
            data_bytes = gzip.decompress(data_blob)
            print(f"\n✓ Decompressed: {len(data_blob):,} → {len(data_bytes):,} bytes")
        else:
            data_bytes = data_blob
        
        # Deserialize data
        if content_type == 'json':
            data_str = data_bytes.decode('utf-8')
            data = json.loads(data_str)
            
            print(f"\nData:")
            if isinstance(data, list):
                print(f"  - Type: list")
                print(f"  - Record count: {len(data)}")
                print(f"  - First record:")
                print(f"    {json.dumps(data[0], indent=6)}")
                print(f"  - Last record:")
                print(f"    {json.dumps(data[-1], indent=6)}")
            elif isinstance(data, dict):
                print(f"  - Type: dict")
                print(f"  - Keys: {list(data.keys())[:10]}")
            else:
                print(f"  - Type: {type(data).__name__}")
        
        # Build response (as the API would)
        response = {
            "status": "success",
            "reference_id": ref_id,
            "data": data if content_type == 'json' else data_bytes.decode('utf-8'),
            "metadata": {
                "tool_name": tool_name,
                "storage_type": storage_type,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "compressed": bool(compressed),
                "created_at": created_at,
                "access_count": access_count + 1,
                **metadata
            }
        }
        
        print(f"\n✓ API Response structure:")
        print(f"  - Status: {response['status']}")
        print(f"  - Reference ID: {response['reference_id']}")
        print(f"  - Data type: {type(response['data']).__name__}")
        if isinstance(response['data'], list):
            print(f"  - Data length: {len(response['data'])} records")
        print(f"  - Metadata keys: {list(response['metadata'].keys())}")
        
        conn.close()
        print("\n✅ API endpoint simulation test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ API endpoint simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("LARGE DATA RETRIEVAL API - TEST SUITE")
    print("="*80)
    
    # Run all tests
    results = []
    
    results.append(("Reference ID Validation", test_validate_reference_id))
    results.append(("Database Connection", test_database_connection))
    results.append(("Data Retrieval", test_retrieve_data))
    results.append(("API Endpoint Simulation", test_api_simulation))
    
    # Execute tests
    passed = 0
    failed = 0
    
    for test_name, test_func in results:
        try:
            if callable(test_func):
                success = test_func()
            else:
                success = test_func
            
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    print("="*80)
    
    sys.exit(0 if failed == 0 else 1)

