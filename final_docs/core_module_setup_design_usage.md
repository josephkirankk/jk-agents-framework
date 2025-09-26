# Core Module Documentation

## Module Overview

The `core` module provides essential utility systems for the JK-Agents Framework, focusing on efficient data handling, memory management, and system monitoring. It implements a multi-tier storage system, intelligent tool output wrapping, lazy data loading, and comprehensive memory monitoring with auto-cleanup capabilities.

## Setup Instructions

### Prerequisites

1. **Python 3.11+** installed
2. **Required Dependencies**:
   ```bash
   pip install sqlite3
   pip install psutil  # For memory monitoring
   pip install gzip    # For compression support
   ```

### Installation

```bash
# Install from the project root
cd jk-agents-framework
pip install -e .

# Or install specific core dependencies
pip install psutil>=5.9.0
```

### Configuration

```python
# Configure large data storage
from core.large_data_storage import LargeDataStorage

storage = LargeDataStorage(
    storage_path="./data/large_data_storage.db",
    file_storage_path="./data/large_files",
    max_file_size_mb=100,
    compression_enabled=True,
    cleanup_interval=3600,
    cache_size=1000,
    enable_caching=True,
    connection_pool_size=10
)
```

## Design Overview

### Architecture

```
┌────────────────────────────────────────────┐
│              Core Module                    │
├──────────────────────────────────────────────┤
│  Components:                                 │
│  • LargeDataStorage                         │
│  • SmartToolWrapper                         │
│  • LazyDataLoader                           │
│  • MemoryMonitor                            │
└────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌────────────────┐   ┌────────────────────┐
│  Multi-Tier    │   │   Intelligent      │
│   Storage      │   │    Monitoring      │
├────────────────┤   ├────────────────────┤
│ • Small: SQLite│   │ • Memory Tracking  │
│ • Medium: Comp │   │ • Auto-Cleanup     │
│ • Large: Files │   │ • Health Reports   │
│ • Huge: Chunked│   │ • Threshold Alerts │
└────────────────┘   └────────────────────┘
```

### Core Components

#### 1. **LargeDataStorage** (`large_data_storage.py`)

A sophisticated multi-tier storage system that intelligently manages data based on size:

**Storage Tiers:**
- **Small (< 1MB)**: SQLite with optional compression
- **Medium (1-50MB)**: SQLite with mandatory compression
- **Large (50-500MB)**: File system with SQLite metadata
- **Huge (> 500MB)**: Chunked file system with lazy loading

**Key Features:**
- **Connection Pooling**: Reduces SQLite connection overhead
- **LRU Caching**: Fast access to frequently used data
- **Automatic Compression**: GZIP compression for medium/large data
- **Metadata Tracking**: Access patterns, creation times, data types
- **Cleanup Scheduling**: Automatic removal of expired data
- **Thread Safety**: Concurrent access with proper locking

**Database Schema:**
```sql
CREATE TABLE data_references (
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
```

#### 2. **SmartToolWrapper** (`smart_tool_wrapper.py`)

Intelligently handles large tool outputs and creates dynamic exploration tools:

**Features:**
- **Automatic Detection**: Identifies large outputs based on token threshold
- **Smart Summarization**: Generates intelligent summaries of large data
- **Dynamic Tool Creation**: Creates data exploration tools on-the-fly
- **Lifecycle Management**: Auto-expires unused tools
- **Pattern Recognition**: Identifies data patterns (time-series, financial, etc.)

**Summarization Capabilities:**
- List analysis (records, numerical, text)
- Dictionary structure analysis
- Pattern identification
- Statistical summaries
- Large collection detection

#### 3. **LazyDataLoader** (`lazy_data_loader.py`)

Provides efficient lazy loading for large datasets:

**Features:**
- **Chunk-Based Loading**: Load data in manageable chunks
- **Iterator Pattern**: Memory-efficient data traversal
- **On-Demand Loading**: Load only what's needed
- **Streaming Support**: Process data without full loading

#### 4. **MemoryMonitor** (`memory_monitor.py`)

Comprehensive memory monitoring and auto-cleanup system:

