#!/usr/bin/env powershell
# Simple test script for Internal LLM Logging System

Write-Host "=== Testing Internal LLM Logging System ===" -ForegroundColor Green
Write-Host ""

$baseUrl = "http://localhost:8000"

# Function to make safe HTTP requests
function Invoke-SafeRequest {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [string]$Body = $null
    )
    
    try {
        if ($Body) {
            return Invoke-RestMethod -Uri $Uri -Method $Method -Body $Body -ContentType "application/json" -TimeoutSec 30
        } else {
            return Invoke-RestMethod -Uri $Uri -Method $Method -TimeoutSec 30
        }
    }
    catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Step 1: Check server health
Write-Host "1. Checking server health..." -ForegroundColor Yellow
$health = Invoke-SafeRequest -Uri "$baseUrl/health"
if ($health) {
    Write-Host "   Server is healthy: $($health.status)" -ForegroundColor Green
} else {
    Write-Host "   Server is not accessible!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Get initial logging stats
Write-Host "2. Getting initial logging stats..." -ForegroundColor Yellow
$initialStats = Invoke-SafeRequest -Uri "$baseUrl/internal-logging/stats"
if ($initialStats -and $initialStats.success) {
    Write-Host "   Logging enabled: $($initialStats.stats.enabled)" -ForegroundColor Green
    Write-Host "   Current log file: $($initialStats.stats.current_log_file)" -ForegroundColor Gray
    Write-Host "   Total files: $($initialStats.stats.total_log_files)" -ForegroundColor Gray
} else {
    Write-Host "   Failed to get logging stats" -ForegroundColor Red
}
Write-Host ""

# Step 3: Test direct worker call
Write-Host "3. Testing direct worker call..." -ForegroundColor Yellow
$workerBody = '{"agent_name": "test_agent", "input": "Explain quantum computing briefly"}'
$workerResponse = Invoke-SafeRequest -Uri "$baseUrl/worker" -Method "POST" -Body $workerBody

if ($workerResponse -and $workerResponse.success) {
    Write-Host "   Direct worker call successful!" -ForegroundColor Green
    Write-Host "   Agent: $($workerResponse.agent_name)" -ForegroundColor Gray
    Write-Host "   Response length: $($workerResponse.response.Length) chars" -ForegroundColor Gray
} else {
    Write-Host "   Direct worker call failed" -ForegroundColor Red
}
Write-Host ""

# Step 4: Test query endpoint (supervisor)
Write-Host "4. Testing query endpoint (supervisor)..." -ForegroundColor Yellow
$queryBody = '{"input": "Analyze AI trends in 2024 and provide strategic insights"}'
$queryResponse = Invoke-SafeRequest -Uri "$baseUrl/query" -Method "POST" -Body $queryBody

if ($queryResponse -and $queryResponse.success) {
    Write-Host "   Query endpoint call successful!" -ForegroundColor Green
    Write-Host "   Response length: $($queryResponse.response.Length) chars" -ForegroundColor Gray
} else {
    Write-Host "   Query endpoint call failed" -ForegroundColor Red
}
Write-Host ""

# Step 5: Get updated logging stats
Write-Host "5. Getting updated logging stats..." -ForegroundColor Yellow
$updatedStats = Invoke-SafeRequest -Uri "$baseUrl/internal-logging/stats"
if ($updatedStats -and $updatedStats.success) {
    Write-Host "   Updated stats retrieved!" -ForegroundColor Green
    Write-Host "   Total files: $($updatedStats.stats.total_log_files)" -ForegroundColor Gray
    Write-Host "   Total size: $($updatedStats.stats.total_size_mb) MB" -ForegroundColor Gray
    
    $logFile = $updatedStats.stats.current_log_file
    Write-Host "   Current log file: $logFile" -ForegroundColor Gray
    
    # Check log file
    if ($logFile -and (Test-Path $logFile)) {
        Write-Host ""
        Write-Host "6. Analyzing log file..." -ForegroundColor Yellow
        
        $logLines = Get-Content $logFile -Tail 10
        $requestCount = 0
        $responseCount = 0
        $totalTokens = 0
        
        Write-Host "   Recent log entries:" -ForegroundColor Cyan
        foreach ($line in $logLines) {
            try {
                $entry = $line | ConvertFrom-Json
                $timestamp = $entry.timestamp -replace 'T', ' ' -replace '\.\d+.*$', ''
                
                if ($entry.log_type -eq "llm_request") {
                    $requestCount++
                    Write-Host "   -> REQUEST: $($entry.provider)/$($entry.model) [$timestamp]" -ForegroundColor Cyan
                    Write-Host "      Agent: $($entry.agent_name)" -ForegroundColor Gray
                }
                elseif ($entry.log_type -eq "llm_response") {
                    $responseCount++
                    $tokens = if ($entry.token_usage) { $entry.token_usage.total_tokens } else { 0 }
                    $totalTokens += $tokens
                    $time = [math]::Round($entry.response_time_ms, 1)
                    Write-Host "   <- RESPONSE: Status $($entry.status_code), ${tokens} tokens, ${time}ms [$timestamp]" -ForegroundColor Green
                }
                else {
                    Write-Host "   -- $($entry.log_type): [$timestamp]" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "   Invalid JSON line" -ForegroundColor DarkGray
            }
        }
        
        Write-Host ""
        Write-Host "   Summary:" -ForegroundColor Yellow
        Write-Host "   - Requests logged: $requestCount" -ForegroundColor White
        Write-Host "   - Responses logged: $responseCount" -ForegroundColor White
        Write-Host "   - Total tokens: $totalTokens" -ForegroundColor White
    } else {
        Write-Host "   Log file not found: $logFile" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Failed to get updated stats" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Green
Write-Host "Check the logs directory for detailed internal logging files!" -ForegroundColor Cyan
