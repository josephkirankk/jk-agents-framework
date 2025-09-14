# Simple Memory Persistence Test
# Tests that conversation memory is maintained across API calls

$ApiBase = "http://localhost:8000"

Write-Host "=== JK-Agents Memory Persistence Test ===" -ForegroundColor Blue
Write-Host ""

# Test 1: Tell the agent something to remember
Write-Host "=== Test 1: Store Information ===" -ForegroundColor Green
$payload1 = @{
    agent_name = "simple_test_agent"
    input = "I have 10 restaurants. Please remember this."
    config_path = "c:\JK\dev\repo\jk-agents\config\simple_test.yaml"
} | ConvertTo-Json

Write-Host "Sending: I have 10 restaurants. Please remember this." -ForegroundColor Yellow

try {
    $response1 = Invoke-RestMethod -Uri "$ApiBase/worker" -Method Post -Body $payload1 -ContentType "application/json"
    Write-Host "✓ Response: $($response1.response)" -ForegroundColor Green
    Write-Host "Thread ID: $($response1.thread_id)" -ForegroundColor Yellow
    $threadId = $response1.thread_id
} catch {
    Write-Host "✗ Test 1 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Ask the agent to recall the information using the same thread ID
Write-Host "=== Test 2: Recall Information (Same Thread) ===" -ForegroundColor Green
$payload2 = @{
    agent_name = "simple_test_agent"
    input = "How many restaurants do I have?"
    config_path = "c:\JK\dev\repo\jk-agents\config\simple_test.yaml"
    thread_id = $threadId
} | ConvertTo-Json

Write-Host "Sending: How many restaurants do I have? (using thread_id: $threadId)" -ForegroundColor Yellow

try {
    $response2 = Invoke-RestMethod -Uri "$ApiBase/worker" -Method Post -Body $payload2 -ContentType "application/json"
    Write-Host "✓ Response: $($response2.response)" -ForegroundColor Green
    
    if ($response2.response -match "10") {
        Write-Host "✓ MEMORY PERSISTENCE WORKING! Agent remembered the information." -ForegroundColor Green
    } else {
        Write-Host "✗ MEMORY PERSISTENCE FAILED! Agent did not remember." -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Test 2 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: Test memory isolation with different thread ID
Write-Host "=== Test 3: Memory Isolation (Different Thread) ===" -ForegroundColor Green
$payload3 = @{
    agent_name = "simple_test_agent"
    input = "How many restaurants do I have?"
    config_path = "c:\JK\dev\repo\jk-agents\config\simple_test.yaml"
    thread_id = "different-thread-123"
} | ConvertTo-Json

Write-Host "Sending: How many restaurants do I have? (using different thread_id)" -ForegroundColor Yellow

try {
    $response3 = Invoke-RestMethod -Uri "$ApiBase/worker" -Method Post -Body $payload3 -ContentType "application/json"
    Write-Host "✓ Response: $($response3.response)" -ForegroundColor Green
    
    if ($response3.response -notmatch "10") {
        Write-Host "✓ MEMORY ISOLATION WORKING! Different thread has no memory of previous conversation." -ForegroundColor Green
    } else {
        Write-Host "✗ MEMORY ISOLATION FAILED! Different thread has access to previous memory." -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Test 3 failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 4: Check memory stats
Write-Host "=== Test 4: Memory Statistics ===" -ForegroundColor Green
try {
    $memoryStats = Invoke-RestMethod -Uri "$ApiBase/memory/stats" -Method Get
    Write-Host "✓ Memory Stats Retrieved:" -ForegroundColor Green
    Write-Host "  Total Threads: $($memoryStats.memory_stats.total_threads)" -ForegroundColor Yellow
    Write-Host "  Checkpointer Type: $($memoryStats.memory_stats.checkpointer_type)" -ForegroundColor Yellow
} catch {
    Write-Host "✗ Memory stats failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Blue
