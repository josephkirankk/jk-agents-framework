# Conversation Memory Quick Fix Guide

## 🔍 Problem Summary

Conversation memory is not working - the agent doesn't remember previous interactions.

**Example:**
- Request 1: "print 1 to 10" → Works, prints numbers
- Request 2: "write fibonacci for each number here" → Agent asks "which numbers?" instead of using 1-10 from previous request

## ✅ Root Cause

**The conversation memory system is working correctly.** The issue is that **you're not providing the same `thread_id` in both requests**.

Each request without a `thread_id` gets a NEW random thread_id, so the system can't find previous conversations.

## 🛠️ Solution

### Use the Same `thread_id` for Related Requests

#### Option 1: Using curl

```bash
# Define a thread_id for this conversation
THREAD_ID="my-conversation-123"

# Request 1
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"print 1 to 10\",
    \"config_path\": \"config/python_exec_agent_working.yaml\",
    \"thread_id\": \"$THREAD_ID\"
  }"

# Request 2 - uses context from Request 1
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"write fibonacci for each number here\",
    \"config_path\": \"config/python_exec_agent_working.yaml\",
    \"thread_id\": \"$THREAD_ID\"
  }"
```

#### Option 2: Using Python

```python
import requests

# Use the same thread_id for the entire conversation
thread_id = "my-conversation-123"

# Request 1
response1 = requests.post(
    "http://localhost:8000/query",
    json={
        "input": "print 1 to 10",
        "config_path": "config/python_exec_agent_working.yaml",
        "thread_id": thread_id
    }
)

# Request 2 - automatically uses context from Request 1
response2 = requests.post(
    "http://localhost:8000/query",
    json={
        "input": "write fibonacci for each number here",
        "config_path": "config/python_exec_agent_working.yaml",
        "thread_id": thread_id  # SAME thread_id!
    }
)
```

## 🧪 Testing

### Test 1: Verify Conversation Memory System

```bash
# Test the memory system itself
python temp_tests/test_conversation_memory_debug.py
```

Expected output: All tests pass ✅

### Test 2: Test API with thread_id

```bash
# Make sure API server is running
python api.py

# In another terminal, run the test
python temp_tests/test_api_conversation_memory.py
```

Or use the shell script:

```bash
./temp_tests/test_conversation_memory_api.sh
```

## 📊 How It Works

```
Request 1 (thread_id="abc123")
  ↓
  User: "print 1 to 10"
  ↓
  Agent: Executes and prints 1-10
  ↓
  Storage: Saves conversation with key "abc123"
  
Request 2 (thread_id="abc123")  ← SAME thread_id
  ↓
  User: "write fibonacci for each number here"
  ↓
  System: Looks up thread "abc123" → Finds previous conversation
  ↓
  Enhanced Input: "Previous context: [Turn-1] User: print 1 to 10..."
  ↓
  Agent: Uses context, knows numbers are 1-10
  ↓
  Agent: Calculates Fibonacci for 1-10
```

## ❌ What Doesn't Work

```
Request 1 (thread_id=auto-generated-xyz)
  ↓
  Conversation stored with key "xyz"

Request 2 (thread_id=auto-generated-abc)  ← DIFFERENT thread_id
  ↓
  System: Looks up thread "abc" → NOT FOUND
  ↓
  Agent: No context, asks for numbers
```

## 🔧 Configuration Check

Your config at `config/python_exec_agent_working.yaml` is correct:

```yaml
conversation_memory:
  enabled: true
  database_url: ""
  max_conversations: 10
  max_context_length: 2000
  prepend_context: true
  pool_size: 10
  cleanup_days: 7
```

✅ No changes needed to the configuration.

## 💡 Best Practices

1. **Generate a unique thread_id per conversation session**
   ```python
   import uuid
   thread_id = f"conversation-{uuid.uuid4()}"
   ```

2. **Store thread_id on the client side** (in session, cookie, or database)

3. **Reuse the same thread_id** for all requests in that conversation

4. **Create a new thread_id** when starting a new conversation topic

## 🎯 Quick Test Command

```bash
# Test with explicit thread_id
THREAD="test-$(date +%s)"
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
  -d "{\"input\": \"print 1 to 10\", \"config_path\": \"config/python_exec_agent_working.yaml\", \"thread_id\": \"$THREAD\"}"

# Use same thread_id for follow-up
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" \
  -d "{\"input\": \"write fibonacci for each number here\", \"config_path\": \"config/python_exec_agent_working.yaml\", \"thread_id\": \"$THREAD\"}"
```

## 📝 Summary

- ✅ Conversation memory system: **WORKING**
- ✅ Configuration: **CORRECT**
- ❌ Issue: **Not providing thread_id in requests**
- ✅ Solution: **Always use the same thread_id for related requests**

## 🔗 Related Files

- Documentation: `temp_docs/CONVERSATION_MEMORY_FIX.md`
- Test script (Python): `temp_tests/test_api_conversation_memory.py`
- Test script (Shell): `temp_tests/test_conversation_memory_api.sh`
- Debug test: `temp_tests/test_conversation_memory_debug.py`
