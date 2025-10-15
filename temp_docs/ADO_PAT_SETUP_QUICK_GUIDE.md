# Azure DevOps PAT Token - Quick Setup Guide

**Problem Solved:** MCP server no longer asks for login repeatedly  
**Solution:** Environment variable expansion now works correctly

---

## Quick Setup (3 Steps)

### Step 1: Get Your PAT Token

Visit: https://dev.azure.com/PepsiCoIT/_usersSettings/tokens

- Click "New Token"
- Name: `jk-agents-readonly`
- Scopes: **Work Items (Read)**, **Code (Read)**, **Build (Read)**, **Wiki (Read)**
- Copy the token immediately

### Step 2: Set Environment Variable

```bash
# Add to your .env file
echo "AZURE_DEVOPS_EXT_PAT=your-actual-pat-token-here" >> .env

# Or export in current shell
export AZURE_DEVOPS_EXT_PAT="your-actual-pat-token-here"
```

### Step 3: Verify It Works

```bash
# Test environment variable expansion
python temp_tests/verify_env_expansion.py

# Run ADO integration tests
cd integration_tests
pytest test_07_mcp_ado_tools.py::TestMCPAzureDevOpsTools::test_simple_workitem_search -v -s
```

---

## What Was Fixed

### Before
```yaml
# In config/ado_working_v1.yaml
env:
  AZURE_DEVOPS_EXT_PAT: "${AZURE_DEVOPS_EXT_PAT}"  # ❌ Not expanded
```

**Result:** MCP server received literal string `"${AZURE_DEVOPS_EXT_PAT}"` → asked for login

### After
```yaml
# Same config, but now with expansion
env:
  AZURE_DEVOPS_EXT_PAT: "${AZURE_DEVOPS_EXT_PAT}"  # ✅ Expanded to actual token
```

**Result:** MCP server receives actual PAT token → authenticated automatically

---

## Verification Checklist

✅ **Environment variable set**
```bash
echo $AZURE_DEVOPS_EXT_PAT
# Should output your token (not empty)
```

✅ **Expansion working**
```bash
python temp_tests/verify_env_expansion.py
# Should show: ✓ ALL TESTS PASSED
```

✅ **MCP tests passing**
```bash
cd integration_tests
pytest test_07_mcp_ado_tools.py -v
# Should show: 10 passed
```

---

## Troubleshooting

### Still asking for login?

1. **Check variable is set:**
   ```bash
   env | grep AZURE_DEVOPS_EXT_PAT
   ```

2. **Test token manually:**
   ```bash
   curl -u :$AZURE_DEVOPS_EXT_PAT \
     "https://dev.azure.com/PepsiCoIT/_apis/projects?api-version=7.0"
   ```

3. **Check token hasn't expired:**
   - Go to: https://dev.azure.com/PepsiCoIT/_usersSettings/tokens
   - Verify token is still active

### Token expansion not working?

Run debug test:
```bash
python temp_tests/verify_env_expansion.py
```

If this passes but tests still fail, check the token has correct permissions.

---

## Files Modified

1. **app/mcp_loader.py** - Added `_expand_env_vars()` function
2. **.env.example** - Added `AZURE_DEVOPS_EXT_PAT` documentation
3. **config/ado_working_v1.yaml** - Fixed memory backend (already done)

---

## Next Steps

Once your PAT token is set:

1. ✅ Run verification: `python temp_tests/verify_env_expansion.py`
2. ✅ Run ADO tests: `pytest integration_tests/test_07_mcp_ado_tools.py -v`
3. ✅ All should pass without login prompts

---

**Status:** Ready to use!
