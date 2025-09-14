# JK-Agents Memory System Documentation

## 🧠 What is Memory in JK-Agents?

Memory in JK-Agents allows AI agents to **remember previous conversations** and maintain context across multiple interactions. Think of it like having a conversation with a friend who remembers what you talked about yesterday.

### 🎯 **Simple Example:**
```
You: "I have 10 restaurants"
Agent: "Got it! I'll remember you have 10 restaurants."

[Later, same conversation...]
You: "How many restaurants do I have?"
Agent: "You have 10 restaurants." ← Agent remembers!

[Different conversation...]
You: "How many restaurants do I have?"
Agent: "I don't have information about your restaurants." ← New conversation, no memory
```

## 🔑 **Key Concepts**

### **Thread ID = Conversation ID**
- Each conversation has a unique **Thread ID** (like `thread-abc123`)
- Same Thread ID = Agent remembers previous messages
- Different Thread ID = Fresh conversation, no memory

### **Memory Persistence**
- Memory lasts while the server is running
- Server restart = All memory is lost
- Each conversation is completely separate

## 🏗️ **How Memory Works**

### **1. Memory Storage Location**
```
Your Computer's RAM Memory
├── JK-Agents Server Process
    ├── Global Memory Manager
        ├── Thread: "thread-abc123"
        │   ├── Message 1: "I have 10 restaurants"
        │   ├── Response 1: "Got it! I'll remember..."
        │   ├── Message 2: "How many restaurants?"
        │   └── Response 2: "You have 10 restaurants."
        ├── Thread: "thread-xyz789"
        │   ├── Message 1: "Hello"
        │   └── Response 1: "Hi there!"
        └── Thread: "different-thread-123"
            ├── Message 1: "How many restaurants?"
            └── Response 1: "I don't have information..."
```

### **2. Memory Flow Process**
```
1. You send a message → API receives it
2. API checks: "Do you have a Thread ID?"
   - Yes → Use existing conversation memory
   - No → Create new Thread ID, start fresh
3. Agent loads previous messages from memory
4. Agent processes your new message WITH context
5. Agent responds and saves the conversation
6. Memory updated with new exchange
```

## 🚀 **Using Memory in Practice**

### **Starting a New Conversation**
```bash
# No thread_id = New conversation
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "simple_test_agent",
    "input": "My name is John and I own 5 coffee shops",
    "config_path": "config/simple_test.yaml"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "Nice to meet you, John! I'll remember that you own 5 coffee shops.",
  "thread_id": "thread-abc123-def456"
}
```

### **Continuing the Conversation**
```bash
# Use the thread_id from previous response
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "simple_test_agent",
    "input": "What did I tell you about my business?",
    "config_path": "config/simple_test.yaml",
    "thread_id": "thread-abc123-def456"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "You told me your name is John and you own 5 coffee shops.",
  "thread_id": "thread-abc123-def456"
}
```

## 🔍 **Memory Management**

### **Check Memory Statistics**
```bash
curl -X GET "http://localhost:8000/memory/stats"
```

**Response:**
```json
{
  "status": "success",
  "memory_stats": {
    "total_threads": 3,
    "threads": {
      "thread-abc123-def456": 4,
      "thread-xyz789-ghi012": 2,
      "thread-different-123": 1
    },
    "checkpointer_type": "InMemorySaver"
  },
  "timestamp": "2025-09-14T10:30:00.000Z"
}
```

**What this means:**
- `total_threads: 3` → You have 3 different conversations
- `"thread-abc123-def456": 4` → This conversation has 4 message exchanges
- `checkpointer_type: "InMemorySaver"` → Memory is stored in RAM

## 🎭 **Memory Isolation Examples**

### **Example 1: Same Thread = Shared Memory**
```bash
# Conversation 1 - Store information
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "simple_test_agent", "input": "I love pizza", "thread_id": "my-thread"}'
# Response: "I'll remember you love pizza!"

# Conversation 2 - Same thread, agent remembers
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "simple_test_agent", "input": "What food do I like?", "thread_id": "my-thread"}'
# Response: "You love pizza!" ✅
```

### **Example 2: Different Thread = No Memory**
```bash
# Conversation 3 - Different thread, no memory
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "simple_test_agent", "input": "What food do I like?", "thread_id": "other-thread"}'
# Response: "I don't have information about your food preferences." ✅
```

## 🛠️ **Best Practices**

### **✅ Do This:**
- **Save Thread IDs**: Always store the `thread_id` from responses
- **Use Descriptive Thread IDs**: `"user-john-session-1"` instead of random strings
- **One Thread per Conversation**: Don't mix different topics in same thread
- **Check Memory Stats**: Monitor memory usage with `/memory/stats`

### **❌ Avoid This:**
- **Don't lose Thread IDs**: You'll lose conversation context
- **Don't reuse Thread IDs**: For completely different conversations
- **Don't assume persistence**: Memory is lost on server restart
- **Don't store sensitive data**: Memory is not encrypted by default

## 🔧 **Configuration Options**

### **Thread ID Format**
- **Auto-generated**: `thread-{uuid}` (e.g., `thread-abc123-def456-ghi789`)
- **Custom**: Any string with letters, numbers, hyphens, underscores
- **Length**: 5-100 characters
- **Valid**: `my-conversation-1`, `user-john-2025-01-15`
- **Invalid**: `a`, `very-long-thread-id-that-exceeds-the-maximum-length-limit-of-100-characters`

