# Memory Subsystem Documentation

## Module Overview

The memory subsystem provides comprehensive conversation memory and context management for the JK-Agents Framework. It combines LangGraph's built-in checkpointing system with intelligent context search capabilities to enable efficient conversation continuity across multiple interactions. The system supports both simple MemorySaver and advanced ChromaDB backends for different use cases.

### Key Features
- **Thread-based Memory Isolation**: Each conversation maintains its own memory space
- **Smart Context Search**: Intelligent extraction and retrieval of relevant context
- **Multi-Backend Support**: Standard MemorySaver or ChromaDB for production
- **Supervisor Context Injection**: Conversation history available to planning agents
- **Efficient Context Usage**: Only retrieves what's contextually needed via vector search
- **Real-time Memory Management**: Built-in cleanup and optimization

## Setup Instructions

### Prerequisites

1. **Python 3.11+** installed
2. **ChromaDB Installation**:
   ```bash
   pip install chromadb>=1.0.0
   pip install langchain-chroma>=0.2.4
   pip install sentence-transformers>=2.2.2
   ```

3. **Additional Dependencies**:
   ```bash
   pip install orjson  # Fast JSON serialization (optional but recommended)
   pip install psutil>=5.9.0  # System monitoring
   pip install tiktoken>=0.7.0  # Token counting
   ```

### Configuration Examples

**Development Config (MemorySaver - in-memory):**
```yaml
# config/simple_memory_test.yaml
models:
  default: "google:gemini-2.0-flash-exp"
  supervisor: "google:gemini-1.5-pro"

business_context: |
  This is a simple memory test configuration.
  You have access to smart context search for referencing previous conversation items.

supervisor:
  name: "supervisor"
  prompt: "You are a task planning supervisor. Break down complex queries into simple executable steps."

checkpointer:
  storage_type: "memory"  # Uses MemorySaver (development)
  enable_stats: true

agents:
  - name: "memory_test_agent"
    description: "Agent for testing memory and context search functionality"
    model: "google:gemini-2.0-flash-lite-001"
    prompt: |
      You are a helpful assistant with memory capabilities. 
      When users refer to "these", "those", "them", or similar references, 
      use the search_context_history tool to find relevant previous information.
      
      Always be specific about what you found and reference the original context.
```

**Production Config (ChromaDB - persistent):**
```yaml
# config/production_memory.yaml
models:
  default: "azure_openai:gpt-4o"
  supervisor: "azure_openai:gpt-4o"

business_context: |
  Production multi-agent system with persistent memory.

supervisor:
  name: "production_supervisor"
  prompt: "You are an enterprise task planning supervisor with access to conversation memory."

checkpointer:
  storage_type: "chroma"  # Uses ChromaDB (production)
  chroma_collection: "production_memory"
  enable_stats: true
  cleanup_enabled: true

agents:
  - name: "production_agent"
    description: "Production agent with full memory capabilities"
    model: "azure_openai:gpt-4o"
    prompt: |
      You are an enterprise assistant with comprehensive memory access.
      Use context search to reference previous conversations efficiently.
      Maintain conversation continuity across sessions.
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args: ["run", "-N", "jsr:@pydantic/mcp-run-python", "stdio"]
```

```python
from app.memory.chromadb_backend import ChromaDBConfig, ChromaDBBackend
from app.memory.manager import MemoryManager, ResourceLimits

# Configure ChromaDB backend
config = ChromaDBConfig(
    path="./chroma_memory",  # Persistent storage path
    max_connections=50,
    min_connections=5,
    l1_cache_size=10000,
    l1_cache_ttl=1800,
    batch_size=100,
    enable_metrics=True
)

# Configure resource limits
limits = ResourceLimits(
    max_memory_mb=2048,
    max_connections=100,
    max_concurrent_operations=500,
    max_cache_size=50000
)

# Initialize memory manager
memory_manager = MemoryManager(
    backend_config=config,
    resource_limits=limits
)
```

### Quick Start

```python
# Initialize for use with agents
from app.checkpointer_manager import get_global_checkpointer

# Get global checkpointer instance
checkpointer = get_global_checkpointer(app_config)

# Use with agent
agent_config = {
    "checkpointer": checkpointer,
    "thread_id": "session_123"
}
```

