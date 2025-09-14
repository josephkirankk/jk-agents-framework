# JK-Agents Memory: Quick Start Guide

## 🚀 **5-Minute Memory Tutorial**

### **What You Need to Know**
1. **Thread ID** = Conversation ID
2. Same Thread ID = Agent remembers
3. Different Thread ID = Fresh start
4. No Thread ID = Auto-generated new conversation

---

## 📝 **Step 1: Start a Conversation**

```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "simple_test_agent",
    "input": "Hi! My name is Sarah and I love cooking.",
    "config_path": "config/simple_test.yaml"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "Hello Sarah! Nice to meet you. I'll remember that you love cooking.",
  "thread_id": "thread-abc123-def456"
}
```

**💡 Important:** Save the `thread_id` - you'll need it!

---

## 🔄 **Step 2: Continue the Conversation**

```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "simple_test_agent",
    "input": "What do you know about me?",
    "config_path": "config/simple_test.yaml",
    "thread_id": "thread-abc123-def456"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "I know your name is Sarah and you love cooking!",
  "thread_id": "thread-abc123-def456"
}
```

**✅ Success!** The agent remembered!

---

## 🆕 **Step 3: Test Memory Isolation**

```bash
curl -X POST "http://localhost:8000/worker" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "simple_test_agent",
    "input": "What do you know about me?",
    "config_path": "config/simple_test.yaml",
    "thread_id": "different-conversation"
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "I don't have any previous information about you. Could you tell me about yourself?",
  "thread_id": "different-conversation"
}
```

**✅ Perfect!** Different thread = No memory access.

---

## 📊 **Step 4: Check Memory Stats**

```bash
curl -X GET "http://localhost:8000/memory/stats"
```

**Response:**
```json
{
  "status": "success",
  "memory_stats": {
    "total_threads": 2,
    "threads": {
      "thread-abc123-def456": 2,
      "different-conversation": 1
    },
    "checkpointer_type": "InMemorySaver"
  }
}
```

**What this means:**
- 2 conversations total
- First conversation has 2 exchanges
- Second conversation has 1 exchange

---

## 🎯 **Common Use Cases**

### **Customer Support Session**
```bash
# Start support session
thread_id="support-customer-12345-$(date +%Y%m%d)"

# Customer describes issue
curl -X POST "http://localhost:8000/worker" \
  -d "{\"agent_name\": \"support_agent\", \"input\": \"My order #12345 is missing\", \"thread_id\": \"$thread_id\"}"

# Follow-up questions maintain context
curl -X POST "http://localhost:8000/worker" \
  -d "{\"agent_name\": \"support_agent\", \"input\": \"When was it supposed to arrive?\", \"thread_id\": \"$thread_id\"}"
```

### **Personal Assistant**
```bash
# User's personal thread
user_thread="assistant-john-personal"

# Store preferences
curl -X POST "http://localhost:8000/worker" \
  -d "{\"agent_name\": \"assistant_agent\", \"input\": \"I prefer meetings after 10 AM\", \"thread_id\": \"$user_thread\"}"

# Later scheduling request uses preferences
curl -X POST "http://localhost:8000/worker" \
  -d "{\"agent_name\": \"assistant_agent\", \"input\": \"Schedule a meeting with the team\", \"thread_id\": \"$user_thread\"}"
```

### **Learning Session**
```bash
# Educational thread
learning_thread="learn-python-basics"

# Build knowledge progressively
curl -X POST "http://localhost:8000/worker" \
  -d "{\"agent_name\": \"tutor_agent\", \"input\": \"I'm new to Python\", \"thread_id\": \"$learning_thread\"}"

curl -X POST "http://localhost:8000/worker" \
  -d "{\"agent_name\": \"tutor_agent\", \"input\": \"I learned about variables. What's next?\", \"thread_id\": \"$learning_thread\"}"
```

---

## ⚡ **PowerShell Quick Test**

```powershell
# Windows PowerShell version
$apiBase = "http://localhost:8000"

# Test 1: Store info
$response1 = Invoke-RestMethod -Uri "$apiBase/worker" -Method Post -ContentType "application/json" -Body '{"agent_name": "simple_test_agent", "input": "I have 3 cats named Fluffy, Whiskers, and Shadow", "config_path": "config/simple_test.yaml"}'

$threadId = $response1.thread_id
Write-Host "Thread ID: $threadId"
Write-Host "Response: $($response1.response)"

# Test 2: Recall info
$response2 = Invoke-RestMethod -Uri "$apiBase/worker" -Method Post -ContentType "application/json" -Body "{`"agent_name`": `"simple_test_agent`", `"input`": `"What are my cats' names?`", `"config_path`": `"config/simple_test.yaml`", `"thread_id`": `"$threadId`"}"

Write-Host "Recall Response: $($response2.response)"
```

---

## 🛠️ **Troubleshooting**

### **Problem: "Agent doesn't remember"**
```bash
# Check if you're using the same thread_id
echo "Thread ID from first call: $THREAD_ID_1"
echo "Thread ID from second call: $THREAD_ID_2"

# They should be identical!
```

### **Problem: "Memory stats show 0 threads"**
```bash
# Make sure server is running
curl -X GET "http://localhost:8000/health"

# Make at least one API call first
curl -X POST "http://localhost:8000/worker" -d '{"agent_name": "simple_test_agent", "input": "test"}'

# Then check stats
curl -X GET "http://localhost:8000/memory/stats"
```

---

## 📋 **Cheat Sheet**

### **Essential Commands**
```bash
# Start new conversation (auto thread ID)
curl -X POST "http://localhost:8000/worker" -d '{"agent_name": "AGENT", "input": "MESSAGE"}'

# Continue conversation (use thread ID)
curl -X POST "http://localhost:8000/worker" -d '{"agent_name": "AGENT", "input": "MESSAGE", "thread_id": "THREAD_ID"}'

# Check memory
curl -X GET "http://localhost:8000/memory/stats"

# Health check
curl -X GET "http://localhost:8000/health"
```

### **Thread ID Best Practices**
- ✅ `user-john-session-20250914`
- ✅ `support-ticket-12345`
- ✅ `learning-python-basics`
- ❌ `a` (too short)
- ❌ `thread-with-special-characters-@#$%` (invalid chars)

---

## 🎉 **You're Ready!**

You now understand:
- ✅ How to start conversations with memory
- ✅ How to continue conversations using thread IDs
- ✅ How memory isolation works
- ✅ How to monitor memory usage
- ✅ Common patterns and troubleshooting

**Next Steps:**
- Read the full [Memory System Documentation](MEMORY_SYSTEM.md)
- Explore [API Reference](API_REFERENCE.md)
- Check out [Advanced Configuration](CONFIGURATION.md)

---

**💡 Pro Tip:** Always save the `thread_id` from API responses - it's your key to maintaining conversation memory!
