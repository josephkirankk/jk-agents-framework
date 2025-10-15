"""
Test Centralized Database Configuration

This test verifies that all database paths are properly centralized and
loaded from environment variables via the database_config module.
"""

import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database_config_module():
    """Test the database_config module loads correctly"""
    print("\n=== Testing Database Config Module ===")
    
    from app.database_config import (
        get_database_config,
        get_large_data_config,
        get_chromadb_path,
        reset_database_config
    )
    
    # Test default config
    print("\n1. Testing default configuration...")
    config = get_database_config()
    print(f"   Base path: {config.paths.base_path}")
    print(f"   Large data DB: {config.paths.large_data_db}")
    print(f"   Large data files: {config.paths.large_data_files}")
    print(f"   ChromaDB: {config.paths.chromadb}")
    assert config.paths.base_path.name == "data"
    print("   ✓ Default config loaded correctly")
    
    # Test test mode config
    print("\n2. Testing test mode configuration...")
    test_config = get_database_config(is_test_mode=True)
    print(f"   Base path: {test_config.paths.base_path}")
    print(f"   Large data DB: {test_config.paths.large_data_db}")
    assert "test" in str(test_config.paths.base_path)
    print("   ✓ Test config loaded correctly")
    
    # Test convenience functions
    print("\n3. Testing convenience functions...")
    large_data_cfg = get_large_data_config()
    print(f"   Large data config (app): {large_data_cfg}")
    assert "sqlite_path" in large_data_cfg
    
    large_data_cfg_core = get_large_data_config(format="core")
    print(f"   Large data config (core): {large_data_cfg_core}")
    assert "storage_path" in large_data_cfg_core
    
    chromadb_path = get_chromadb_path()
    print(f"   ChromaDB path: {chromadb_path}")
    assert "chromadb" in chromadb_path
    print("   ✓ Convenience functions work correctly")
    
    # Clean up
    reset_database_config()
    print("\n✓ Database config module test passed")


def test_large_data_storage_app():
    """Test app.memory.large_data_storage uses centralized config"""
    print("\n=== Testing app.memory.LargeDataStorage ===")
    
    from app.memory.large_data_storage import LargeDataStorage
    from app.database_config import reset_database_config
    
    # Reset to ensure fresh load
    reset_database_config()
    
    # Test with no config (should use centralized)
    print("\n1. Testing with no config (centralized)...")
    storage = LargeDataStorage()
    print(f"   DB path: {storage.db_path}")
    print(f"   Files path: {storage.file_storage_path}")
    assert "data" in str(storage.db_path)
    print("   ✓ Centralized config loaded correctly")
    
    # Test with custom config (should override)
    print("\n2. Testing with custom config...")
    custom_config = {
        "sqlite_path": "./test_custom/db.db",
        "file_path": "./test_custom/files/",
        "compression": False
    }
    storage_custom = LargeDataStorage(custom_config)
    print(f"   DB path: {storage_custom.db_path}")
    assert "test_custom" in str(storage_custom.db_path)
    print("   ✓ Custom config override works correctly")
    
    print("\n✓ app.memory.LargeDataStorage test passed")


def test_large_data_storage_core():
    """Test core.large_data_storage uses centralized config"""
    print("\n=== Testing core.LargeDataStorage ===")
    
    from core.large_data_storage import LargeDataStorage
    from app.database_config import reset_database_config
    
    # Reset to ensure fresh load
    reset_database_config()
    
    # Test with no paths (should use centralized)
    print("\n1. Testing with no paths (centralized)...")
    storage = LargeDataStorage()
    print(f"   DB path: {storage.storage_path}")
    print(f"   Files path: {storage.file_storage_path}")
    assert "data" in str(storage.storage_path)
    print("   ✓ Centralized config loaded correctly")
    
    # Test with custom paths (should override)
    print("\n2. Testing with custom paths...")
    storage_custom = LargeDataStorage(
        storage_path="./test_custom_core/db.db",
        file_storage_path="./test_custom_core/files/"
    )
    print(f"   DB path: {storage_custom.storage_path}")
    assert "test_custom_core" in str(storage_custom.storage_path)
    print("   ✓ Custom path override works correctly")
    
    print("\n✓ core.LargeDataStorage test passed")


