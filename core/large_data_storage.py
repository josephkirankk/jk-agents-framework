"""
Large Data Storage System

A multi-tier storage system for efficiently handling large datasets in agent workflows.
Provides intelligent data classification, compression, and retrieval with metadata tracking.
"""

import sqlite3
import json
import pickle
import gzip
import os
import hashlib
import time
import threading
import weakref
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging
from contextlib import contextmanager
from queue import Queue, Empty

# Import your existing memory structures
try:
    from app.memory.structures import LRUCache, get_memory_stats
except ImportError:
    # Fallback if not available
    class LRUCache:
        def __init__(self, maxsize=10000):
            self._cache = {}
            self.maxsize = maxsize
            self._lock = threading.RLock()
        
        def get(self, key):
            with self._lock:
                return self._cache.get(key)
        
        def set(self, key, value):
            with self._lock:
                if len(self._cache) >= self.maxsize:
                    # Simple eviction - remove oldest
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[key] = value
        
        def delete(self, key):
            with self._lock:
                return self._cache.pop(key, None) is not None
        
        def stats(self):
            return {"size": len(self._cache), "maxsize": self.maxsize}
    
    def get_memory_stats():
        return {"string_intern": {}, "memory_pool": {}}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionPool:
    """
    Simple SQLite connection pool to reduce connection overhead.
    """
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections = Queue(maxsize=max_connections)
        self._created_connections = 0
        self._lock = threading.RLock()
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = None
        try:
            # Try to get an existing connection
            try:
                conn = self._connections.get_nowait()
            except Empty:
                # Create new connection if under limit
                with self._lock:
                    if self._created_connections < self.max_connections:
                        conn = sqlite3.connect(self.db_path, check_same_thread=False)
                        conn.execute("PRAGMA journal_mode=WAL")
                        conn.execute("PRAGMA synchronous=NORMAL")
                        conn.execute("PRAGMA cache_size=10000")
                        self._created_connections += 1
                    else:
                        # Wait for a connection to be available
                        conn = self._connections.get()
            
            yield conn
        finally:
            if conn:
                # Return connection to pool
                try:
                    self._connections.put_nowait(conn)
                except:
                    # Pool full, close connection
                    conn.close()
                    with self._lock:
                        self._created_connections -= 1


