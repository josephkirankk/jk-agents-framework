# Immediate Action Plan - Fix Serper API 403 Error

## Quick Summary

**Problem**: Serper API returning 403 Forbidden (Unauthorized)  
**Cause**: Invalid or expired `SERPER_API_KEY` in `.env` file  
**Fix Time**: ~5 minutes

---

## STEP-BY-STEP FIX (Manual)

### Step 1: Check Current Key (30 seconds)

Open your `.env` file and look for:
```bash
SERPER_API_KEY=...
```

**If it says**: `SERPER_API_KEY=your-serper-api-key-here`  
→ This is the placeholder, you need a real key

**If it's a real key** (32 alphanumeric characters):  
→ It's expired or invalid, you need a new one

### Step 2: Get New API Key (3 minutes)

1. Go to: **https://serper.dev**
2. Click "Sign Up" or "Log In"
3. Complete registration (email + password)
4. Go to Dashboard
5. Copy your API key (will look like: `407c1d047c5e8f9a2b3d4e5f6a7b8c9d`)

**Important**: Free tier gives you 2,500 searches/month - no credit card needed!

### Step 3: Update .env File (1 minute)

Open `.env` in your project root:

**Before:**
```bash
SERPER_API_KEY=your-serper-api-key-here
```

**After:**
```bash
SERPER_API_KEY=407c1d047c5e8f9a2b3d4e5f6a7b8c9d
```

**Replace with YOUR actual key from serper.dev!**

⚠️ **Common Mistakes to Avoid**:
- Don't add quotes: ~~`SERPER_API_KEY="..."`~~
- Don't add spaces: ~~`SERPER_API_KEY = ...`~~
- Don't use placeholder: ~~`your-serper-api-key-here`~~

### Step 4: Test the Key (30 seconds)

Run this in terminal:

```bash
cd /Users/A80997271/Documents/projects/jk-agents-core

# Test with curl
curl -X POST 'https://google.serper.dev/search' \
  -H 'X-API-KEY: YOUR_KEY_HERE' \
  -H 'Content-Type: application/json' \
  -d '{"q": "test", "num": 1}'
```

**Expected**: HTTP 200 with JSON results  
**If 403**: Key is still wrong, go back to Step 2

### Step 5: Restart API Server (30 seconds)

```bash
# Stop current server (Ctrl+C)
# Then restart:
cd /Users/A80997271/Documents/projects/jk-agents-core
source .venv/bin/activate
python api.py
```

### Step 6: Re-run Your Query (30 seconds)

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="research on mcp server as of now"' \
--form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-deep-pep-003"'
```

**Expected**: Successful research results, no 403 errors

---

## Alternative: Use Different Search (Faster)

If you don't want to sign up for Serper, use Brave Search instead:

```bash
# Make sure BRAVE_API_KEY is set in .env first
curl --location 'http://localhost:8000/query/form' \
--form 'input="research on mcp server as of now"' \
--form 'config_path="config/brave-research.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-deep-pep-003"'
```

---

## Automated Testing Scripts

### Option 1: Shell Script
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
./temp_tests/test_serper_api.sh
```

### Option 2: Python Script
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
source .venv/bin/activate
python temp_tests/verify_serper_key.py
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] ✓ `.env` file has real Serper API key (not placeholder)
- [ ] ✓ Key is 32 characters, alphanumeric
- [ ] ✓ Curl test returns HTTP 200 (not 403)
- [ ] ✓ API server restarted
- [ ] ✓ Query runs without errors
- [ ] ✓ Research results returned successfully

---

## Expected Log Output (Success)

After fix, you should see:

```
INFO:mcp_loader:Loaded 2 tools from MCP servers: google_search, scrape
INFO:agent_builder:Built agent research_orchestrator with 2 tools
INFO:planner_executor:Worker s1 attempt 1: ainvoke start (timeout=300s)
INFO:deep_agent_adapter:DeepAgent 'research_orchestrator' invoked successfully
```

**No more**: `ERROR:mcp_loader:Tool google_search failed`  
**No more**: `Serper API error: 403 Forbidden`

---

## Troubleshooting

### Issue: "Still getting 403 after updating"

**Solution**:
1. Double-check `.env` file saved correctly
2. Verify no typos in key
3. Restart API server (important!)
4. Test key with curl directly
5. Check serper.dev dashboard for key status

### Issue: "Key works in curl but not in app"

**Solution**:
1. Make sure `.env` is in project root
2. Check for multiple `.env` files
3. Verify server picks up environment variables
4. Check logs for actual key being used (first 10 chars)

### Issue: "How do I know my key is valid?"

**Test with curl**:
```bash
# Replace YOUR_KEY with actual key
curl -X POST 'https://google.serper.dev/search' \
  -H 'X-API-KEY: YOUR_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"q": "test", "num": 1}'
```

- HTTP 200 = Valid key ✅
- HTTP 403 = Invalid key ❌
- HTTP 429 = Valid but rate limited ⚠️

---

## Need Help?

1. **Serper API Key Issues**: https://serper.dev/dashboard
2. **Check logs**: `/Users/A80997271/Documents/projects/jk-agents-core/agentlogs/`
3. **Documentation**: `temp_docs/SERPER_API_KEY_FIX.md`

---

**Status**: Fix ready for implementation  
**Estimated Time**: 5 minutes  
**Difficulty**: Easy