**Thresholds:**
```python
@dataclass
class MemoryThresholds:
    warning_mb: float = 1000.0      # Log warning
    cleanup_mb: float = 1500.0      # Trigger cleanup
    critical_mb: float = 2000.0     # Aggressive cleanup
    emergency_mb: float = 3000.0    # Emergency cleanup + GC
```

**Monitoring Features:**
- Process memory tracking
- System memory percentage
- Python object counting
- Storage statistics
- Tool usage metrics
- Historical snapshots

## Usage Guide

### Basic Usage: Large Data Storage

```python
from core.large_data_storage import LargeDataStorage

# Initialize storage
storage = LargeDataStorage(
    storage_path="./data/storage.db",
    enable_caching=True
)

# Store data
data = {"results": [1, 2, 3] * 100000}  # Large dataset
reference_id = storage.store(
    data=data,
    data_type="analysis_results",
    metadata={"source": "calculation", "version": "1.0"}
)

# Retrieve data
retrieved_data = storage.retrieve(reference_id)

# Get storage statistics
stats = storage.get_storage_stats()
print(f"Total items: {stats['total_items']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")
```

### Advanced Usage: Smart Tool Wrapper

```python
from core.smart_tool_wrapper import SmartToolWrapper
from core.large_data_storage import LargeDataStorage

# Initialize components
storage = LargeDataStorage()
wrapper = SmartToolWrapper(
    storage=storage,
    token_threshold=5000,
    summarization_max_tokens=500
)

# Wrap a tool that might return large data
def analyze_dataset(query):
    # Simulate large result
    return [{"id": i, "value": i*2} for i in range(10000)]

# Process tool output
result = analyze_dataset("SELECT * FROM large_table")
wrapped_result = wrapper.wrap_tool_output(
    output=result,
    tool_name="analyze_dataset",
    original_input={"query": "SELECT * FROM large_table"}
)

# Result contains summary and reference
print(wrapped_result["summary"])
print(f"Data stored with reference: {wrapped_result['reference_id']}")

# Dynamic tools are automatically created
tools = wrapper.get_dynamic_tools()
```

### Memory Monitoring

```python
from core.memory_monitor import MemoryMonitor, MemoryThresholds

# Configure thresholds
thresholds = MemoryThresholds(
    warning_mb=500.0,
    cleanup_mb=750.0,
    critical_mb=1000.0,
    emergency_mb=1500.0
)

# Initialize monitor
monitor = MemoryMonitor(
    storage_manager=storage,
    tool_wrapper=wrapper,
    monitoring_interval=30,
    thresholds=thresholds,
    enable_auto_cleanup=True
)

# Start monitoring
monitor.start_monitoring()

# Get current memory snapshot
snapshot = monitor.get_current_snapshot()
print(f"Process memory: {snapshot.process_memory_mb:.2f} MB")
print(f"System memory: {snapshot.system_memory_percent:.1f}%")

# Get memory trends
trends = monitor.get_memory_trends(hours=1)
for trend in trends:
    print(f"{trend.timestamp}: {trend.process_memory_mb:.2f} MB")

# Manual cleanup trigger
cleanup_results = monitor.trigger_cleanup(force=True)
print(f"Freed memory: {cleanup_results['memory_freed_mb']:.2f} MB")
```

### Lazy Data Loading

```python
from core.lazy_data_loader import LazyDataLoader

# Create lazy loader for large file
loader = LazyDataLoader(
    source="./data/large_dataset.json",
    chunk_size=1000
)

# Process data in chunks
for chunk in loader:
    # Process chunk without loading entire dataset
    processed_chunk = process_data(chunk)
    # Save or aggregate results
    
# Get specific chunk
chunk_5 = loader.get_chunk(5)

# Get total chunks
total_chunks = loader.total_chunks()
```

### Integration with Agents