## Design Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System Architecture                 │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                               │
│  • FastAPI Endpoints (/memory/stats, /memory/clear)        │
│  • Thread ID Management (get_or_create_thread_id)          │
│  • Memory Stats & Cleanup Functions                        │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Checkpointer Manager                        │
│  • Global Singleton Pattern                                │
│  • Backend Selection (MemorySaver/ChromaDB)                │
│  • Configuration Management                                 │
└─────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   LangGraph     │ │  Smart Context  │ │   Supervisor    │
│  Integration    │ │     Search      │ │    Context      │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ • Agent Builder │ │ • Entity Extract│ │ • History Load  │
│ • Checkpointer  │ │ • Relevance     │ │ • Context Inject│
│ • Thread Config │ │ • Vector Search │ │ • Planning Aid  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend Storage                         │
│                                                             │
│  Standard Mode:          Production Mode:                   │
│  • MemorySaver          • ChromaDB Backend                 │
│  • In-Memory            • Persistent Storage               │
│  • Thread-based         • Vector Embeddings               │
│                         • Multi-level Caching             │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **Checkpointer Manager** (`checkpointer_manager.py`)

The central memory orchestration layer that provides global checkpointer instances:

**Features:**
- **Singleton Pattern**: Global shared checkpointer instance
- **Backend Selection**: Automatic backend selection based on configuration
- **Memory Statistics**: Built-in memory usage tracking and reporting
- **Thread Cleanup**: Memory cleanup utilities for thread management

**Configuration:**
```python
class CheckpointerManager:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._memory_backend = config.get("memory", {}).get("backend", "standard")
        
        if self._memory_backend == "chromadb":
            # ChromaDB backend for production
            self._checkpointer = ChromaDBCheckpointer(...)
        else:
            # Standard MemorySaver for development
            self._checkpointer = MemorySaver()
```

#### 2. **Smart Context Search** (`smart_context_search.py`)

Intelligent conversation context search system:

**Features:**
- **Context Query Detection**: Automatically detects when users reference "these", "them", "those"
- **Entity Extraction**: Extracts IDs, numbers, lists, and key phrases from messages
- **Relevance Scoring**: Ranks context items by relevance to current query
- **Efficient Retrieval**: Only returns contextually needed information
- **Vector-like Search**: Uses keyword and semantic matching for context relevance

**Search Strategy:**
```python
class ContextSearcher:
    def detect_context_query_type(self, query: str) -> str:
        # Reference to specific items/entities
        if any(word in query_lower for word in ['these', 'them', 'those']):
            if any(word in query_lower for word in ['count', 'number']):
                return 'count_items'
            else:
                return 'reference_items'
        return 'general'
        
    def extract_entities_from_messages(self, messages) -> List[Dict]:
        # Extract IDs, lists, key phrases with context
        entities = []
        for msg in messages:
            # ID patterns: numbers, work item IDs
            # List patterns: numbered items, bullet points
            # Key phrases: titles, bold text
        return entities
```

#### 3. **ChromaDB Backend** (`chromadb_backend.py`)

High-performance vector database backend:

**Features:**
- **Connection Pooling**: Efficient connection management
- **Multi-level Caching**: L1 (memory) and L2 (disk) caches
- **Batch Processing**: Optimized bulk operations
- **User Isolation**: Multi-tenant support with user-specific namespaces
- **Async Operations**: Non-blocking I/O for concurrency

**Collections:**
- `jk_checkpoints`: Agent state and conversation history
- `jk_contexts`: Long-term context storage
- `jk_embeddings`: Vector embeddings for semantic search

#### 3. **Data Structures** (`structures.py`)

Memory-efficient data structures for zero-copy operations:

**OptimizedCheckpoint:**
```python
@dataclass(slots=True, frozen=True)
class OptimizedCheckpoint:
    thread_id: str
    user_hash: int      # 8 bytes vs full string
    timestamp: int      # Unix timestamp
    data: bytes         # Pre-serialized
    size: int
```

**String Interning:**
- Deduplicates common strings (thread IDs, agent names)
- Reduces memory usage by 30-40% for string-heavy workloads

**Memory Pool:**
- Pre-allocated buffer pool
- Eliminates allocation overhead
- Reduces garbage collection pressure

#### 4. **LangGraph Adapter** (`langgraph_adapter.py`)

Integration with LangGraph's checkpointing system:

