# Azure DevOps Integration - Quick Setup Guide

## 🚨 Current Issue

**Your ADO integration tests are failing because the PAT token lacks required permissions.**

The authentication mechanism is working perfectly - it's just a permission configuration issue.

---

## ✅ 5-Minute Fix

### 1. Generate New PAT Token (2 minutes)

Go to: **https://dev.azure.com/PepsiCoIT/_usersSettings/tokens**

Click **"New Token"** and configure:

```
Name: jk-agents-integration-tests
Organization: PepsiCoIT
Expiration: 90 days (or longer)

Scopes (READ permissions only):
☑ Project and Team (Read)
☑ Work Items (Read)
☑ Code (Read)
☑ Build (Read)
☑ Release (Read)
☐ Graph (Read) - Optional
☐ Wiki (Read) - Optional
☐ Test Management (Read) - Optional
```

**Important**: Copy the token immediately - you won't see it again!

---

### 2. Update .env File (1 minute)

Open `.env` file in project root and update:

```bash
AZURE_DEVOPS_EXT_PAT=paste-your-new-token-here
```

Save the file.

---

### 3. Verify It Works (2 minutes)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run permission checker
python temp_tests/check_pat_permissions.py
```

**Expected Output**:
```
✅ PAT TOKEN PERMISSIONS VERIFIED
Your PAT token has all required permissions!
```

---

## 🧪 Run Tests

Once permissions are verified:

```bash
# Basic connection test
pytest integration_tests/test_01_ado_mcp_connection.py -v -s

# Full ADO tools test
pytest integration_tests/test_07_mcp_ado_tools.py -v -s
```

---

## 🛠️ Diagnostic Tools

If you encounter issues, use these diagnostic tools:

### Check Everything
```bash
python temp_tests/diagnose_ado_auth.py
```
Tests: env file, PAT token, Node.js, MCP package, subprocess, server startup, tool loading

### Check Permissions Only
```bash
python temp_tests/check_pat_permissions.py
```
Tests specific PAT token permissions and reports which are missing

### Test Tool Invocation
```bash
python temp_tests/test_ado_tool_invoke.py
```
Actually invokes an ADO tool to verify end-to-end authentication

---

## ❓ Common Issues

### "PAT token is a placeholder"
**Cause**: `.env` file has placeholder value  
**Fix**: Replace with actual token from Azure DevOps

### "Permission denied (TF400813)"
**Cause**: PAT token lacks required scopes  
**Fix**: Regenerate token with all required read permissions

### "MCP server times out"
**Cause**: PAT token not set or invalid  
**Fix**: Verify PAT token in `.env` file

### Tests pass but return "please login with az login"
**Cause**: PAT token lacks permissions, agent catches error gracefully  
**Fix**: Update PAT token permissions

---

## 📚 Detailed Documentation

For comprehensive technical details, see:
- `temp_docs/ADO_PAT_ISSUE_RESOLUTION.md` - Complete analysis and resolution guide
- `temp_docs/ADO_PAT_PERMISSIONS_FIX.md` - Detailed permission fix instructions

---

## ✨ What's Working

The investigation confirmed these components work correctly:

✅ Environment file loading  
✅ PAT token variable expansion  
✅ Subprocess environment passing  
✅ MCP server initialization  
✅ PAT token authentication  
✅ 64 Azure DevOps tools loaded  

**The code is perfect** - it's just a configuration issue with the PAT token permissions.

---

## 🎯 Summary

**Problem**: PAT token lacks Azure DevOps permissions  
**Solution**: Generate new token with required READ scopes  
**Time**: 5 minutes  
**Status**: Ready to fix - user action required  

**No code changes needed!** The authentication mechanism is working as designed.
