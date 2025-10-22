# Serper API Key 403 Forbidden - Fix Documentation

## Issue Summary

**Error**: `Serper API error: 403 Forbidden - {"message":"Unauthorized.","statusCode":403}`

**Location**: Deep Agent with Serper MCP Server (`config/deep_agent_advanced_serpapi.yaml`)

**Root Cause**: Invalid or expired SERPER_API_KEY in `.env` file

## Problem Details

The error occurs when the MCP server tries to use the Serper API for web search:

```
ERROR:mcp_loader:Tool google_search failed after 2 attempts. 
Last error: unhandled errors in a TaskGroup (1 sub-exception)
mcp.shared.exceptions.McpError: Search failed: Error: SearchTool: failed to search
Error: Serper API error: 403 Forbidden - {"message":"Unauthorized.","statusCode":403}
```

## Solution Steps

### Step 1: Get a Valid Serper API Key

1. Visit [https://serper.dev](https://serper.dev)
2. Sign up for a free account (no credit card required)
3. Navigate to your dashboard
4. Copy your API key

**Free Tier Benefits**:
- 2,500 free searches per month
- No credit card required
- Instant activation

### Step 2: Update Your .env File

Open your `.env` file in the project root and update:

```bash
# Old (invalid key)
SERPER_API_KEY=407c1d047c...

# New (your actual key from serper.dev)
SERPER_API_KEY=your_actual_key_from_serper_dev
```

**Important**: Make sure to:
- Remove any quotes around the key
- Ensure there are no spaces before or after the `=`
- The key should be a 32-character alphanumeric string

### Step 3: Verify the API Key

Run the verification script:

```bash
source .venv/bin/activate
python temp_tests/verify_serper_key.py
```

Or test manually with curl:

```bash
# Replace YOUR_KEY_HERE with your actual key
curl -X POST 'https://google.serper.dev/search' \
  -H 'X-API-KEY: YOUR_KEY_HERE' \
  -H 'Content-Type: application/json' \
  -d '{"q": "test query", "num": 1}'
```

**Expected Success Response**: HTTP 200 with search results
**Expected Failure Response**: HTTP 403 with "Unauthorized" message

### Step 4: Restart the API Server

After updating the `.env` file, restart your API server:

```bash
# Stop the current server (Ctrl+C if running)
# Then restart:
source .venv/bin/activate
python api.py
```

### Step 5: Test the Fixed Configuration

Re-run your original query:

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="research on mcp server as of now"' \
--form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-deep-pep-003"'
```

## Verification Checklist

- [ ] Obtained valid Serper API key from serper.dev
- [ ] Updated `.env` file with new key
- [ ] Verified key format (32 chars, no spaces/quotes)
- [ ] Tested key with curl or Python script
- [ ] Restarted API server
- [ ] Re-ran the failing query
- [ ] Confirmed successful search results

## Alternative: Use Different Search Provider

If you don't want to use Serper, you can switch to other search providers:

### Option 1: Brave Search

Update your config to use `brave-research.yaml` instead:

```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="research on mcp server as of now"' \
--form 'config_path="config/brave-research.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="jk-deep-pep-003"'
```

Requires: `BRAVE_API_KEY` in `.env` file

### Option 2: Use a Different MCP Server

Modify the config file to use a different MCP search server that doesn't require Serper.

## Common Mistakes

1. **Using placeholder key**: `SERPER_API_KEY=your-serper-api-key-here`
   - **Fix**: Replace with actual key from serper.dev

2. **Expired key**: Keys can expire if unused for extended periods
   - **Fix**: Generate a new key from your serper.dev dashboard

3. **Incorrect key format**: Extra spaces, quotes, or partial key
   - **Fix**: Ensure exact format: `SERPER_API_KEY=32characterstring`

4. **Env not loaded**: Changes to `.env` not picked up
   - **Fix**: Restart the API server after `.env` changes

5. **Rate limit exceeded**: Too many requests
   - **Error**: HTTP 429 instead of 403
   - **Fix**: Wait or upgrade plan

## Troubleshooting

### Still getting 403 after updating key?

1. **Verify key is actually updated**:
   ```bash
   grep SERPER_API_KEY .env
   ```

2. **Check for .env.local or other env files**:
   ```bash
   find . -name ".env*" -type f
   ```

3. **Test key directly with curl** (see Step 3)

4. **Check server restart**: Make sure you restarted the Python API server

### Key works in curl but not in app?

1. **Clear any cached configs**: Delete cached agent configs if any
2. **Check env variable loading**: Ensure `.env` is in project root
3. **Verify MCP server config**: Check `config/deep_agent_advanced_serpapi.yaml` line 124

## Technical Details

### How the Key is Used

1. **Config file** (`deep_agent_advanced_serpapi.yaml`):
   ```yaml
   mcp_servers:
     serper-search:
       env:
         SERPER_API_KEY: "${SERPER_API_KEY}"
   ```

2. **MCP loader** reads from environment:
   ```python
   INFO:mcp_loader:MCP server 'serper-search' environment variables being set:
   INFO:mcp_loader:  SERPER_API_KEY: 407c1d047c...
   ```

3. **NPX runs MCP server** with env vars:
   ```bash
   npx -y serper-search-scrape-mcp-server
   ```

4. **MCP server calls Serper API**:
   ```javascript
   headers: { "X-API-KEY": process.env.SERPER_API_KEY }
   ```

## Prevention

- **Monitor key usage**: Check your serper.dev dashboard regularly
- **Set expiry alerts**: Configure notifications for key expiry
- **Document key source**: Keep track of where keys are obtained
- **Test after changes**: Always verify after updating keys

## Related Files

- `.env` - Environment variables (contains SERPER_API_KEY)
- `.env.example` - Template file with placeholder
- `config/deep_agent_advanced_serpapi.yaml` - Config using Serper
- `app/mcp_loader.py` - MCP server loader that reads env vars
- `temp_tests/verify_serper_key.py` - Verification script

## Status After Fix

Once fixed, you should see:
- ✅ Successful search results
- ✅ No 403 errors
- ✅ Proper research orchestration
- ✅ Subagents working correctly

---

**Last Updated**: 2025-01-20  
**Status**: Ready for implementation  
**Verification**: Pending API key update
