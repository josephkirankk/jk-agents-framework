"""
Memory Backend System for JK-Agents Framework

This package provides memory backends for storing and retrieving
conversation checkpoints and context for LangGraph agents.

Available Components:
- Simple ChromaDB memory integration
- LangGraph checkpointer
- High-performance backends (optional)
"""

# Core simple components (try to import, fail gracefully if dependencies missing)
try:
    from .simple_chromadb_memory import SimpleChromaDBMemory, create_memory_enabled_graph
    _HAS_SIMPLE_CHROMADB = True
except ImportError:
    SimpleChromaDBMemory = None
    create_memory_enabled_graph = None
    _HAS_SIMPLE_CHROMADB = False

try:
    from .chromadb_checkpointer import ChromaDBCheckpointer, create_chromadb_checkpointer
    _HAS_CHROMADB_CHECKPOINTER = True
except ImportError:
    ChromaDBCheckpointer = None
    create_chromadb_checkpointer = None
    _HAS_CHROMADB_CHECKPOINTER = False

# Memory transaction logging (always available - no external dependencies)
try:
    from .transaction_logger import MemoryTransactionLogger, get_memory_logger, initialize_memory_logger
    from .conversation_store import ConversationStore, ConversationEntry
    from .context_enhancer import ConversationContextEnhancer
    from .memory_integration import initialize_conversation_memory, enhance_system_message_with_memory
    _HAS_MEMORY_LOGGING = True
except ImportError:
    _HAS_MEMORY_LOGGING = False

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

# Core exports (conditionally available)
__all__ = []

if _HAS_SIMPLE_CHROMADB:
    __all__.extend(['SimpleChromaDBMemory', 'create_memory_enabled_graph'])
    
if _HAS_CHROMADB_CHECKPOINTER:
    __all__.extend(['ChromaDBCheckpointer', 'create_chromadb_checkpointer'])
    
if _HAS_MEMORY_LOGGING:
    __all__.extend([
        'MemoryTransactionLogger', 'get_memory_logger', 'initialize_memory_logger',
        'ConversationStore', 'ConversationEntry', 'ConversationContextEnhancer',
        'initialize_conversation_memory', 'enhance_system_message_with_memory'
    ])

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