**Features:**
- Seamless integration with LangGraph agents
- State persistence and recovery
- Thread-based conversation tracking
- Checkpoint versioning and rollback

#### 5. **ChromaDB Checkpointer** (`chromadb_checkpointer.py`)

Persistent checkpointing implementation:

**Features:**
- Automatic checkpoint creation
- Configurable retention policies
- Checkpoint compression
- Fast recovery mechanisms

#### 6. **Enhanced Tool Node** (`enhanced_tool_node.py`)

Tool execution with memory integration:

**Features:**
- Tool output caching
- Result persistence
- Execution history tracking

#### 7. **Smart Tool Wrapper** (`smart_tool_wrapper.py`)

Intelligent handling of tool outputs:

**Features:**
- Large output detection and storage
- Automatic summarization
- Reference-based retrieval

#### 8. **Simple ChromaDB Memory** (`simple_chromadb_memory.py`)

Lightweight memory interface for simple use cases:

**Features:**
- Simplified API
- Quick setup
- Basic CRUD operations

## Usage Guide

### Basic Configuration

**Standard Configuration (Development):**
```yaml
# config/agents.yaml
memory:
  backend: "standard"  # Uses MemorySaver

agents:
  - name: "assistant"
    model: "azure_openai:gpt-4.1"
    prompt: |
      You are a helpful assistant with memory capabilities.
      {{dependent_request_responses}}
```

**Production Configuration (ChromaDB):**
```yaml
# config/agents.yaml
memory:
  backend: "chromadb"
  chromadb:
    path: "./advanced_memory"
    max_connections: 20
    l1_cache_size: 5000
    enable_metrics: true
```

### Basic Memory Operations

```python
from app.checkpointer_manager import get_global_checkpointer
from app.thread_manager import get_or_create_thread_id

# Get global checkpointer instance
app_config = {"memory": {"backend": "standard"}}
checkpointer = get_global_checkpointer(app_config)

# Create or get thread ID
thread_id = get_or_create_thread_id("optional-existing-thread")

# Get memory statistics
from app.checkpointer_manager import get_memory_stats
stats = get_memory_stats()
print(f"Total threads: {stats['total_threads']}")
print(f"Threads: {stats['threads']}")
```

### Smart Context Search Usage

**Automatic Context Tool Integration:**
The smart context search tool is automatically added to agents when a thread_id is available:

```python
from api import run_direct_agent_api

# First query establishes context
result1 = await run_direct_agent_api(
    agent_name="simple_agent",
    user_input="Here are three numbers: 42, 87, 156",
    app_cfg=app_cfg,
    thread_id="conversation-123"
)

# Second query references context
result2 = await run_direct_agent_api(
    agent_name="simple_agent", 
    user_input="What's the average of those numbers?",  # "those" triggers context search
    app_cfg=app_cfg,
    thread_id="conversation-123"  # Same thread
)

# The agent will automatically:
# 1. Detect "those" as a context reference
# 2. Search conversation history for relevant numbers
# 3. Find [42, 87, 156] from previous message
# 4. Calculate the average
```

**Manual Context Search Tool Usage:**
```python
from app.smart_context_search import create_smart_context_tool
from app.checkpointer_manager import get_global_checkpointer

# Create context search tool
checkpointer = get_global_checkpointer()
context_tool = create_smart_context_tool("thread-123", checkpointer)

# Use tool to search for context
context_result = context_tool("find the user stories we discussed")
print(context_result)
# Output: Found 3 relevant items from previous conversation:
# 1. Id: 19283111
#    Context: **ID 19283111** Title: MX | Rule Based Insight...
```

**Context Query Types:**
- `reference_items`: "these", "them", "those" → Returns specific items/entities
- `count_items`: "count of these", "how many of those" → Returns items for counting
- `calculate_items`: "average of these", "sum of those" → Returns items for calculation
- `recall_information`: "what we discussed", "mentioned earlier" → Returns general information

### Agent Memory Integration

**Building Agents with Memory:**
```python
from app.agent_builder import build_react_agent
from app.checkpointer_manager import get_global_checkpointer

# Get checkpointer
checkpointer = get_global_checkpointer(app_config)

# Build agent with memory and context search
agent, mcp_client = await build_react_agent(
    agent_config,
    default_model="azure_openai:gpt-4.1",
    checkpointer=checkpointer,
    thread_id="conversation-123",  # Enables smart context search tool
)

# Execute with thread tracking
config = {"configurable": {"thread_id": "conversation-123"}}
result = await agent.ainvoke(
    {"messages": [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What did we discuss about those items?"}
    ]},
    config=config
)
```

