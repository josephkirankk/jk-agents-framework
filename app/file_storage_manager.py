"""
File Storage Manager for Thread-Based File Context

Manages file uploads with reference IDs tied to thread contexts.
Files are stored in memory and can be retrieved by agents using reference IDs.
"""
import uuid
import base64
import mimetypes
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import logging
from pathlib import Path
import threading

log = logging.getLogger(__name__)


class FileReference:
    """Represents a stored file with metadata."""
    
    def __init__(
        self,
        reference_id: str,
        filename: str,
        content: bytes,
        mime_type: Optional[str],
        thread_id: str,
        size_bytes: int,
        uploaded_at: str,
        compression_metadata: Optional[Dict[str, Any]] = None
    ):
        self.reference_id = reference_id
        self.filename = filename
        self.content = content
        self.mime_type = mime_type or "application/octet-stream"
        self.thread_id = thread_id
        self.size_bytes = size_bytes
        self.uploaded_at = uploaded_at
        self.compression_metadata = compression_metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without content for logging)."""
        result = {
            "reference_id": self.reference_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "thread_id": self.thread_id,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at
        }
        if self.compression_metadata:
            result["compression"] = self.compression_metadata
        return result
    
    def get_base64_content(self) -> str:
        """Get base64-encoded content."""
        return base64.b64encode(self.content).decode('utf-8')
    
    def is_image(self) -> bool:
        """Check if file is an image."""
        return self.mime_type.startswith('image/')
    
    def is_text(self) -> bool:
        """Check if file is text-based."""
        text_types = ['text/', 'application/json', 'application/xml', 'application/csv']
        return any(self.mime_type.startswith(t) for t in text_types)


class FileStorageManager:
    """
    Thread-safe file storage manager with automatic image compression.
    Stores files in memory with reference IDs tied to thread contexts.
    """
    
    def __init__(self, compress_images: bool = True, max_image_dimension: int = 1536):
        self._storage: Dict[str, FileReference] = {}
        self._thread_index: Dict[str, List[str]] = {}  # thread_id -> [reference_ids]
        self._lock = threading.RLock()
        self.compress_images = compress_images
        self.max_image_dimension = max_image_dimension
        log.info(f"FileStorageManager initialized (compression={compress_images}, max_dim={max_image_dimension})")
    
    def _compress_if_image(self, content: bytes, mime_type: str, filename: str) -> Tuple[bytes, Dict[str, Any]]:
        """Compress image if it's an image type and compression is enabled.
        Returns possibly-updated content and compression metadata. If compression
        would increase size or fails, original content is returned and metadata is {}.
        """
        compression_metadata: Dict[str, Any] = {}
        
        if not self.compress_images:
            return content, compression_metadata
        
        if not mime_type or not mime_type.startswith('image/'):
            return content, compression_metadata
        
        try:
            from app.image_compression import compress_image, should_compress_image
            
            if should_compress_image(content, dimension_threshold=self.max_image_dimension):
                log.info(f"Compressing image {filename} ({len(content):,} bytes)")
                compressed_content, out_format, metadata = compress_image(
                    content,
                    max_dimension=self.max_image_dimension
                )
                
                # If metadata is empty, compressor decided to use original
                if not metadata:
                    log.info(f"Compression skipped for {filename} (original smaller). Using original bytes.")
                    return content, {}
                
                # Update MIME type if format changed
                if out_format.upper() == 'JPEG':
                    new_mime = 'image/jpeg'
                elif out_format.upper() == 'PNG':
                    new_mime = 'image/png'
                else:
                    new_mime = mime_type
                
                # Log final stats
                orig_size = metadata.get('original_size_bytes', len(content))
                comp_size = metadata.get('compressed_size_bytes', len(compressed_content))
                ratio = metadata.get('compression_ratio_percent', round((1 - (comp_size / max(1, orig_size))) * 100, 2))
                q_used = metadata.get('quality_used')
                log.info(
                    f"Compressed {filename}: {orig_size:,} -> {comp_size:,} bytes "
                    f"({ratio:.1f}% reduction){' | Q='+str(q_used) if q_used is not None else ''}"
                )
                
                # Store the updated mime back into metadata for visibility
                metadata['compressed_mime_type'] = new_mime
                
                # Return compressed content and full metadata
                return compressed_content, metadata
            else:
                log.debug(f"Image {filename} does not need compression")
                return content, compression_metadata
                
        except Exception as e:
            log.warning(f"Image compression failed for {filename}: {e}, using original")
            return content, compression_metadata
    
    def store_file(
        self,
        filename: str,
        content: bytes,
        mime_type: Optional[str],
        thread_id: str
    ) -> str:
        """
        Store a file and return its reference ID.
        Images are automatically compressed to reduce token usage.
        
        Args:
            filename: Original filename
            content: File content as bytes
            mime_type: MIME type (auto-detected if None)
            thread_id: Thread context ID
            
        Returns:
            reference_id: Unique reference ID for the file
        """
        with self._lock:
            # Generate unique reference ID
            reference_id = f"file_{uuid.uuid4().hex[:12]}"
            
            # Detect MIME type if not provided
            if not mime_type:
                mime_type = mimetypes.guess_type(filename)[0]
            
            # Compress image if applicable
            processed_content, compression_metadata = self._compress_if_image(content, mime_type, filename)
            
            # If compression changed the format, update mime type accordingly
            effective_mime = mime_type
            if compression_metadata and 'compressed_mime_type' in compression_metadata:
                effective_mime = compression_metadata['compressed_mime_type']
            
            # Create file reference
            file_ref = FileReference(
                reference_id=reference_id,
                filename=filename,
                content=processed_content,
                mime_type=effective_mime,
                thread_id=thread_id,
                size_bytes=len(processed_content),
                uploaded_at=datetime.now(timezone.utc).isoformat(),
                compression_metadata=compression_metadata
            )
            
            # Store file
            self._storage[reference_id] = file_ref
            
            # Update thread index
            if thread_id not in self._thread_index:
                self._thread_index[thread_id] = []
            self._thread_index[thread_id].append(reference_id)
            
            log.info(
                f"Stored file: {filename} (reference_id={reference_id}, "
                f"thread_id={thread_id}, size={len(processed_content)} bytes, mime={mime_type})"
            )
            
            return reference_id
    
    def get_file(self, reference_id: str) -> Optional[FileReference]:
        """
        Internal method: Retrieve a file reference by ID.
        
        Args:
            reference_id: File reference ID
            
        Returns:
            FileReference if found, None otherwise
        """
        with self._lock:
            return self._storage.get(reference_id)
    
    def get_file_metadata(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata without retrieving content.
        
        Args:
            reference_id: File reference ID
            
        Returns:
            Dictionary with metadata (no content) or None if not found
        """
        with self._lock:
            file_ref = self._storage.get(reference_id)
            if not file_ref:
                return None
            
            metadata = {
                "reference_id": file_ref.reference_id,
                "filename": file_ref.filename,
                "mime_type": file_ref.mime_type,
                "size_bytes": file_ref.size_bytes,
                "uploaded_at": file_ref.uploaded_at,
                "is_image": file_ref.is_image(),
                "is_text": file_ref.is_text()
            }
            
            if file_ref.compression_metadata:
                metadata["compression"] = file_ref.compression_metadata
            
            return metadata
    
    def get_file_content_raw(self, reference_id: str) -> Optional[bytes]:
        """
        Get file content as raw bytes (for non-image files).
        
        Args:
            reference_id: File reference ID
            
        Returns:
            Raw bytes content or None if not found
        """
        with self._lock:
            file_ref = self._storage.get(reference_id)
            if not file_ref:
                return None
            
            log.info(f"Retrieved raw content for {reference_id} ({file_ref.filename}, {file_ref.size_bytes:,} bytes)")
            return file_ref.content
    
    def get_file_content_base64(self, reference_id: str) -> Optional[str]:
        """
        Get file content as base64 string (for images).
        
        Args:
            reference_id: File reference ID
            
        Returns:
            Base64-encoded string or None if not found
        """
        with self._lock:
            file_ref = self._storage.get(reference_id)
            if not file_ref:
                return None
            
            # Log compression info if available
            compression_info = ""
            if file_ref.compression_metadata:
                comp_meta = file_ref.compression_metadata
                compression_info = f" [Compressed: {comp_meta.get('original_size_bytes', 0):,} -> {file_ref.size_bytes:,} bytes ({comp_meta.get('compression_ratio_percent', 0):.1f}% reduction)]"
            
            log.info(f"Retrieved base64 content for {reference_id} ({file_ref.filename}, {file_ref.size_bytes:,} bytes){compression_info}")
            return file_ref.get_base64_content()
    
    def get_thread_files(self, thread_id: str) -> List[FileReference]:
        """
        Get all files for a thread.
        
        Args:
            thread_id: Thread context ID
            
        Returns:
            List of FileReference objects
        """
        with self._lock:
            reference_ids = self._thread_index.get(thread_id, [])
            return [self._storage[ref_id] for ref_id in reference_ids if ref_id in self._storage]
    
    def list_files(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        List file metadata for a thread (without content).
        
        Args:
            thread_id: Thread context ID
            
        Returns:
            List of file metadata dictionaries
        """
        files = self.get_thread_files(thread_id)
        return [f.to_dict() for f in files]
    
    def delete_file(self, reference_id: str) -> bool:
        """
        Delete a file by reference ID.
        
        Args:
            reference_id: File reference ID
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            file_ref = self._storage.get(reference_id)
            if not file_ref:
                return False
            
            # Remove from storage
            del self._storage[reference_id]
            
            # Remove from thread index
            thread_id = file_ref.thread_id
            if thread_id in self._thread_index:
                self._thread_index[thread_id].remove(reference_id)
                if not self._thread_index[thread_id]:
                    del self._thread_index[thread_id]
            
            log.info(f"Deleted file: reference_id={reference_id}")
            return True
    
    def clear_thread_files(self, thread_id: str) -> int:
        """
        Delete all files for a thread.
        
        Args:
            thread_id: Thread context ID
            
        Returns:
            Number of files deleted
        """
        with self._lock:
            reference_ids = self._thread_index.get(thread_id, []).copy()
            count = 0
            for ref_id in reference_ids:
                if self.delete_file(ref_id):
                    count += 1
            
            log.info(f"Cleared {count} files for thread_id={thread_id}")
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with self._lock:
            total_files = len(self._storage)
            total_size = sum(f.size_bytes for f in self._storage.values())
            total_threads = len(self._thread_index)
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_threads": total_threads,
                "threads": {
                    thread_id: len(ref_ids)
                    for thread_id, ref_ids in self._thread_index.items()
                }
            }


# Global file storage manager instance
_file_storage_manager: Optional[FileStorageManager] = None
_file_storage_lock = threading.Lock()  # CRITICAL FIX: Thread-safe singleton


def get_file_storage_manager() -> FileStorageManager:
    """Get or create the global file storage manager instance - THREAD SAFE."""
    global _file_storage_manager
    # First check without lock (optimization)
    if _file_storage_manager is not None:
        return _file_storage_manager
    
    # Acquire lock for initialization
    with _file_storage_lock:
        # Double-check after acquiring lock (prevents race condition)
        if _file_storage_manager is None:
            _file_storage_manager = FileStorageManager()
    
    return _file_storage_manager
