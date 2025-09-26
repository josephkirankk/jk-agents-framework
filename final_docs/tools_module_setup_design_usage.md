# Tools Module Documentation

## Module Overview

The `tools` module provides specialized utility tools for the JK-Agents Framework, including Python function execution, memory performance testing, and large data handling tools. These tools can be integrated with agents to extend their capabilities.

## Setup Instructions

### Prerequisites

```bash
pip install psutil>=5.9.0
pip install numpy>=1.24.0  # For data testing tools
pip install pandas>=2.0.0  # For data manipulation
```

### Installation

```bash
# From project root
cd jk-agents-framework
python -m tools.python_function_tools  # Test Python tools
```

## Design Overview

### Architecture

```
┌────────────────────────────────────────────┐
│              Tools Module                    │
├──────────────────────────────────────────────┤
│  Components:                                 │
│  • Python Function Tools                    │
│  • Memory Performance Tools                 │
│  • Large Data Test Tools                    │
└──────────────────────────────────────────────┘
```

### Core Components

#### 1. **Python Function Tools** (`python_function_tools.py`)

Provides safe Python code execution and function management:

**Features:**
- Safe code execution in sandboxed environment
- Dynamic function loading and registration
- Type validation and error handling
- Async function support
- Result caching

**Key Functions:**
- `execute_python_code()`: Execute arbitrary Python code safely
- `load_function_from_module()`: Dynamically load Python functions
- `create_tool_from_function()`: Convert Python functions to LangChain tools
- `validate_function_signature()`: Ensure function compatibility

#### 2. **Memory Performance Tools** (`memory_performance_tools.py`)

Tools for testing and benchmarking memory subsystem performance:

**Features:**
- Memory usage profiling
- Performance benchmarking
- Cache hit rate testing
- Load testing utilities
- Memory leak detection

**Key Functions:**
- `benchmark_memory_operations()`: Test memory operation performance
- `profile_memory_usage()`: Track memory consumption over time
- `stress_test_cache()`: Test cache under load
- `detect_memory_leaks()`: Identify potential memory leaks

#### 3. **Large Data Test Tools** (`large_data_test_tools.py`)

Utilities for testing large data handling capabilities:

**Features:**
- Large dataset generation
- Data processing simulation
- Streaming data tests
- Compression testing
- I/O performance testing

**Key Functions:**
- `generate_large_dataset()`: Create test datasets of various sizes
- `test_data_streaming()`: Test streaming data processing
- `benchmark_compression()`: Test compression ratios and performance
- `simulate_data_pipeline()`: Simulate real-world data processing

## Usage Guide

### Basic Usage: Python Function Tools

```python
from tools.python_function_tools import (
    execute_python_code,
    create_tool_from_function,
    load_function_from_module
)

# Execute Python code safely
code = """
def calculate_sum(numbers):
    return sum(numbers)
    
result = calculate_sum([1, 2, 3, 4, 5])
"""
output = execute_python_code(code)
print(output["result"])  # 15

# Create tool from function
def analyze_text(text: str) -> dict:
    """Analyze text and return statistics."""
    return {
        "length": len(text),
        "words": len(text.split()),
        "lines": len(text.splitlines())
    }

tool = create_tool_from_function(analyze_text)
result = tool.invoke({"text": "Hello world!"})

# Load function from module
func = load_function_from_module("math", "sqrt")
result = func(16)  # 4.0
```

### Advanced Usage: Memory Performance Tools

```python
from tools.memory_performance_tools import (
    benchmark_memory_operations,
    profile_memory_usage,
    stress_test_cache
)

# Benchmark memory operations
results = benchmark_memory_operations(
    operations=["store", "retrieve", "delete"],
    iterations=10000,
    data_size_mb=1
)
print(f"Average latency: {results['avg_latency']:.3f}ms")
print(f"Throughput: {results['ops_per_second']:.0f} ops/s")

# Profile memory usage
profile = profile_memory_usage(
    duration_seconds=60,
    interval_seconds=1
)
print(f"Peak memory: {profile['peak_memory_mb']:.2f} MB")
print(f"Average memory: {profile['avg_memory_mb']:.2f} MB")

# Stress test cache
stress_results = stress_test_cache(
    cache_size=10000,
    num_operations=100000,
    num_threads=10
)
print(f"Cache hit rate: {stress_results['hit_rate']:.2%}")
```

