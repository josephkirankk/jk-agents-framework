# JK-Agents Memory: Frequently Asked Questions

## 🤔 **Basic Questions**

### **Q: What is memory in JK-Agents?**
**A:** Memory allows AI agents to remember previous conversations. When you use the same Thread ID, the agent can recall what you discussed earlier, just like talking to a friend who remembers your past conversations.

### **Q: How long does memory last?**
**A:** Memory lasts while the JK-Agents server is running. When you restart the server, all memory is lost. Think of it like RAM in your computer - it's temporary storage.

### **Q: What is a Thread ID?**
**A:** A Thread ID is like a conversation ID. It's a unique identifier (like `thread-abc123`) that groups related messages together. Same Thread ID = same conversation with memory.

---

## 🔧 **Technical Questions**

### **Q: Where is memory physically stored?**
**A:** Memory is stored in your computer's RAM (system memory) using LangGraph's `InMemorySaver`. It's not saved to disk, which is why it's lost when the server restarts.

### **Q: How much memory can I store?**
**A:** Memory is limited by your computer's available RAM. Each conversation thread stores the message history, so more conversations and longer conversations use more memory.

### **Q: Can different agents share memory?**
**A:** Yes! All agents using the same Thread ID share the same memory. For example:
```bash
# Agent 1 stores info
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "agent1", "input": "I like pizza", "thread_id": "shared"}'

# Agent 2 can access the same memory
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "agent2", "input": "What food do I like?", "thread_id": "shared"}'
# Response: "You like pizza"
```

### **Q: What happens if I don't provide a Thread ID?**
**A:** The system automatically generates a new Thread ID for you. This starts a fresh conversation with no memory of previous interactions.

---

## 🚨 **Troubleshooting Questions**

### **Q: Why doesn't the agent remember what I said?**
**A:** Check these common issues:
1. **Different Thread ID**: Make sure you're using the exact same Thread ID
2. **Server Restart**: Memory is lost when the server restarts
3. **Typo in Thread ID**: Thread IDs are case-sensitive
4. **New Conversation**: You might have started a new conversation accidentally

**Debug Steps:**
```bash
# Check if your thread exists
curl -X GET "http://localhost:8000/memory/stats"

# Look for your thread_id in the response
```

### **Q: Memory stats show 0 threads but I made API calls**
**A:** This can happen if:
1. **No successful calls**: Check if your API calls actually succeeded
2. **Server restart**: Memory was cleared
3. **Wrong endpoint**: Make sure you're calling the correct API endpoint

**Solution:**
```bash
# Make a test call first
curl -X POST "http://localhost:8000/worker" \
  -d '{"agent_name": "simple_test_agent", "input": "test"}'

# Then check stats
curl -X GET "http://localhost:8000/memory/stats"
```

### **Q: I get "Invalid thread ID" errors**
**A:** Thread IDs must follow these rules:
- ✅ **Valid characters**: Letters, numbers, hyphens (-), underscores (_)
- ✅ **Length**: 5-100 characters
- ❌ **Invalid**: Special characters like @, #, $, %, spaces

**Examples:**
```bash
# Valid Thread IDs
"my-conversation-1"
"user_john_session_2025"
"thread-abc123-def456"

# Invalid Thread IDs
"a"                    # Too short
"my conversation"      # Contains space
"user@domain.com"      # Contains @
```

---

## 💼 **Usage Questions**

### **Q: How should I structure Thread IDs for my application?**
**A:** Use descriptive, hierarchical naming:

```bash
# User-based sessions
"user-{user_id}-session-{timestamp}"
"user-john123-session-20250914"

# Feature-based sessions
"support-ticket-{ticket_id}"
"learning-{subject}-{user_id}"
"chat-{room_id}-{date}"

# Business use cases
"customer-support-case-12345"
"sales-lead-conversation-67890"
"training-session-python-basics"
```

### **Q: Can I have multiple conversations with the same user?**
**A:** Absolutely! Use different Thread IDs for different topics:

```bash
# User John's restaurant conversation
thread_restaurants = "user-john-restaurants"

# User John's travel conversation  
thread_travel = "user-john-travel"

# User John's business conversation
thread_business = "user-john-business"
```

