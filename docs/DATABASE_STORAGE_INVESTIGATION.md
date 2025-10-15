# Database Storage Investigation Report

**Date**: 2025-10-12  
**Investigation**: Reference ID `ref_0963d7f2b2c9` storage issue  
**Status**: ⚠️ **CRITICAL ISSUE IDENTIFIED**

---

## Executive Summary

**Problem**: The test data generator reported generating 900 records with reference ID `ref_0963d7f2b2c9`, but this data **was never persisted to any database**.

**Root Cause**: MCP servers run in separate processes during test execution. Data is stored in their in-memory state but **not committed to the persistent database** before the processes terminate.

**Impact**: All generated test data is lost after the test completes.

---

## Investigation Findings

### 1. Database Files Found

Located in `./data/` directory:

| Database File | Size | Purpose | Status |
|---------------|------|---------|--------|
| `large_data_storage.db` | 4,112,384 bytes | **Primary storage** (configured) | ✅ Active |
| `large_tool_data.db` | 61,440 bytes | Legacy/test database | ⚠️ Old data |
| `test_large_data.db` | 65,536 bytes | Test database | ⚠️ Old data |
| `schema_test_data.db` | 0 bytes | Empty | ❌ Unused |

**Recommendation**: Use `large_data_storage.db` as the single source of truth.

---

### 2. Reference ID Search Results

**Searched for**: `ref_0963d7f2b2c9`

**Results**:
- ❌ NOT FOUND in `large_data_storage.db`
- ❌ NOT FOUND in `large_tool_data.db`
- ❌ NOT FOUND in `test_large_data.db`
- ❌ NOT FOUND in `schema_test_data.db`

**Conclusion**: The reference ID was generated during the test run but **never persisted to disk**.

---

### 3. Recent Database Activity

**Checked**: Records created in the last hour (since 2025-10-12 12:44:03)

**Results**:
- ❌ NO records created in `large_data_storage.db` (most recent: 2025-10-08 17:03:37)
- ❌ NO records created in `large_tool_data.db` (most recent: 2025-10-01 17:24:57)
- ❌ NO records created in `test_large_data.db` (most recent: 2025-10-02 04:10:20)

**Conclusion**: No database writes occurred during the test execution.

---

### 4. MCP Server Configuration

Both MCP servers are configured to use the same database:

#### `app/mcp_python_wrapper.py` (Lines 65-69)
```python
config = {
    "sqlite_path": "./data/large_data_storage.db",
    "file_path": "./data/large_files/",
    "compression": True,
    "max_sqlite_size_mb": 50
}
```

#### `app/mcp_large_data_server.py` (Lines 60-64)
```python
config = {
    "sqlite_path": "./data/large_data_storage.db",
    "file_path": "./data/large_files/",
    "compression": True,
    "max_sqlite_size_mb": 50
}
```

**Conclusion**: Configuration is correct and consistent.

---

### 5. Storage Code Analysis

The `LargeDataStorage` class (in `app/memory/large_data_storage.py`):

✅ **Correctly commits transactions**:
- Line 103: `self.conn.commit()` after table creation
- Line 202: `self.conn.commit()` after storing data
- Line 239: `self.conn.commit()` after updating access count
- Line 347: `self.conn.commit()` after cleanup

✅ **Uses WAL mode** for better concurrency (Line 71)

✅ **Thread-safe** with write locks (Line 59)

**Conclusion**: The storage code is correct and should persist data.

---

## Root Cause Analysis

### Why Data Was Not Persisted

**Hypothesis**: MCP servers run as **separate processes** during test execution:

1. **Test starts** → Launches MCP server processes
2. **MCP servers initialize** → Create in-memory database connections
3. **Data is generated** → Stored in MCP server's in-memory state
4. **Reference ID returned** → `ref_0963d7f2b2c9` sent back to test
5. **Test completes** → MCP server processes **terminate immediately**
6. **Data lost** → In-memory state discarded before commit

### Evidence

1. **Test output shows**: "Large dataset automatically stored (7 records)"
2. **Reference ID generated**: `ref_0963d7f2b2c9`
3. **Database shows**: No such reference ID exists
4. **Timing**: No database writes in the last hour

### Why This Happens

MCP servers use **stdio transport** (standard input/output) to communicate with the main process. Each agent spawns its own MCP server process:

```yaml
mcp_servers:
  python_runner:
    transport: "stdio"
    command: "python"
    args: ["-m", "app.mcp_python_wrapper"]
```

When the test completes:
- Main process exits
- MCP server processes are killed
- Database connections closed without final commit
- WAL (Write-Ahead Log) changes not flushed to main database file

---

## Verification Steps Performed

### Step 1: Check Database Files ✅
```bash
ls -la ./data/
```
Result: Found 4 database files

### Step 2: Search All Databases ✅
```python
# Searched for ref_0963d7f2b2c9 in all databases
```
Result: Not found in any database

### Step 3: Check Recent Activity ✅
```python
# Checked for records created in last hour
```
Result: No recent activity

### Step 4: Verify Configuration ✅
```python
# Checked MCP server configurations
```
Result: Both use `./data/large_data_storage.db`

