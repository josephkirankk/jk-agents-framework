# Memory Transaction Logging

A simple, file-based memory transaction logging system for troubleshooting memory operations in the JK-Agents Framework.

## Overview

The memory transaction logging system provides detailed logging of memory operations per conversation thread for debugging and troubleshooting purposes. It creates one log file per conversation thread with timestamped JSON entries, making it easy to analyze memory usage patterns and diagnose issues.

## Features

- **Thread-specific logging**: One log file per conversation thread_id
- **JSON format**: Human-readable, structured log entries
- **Zero-impact when disabled**: Minimal performance overhead when logging is disabled
- **Thread-safe**: Safe for concurrent operations
- **Analysis tools**: Built-in tools for log analysis and cleanup
- **Environment-based configuration**: Easy to enable/disable via environment variables

## Architecture

### Core Components

1. **MemoryTransactionLogger**: Core logging class that manages file-based logging
2. **MemoryLoggingConfig**: Configuration management via environment variables
3. **Integration points**: Logging calls integrated into existing memory operations
4. **Analysis tools**: Command-line utilities for log analysis and maintenance

### File Structure

```
memory_logs/
├── README.md                           # Directory documentation
├── memory_thread_123_20250127062245.log  # Thread-specific log files
├── memory_thread_456_20250127062300.log
└── ...
```

### Log Entry Format

Each log entry follows this structure:

```
2025-01-27 06:22:45,123 - {
  "operation": "STORE_CONVERSATION",
  "timestamp": "2025-01-27T06:22:45.123Z",
  "thread_id": "thread_123",
  "user_message_length": 150,
  "assistant_response_length": 500,
  "has_metadata": true
}
```

## Configuration

### Environment Variables

Configure memory logging using these environment variables:

```bash
# Enable memory transaction logging (default: false)
MEMORY_LOGGING_ENABLED=true

# Directory for log files (default: memory_logs)
MEMORY_LOGGING_DIRECTORY=memory_logs
```

### In Application Code

Memory logging is automatically configured when the application starts using the `MemoryLoggingConfig` class, which reads from environment variables.

```python
from app.config import AppConfig

# Configuration is loaded automatically
app_config = AppConfig()
memory_config = app_config.memory_logging
print(f"Logging enabled: {memory_config.enabled}")
```

## Usage

### Enabling Logging

1. Set the environment variable:
   ```bash
   export MEMORY_LOGGING_ENABLED=true
   ```

2. Restart the application

3. Memory operations will now be logged to the `memory_logs` directory

### Logged Operations

The following memory operations are automatically logged:

#### Conversation Store Operations
- `STORE_CONVERSATION`: Storing conversation entries
- `GET_CONVERSATION_HISTORY`: Retrieving conversation history
- `GET_RECENT_CONVERSATIONS`: Retrieving recent conversations
- `COUNT_CONVERSATIONS`: Counting conversations for a thread

#### Context Enhancer Operations
- `GET_CONVERSATION_CONTEXT`: Retrieving formatted conversation context
- `ENHANCE_SYSTEM_MESSAGE`: Enhancing system messages with context
- `STORE_CONVERSATION_ENTRY_VIA_ENHANCER`: Storing entries via enhancer

#### Memory Integration Operations
- `ENHANCE_SYSTEM_MESSAGE_WITH_MEMORY`: System message enhancement
- `STORE_CONVERSATION_MEMORY`: Memory storage operations
- `CLEANUP_OLD_CONVERSATIONS`: Cleanup operations

## Analysis Tools

### Analyze Memory Logs

Use the analysis tool to examine log files for specific threads:

```bash
# Analyze logs for a specific thread
python tools/analyze_memory_logs.py thread_123

# List all available thread IDs
python tools/analyze_memory_logs.py --list

# Show directory statistics
python tools/analyze_memory_logs.py --stats

# Use custom log directory
python tools/analyze_memory_logs.py thread_123 --log-dir custom_logs
```

#### Example Output

