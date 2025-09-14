# JK-Agents Thread ID Curl Commands Demo

This document provides individual curl commands to demonstrate thread ID functionality with conversation continuity using the `pep_mcp_sample.yaml` configuration.

## Configuration
- **API Base URL**: `http://localhost:8000`
- **Config Path**: `c:\JK\dev\repo\jk-agents\config\pep_mcp_sample.yaml`

## Step-by-Step Thread ID Demo

### Step 1: Start New Conversation (No Thread ID)
This will generate a new thread ID automatically.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello! I need help finding restaurants in New York. Please remember that I prefer Italian cuisine.",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml"
  }'
```

**Expected Response Structure:**
```json
{
  "success": true,
  "response": "Hello! I'd be happy to help you find Italian restaurants in New York...",
  "thread_id": "thread-12345678-1234-1234-1234-123456789abc",
  "metadata": {...}
}
```

**📝 Note**: Copy the `thread_id` from the response for the next steps!

### Step 2: Continue Conversation (Using Thread ID)
Replace `YOUR_THREAD_ID_HERE` with the thread_id from Step 1.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Can you remember what type of cuisine I mentioned I prefer? And can you search for those restaurants in Manhattan?",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "YOUR_THREAD_ID_HERE"
  }'
```

**Expected Behavior**: The agent should remember you prefer Italian cuisine from the previous conversation.

### Step 3: Direct Agent Call (Using Same Thread ID)
This demonstrates thread ID continuity across different endpoints.

```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "restaurants_agent",
    "input": "Based on our previous conversation, can you find 3 specific Italian restaurants in Manhattan with high ratings?",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "YOUR_THREAD_ID_HERE"
  }'
```

**Expected Behavior**: The restaurants_agent should have context from previous conversation steps.

### Step 4: New Conversation (No Thread ID)
This will create a completely new conversation thread.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "What type of cuisine do I prefer? This should be a fresh conversation.",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml"
  }'
```

**Expected Behavior**: The agent should NOT remember your Italian cuisine preference since this is a new thread.

### Step 5: Custom Thread ID
You can provide your own thread ID for session management.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "I want to start a new restaurant search session. Please remember I am looking for vegetarian options.",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "my-restaurant-session-2024"
  }'
```

### Step 6: Continue Custom Thread
Use the same custom thread ID to continue the conversation.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Can you remember what dietary preference I mentioned?",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "my-restaurant-session-2024"
  }'
```

**Expected Behavior**: The agent should remember you're looking for vegetarian options.

## Additional Endpoints Supporting Thread ID

### Form-based Query Endpoint
```bash
curl -X POST "http://localhost:8000/query/form" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "input=Find vegetarian restaurants in Brooklyn&config_path=c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml&thread_id=YOUR_THREAD_ID_HERE"
```

### Worker Upload Endpoint (with files)
```bash
curl -X POST "http://localhost:8000/worker/upload" \
  -F "agent_name=restaurants_agent" \
  -F "input=Analyze this restaurant data in context of our previous discussion" \
  -F "config_path=c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml" \
  -F "thread_id=YOUR_THREAD_ID_HERE" \
  -F "files=@restaurant_data.csv"
```

## Testing Thread ID Validation

### Valid Thread ID Formats
```bash
# UUID-based (auto-generated format)
"thread-12345678-1234-1234-1234-123456789abc"

# Custom alphanumeric with hyphens/underscores
"my-session-2024"
"user_123_session"
"restaurant-search-001"
```

### Invalid Thread ID (Will Generate New One)
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Test with invalid thread ID",
    "config_path": "c:\\JK\\dev\\repo\\jk-agents\\config\\pep_mcp_sample.yaml",
    "thread_id": "invalid@thread#id!"
  }'
```

**Expected Behavior**: System will generate a new valid thread ID and use that instead.

## Key Thread ID Features

1. **Automatic Generation**: If no thread_id provided, system generates one
2. **Validation**: Invalid thread IDs are rejected and new ones generated
3. **Consistency**: Same thread_id maintains conversation history across calls
4. **Isolation**: Different thread IDs have completely separate memories
5. **Cross-Endpoint**: Thread IDs work across all API endpoints
6. **Custom IDs**: You can provide your own thread IDs for session management

## Response Structure

All API responses include the thread_id field:

```json
{
  "success": true,
  "response": "Agent response text...",
  "thread_id": "thread-12345678-1234-1234-1234-123456789abc",
  "metadata": {
    "agent_name": "restaurants_agent",
    "model_used": "azure_openai:gpt-4.1",
    "business_context": true
  }
}
```

## Troubleshooting

### Server Not Running
```bash
# Check if server is running
curl -X GET "http://localhost:8000/health"
```

### Check Available Agents
```bash
curl -X GET "http://localhost:8000/"
```

### View API Documentation
Open in browser: `http://localhost:8000/docs`

## Thread ID Hierarchy (Internal)

The system creates hierarchical thread IDs internally:
- **Base Thread**: `thread-abc123` (what you see in responses)
- **Supervisor Thread**: `thread-abc123-supervisor` (internal)
- **Step Threads**: `thread-abc123-step-1`, `thread-abc123-step-2` (internal)

This ensures proper isolation and memory management across the multi-agent system.
