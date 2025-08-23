# Internal LLM Logging System

## Overview

The Internal LLM Logging System provides comprehensive logging for all LLM API interactions across multiple providers (OpenAI, Azure AI, Google Gemini, etc.). It captures raw requests, responses, token usage, and error information in structured JSON format for analysis and debugging.

## Features

- **Multi-Provider Support**: Works with OpenAI, Azure OpenAI, Google Gemini, Anthropic, and other LLM providers
- **Structured JSON Logging**: All logs are in structured JSON format for easy parsing and analysis
- **Thread-Safe Operations**: Safe for use in multi-threaded environments
- **Log Rotation and Compression**: Automatic log rotation with optional gzip compression
- **Sensitive Data Masking**: Configurable masking of API keys, tokens, and other sensitive information
- **Request/Response Correlation**: Each request-response pair is correlated with unique IDs
- **Performance Metrics**: Tracks response times and token usage
- **Configurable Logging Levels**: Support for disabled, error, info, and debug levels
- **Agent Context Tracking**: Associates logs with specific agents and user inputs

## Architecture

### Core Components

1. **InternalLogger**: Main logging engine that handles file operations, rotation, and formatting
2. **HTTP Interceptors**: Capture HTTP requests/responses from various LLM providers
3. **Configuration Manager**: Handles configuration from environment variables and files
4. **Integration Layer**: Seamlessly integrates with existing agent system

### Log File Structure

Log files are named `internal_logs_<YYYYMMDDHHMMSS>.log` and stored in the configured logs directory.

Each log entry is a single JSON line with the following structure:

```json
{
  "log_type": "llm_request|llm_response|agent_execution_start|agent_execution_end",
  "timestamp": "2025-01-23T20:32:56.123456Z",
  "request_id": "uuid-string",
  "correlation_id": "uuid-string",
  "provider": "openai|azure_openai|google_gemini|anthropic|unknown",
  "model": "gpt-4|gemini-2.0-flash|claude-sonnet-4",
  "agent_name": "agent_name",
  "user_input": "user query text",
  // ... additional fields based on log_type
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INTERNAL_LOGGING_ENABLED` | `true` | Enable/disable internal logging |
| `INTERNAL_LOGGING_LEVEL` | `info` | Log level (disabled, error, info, debug) |
| `INTERNAL_LOGGING_DIR` | `logs` | Directory for log files |
| `INTERNAL_LOGGING_MAX_FILE_SIZE_MB` | `100` | Maximum file size in MB |
| `INTERNAL_LOGGING_MAX_FILES` | `10` | Maximum number of files to keep |
| `INTERNAL_LOGGING_COMPRESS` | `true` | Compress old files with gzip |
| `INTERNAL_LOGGING_INCLUDE_REQUEST_HEADERS` | `true` | Include request headers |
| `INTERNAL_LOGGING_INCLUDE_RESPONSE_HEADERS` | `true` | Include response headers |
| `INTERNAL_LOGGING_INCLUDE_PAYLOAD` | `true` | Include payload content |
| `INTERNAL_LOGGING_MASK_SENSITIVE` | `true` | Mask sensitive data |
| `INTERNAL_LOGGING_SENSITIVE_KEYS` | `api-key,authorization,...` | Comma-separated sensitive keys |

### Configuration File

You can also configure the system using a JSON file. See `config/internal_logging_template.json` for the complete structure.

### Runtime Configuration

Configuration can be updated at runtime using the configuration manager:

```python
from app.internal_logging_config import update_internal_logging_config

# Update configuration at runtime
update_internal_logging_config(
    log_level="debug",
    max_file_size_mb=50
)
```

## Usage

### Automatic Integration

The system automatically integrates with the existing agent system. No code changes are required for basic logging.

### Manual Context Setting

For custom integrations, you can set agent context manually:

```python
from app.internal_logging_integration import agent_logging_context

with agent_logging_context("my_agent", "user query"):
    # Your agent logic here
    # All LLM calls within this context will be logged
    pass
```

### Direct Logging

For advanced use cases, you can log interactions directly:

