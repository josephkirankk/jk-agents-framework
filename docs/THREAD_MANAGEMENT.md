# Thread ID Management

This document explains the thread ID management system implemented in the JK-Agents framework to enable proper conversation continuity and isolation.

## Overview

The thread ID management system allows:
- **Conversation Continuity**: Continue conversations by providing the same thread ID
- **Conversation Isolation**: Each new conversation gets a unique thread ID
- **Memory Management**: Proper isolation of conversation history between different sessions

## How It Works

### Thread ID Generation

When no thread ID is provided, the system automatically generates a unique one:

```python
# Generates: "thread-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
thread_id = generate_unique_thread_id()
```

### Thread ID Validation

All thread IDs are validated to ensure they meet security and format requirements:
- Length: 5-100 characters
- Characters: alphanumeric, hyphens, and underscores only
- Format: `^[a-zA-Z0-9_-]{5,100}$`

### Thread ID Hierarchy

The system creates different thread IDs for different components:
- **Base Thread ID**: Main conversation identifier
- **Supervisor Thread ID**: `{base_thread_id}-supervisor`
- **Step Thread ID**: `{base_thread_id}-step-{step_id}`

## API Usage

### Query Endpoint

**Without Thread ID (New Conversation):**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello, start a new conversation"
  }'
```

Response includes generated thread ID:
```json
{
  "success": true,
  "response": "Hello! How can I help you?",
  "thread_id": "thread-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "metadata": {...}
}
```

**With Thread ID (Continue Conversation):**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Continue our previous conversation",
    "thread_id": "thread-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }'
```

### Worker Endpoint

**Without Thread ID:**
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "web_agent",
    "input": "Search for something"
  }'
```

**With Thread ID:**
```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "web_agent",
    "input": "Continue searching",
    "thread_id": "my-custom-thread-123"
  }'
```

### Form Endpoint

The form endpoint also supports thread IDs:
```bash
curl -X POST "http://localhost:8000/query/form" \
  -F "input=Hello from form" \
  -F "thread_id=my-form-conversation"
```

## Request/Response Models

### Request Models

Both `QueryRequest` and `WorkerRequest` now include:
```python
thread_id: Optional[str] = Field(
    None, 
    description="Optional thread ID for conversation continuity. "
                "If not provided, a new thread will be created."
)
```

### Response Models

Both `QueryResponse` and `WorkerResponse` now include:
```python
thread_id: str = Field(
    ..., description="Thread ID used for this conversation"
)
```

## Conversation Continuity Examples

### Example 1: Multi-turn Conversation

```python
import requests

# First message - no thread_id provided
response1 = requests.post("http://localhost:8000/query", json={
    "input": "My name is Alice. Remember this."
})
thread_id = response1.json()["thread_id"]

# Second message - use same thread_id
response2 = requests.post("http://localhost:8000/query", json={
    "input": "What's my name?",
    "thread_id": thread_id
})
# Agent should remember "Alice" from previous message
```

### Example 2: Multiple Separate Conversations

```python
# Conversation 1
response1a = requests.post("http://localhost:8000/query", json={
    "input": "I like pizza",
    "thread_id": "conversation-1"
})

response1b = requests.post("http://localhost:8000/query", json={
    "input": "What do I like?",
    "thread_id": "conversation-1"
})
# Should respond: "You like pizza"

# Conversation 2 (separate)
response2a = requests.post("http://localhost:8000/query", json={
    "input": "I like burgers",
    "thread_id": "conversation-2"
})

response2b = requests.post("http://localhost:8000/query", json={
    "input": "What do I like?",
    "thread_id": "conversation-2"
})
# Should respond: "You like burgers" (not pizza)
```

## CLI Usage

The CLI automatically generates unique thread IDs for each execution:

```bash
python -m app.main --agent web_agent "Search for Python tutorials"
# Each CLI run gets a fresh thread ID
```

## Implementation Details

### Thread Manager Module

The `app/thread_manager.py` module provides:
- `get_or_create_thread_id(provided_thread_id)`: Main function for thread ID management
- `generate_unique_thread_id()`: Creates UUID-based thread IDs
- `generate_timestamped_thread_id()`: Creates timestamp-based thread IDs
- `validate_thread_id(thread_id)`: Validates thread ID format
- `create_supervisor_thread_id(base_thread_id)`: Creates supervisor-specific thread ID
- `create_step_thread_id(base_thread_id, step_id)`: Creates step-specific thread ID

### Memory Isolation

Each thread ID maintains its own conversation history in LangGraph's MemorySaver:
- Different thread IDs = completely isolated conversations
- Same thread ID = shared conversation history
- No cross-contamination between conversations

## Migration from Previous Version

**Before (Hardcoded Thread IDs):**
- All API calls shared the same "test-thread" 
- Conversations leaked into each other
- No way to maintain separate conversations

**After (Dynamic Thread IDs):**
- Each new request gets unique thread ID (if not provided)
- Clients can provide thread IDs for continuity
- Complete conversation isolation
- Proper memory management

## Best Practices

1. **For New Conversations**: Don't provide a thread_id, let the system generate one
2. **For Continuing Conversations**: Always use the thread_id from the previous response
3. **For Session Management**: Use meaningful thread IDs like "user-123-session-456"
4. **For Testing**: Use descriptive thread IDs like "test-conversation-1"

## Troubleshooting

### Invalid Thread ID Error
If you get a thread ID validation error:
- Check length (5-100 characters)
- Use only alphanumeric characters, hyphens, and underscores
- Avoid special characters like @, #, $, etc.

### Memory Not Persisting
If conversations don't remember previous messages:
- Ensure you're using the same thread_id for all messages in the conversation
- Check that the thread_id in the response matches what you sent

### Cross-Conversation Contamination
If conversations are mixing up:
- Use different thread_ids for different conversations
- Don't reuse thread_ids across different users or sessions