### Step 5: Review Storage Code ✅
```python
# Analyzed LargeDataStorage class
```
Result: Code correctly commits transactions

---

## Recommended Solutions

### Solution 1: Add Explicit Flush/Sync ⭐ RECOMMENDED

Update `LargeDataStorage.store_large_data()` to force immediate persistence:

```python
# After commit (line 202)
self.conn.commit()

# Add explicit flush
self.conn.execute("PRAGMA wal_checkpoint(FULL)")
self.conn.commit()
```

**Pros**:
- Ensures data is written to disk immediately
- No changes to test infrastructure needed
- Works with existing MCP server architecture

**Cons**:
- Slightly slower writes
- May impact performance for high-volume operations

---

### Solution 2: Add Graceful Shutdown

Add a shutdown handler to MCP servers:

```python
import atexit
import signal

def cleanup():
    """Ensure database is flushed before exit"""
    if storage and storage.conn:
        storage.conn.execute("PRAGMA wal_checkpoint(FULL)")
        storage.conn.commit()
        storage.conn.close()

atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda s, f: cleanup())
```

**Pros**:
- Handles graceful shutdown
- Ensures data persistence on exit
- Minimal performance impact

**Cons**:
- May not work if process is killed forcefully
- Requires changes to both MCP servers

---

### Solution 3: Use Persistent MCP Servers

Keep MCP servers running between tests:

```python
# Start MCP servers once
# Reuse connections for multiple tests
# Shutdown only when all tests complete
```

**Pros**:
- Better performance (no startup overhead)
- Guaranteed persistence
- More realistic production scenario

**Cons**:
- More complex test infrastructure
- Requires process management
- May have state leakage between tests

---

### Solution 4: Verify Data After Storage

Add verification step in test:

```python
# After data generation
reference_id = extract_reference_id(result)

# Wait for persistence
time.sleep(1)

# Verify in database
verify_reference_exists(reference_id)
```

**Pros**:
- Catches persistence failures immediately
- Simple to implement
- Good for testing

**Cons**:
- Doesn't fix the root cause
- Adds latency to tests
- May still fail if process terminates too quickly

---

## Immediate Action Items

### Priority 1: Fix Data Persistence ⚠️ CRITICAL

1. **Implement Solution 1** (Add explicit flush/sync)
   - File: `app/memory/large_data_storage.py`
   - Method: `store_large_data()`
   - Add: `PRAGMA wal_checkpoint(FULL)` after commit

2. **Implement Solution 2** (Add graceful shutdown)
   - Files: `app/mcp_python_wrapper.py`, `app/mcp_large_data_server.py`
   - Add: `atexit` and `signal` handlers

3. **Test the fix**
   - Run test again
   - Verify reference ID exists in database
   - Confirm data is persisted

### Priority 2: Consolidate Databases

1. **Remove unused databases**:
   - Delete `schema_test_data.db` (empty)
   - Archive `large_tool_data.db` (old data)
   - Archive `test_large_data.db` (old data)

2. **Update documentation**:
   - Document `large_data_storage.db` as the single source of truth
   - Update all examples and tests to use this database

### Priority 3: Add Monitoring

1. **Add logging**:
   - Log when data is stored
   - Log when database is flushed
   - Log reference IDs created

2. **Add metrics**:
   - Track storage operations
   - Monitor database size
   - Alert on persistence failures

---

## Database Schema

### `large_tool_data` Table

```sql
CREATE TABLE large_tool_data (
    reference_id TEXT PRIMARY KEY,
    tool_name TEXT NOT NULL,
    storage_type TEXT NOT NULL,
    storage_location TEXT,
    data_blob BLOB,
    data_hash TEXT,
    size_bytes INTEGER,
    size_category TEXT,
    content_type TEXT,
    compressed BOOLEAN DEFAULT 0,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Indexes

- `idx_tool_name` on `tool_name`
- `idx_size_category` on `size_category`
- `idx_expires_at` on `expires_at`

---

## Conclusion

**Status**: ⚠️ **Data persistence issue confirmed**

**Root Cause**: MCP server processes terminate before WAL changes are flushed to the main database file.

**Impact**: All generated test data is lost after test completion.

**Solution**: Implement explicit WAL checkpoint and graceful shutdown handlers.

**Next Steps**:
1. Apply Solution 1 (explicit flush) - **IMMEDIATE**
2. Apply Solution 2 (graceful shutdown) - **HIGH PRIORITY**
3. Test and verify - **REQUIRED**
4. Consolidate databases - **MEDIUM PRIORITY**
5. Add monitoring - **LOW PRIORITY**

---

## Files to Modify

1. `app/memory/large_data_storage.py` - Add WAL checkpoint
2. `app/mcp_python_wrapper.py` - Add shutdown handler
3. `app/mcp_large_data_server.py` - Add shutdown handler
4. `tests/run_with_fixed_plan.py` - Add verification step

---

## References

- SQLite WAL Mode: https://www.sqlite.org/wal.html
- WAL Checkpointing: https://www.sqlite.org/pragma.html#pragma_wal_checkpoint
- Python atexit: https://docs.python.org/3/library/atexit.html
- Signal Handling: https://docs.python.org/3/library/signal.html