### Large Data Testing

```python
from tools.large_data_test_tools import (
    generate_large_dataset,
    test_data_streaming,
    benchmark_compression
)

# Generate test dataset
dataset = generate_large_dataset(
    size_mb=100,
    data_type="json",
    structure="nested"
)

# Test streaming processing
stream_results = test_data_streaming(
    dataset,
    chunk_size=1024,
    processing_func=lambda x: x.upper()
)
print(f"Processing rate: {stream_results['mb_per_second']:.2f} MB/s")

# Benchmark compression
compression_results = benchmark_compression(
    data=dataset,
    algorithms=["gzip", "bz2", "lz4"],
    levels=[1, 5, 9]
)
for algo, stats in compression_results.items():
    print(f"{algo}: ratio={stats['ratio']:.2f}, time={stats['time']:.3f}s")
```

### Integration with Agents

```python
from app.agent_builder import build_react_agent
from tools.python_function_tools import create_tool_from_function

# Define custom tool
def data_processor(data: list, operation: str) -> dict:
    """Process data with specified operation."""
    if operation == "sum":
        return {"result": sum(data)}
    elif operation == "average":
        return {"result": sum(data) / len(data)}
    elif operation == "max":
        return {"result": max(data)}
    else:
        return {"error": "Unknown operation"}

# Create tool
processing_tool = create_tool_from_function(data_processor)

# Configure agent with tool
agent_config = {
    "name": "data_analyst",
    "python_tools": {
        "processor": {
            "module_path": "tools.custom_tools",
            "function_name": "data_processor"
        }
    }
}

# Agent can now use the data processing tool
```

## Key Features

### 1. **Safe Execution**
- Sandboxed Python code execution
- Resource limits and timeouts
- Error isolation and handling
- Input/output validation

### 2. **Performance Testing**
- Comprehensive benchmarking suite
- Multi-threaded load testing
- Memory profiling and analysis
- Latency and throughput measurement

### 3. **Data Generation**
- Various data types and structures
- Configurable size and complexity
- Realistic data patterns
- Streaming data simulation

### 4. **Tool Integration**
- LangChain tool compatibility
- Automatic type conversion
- Documentation generation
- Error handling wrapper

## Configuration Options

### Python Function Tools

| Parameter | Default | Description |
|-----------|---------|-------------|
| `timeout` | `30` | Execution timeout (seconds) |
| `max_memory_mb` | `512` | Memory limit for execution |
| `safe_mode` | `True` | Enable sandboxed execution |
| `cache_results` | `True` | Cache function results |

### Memory Performance Tools

| Parameter | Default | Description |
|-----------|---------|-------------|
| `warmup_iterations` | `100` | Warmup before benchmarking |
| `sample_interval` | `0.1` | Sampling interval (seconds) |
| `enable_profiling` | `True` | Enable detailed profiling |

### Large Data Test Tools

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_file_size_mb` | `1000` | Maximum test file size |
| `chunk_size_kb` | `64` | Default chunk size |
| `compression_level` | `6` | Default compression level |

## Best Practices

### Tool Development
1. Always validate inputs and outputs
2. Implement proper error handling
3. Add comprehensive logging
4. Document function parameters clearly
5. Use type hints for better integration

### Performance Testing
1. Run warmup iterations before benchmarking
2. Test with realistic data sizes
3. Monitor system resources during tests
4. Run multiple iterations for accuracy

### Data Testing
1. Start with small datasets and scale up
2. Test edge cases and error conditions
3. Monitor memory usage during processing
4. Clean up temporary files after tests

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Verify module path is correct
   - Check PYTHONPATH configuration
   - Ensure dependencies are installed

2. **Execution Timeout**
   - Increase timeout value
   - Optimize code for performance
   - Check for infinite loops

3. **Memory Errors**
   - Increase memory limits
   - Process data in chunks
   - Use lazy loading techniques

4. **Tool Registration Fails**
   - Verify function signature
   - Check type annotations
   - Ensure docstring is present

## Extension Points

1. **Custom Tools**: Add new tool implementations
2. **Test Scenarios**: Create domain-specific tests
3. **Benchmarks**: Add custom benchmark suites
4. **Data Generators**: Implement custom data generation
5. **Validators**: Add input/output validators