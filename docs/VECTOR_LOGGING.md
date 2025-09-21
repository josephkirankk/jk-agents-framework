# VectorDB Wrapper - Vector Operations Logging

This document describes the comprehensive logging functionality for VectorDB operations, including search and upsert operations with detailed performance metrics and cross-platform compatibility.

## Overview

The VectorDB wrapper now includes comprehensive logging for all vector operations. Each operation is logged with detailed information including:

- Operation type and timing
- Input parameters
- Results or error details
- Performance metrics
- Cross-platform compatible file handling

## Log File Structure

### Directory Structure
```
vectordb_wrapper/
├── vectorlogs/
│   ├── vector_20250921110907.json
│   ├── vector_20250921111205.json
│   └── ...
└── [other vectordb_wrapper files]
```

### Log File Naming
Log files use the format: `vector_<YYYYMMDDHHMMSS>.json`

Where the timestamp represents when the operation was initiated.

## Log Entry Format

Each log entry is a JSON object on a single line with the following structure:

```json
{
  "timestamp": "2025-09-21T11:09:07.123456",
  "operation_type": "search|upsert|search_get|upsert_json_batch",
  "operation_start": "2025-09-21T11:09:07.123456",
  "operation_end": "2025-09-21T11:09:07.234567",
  "execution_time_ms": 111.111,
  "input_parameters": {...},
  "success": true|false,
  "result": {...},
  "error": "error message if any",
  "performance_metrics": {...}
}
```

### Field Descriptions

- **timestamp**: When the log entry was created
- **operation_type**: Type of operation performed
- **operation_start**: When the operation started
- **operation_end**: When the operation completed
- **execution_time_ms**: Total execution time in milliseconds
- **input_parameters**: Sanitized input parameters
- **success**: Whether the operation succeeded
- **result**: Operation results (if successful)
- **error**: Error message (if failed)
- **performance_metrics**: Additional performance data

## Operation Types

### Search Operations

#### search
Standard POST-based search operations.

**Input Parameters:**
```json
{
  "query": "hydraulic pump failure",
  "top_n": 5,
  "min_score": 0.7
}
```

**Result:**
```json
{
  "query": "hydraulic pump failure",
  "results_count": 3,
  "results": [
    {
      "defect_code": "PLG.HYD.CYLINDER.FAIL",
      "score": 0.870251,
      "subsystem": "CYL"
    }
  ]
}
```

**Performance Metrics:**
```json
{
  "api_response_time_ms": 2408.39,
  "results_count": 3,
  "min_score": 0.6,
  "top_n": 3
}
```

#### search_get
GET-based search operations.

Similar to search but includes `"method": "GET"` in performance metrics.

### Upsert Operations

#### upsert
Single defect upsert operations.

**Input Parameters:**
```json
{
  "defect_code": "TEST.001",
  "defect_text": "Test defect description",
  "subsystem": "TST",
  "severity": "Low",
  "symptoms": ["test symptom"],
  "tags": ["test"]
}
```

**Result:**
```json
{
  "defect_code": "TEST.001",
  "operation": "created",
  "success": true,
  "message": "Defect created successfully"
}
```

**Performance Metrics:**
```json
{
  "api_response_time_ms": 1036.98,
  "defect_code": "TEST.001",
  "subsystem": "TST",
  "operation_type": "created"
}
```

#### upsert_json_batch
Batch upsert operations from JSON.

**Input Parameters:**
```json
{
  "total_defects": 2,
  "json_size_chars": 917
}
```

**Result:**
```json
{
  "total_defects": 2,
  "successful_upserts": 2,
  "failed_upserts": 0,
  "success_rate": 1.0
}
```

**Performance Metrics:**
```json
{
  "total_defects": 2,
  "successful_upserts": 2,
  "failed_upserts": 0,
  "success_rate_percent": 100.0
}
```

## Configuration

### Environment Variables

- **VECTORDB_VECTOR_LOGGING**: Enable/disable vector logging (default: "true")
  ```bash
  export VECTORDB_VECTOR_LOGGING=true
  ```