def test_chromadb_backend():
    """Test ChromaDB backend uses centralized config"""
    print("\n=== Testing ChromaDB Backend ===")
    
    try:
        from app.memory.chromadb_backend import ChromaDBConfig
        from app.database_config import reset_database_config
        
        # Reset to ensure fresh load
        reset_database_config()
        
        # Test loading from env
        print("\n1. Testing ChromaDBConfig.load_from_env()...")
        config = ChromaDBConfig()
        config.load_from_env()
        print(f"   ChromaDB path: {config.path}")
        assert config.path is not None
        assert "chromadb" in str(config.path)
        print("   ✓ ChromaDB config loaded correctly")
        
        print("\n✓ ChromaDB backend test passed")
    except ImportError as e:
        print(f"\n⚠ ChromaDB not available, skipping: {e}")


def test_data_storage_and_retrieval():
    """Test that data can be stored and retrieved with centralized config"""
    print("\n=== Testing Data Storage and Retrieval ===")
    
    from app.memory.large_data_storage import LargeDataStorage
    from app.database_config import reset_database_config
    
    # Reset and use test mode
    reset_database_config()
    
    # Create storage with test mode config
    from app.database_config import get_database_config
    test_config = get_database_config(is_test_mode=True)
    storage = LargeDataStorage(test_config.get_large_data_config())
    
    print("\n1. Storing test data...")
    test_data = {
        "test": "data",
        "items": [1, 2, 3, 4, 5],
        "nested": {"key": "value"}
    }
    
    ref_id = "test_ref_centralized_config"
    storage_info = storage.store_large_data(ref_id, "test_tool", test_data)
    print(f"   Stored with reference: {ref_id}")
    print(f"   Storage info: {storage_info}")
    
    print("\n2. Retrieving test data...")
    retrieved = storage.retrieve_large_data(ref_id)
    print(f"   Retrieved: {retrieved}")
    assert retrieved == test_data
    print("   ✓ Data matches original")
    
    print("\n3. Checking storage stats...")
    stats = storage.get_storage_stats()
    print(f"   Total references: {stats.get('total_references', 0)}")
    print(f"   Total size: {stats.get('total_size_mb', 0):.2f} MB")
    
    print("\n✓ Data storage and retrieval test passed")


def test_environment_variable_override():
    """Test that environment variables properly override defaults"""
    print("\n=== Testing Environment Variable Override ===")
    
    from app.database_config import reset_database_config, get_database_config
    
    # Set custom env vars
    print("\n1. Setting custom environment variables...")
    os.environ["DB_BASE_PATH"] = "./custom_env_test"
    os.environ["LARGE_DATA_DB_PATH"] = "./custom_env_test/custom_db.db"
    
    # Reset to force reload
    reset_database_config()
    
    # Load config
    print("\n2. Loading config with custom env vars...")
    config = get_database_config(force_reload=True)
    print(f"   Base path: {config.paths.base_path}")
    print(f"   Large data DB: {config.paths.large_data_db}")
    
    assert "custom_env_test" in str(config.paths.base_path)
    assert "custom_db.db" in str(config.paths.large_data_db)
    print("   ✓ Environment variables override defaults correctly")
    
    # Clean up env vars
    del os.environ["DB_BASE_PATH"]
    del os.environ["LARGE_DATA_DB_PATH"]
    reset_database_config()
    
    print("\n✓ Environment variable override test passed")


def cleanup_test_directories():
    """Clean up any test directories created during testing"""
    print("\n=== Cleaning up test directories ===")
    test_dirs = [
        "./test_custom",
        "./test_custom_core",
        "./custom_env_test",
    ]
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
                print(f"   Removed {test_dir}")
            except Exception as e:
                print(f"   Warning: Could not remove {test_dir}: {e}")


def main():
    """Run all tests"""
    print("=" * 70)
    print("CENTRALIZED DATABASE CONFIGURATION TEST SUITE")
    print("=" * 70)
    
    try:
        # Run tests
        test_database_config_module()
        test_large_data_storage_app()
        test_large_data_storage_core()
        test_chromadb_backend()
        test_data_storage_and_retrieval()
        test_environment_variable_override()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nCentralized database configuration is working correctly!")
        print("All database paths are now loaded from environment variables.")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        cleanup_test_directories()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