### **Q: How do I implement user sessions in my app?**
**A:** Here's a common pattern:

```python
# Python example
import uuid
from datetime import datetime

def create_user_session(user_id, topic=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if topic:
        return f"user-{user_id}-{topic}-{timestamp}"
    else:
        return f"user-{user_id}-session-{timestamp}"

# Usage
thread_id = create_user_session("john123", "support")
# Result: "user-john123-support-20250914_143022"
```

---

## 🔒 **Security Questions**

### **Q: Is memory data encrypted?**
**A:** By default, no. Memory is stored in plain text in RAM. For production use with sensitive data, consider:
1. Using encrypted checkpointers (PostgresSaver with encryption)
2. Implementing data sanitization
3. Using secure thread ID patterns

### **Q: Can other users access my conversation memory?**
**A:** Only if they know your exact Thread ID. Thread IDs act as access keys to conversations. Keep them secure and don't share them.

### **Q: What data is stored in memory?**
**A:** Memory stores:
- All messages in the conversation (user inputs and agent responses)
- System context and prompts
- Conversation metadata (timestamps, agent names)
- Any data the agent processes during the conversation

---

## 🚀 **Performance Questions**

### **Q: Does memory slow down the agents?**
**A:** Minimal impact. Loading conversation history adds a small delay, but it's usually negligible. Longer conversations may take slightly more time to process.

### **Q: How many conversations can I have simultaneously?**
**A:** Limited by your system's RAM. Each conversation thread stores message history, so the limit depends on:
- Available memory
- Length of conversations
- Number of messages per conversation

### **Q: Can I clear memory for specific conversations?**
**A:** Currently, there's no direct API to clear individual thread memory. You can:
1. Stop using the Thread ID (it will remain in memory but unused)
2. Restart the server (clears all memory)
3. Use a new Thread ID for fresh conversations

---

## 🔄 **Integration Questions**

### **Q: How do I integrate memory with my web application?**
**A:** Common patterns:

```javascript
// JavaScript example
class JKAgentsClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.sessions = new Map(); // Store thread IDs
  }
  
  async startConversation(userId, topic = 'general') {
    const threadId = `user-${userId}-${topic}-${Date.now()}`;
    this.sessions.set(`${userId}-${topic}`, threadId);
    return threadId;
  }
  
  async sendMessage(userId, message, topic = 'general') {
    const threadId = this.sessions.get(`${userId}-${topic}`);
    
    const response = await fetch(`${this.baseUrl}/worker`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_name: 'simple_test_agent',
        input: message,
        thread_id: threadId
      })
    });
    
    return response.json();
  }
}
```

### **Q: How do I handle memory in a multi-user application?**
**A:** Use user-specific Thread ID patterns:

```bash
# Pattern: "user-{user_id}-{session_type}-{timestamp}"
user_123_support = "user-123-support-20250914"
user_456_chat = "user-456-chat-20250914"
user_789_learning = "user-789-learning-20250914"
```

---

## 📚 **Learning Questions**

### **Q: Where can I learn more about memory implementation?**
**A:** Check these resources:
- [Memory System Documentation](MEMORY_SYSTEM.md) - Complete technical guide
- [Memory Quick Start](MEMORY_QUICK_START.md) - 5-minute tutorial
- [Thread Management](THREAD_MANAGEMENT.md) - Thread ID details
- [API Reference](API_REFERENCE.md) - All endpoints and parameters

### **Q: Are there example applications using memory?**
**A:** Yes! Check the `examples/` directory for:
- Customer support chatbot
- Personal assistant
- Learning companion
- Multi-user chat system

---

## 💡 **Pro Tips**

1. **Always save Thread IDs** - They're your key to conversation continuity
2. **Use descriptive naming** - Makes debugging and management easier
3. **Monitor memory usage** - Use `/memory/stats` to track conversations
4. **Plan for restarts** - Remember that memory is temporary
5. **Test memory isolation** - Verify different threads don't share data

---

**Still have questions?** Check the full documentation or create an issue in the repository!
