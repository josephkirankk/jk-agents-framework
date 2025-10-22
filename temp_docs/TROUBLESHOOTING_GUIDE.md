# Troubleshooting Guide: Serper MCP Errors & Logging

**Last Updated:** October 21, 2025

---

## 🔍 Quick Diagnosis

### Symptom: "Scraping failed" / 500 Error

**Error Message:**
```
Error: Serper API error: 500 Internal Server Error - {"message":"Scraping failed.","statusCode":500}
```

**✅ THIS IS NOW FIXED AND HANDLED GRACEFULLY**

**What This Means:**
- Serper's scraping service is having issues (their server problem, not yours)
- **Before fix:** Agent would crash
- **After fix:** Agent continues with search results only

**Expected Behavior (After Fix):**
```
WARNING - Tool scrape failed (non-fatal): Scraping temporarily unavailable
Agent: [Provides response using search results]
✅ Query succeeds
```

**Action Required:** None - agent handles this automatically

---

### Symptom: "Can't Find Logs"

**Problem:** You see logs in console but don't know where files are

**✅ THIS IS NOW FIXED**

**Solution:**
1. **Logs are in:** `<repo>/agentlogs/agentlog_<timestamp>.log`
2. **Check location:**
   ```bash
   python -c "from app.logging_config import get_log_directory; print(get_log_directory())"
   ```
3. **List recent logs:**
   ```bash
   ls -lt agentlogs/*.log | head -5
   ```

---

## 📋 Step-by-Step Troubleshooting

### Step 1: Verify Fixes Are Applied

```bash
# Check if mcp_loader.py has graceful degradation
grep -n "is_scrape_failure" app/mcp_loader.py
```

**Expected:** Should find line with `is_scrape_failure` check

```bash
# Check if logging_config.py exists
ls -l app/logging_config.py
```

**Expected:** File should exist

---

### Step 2: Check Log Directory

```bash
# Navigate to repo
cd /Users/A80997271/Documents/projects/jk-agents-core

# Check agentlogs directory
ls -la agentlogs/
```

**Expected Output:**
```
drwxr-xr-x  agentlogs
-rw-r--r--  agentlog_20251021120000.log
...
```

**If directory doesn't exist:**
```bash
mkdir -p agentlogs
chmod 755 agentlogs
```

---

### Step 3: Test Logging

```python
# test_logging.py
from app.logging_config import quick_setup, print_log_info

# Setup logging
log_file = quick_setup()
print(f"✅ Logging configured: {log_file}")

# Show log info
print_log_info()
```

Run:
```bash
python test_logging.py
```

**Expected:**
- ✅ Log file path displayed
- ✅ Recent logs listed
- ✅ No errors

---

### Step 4: Test Serper Example

```bash
# Run with a simple query
python examples/deep_agent_serper_example.py --query "test search"
```

**What to Check:**
1. **Log location displayed** at startup
2. **Scrape failures** logged as WARNING (not ERROR)
3. **Agent provides response** even if scrape fails
4. **Log file created** in agentlogs/

---

### Step 5: Review Log File

```bash
# View latest log
tail -50 agentlogs/agentlog_*.log

# Check for scrape warnings
grep "scrape" agentlogs/agentlog_*.log | tail -10

# Check for errors
grep "ERROR" agentlogs/agentlog_*.log | tail -10
```

**What You Should See:**
- `WARNING` for scrape failures (not ERROR)
- Detailed error information
- Clear error messages

---

## 🐛 Common Issues & Fixes

### Issue 1: "ExceptionGroup" Still Appearing

**Symptom:**
```
ERROR - ExceptionGroup: unhandled errors in a TaskGroup
```

**Diagnosis:**
- Old version of code still loaded
- Python cache not cleared

**Fix:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Restart Python interpreter
# Re-run your script
```

---

### Issue 2: Logs Not in agentlogs/

**Symptom:** Can't find log files in expected location

**Diagnosis:**
- Running from different directory
- Logging not configured

**Fix:**
```bash
# Check where you're running from
pwd

# Check if logging is configured in your script
grep "logging_config" your_script.py

# Add logging configuration
```

Add to your script:
```python
from app.logging_config import quick_setup
log_file = quick_setup()
print(f"Logs: {log_file}")
```

---

### Issue 3: Agent Still Crashes on Scrape Failure

**Symptom:** Agent fails completely when scrape returns 500

**Diagnosis:**
- Fix not applied
- Different error (not scrape-related)

**Check:**
```bash
# Verify fix is in place
grep -A 10 "is_scrape_failure" app/mcp_loader.py
```

Should see:
```python
is_scrape_failure = "scrape" in error_msg.lower()...
if is_scrape_failure and is_mcp_server_error:
    # Graceful degradation code
```

**If not found:**
- Re-apply the fix from SERPER_ERROR_FIX_SUMMARY.md
- Restart your script

---

### Issue 4: Too Many WARNING Messages

**Symptom:** Logs filled with scrape warnings

**This is normal** if Serper's scrape service is down. To reduce noise:

**Option 1: Increase log level**
```python
from app.logging_config import quick_setup
log_file = quick_setup(verbose=False)  # INFO level, less noise
```

**Option 2: Filter specific logger**
```python
import logging
logging.getLogger("mcp_loader").setLevel(logging.ERROR)  # Only errors
```

**Option 3: Disable scrape tool entirely**

In your config YAML, comment out the scrape tool or remove it from the MCP server.

---

## 🔧 Advanced Troubleshooting

### Enable DEBUG Logging

```python
from app.logging_config import quick_setup
log_file = quick_setup(verbose=True)  # DEBUG level
```

This will show:
- Full tracebacks
- Detailed tool execution
- MCP communication details

### Check MCP Server Status

```bash
# Test if MCP server can start
npx -y serper-search-scrape-mcp-server --version
```

### Check Serper API Directly

```python
import requests
import json

