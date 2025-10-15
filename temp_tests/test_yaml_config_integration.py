"""
Test YAML Config Integration with Centralized Database Configuration

This test verifies that the YAML config files work correctly with the
centralized database configuration system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_yaml_env_vars():
    """Test that YAML environment variables are properly recognized"""
    print("\n=== Testing YAML Environment Variables ===")
    
    # Simulate environment variables from YAML config
    os.environ["LARGE_DATA_DB_PATH"] = "./data/schema_test_data.db"
    os.environ["LARGE_DATA_FILES_PATH"] = "./data/schema_test_files/"
    os.environ["LARGE_DATA_COMPRESSION_ENABLED"] = "true"
    os.environ["LARGE_DATA_MAX_SQLITE_SIZE_MB"] = "100"
    
    from app.database_config import reset_database_config, get_database_config
    
    # Reset to force reload
    reset_database_config()
    
    print("\n1. Loading config with YAML-style env vars...")
    config = get_database_config(force_reload=True)
    
    print(f"   DB Path: {config.paths.large_data_db}")
    print(f"   Files Path: {config.paths.large_data_files}")
    print(f"   Compression: {config.large_data.compression_enabled}")
    print(f"   Max Size: {config.large_data.max_sqlite_size_mb} MB")
    
    assert "schema_test_data.db" in str(config.paths.large_data_db)
    assert "schema_test_files" in str(config.paths.large_data_files)
    assert config.large_data.compression_enabled == True
    assert config.large_data.max_sqlite_size_mb == 100
    
    print("   ✓ YAML environment variables loaded correctly")
    
    # Clean up
    del os.environ["LARGE_DATA_DB_PATH"]
    del os.environ["LARGE_DATA_FILES_PATH"]
    del os.environ["LARGE_DATA_COMPRESSION_ENABLED"]
    del os.environ["LARGE_DATA_MAX_SQLITE_SIZE_MB"]
    reset_database_config()
    
    print("\n✓ YAML environment variables test passed")


def test_backward_compatibility():
    """Test backward compatibility with old environment variable names"""
    print("\n=== Testing Backward Compatibility ===")
    
    # Use OLD environment variable names (deprecated but should still work)
    os.environ["LARGE_DATA_SQLITE_PATH"] = "./data/old_style.db"
    os.environ["LARGE_DATA_FILE_PATH"] = "./data/old_style_files/"
    os.environ["LARGE_DATA_COMPRESSION"] = "false"
    os.environ["LARGE_DATA_MAX_SQLITE_MB"] = "75"
    
    from app.database_config import reset_database_config, get_database_config
    
    # Reset to force reload
    reset_database_config()
    
    print("\n1. Loading config with OLD env var names...")
    config = get_database_config(force_reload=True)
    
    print(f"   DB Path: {config.paths.large_data_db}")
    print(f"   Files Path: {config.paths.large_data_files}")
    print(f"   Compression: {config.large_data.compression_enabled}")
    print(f"   Max Size: {config.large_data.max_sqlite_size_mb} MB")
    
    assert "old_style.db" in str(config.paths.large_data_db)
    assert "old_style_files" in str(config.paths.large_data_files)
    assert config.large_data.compression_enabled == False
    assert config.large_data.max_sqlite_size_mb == 75
    
    print("   ✓ Old environment variable names still work")
    
    # Clean up
    del os.environ["LARGE_DATA_SQLITE_PATH"]
    del os.environ["LARGE_DATA_FILE_PATH"]
    del os.environ["LARGE_DATA_COMPRESSION"]
    del os.environ["LARGE_DATA_MAX_SQLITE_MB"]
    reset_database_config()
    
    print("\n✓ Backward compatibility test passed")


def test_storage_with_yaml_config():
    """Test that storage systems work with YAML-style config"""
    print("\n=== Testing Storage with YAML Config ===")
    
    # Set YAML-style environment variables
    os.environ["LARGE_DATA_DB_PATH"] = "./test_yaml_integration/test.db"
    os.environ["LARGE_DATA_FILES_PATH"] = "./test_yaml_integration/files/"
    os.environ["LARGE_DATA_COMPRESSION_ENABLED"] = "true"
    
    from app.database_config import reset_database_config
    from app.memory.large_data_storage import LargeDataStorage
    
    # Reset to force reload
    reset_database_config()
    
    print("\n1. Initializing LargeDataStorage with YAML env vars...")
    storage = LargeDataStorage()
    
    print(f"   DB Path: {storage.db_path}")
    print(f"   Files Path: {storage.file_storage_path}")
    print(f"   Compression: {storage.compression_enabled}")
    
    assert "test_yaml_integration" in str(storage.db_path)
    assert "test_yaml_integration" in str(storage.file_storage_path)
    
    print("   ✓ Storage initialized with YAML config")
    
    print("\n2. Testing data storage and retrieval...")
    test_data = {"yaml_test": "data", "items": [1, 2, 3]}
    ref_id = "yaml_test_ref"
    
    storage_info = storage.store_large_data(ref_id, "yaml_test_tool", test_data)
    print(f"   Stored: {ref_id}")
    
    retrieved = storage.retrieve_large_data(ref_id)
    print(f"   Retrieved: {retrieved}")
    
    assert retrieved == test_data
    print("   ✓ Data storage and retrieval works")
    
    # Clean up
    import shutil
    if os.path.exists("./test_yaml_integration"):
        shutil.rmtree("./test_yaml_integration")
    
    del os.environ["LARGE_DATA_DB_PATH"]
    del os.environ["LARGE_DATA_FILES_PATH"]
    del os.environ["LARGE_DATA_COMPRESSION_ENABLED"]
    reset_database_config()
    
    print("\n✓ Storage with YAML config test passed")


def test_new_vs_old_env_vars():
    """Test that new env vars take precedence over old ones"""
    print("\n=== Testing New vs Old Environment Variables ===")
    
    # Set BOTH old and new - new should take precedence
    os.environ["LARGE_DATA_SQLITE_PATH"] = "./data/old.db"  # Old (deprecated)
    os.environ["LARGE_DATA_DB_PATH"] = "./data/new.db"      # New (should win)
    
    os.environ["LARGE_DATA_FILE_PATH"] = "./data/old_files/"      # Old
    os.environ["LARGE_DATA_FILES_PATH"] = "./data/new_files/"     # New (should win)
    
    from app.database_config import reset_database_config, get_database_config
    
    reset_database_config()
    
    print("\n1. Loading config with both old and new env vars...")
    config = get_database_config(force_reload=True)
    
    print(f"   DB Path: {config.paths.large_data_db}")
    print(f"   Files Path: {config.paths.large_data_files}")
    
    # New variables should take precedence
    assert "new.db" in str(config.paths.large_data_db)
    assert "new_files" in str(config.paths.large_data_files)
    
    print("   ✓ New environment variables take precedence")
    
    # Clean up
    del os.environ["LARGE_DATA_SQLITE_PATH"]
    del os.environ["LARGE_DATA_DB_PATH"]
    del os.environ["LARGE_DATA_FILE_PATH"]
    del os.environ["LARGE_DATA_FILES_PATH"]
    reset_database_config()
    
    print("\n✓ Precedence test passed")


def main():
    """Run all tests"""
    print("=" * 70)
    print("YAML CONFIG INTEGRATION TEST SUITE")
    print("=" * 70)
    
    try:
        test_yaml_env_vars()
        test_backward_compatibility()
        test_storage_with_yaml_config()
        test_new_vs_old_env_vars()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nYAML config files are now compatible with centralized database config!")
        print("Both old and new environment variable names are supported.")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
