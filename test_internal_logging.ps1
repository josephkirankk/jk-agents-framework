#!/usr/bin/env powershell
<#
.SYNOPSIS
    Test script for Internal LLM Logging System
.DESCRIPTION
    This script tests the internal logging system by making direct agent calls,
    supervisor calls, and then analyzing the generated logs.
#>

Write-Host "=== Testing Internal LLM Logging System ===" -ForegroundColor Green
Write-Host "Testing comprehensive logging for all LLM interactions" -ForegroundColor Gray
Write-Host ""

# Configuration
$baseUrl = "http://localhost:8000"
$timeout = 30

# Function to make HTTP requests with error handling
function Invoke-SafeRestMethod {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [string]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            TimeoutSec = $timeout
        }
        
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = $ContentType
        }
        
        return Invoke-RestMethod @params
    }
    catch {
        Write-Host "❌ HTTP Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "   Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        }
        return $null
    }
}

# Function to display log entry summary
function Show-LogEntry {
    param($entry)
    
    $timestamp = $entry.timestamp -replace 'T', ' ' -replace '\.\d+Z?$', ''
    
    switch ($entry.log_type) {
        "llm_request" {
            Write-Host "  📤 REQUEST [$timestamp]" -ForegroundColor Cyan
            Write-Host "     Provider: $($entry.provider) | Model: $($entry.model)" -ForegroundColor Gray
            Write-Host "     Agent: $($entry.agent_name)" -ForegroundColor Gray
            Write-Host "     Endpoint: $($entry.endpoint)" -ForegroundColor DarkGray
        }
        "llm_response" {
            $tokens = if ($entry.token_usage) { $entry.token_usage.total_tokens } else { "N/A" }
            $time = [math]::Round($entry.response_time_ms, 1)
            Write-Host "  📥 RESPONSE [$timestamp]" -ForegroundColor Green
            Write-Host "     Status: $($entry.status_code) | Tokens: $tokens | Time: ${time}ms" -ForegroundColor Gray
            if ($entry.error_message) {
                Write-Host "     Error: $($entry.error_message)" -ForegroundColor Red
            }
        }
        "agent_execution_start" {
            Write-Host "  🚀 AGENT START [$timestamp]" -ForegroundColor Yellow
            Write-Host "     Agent: $($entry.agent_name) | Model: $($entry.model)" -ForegroundColor Gray
        }
        "agent_execution_end" {
            $status = if ($entry.success) { "SUCCESS" } else { "FAILED" }
            $color = if ($entry.success) { "Green" } else { "Red" }
            Write-Host "  🏁 AGENT END [$timestamp] - $status" -ForegroundColor $color
            if ($entry.error_message) {
                Write-Host "     Error: $($entry.error_message)" -ForegroundColor Red
            }
        }
        default {
            Write-Host "  ℹ️  $($entry.log_type.ToUpper()) [$timestamp]" -ForegroundColor Gray
        }
    }
}

