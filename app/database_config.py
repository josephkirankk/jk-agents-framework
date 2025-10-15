"""
Centralized Database Configuration Module

This module provides centralized configuration for all database paths used across
the JK Agents framework. All database paths are loaded from environment variables
to ensure consistency and avoid hardcoded paths.

Environment Variables:
    DB_BASE_PATH: Base directory for all database files (default: ./data)
    LARGE_DATA_DB_PATH: Large data storage database path
    LARGE_DATA_FILES_PATH: Large data file storage directory
    CHROMADB_PATH: ChromaDB persistent storage path
    TEST_DB_BASE_PATH: Base directory for test databases
    LARGE_DATA_COMPRESSION_ENABLED: Enable compression for large data
    LARGE_DATA_MAX_SQLITE_SIZE_MB: Max SQLite storage size
    LARGE_DATA_TOKEN_THRESHOLD: Token threshold for large data handling
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

log = logging.getLogger(__name__)


@dataclass
class DatabasePaths:
    """Container for database paths"""
    base_path: Path
    large_data_db: Path
    large_data_files: Path
    chromadb: Path
    
    def ensure_directories(self):
        """Create all necessary directories if they don't exist"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.large_data_files.mkdir(parents=True, exist_ok=True)
        self.chromadb.mkdir(parents=True, exist_ok=True)
        # Parent directory for DB file
        self.large_data_db.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class LargeDataConfig:
    """Configuration for large data storage"""
    db_path: Path
    files_path: Path
    compression_enabled: bool
    max_sqlite_size_mb: int
    token_threshold: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for LargeDataStorage"""
        return {
            "sqlite_path": str(self.db_path),
            "file_path": str(self.files_path),
            "compression": self.compression_enabled,
            "max_sqlite_size_mb": self.max_sqlite_size_mb,
        }
    
    def to_core_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for core.LargeDataStorage"""
        return {
            "storage_path": str(self.db_path),
            "file_storage_path": str(self.files_path),
            "compression_enabled": self.compression_enabled,
            "max_file_size_mb": self.max_sqlite_size_mb,
        }


class DatabaseConfig:
    """
    Centralized database configuration manager
    
    This class loads database configuration from environment variables
    and provides consistent paths across the entire application.
    """
    
    def __init__(self, is_test_mode: bool = False):
        """
        Initialize database configuration
        
        Args:
            is_test_mode: If True, use test database paths
        """
        self.is_test_mode = is_test_mode
        self._load_config()
        log.info(f"Database config initialized (test_mode={is_test_mode})")
    
    def _load_config(self):
        """Load configuration from environment variables"""
        if self.is_test_mode:
            # Test mode paths
            base_path = os.getenv("TEST_DB_BASE_PATH", "./test_data")
            large_data_db = os.getenv("TEST_LARGE_DATA_DB_PATH", 
                                     f"{base_path}/large_data_storage.db")
            large_data_files = os.getenv("TEST_LARGE_DATA_FILES_PATH", 
                                        f"{base_path}/large_files")
            chromadb_path = os.getenv("TEST_CHROMADB_PATH", 
                                     f"{base_path}/chromadb")
        else:
            # Production paths with backward compatibility for old env var names
            base_path = os.getenv("DB_BASE_PATH", "./data")
            
            # LARGE_DATA_DB_PATH (new) or LARGE_DATA_SQLITE_PATH (old, deprecated)
            large_data_db = os.getenv("LARGE_DATA_DB_PATH") or \
                           os.getenv("LARGE_DATA_SQLITE_PATH") or \
                           f"{base_path}/large_data_storage.db"
            
            # LARGE_DATA_FILES_PATH (new) or LARGE_DATA_FILE_PATH (old, deprecated)
            large_data_files = os.getenv("LARGE_DATA_FILES_PATH") or \
                              os.getenv("LARGE_DATA_FILE_PATH") or \
                              f"{base_path}/large_files"
            
            chromadb_path = os.getenv("CHROMADB_PATH", 
                                     f"{base_path}/chromadb")
        
        # Create paths object
        self.paths = DatabasePaths(
            base_path=Path(base_path),
            large_data_db=Path(large_data_db),
            large_data_files=Path(large_data_files),
            chromadb=Path(chromadb_path)
        )
        
        # Large data configuration with backward compatibility
        # LARGE_DATA_COMPRESSION_ENABLED (new) or LARGE_DATA_COMPRESSION (old, deprecated)
        compression_str = os.getenv("LARGE_DATA_COMPRESSION_ENABLED") or \
                         os.getenv("LARGE_DATA_COMPRESSION") or \
                         "true"
        
        # LARGE_DATA_MAX_SQLITE_SIZE_MB (new) or LARGE_DATA_MAX_SQLITE_MB (old, deprecated)
        max_size_str = os.getenv("LARGE_DATA_MAX_SQLITE_SIZE_MB") or \
                      os.getenv("LARGE_DATA_MAX_SQLITE_MB") or \
                      "50"
        
        self.large_data = LargeDataConfig(
            db_path=self.paths.large_data_db,
            files_path=self.paths.large_data_files,
            compression_enabled=compression_str.lower() in ("true", "1", "yes"),
            max_sqlite_size_mb=int(max_size_str),
            token_threshold=int(os.getenv("LARGE_DATA_TOKEN_THRESHOLD", "1000"))
        )
    
    def ensure_directories(self):
        """Create all necessary database directories"""
        self.paths.ensure_directories()
        log.info(f"Database directories ensured at {self.paths.base_path}")
    
    def get_chromadb_config(self) -> Dict[str, Any]:
        """Get ChromaDB configuration"""
        return {
            "path": str(self.paths.chromadb)
        }
    
    def get_large_data_config(self, format: str = "app") -> Dict[str, Any]:
        """
        Get large data storage configuration
        
        Args:
            format: "app" for app.memory.LargeDataStorage or "core" for core.LargeDataStorage
        
        Returns:
            Configuration dictionary
        """
        if format == "core":
            return self.large_data.to_core_dict()
        return self.large_data.to_dict()
    
    def override_path(self, path_type: str, new_path: str):
        """
        Override a specific path (useful for testing or specific use cases)
        
        Args:
            path_type: One of "base", "large_data_db", "large_data_files", "chromadb"
            new_path: New path to use
        """
        path_obj = Path(new_path)
        
        if path_type == "base":
            self.paths.base_path = path_obj
        elif path_type == "large_data_db":
            self.paths.large_data_db = path_obj
            self.large_data.db_path = path_obj
        elif path_type == "large_data_files":
            self.paths.large_data_files = path_obj
            self.large_data.files_path = path_obj
        elif path_type == "chromadb":
            self.paths.chromadb = path_obj
        else:
            raise ValueError(f"Unknown path_type: {path_type}")
        
        log.info(f"Overridden {path_type} path to {new_path}")
    
    def __repr__(self) -> str:
        return (
            f"DatabaseConfig(test_mode={self.is_test_mode}, "
            f"base={self.paths.base_path}, "
            f"large_data_db={self.paths.large_data_db})"
        )