```
🔍 Analyzing thread: thread_123
📁 Found 2 log files
📂 Log directory: /path/to/memory_logs

============================================================
📊 OPERATION SUMMARY
============================================================
STORE_CONVERSATION                      15 ( 45.5%)
GET_RECENT_CONVERSATIONS               12 ( 36.4%)
ENHANCE_SYSTEM_MESSAGE                  6 ( 18.2%)

📈 Total operations: 33

============================================================
⏰ RECENT TIMELINE (Last 15 operations)
============================================================
14:22:45 - STORE_CONVERSATION              (memory_thread_123_20250127142200.log)
14:23:01 - GET_RECENT_CONVERSATIONS        (memory_thread_123_20250127142200.log)
14:23:02 - ENHANCE_SYSTEM_MESSAGE          (memory_thread_123_20250127142200.log)
...

============================================================
🔍 OPERATION DETAILS
============================================================

STORE_CONVERSATION (15 occurrences):
--------------------------------------------------
  📝 Avg user message length: 87 chars
  🤖 Avg assistant response length: 423 chars
  📋 Entries with metadata: 8/15
```

### Cleanup Memory Logs

Manage log files and disk usage:

```bash
# Remove files older than 7 days
python tools/cleanup_memory_logs.py --days 7

# Preview what would be deleted (dry run)
python tools/cleanup_memory_logs.py --days 7 --dry-run

# Analyze disk usage
python tools/cleanup_memory_logs.py --analyze

# List files by thread
python tools/cleanup_memory_logs.py --list-threads --show-sizes
```

#### Example Cleanup Output

```
🗂️  Found 25 files to remove
💾 Total space to free: 2.3 MB

🗑️  Removed: memory_thread_123_20250120142200.log (157.2 KB)
🗑️  Removed: memory_thread_456_20250120143000.log (89.4 KB)
...

✅ CLEANUP COMPLETE
   Files removed: 25
   Space freed: 2.3 MB

📊 CURRENT STATUS
   Files remaining: 12
   Directory size: 1.1 MB
```

## Manual Log Analysis

### Using Standard Unix Tools

Since log files use a simple text format with JSON, you can use standard tools:

```bash
# View recent log entries for a thread
tail -f memory_logs/memory_thread_123_*.log

# Search for specific operations
grep "STORE_CONVERSATION" memory_logs/memory_thread_123_*.log

# Count operations by type
grep -o '"operation": "[^"]*"' memory_logs/memory_thread_123_*.log | sort | uniq -c

# Extract timestamps
grep -o '"timestamp": "[^"]*"' memory_logs/memory_thread_123_*.log
```

### Processing with jq

Use `jq` for advanced JSON processing:

```bash
# Extract operation types
cat memory_logs/memory_thread_123_*.log | grep ' - {' | sed 's/.*- //' | jq -r '.operation' | sort | uniq -c

# Filter operations by time
cat memory_logs/memory_thread_123_*.log | grep ' - {' | sed 's/.*- //' | jq 'select(.timestamp > "2025-01-27T14:00:00")'

# Calculate average message lengths
cat memory_logs/memory_thread_123_*.log | grep ' - {' | sed 's/.*- //' | jq -s 'map(select(.user_message_length)) | [.[].user_message_length] | add / length'
```

## Performance Considerations

### When Disabled

When `MEMORY_LOGGING_ENABLED=false`, the logging system has minimal impact:

- Function calls return immediately after checking the enabled flag
- No file I/O operations are performed
- No JSON serialization occurs
- Memory overhead is negligible

### When Enabled

Performance impact is minimal but measurable:

- File I/O is performed asynchronously where possible
- JSON serialization uses standard library (efficient)
- Log files are buffered by the OS
- Thread-safe operations use efficient locking

### Best Practices

1. **Enable only when needed**: Use for development/debugging, not production
2. **Monitor disk space**: Set up regular cleanup using the provided tools
3. **Use appropriate retention**: Keep logs for 7-30 days depending on needs
4. **Thread-specific analysis**: Focus analysis on specific problematic threads

## Error Handling

The logging system is designed to never break the main application:

