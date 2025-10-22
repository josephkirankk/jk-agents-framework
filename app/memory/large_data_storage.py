"""
Large Data Storage System for JK Agents Framework

Handles storage and retrieval of large tool call results using optimized
multi-tier storage: SQLite for metadata and medium data, File system for huge data.
ChromaDB is reserved for references and conversation memory only.
"""

import sqlite3
import json
import os
import gzip
import pickle
import hashlib
import logging
import threading
import queue
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from contextlib import contextmanager

# Import centralized database configuration
try:
    from app.database_config import get_large_data_config
except ImportError:
    # Fallback for standalone usage
    get_large_data_config = None

log = logging.getLogger(__name__)

class DataSize(Enum):
    SMALL = "small"      # < 1MB - SQLite blob
    MEDIUM = "medium"    # 1-50MB - Compressed SQLite
    LARGE = "large"      # 50-500MB - File system
    HUGE = "huge"        # >500MB - File system with chunking

@dataclass
class StorageInfo:
    reference_id: str
    storage_type: str
    size_bytes: int
    size_mb: float
    size_category: DataSize
    content_type: str
    compressed: bool
    file_path: Optional[str] = None

class LargeDataStorage:
    """Optimized storage for large tool call data - separate from ChromaDB

    Thread Safety:
    - Uses SQLite WAL mode for concurrent reads/writes
    - Reference IDs are UUID4-based (cryptographically unique)
    - Database operations use thread-safe connection with check_same_thread=False
    - Write operations are protected by threading.Lock for safety
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Large Data Storage
        
        Args:
            config: Optional configuration dict. If None, loads from environment via database_config.
                   Expected keys:
                   - sqlite_path: Path to SQLite database
                   - file_path: Path to file storage directory
                   - compression: Enable compression (default: True)
                   - max_sqlite_size_mb: Max SQLite size in MB (default: 50)
        """
        # Load from centralized config if no config provided
        if config is None:
            if get_large_data_config is not None:
                config = get_large_data_config(format="app")
                log.info("Using centralized database configuration")
            else:
                # Fallback to defaults
                config = {
                    "sqlite_path": "./data/large_data_storage.db",
                    "file_path": "./data/large_files/",
                    "compression": True,
                    "max_sqlite_size_mb": 50
                }
                log.warning("Using fallback database configuration")
        
        self.db_path = config.get("sqlite_path", "./large_tool_data.db")
        self.file_storage_path = Path(config.get("file_path", "./large_tool_data_files/"))
        self.compression_enabled = config.get("compression", True)
        self.max_sqlite_size_mb = config.get("max_sqlite_size_mb", 50)
        self.pool_size = config.get("connection_pool_size", 10)

        # Thread safety: Connection pool for concurrent access
        self._connection_pool: queue.Queue = queue.Queue(maxsize=self.pool_size)
        self._pool_lock = threading.Lock()
        self._pool_initialized = False

        # Create directories
        self.file_storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize connection pool
        self._init_connection_pool()
        log.info(f"Large data storage initialized: DB={self.db_path}, Files={self.file_storage_path}, Pool size={self.pool_size}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with optimal settings."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
        conn.execute("PRAGMA cache_size=20000")  # 80MB cache
        conn.execute("PRAGMA temp_store=MEMORY")  # Memory for temp operations
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
        return conn
    
    def _init_connection_pool(self):
        """Initialize connection pool with schema creation."""
        with self._pool_lock:
            if self._pool_initialized:
                return
            
            # Create initial connection to set up schema
            init_conn = self._create_connection()
            
            # Create optimized table structure
            init_conn.execute("""
                CREATE TABLE IF NOT EXISTS large_tool_data (
                    reference_id TEXT PRIMARY KEY,
                    tool_name TEXT NOT NULL,
                    storage_type TEXT NOT NULL,
                    storage_location TEXT,
                    data_blob BLOB,
                    data_hash TEXT,
                    size_bytes INTEGER,
                    size_category TEXT,
                    content_type TEXT,
                    compressed BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes for fast lookup
            init_conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_name ON large_tool_data(tool_name)")
            init_conn.execute("CREATE INDEX IF NOT EXISTS idx_size_category ON large_tool_data(size_category)")
            init_conn.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON large_tool_data(expires_at)")
            
            init_conn.commit()
            
            # Add connections to pool
            self._connection_pool.put(init_conn)
            for _ in range(self.pool_size - 1):
                self._connection_pool.put(self._create_connection())
            
            self._pool_initialized = True
            log.info(f"Connection pool initialized with {self.pool_size} connections")
    
    @contextmanager
    def _get_connection(self):
        """Get a connection from the pool (context manager)."""
        conn = None
        try:
            # Get connection from pool (blocks if all connections are in use)
            conn = self._connection_pool.get(timeout=30.0)
            yield conn
        except queue.Empty:
            log.error("Connection pool exhausted - timeout waiting for connection")
            raise RuntimeError("Database connection pool exhausted")
        finally:
            if conn is not None:
                # Return connection to pool
                self._connection_pool.put(conn)
    
    def close_pool(self):
        """Close all connections in the pool."""
        with self._pool_lock:
            while not self._connection_pool.empty():
                try:
                    conn = self._connection_pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            self._pool_initialized = False
            log.info("Connection pool closed")
    
    def store_large_data(self, reference_id: str, tool_name: str,
                        data: Any, metadata: Optional[Dict] = None) -> StorageInfo:
        """Store large data using optimal storage strategy

        Thread-safe: Uses lock for write operations to prevent race conditions.
        """

        # Serialize data
        if isinstance(data, (dict, list)):
            serialized = json.dumps(data, default=str, ensure_ascii=False)
            content_type = 'json'
        elif isinstance(data, str):
            serialized = data
            content_type = 'text'
        else:
            serialized = str(data)
            content_type = 'string'

        data_bytes = serialized.encode('utf-8')
        size_bytes = len(data_bytes)
        size_mb = size_bytes / (1024 * 1024)

        # Determine optimal storage strategy
        storage_info = self._determine_storage_strategy(size_mb)
        data_hash = hashlib.sha256(data_bytes).hexdigest()
        expires_at = datetime.now() + timedelta(hours=48)  # Default 48h expiry

        # Thread safety: Use connection pool for write operation
        with self._get_connection() as conn:
            if storage_info["type"] == "sqlite":
                # Store in SQLite (with optional compression)
                data_to_store = data_bytes
                if self.compression_enabled and size_mb > 0.1:  # Compress if >100KB
                    data_to_store = gzip.compress(data_bytes)
                    compressed = True
                else:
                    compressed = False

                conn.execute("""
                    INSERT OR REPLACE INTO large_tool_data
                    (reference_id, tool_name, storage_type, data_blob, data_hash,
                     size_bytes, size_category, content_type, compressed, metadata, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reference_id, tool_name, storage_info["type"], data_to_store, data_hash,
                    size_bytes, storage_info["category"].value, content_type, compressed,
                    json.dumps(metadata or {}), expires_at
                ))

                result = StorageInfo(
                    reference_id=reference_id,
                    storage_type=storage_info["type"],
                    size_bytes=size_bytes,
                    size_mb=size_mb,
                    size_category=storage_info["category"],
                    content_type=content_type,
                    compressed=compressed
                )

            else:
                # Store in file system
                file_name = f"{reference_id}.json.gz" if self.compression_enabled else f"{reference_id}.json"
                file_path = self.file_storage_path / file_name

                if self.compression_enabled:
                    with gzip.open(file_path, 'wb') as f:
                        f.write(data_bytes)
                    compressed = True
                else:
                    with open(file_path, 'wb') as f:
                        f.write(data_bytes)
                    compressed = False

                # Store metadata in SQLite
                conn.execute("""
                    INSERT OR REPLACE INTO large_tool_data
                    (reference_id, tool_name, storage_type, storage_location, data_hash,
                     size_bytes, size_category, content_type, compressed, metadata, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reference_id, tool_name, "file_system", str(file_path), data_hash,
                    size_bytes, storage_info["category"].value, content_type, compressed,
                    json.dumps(metadata or {}), expires_at
                ))

                result = StorageInfo(
                    reference_id=reference_id,
                    storage_type="file_system",
                    size_bytes=size_bytes,
                    size_mb=size_mb,
                    size_category=storage_info["category"],
                    content_type=content_type,
                    compressed=compressed,
                    file_path=str(file_path)
                )

            # Commit transaction
            conn.commit()

            # Force immediate persistence to disk (critical for MCP server processes)
            # This ensures data is written even if process terminates immediately
            try:
                conn.execute("PRAGMA wal_checkpoint(FULL)")
                conn.commit()
                log.debug(f"WAL checkpoint completed for {reference_id}")
            except Exception as e:
                log.warning(f"WAL checkpoint failed (non-critical): {e}")

            log.debug(f"Stored {size_mb:.2f}MB data with reference {reference_id} using {storage_info['type']}")
            return result
    
    def _determine_storage_strategy(self, size_mb: float) -> Dict[str, Any]:
        """Determine optimal storage strategy based on data size"""
        if size_mb < 1:
            return {"type": "sqlite", "category": DataSize.SMALL}
        elif size_mb < self.max_sqlite_size_mb:
            return {"type": "sqlite", "category": DataSize.MEDIUM}
        elif size_mb < 500:
            return {"type": "file_system", "category": DataSize.LARGE}
        else:
            return {"type": "file_system", "category": DataSize.HUGE}
    
    def retrieve_large_data(self, reference_id: str) -> Optional[Any]:
        """Retrieve large data from appropriate storage layer"""
        
        # Get metadata from SQLite using connection pool
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT storage_type, storage_location, data_blob, content_type, compressed
                FROM large_tool_data 
                WHERE reference_id = ?
            """, (reference_id,))
            
            row = cursor.fetchone()
            if not row:
                log.warning(f"Reference ID {reference_id} not found")
                return None
            
            storage_type, storage_location, data_blob, content_type, compressed = row
            
            # Update access tracking
            conn.execute("""
                UPDATE large_tool_data 
                SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                WHERE reference_id = ?
            """, (reference_id,))
            conn.commit()
        
        try:
            if storage_type == "sqlite":
                # Data stored in SQLite blob
                data_bytes = data_blob
                if compressed:
                    data_bytes = gzip.decompress(data_bytes)
                
                serialized = data_bytes.decode('utf-8')
            
            else:
                # Data stored in file system
                file_path = Path(storage_location)
                if not file_path.exists():
                    log.error(f"File not found: {file_path}")
                    return None
                
                if compressed:
                    with gzip.open(file_path, 'rb') as f:
                        data_bytes = f.read()
                else:
                    with open(file_path, 'rb') as f:
                        data_bytes = f.read()
                
                serialized = data_bytes.decode('utf-8')
            
            # Deserialize based on content type
            if content_type == 'json':
                return json.loads(serialized)
            else:
                return serialized
                
        except Exception as e:
            log.error(f"Error retrieving data for {reference_id}: {e}")
            return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_references,
                    SUM(size_bytes) as total_size_bytes,
                AVG(size_bytes) as avg_size_bytes,
                storage_type,
                size_category,
                COUNT(*) as count_by_type
            FROM large_tool_data 
            GROUP BY storage_type, size_category
        """)
        
        stats = {
            "total_references": 0,
            "total_size_mb": 0,
            "storage_breakdown": {},
            "file_system_usage": 0
        }
        
        for row in cursor.fetchall():
            total, total_bytes, avg_bytes, storage_type, size_category, count = row
            
            stats["total_references"] += count
            stats["total_size_mb"] += (total_bytes or 0) / (1024 * 1024)
            
            key = f"{storage_type}_{size_category}"
            stats["storage_breakdown"][key] = {
                "count": count,
                "total_mb": (total_bytes or 0) / (1024 * 1024),
                "avg_mb": (avg_bytes or 0) / (1024 * 1024)
            }
        
        # File system usage
        if self.file_storage_path.exists():
            file_sizes = [f.stat().st_size for f in self.file_storage_path.glob("*") if f.is_file()]
            stats["file_system_usage"] = sum(file_sizes) / (1024 * 1024)  # MB
        
        return stats
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired data references"""
        
        with self._get_connection() as conn:
            # Find expired records
            cursor = conn.execute("""
                SELECT reference_id, storage_type, storage_location
                FROM large_tool_data 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            
            expired_records = cursor.fetchall()
            cleaned_records = 0
            cleaned_files = 0
            
            for reference_id, storage_type, storage_location in expired_records:
                try:
                    # Delete file if it exists
                    if storage_type == "file_system" and storage_location:
                        file_path = Path(storage_location)
                        if file_path.exists():
                            file_path.unlink()
                            cleaned_files += 1
                    
                    # Remove from database
                    conn.execute("DELETE FROM large_tool_data WHERE reference_id = ?", (reference_id,))
                    cleaned_records += 1
                    
                except Exception as e:
                    log.error(f"Error cleaning up {reference_id}: {e}")
            
            conn.commit()
        
        return {
            "cleaned_records": cleaned_records,
            "cleaned_files": cleaned_files
        }
    
    def list_references(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List stored data references"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT reference_id, tool_name, size_bytes, size_category,
                       storage_type, content_type, created_at, last_accessed
                FROM large_tool_data 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            references = []
            for row in cursor.fetchall():
                ref_id, tool_name, size_bytes, size_category, storage_type, content_type, created_at, last_accessed = row
                references.append({
                    "reference_id": ref_id,
                    "tool_name": tool_name,
                    "size_bytes": size_bytes,
                    "size_mb": size_bytes / (1024 * 1024),
                    "size_category": size_category,
                    "storage_type": storage_type,
                    "content_type": content_type,
                    "created_at": created_at,
                    "last_accessed": last_accessed
            })
        
        return references
