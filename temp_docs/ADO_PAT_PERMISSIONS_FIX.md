# Azure DevOps PAT Token Permissions Fix

## Executive Summary

**Status**: ✅ PAT token authentication mechanism is working correctly  
**Issue**: ❌ PAT token lacks required Azure DevOps permissions  
**Error**: `TF400813: The user is not authorized to access this resource`

## Root Cause Analysis

### What Works ✅
1. ✅ `.env` file is loaded correctly
2. ✅ `AZURE_DEVOPS_EXT_PAT` environment variable is set
3. ✅ PAT token is passed to subprocess correctly
4. ✅ MCP server starts successfully with PAT authentication
5. ✅ 64 Azure DevOps tools are loaded
6. ✅ PAT token is being used for authentication (not Azure CLI)

### What Doesn't Work ❌
When tools are invoked, Azure DevOps API returns:
```
Error fetching projects: TF400813: The user 'c8ba2cff-089f-651c-92dc-de93f7f49f54' 
is not authorized to access this resource.
```

This is **NOT** an authentication error - the PAT token authenticated successfully. This is an **authorization error** - the token's permissions are insufficient.

## Diagnostic Evidence

### Test Results
Ran comprehensive diagnostic tests:
```bash
✅ PASS: env_file
✅ PASS: pat_in_env
✅ PASS: node_npx
✅ PASS: ado_package
✅ PASS: subprocess_env
✅ PASS: mcp_with_env
✅ PASS: mcp_loader
```

### Tool Invocation Test
```bash
✓ Loaded 64 tools
✓ Testing tool: core_list_projects
❌ Tool invocation failed: TF400813: The user is not authorized
```

The error `TF400813` specifically indicates **authorization** (permissions) not **authentication** (identity).

## Solution

### Option 1: Regenerate PAT Token with Correct Permissions ✅ RECOMMENDED

1. **Navigate to Azure DevOps Personal Access Tokens**:
   - Go to: https://dev.azure.com/PepsiCoIT/_usersSettings/tokens
   - Or: Click on your profile → Security → Personal access tokens

2. **Create New Token or Update Existing Token**:
   - Click "New Token" or edit the existing token
   - Name: `jk-agents-core-integration-tests`
   - Organization: `PepsiCoIT`
   - **Expiration**: Choose appropriate duration (recommend: 90 days minimum)

3. **Required Permissions (READ-ONLY)**:
   Select these scopes with **READ** permissions:
   
   | Scope | Permission | Required |
   |-------|-----------|----------|
   | **Work Items** | Read | ✅ Critical |
   | **Code** | Read | ✅ Critical |
   | **Build** | Read | ✅ Critical |
   | **Release** | Read | ✅ Critical |
   | **Project and Team** | Read | ✅ Critical |
   | **Graph** | Read | ⚠️ Optional (for user identity resolution) |
   | **Wiki** | Read | ⚠️ Optional (for wiki queries) |
   | **Test Management** | Read | ⚠️ Optional (for test plans) |