- All logging operations are wrapped in try-catch blocks
- Failures are logged to the standard application log
- Main functionality continues if logging fails
- Graceful degradation when disk space is low

### Common Issues and Solutions

1. **Permission denied**: Ensure the application has write access to the log directory
2. **Disk full**: Set up regular cleanup or reduce retention period
3. **High volume**: Consider filtering which operations to log
4. **File locks**: The system handles concurrent access safely

## Integration Points

### Adding Custom Logging

To add logging to new memory operations:

```python
from app.memory.transaction_logger import get_memory_logger

def my_memory_operation(thread_id: str, data: dict):
    # Log the operation
    try:
        memory_logger = get_memory_logger()
        memory_logger.log_transaction(thread_id, 'MY_CUSTOM_OPERATION', {
            'data_size': len(str(data)),
            'operation_type': 'custom',
            'custom_field': 'custom_value'
        })
    except Exception as e:
        logger.warning(f"Failed to log MY_CUSTOM_OPERATION for thread {thread_id}: {e}")
    
    # Main operation logic here
    return perform_operation(data)
```

### Extending Analysis Tools

The analysis tools can be extended to support custom operations:

1. Add operation-specific parsing in `analyze_memory_logs.py`
2. Create custom analysis functions for your operation types
3. Add new command-line options for specific analysis needs

## Testing

### Running Tests

```bash
# Run all memory logging tests
python -m pytest tests/test_memory_transaction_logging.py -v

# Run specific test class
python -m pytest tests/test_memory_transaction_logging.py::TestMemoryTransactionLogger -v

# Run with coverage
python -m pytest tests/test_memory_transaction_logging.py --cov=app.memory.transaction_logger
```

### Test Coverage

The test suite covers:

- Core logger functionality
- Configuration management
- Thread safety
- Error handling
- Integration with memory operations
- Log file format and structure
- Performance characteristics

## Troubleshooting

### Enable Debug Logging

For detailed logging system diagnostics:

```python
import logging
logging.getLogger('app.memory.transaction_logger').setLevel(logging.DEBUG)
```

### Common Debug Steps

1. **Verify configuration**:
   ```python
   from app.memory.transaction_logger import get_memory_logger
   logger = get_memory_logger()
   print(f"Enabled: {logger.enabled}")
   print(f"Directory: {logger.log_directory}")
   ```

2. **Check file permissions**:
   ```bash
   ls -la memory_logs/
   ```

3. **Monitor disk usage**:
   ```bash
   python tools/cleanup_memory_logs.py --analyze
   ```

4. **Verify log format**:
   ```bash
   tail memory_logs/memory_*.log | head -5
   ```

## Security Considerations

- Log files may contain sensitive conversation data
- Ensure appropriate file permissions on the log directory
- Consider log rotation and secure deletion for sensitive environments
- Monitor access to log files in production environments

## Migration and Upgrades

### From Previous Versions

If upgrading from a version without memory logging:

1. Add environment variables to your deployment
2. Create the log directory with appropriate permissions
3. Test with `MEMORY_LOGGING_ENABLED=false` first
4. Enable gradually in non-production environments

### Backup and Recovery

- Log files are independent and can be backed up separately
- No database changes are required
- Configuration is environment-variable based (easy to version control)
- Tools are stateless and can be run on copied log files

## FAQ

**Q: Does logging affect performance?**
A: When disabled (default), impact is negligible. When enabled, there's minimal I/O overhead but main operations are not blocked.

**Q: How much disk space do logs use?**
A: Depends on conversation volume. Typical entry is 200-500 bytes. Use the analysis tools to monitor usage.

**Q: Can I log custom operations?**
A: Yes, use the `get_memory_logger().log_transaction()` method in your code.

**Q: Are logs rotated automatically?**
A: No, use the cleanup utility (`cleanup_memory_logs.py`) for log management.

**Q: Is the system thread-safe?**
A: Yes, the logger uses proper locking and is safe for concurrent use.

**Q: Can I parse logs with external tools?**
A: Yes, logs use standard JSON format and can be processed with any JSON tool.