### **Memory Limits**
- **Storage**: Limited by available RAM
- **Persistence**: Until server restart
- **Threads**: No hard limit (memory dependent)
- **Messages**: No hard limit per thread

## 🚨 **Troubleshooting**

### **Problem: Agent doesn't remember**
**Symptoms:**
```json
{
  "input": "What did I tell you earlier?",
  "response": "I don't have any previous information from our conversation."
}
```

**Solutions:**
1. **Check Thread ID**: Ensure you're using the same `thread_id`
2. **Verify Response**: Confirm previous calls returned same `thread_id`
3. **Check Server**: Server restart clears all memory
4. **Test Memory**: Use `/memory/stats` to verify thread exists

### **Problem: Memory stats show 0 threads**
**Symptoms:**
```json
{
  "memory_stats": {
    "total_threads": 0,
    "threads": {}
  }
}
```

**Solutions:**
1. **Make API Call**: Memory is created after first agent interaction
2. **Check Server Logs**: Look for memory-related errors
3. **Restart Server**: Fresh start might resolve issues

## 📊 **Memory Architecture**

### **Technical Overview**
```
┌─────────────────────────────────────────┐
│           JK-Agents Server              │
├─────────────────────────────────────────┤
│  Global Checkpointer Manager           │
│  ├── InMemorySaver Instance             │
│  │   ├── Thread: "thread-abc123"       │
│  │   │   └── Conversation History      │
│  │   ├── Thread: "thread-xyz789"       │
│  │   │   └── Conversation History      │
│  │   └── Thread: "thread-def456"       │
│  │       └── Conversation History      │
│  └── Memory Statistics API             │
└─────────────────────────────────────────┘
```

### **Data Flow**
```
API Request → Thread Manager → Global Memory → Agent → Response
     ↓              ↓              ↓           ↓         ↓
  thread_id    Validate ID    Load History  Process   Save State
```

## 🎯 **Quick Reference**

### **Essential Endpoints**
- `POST /worker` - Execute agent with memory
- `POST /query` - Multi-agent system with memory  
- `GET /memory/stats` - Check memory statistics

### **Key Parameters**
- `thread_id` - Conversation identifier (optional)
- `agent_name` - Which agent to use
- `input` - Your message/question
- `config_path` - Agent configuration file

### **Response Fields**
- `thread_id` - Use this for follow-up messages
- `response` - Agent's reply
- `success` - Whether the request succeeded

---

## 🔄 **Advanced Usage**

### **Multi-Agent Memory Sharing**
All agents in the same thread share the same memory:

```bash
# Agent 1 stores information
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "simple_test_agent", "input": "I prefer Italian food", "thread_id": "shared-thread"}'

# Agent 2 can access the same memory
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "restaurants_agent", "input": "What food does the user prefer?", "thread_id": "shared-thread"}'
# Response: "The user prefers Italian food."
```

### **Memory in Supervisor Mode**
The supervisor system also uses memory:

```bash
curl -X POST "http://localhost:8000/query" \
  -d '{"input": "Plan a dinner based on my food preferences", "thread_id": "planning-thread"}'
```

### **Session Management Patterns**

#### **User-Based Sessions**
```bash
# Create user-specific thread IDs
thread_id = f"user-{user_id}-session-{timestamp}"
# Example: "user-john123-session-20250914"
```

#### **Topic-Based Sessions**
```bash
# Separate threads for different topics
restaurant_thread = "user-john-restaurants"
travel_thread = "user-john-travel"
business_thread = "user-john-business"
```

## 🧪 **Testing Memory**

### **Quick Memory Test Script**
```bash
#!/bin/bash
# Test memory persistence

echo "=== Testing Memory Persistence ==="

# Step 1: Store information
echo "Storing information..."
RESPONSE1=$(curl -s -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "simple_test_agent", "input": "My favorite color is blue", "config_path": "config/simple_test.yaml"}')

# Extract thread ID
THREAD_ID=$(echo $RESPONSE1 | jq -r '.thread_id')
echo "Thread ID: $THREAD_ID"

# Step 2: Test recall
echo "Testing recall..."
RESPONSE2=$(curl -s -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d "{\"agent_name\": \"simple_test_agent\", \"input\": \"What is my favorite color?\", \"config_path\": \"config/simple_test.yaml\", \"thread_id\": \"$THREAD_ID\"}")

echo "Response: $(echo $RESPONSE2 | jq -r '.response')"

# Step 3: Test isolation
echo "Testing memory isolation..."
RESPONSE3=$(curl -s -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "simple_test_agent", "input": "What is my favorite color?", "config_path": "config/simple_test.yaml", "thread_id": "different-thread"}')

echo "Different thread response: $(echo $RESPONSE3 | jq -r '.response')"
```

## 📚 **Related Documentation**

- **[Thread Management](THREAD_MANAGEMENT.md)** - Detailed thread ID management
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Configuration Guide](CONFIGURATION.md)** - Agent configuration options
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions

## 💡 **Remember**
Memory in JK-Agents is like having a conversation with someone who has a perfect memory of everything you've discussed in that specific conversation, but starts fresh with each new conversation thread. Use Thread IDs to maintain context, and always save them for continued conversations!
