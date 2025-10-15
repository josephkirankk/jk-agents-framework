# Azure DevOps PAT Token Issue - Complete Resolution Guide

## Issue Summary

**Problem**: Azure DevOps integration tests fail with authentication/authorization errors  
**Root Cause**: PAT token lacks required Azure DevOps permissions  
**Status**: ✅ Identified and documented with verification tools  
**Action Required**: User must update PAT token permissions in Azure DevOps

---

## Quick Fix (5 minutes)

1. **Go to Azure DevOps Personal Access Tokens**:
   ```
   https://dev.azure.com/PepsiCoIT/_usersSettings/tokens
   ```

2. **Create New Token with These Permissions**:
   - ✅ Project and Team: **Read**
   - ✅ Work Items: **Read** 
   - ✅ Code: **Read**
   - ✅ Build: **Read**
   - ✅ Release: **Read**

3. **Update .env File**:
   ```bash
   AZURE_DEVOPS_EXT_PAT=your-new-token-here
   ```

4. **Verify It Works**:
   ```bash
   source .venv/bin/activate
   python temp_tests/check_pat_permissions.py
   ```

---

## Detailed Analysis

### What Was Wrong ❌

The PAT token authentication mechanism was working perfectly, but the token itself didn't have the required Azure DevOps permissions.

**Error Message**:
```
TF400813: The user 'c8ba2cff-089f-651c-92dc-de93f7f49f54' is not authorized to access this resource.
```

This error code `TF400813` specifically indicates **authorization failure** (permissions), not authentication failure (identity).

### What Was Not Wrong ✅

The investigation confirmed these components work correctly:

1. ✅ `.env` file loading (`dotenv` library)
2. ✅ Environment variable expansion (`${AZURE_DEVOPS_EXT_PAT}`)
3. ✅ Subprocess environment passing (`os.environ.copy()`)
4. ✅ MCP server initialization (`npx @azure-devops/mcp`)
5. ✅ PAT token authentication (`-a env` flag)
6. ✅ Tool loading (64 Azure DevOps tools loaded)

**The code is working perfectly** - it's a configuration/permission issue with the PAT token itself.

---

## Verification Tools Created

### 1. Comprehensive Diagnostic Tool
**File**: `temp_tests/diagnose_ado_auth.py`

Tests every step of the authentication chain:
- Environment file loading
- PAT token presence
- Node.js/npx availability  
- Azure DevOps MCP package
- Subprocess environment passing
- MCP server startup
- Tool loading

**Usage**:
```bash
python temp_tests/diagnose_ado_auth.py
```

### 2. Tool Invocation Test
**File**: `temp_tests/test_ado_tool_invoke.py`

Actually invokes an Azure DevOps tool to verify end-to-end authentication.

**Usage**:
```bash
python temp_tests/test_ado_tool_invoke.py
```

### 3. Permission Checker
**File**: `temp_tests/check_pat_permissions.py`

Tests specific PAT token permissions and reports which are missing.

**Usage**:
```bash
python temp_tests/check_pat_permissions.py
```

**Sample Output**:
```
Testing: Project and Team (Read)
  ❌ FAILED: Permission denied

Your PAT token is missing required permissions.
To fix this:
  1. Go to: https://dev.azure.com/PepsiCoIT/_usersSettings/tokens
  2. Create new token with required scopes
  3. Update .env file
```

---

## How PAT Token Authentication Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Python Process Starts                                    │
│    └─> loads .env file                                      │
│        └─> AZURE_DEVOPS_EXT_PAT=<token>                    │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. MCP Loader (mcp_loader.py)                              │
│    └─> Expands ${AZURE_DEVOPS_EXT_PAT}                     │
│    └─> Merges with os.environ                               │
│    └─> Creates subprocess environment                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Subprocess: npx @azure-devops/mcp PepsiCoIT -a env      │
│    └─> Receives AZURE_DEVOPS_EXT_PAT in environment        │
│    └─> Uses PAT for Azure DevOps API authentication        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Azure DevOps API                                         │
│    └─> Authenticates user via PAT token ✅                  │
│    └─> Checks user permissions ❌ FAILED                    │
│    └─> Returns TF400813 error                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Code Locations

1. **Environment Loading** (`integration_tests/conftest.py:27-31`):
   ```python
   from dotenv import load_dotenv
   load_dotenv(dotenv_path=env_path, override=True)
   ```

2. **Variable Expansion** (`app/mcp_loader.py:204-232`):
   ```python
   def _expand_env_vars(env_dict: Dict[str, str]) -> Dict[str, str]:
       expanded_value = re.sub(r'\$\{([^}]+)\}', replace_var, value)
   ```

3. **Environment Merging** (`app/mcp_loader.py:262-301`):
   ```python
   merged_env = os.environ.copy()
   merged_env.update(expanded_env)
   
   client_cfg[name] = {
       "env": merged_env,  # PAT token included
   }
   ```

4. **MCP Server Config** (`config/ado_working_v1.yaml:173`):
   ```yaml
   args: ["-y", "@azure-devops/mcp", "PepsiCoIT", "-d", "core", ..., "-a", "env"]
   env:
     AZURE_DEVOPS_EXT_PAT: "${AZURE_DEVOPS_EXT_PAT}"
   ```

---

## Required PAT Token Permissions

### Critical (Must Have) ✅

| Scope | Permission | Why Needed |
|-------|-----------|------------|
| **Project and Team** | Read | List projects, teams, and organizational structure |
| **Work Items** | Read | Query work items, features, epics, user stories |
| **Code** | Read | Access repositories, branches, pull requests |
| **Build** | Read | View build pipelines, definitions, and run history |
| **Release** | Read | View release pipelines and deployment history |