```python
from app.internal_logger import get_internal_logger, LLMProvider

logger = get_internal_logger()

with logger.log_llm_interaction(
    provider=LLMProvider.OPENAI,
    model="gpt-4",
    agent_name="my_agent",
    user_input="user query"
) as ctx:
    # Log request
    ctx.log_request(
        endpoint="https://api.openai.com/v1/chat/completions",
        method="POST",
        headers={"Authorization": "Bearer ***"},
        payload={"model": "gpt-4", "messages": [...]}
    )
    
    # Make API call here
    
    # Log response
    ctx.log_response(
        status_code=200,
        headers={"Content-Type": "application/json"},
        payload={"choices": [...]},
        token_usage={"prompt_tokens": 10, "completion_tokens": 5}
    )
```

## API Endpoints

### Get Logging Statistics

```http
GET /internal-logging/stats
```

Returns statistics about the logging system:

```json
{
  "success": true,
  "stats": {
    "enabled": true,
    "log_level": "info",
    "current_log_file": "/path/to/current.log",
    "total_log_files": 5,
    "total_size_bytes": 1048576,
    "total_size_mb": 1.0,
    "log_directory": "/path/to/logs",
    "config": {
      "enabled": true,
      "log_level": "info",
      "max_file_size_mb": 100,
      "max_files": 10,
      "compress_old_files": true,
      "mask_sensitive_data": true
    }
  }
}
```

## Log Analysis

### Parsing Log Files

Log files contain one JSON object per line. You can parse them using any JSON parser:

```python
import json

with open('internal_logs_20250123203256.log', 'r') as f:
    for line in f:
        log_entry = json.loads(line)
        print(f"Type: {log_entry['log_type']}, Time: {log_entry['timestamp']}")
```

### Common Queries

#### Find all requests for a specific agent:
```bash
grep '"agent_name":"my_agent"' internal_logs_*.log
```

#### Find all errors:
```bash
grep '"status_code":[45][0-9][0-9]' internal_logs_*.log
```

#### Calculate token usage:
```bash
grep '"token_usage"' internal_logs_*.log | jq '.token_usage.total_tokens' | awk '{sum+=$1} END {print sum}'
```

## Security Considerations

### Sensitive Data Masking

The system automatically masks sensitive data based on configurable key patterns. By default, it masks:
- API keys
- Authorization headers
- Tokens
- Passwords
- Other sensitive fields

### Log File Security

- Log files contain sensitive information even with masking enabled
- Ensure proper file permissions on the logs directory
- Consider encrypting log files at rest
- Implement proper log retention policies

### Network Security

- The system intercepts HTTP traffic to log requests/responses
- Ensure the logging system itself doesn't introduce security vulnerabilities
- Monitor for any performance impact from logging

## Performance Considerations

### Impact on Response Times

The logging system is designed to have minimal impact on response times:
- Asynchronous logging where possible
- Efficient JSON serialization
- Configurable payload inclusion

### Disk Usage

- Log files can grow large with high API usage
- Automatic rotation and compression help manage disk usage
- Monitor disk space in the logs directory
- Configure appropriate retention policies

### Memory Usage

- The system uses minimal memory for buffering
- Thread-safe operations may have slight overhead
- Consider disabling detailed logging in high-throughput scenarios

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check if logging is enabled and log level is appropriate
2. **Permission errors**: Ensure write permissions on the logs directory
3. **Large log files**: Reduce max_file_size_mb or disable payload logging
4. **Performance issues**: Consider reducing log level or disabling in production

### Debug Mode

Enable debug mode for detailed logging:

```bash
export INTERNAL_LOGGING_LEVEL=debug
```

### Log File Validation

Validate log file format:

```bash
cat internal_logs_*.log | jq empty
```

## Integration with Existing Systems

### Compatibility

The internal logging system is designed to be compatible with:
- Existing agent logging (agentlog_*.log files)
- Direct agent logging (direct_agentlog_*.log files)
- All LLM providers currently supported
- Both synchronous and asynchronous operations

### Migration

No migration is required. The system works alongside existing logging without conflicts.

## Future Enhancements

Planned improvements include:
- Real-time log streaming
- Integration with monitoring systems
- Advanced analytics and reporting
- Custom log formatters
- Database storage options
