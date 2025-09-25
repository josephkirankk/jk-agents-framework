"""
Lazy Data Loader for Large Datasets

Provides chunked/streaming data access to minimize peak memory usage when processing
very large datasets in the JK-Agents Framework.
"""

import json
import pickle
import gzip
import logging
import weakref
from typing import Any, Dict, List, Optional, Iterator, Union, Callable, Tuple
from dataclasses import dataclass
from pathlib import Path
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ChunkInfo:
    """Information about a data chunk."""
    chunk_id: str
    start_index: int
    end_index: int
    size_bytes: int
    compressed: bool
    file_path: Optional[str] = None


class DataChunk:
    """
    A lazy-loaded chunk of data that loads content only when accessed.
    """
    
    def __init__(self, chunk_info: ChunkInfo, loader_func: Callable[[ChunkInfo], Any]):
        self.info = chunk_info
        self._loader_func = loader_func
        self._data = None
        self._loaded = False
        self._lock = threading.RLock()
    
    @property
    def data(self) -> Any:
        """Get the chunk data, loading it if necessary."""
        if not self._loaded:
            with self._lock:
                if not self._loaded:  # Double-check pattern
                    self._data = self._loader_func(self.info)
                    self._loaded = True
        return self._data
    
    @property
    def is_loaded(self) -> bool:
        """Check if chunk data is currently loaded."""
        return self._loaded
    
    def unload(self):
        """Unload chunk data to free memory."""
        with self._lock:
            self._data = None
            self._loaded = False
    
    def __len__(self) -> int:
        """Get the length of the chunk."""
        return self.info.end_index - self.info.start_index
    
    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "unloaded"
        return f"DataChunk({self.info.chunk_id}, {len(self)} items, {status})"


