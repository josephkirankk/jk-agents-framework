# Multi-Turn & Search Issues Analysis

**Date:** October 21, 2025  
**Status:** 🔍 **IN PROGRESS - ROOT CAUSE ANALYSIS**

---

## 🎯 Issues Reported by User

User reported issues with:
1. **Multi-turn conversations** - Context not being maintained across turns
2. **Search functionality** - google_search tool having issues

---

## 🔍 Root Cause Analysis

Based on code review and diagnostics, here are the identified issues:

### 1. ✅ **FIXED**: SerperToolWrapper Signature Issue

**Status:** ALREADY FIXED in previous session

**Original Problem:**
```python
# ❌ WRONG - Accepts single payload argument
async def _arun(self, payload: Any) -> str:
```

**Fixed To:**
```python
# ✅ CORRECT - Accepts **kwargs
async def _arun(self, **kwargs: Any) -> str:
    params = dict(kwargs)
    params = self._inject_defaults(params)
```

**Impact:** Without this fix, the tool would crash with `TypeError: unexpected keyword argument 'query'`

---

### 2. ⚠️ **ISSUE**: Conversation Memory Using In-Memory Storage

**Status:** CONFIGURATION ISSUE (May be intentional)

**Problem:**
```yaml
conversation_memory:
  enabled: true
  database_url: ""  # ← EMPTY = In-memory only, NOT persistent
```

**Impact:**
- Conversation history is lost when API server restarts
- Multi-turn conversations only work within the same session
- No persistence across different user sessions

**Fix Options:**

**Option A:** Use in-memory (current) - Fast but not persistent
```yaml
conversation_memory:
  enabled: true
  database_url: ""  # Empty = in-memory
```

**Option B:** Use persistent storage (recommended)
```yaml
conversation_memory:
  enabled: true
  database_url: "sqlite:///./data/conversations.db"
```

---

### 3. ✅ **WORKING**: ChromaDB Backend for Checkpoints

**Status:** CONFIGURED CORRECTLY

**Current Config:**
```yaml
memory:
  backend: "chromadb"
  chromadb:
    path: "./serp_memory"
    checkpoint_collection: "serp-checkpoints"
    context_collection: "serp-context"
```

**Note:** This is for LangGraph checkpoints (agent state persistence), NOT conversation memory. These are separate systems.

---

### 4. ✅ **VERIFIED**: SERPER_API_KEY is Set

**Status:** WORKING

- Key is properly set in environment
- SerperToolWrapper correctly injects defaults (gl="us", hl="en")
- No authentication issues expected

---

## 🔧 How Multi-Turn Should Work

### Architecture:

```
1. User sends message (Turn 1)
   ↓
2. API stores: user message → conversation_memory
   ↓
3. Agent processes with context from conversation_memory
   ↓
4. API stores: assistant response → conversation_memory
   ↓
5. User sends message (Turn 2) with same thread_id
   ↓
6. API retrieves: previous context from conversation_memory
   ↓
7. Agent sees full conversation history
   ↓
8. Continues conversation naturally
```

### Current Implementation:

**File:** `app/memory_integration.py`

```python
# In-memory storage
_conversations: Dict[str, List[Dict[str, Any]]] = {}

async def store_conversation_turn(
    thread_id: str,
    user_input: str,
    assistant_response: str
) -> bool:
    # Stores in _conversations dict
    # PROBLEM: Lost on server restart
```

---

## 🚨 Critical Issues Found

### Issue #1: Conversation Context Not Persisted

**Severity:** HIGH  
**Impact:** Multi-turn fails across sessions

**Current Behavior:**
- Conversation stored in Python dict: `_conversations`
- Cleared when API server restarts
- No database persistence

**Expected Behavior:**
- Conversations persisted to database
- Available across server restarts
- Searchable and retrievable

**Fix Required:**
- Implement database backend for conversation storage
- Or document that in-memory is intentional
- Add warning to users about session persistence

---

### Issue #2: Thread ID Consistency

**Severity:** MEDIUM  
**Impact:** Context mixing between conversations

**Potential Problem:**
- If thread_id is not passed correctly from UI → API
- Or if thread_id changes between turns
- Conversation context will be lost

**Verification Needed:**
- Check how thread_id is generated on first turn
- Check how thread_id is passed on subsequent turns
- Ensure UI/client maintains thread_id consistently

---