### Test Scripts and Validation

**Simple Memory Test Script:**
```python
# scripts/test_memory_context.py
import asyncio
from api import run_direct_agent_api
from app.config import load_app_config
from app.thread_manager import get_thread_id

async def test_memory_context():
    # Load test configuration
    app_cfg = load_app_config("config/simple_memory_test.yaml")
    thread_id = get_thread_id()  # Generate unique thread
    
    print(f"Testing memory with thread ID: {thread_id}")
    
    # Test 1: Store some information
    print("\n=== Test 1: Storing Context ===")
    result1 = await run_direct_agent_api(
        agent_name="memory_test_agent",
        user_input="Remember these user story IDs: 12345, 67890, 11111",
        app_cfg=app_cfg,
        thread_id=thread_id
    )
    print(f"Agent Response: {result1['response']}")
    
    # Test 2: Reference stored information
    print("\n=== Test 2: Referencing Context ===")
    result2 = await run_direct_agent_api(
        agent_name="memory_test_agent",
        user_input="What were those user story IDs again?",
        app_cfg=app_cfg,
        thread_id=thread_id
    )
    print(f"Agent Response: {result2['response']}")
    
    # Test 3: Complex context calculation
    print("\n=== Test 3: Context Calculation ===")
    result3 = await run_direct_agent_api(
        agent_name="memory_test_agent",
        user_input="What's the average of those IDs?",
        app_cfg=app_cfg,
        thread_id=thread_id
    )
    print(f"Agent Response: {result3['response']}")
    
    # Test memory stats
    print("\n=== Memory Statistics ===")
    from app.checkpointer_manager import get_global_checkpointer
    checkpointer = get_global_checkpointer()
    stats = checkpointer.get_memory_stats()
    print(f"Memory Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(test_memory_context())
```

**CLI Testing Commands:**
```bash
# Test memory with CLI
python scripts/test_memory_context.py

# Direct CLI testing with same thread
python -m app.main "Store these numbers: 10, 20, 30" --config config/simple_memory_test.yaml --thread-id test-123
python -m app.main "What's the sum of those numbers?" --config config/simple_memory_test.yaml --thread-id test-123

# Test memory stats
curl -X GET http://localhost:8000/memory/stats

# Clear specific thread
curl -X DELETE http://localhost:8000/memory/clear/test-123
```

### Debugging and Monitoring

**Memory Debug Mode:**
```python
# Enable detailed memory logging
import logging
logging.getLogger('app.smart_context_search').setLevel(logging.DEBUG)
logging.getLogger('app.checkpointer_manager').setLevel(logging.DEBUG)

# Check memory usage
from app.checkpointer_manager import get_global_checkpointer
checkpointer = get_global_checkpointer()
stats = checkpointer.get_memory_stats()
print(f"Active threads: {stats.get('thread_count', 0)}")
print(f"Total messages: {stats.get('message_count', 0)}")
```

**Context Search Debug:**
```python
# Debug context search behavior
from app.smart_context_search import detect_context_query, extract_entities

# Test query detection
query = "What were those user stories we discussed?"
query_type = detect_context_query(query)
print(f"Query type: {query_type}")  # Should be 'recall_information'

# Test entity extraction  
text = "Here are the IDs: 12345, 67890, 11111"
entities = extract_entities(text)
print(f"Entities found: {entities}")
```

### Performance Considerations

**Memory Backend Selection:**
- **MemorySaver**: Best for development, testing, and short sessions
  - Fast in-memory operations
  - Automatic cleanup on process restart
  - No persistence between sessions

- **ChromaDB**: Best for production and long-term memory
  - Persistent storage across restarts
  - Vector-based similarity search
  - Optimized for large conversation histories
  - Requires disk space for storage

**Context Search Optimization:**
```python
# Limit search scope for better performance
context_tool = create_smart_context_tool(
    thread_id="conversation-123",
    checkpointer=checkpointer,
    max_results=5,  # Limit results for efficiency
    score_threshold=0.3  # Only return high-relevance matches
)
```