# Step 0: Check server health
Write-Host "🔍 Step 0: Checking server health..." -ForegroundColor Yellow
$health = Invoke-SafeRestMethod -Uri "$baseUrl/health"
if (-not $health) {
    Write-Host "❌ Server is not running or not accessible at $baseUrl" -ForegroundColor Red
    Write-Host "   Please start the server with: uvicorn app.api:app --reload" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Server is healthy (Status: $($health.status))" -ForegroundColor Green
Write-Host ""

# Step 1: Get initial logging stats
Write-Host "📊 Step 1: Getting initial logging statistics..." -ForegroundColor Yellow
$initialStats = Invoke-SafeRestMethod -Uri "$baseUrl/internal-logging/stats"
if ($initialStats -and $initialStats.success) {
    $stats = $initialStats.stats
    Write-Host "✅ Initial logging stats retrieved:" -ForegroundColor Green
    Write-Host "   Enabled: $($stats.enabled)" -ForegroundColor Gray
    Write-Host "   Log Level: $($stats.config.log_level)" -ForegroundColor Gray
    Write-Host "   Total Files: $($stats.total_log_files)" -ForegroundColor Gray
    Write-Host "   Total Size: $($stats.total_size_mb) MB" -ForegroundColor Gray
    Write-Host "   Current File: $($stats.current_log_file)" -ForegroundColor Gray
} else {
    Write-Host "❌ Failed to get initial logging stats" -ForegroundColor Red
}
Write-Host ""

# Step 2: Test direct agent call
Write-Host "🤖 Step 2: Testing direct agent call..." -ForegroundColor Yellow
$directBody = @{
    agent_name = "google_gemini_agent"
    user_input = "Explain quantum computing in simple terms. What are its main applications?"
    file_ids = @()
} | ConvertTo-Json -Compress

Write-Host "   Making request to direct agent..." -ForegroundColor Gray
$directResponse = Invoke-SafeRestMethod -Uri "$baseUrl/agent/direct" -Method POST -Body $directBody

if ($directResponse -and $directResponse.success) {
    Write-Host "✅ Direct agent call successful:" -ForegroundColor Green
    Write-Host "   Agent: $($directResponse.agent_name)" -ForegroundColor Gray
    Write-Host "   Response Length: $($directResponse.response.Length) characters" -ForegroundColor Gray
    if ($directResponse.log_file) {
        Write-Host "   Agent Log File: $($directResponse.log_file)" -ForegroundColor Gray
    }
    Write-Host "   Response Preview: $($directResponse.response.Substring(0, [Math]::Min(100, $directResponse.response.Length)))..." -ForegroundColor DarkGray
} else {
    Write-Host "❌ Direct agent call failed" -ForegroundColor Red
}
Write-Host ""

# Step 3: Test supervisor agent call
Write-Host "👥 Step 3: Testing supervisor agent call..." -ForegroundColor Yellow
$supervisorBody = @{
    user_input = "Analyze the current trends in artificial intelligence and machine learning. What are the key developments in 2024?"
    file_ids = @()
} | ConvertTo-Json -Compress

Write-Host "   Making request to supervisor agent..." -ForegroundColor Gray
$supervisorResponse = Invoke-SafeRestMethod -Uri "$baseUrl/agent/supervisor" -Method POST -Body $supervisorBody

if ($supervisorResponse -and $supervisorResponse.success) {
    Write-Host "✅ Supervisor agent call successful:" -ForegroundColor Green
    Write-Host "   Response Length: $($supervisorResponse.response.Length) characters" -ForegroundColor Gray
    Write-Host "   Response Preview: $($supervisorResponse.response.Substring(0, [Math]::Min(100, $supervisorResponse.response.Length)))..." -ForegroundColor DarkGray
} else {
    Write-Host "❌ Supervisor agent call failed" -ForegroundColor Red
}
Write-Host ""

# Step 4: Get updated logging stats
Write-Host "📈 Step 4: Getting updated logging statistics..." -ForegroundColor Yellow
$updatedStats = Invoke-SafeRestMethod -Uri "$baseUrl/internal-logging/stats"

if ($updatedStats -and $updatedStats.success) {
    $stats = $updatedStats.stats
    Write-Host "✅ Updated logging stats retrieved:" -ForegroundColor Green
    Write-Host "   Total Files: $($stats.total_log_files)" -ForegroundColor Gray
    Write-Host "   Total Size: $($stats.total_size_mb) MB" -ForegroundColor Gray
    Write-Host "   Current File: $($stats.current_log_file)" -ForegroundColor Gray
    
    $logFile = $stats.current_log_file
    
    # Step 5: Analyze log file
    if ($logFile -and (Test-Path $logFile)) {
        Write-Host ""
        Write-Host "📋 Step 5: Analyzing internal log entries..." -ForegroundColor Yellow
        
        try {
            $logLines = Get-Content $logFile -Encoding UTF8
            $totalEntries = $logLines.Count
            $requests = 0
            $responses = 0
            $errors = 0
            $totalTokens = 0
            $providers = @{}
            $models = @{}
            $agents = @{}
            
            Write-Host "   Found $totalEntries log entries" -ForegroundColor Gray
            Write-Host ""
            Write-Host "   Recent entries (last 10):" -ForegroundColor Cyan
            
            # Show last 10 entries
            $recentEntries = $logLines | Select-Object -Last 10
            foreach ($line in $recentEntries) {
                try {
                    $entry = $line | ConvertFrom-Json
                    Show-LogEntry $entry
                    
                    # Collect statistics
                    if ($entry.log_type -eq "llm_request") {
                        $requests++
                        if ($entry.provider) { $providers[$entry.provider] = ($providers[$entry.provider] ?? 0) + 1 }
                        if ($entry.model) { $models[$entry.model] = ($models[$entry.model] ?? 0) + 1 }
                        if ($entry.agent_name) { $agents[$entry.agent_name] = ($agents[$entry.agent_name] ?? 0) + 1 }
                    }
                    elseif ($entry.log_type -eq "llm_response") {
                        $responses++
                        if ($entry.status_code -ge 400) { $errors++ }
                        if ($entry.token_usage -and $entry.token_usage.total_tokens) {
                            $totalTokens += $entry.token_usage.total_tokens
                        }
                    }
                }
                catch {
                    Write-Host "   ⚠️  Invalid JSON line: $($line.Substring(0, [Math]::Min(50, $line.Length)))..." -ForegroundColor DarkYellow
                }
            }
            
            # Display summary statistics
            Write-Host ""
            Write-Host "📊 Log Analysis Summary:" -ForegroundColor Yellow
            Write-Host "   Total Entries: $totalEntries" -ForegroundColor White
            Write-Host "   LLM Requests: $requests" -ForegroundColor White
            Write-Host "   LLM Responses: $responses" -ForegroundColor White
            Write-Host "   Errors: $errors" -ForegroundColor $(if ($errors -gt 0) { "Red" } else { "White" })
            Write-Host "   Total Tokens Used: $totalTokens" -ForegroundColor White
            
            if ($providers.Count -gt 0) {
                Write-Host "   Providers Used:" -ForegroundColor Cyan
                foreach ($provider in $providers.Keys) {
                    Write-Host "     - $provider`: $($providers[$provider]) requests" -ForegroundColor Gray
                }
            }
            
            if ($models.Count -gt 0) {
                Write-Host "   Models Used:" -ForegroundColor Cyan
                foreach ($model in $models.Keys) {
                    Write-Host "     - $model`: $($models[$model]) requests" -ForegroundColor Gray
                }
            }
            
            if ($agents.Count -gt 0) {
                Write-Host "   Agents Used:" -ForegroundColor Cyan
                foreach ($agent in $agents.Keys) {
                    Write-Host "     - $agent`: $($agents[$agent]) requests" -ForegroundColor Gray
                }
            }
        }
        catch {
            Write-Host "❌ Error analyzing log file: $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host ""
        Write-Host "⚠️  Step 5: Internal log file not found at: $logFile" -ForegroundColor Yellow
        Write-Host "   This might indicate that internal logging is not working properly." -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Failed to get updated logging stats" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 === Test Complete ===" -ForegroundColor Green
Write-Host "Internal LLM logging system test finished!" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Check the logs directory for internal_logs_*.log files" -ForegroundColor Gray
Write-Host "   2. Verify that LLM requests and responses are being captured" -ForegroundColor Gray
Write-Host "   3. Review token usage and performance metrics" -ForegroundColor Gray
Write-Host "   4. Monitor log file rotation and compression" -ForegroundColor Gray