### Issue #3: Context Window Limit

**Severity:** MEDIUM  
**Impact:** Long conversations may lose early context

**Current Implementation:**
```python
def get_conversation_context(thread_id: str) -> str:
    messages = _conversations[thread_id]
    # Returns ALL messages - no summarization
```

**Problem:**
- No automatic summarization
- Long conversations will exceed LLM context window
- Early messages will be truncated

**Fix Required:**
- Implement automatic summarization
- Or sliding window approach
- Or use `simple_conversation_memory_fixed.py` which has this

---

## 💡 Recommended Fixes

### Fix #1: Use Simple Conversation Memory

**Status:** CODE ALREADY EXISTS

**File:** `app/simple_conversation_memory_fixed.py`

This file has:
- ✅ Disk persistence
- ✅ Turn tracking
- ✅ Automatic summarization (triggers at 30+ messages)
- ✅ Thread-safe operations

**To Enable:**
1. Import and use `SimpleConversationMemory` instead of `_conversations` dict
2. Update `memory_integration.py` to use it
3. Test multi-turn conversations

---

### Fix #2: Add Database URL to Config

**For Production:**
```yaml
conversation_memory:
  enabled: true
  database_url: "sqlite:///./data/conversations.db"
  max_conversations: 100
  max_context_length: 4000
```

---

### Fix #3: Verify Thread ID Flow

**Check:**
1. API endpoint receives `thread_id` in request
2. Thread ID is passed to agent/memory system
3. Same thread ID used for storing and retrieving
4. UI/client maintains thread ID across turns

**Test:**
```bash
# Turn 1
curl -X POST http://localhost:8000/query/form \
  -d "query=Hello&thread_id=test-123"

# Turn 2 (same thread_id)
curl -X POST http://localhost:8000/query/form \
  -d "query=What did I just say?&thread_id=test-123"
```

Expected: Agent remembers "Hello" from Turn 1

---

## 🧪 Testing Plan

### Test 1: Single Turn (Should Work)
```bash
curl -X POST http://localhost:8000/query/form \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "query=suggest best phones under 20000&config_name=deep_agent_advanced_serpapi.yaml"
```

**Expected:** google_search tool works, agent provides results

---

### Test 2: Multi-Turn (May Fail)
```bash
# Turn 1
curl -X POST http://localhost:8000/query/form \
  -d "query=Tell me about iPhone 15&config_name=deep_agent_advanced_serpapi.yaml&thread_id=test-001"

# Turn 2
curl -X POST http://localhost:8000/query/form \
  -d "query=What about its battery life?&config_name=deep_agent_advanced_serpapi.yaml&thread_id=test-001"
```

**Expected:** Turn 2 should know we're talking about iPhone 15

**If Fails:** Check logs for:
- Thread ID mismatch
- Context not retrieved
- Memory not initialized

---

## 🎯 Next Steps

1. ✅ SerperToolWrapper fix verified
2. ⏳ Test multi-turn conversation flow
3. ⏳ Verify thread_id handling in API
4. ⏳ Decide: in-memory vs persistent storage
5. ⏳ Implement chosen solution
6. ⏳ Add tests for multi-turn
7. ⏳ Document configuration options

---

## 📋 Files to Review

| File | Purpose | Status |
|------|---------|--------|
| `app/memory_integration.py` | Conversation memory (in-memory) | ⚠️ Needs review |
| `app/simple_conversation_memory_fixed.py` | Better conversation memory | ✅ Ready to use |
| `api.py` | API endpoints, thread ID handling | ⏳ Need to verify |
| `app/planner_executor.py` | Agent execution | ⏳ Need to verify |
| `config/deep_agent_advanced_serpapi.yaml` | Configuration | ⚠️ database_url empty |

---

## 🔑 Key Questions

1. **Is in-memory conversation storage intentional?**
   - If yes: Document this limitation
   - If no: Switch to persistent storage

2. **How is thread_id generated and maintained?**
   - Need to trace through API code
   - Verify client passes it correctly

3. **Is conversation context being passed to agents?**
   - Check `enhance_system_message_with_memory()` usage
   - Verify it's called in agent invocation flow

4. **Are we using the right memory system?**
   - `memory_integration.py` (current) - Simple in-memory
   - `simple_conversation_memory_fixed.py` - Better features
   - Choose one and stick with it

---

*Analysis complete. Awaiting decision on next steps.*
