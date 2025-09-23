"""
Memory Backend System for JK-Agents Framework

This package provides memory backends for storing and retrieving
conversation checkpoints and context for LangGraph agents.

Available Components:
- Simple ChromaDB memory integration
- LangGraph checkpointer
- High-performance backends (optional)
"""

# Core simple components (always available)
from .simple_chromadb_memory import SimpleChromaDBMemory, create_memory_enabled_graph
from .chromadb_checkpointer import ChromaDBCheckpointer, create_chromadb_checkpointer

# Import optional advanced components only if available
try:
    from .protocols import MemoryBackend, CheckpointStore, ContextStore
    _HAS_PROTOCOLS = True
except ImportError:
    _HAS_PROTOCOLS = False

try:
    from .structures import OptimizedCheckpoint, MemoryPool, StringIntern
    _HAS_STRUCTURES = True
except ImportError:
    _HAS_STRUCTURES = False

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

try:
    from .langgraph_adapter import HighPerformanceCheckpointer, MemorySaverReplacement
    _HAS_LANGGRAPH_ADAPTER = True
except ImportError:
    HighPerformanceCheckpointer = None
    MemorySaverReplacement = None
    _HAS_LANGGRAPH_ADAPTER = False

# Core exports (always available)
__all__ = [
    'SimpleChromaDBMemory',
    'create_memory_enabled_graph',
    'ChromaDBCheckpointer', 
    'create_chromadb_checkpointer',
]

# Add optional exports
if _HAS_PROTOCOLS:
    __all__.extend(['MemoryBackend', 'CheckpointStore', 'ContextStore'])

if _HAS_STRUCTURES:
    __all__.extend(['OptimizedCheckpoint', 'MemoryPool', 'StringIntern'])
    
if _HAS_CHROMADB_BACKEND:
    __all__.append('ChromaDBBackend')
    
if _HAS_MANAGER:
    __all__.append('HighPerformanceMemoryManager')

if _HAS_LANGGRAPH_ADAPTER:
    __all__.extend(['HighPerformanceCheckpointer', 'MemorySaverReplacement'])
