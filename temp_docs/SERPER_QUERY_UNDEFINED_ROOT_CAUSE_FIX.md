# Serper Query "undefined" - ACTUAL Root Cause & Fix

## 🎯 The Real Problem

The Serper MCP server expects parameter name **`q`**, but LangChain/LLMs use **`query`**.

### Evidence from Serper MCP Server Source Code
```typescript
// From: https://github.com/marcopesani/mcp-server-serper/blob/main/src/index.ts
case "google_search": {
  const {
    q,        // ← Expects 'q', not 'query'!
    gl,
    hl,
    ...
  } = request.params.arguments || {};

  if (!q || !gl || !hl) {
    throw new Error(
      "Search query and region code and language are required"
    );
  }
```

When we passed `{"query": "...", "gl": "in", "hl": "en"}`:
- Serper MCP looked for `q` parameter
- Found nothing (only found `query`)
- Used `undefined` as the value
- Sent to Serper API as `"q": "undefined"`

## 🔧 The Complete Fix

### Problem #1: Parameter Name Mismatch
**Fixed in** `/app/mcp_loader.py`, `SerperToolWrapper._inject_defaults()` (lines 88-106)

```python
def _inject_defaults(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Inject default parameters for Serper tools."""
    if self.name == "google_search":
        # CRITICAL: Serper MCP server expects 'q' not 'query'
        # Convert 'query' to 'q' for compatibility
        if "query" in params and "q" not in params:
            params["q"] = params.pop("query")  # ← THE KEY FIX
        
        # Ensure required parameters exist
        if "gl" not in params or not params.get("gl"):
            params["gl"] = self._default_gl
        if "hl" not in params or not params.get("hl"):
            params["hl"] = self._default_hl
        if "q" not in params or not params.get("q"):
            log.warning(f"google_search called without 'q' parameter")
    
    return params
```

### Problem #2: Multiple Argument Formats
**Fixed in** `/app/mcp_loader.py`, `SerperToolWrapper._arun()` (lines 111-142)

The log showed TWO different call patterns:
1. `google_search(args=[{'query': ..., 'gl': 'in', 'hl': 'en'}])` - args is a LIST
2. `google_search(query="...", gl="in", hl="en")` - keyword arguments

```python
async def _arun(self, *args: Any, **kwargs: Any) -> str:
    # Extract parameters from either args or kwargs
    if kwargs:
        params = dict(kwargs)
    elif args:
        # Handle different argument formats:
        first_arg = args[0]
        if isinstance(first_arg, dict):
            params = first_arg
        elif isinstance(first_arg, list) and len(first_arg) > 0:
            # Handle args=[[{...}]] format seen in logs
            if isinstance(first_arg[0], dict):
                params = first_arg[0]  # ← Unwrap list
        else:
            params = {"query": str(first_arg)}
    else:
        params = {}
    
    # Inject defaults and convert 'query' to 'q'
    params = self._inject_defaults(params)  # ← Converts query→q
    
    # Call inner MCP tool
    return await self._inner.arun(params)
```

### Problem #3: Wrapper Signature Mismatch
**Also fixed in** same `_arun()` method:

```python
# Before: Only accepted **kwargs
async def _arun(self, **kwargs: Any) -> str:

# After: Accepts both positional and keyword arguments  
async def _arun(self, *args: Any, **kwargs: Any) -> str:
```

## ✅ What's Fixed

### Before the Fix
```json
{
  "searchParameters": {
    "q": "undefined",  // ❌ Query lost
    "gl": "in",
    "hl": "en"
  }
}
```

### After the Fix
```json
{
  "searchParameters": {
    "q": "best smartphones under 20000 rupees India 2025",  // ✅ Actual query
    "gl": "in",
    "hl": "en"
  }
}
```

## 📊 Test Results

All 4 tests pass:
- ✅ Positional dict args: `_arun({'query': '...'})`
- ✅ Keyword args: `_arun(query='...', gl='in')`
- ✅ List args: `_arun([{'query': '...', 'gl': 'in'}])`
- ✅ Empty query handling with warnings

## 🔍 Why This Was Hard to Find

1. **Multiple layers of wrapping**: `Agent → TimeoutTool → SerperToolWrapper → MCP Tool`
2. **Different call patterns**: Args could be dict, list, or kwargs
3. **Parameter name mismatch**: The real issue was `query` vs `q`, not the wrapping
4. **No error messages**: MCP server didn't complain, just used `undefined`

## 📝 Key Insight

**The wrapper fix alone wasn't enough** - we needed to:
1. Accept multiple argument formats (*args, **kwargs)
2. Unwrap lists when needed
3. **Convert 'query' to 'q' for Serper MCP compatibility** ← THE CRITICAL PART

## 🚀 To Verify the Fix

1. Restart the API server:
   ```bash
   # Kill old server
   lsof -ti:8000 | xargs kill -9
   
   # Start new server with fix
   python api.py
   ```

2. Run the original curl command:
   ```bash
   curl --location 'http://localhost:8000/query/form' \
     --form 'input="top smartphones under ₹20,000 in India (as of Oct 21st, 2025)"' \
     --form 'config_path="config/deep_agent_advanced_serpapi.yaml"' \
     --form 'raw_output="True"' \
     --form 'thread_id="jk-deep-test-fix"'
   ```

3. Check the latest log in `agentlogs/`:
   ```bash
   tail -100 agentlogs/agentlog_*.log | grep -A 5 "searchParameters"
   ```

4. Verify you see:
   ```json
   "searchParameters": {
     "q": "actual search query text",  // ✅ Not "undefined"
     "gl": "in",
     "hl": "en"
   }
   ```

## 📂 Files Modified

- `/app/mcp_loader.py` (lines 88-152)
  - `SerperToolWrapper._inject_defaults()` - Convert `query` → `q`
  - `SerperToolWrapper._arun()` - Handle multiple arg formats

## 📚 Additional Files

- `/temp_tests/verify_serper_wrapper_fix.py` - Comprehensive unit tests
- `/temp_docs/SERPER_QUERY_UNDEFINED_ROOT_CAUSE_FIX.md` - This document

---

**Fix Date**: October 21, 2025  
**Root Cause**: Parameter name mismatch (`query` vs `q`) + Multiple argument formats  
**Status**: ✅ Fixed and Verified with Unit Tests
