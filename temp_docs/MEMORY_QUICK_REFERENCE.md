# Memory System - Quick Reference Guide

## Quick Start

### Basic Setup

```python
# 1. Initialize conversation memory (PostgreSQL)
from app.memory import initialize_conversation_memory
from app.config import AppConfig

config = AppConfig()
await initialize_conversation_memory(config)

# 2. Create LangGraph checkpointer
from app.memory import HighPerformanceCheckpointer

checkpointer = HighPerformanceCheckpointer({
    "memory": {
        "backend": "chromadb",
        "chromadb": {"path": "./checkpoints"}
    }
})

# 3. Use with LangGraph agent
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(llm, tools, checkpointer=checkpointer)
result = await agent.ainvoke(
    {"messages": [HumanMessage("Hello")]},
    config={"configurable": {"thread_id": "user_123"}}
)
```

## Common Patterns

### Pattern 1: Agent with Conversation Memory

```python
async def create_memory_agent(llm, tools):
    """Create agent with full memory support"""
    
    # Initialize systems
    config = AppConfig()
    await initialize_conversation_memory(config)
    checkpointer = HighPerformanceCheckpointer()
    await checkpointer._ensure_initialized()
    
    # Create agent
    agent = create_react_agent(llm, tools, checkpointer=checkpointer)
    
    return agent, config

async def chat_with_memory(agent, config, thread_id, message):
    """Chat with conversation history"""
    
    # Get context
    from app.memory import enhance_system_message_with_memory
    context = await enhance_system_message_with_memory(
        "You are a helpful assistant.",
        thread_id,
        config
    )
    
    # Run agent
    result = await agent.ainvoke(
        {"messages": [HumanMessage(message)]},
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # Store for next time
    from app.memory import store_conversation_memory
    await store_conversation_memory(
        thread_id, message,
        result["messages"][-1].content,
        config
    )
    
    return result
```

### Pattern 2: Large Data Handling

```python
from app.memory import EnhancedToolNode

# Wrap tools with automatic optimization
tools = [your_tool_1, your_tool_2]
enhanced_node = EnhancedToolNode(
    tools=tools,
    config={
        "enabled": True,
        "token_threshold": 1000,  # Optimize responses >1000 tokens
        "large_data": {
            "sqlite_path": "./large_data.db",
            "file_path": "./large_files/"
        }
    }
)

# Use in LangGraph
graph.add_node("tools", enhanced_node)
```

### Pattern 3: Direct Conversation Store

```python
from app.memory import ConversationStore

store = ConversationStore(
    database_url=os.getenv("DATABASE_URL"),
    pool_size=10
)
await store.initialize()

# Store
await store.store_conversation(
    thread_id="thread_123",
    user_message="Question",
    assistant_response="Answer"
)

# Retrieve
conversations = await store.get_recent_conversations(
    thread_id="thread_123",
    limit=5
)
```

## Common Issues & Solutions

### Issue 1: "Circuit breaker is OPEN"

**Cause**: Too many failures connecting to backend  
**Solution**:
```python
# Check backend health
health = await checkpointer.health_check()
print(health)

# Reset circuit breaker (if transient issue resolved)
checkpointer._circuit_breaker.failure_count = 0
checkpointer._circuit_breaker.state = "CLOSED"
```

### Issue 2: Slow checkpoint operations

**Cause**: Using embeddings instead of direct storage  
**Solution**: Use FastCheckpointer (SQLite) instead

```python
# Replace chromadb_checkpointer with:
from app.memory.fast_checkpointer import FastCheckpointer

checkpointer = FastCheckpointer(db_path="./checkpoints.db")
```

### Issue 3: Memory leaks

**Cause**: Not cleaning up old data  
**Solution**:
```python
# Schedule periodic cleanup
import asyncio

async def cleanup_loop():
    while True:
        await asyncio.sleep(3600)  # Every hour
        
        # Clean conversations
        from app.memory import cleanup_old_conversations
        deleted = await cleanup_old_conversations(config)
        
        # Clean large data
        from app.memory import LargeDataStorage
        storage = LargeDataStorage()
        storage.cleanup_expired_data()
```

### Issue 4: "Cannot call sync get() from async context"

**Cause**: Using sync methods in async code  
**Solution**: Use async versions

```python
# BAD
checkpoint = checkpointer.get(config)

# GOOD
checkpoint = await checkpointer.aget(config)
```

## Configuration Cheat Sheet

### Minimal (Development)

```yaml
conversation_memory:
  enabled: true
  database_url: "postgresql://localhost/dev"
  
chromadb:
  path: "./data/chromadb"
```

### Production (High Performance)

```yaml
conversation_memory:
  enabled: true
  database_url: "postgresql://prod-host/db"
  pool_size: 50
  max_conversations: 20
  cleanup_days: 30

chromadb:
  path: "/data/chromadb"
  max_connections: 100
  batch_size: 200
  batch_timeout: 0.05
  l1_cache_size: 50000
  enable_batch_processing: true

performance:
  max_memory_mb: 2048
  max_concurrent_operations: 1000
```

### Memory-Constrained

```yaml
chromadb:
  path: "./chromadb"
  max_connections: 10
  batch_size: 20
  l1_cache_size: 1000

performance:
  max_memory_mb: 256
```

## Testing Snippets

### Test Checkpoint Save/Load

```python
async def test_checkpoint():
    checkpointer = HighPerformanceCheckpointer()
    await checkpointer._ensure_initialized()
    
    config = {"configurable": {"thread_id": "test"}}
    checkpoint = {"data": "test_data"}
    
    # Save
    await checkpointer.aput(config, checkpoint, {}, {})
    
    # Load
    loaded = await checkpointer.aget(config)
    assert loaded is not None
    print(f"✓ Checkpoint saved and loaded: {loaded}")
```