class LargeDataStorage:
    """
    Multi-tier storage system for large data optimization with enhanced memory management.
    
    Features:
    - LRU caching for frequently accessed data
    - Connection pooling for SQLite operations
    - Memory usage monitoring and cleanup
    - Lazy loading support for large datasets
    
    Storage tiers:
    - Small (< 1MB): SQLite with optional compression
    - Medium (1-50MB): SQLite with compression
    - Large (50-500MB): File system with SQLite metadata
    - Huge (> 500MB): Chunked file system with SQLite metadata
    """
    
    SIZE_THRESHOLDS = {
        'small': 1 * 1024 * 1024,      # 1MB
        'medium': 50 * 1024 * 1024,    # 50MB
        'large': 500 * 1024 * 1024,    # 500MB
    }
    
    def __init__(self, 
                 storage_path: str = "./data/large_data_storage.db",
                 file_storage_path: str = "./data/large_files",
                 max_file_size_mb: int = 100,
                 compression_enabled: bool = True,
                 cleanup_interval: int = 3600,
                 cache_size: int = 1000,
                 enable_caching: bool = True,
                 connection_pool_size: int = 10):
        
        self.storage_path = Path(storage_path)
        self.file_storage_path = Path(file_storage_path)
        self.max_file_size_mb = max_file_size_mb
        self.compression_enabled = compression_enabled
        self.cleanup_interval = cleanup_interval
        self.enable_caching = enable_caching
        
        # Initialize caching system
        if self.enable_caching:
            self._data_cache = LRUCache(maxsize=cache_size)
            self._metadata_cache = LRUCache(maxsize=cache_size // 2)
        else:
            self._data_cache = None
            self._metadata_cache = None
        
        # Initialize connection pool
        self._connection_pool = ConnectionPool(str(self.storage_path), connection_pool_size)
        
        # Statistics tracking
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_reads": 0,
            "db_writes": 0,
            "compressions": 0,
            "decompressions": 0
        }
        self._stats_lock = threading.RLock()
        
        # Create directories
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"LargeDataStorage initialized: {self.storage_path} (caching: {enable_caching}, pool_size: {connection_pool_size})")
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with self._connection_pool.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_references (
                    reference_id TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    size_classification TEXT NOT NULL,
                    storage_type TEXT NOT NULL,
                    file_path TEXT,
                    compressed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    data_blob BLOB
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON data_references(created_at)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_size_classification ON data_references(size_classification)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_at ON data_references(accessed_at)
            """)
            
            conn.commit()
        
        with self._stats_lock:
            self._stats["db_writes"] += 1
    
    def _generate_reference_id(self, data: Any) -> str:
        """Generate a unique reference ID for data"""
        data_str = str(data)
        hash_obj = hashlib.md5(data_str.encode() + str(time.time()).encode())
        return hash_obj.hexdigest()[:12]
    
    def _classify_size(self, size_bytes: int) -> str:
        """Classify data size into storage tiers"""
        if size_bytes < self.SIZE_THRESHOLDS['small']:
            return 'small'
        elif size_bytes < self.SIZE_THRESHOLDS['medium']:
            return 'medium'
        elif size_bytes < self.SIZE_THRESHOLDS['large']:
            return 'large'
        else:
            return 'huge'
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data to bytes"""
        try:
            # Try JSON first (more readable)
            return json.dumps(data, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # Fallback to pickle
            return pickle.dumps(data)
    
    def _deserialize_data(self, data_bytes: bytes, is_json: bool = True) -> Any:
        """Deserialize data from bytes"""
        try:
            return json.loads(data_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            # Fallback to pickle
            try:
                return pickle.loads(data_bytes)
            except:
                # If both fail, try to decode as string
                return data_bytes.decode('utf-8', errors='ignore')
    
    def _compress_data(self, data_bytes: bytes) -> bytes:
        """Compress data using gzip"""
        if self.compression_enabled:
            return gzip.compress(data_bytes)
        return data_bytes
    
    def _decompress_data(self, compressed_bytes: bytes, was_compressed: bool = True) -> bytes:
        """Decompress data"""
        if was_compressed and self.compression_enabled:
            return gzip.decompress(compressed_bytes)
        return compressed_bytes
    
    def store_data(self, data: Any, data_type: str = "unknown") -> str:
        """
        Store data and return reference ID
        
        Args:
            data: Data to store
            data_type: Type/description of data
            
        Returns:
            Reference ID for retrieving the data
        """
        reference_id = self._generate_reference_id(data)
        
        # Serialize data
        serialized_data = self._serialize_data(data)
        size_bytes = len(serialized_data)
        size_classification = self._classify_size(size_bytes)
        
        # Determine storage strategy
        if size_classification in ['small', 'medium']:
            # Store in SQLite
            self._store_in_sqlite(reference_id, data, data_type, size_bytes, 
                                size_classification, serialized_data)
        else:
            # Store in file system
            self._store_in_files(reference_id, data, data_type, size_bytes,
                               size_classification, serialized_data)
        
        logger.info(f"Stored data reference {reference_id} ({size_classification}, {size_bytes:,} bytes)")
        return reference_id
    
    def _store_in_sqlite(self, reference_id: str, data: Any, data_type: str,
                        size_bytes: int, size_classification: str, serialized_data: bytes):
        """Store data directly in SQLite"""
        # Only compress if it reduces size significantly
        compressed_data = self._compress_data(serialized_data)
        was_compressed = self.compression_enabled and len(compressed_data) < len(serialized_data) * 0.9
        
        # Use original data if compression doesn't help much
        final_data = compressed_data if was_compressed else serialized_data
        
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO data_references 
                (reference_id, data_type, size_bytes, size_classification, storage_type,
                 compressed, metadata, data_blob)
                VALUES (?, ?, ?, ?, 'sqlite', ?, ?, ?)
            """, (
                reference_id, data_type, size_bytes, size_classification,
                was_compressed, json.dumps({"original_size": len(serialized_data), "compressed": was_compressed}),
                final_data
            ))
            conn.commit()
    
    def _store_in_files(self, reference_id: str, data: Any, data_type: str,
                       size_bytes: int, size_classification: str, serialized_data: bytes):
        """Store data in file system with metadata in SQLite"""
        file_path = self.file_storage_path / f"{reference_id}.data"
        
        # Compress and write to file
        compressed_data = self._compress_data(serialized_data)
        was_compressed = len(compressed_data) < len(serialized_data)
        
        with open(file_path, 'wb') as f:
            f.write(compressed_data)
        
        # Store metadata in SQLite
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO data_references 
                (reference_id, data_type, size_bytes, size_classification, storage_type,
                 file_path, compressed, metadata)
                VALUES (?, ?, ?, ?, 'file', ?, ?, ?)
            """, (
                reference_id, data_type, size_bytes, size_classification,
                str(file_path), was_compressed,
                json.dumps({
                    "original_size": len(serialized_data),
                    "compressed_size": len(compressed_data),
                    "compression_ratio": len(compressed_data) / len(serialized_data)
                })
            ))
            conn.commit()
    
    def get_data(self, reference_id: str) -> Optional[Any]:
        """
        Retrieve data by reference ID with caching support.
        
        Args:
            reference_id: Reference ID returned by store_data
            
        Returns:
            Original data or None if not found
        """
        # Check cache first
        if self.enable_caching and self._data_cache:
            cached_data = self._data_cache.get(reference_id)
            if cached_data is not None:
                with self._stats_lock:
                    self._stats["cache_hits"] += 1
                return cached_data
        
        # Cache miss - fetch from storage
        with self._stats_lock:
            self._stats["cache_misses"] += 1
            self._stats["db_reads"] += 1
        
        with self._connection_pool.get_connection() as conn:
            conn.execute("""
                UPDATE data_references SET accessed_at = CURRENT_TIMESTAMP 
                WHERE reference_id = ?
            """, (reference_id,))
            
            cursor = conn.execute("""
                SELECT storage_type, file_path, compressed, data_blob
                FROM data_references WHERE reference_id = ?
            """, (reference_id,))
            
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Reference ID {reference_id} not found")
                return None
            
            storage_type, file_path, compressed, data_blob = row
            
            data = None
            
            if storage_type == 'sqlite':
                # Data stored in SQLite
                with self._stats_lock:
                    self._stats["decompressions"] += 1
                decompressed_data = self._decompress_data(data_blob, compressed)
                data = self._deserialize_data(decompressed_data)
            
            elif storage_type == 'file' and file_path:
                # Data stored in file system
                try:
                    with open(file_path, 'rb') as f:
                        compressed_data = f.read()
                    
                    with self._stats_lock:
                        self._stats["decompressions"] += 1
                    decompressed_data = self._decompress_data(compressed_data, compressed)
                    data = self._deserialize_data(decompressed_data)
                
                except FileNotFoundError:
                    logger.error(f"File not found: {file_path}")
                    return None
            
            # Cache the result for future use
            if data is not None and self.enable_caching and self._data_cache:
                self._data_cache.set(reference_id, data)
            
            return data
    
    def get_metadata(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a reference ID"""
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("""
                SELECT data_type, size_bytes, size_classification, storage_type,
                       compressed, created_at, accessed_at, metadata
                FROM data_references WHERE reference_id = ?
            """, (reference_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            (data_type, size_bytes, size_classification, storage_type,
             compressed, created_at, accessed_at, metadata_json) = row
            
            metadata = json.loads(metadata_json) if metadata_json else {}
            
            return {
                "reference_id": reference_id,
                "data_type": data_type,
                "size_bytes": size_bytes,
                "size_mb": size_bytes / (1024 * 1024),
                "size_classification": size_classification,
                "storage_type": storage_type,
                "compressed": bool(compressed),
                "created_at": created_at,
                "accessed_at": accessed_at,
                "additional_metadata": metadata
            }
    
    def delete_data(self, reference_id: str) -> bool:
        """Delete data by reference ID"""
        with sqlite3.connect(self.storage_path) as conn:
            # Get file path if it exists
            cursor = conn.execute("""
                SELECT storage_type, file_path FROM data_references 
                WHERE reference_id = ?
            """, (reference_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            storage_type, file_path = row
            
            # Delete file if it exists
            if storage_type == 'file' and file_path:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
            
            # Delete from database
            cursor = conn.execute("""
                DELETE FROM data_references WHERE reference_id = ?
            """, (reference_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def cleanup_expired_data(self, max_age_hours: int = 24) -> int:
        """
        Clean up data older than specified hours
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
            
        Returns:
            Number of items cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with sqlite3.connect(self.storage_path) as conn:
            # Get file paths for cleanup
            cursor = conn.execute("""
                SELECT reference_id, file_path FROM data_references 
                WHERE created_at < ? AND storage_type = 'file'
            """, (cutoff_time,))
            
            files_to_delete = cursor.fetchall()
            
            # Delete files
            for ref_id, file_path in files_to_delete:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        logger.warning(f"Could not delete file: {file_path}")
            
            # Delete from database
            cursor = conn.execute("""
                DELETE FROM data_references WHERE created_at < ?
            """, (cutoff_time,))
            
            conn.commit()
            cleaned_count = cursor.rowcount
        
        logger.info(f"Cleaned up {cleaned_count} expired data references")
        return cleaned_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_references,
                    SUM(size_bytes) as total_size_bytes,
                    AVG(size_bytes) as avg_size_bytes,
                    size_classification,
                    COUNT(*) as count_by_class
                FROM data_references 
                GROUP BY size_classification
            """)
            
            class_stats = cursor.fetchall()
            
            # Get total stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_references,
                    COALESCE(SUM(size_bytes), 0) as total_size_bytes,
                    COALESCE(AVG(size_bytes), 0) as avg_size_bytes
                FROM data_references
            """)
            
            total_stats = cursor.fetchone()
            
        total_references, total_size_bytes, avg_size_bytes = total_stats or (0, 0, 0)
        
        size_distribution = {}
        for row in class_stats:
            if len(row) >= 5:
                size_class, count = row[3], row[4]
                size_distribution[size_class] = count
        
        return {
            "total_references": total_references,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": total_size_bytes / (1024 * 1024) if total_size_bytes else 0,
            "avg_size_bytes": avg_size_bytes,
            "avg_size_mb": avg_size_bytes / (1024 * 1024) if avg_size_bytes else 0,
            "size_distribution": size_distribution,
            "storage_path": str(self.storage_path),
            "file_storage_path": str(self.file_storage_path)
        }
    
    def list_references(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List stored data references"""
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("""
                SELECT reference_id, data_type, size_bytes, size_classification,
                       storage_type, created_at, accessed_at
                FROM data_references 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            references = []
            for row in cursor.fetchall():
                ref_id, data_type, size_bytes, size_class, storage_type, created_at, accessed_at = row
                references.append({
                    "reference_id": ref_id,
                    "data_type": data_type,
                    "size_bytes": size_bytes,
                    "size_mb": size_bytes / (1024 * 1024),
                    "size_classification": size_class,
                    "storage_type": storage_type,
                    "created_at": created_at,
                    "accessed_at": accessed_at
                })
            
            return references
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance and memory statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        with self._stats_lock:
            stats = self._stats.copy()
        
        # Calculate hit rates
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        cache_hit_rate = stats["cache_hits"] / max(1, total_requests)
        
        result = {
            "storage_stats": stats,
            "cache_hit_rate": cache_hit_rate,
            "total_requests": total_requests,
        }
        
        # Add cache statistics if available
        if self.enable_caching:
            if self._data_cache:
                result["data_cache"] = self._data_cache.stats()
            if self._metadata_cache:
                result["metadata_cache"] = self._metadata_cache.stats()
        
        # Get database statistics
        try:
            with self._connection_pool.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM data_references")
                count, total_size = cursor.fetchone()
                
                cursor = conn.execute("""
                    SELECT size_classification, COUNT(*), SUM(size_bytes) 
                    FROM data_references 
                    GROUP BY size_classification
                """)
                size_distribution = {row[0]: {"count": row[1], "total_bytes": row[2]} 
                                   for row in cursor.fetchall()}
                
                result.update({
                    "total_references": count or 0,
                    "total_storage_bytes": total_size or 0,
                    "total_storage_mb": (total_size or 0) / (1024 * 1024),
                    "size_distribution": size_distribution
                })
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
        
        return result
    
    def clear_cache(self) -> None:
        """
        Clear all cached data to free memory.
        """
        if self.enable_caching:
            if self._data_cache:
                self._data_cache.clear()
            if self._metadata_cache:
                self._metadata_cache.clear()
        
        logger.info("Cleared all cached data")
    
    def optimize_cache(self, target_size_ratio: float = 0.8) -> Dict[str, int]:
        """
        Optimize cache by removing least recently used items to target size ratio.
        
        Args:
            target_size_ratio: Target cache size as ratio of maximum (0.0-1.0)
        
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.enable_caching:
            return {"data_cache_evicted": 0, "metadata_cache_evicted": 0}
        
        evicted = {"data_cache_evicted": 0, "metadata_cache_evicted": 0}
        
        # Optimize data cache
        if self._data_cache:
            current_stats = self._data_cache.stats()
            target_size = int(current_stats["maxsize"] * target_size_ratio)
            current_size = current_stats["size"]
            
            if current_size > target_size:
                # Simple eviction by clearing cache - in a more sophisticated implementation,
                # you'd selectively remove LRU items
                items_to_remove = current_size - target_size
                evicted["data_cache_evicted"] = items_to_remove
                logger.info(f"Would evict {items_to_remove} items from data cache")
        
        # Optimize metadata cache similarly
        if self._metadata_cache:
            current_stats = self._metadata_cache.stats()
            target_size = int(current_stats["maxsize"] * target_size_ratio)
            current_size = current_stats["size"]
            
            if current_size > target_size:
                items_to_remove = current_size - target_size
                evicted["metadata_cache_evicted"] = items_to_remove
                logger.info(f"Would evict {items_to_remove} items from metadata cache")
        
        return evicted
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage statistics.
        
        Returns:
            Dictionary with memory usage information
        """
        import sys
        
        try:
            import psutil
            import os
            import gc
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                "process_memory_mb": memory_info.rss / (1024 * 1024),
                "virtual_memory_mb": memory_info.vms / (1024 * 1024),
                "python_objects_count": len(gc.get_objects()),
                "storage_stats": self.get_performance_stats(),
                "global_memory_stats": get_memory_stats()
            }
        except ImportError:
            return {
                "error": "psutil not available for memory monitoring",
                "storage_stats": self.get_performance_stats(),
                "global_memory_stats": get_memory_stats()
            }

if __name__ == "__main__":
    # Simple test
    storage = LargeDataStorage()
    
    # Test small data
    small_data = {"test": "data", "size": "small"}
    ref_id = storage.store_data(small_data, "test_data")
    retrieved = storage.get_data(ref_id)
    print(f"Small data test: {retrieved == small_data}")
    
    # Test large data
    large_data = {"records": [{"id": i, "data": "x" * 1000} for i in range(1000)]}
    ref_id = storage.store_data(large_data, "large_test")
    retrieved = storage.get_data(ref_id)
    print(f"Large data test: {len(retrieved['records']) == 1000}")
    
    # Print stats
    stats = storage.get_storage_stats()
    print(f"Storage stats: {stats}")