**Memory Cleanup Strategies:**
```python
# Automated cleanup (production)
checkpointer_config = {
    "storage_type": "chroma",
    "cleanup_enabled": True,
    "max_thread_age_days": 30,  # Clean threads older than 30 days
    "max_messages_per_thread": 1000  # Limit thread size
}

# Manual cleanup
checkpointer = get_global_checkpointer()
checkpointer.cleanup_old_threads(days=7)  # Clean 7+ day old threads
```

### Troubleshooting

**Common Issues and Solutions:**

1. **Context Search Not Working:**
   ```python
   # Check if tool was added to agent
   agent_tools = [tool.name for tool in agent.tools]
   print("Available tools:", agent_tools)
   # Should include 'search_context_history'
   ```

2. **Memory Stats Empty:**
   ```python
   # Verify checkpointer initialization
   checkpointer = get_global_checkpointer()
   print(f"Checkpointer type: {type(checkpointer)}")
   print(f"Stats enabled: {checkpointer.stats_enabled}")
   ```

3. **ChromaDB Connection Issues:**
   ```bash
   # Check ChromaDB directory permissions
   ls -la chroma_memory/
   
   # Clear corrupted ChromaDB
   rm -rf chroma_memory/ && mkdir chroma_memory/
   ```

4. **High Memory Usage:**
   ```python
   # Monitor memory stats
   stats = checkpointer.get_memory_stats()
   if stats.get('message_count', 0) > 10000:
       print("Consider running cleanup")
       checkpointer.cleanup_old_threads(days=7)
   ```

5. **Context Search Returns Irrelevant Results:**
   ```python
   # Adjust search parameters
   # Increase score threshold for more precision
   # Decrease for more recall
   context_tool = create_smart_context_tool(
       thread_id=thread_id,
       checkpointer=checkpointer,
       score_threshold=0.5  # Higher = more selective
   )
   ```

**Debug Mode Activation:**
```python
# Enable comprehensive debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Specific memory system debug
loggers = [
    'app.smart_context_search',
    'app.checkpointer_manager', 
    'app.agent_builder',
    'langchain.schema.runnable'
]

for logger_name in loggers:
    logging.getLogger(logger_name).setLevel(logging.DEBUG)
```

### Advanced Usage: Context Storage

```python
from app.memory.protocols import ContextStore

# Store long-term context
await manager.store_context(
    context_id="project_context",
    user_id="user_456",
    context_data={
        "project_name": "AI Assistant",
        "preferences": {"temperature": 0.7},
        "history": []
    },
    ttl=86400  # 24 hours
)

# Retrieve context
context = await manager.get_context(
    context_id="project_context",
    user_id="user_456"
)

# Update context
await manager.update_context(
    context_id="project_context",
    user_id="user_456",
    updates={"preferences": {"temperature": 0.5}}
)
```

### Integration with Agents

```python
from app.agent_builder import build_react_agent
from app.checkpointer_manager import get_global_checkpointer

# Get checkpointer
checkpointer = get_global_checkpointer(app_config)

# Build agent with memory
agent, mcp_client = await build_react_agent(
    agent_config,
    default_model="google:gemini-2.0-flash-exp",
    checkpointer=checkpointer
)

# Execute with thread tracking
config = {"configurable": {"thread_id": "session_123"}}
result = await agent.ainvoke(
    {"input": "What did we discuss earlier?"},
    config=config
)
```

### Performance Monitoring

```python
# Get performance metrics
metrics = await manager.get_performance_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate']:.2f}%")
print(f"Average latency: {metrics['average_latency']:.3f}s")
print(f"Operations/sec: {metrics['operations_per_second']:.0f}")

# Get memory statistics
stats = await manager.get_memory_stats()
print(f"Total checkpoints: {stats['total_checkpoints']}")
print(f"Memory usage: {stats['memory_usage_mb']:.2f} MB")
print(f"Active connections: {stats['active_connections']}")

# Performance report
report = manager.performance_monitor.get_performance_report()
print(f"CPU usage: {report['current']['cpu_usage']:.1f}%")
print(f"Memory usage: {report['current']['memory_usage']:.1f}%")
```

### Batch Operations

```python
# Batch store
checkpoints = [
    {"thread_id": f"thread_{i}", "data": {"step": i}}
    for i in range(100)
]

await manager.batch_store_checkpoints(
    checkpoints,
    user_id="user_456"
)

# Batch retrieve
thread_ids = [f"thread_{i}" for i in range(100)]
results = await manager.batch_get_checkpoints(
    thread_ids,
    user_id="user_456"
)
```

