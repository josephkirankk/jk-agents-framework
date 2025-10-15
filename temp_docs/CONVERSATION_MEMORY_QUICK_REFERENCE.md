# Conversation Memory - Quick Reference

## ✅ Problem FIXED

**Issue**: Tool call protocol errors after 2-3 conversation turns
**Root Cause**: ChromaDB checkpointer conflict with conversation_memory
**Solution**: Disabled ChromaDB backend in config

## 🔧 What Was Changed

**File**: `config/python_exec_agent_working.yaml`

```yaml
# BEFORE (causing errors):
memory:
  backend: "chromadb"
  chromadb:
    path: "./advanced_memory_test"
    # ... more config

# AFTER (fixed):
memory:
  backend: "none"  # Disabled - using conversation_memory instead
  # chromadb: ... (commented out)
```

## 🧪 Quick Test

```bash
# Run verification test
./temp_tests/verify_conversation_memory_fix.sh
```

## 💡 How to Use

### Option 1: Helper Script (Recommended)
```bash
# Automatically manages thread_id
./temp_tests/query_with_memory.sh "your question here"

# Start new conversation
rm .current_thread_id
```

### Option 2: Manual curl
```bash
THREAD_ID="my-session-$(date +%s)"

curl --location 'http://localhost:8000/query/form' \
  --form "input=\"your question\"" \
  --form 'config_path="config/python_exec_agent_working.yaml"' \
  --form 'raw_output="True"' \
  --form "thread_id=\"$THREAD_ID\""
```

## 📊 What's Working Now

- ✅ Conversation memory stores context
- ✅ Context injected into subsequent requests
- ✅ Agents use previous conversation data
- ✅ NO tool call protocol errors
- ✅ Multi-turn conversations stable

## 🔍 Verify It's Working

```bash
# Check conversation storage
ls -lt simple_memory/ | head -5

# View specific conversation
cat simple_memory/[thread-id].json | python -m json.tool

# Check config
grep 'backend:' config/python_exec_agent_working.yaml
# Should show: backend: "none"
```

## 🆘 If Issues Persist

1. **Restart API server** (to reload config)
   ```bash
   # Kill existing server
   pkill -f "python api.py"
   
   # Start fresh
   python api.py
   ```

2. **Clear conversation and retry**
   ```bash
   rm .current_thread_id
   ./temp_tests/query_with_memory.sh "test message"
   ```

3. **Verify config change**
   ```bash
   grep -A 2 'memory:' config/python_exec_agent_working.yaml
   # Should show: backend: "none"
   ```

## 📁 Related Files

- **Config**: `config/python_exec_agent_working.yaml` (modified)
- **Helper**: `temp_tests/query_with_memory.sh`
- **Verification**: `temp_tests/verify_conversation_memory_fix.sh`
- **Documentation**: `temp_docs/CONVERSATION_MEMORY_FINAL_FIX.md`

## 🎯 Key Takeaway

**Use ONE memory system at a time**:
- ✅ Simple conversation_memory (text-based) - RECOMMENDED
- ❌ ChromaDB checkpointer + conversation_memory - CAUSES CONFLICTS
