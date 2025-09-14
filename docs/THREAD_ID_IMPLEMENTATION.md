# Thread ID Implementation Guide

## Overview

The JK-Agents API implements comprehensive thread ID management to enable conversation continuity and memory isolation across multi-agent interactions. Every API response includes a `thread_id` field that can be used in subsequent requests to maintain conversation context.

## Key Features

✅ **Automatic Thread ID Generation**: System generates unique thread IDs when none provided  
✅ **Thread ID Validation**: Invalid thread IDs are rejected and new ones generated  
✅ **Conversation Continuity**: Same thread ID maintains conversation history  
✅ **Memory Isolation**: Different thread IDs have completely separate memories  
✅ **Cross-Endpoint Support**: Thread IDs work across all API endpoints  
✅ **Custom Thread IDs**: Support for user-provided thread IDs  
✅ **Hierarchical Threading**: Internal thread management for multi-agent coordination  

## API Endpoints Supporting Thread ID

All major endpoints support the optional `thread_id` parameter and return `thread_id` in responses:

- `POST /query` - Multi-agent query endpoint
- `POST /query/form` - Form-based query endpoint  
- `POST /worker` - Direct agent execution endpoint
- `POST /worker/upload` - Agent execution with file uploads

## Thread ID Format

### Auto-Generated Format
```
thread-{uuid}
Example: thread-f882a9c0-8da9-455a-afd8-27769d6678f3
```

### Custom Format Requirements
- Length: 5-100 characters
- Allowed characters: alphanumeric, hyphens (-), underscores (_)
- Pattern: `^[a-zA-Z0-9_-]{5,100}$`

### Valid Custom Examples
```
my-session-2024
user_123_conversation
restaurant-search-001
```

## Implementation Details

### Thread Manager Module
Located in `app/thread_manager.py`, provides:

- `get_or_create_thread_id(provided_thread_id)` - Main thread ID management
- `generate_unique_thread_id()` - Creates UUID-based thread IDs
- `validate_thread_id(thread_id)` - Validates thread ID format
- `create_supervisor_thread_id(base_thread_id)` - Creates supervisor-specific thread ID
- `create_step_thread_id(base_thread_id, step_id)` - Creates step-specific thread ID

### Thread ID Hierarchy

The system creates hierarchical thread IDs for internal coordination:

```
Base Thread:       thread-abc123
Supervisor Thread: thread-abc123-supervisor  
Step 1 Thread:     thread-abc123-step-1
Step 2 Thread:     thread-abc123-step-2
```

This ensures proper memory isolation between different components while maintaining overall conversation context.

### API Response Structure

All endpoints return thread_id in the response:

```json
{
  "success": true,
  "response": "Agent response text...",
  "thread_id": "thread-f882a9c0-8da9-455a-afd8-27769d6678f3",
  "metadata": {...}
}
```

Even error responses include thread_id when available:

```json
{
  "success": false,
  "response": "",
  "error": "Error message",
  "thread_id": "thread-f882a9c0-8da9-455a-afd8-27769d6678f3"
}
```

## Usage Examples

### 1. Start New Conversation
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, I need help with restaurants",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml"
  }'
```

Response includes generated thread_id:
```json
{
  "success": true,
  "response": "I'd be happy to help you find restaurants...",
  "thread_id": "thread-f882a9c0-8da9-455a-afd8-27769d6678f3"
}
```

### 2. Continue Conversation
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Can you remember what I asked about?",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "thread-f882a9c0-8da9-455a-afd8-27769d6678f3"
  }'
```

### 3. Direct Agent with Thread ID
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "restaurants_agent",
    "input": "Based on our previous discussion, find Italian restaurants",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "thread-f882a9c0-8da9-455a-afd8-27769d6678f3"
  }'
```

### 4. Custom Thread ID
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Start new restaurant search session",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "my-restaurant-session-2024"
  }'
```

## Code Changes Made

### 1. Updated `/worker/upload` Endpoint
- Added `thread_id` parameter to form data
- Updated `run_direct_agent_with_files` function signature
- Added thread ID handling and response inclusion

### 2. Enhanced Thread ID Management
- All endpoints now consistently return thread_id
- Error responses include thread_id when available
- Proper thread ID validation and generation

### 3. Response Model Updates
- All response models include required `thread_id` field
- Consistent thread ID handling across all endpoints

## Testing

### Automated Test Scripts

1. **PowerShell Script**: `test_thread_continuity.ps1`
   ```powershell
   .\test_thread_continuity.ps1
   ```

2. **Bash Script**: `test_thread_continuity.sh`
   ```bash
   chmod +x test_thread_continuity.sh
   ./test_thread_continuity.sh
   ```

3. **Windows Batch**: `test_thread_continuity.bat`
   ```cmd
   test_thread_continuity.bat
   ```

### Manual Testing

See `curl_commands_thread_demo.md` for individual curl commands to test thread ID functionality.

## Benefits

1. **Conversation Continuity**: Agents can reference previous interactions within the same thread
2. **Session Management**: Applications can manage multiple user sessions with custom thread IDs
3. **Memory Isolation**: Different conversations are completely isolated from each other
4. **Debugging**: Thread IDs help track conversation flows in logs
5. **Scalability**: Proper thread management enables concurrent user sessions

## Best Practices

1. **Always Use Thread IDs**: Include thread_id in follow-up requests for conversation continuity
2. **Store Thread IDs**: Client applications should store and manage thread IDs per user session
3. **Custom Thread IDs**: Use meaningful custom thread IDs for session management
4. **Error Handling**: Handle cases where thread IDs might be regenerated due to validation failures
5. **Thread Lifecycle**: Consider thread cleanup strategies for long-running applications

## Troubleshooting

### Thread ID Not Working
- Verify thread_id format matches validation pattern
- Check that same thread_id is used across related requests
- Ensure server has proper memory persistence configured

### Memory Not Maintained
- Confirm thread_id is identical across requests (case-sensitive)
- Check server logs for thread ID validation messages
- Verify LangGraph MemorySaver is properly configured

### Invalid Thread ID
- System will automatically generate new thread ID
- Check server logs for validation warnings
- Use valid characters: alphanumeric, hyphens, underscores only