### Test Conversation Store

```python
async def test_conversations():
    store = ConversationStore(
        database_url=os.getenv("DATABASE_URL")
    )
    await store.initialize()
    
    # Store
    await store.store_conversation(
        thread_id="test",
        user_message="Hello",
        assistant_response="Hi!"
    )
    
    # Retrieve
    convs = await store.get_recent_conversations("test", limit=1)
    assert len(convs) == 1
    assert convs[0].user_message == "Hello"
    print(f"✓ Conversation stored and retrieved")
```

### Test Large Data

```python
def test_large_data():
    from app.memory import LargeDataStorage
    
    storage = LargeDataStorage()
    
    # Store large data
    large_data = {"items": [f"item_{i}" for i in range(10000)]}
    ref_id = "test_ref_123"
    
    info = storage.store_large_data(
        reference_id=ref_id,
        tool_name="test_tool",
        data=large_data
    )
    
    print(f"Stored {info.size_mb:.2f}MB as {info.storage_type}")
    
    # Retrieve
    retrieved = storage.retrieve_large_data(ref_id)
    assert retrieved == large_data
    print("✓ Large data stored and retrieved")
```

## Performance Monitoring

### Check Memory Stats

```python
# Get comprehensive stats
stats = await checkpointer.get_comprehensive_stats()

print(f"Cache hit rate: {stats['backend']['cache']['hit_rate']:.1%}")
print(f"Active connections: {stats['backend']['pool']['active_operations']}")
print(f"CPU usage: {stats['performance']['current']['cpu_usage']:.1f}%")
print(f"Memory usage: {stats['performance']['current']['memory_usage']:.1f}%")
```

### Monitor Operations

```python
from app.memory import get_memory_logger

# Check transaction logs
logger = get_memory_logger()
# Logs are in: ./memory_logs/memory_{thread_id}_{timestamp}.log
```

### Get Storage Stats

```python
from app.memory import LargeDataStorage

storage = LargeDataStorage()
stats = storage.get_storage_stats()

print(f"Total references: {stats['total_references']}")
print(f"Total size: {stats['total_size_mb']:.2f}MB")
print(f"File system usage: {stats['file_system_usage']:.2f}MB")
```

## Troubleshooting Commands

### Reset Stuck Circuit Breaker

```python
checkpointer._circuit_breaker.state = "CLOSED"
checkpointer._circuit_breaker.failure_count = 0
```

### Clear Cache

```python
# Clear LRU cache
if checkpointer._backend:
    checkpointer._backend.checkpoint_store._cache.clear()
```

### Force Checkpoint Flush

```python
# For batch processing systems
if checkpointer._backend:
    store = checkpointer._backend.checkpoint_store
    if hasattr(store, '_batch_queue'):
        # Process any queued batches immediately
        await store._process_batch(list(store._batch_queue._queue))
```

### Check Database Connection

```python
# Test PostgreSQL connection
store = ConversationStore(database_url=url)
try:
    await store.initialize()
    count = await store.count_conversations("test_thread")
    print(f"✓ Connected, {count} conversations found")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

## Environment Setup

### Required Environment Variables

```bash
# Database
export DATABASE_URL="postgresql://user:pass@localhost:5432/db"

# Optional
export CHROMADB_PATH="./data/chromadb"
export MEMORY_LOGGING_ENABLED="true"
export MEMORY_LOGGING_DIRECTORY="./memory_logs"
```

### Docker Compose Example

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: agents_db
      POSTGRES_USER: agent_user
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  agent:
    build: .
    environment:
      DATABASE_URL: postgresql://agent_user:secret@postgres:5432/agents_db
      CHROMADB_PATH: /data/chromadb
    volumes:
      - ./data:/data
    depends_on:
      - postgres
```

## Migration Guide

### From MemorySaver to HighPerformanceCheckpointer

```python
# Old
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# New
from app.memory import HighPerformanceCheckpointer
checkpointer = HighPerformanceCheckpointer()
await checkpointer._ensure_initialized()
```

### From Simple to Enhanced Tool Node

```python
# Old
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)

# New
from app.memory import EnhancedToolNode
tool_node = EnhancedToolNode(
    tools,
    config={"enabled": True, "token_threshold": 1000}
)
```

## Best Practices

### ✓ DO

1. **Always use async methods** in async contexts
2. **Set thread_id** for all agent invocations
3. **Clean up old data** periodically
4. **Monitor performance** with stats
5. **Use connection pooling** for databases
6. **Handle failures gracefully** with try-except
7. **Log important operations** for debugging

### ✗ DON'T

1. **Don't mix sync/async** event loops
2. **Don't ignore circuit breaker** states
3. **Don't store credentials** in code
4. **Don't skip cleanup** tasks
5. **Don't use embeddings** for simple key-value storage
6. **Don't log sensitive data** in production
7. **Don't ignore health checks**

## Quick Links

- Full Documentation: `MODULE_DOC_MEMORY_SYSTEM.md`
- Critical Issues: `MEMORY_CODE_REVIEW_CRITICAL_ISSUES.md`
- Code Fixes: `MEMORY_CRITICAL_FIXES.patch`
- Test Examples: `tests/test_memory_*.py`

## Support

For issues or questions:
1. Check logs in `./memory_logs/`
2. Review health check output
3. Examine stats and metrics
4. Consult full documentation
5. Create GitHub issue with logs

---

**Last Updated**: 2024  
**Version**: 1.0