url = "https://google.serper.dev/search"
headers = {
    'X-API-KEY': 'your-key-here',
    'Content-Type': 'application/json'
}
payload = {"q": "test"}

response = requests.post(url, headers=headers, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

If search works but scrape doesn't, it's a Serper service issue.

---

## 📊 Understanding Log Levels

| Level | When Used | Example |
|-------|-----------|---------|
| DEBUG | Development, detailed info | Full tracebacks, variable values |
| INFO | Normal operations | "Agent started", "Query processed" |
| WARNING | Unexpected but handled | "Scrape unavailable", "Cache miss" |
| ERROR | Operation failed | "Authentication failed", "Tool crashed" |
| CRITICAL | System failure | "Database unreachable", "Out of memory" |

**After the fix:**
- Scrape failures = WARNING (non-fatal, handled)
- Other tool failures = ERROR (needs attention)

---

## 🎯 Quick Reference Commands

### View Logs
```bash
# Latest log (real-time)
tail -f agentlogs/agentlog_*.log

# Last 100 lines
tail -n 100 agentlogs/agentlog_*.log

# Errors only
grep ERROR agentlogs/*.log

# Warnings (scrape failures)
grep WARNING agentlogs/*.log | grep scrape
```

### Find Log Files
```bash
# List all logs
ls -lt agentlogs/

# Find logs from today
find agentlogs -name "*.log" -mtime 0

# Find logs from last hour
find agentlogs -name "*.log" -mmin -60
```

### Clean Old Logs
```bash
# Delete logs older than 7 days
find agentlogs -name "*.log" -mtime +7 -delete

# Keep only last 10 logs
ls -t agentlogs/*.log | tail -n +11 | xargs rm
```

---

## ✅ Verification Checklist

Use this checklist to verify everything is working:

- [ ] `app/mcp_loader.py` has graceful degradation code
- [ ] `app/logging_config.py` file exists
- [ ] `agentlogs/` directory exists and is writable
- [ ] Example scripts show log file location on startup
- [ ] Scrape failures show as WARNING (not ERROR)
- [ ] Agent continues working when scrape fails
- [ ] Log files are being created with timestamps
- [ ] Can find and read log files

---

## 🆘 Still Having Issues?

### Collect Debug Information

```bash
# 1. Check Python version
python --version

# 2. Check installed packages
pip list | grep -E "mcp|langchain|serper"

# 3. Check repository status
git status
git log -1

# 4. Collect recent logs
tar -czf debug-logs.tar.gz agentlogs/*.log

# 5. Test configuration
python -c "from app.logging_config import print_log_info; print_log_info()"
```

### What to Include in Bug Report

1. **Error message** (full text)
2. **Log file content** (last 50 lines)
3. **Command you ran**
4. **Expected vs actual behavior**
5. **Python version** and OS
6. **Timestamp** of the error

### Example Bug Report Template

```
**Issue:** Scrape tool still crashing agent

**Command:**
python examples/deep_agent_serper_example.py --query "test"

**Error:**
[paste error here]

**Log excerpt:**
[paste last 50 lines of log]

**Expected:** Agent should continue with search results
**Actual:** Agent crashes

**Environment:**
- Python: 3.12.9
- OS: macOS
- Timestamp: 2025-10-21 12:00:00

**Files checked:**
- mcp_loader.py: [yes/no] has graceful degradation
- logging_config.py: [yes/no] exists
- agentlogs/: [yes/no] directory exists
```

---

## 💡 Tips & Best Practices

### 1. Always Use Logging Configuration

```python
# ✅ DO THIS
from app.logging_config import quick_setup
log_file = quick_setup()

# ❌ DON'T DO THIS
import logging
logging.basicConfig(...)  # No file output
```

### 2. Show Log Location to Users

```python
# ✅ DO THIS
print(f"📋 Logs: {log_file}")

# ❌ DON'T DO THIS (silently logging)
# (no indication where logs are)
```

### 3. Handle Known Failures Gracefully

```python
# ✅ DO THIS (now implemented)
if scrape_fails:
    log.warning("Scrape unavailable, using search only")
    return_search_results()

# ❌ DON'T DO THIS
if scrape_fails:
    raise Exception("Scrape failed!")  # Crashes agent
```

### 4. Use Appropriate Log Levels

```python
# ✅ DO THIS
log.info("Normal operation")
log.warning("Handled issue")
log.error("Unrecoverable error")

# ❌ DON'T DO THIS
log.error("Everything")  # Too noisy
```

---

**Remember:** The fixes handle scrape failures gracefully. If scrape is failing, that's a Serper API issue, not your code. The agent will continue working with search results only.

---

*Last Updated: October 21, 2025*  
*Status: Complete*  
*All fixes verified and tested*
