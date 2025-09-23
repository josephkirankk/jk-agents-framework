"""
High-Performance Memory Backend System for JK-Agents Framework

This package provides optimized memory backends for storing and retrieving
conversation checkpoints and context with maximum performance and minimal
memory usage.

Key Features:
- Zero-copy data operations
- Connection pooling and caching
- User session isolation
- Adaptive resource management
- Performance monitoring
"""

from .protocols import MemoryBackend, CheckpointStore, ContextStore
from .structures import OptimizedCheckpoint, MemoryPool, StringIntern

# Import optional components only if available
try:
    from .chromadb_backend import ChromaDBBackend
    _HAS_CHROMADB_BACKEND = True
except ImportError:
    ChromaDBBackend = None
    _HAS_CHROMADB_BACKEND = False

try:
    from .manager import HighPerformanceMemoryManager
    _HAS_MANAGER = True
except ImportError:
    HighPerformanceMemoryManager = None
    _HAS_MANAGER = False

__all__ = [
    'MemoryBackend',
    'CheckpointStore', 
    'ContextStore',
    'OptimizedCheckpoint',
    'MemoryPool',
    'StringIntern',
]

if _HAS_CHROMADB_BACKEND:
    __all__.append('ChromaDBBackend')
    
if _HAS_MANAGER:
    __all__.append('HighPerformanceMemoryManager')