### Programmatic Configuration

```python
from vectordb_wrapper.vector_logger import VectorLogger

# Custom logger with specific directory
logger = VectorLogger(base_dir="/custom/log/path", enabled=True)

# Check if logging is enabled
from vectordb_wrapper.vector_logger import get_vector_logger
vector_logger = get_vector_logger()
print(f"Logging enabled: {vector_logger.enabled}")
```

## Cross-Platform Compatibility

The logging system is designed for cross-platform compatibility:

- **File Encoding**: Uses UTF-8 encoding explicitly for Windows compatibility
- **Path Handling**: Uses `pathlib.Path` for cross-platform path operations
- **Directory Creation**: Uses `os.makedirs(exist_ok=True)` for safe directory creation
- **Error Handling**: Graceful fallback if logging fails

## Performance Considerations

- **Lightweight**: Logging operations are designed to be lightweight
- **Non-blocking**: Logging failures don't affect main operations
- **Efficient**: JSON serialization with minimal overhead
- **Sanitization**: Large result sets are truncated for logging efficiency

## Error Handling

The logging system includes comprehensive error handling:

1. **Directory Creation Failures**: Disables logging if directory cannot be created
2. **File Write Failures**: Logs errors to standard logger
3. **JSON Serialization Errors**: Handles serialization failures gracefully
4. **Permission Issues**: Handles file permission errors on Windows/macOS

## Usage Examples

### Basic Usage
The logging is automatic when using VectorDBClient:

```python
from vectordb_wrapper import VectorDBClient, SearchRequest

async with VectorDBClient() as client:
    # This search will be automatically logged
    request = SearchRequest(query="pump failure", top_n=5)
    response = await client.search(request)
```

### Checking Log Files
```python
from pathlib import Path

log_dir = Path("vectordb_wrapper/vectorlogs")
log_files = list(log_dir.glob("vector_*.json"))

# Read latest log file
if log_files:
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    with open(latest_log, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                import json
                entry = json.loads(line.strip())
                print(f"{entry['operation_type']}: {entry['success']}")
```

### Disabling Logging
```bash
# Disable vector logging
export VECTORDB_VECTOR_LOGGING=false
```

## Log Analysis

### Performance Analysis
```python
import json
from pathlib import Path

def analyze_performance():
    log_dir = Path("vectordb_wrapper/vectorlogs")

    for log_file in log_dir.glob("vector_*.json"):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line.strip())
                    operation = entry['operation_type']
                    exec_time = entry['execution_time_ms']
                    success = entry['success']

                    print(f"{operation}: {exec_time:.1f}ms ({'✅' if success else '❌'})")
```

### Error Analysis
```python
def analyze_errors():
    log_dir = Path("vectordb_wrapper/vectorlogs")

    for log_file in log_dir.glob("vector_*.json"):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line.strip())
                    if not entry['success']:
                        print(f"Error in {entry['operation_type']}: {entry.get('error', 'Unknown')}")
```

## Maintenance

### Log Rotation
The system doesn't automatically rotate logs. For production use, consider implementing log rotation:

```python
from pathlib import Path
import time

def cleanup_old_logs(days_to_keep=7):
    log_dir = Path("vectordb_wrapper/vectorlogs")
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

    for log_file in log_dir.glob("vector_*.json"):
        if log_file.stat().st_mtime < cutoff_time:
            log_file.unlink()
            print(f"Deleted old log file: {log_file.name}")
```

## Troubleshooting

### Common Issues

1. **Directory Not Created**: Check file permissions in the vectordb_wrapper directory
2. **Logging Disabled**: Verify VECTORDB_VECTOR_LOGGING environment variable
3. **File Encoding Issues**: The system uses UTF-8 encoding by default
4. **Permission Errors**: Ensure write permissions to the vectorlogs directory

### Debug Information
```python
from vectordb_wrapper.vector_logger import get_vector_logger

logger = get_vector_logger()
print(f"Logging enabled: {logger.enabled}")
print(f"Log directory: {logger.log_dir}")
print(f"Directory exists: {logger.log_dir.exists()}")
```
