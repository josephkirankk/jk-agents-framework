# Memory Logging Enhancements

## Overview

This document describes the enhancements made to the JK-Agents Framework memory logging system to provide complete visibility into conversation memory operations, including the actual message content being processed.

## Problem Statement

Previously, the memory logs only showed metadata such as message lengths and operation types, but not the actual content of messages. This made it difficult to:

- Debug conversation memory operations
- Understand what content was being stored and retrieved
- Verify that conversation context was being properly injected
- Troubleshoot memory-related issues

## Solution Implemented

### 1. Enhanced Memory Logging Configuration

Added comprehensive logging configuration in `app/config.py`:

```python
class MemoryLoggingConfig(BaseModel):
    """Configuration for memory transaction logging."""
    enabled: bool = True
    log_directory: str = "memory_logs"
    include_content: bool = True  # NEW: Control content inclusion
    max_content_length: int = 1000  # NEW: Control content truncation
```

### 2. Content Logging Infrastructure

Enhanced `app/memory/transaction_logger.py` with:

- **Content preparation**: `prepare_content_for_logging()` function that safely handles content inclusion and truncation
- **Configurable content logging**: Respects `include_content` and `max_content_length` settings
- **Truncation tracking**: Logs whether content was truncated for debugging
- **UTF-8 safe truncation**: Handles multi-byte characters properly

### 3. Updated Memory Integration Modules

#### memory_integration.py
- ✅ **Already properly implemented** with content logging for:
  - User messages and assistant responses during storage operations
  - Original and enhanced system messages during context enhancement
  - All metadata when content logging is enabled

#### conversation_store.py
- ✅ **Enhanced** to accept and use `app_config` parameter
- ✅ **Added content logging** for all conversation storage operations
- ✅ **Improved metadata handling** with full content when enabled

#### context_enhancer.py
- ✅ **Enhanced** to accept and use `app_config` parameter
- ✅ **Added content logging** for:
  - Context retrieval operations with actual retrieved content
  - System message enhancement with before/after content
  - Conversation storage operations with full message content

### 4. Default Configuration

Created a comprehensive default `config/agents.yaml` with:

- **Conversation memory enabled** by default
- **Memory logging enabled** with content inclusion
- **Proper configuration structure** for out-of-the-box functionality
- **Complete multi-agent system** with research, analysis, and problem-solving agents

## Features Implemented

### Content Logging
- **Full message content**: Logs actual user messages, assistant responses, and system messages
- **Configurable inclusion**: Can disable content logging via `include_content: false`
- **Content truncation**: Automatically truncates long content to configured limits
- **Truncation tracking**: Logs `truncated: true/false` for debugging

### Metadata Logging
- **Complete metadata**: Logs full metadata objects when content logging is enabled
- **Metadata keys only**: When content logging is disabled, logs only metadata keys
- **Operation tracking**: Comprehensive tracking of all memory operations

### Operation Flow Visibility
- **Multi-level logging**: Logs operations from integration layer through store and enhancer
- **Operation chaining**: Track how operations flow through the system
- **Source identification**: Each log entry identifies its source module
- **Timestamp tracking**: Full timestamp information for performance analysis

## Log Output Format

Example log entry with content:

```json
{
  "operation": "STORE_CONVERSATION_MEMORY",
  "timestamp": "2025-09-27T12:44:08.176312",
  "thread_id": "test_thread_123",
  "memory_enabled": true,
  "has_metadata": true,
  "operation_source": "memory_integration",
  "user_message_content_length": 49,
  "user_message_content": "Hello, this is a test message for memory logging.",
  "user_message_truncated": false,
  "assistant_response_content_length": 55,
  "assistant_response_content": "Thank you for testing the memory logging functionality!",
  "assistant_response_truncated": false,
  "metadata": {
    "test": true,
    "agent_name": "test_agent"
  }
}
```

## Configuration Options

### Memory Logging Settings
```yaml
memory_logging:
  enabled: true              # Enable/disable logging
  include_content: true      # Include actual message content
  max_content_length: 1000   # Maximum characters per content field
  log_directory: "memory_logs" # Directory for log files
```

### Conversation Memory Settings
```yaml
conversation_memory:
  enabled: true              # Enable conversation memory
  database_url: null         # Use DATABASE_URL environment variable
  max_conversations: 5       # Number of recent conversations to include
  max_context_length: 2000   # Maximum context length in characters
  prepend_context: false     # Prepend vs append context to system message
  cleanup_days: 30          # Days to keep conversation history
  pool_size: 10             # Database connection pool size
```

## Testing

Implemented comprehensive test script (`test_memory_logging.py`) that:

- ✅ Verifies configuration loading
- ✅ Tests conversation storage with content logging
- ✅ Tests system message enhancement with content logging
- ✅ Validates log file creation and content inclusion
- ✅ Checks for proper content truncation handling
- ✅ Demonstrates full memory operation visibility

## Benefits

### For Debugging
- **Complete visibility**: See exactly what content is being processed
- **Operation tracing**: Track operations through the entire memory system
- **Content verification**: Verify that context injection is working correctly
- **Performance monitoring**: Analyze operation timing and content sizes

### for Development
- **Easier troubleshooting**: Quickly identify issues with memory operations
- **Content validation**: Verify that content truncation is working properly
- **Integration testing**: Validate memory system integration with agents
- **Configuration testing**: Ensure memory settings are working as expected

### For Production
- **Configurable privacy**: Can disable content logging for sensitive data
- **Performance monitoring**: Track memory operation performance
- **Issue diagnosis**: Detailed logs for troubleshooting production issues
- **Audit trail**: Complete record of memory operations

## Migration Notes

### Existing Installations
1. **Update configuration**: Add `memory_logging` section to your config file
2. **Set environment variables**: Ensure `DATABASE_URL` is set for PostgreSQL
3. **Check log directory**: Logs will be created in `memory_logs/` by default
4. **Review content settings**: Set `include_content: false` for sensitive environments

### New Installations
- **Use default config**: The new `config/agents.yaml` provides complete setup
- **Set DATABASE_URL**: Point to your PostgreSQL database
- **Configure content logging**: Adjust `max_content_length` as needed

## Security Considerations

- **Content sensitivity**: Disable `include_content` for sensitive data environments
- **Log rotation**: Implement log rotation for production environments
- **Access control**: Secure access to memory log files
- **Data retention**: Configure appropriate `cleanup_days` settings

## Future Enhancements

Potential future improvements:
- **Log rotation**: Automatic log file rotation and cleanup
- **Performance metrics**: Built-in performance monitoring and alerting
- **Content filtering**: Selective content logging based on content type
- **Structured search**: Enhanced log search and analysis capabilities