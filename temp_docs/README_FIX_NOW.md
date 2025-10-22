# 🚨 URGENT: Fix Serper API 403 Error - DO THIS NOW

## Problem
Your query is failing with: **403 Forbidden - Unauthorized**

```
Serper API error: 403 Forbidden - {"message":"Unauthorized.","statusCode":403}
```

## Root Cause
**Invalid SERPER_API_KEY in your `.env` file**

---

## ⚡ QUICK FIX (5 Minutes)

### Step 1: Get a Valid Key (3 min)

1. Open browser: **https://serper.dev**
2. Click "Sign Up" (free, no credit card)
3. Verify email
4. Go to Dashboard
5. **Copy your API key** (looks like: `a1b2c3d4e5f6...`)

### Step 2: Update .env File (1 min)

Open this file in your editor:
```
/Users/A80997271/Documents/projects/jk-agents-core/.env
```

Find this line:
```bash
SERPER_API_KEY=your-serper-api-key-here
```

Replace with YOUR key:
```bash
SERPER_API_KEY=paste_your_actual_key_here
```

**Save the file!**

### Step 3: Restart Your Server (30 sec)

In your terminal:
```bash
# Press Ctrl+C to stop current server

# Then restart:
cd /Users/A80997271/Documents/projects/jk-agents-core
source .venv/bin/activate
python api.py
```

### Step 4: Test Again (30 sec)

Run your original command:
```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="research on mcp server as of now"' \
--form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-deep-pep-003"'
```

**Expected**: Should work now! ✅

---

## 🧪 Verify Your Fix

After updating the key, run:

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
bash temp_tests/verify_fix_complete.sh
```

This will test everything automatically.

---

## 🆘 Still Not Working?

### Test your key manually:

```bash
# Replace YOUR_KEY_HERE with your actual key from .env
curl -X POST 'https://google.serper.dev/search' \
  -H 'X-API-KEY: YOUR_KEY_HERE' \
  -H 'Content-Type: application/json' \
  -d '{"q":"test","num":1}'
```

**If you get HTTP 200**: Key is valid ✅  
**If you get HTTP 403**: Key is wrong ❌ (get new one)

---

## 📁 Files Created for You

1. **`temp_tests/verify_fix_complete.sh`** - Automated verification
2. **`temp_tests/verify_serper_key.py`** - Python test script
3. **`temp_docs/SERPER_API_KEY_FIX.md`** - Detailed documentation
4. **`temp_docs/IMMEDIATE_ACTION_PLAN.md`** - Step-by-step guide
5. **`temp_docs/FIX_COMPLETE_SUMMARY.md`** - Technical details

---

## ✅ Checklist

- [ ] Got valid key from https://serper.dev
- [ ] Updated `.env` file with new key
- [ ] Saved `.env` file
- [ ] Restarted API server
- [ ] Re-ran the query
- [ ] Verified it works (no 403 errors)

---

## 🎯 What Success Looks Like

**Before (Current - Broken):**
```
ERROR:mcp_loader:Tool google_search failed
Serper API error: 403 Forbidden
RuntimeError: Step s1 failed
```

**After (Fixed):**
```
INFO:mcp_loader:Loaded 2 tools from MCP servers: google_search, scrape
INFO:planner_executor:Worker s1 completed successfully
[Research results returned successfully]
```

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `bash temp_tests/verify_fix_complete.sh` | Verify everything works |
| `grep SERPER_API_KEY .env` | Check current key |
| `python api.py` | Start API server |

---

**TIME TO FIX**: 5 minutes  
**DIFFICULTY**: Easy  
**PRIORITY**: High (blocking all research queries)

👉 **DO THIS NOW** - Your queries will work immediately after!