```python
from core.large_data_storage import LargeDataStorage
from core.smart_tool_wrapper import SmartToolWrapper
from app.agent_builder import build_react_agent

# Initialize core components
storage = LargeDataStorage()
wrapper = SmartToolWrapper(storage=storage)

# Create custom tool that uses smart wrapping
def data_analysis_tool(query: str) -> dict:
    """Analyze data with automatic large result handling."""
    raw_result = perform_analysis(query)
    return wrapper.wrap_if_large(raw_result, "data_analysis")

# Register tool with agent
agent_config = {
    "name": "data_analyst",
    "tools": [data_analysis_tool],
    "storage": storage
}
```

## Key Features

### 1. **Multi-Tier Storage Architecture**
- Automatic classification based on data size
- Optimal storage method selection
- Seamless retrieval regardless of storage tier
- Transparent compression/decompression

### 2. **Intelligent Caching**
- LRU cache for frequently accessed data
- Metadata caching for quick lookups
- Connection pooling for database operations
- Cache statistics and optimization

### 3. **Memory Management**
- Continuous monitoring with configurable intervals
- Multi-level threshold system
- Automatic cleanup triggers
- Emergency garbage collection

### 4. **Smart Summarization**
- Pattern recognition in data structures
- Statistical summaries for numerical data
- Structure analysis for complex objects
- Custom summarizer support

### 5. **Performance Optimization**
- Lazy loading for large datasets
- Chunk-based processing
- Thread-safe operations
- Weak references for memory efficiency

## Configuration Options

### LargeDataStorage Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `storage_path` | `"./data/large_data_storage.db"` | SQLite database path |
| `file_storage_path` | `"./data/large_files"` | Directory for file storage |
| `max_file_size_mb` | `100` | Maximum single file size |
| `compression_enabled` | `True` | Enable GZIP compression |
| `cleanup_interval` | `3600` | Cleanup interval in seconds |
| `cache_size` | `1000` | LRU cache size |
| `enable_caching` | `True` | Enable caching system |
| `connection_pool_size` | `10` | SQLite connection pool size |

### SmartToolWrapper Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `token_threshold` | `5000` | Threshold for large data detection |
| `summarization_max_tokens` | `500` | Maximum tokens in summary |
| `tool_expiry_hours` | `24` | Dynamic tool expiration time |
| `max_dynamic_tools` | `1000` | Maximum dynamic tools |

### MemoryMonitor Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `monitoring_interval` | `30` | Monitoring interval in seconds |
| `history_size` | `100` | Number of snapshots to retain |
| `enable_auto_cleanup` | `True` | Enable automatic cleanup |

## Best Practices

### Storage Management
1. Set appropriate size thresholds based on your use case
2. Enable compression for text-heavy data
3. Configure cleanup intervals based on data lifecycle
4. Monitor cache hit rates and adjust cache size

### Memory Optimization
1. Set conservative memory thresholds initially
2. Monitor memory trends to identify patterns
3. Register cleanup callbacks for custom components
4. Use weak references for temporary data

### Performance Tuning
1. Use connection pooling for frequent database access
2. Enable caching for read-heavy workloads
3. Implement lazy loading for large datasets
4. Profile memory usage under load

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check memory monitor thresholds
   - Review cache sizes
   - Enable aggressive cleanup
   - Check for memory leaks in custom tools

2. **Slow Data Retrieval**
   - Enable caching if disabled
   - Increase cache size
   - Check database indexes
   - Monitor connection pool usage

3. **Storage Space Issues**
   - Configure cleanup intervals
   - Set data expiration policies
   - Monitor file storage directory
   - Implement data archival

4. **Compression Errors**
   - Verify data serialization
   - Check available disk space
   - Monitor compression ratios
   - Handle binary data separately

## Performance Metrics

### Storage Metrics
- Cache hit/miss ratio
- Average retrieval time
- Compression ratio
- Storage distribution by tier

### Memory Metrics
- Peak memory usage
- Average memory usage
- Cleanup frequency
- GC trigger count

### System Health
- Database connection pool utilization
- File system usage
- Thread pool statistics
- Error rates

## Extension Points

1. **Custom Storage Backends**: Implement alternative storage systems
2. **Summarization Strategies**: Add domain-specific summarizers
3. **Cleanup Policies**: Define custom cleanup strategies
4. **Monitoring Plugins**: Add custom monitoring metrics
5. **Compression Algorithms**: Integrate alternative compression