# Global configuration instances
_default_config: Optional[DatabaseConfig] = None
_test_config: Optional[DatabaseConfig] = None


def get_database_config(is_test_mode: bool = False, force_reload: bool = False) -> DatabaseConfig:
    """
    Get the global database configuration instance
    
    Args:
        is_test_mode: If True, return test configuration
        force_reload: If True, reload configuration from environment
    
    Returns:
        DatabaseConfig instance
    """
    global _default_config, _test_config
    
    if is_test_mode:
        if _test_config is None or force_reload:
            _test_config = DatabaseConfig(is_test_mode=True)
            _test_config.ensure_directories()
        return _test_config
    else:
        if _default_config is None or force_reload:
            _default_config = DatabaseConfig(is_test_mode=False)
            _default_config.ensure_directories()
        return _default_config


def reset_database_config():
    """Reset global configuration (useful for testing)"""
    global _default_config, _test_config
    _default_config = None
    _test_config = None


# Convenience functions for quick access
def get_large_data_config(is_test_mode: bool = False, format: str = "app") -> Dict[str, Any]:
    """
    Get large data storage configuration
    
    Args:
        is_test_mode: If True, use test paths
        format: "app" or "core" for different LargeDataStorage implementations
    
    Returns:
        Configuration dictionary ready to pass to LargeDataStorage
    """
    config = get_database_config(is_test_mode)
    return config.get_large_data_config(format)


def get_chromadb_path(is_test_mode: bool = False) -> str:
    """
    Get ChromaDB storage path
    
    Args:
        is_test_mode: If True, use test path
    
    Returns:
        ChromaDB path as string
    """
    config = get_database_config(is_test_mode)
    return str(config.paths.chromadb)


if __name__ == "__main__":
    # Demo usage
    print("=== Default Configuration ===")
    config = get_database_config()
    print(config)
    print(f"\nLarge Data Config (app format): {config.get_large_data_config('app')}")
    print(f"Large Data Config (core format): {config.get_large_data_config('core')}")
    print(f"ChromaDB Config: {config.get_chromadb_config()}")
    
    print("\n=== Test Configuration ===")
    test_config = get_database_config(is_test_mode=True)
    print(test_config)
    print(f"\nLarge Data Config: {test_config.get_large_data_config()}")
    
    print("\n=== Convenience Functions ===")
    print(f"Large Data Config: {get_large_data_config()}")
    print(f"ChromaDB Path: {get_chromadb_path()}")