class ChunkedDataset:
    """
    A dataset that loads data in chunks to minimize memory usage.
    """
    
    def __init__(self, chunks: List[DataChunk], total_size: int, metadata: Dict[str, Any] = None):
        self.chunks = chunks
        self.total_size = total_size
        self.metadata = metadata or {}
        self._current_chunk_cache: Optional[DataChunk] = None
        self._cache_lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "chunks_loaded": 0,
            "total_loads": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
    
    def __len__(self) -> int:
        """Get total number of items across all chunks."""
        return self.total_size
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over all items in the dataset."""
        for chunk in self.chunks:
            chunk_data = chunk.data
            if isinstance(chunk_data, list):
                yield from chunk_data
            else:
                yield chunk_data
            
            # Optionally unload chunk after iteration to save memory
            # chunk.unload()
    
    def __getitem__(self, index: Union[int, slice]) -> Any:
        """Get item(s) by index."""
        if isinstance(index, slice):
            return self._get_slice(index)
        
        if not (0 <= index < self.total_size):
            raise IndexError(f"Index {index} out of range for dataset of size {self.total_size}")
        
        # Find which chunk contains this index
        chunk = self._find_chunk_for_index(index)
        if not chunk:
            raise IndexError(f"Could not find chunk for index {index}")
        
        # Get the local index within the chunk
        local_index = index - chunk.info.start_index
        chunk_data = chunk.data
        
        if isinstance(chunk_data, list):
            return chunk_data[local_index]
        else:
            # Single item chunk
            return chunk_data
    
    def _get_slice(self, slice_obj: slice) -> List[Any]:
        """Get a slice of the dataset."""
        start, stop, step = slice_obj.indices(self.total_size)
        result = []
        
        for i in range(start, stop, step):
            result.append(self[i])
        
        return result
    
    def _find_chunk_for_index(self, index: int) -> Optional[DataChunk]:
        """Find the chunk that contains the given index."""
        for chunk in self.chunks:
            if chunk.info.start_index <= index < chunk.info.end_index:
                return chunk
        return None
    
    def get_chunk(self, chunk_index: int) -> DataChunk:
        """Get a specific chunk by its index."""
        if not (0 <= chunk_index < len(self.chunks)):
            raise IndexError(f"Chunk index {chunk_index} out of range")
        return self.chunks[chunk_index]
    
    def get_loaded_chunks(self) -> List[DataChunk]:
        """Get list of currently loaded chunks."""
        return [chunk for chunk in self.chunks if chunk.is_loaded]
    
    def unload_all_chunks(self):
        """Unload all chunks to free memory."""
        for chunk in self.chunks:
            chunk.unload()
        self.stats["chunks_loaded"] = 0
    
    def get_memory_usage_estimate(self) -> Dict[str, Any]:
        """Estimate current memory usage."""
        loaded_chunks = self.get_loaded_chunks()
        total_bytes = sum(chunk.info.size_bytes for chunk in loaded_chunks)
        
        return {
            "loaded_chunks": len(loaded_chunks),
            "total_chunks": len(self.chunks),
            "estimated_memory_mb": total_bytes / (1024 * 1024),
            "utilization_ratio": len(loaded_chunks) / len(self.chunks)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        return {
            **self.stats,
            "total_chunks": len(self.chunks),
            "loaded_chunks": len(self.get_loaded_chunks()),
            "total_size": self.total_size,
            "metadata": self.metadata
        }


class LazyDataLoader:
    """
    Creates chunked datasets for lazy loading of large data structures.
    """
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 max_memory_mb: float = 100.0,
                 storage_path: str = "./data/lazy_chunks"):
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LazyDataLoader initialized with chunk_size={chunk_size}, "
                   f"max_memory={max_memory_mb}MB")
    
    def create_chunked_dataset(self, 
                             data: Any, 
                             reference_id: str,
                             data_type: str = "unknown") -> ChunkedDataset:
        """
        Create a chunked dataset from large data.
        
        Args:
            data: Large data structure to chunk
            reference_id: Unique identifier for this dataset
            data_type: Type description of the data
        
        Returns:
            ChunkedDataset for lazy loading
        """
        if isinstance(data, list):
            return self._chunk_list_data(data, reference_id, data_type)
        elif isinstance(data, dict):
            return self._chunk_dict_data(data, reference_id, data_type)
        else:
            # Single item - wrap in a single chunk
            return self._create_single_chunk_dataset(data, reference_id, data_type)
    
    def _chunk_list_data(self, data: List[Any], reference_id: str, data_type: str) -> ChunkedDataset:
        """Chunk list data into smaller pieces."""
        total_size = len(data)
        chunks = []
        
        for i in range(0, total_size, self.chunk_size):
            chunk_start = i
            chunk_end = min(i + self.chunk_size, total_size)
            chunk_data = data[chunk_start:chunk_end]
            
            # Create chunk info
            chunk_id = f"{reference_id}_chunk_{i//self.chunk_size}"
            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                start_index=chunk_start,
                end_index=chunk_end,
                size_bytes=self._estimate_size(chunk_data),
                compressed=False
            )
            
            # Store chunk data
            chunk_file_path = self._store_chunk_data(chunk_data, chunk_id)
            chunk_info.file_path = str(chunk_file_path)
            
            # Create chunk with loader function
            chunk = DataChunk(chunk_info, self._load_chunk_from_file)
            chunks.append(chunk)
        
        metadata = {
            "original_type": "list",
            "data_type": data_type,
            "chunk_count": len(chunks),
            "created_at": str(Path().cwd())
        }
        
        return ChunkedDataset(chunks, total_size, metadata)
    
    def _chunk_dict_data(self, data: Dict[str, Any], reference_id: str, data_type: str) -> ChunkedDataset:
        """Chunk dictionary data by keys."""
        keys = list(data.keys())
        total_size = len(keys)
        chunks = []
        
        for i in range(0, total_size, self.chunk_size):
            chunk_keys = keys[i:i + self.chunk_size]
            chunk_data = {k: data[k] for k in chunk_keys}
            
            # Create chunk info
            chunk_id = f"{reference_id}_dict_chunk_{i//self.chunk_size}"
            chunk_info = ChunkInfo(
                chunk_id=chunk_id,
                start_index=i,
                end_index=min(i + self.chunk_size, total_size),
                size_bytes=self._estimate_size(chunk_data),
                compressed=False
            )
            
            # Store chunk data
            chunk_file_path = self._store_chunk_data(chunk_data, chunk_id)
            chunk_info.file_path = str(chunk_file_path)
            
            # Create chunk with loader function
            chunk = DataChunk(chunk_info, self._load_chunk_from_file)
            chunks.append(chunk)
        
        metadata = {
            "original_type": "dict",
            "data_type": data_type,
            "chunk_count": len(chunks),
            "keys": keys  # Store original key order
        }
        
        return ChunkedDataset(chunks, total_size, metadata)
    
    def _create_single_chunk_dataset(self, data: Any, reference_id: str, data_type: str) -> ChunkedDataset:
        """Create a single chunk dataset for non-list/dict data."""
        chunk_id = f"{reference_id}_single"
        chunk_info = ChunkInfo(
            chunk_id=chunk_id,
            start_index=0,
            end_index=1,
            size_bytes=self._estimate_size(data),
            compressed=False
        )
        
        # Store chunk data
        chunk_file_path = self._store_chunk_data(data, chunk_id)
        chunk_info.file_path = str(chunk_file_path)
        
        # Create chunk with loader function
        chunk = DataChunk(chunk_info, self._load_chunk_from_file)
        
        metadata = {
            "original_type": type(data).__name__,
            "data_type": data_type,
            "chunk_count": 1
        }
        
        return ChunkedDataset([chunk], 1, metadata)
    
    def _store_chunk_data(self, chunk_data: Any, chunk_id: str) -> Path:
        """Store chunk data to file."""
        chunk_file = self.storage_path / f"{chunk_id}.chunk"
        
        try:
            # Try JSON serialization first
            serialized = json.dumps(chunk_data, default=str).encode('utf-8')
        except (TypeError, ValueError):
            # Fall back to pickle
            serialized = pickle.dumps(chunk_data)
        
        # Compress if beneficial
        compressed = gzip.compress(serialized)
        if len(compressed) < len(serialized) * 0.9:
            final_data = compressed
            use_compression = True
        else:
            final_data = serialized
            use_compression = False
        
        # Write to file
        with open(chunk_file, 'wb') as f:
            # Write compression flag first
            f.write(b'1' if use_compression else b'0')
            f.write(final_data)
        
        return chunk_file
    
    def _load_chunk_from_file(self, chunk_info: ChunkInfo) -> Any:
        """Load chunk data from file."""
        if not chunk_info.file_path:
            raise ValueError(f"No file path for chunk {chunk_info.chunk_id}")
        
        chunk_file = Path(chunk_info.file_path)
        if not chunk_file.exists():
            raise FileNotFoundError(f"Chunk file not found: {chunk_file}")
        
        with open(chunk_file, 'rb') as f:
            # Read compression flag
            compression_flag = f.read(1)
            use_compression = compression_flag == b'1'
            
            # Read data
            data_bytes = f.read()
        
        # Decompress if needed
        if use_compression:
            data_bytes = gzip.decompress(data_bytes)
        
        # Deserialize
        try:
            # Try JSON first
            return json.loads(data_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle
            return pickle.loads(data_bytes)
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate size of data in bytes."""
        try:
            # Quick estimate using JSON serialization
            json_str = json.dumps(data, default=str)
            return len(json_str.encode('utf-8'))
        except:
            # Fall back to pickle size estimation
            try:
                return len(pickle.dumps(data))
            except:
                # Very rough estimate
                return len(str(data)) * 2
    
    def cleanup_chunks(self, reference_id: str) -> int:
        """Clean up chunk files for a specific reference ID."""
        pattern = f"{reference_id}_*"
        deleted_count = 0
        
        for chunk_file in self.storage_path.glob(f"{pattern}.chunk"):
            try:
                chunk_file.unlink()
                deleted_count += 1
            except OSError as e:
                logger.warning(f"Could not delete chunk file {chunk_file}: {e}")
        
        return deleted_count
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about chunk storage."""
        chunk_files = list(self.storage_path.glob("*.chunk"))
        total_size = sum(f.stat().st_size for f in chunk_files)
        
        return {
            "chunk_files_count": len(chunk_files),
            "total_storage_bytes": total_size,
            "total_storage_mb": total_size / (1024 * 1024),
            "storage_path": str(self.storage_path)
        }


class StreamingDataProcessor:
    """
    Process chunked datasets in a streaming fashion to minimize memory usage.
    """
    
    def __init__(self, max_chunks_in_memory: int = 3):
        self.max_chunks_in_memory = max_chunks_in_memory
        self.processing_stats = {
            "items_processed": 0,
            "chunks_processed": 0,
            "memory_cleanups": 0
        }
    
    def process_dataset(self, 
                       dataset: ChunkedDataset, 
                       processor_func: Callable[[Any], Any],
                       batch_size: int = 100) -> Iterator[Any]:
        """
        Process a chunked dataset in streaming fashion.
        
        Args:
            dataset: ChunkedDataset to process
            processor_func: Function to apply to each item
            batch_size: Number of items to process before yielding
        
        Yields:
            Processed items
        """
        batch = []
        loaded_chunks = []
        
        for chunk_idx, chunk in enumerate(dataset.chunks):
            # Load chunk data
            chunk_data = chunk.data
            loaded_chunks.append(chunk)
            
            # Process items in this chunk
            items = chunk_data if isinstance(chunk_data, list) else [chunk_data]
            
            for item in items:
                processed_item = processor_func(item)
                batch.append(processed_item)
                self.processing_stats["items_processed"] += 1
                
                # Yield batch when full
                if len(batch) >= batch_size:
                    yield from batch
                    batch = []
            
            self.processing_stats["chunks_processed"] += 1
            
            # Memory management: unload old chunks
            if len(loaded_chunks) > self.max_chunks_in_memory:
                old_chunk = loaded_chunks.pop(0)
                old_chunk.unload()
                self.processing_stats["memory_cleanups"] += 1
        
        # Yield remaining items
        if batch:
            yield from batch
        
        # Clean up remaining loaded chunks
        for chunk in loaded_chunks:
            chunk.unload()
    
    def aggregate_dataset(self, 
                         dataset: ChunkedDataset,
                         aggregator_func: Callable[[Any, Any], Any],
                         initial_value: Any = None) -> Any:
        """
        Aggregate a chunked dataset in streaming fashion.
        
        Args:
            dataset: ChunkedDataset to aggregate
            aggregator_func: Function to combine items (accumulator, item) -> new_accumulator
            initial_value: Initial value for aggregation
        
        Returns:
            Aggregated result
        """
        accumulator = initial_value
        
        for chunk in dataset.chunks:
            chunk_data = chunk.data
            items = chunk_data if isinstance(chunk_data, list) else [chunk_data]
            
            for item in items:
                accumulator = aggregator_func(accumulator, item)
                self.processing_stats["items_processed"] += 1
            
            # Unload chunk to save memory
            chunk.unload()
            self.processing_stats["chunks_processed"] += 1
        
        return accumulator
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.processing_stats.copy()


# Example usage functions
def create_lazy_dataset_from_large_data(data: Any, 
                                       reference_id: str,
                                       chunk_size: int = 1000) -> ChunkedDataset:
    """
    Convenience function to create a chunked dataset from large data.
    """
    loader = LazyDataLoader(chunk_size=chunk_size)
    return loader.create_chunked_dataset(data, reference_id)


def process_large_dataset_streaming(dataset: ChunkedDataset,
                                   processor_func: Callable[[Any], Any],
                                   batch_size: int = 100) -> List[Any]:
    """
    Convenience function to process a large dataset in streaming fashion.
    """
    processor = StreamingDataProcessor()
    results = list(processor.process_dataset(dataset, processor_func, batch_size))
    return results