4. **Copy the Token**:
   - Copy the generated token (you'll only see it once!)
   - Update `.env` file:
     ```bash
     AZURE_DEVOPS_EXT_PAT=your-new-pat-token-here
     ```

5. **Verify Token Works**:
   ```bash
   source .venv/bin/activate
   python temp_tests/test_ado_tool_invoke.py
   ```

### Option 2: Grant User Permissions in Azure DevOps

If you want to keep the same PAT token, grant the user additional permissions:

1. **Identify User**: 
   - User ID: `c8ba2cff-089f-651c-92dc-de93f7f49f54`

2. **Grant Project Access**:
   - Go to Project Settings → Teams
   - Add user to appropriate team with Reader permissions

3. **Verify Organization Permissions**:
   - Go to Organization Settings → Users
   - Ensure user has "Basic" or higher access level

## Technical Details

### How PAT Token is Passed to MCP Server

1. **Environment Loading** (`conftest.py`):
   ```python
   from dotenv import load_dotenv
   load_dotenv(dotenv_path=env_path, override=True)
   ```

2. **Environment Expansion** (`mcp_loader.py` lines 204-232):
   ```python
   def _expand_env_vars(env_dict: Dict[str, str]) -> Dict[str, str]:
       # Expands ${AZURE_DEVOPS_EXT_PAT} to actual token value
   ```

3. **Environment Merging** (`mcp_loader.py` lines 262-301):
   ```python
   # Merge with current process environment
   merged_env = os.environ.copy()
   merged_env.update(expanded_env)
   
   # Pass to MCP subprocess
   client_cfg[name] = {
       "transport": "stdio",
       "command": "npx",
       "args": ["-y", "@azure-devops/mcp", "PepsiCoIT", "-a", "env"],
       "env": merged_env,  # ← PAT token included here
   }
   ```

4. **ADO MCP Server** receives environment and uses PAT token for authentication:
   ```bash
   npx -y @azure-devops/mcp PepsiCoIT -a env
   ```
   The `-a env` flag tells it to use `AZURE_DEVOPS_EXT_PAT` from environment.

### Why Tests Appear to "Pass" But Don't Work

The integration tests have graceful error handling:

```python
# In ado_working_v1.yaml
ERROR HANDLING:
If a tool call returns an error:
- Authentication errors → "Please ensure you're logged in with 'az login'..."
```

When a tool fails with authorization error, the LLM agent catches it and returns a friendly message instead of crashing. This makes tests "pass" but return unhelpful responses.

## Verification Steps

After fixing the PAT token permissions:

### 1. Run Diagnostic Tests
```bash
source .venv/bin/activate
python temp_tests/diagnose_ado_auth.py
```
Expected: All tests should pass ✅

### 2. Run Tool Invocation Test
```bash
source .venv/bin/activate
python temp_tests/test_ado_tool_invoke.py
```
Expected: Tool invocation succeeds with project data ✅

### 3. Run Integration Tests
```bash
source .venv/bin/activate
pytest integration_tests/test_01_ado_mcp_connection.py -v -s
pytest integration_tests/test_07_mcp_ado_tools.py::TestMCPAzureDevOpsTools::test_simple_workitem_search -v -s
```
Expected: Tests pass with actual Azure DevOps data ✅

## Common Pitfalls

### ❌ Mistake 1: Thinking It's an Authentication Issue
**Symptom**: "Please ensure you're logged in with 'az login'"  
**Reality**: PAT token authenticated successfully, but lacks permissions  
**Fix**: Update PAT token permissions, not authentication method

### ❌ Mistake 2: Using Azure CLI Instead
**Symptom**: Tests prompt for browser login  
**Reality**: PAT token is the correct method for automation  
**Fix**: Ensure `-a env` flag is used and PAT token is set

### ❌ Mistake 3: Expired PAT Token
**Symptom**: Authentication errors  
**Reality**: PAT tokens expire after set duration  
**Fix**: Regenerate token with longer expiration

### ❌ Mistake 4: Wrong Organization Name
**Symptom**: 404 or organization not found errors  
**Reality**: Organization must match exactly  
**Fix**: Verify organization is `PepsiCoIT` (case-sensitive)

## Testing Checklist

- [ ] PAT token generated with all required READ permissions
- [ ] PAT token copied to `.env` file
- [ ] `.env` file is in project root (not in `.gitignore`)
- [ ] Virtual environment activated
- [ ] Node.js 20+ installed
- [ ] Diagnostic tests all pass
- [ ] Tool invocation test succeeds
- [ ] Integration tests return actual Azure DevOps data

## Files Modified/Created

| File | Purpose | Status |
|------|---------|--------|
| `temp_tests/diagnose_ado_auth.py` | Comprehensive diagnostic tool | ✅ Created |
| `temp_tests/test_ado_tool_invoke.py` | Tool invocation test | ✅ Created |
| `temp_docs/ADO_PAT_PERMISSIONS_FIX.md` | This document | ✅ Created |
| `.env` | Environment variables | ⚠️ Needs PAT token update |

## Next Steps

1. **Immediate**: Update PAT token in `.env` with correct permissions
2. **Verify**: Run diagnostic and invocation tests
3. **Test**: Run full integration test suite
4. **Document**: Update README with PAT token setup instructions
5. **Monitor**: Set calendar reminder for PAT token expiration

## References

- Azure DevOps PAT Token Documentation: https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate
- Azure DevOps MCP Server: https://github.com/microsoft/azure-devops-mcp
- Error Code TF400813: https://learn.microsoft.com/en-us/azure/devops/organizations/security/permissions

---

**Created**: 2025-10-14  
**Status**: Ready for PAT token update  
**Impact**: High - Blocks ADO integration tests  
**Priority**: P0 - Critical path for testing
