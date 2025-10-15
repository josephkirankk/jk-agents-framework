# Concurrency Integration Tests

## Overview

**File**: `test_08_concurrency_integration.py`  
**Purpose**: Comprehensive concurrency testing with **real API endpoints and actual data** (no mocks)  
**Coverage**: Thread safety, race conditions, cache isolation, concurrent load handling

---

## Test Categories

### 1. **Concurrent API Requests** (TestConcurrentAPIRequests)

Tests real FastAPI endpoints under high concurrent load.

#### test_concurrent_health_checks
- **Load**: 100 concurrent health check requests
- **Validates**: 
  - All requests complete successfully
  - No race conditions in request handling
  - Response time under load
- **Real Data**: Actual HTTP requests to `/health`

#### test_concurrent_worker_requests
- **Load**: 50 concurrent worker/agent requests
- **Validates**:
  - Agent execution under concurrent load
  - Thread-safe agent instantiation
  - Response consistency
  - Success rate > 80%
- **Real Data**: Actual agent configurations, unique inputs per request

#### test_concurrent_requests_with_files
- **Load**: 30 concurrent file upload requests
- **Validates**:
  - File handling under concurrent load
  - No file corruption
  - Thread-safe file storage
- **Real Data**: Actual file uploads with unique content

---

### 2. **Concurrent Singleton Access** (TestConcurrentSingletonAccess)

Tests singleton patterns under extreme concurrent access.

#### test_file_storage_manager_concurrent_access
- **Load**: 100 concurrent operations
- **Operations**:
  - Get singleton instance
  - Store file
  - Retrieve metadata
  - Delete file
- **Validates**:
  - Single instance across all threads
  - No race conditions in initialization
  - Thread-safe file operations
- **Real Data**: Actual files stored/retrieved/deleted

#### test_conversation_memory_concurrent_access
- **Load**: 100 concurrent operations
- **Operations**:
  - Get singleton instance
  - Add messages
  - Retrieve history
  - Clear conversations
- **Validates**:
  - Single instance across all threads
  - Thread-safe memory operations
  - Data isolation per thread
- **Real Data**: Actual conversation messages

---

### 3. **Concurrent Metrics** (TestConcurrentMetrics)

Tests performance metrics under concurrent updates.

#### test_metrics_concurrent_updates
- **Load**: 1000 concurrent metric updates
- **Validates**:
  - Atomic counter increments
  - No lost updates
  - Thread-safe dictionary operations
  - Final count accuracy
- **Real Data**: Actual metrics structure from `api.py`

#### test_metrics_tracking_under_load
- **Load**: 50 concurrent API requests
- **Validates**:
  - Metrics update correctly during real load
  - Thread context tracking
  - No corruption in metrics data
- **Real Data**: Metrics from actual API requests

---

### 4. **Concurrent Cache Operations** (TestConcurrentCacheOperations)

Tests cache isolation and deep copy effectiveness.

#### test_cache_isolation_under_concurrent_access
- **Load**: 50 concurrent cache accesses
- **Operations**:
  - Get cached objects (using deepcopy)
  - Modify copies
  - Verify original unchanged
- **Validates**:
  - Deep copy prevents cross-request contamination
  - Modifications don't leak to other requests
  - Original cache integrity maintained
- **Real Data**: Simulates actual agent cache structure

---

### 5. **Concurrent File Operations** (TestConcurrentFileOperations)

Tests file storage under intensive concurrent load.

#### test_concurrent_file_store_retrieve_delete
- **Load**: 100 concurrent file operations
- **Operations** (per thread):
  - Store file
  - Retrieve metadata
  - Retrieve content
  - Delete file
  - Verify deletion
- **Validates**:
  - Thread-safe file storage
  - No race conditions in file operations
  - Data integrity
  - Proper cleanup
- **Real Data**: Actual files with unique content

#### test_concurrent_file_access_same_thread
- **Load**: 50 concurrent accesses to shared thread files
- **Operations**:
  - List files for thread
  - Random file access
  - Concurrent reads
- **Validates**:
  - Thread-safe file listing
  - No corruption when multiple threads access same data
  - Consistent file metadata
- **Real Data**: Pre-populated files, concurrent access

---

### 6. **Stress Test** (TestConcurrentStressTest)

Mixed load test simulating real-world scenarios.

#### test_mixed_concurrent_load
- **Total Load**: 200 operations
  - 100 API requests (async)
  - 50 file operations (threaded)
  - 50 memory operations (threaded)
- **Validates**:
  - System stability under mixed load
  - No deadlocks
  - Success rate > 90%
  - Error rate < 10%
- **Real Data**: All operations use actual API/storage/memory

---

## Running the Tests

### Run All Concurrency Tests
```bash
cd /Users/A80997271/Documents/projects/jk-agents-core
python -m pytest integration_tests/test_08_concurrency_integration.py -v -s
```

### Run Specific Test Class
```bash
# Singleton tests
python -m pytest integration_tests/test_08_concurrency_integration.py::TestConcurrentSingletonAccess -v -s

# API tests
python -m pytest integration_tests/test_08_concurrency_integration.py::TestConcurrentAPIRequests -v -s

# Stress test
python -m pytest integration_tests/test_08_concurrency_integration.py::TestConcurrentStressTest -v -s
```

