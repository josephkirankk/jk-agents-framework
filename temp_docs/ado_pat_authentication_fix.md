# Azure DevOps PAT Authentication Fix

## Problem
When running `pytest integration_tests/test_07_mcp_ado_tools.py`, the Azure DevOps MCP server was opening a browser for interactive authentication instead of using the PAT (Personal Access Token) from the `.env` file.

## Root Cause
The Azure DevOps MCP server (`@azure-devops/mcp`) defaults to `'interactive'` authentication mode, which opens a browser for OAuth authentication. The server needs to be explicitly configured to use environment variable authentication.

## Solution

### 1. Added Explicit .env Loading in Test File
**File**: `integration_tests/test_07_mcp_ado_tools.py`

Added explicit `.env` file loading at the top of the test file to ensure the `AZURE_DEVOPS_EXT_PAT` environment variable is available before any tests run:

```python
# Load .env file explicitly to ensure AZURE_DEVOPS_EXT_PAT is available
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Verify PAT token is loaded
ado_pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
if ado_pat:
    print(f"✓ Azure DevOps PAT token loaded (length: {len(ado_pat)})")
else:
    print("⚠ Warning: AZURE_DEVOPS_EXT_PAT not found in environment")
```

### 2. Updated MCP Server Configuration
**File**: `config/ado_working_v1.yaml`

Added the `-a env` flag to the Azure DevOps MCP server arguments to specify environment variable authentication:

**Before:**
```yaml
args: ["-y", "@azure-devops/mcp", "PepsiCoIT", "-d", "core", "work", "work-items", "repositories", "pipelines", "wiki", "search"]
```

**After:**
```yaml
args: ["-y", "@azure-devops/mcp", "PepsiCoIT", "-d", "core", "work", "work-items", "repositories", "pipelines", "wiki", "search", "-a", "env"]
```

### 3. Improved MCP Loader Logging
**File**: `app/mcp_loader.py`

- Increased default tool timeout from 30 seconds to 60 seconds for Azure DevOps API calls
- Increased default retries from 0 to 1
- Added INFO-level logging for environment variable verification
- Added special check to verify `AZURE_DEVOPS_EXT_PAT` is present in the merged environment

```python
async def load_mcp_tools(
    servers_cfg: Dict[str, Any],
    tool_timeout: float = 60.0,  # Increased from 30.0
    tool_retries: int = 1,        # Increased from 0
) -> Tuple[Optional[MultiServerMCPClient], List[BaseTool]]:
```

## Azure DevOps MCP Server Authentication Options

The `@azure-devops/mcp` server supports three authentication modes:

1. **`interactive`** (default): Opens a browser for OAuth authentication
2. **`azcli`**: Uses Azure CLI authentication (`az login`)
3. **`env`**: Uses environment variable `AZURE_DEVOPS_EXT_PAT`

To use environment variable authentication, you must:
- Set the `AZURE_DEVOPS_EXT_PAT` environment variable with your PAT token
- Add the `-a env` flag to the MCP server arguments

## Verification

A verification script was created to test the fix:

**File**: `temp_tests/verify_ado_pat.py`

This script:
1. Verifies the PAT token is loaded from `.env`
2. Checks the MCP server configuration includes `-a env`
3. Builds the agent and starts the MCP server
4. Confirms no browser opens during authentication

**Result**: ✅ SUCCESS - The MCP server uses PAT token authentication without opening a browser.

## Testing

Run the tests with:

```bash
# Single test
pytest integration_tests/test_07_mcp_ado_tools.py::TestMCPAzureDevOpsTools::test_simple_workitem_search -v -s

# All ADO tests
pytest integration_tests/test_07_mcp_ado_tools.py -v -s
```

## Environment Setup

Ensure your `.env` file contains:

```bash
AZURE_DEVOPS_EXT_PAT=your-pat-token-here
```

The PAT token should have READ permissions for:
- Work Items (read)
- Code (read)
- Build (read)
- Release (read)
- Test Management (read)
- Wiki (read)

## Files Modified

1. `integration_tests/test_07_mcp_ado_tools.py` - Added explicit .env loading
2. `config/ado_working_v1.yaml` - Added `-a env` authentication flag
3. `app/mcp_loader.py` - Increased timeouts and improved logging

## Files Created

1. `temp_tests/verify_ado_pat.py` - Verification script
2. `temp_docs/ado_pat_authentication_fix.md` - This documentation

## Summary

The fix ensures that:
- ✅ The `.env` file is loaded before tests run
- ✅ The `AZURE_DEVOPS_EXT_PAT` environment variable is available
- ✅ The Azure DevOps MCP server uses environment variable authentication (`-a env`)
- ✅ No browser opens during test execution
- ✅ Tests can run in CI/CD environments without interactive authentication
