#!/usr/bin/env python3
"""
Quick test to verify SQLite connection pool works correctly.
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.memory.large_data_storage import LargeDataStorage

def test_connection_pool():
    """Test that connection pool is properly initialized and used."""
    print("\n🔍 Testing SQLite Connection Pool...")
    
    # Create temp directory for test
    temp_dir = tempfile.mkdtemp()
    try:
        # Initialize storage with connection pool
        config = {
            "sqlite_path": f"{temp_dir}/test.db",
            "file_path": f"{temp_dir}/files/",
            "connection_pool_size": 5,
            "compression": True
        }
        
        storage = LargeDataStorage(config)
        
        # Verify pool is initialized
        assert storage._pool_initialized, "Pool not initialized"
        assert storage._connection_pool.qsize() == 5, f"Expected 5 connections, got {storage._connection_pool.qsize()}"
        print("✅ Connection pool initialized with 5 connections")
        
        # Test storing data
        test_data = {"test": "data", "items": list(range(100))}
        info = storage.store_large_data(
            reference_id="test_ref_001",
            tool_name="test_tool",
            data=test_data
        )
        print(f"✅ Stored data: {info.size_mb:.4f}MB as {info.storage_type}")
        
        # Test retrieving data
        retrieved = storage.retrieve_large_data("test_ref_001")
        assert retrieved == test_data, "Data mismatch!"
        print("✅ Retrieved data successfully")
        
        # Verify pool still has connections
        assert storage._connection_pool.qsize() == 5, "Pool size changed unexpectedly"
        print("✅ Pool size maintained after operations")
        
        # Test stats
        stats = storage.get_storage_stats()
        print(f"✅ Storage stats: {stats['total_references']} references, {stats['total_size_mb']:.2f}MB")
        
        # Test cleanup
        storage.close_pool()
        assert storage._connection_pool.qsize() == 0, "Pool not emptied"
        assert not storage._pool_initialized, "Pool still marked as initialized"
        print("✅ Pool closed successfully")
        
        print("\n✅ All connection pool tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_connection_pool()
    sys.exit(0 if success else 1)