### Run Specific Test
```bash
python -m pytest integration_tests/test_08_concurrency_integration.py::TestConcurrentMetrics::test_metrics_concurrent_updates -v -s
```

---

## Test Execution Time

| Test Class | Tests | Approx Time | Load |
|-----------|-------|-------------|------|
| TestConcurrentAPIRequests | 3 | 30-60s | 180 requests |
| TestConcurrentSingletonAccess | 2 | 10-20s | 200 operations |
| TestConcurrentMetrics | 2 | 5-10s | 1050 operations |
| TestConcurrentCacheOperations | 1 | 2-5s | 50 operations |
| TestConcurrentFileOperations | 2 | 15-30s | 150 operations |
| TestConcurrentStressTest | 1 | 20-40s | 200 mixed ops |
| **TOTAL** | **11** | **~2-3 min** | **~1830 ops** |

---

## What Makes These Tests Comprehensive

### ✅ Real API Endpoints
- Uses actual FastAPI app instance
- Real HTTP requests via `httpx.AsyncClient`
- No mocks or stubs

### ✅ Real Data
- Actual agent configurations
- Real file content
- Genuine conversation messages
- Production-like payloads

### ✅ High Concurrency
- 50-100 concurrent operations per test
- Mixed async/threaded execution
- Simulates production load patterns

### ✅ Thread Safety Validation
- Tests all critical singleton patterns
- Validates lock types and usage
- Checks for race conditions
- Verifies data isolation

### ✅ Multiple Scenarios
- API load
- File operations
- Memory operations
- Cache access
- Metrics updates
- Mixed concurrent load

### ✅ Comprehensive Coverage
- 11 distinct test methods
- ~1830 operations total
- Tests async, threading, and mixed patterns
- Validates all critical fixes applied

---

## Expected Results

### Successful Run:
```
🔍 Testing 100 concurrent health checks...
✅ All 100 requests succeeded in 2.15s (46.5 req/s)

🔍 Testing FileStorageManager under 100 concurrent accesses...
✅ All 100 operations used same singleton (ID: 12345678)

🔍 Testing metrics with 1000 concurrent updates...
✅ All 1000 updates completed correctly

...

✅ 11 tests passed
```

### Pass Criteria:
- **Success Rate**: ≥ 80% (most tests expect 100%)
- **No Race Conditions**: All assertions pass
- **Singleton Integrity**: Single instance confirmed
- **Data Isolation**: No cross-contamination
- **No Deadlocks**: All operations complete

---

## Validation Checklist

After running tests, verify:

- [ ] All 11 tests pass
- [ ] No race condition errors
- [ ] Singletons maintain single instance
- [ ] Cache isolation working (deep copy)
- [ ] Metrics accurate under load
- [ ] File operations thread-safe
- [ ] No deadlocks or hangs
- [ ] Success rates meet thresholds
- [ ] Error rates below limits
- [ ] Mixed load test passes

---

## Troubleshooting

### Test Timeouts
- Normal for stress tests (20-40s)
- Increase timeout if needed: `--timeout=120`

### Import Errors
- Ensure project root in PYTHONPATH
- Check imports use `from api import ...`
- Verify app modules installed

### Low Success Rates
- Check if real agents configured
- Verify config files exist
- Review API error logs

### Race Condition Failures
- Indicates concurrency fix needed
- Review lock usage in failed component
- Check for asyncio vs threading lock confusion

---

## Integration with CI/CD

### Add to Test Suite
```yaml
# .github/workflows/tests.yml
- name: Run Concurrency Integration Tests
  run: |
    python -m pytest integration_tests/test_08_concurrency_integration.py \
      -v --tb=short --durations=10
```

### Performance Benchmarks
```bash
# Track performance over time
python -m pytest integration_tests/test_08_concurrency_integration.py \
  --durations=0 > concurrency_benchmarks.txt
```

---

## Complementary Testing

These tests complement:

1. **Unit Tests** (`temp_tests/test_concurrency_fixes.py`)
   - Tests lock types
   - Tests singleton patterns
   - Faster, more focused

2. **Integration Tests** (other `test_*.py`)
   - Tests individual features
   - Single-threaded scenarios

3. **Load Tests** (manual with `ab`, `locust`)
   - Higher concurrent load (1000+)
   - Performance profiling
   - Bottleneck identification

---

## Test Maintenance

### When to Update Tests

- After adding new API endpoints
- When modifying singleton patterns
- After cache structure changes
- When adding new concurrent features

### Regular Verification

- Run before each release
- Run after concurrency-related changes
- Include in regression test suite
- Monitor for flakiness

---

## Related Documentation

- `CONCURRENCY_AUDIT_REPORT.md` - Full audit findings
- `CONCURRENCY_FIXES_APPLIED.md` - Applied fixes
- `test_concurrency_fixes.py` - Unit-level concurrency tests
- `INTEGRATION_TESTS_GUIDE.md` - General integration testing guide

---

**Created**: 2025-01-14  
**Purpose**: Validate concurrency fixes with real-world scenarios  
**Status**: ✅ Comprehensive test suite ready for execution