### Optional (Recommended) ⚠️

| Scope | Permission | Why Needed |
|-------|-----------|------------|
| **Graph** | Read | Resolve user identities and group memberships |
| **Wiki** | Read | Access wiki pages and documentation |
| **Test Management** | Read | View test plans, suites, and results |

### Not Needed ❌

- Any **Write**, **Create**, **Update**, or **Delete** permissions
- **Full Access** scope
- **Manage** permissions

**The application is READ-ONLY** - only read permissions are required.

---

## Common Errors and Solutions

### Error: TF400813 - User not authorized

**Symptom**:
```
Error: TF400813: The user is not authorized to access this resource
```

**Cause**: PAT token lacks required permissions

**Solution**: 
1. Regenerate PAT token with required scopes
2. Or grant user permissions in Azure DevOps project settings

---

### Error: "Please ensure you're logged in with 'az login'"

**Symptom**: Agent returns this message despite PAT token being set

**Cause**: This is the agent's generic error message for authentication/authorization failures

**Reality**: PAT token is being used (not Azure CLI), but lacks permissions

**Solution**: Update PAT token permissions, not authentication method

---

### Error: MCP server hangs or times out

**Symptom**: Test hangs for 10+ seconds then times out

**Cause**: 
- PAT token not set (opens browser for interactive auth)
- PAT token is a placeholder

**Solution**:
```bash
# Check if PAT is set
python -c "import os; print(os.getenv('AZURE_DEVOPS_EXT_PAT'))"

# If blank or placeholder, update .env file
```

---

### Error: "Cannot be called from a running event loop"

**Symptom**: `RuntimeError: asyncio.run() cannot be called from a running event loop`

**Cause**: Incorrect async usage in diagnostic scripts (now fixed)

**Solution**: Use `await` instead of `asyncio.run()` in async context

---

## Testing Workflow

### Step 1: Basic Environment Check
```bash
source .venv/bin/activate

# Check PAT token is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('PAT:', os.getenv('AZURE_DEVOPS_EXT_PAT')[:20] + '...')"
```

### Step 2: Run Comprehensive Diagnostics
```bash
python temp_tests/diagnose_ado_auth.py
```
**Expected**: All tests pass ✅

### Step 3: Check Permissions
```bash
python temp_tests/check_pat_permissions.py
```
**Expected**: "PAT TOKEN PERMISSIONS VERIFIED" ✅

### Step 4: Test Tool Invocation
```bash
python temp_tests/test_ado_tool_invoke.py
```
**Expected**: Tool returns actual Azure DevOps data ✅

### Step 5: Run Integration Tests
```bash
# Quick connection test
pytest integration_tests/test_01_ado_mcp_connection.py -v -s

# Full tool test
pytest integration_tests/test_07_mcp_ado_tools.py::TestMCPAzureDevOpsTools::test_simple_workitem_search -v -s
```
**Expected**: Tests pass with real data ✅

---

## Files Created/Modified

| File | Type | Purpose |
|------|------|---------|
| `temp_tests/diagnose_ado_auth.py` | Tool | Comprehensive authentication diagnostics |
| `temp_tests/test_ado_tool_invoke.py` | Tool | Test actual tool invocation |
| `temp_tests/check_pat_permissions.py` | Tool | Check PAT token permissions |
| `temp_docs/ADO_PAT_PERMISSIONS_FIX.md` | Doc | Detailed fix guide |
| `temp_docs/ADO_PAT_ISSUE_RESOLUTION.md` | Doc | This comprehensive guide |
| `.env` | Config | **Needs update with new PAT token** ⚠️ |

---

## Next Steps

### Immediate (User Action Required) 🔴

1. **Generate New PAT Token**:
   - Go to https://dev.azure.com/PepsiCoIT/_usersSettings/tokens
   - Create token with required read permissions
   - Copy token (shown only once!)

2. **Update .env File**:
   ```bash
   AZURE_DEVOPS_EXT_PAT=your-new-token-with-permissions
   ```

3. **Verify**:
   ```bash
   python temp_tests/check_pat_permissions.py
   ```

### Short Term (Optional) 🟡

1. Add PAT token expiration reminder to calendar
2. Document PAT token setup in team wiki
3. Create troubleshooting guide for team members
4. Consider using Azure Key Vault for token storage

### Long Term (Improvements) 🟢

1. Implement automatic token expiration checking
2. Add more detailed permission error messages
3. Create setup wizard for first-time configuration
4. Add health check endpoint for monitoring

---

## References

- **Azure DevOps REST API**: https://learn.microsoft.com/en-us/rest/api/azure/devops/
- **PAT Token Documentation**: https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate
- **Azure DevOps MCP Server**: https://github.com/microsoft/azure-devops-mcp
- **Error Code Reference**: https://learn.microsoft.com/en-us/azure/devops/reference/error/

---

## Lessons Learned

1. **Authentication ≠ Authorization**: Token can authenticate successfully but still lack permissions
2. **Test Granularly**: Test each component separately to isolate issues
3. **Clear Error Messages**: Generic errors hide root causes
4. **Diagnostic Tools**: Invest in good diagnostics upfront
5. **Documentation**: Clear docs prevent repeated issues

---

**Created**: 2025-10-14  
**Last Updated**: 2025-10-14  
**Status**: ✅ Issue identified and documented  
**Action Required**: User must update PAT token permissions  
**Estimated Time**: 5 minutes  
**Priority**: P0 - Blocks all ADO integration tests
