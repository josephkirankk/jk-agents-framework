# Memory System Regression Test Guide

This document describes the comprehensive regression tests created to validate the memory system fixes for AIMessage serialization and ChromaDB duplicate ID issues.

## Issues Fixed

### 1. AIMessage JSON Serialization Error
- **Problem**: `Object of type AIMessage is not JSON serializable`
- **Fix**: Custom JSON serializer in `langgraph_adapter.py`
- **Validation**: Tests with complex conversation data and large payloads

### 2. ChromaDB Duplicate ID Error  
- **Problem**: `Expected IDs to be unique, found duplicates`
- **Fix**: Enhanced ID generation with UUID and random components
- **Validation**: Rapid concurrent request tests

## Test Files Created

### 1. Comprehensive Python Test Suite
**File**: `reg_tests/test_memory_multiturn_bigdata_regression.py`

**Features**:
- Multi-turn conversation memory persistence
- Big data serialization testing (progressive data sizes)
- Rapid concurrent request handling
- Thread isolation verification
- Complex conversation context preservation

**Usage**:
```bash
cd /path/to/jk-agents-framework
source .venv/bin/activate
python reg_tests/test_memory_multiturn_bigdata_regression.py --url http://localhost:8000 --output results.json
```

**Test Cases**:
1. **Basic Memory Persistence**: Tests if context is preserved across conversation turns
2. **Big Data Serialization**: Tests with small/medium/large data payloads to stress-test serialization
3. **Rapid Requests**: 10 concurrent requests to test duplicate ID prevention  
4. **Complex Multi-turn**: 5-turn conversation with context building and recall
5. **Thread Isolation**: Separate thread IDs maintain separate contexts

### 2. Quick Curl-based Test
**File**: `reg_tests/quick_memory_test.sh`

**Features**:
- Pure curl commands for realistic API testing
- Multi-turn conversation simulation
- Big data payload testing
- Rapid request simulation
- Manual verification checklist

**Usage**:
```bash
cd /path/to/jk-agents-framework
./reg_tests/quick_memory_test.sh
```

### 3. Test Runner Script
**File**: `reg_tests/run_memory_regression.sh`

**Features**:
- Automated test execution with environment setup
- API server health check
- Results collection and reporting
- Pass/fail summary with colored output

**Usage**:
```bash
cd /path/to/jk-agents-framework
./reg_tests/run_memory_regression.sh
```

## Validation Checklist

When running these tests, verify the following:

### ✅ Memory System Functionality
- [ ] Multi-turn conversations preserve context correctly
- [ ] Large data payloads process without serialization errors  
- [ ] Rapid requests don't cause duplicate ID conflicts
- [ ] Thread isolation maintains separate memory contexts
- [ ] Complex conversations build and maintain context properly

### ✅ Error Log Validation
Monitor server logs for absence of these errors:
- [ ] No `Object of type AIMessage is not JSON serializable`
- [ ] No `Expected IDs to be unique, found duplicates`
- [ ] Memory system components initialize successfully
- [ ] ChromaDB operations complete without conflicts

### ✅ Performance Validation
- [ ] Response times remain reasonable under load
- [ ] Memory usage stays within acceptable bounds
- [ ] Concurrent requests process successfully
- [ ] No memory leaks or resource exhaustion

## Sample Test Scenarios

### Scenario 1: Customer Service Conversation
```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="My name is Alice, order #12345, shipped to New York"' \
--form 'config_path="config/python_exec_agent_working.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="customer-service-test"'

curl --location 'http://localhost:8000/query/form' \
--form 'input="What was my order number and shipping address?"' \
--form 'config_path="config/python_exec_agent_working.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="customer-service-test"'
```

### Scenario 2: Big Data Analysis Context
```bash
curl --location 'http://localhost:8000/query/form' \
--form 'input="I have sales data: Q1 2024 revenue $2.5M from 15000 transactions across 500 products in 25 regions with customer segments Enterprise(40%), SMB(35%), Consumer(25%)"' \
--form 'config_path="config/python_exec_agent_working.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="bigdata-test"'

curl --location 'http://localhost:8000/query/form' \
--form 'input="What was the Q1 revenue and customer segment breakdown I mentioned?"' \
--form 'config_path="config/python_exec_agent_working.yaml"' \
--form 'raw_output="True"' \
--form 'thread_id="bigdata-test"'
```

### Scenario 3: Rapid Load Test
```bash
for i in {1..5}; do
  curl --location 'http://localhost:8000/query/form' \
  --form "input=\"Load test request $i with timestamp $(date)\"" \
  --form 'config_path="config/python_exec_agent_working.yaml"' \
  --form 'raw_output="True"' \
  --form 'thread_id="load-test"' &
done
wait
```

## Expected Results

### Success Indicators
- All curl requests return HTTP 200 status
- Responses contain relevant context from previous turns  
- Server logs show no serialization or duplicate ID errors
- Memory components initialize and operate correctly
- Response times remain under 5 seconds for normal requests

### Failure Indicators  
- HTTP error responses (4xx, 5xx)
- Missing context in multi-turn conversations
- Serialization errors in server logs
- Duplicate ID conflicts in ChromaDB operations
- Excessive response times or timeouts

## Troubleshooting

### Common Issues
1. **API Server Not Running**: Ensure server is started with `python api.py`
2. **Configuration File Missing**: Check `config/python_exec_agent_working.yaml` exists
3. **Virtual Environment**: Activate `.venv` before running tests
4. **Port Conflicts**: Ensure port 8000 is available

### Debug Steps
1. Check server logs for specific error details
2. Verify memory backend initialization in logs
3. Test with simple requests before complex scenarios  
4. Monitor system resources during load tests
5. Check ChromaDB data persistence between test runs

## Integration with CI/CD

These tests can be integrated into automated pipelines:

```bash
#!/bin/bash
# CI/CD Integration Example

# Start API server in background
python api.py &
API_PID=$!

# Wait for server to be ready
sleep 10

# Run regression tests
./reg_tests/run_memory_regression.sh

# Capture exit code
TEST_RESULT=$?

# Cleanup
kill $API_PID

# Exit with test result
exit $TEST_RESULT
```

## Maintenance

### Regular Test Updates
- Add new test scenarios as features evolve
- Update data payloads to match production scale
- Adjust timing and concurrency based on performance requirements
- Monitor for new edge cases in production logs

### Performance Baselines
- Establish response time baselines for different request types
- Monitor memory usage patterns over time
- Track success rates for concurrent request scenarios
- Set up alerts for regression in key metrics