### Memory Cleanup

```python
from app.checkpointer_manager import (
    clear_thread_memory,
    reset_all_memory,
    cleanup_old_checkpoints
)

# Clear specific thread
await clear_thread_memory("thread_123")

# Cleanup old checkpoints (older than 7 days)
deleted_count = await cleanup_old_checkpoints(days=7)
print(f"Deleted {deleted_count} old checkpoints")

# Reset all memory (caution!)
await reset_all_memory()
```

## Key Features

### 1. **High Performance**
- Sub-millisecond retrieval with caching
- Connection pooling for efficiency
- Batch operations for throughput
- Async/await for concurrency

### 2. **Scalability**
- Adaptive resource management
- Automatic scaling based on load
- Distributed backend support
- Horizontal scaling capability

### 3. **Reliability**
- Persistent storage with ChromaDB
- Checkpoint versioning
- Automatic recovery mechanisms
- Transaction support

### 4. **Multi-Tenancy**
- User isolation with namespacing
- Per-user quota management
- Access control hooks
- Audit logging

### 5. **Observability**
- Real-time performance metrics
- Resource usage monitoring
- Cache hit/miss statistics
- Detailed logging

## Configuration Options

### ChromaDB Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | `None` | Persistent storage path |
| `host` | `"localhost"` | ChromaDB server host |
| `port` | `8000` | ChromaDB server port |
| `max_connections` | `50` | Maximum connection pool size |
| `min_connections` | `5` | Minimum connection pool size |
| `l1_cache_size` | `10000` | L1 cache entries |
| `l1_cache_ttl` | `1800` | L1 cache TTL (seconds) |
| `batch_size` | `100` | Batch operation size |
| `enable_metrics` | `True` | Enable metrics collection |

### Resource Limits

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_memory_mb` | `1024` | Maximum memory usage |
| `max_connections` | `100` | Maximum connections |
| `max_concurrent_operations` | `500` | Maximum concurrent ops |
| `max_cache_size` | `50000` | Maximum cache entries |
| `scale_up_cpu_threshold` | `80.0` | CPU threshold for scale-up |
| `scale_down_cpu_threshold` | `20.0` | CPU threshold for scale-down |

## Best Practices

### Performance Optimization
1. Enable multi-level caching for read-heavy workloads
2. Use batch operations for bulk data
3. Configure connection pool based on concurrency
4. Monitor cache hit rates and adjust sizes

### Memory Management
1. Set appropriate TTL for context data
2. Implement regular cleanup jobs
3. Monitor memory usage trends
4. Use string interning for repeated values

### Reliability
1. Configure persistent storage path
2. Implement checkpoint retention policies
3. Set up monitoring and alerting
4. Test recovery procedures

### Security
1. Enable user isolation
2. Implement access control
3. Audit sensitive operations
4. Encrypt data at rest

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check cache sizes
   - Review retention policies
   - Enable cleanup jobs
   - Monitor for memory leaks

2. **Slow Retrieval**
   - Verify cache configuration
   - Check connection pool size
   - Review indexing
   - Monitor network latency

3. **Connection Errors**
   - Check ChromaDB server status
   - Verify network connectivity
   - Review firewall rules
   - Check authentication

4. **Data Loss**
   - Verify persistent storage
   - Check disk space
   - Review backup procedures
   - Test recovery mechanisms

## Performance Metrics

### Key Metrics to Monitor

- **Cache Performance**
  - Hit rate (target: >90%)
  - Miss rate
  - Eviction rate
  - Cache size

- **Operation Latency**
  - Average latency (<100ms)
  - P95 latency
  - P99 latency
  - Max latency

- **Resource Usage**
  - Memory consumption
  - CPU utilization
  - Connection pool usage
  - Disk I/O

- **Throughput**
  - Operations per second
  - Batch processing rate
  - Concurrent operations
  - Queue lengths

## Extension Points

1. **Custom Backends**: Implement alternative storage backends
2. **Cache Strategies**: Add custom caching algorithms
3. **Serialization**: Integrate custom serializers
4. **Monitoring**: Add custom metrics collectors
5. **Security**: Implement custom authentication/authorization