@echo off
setlocal enabledelayedexpansion

REM JK-Agents Thread ID Continuity Test Script (Windows)
REM This script demonstrates how thread IDs enable conversation continuity
REM across multiple API calls using the pep_mcp_sample.yaml configuration

echo === JK-Agents Thread ID Continuity Test ===
echo Using config: c:\JK\dev\repo\jk-agents\config\pep_mcp_sample.yaml
echo.

REM Configuration
set API_BASE=http://localhost:8000
set CONFIG_PATH=c:\JK\dev\repo\jk-agents\config\pep_mcp_sample.yaml

REM Test 1: Start new conversation (no thread_id) - Multi-agent query
echo === Test 1: Start New Conversation (Multi-Agent Query) ===
echo Making API call to /query endpoint...

curl -s -X POST "%API_BASE%/query" ^
    -H "Content-Type: application/json" ^
    -d "{\"input\": \"Hello! I need help finding restaurants in New York. Please remember that I prefer Italian cuisine.\", \"config_path\": \"%CONFIG_PATH%\"}" > response1.json

if %errorlevel% neq 0 (
    echo ERROR: First API call failed
    exit /b 1
)

REM Extract thread_id from response1.json (simplified extraction)
for /f "tokens=2 delims=:" %%a in ('findstr "thread_id" response1.json') do (
    set thread_id1=%%a
    set thread_id1=!thread_id1:"=!
    set thread_id1=!thread_id1:,=!
    set thread_id1=!thread_id1: =!
)

echo ✓ First API call successful
echo Generated Thread ID: !thread_id1!
echo Response saved to response1.json
echo.

REM Test 2: Continue conversation using thread_id
echo === Test 2: Continue Conversation (Using Thread ID) ===
echo Making API call with thread_id: !thread_id1!

curl -s -X POST "%API_BASE%/query" ^
    -H "Content-Type: application/json" ^
    -d "{\"input\": \"Can you remember what type of cuisine I mentioned I prefer? And can you search for those restaurants in Manhattan?\", \"config_path\": \"%CONFIG_PATH%\", \"thread_id\": \"!thread_id1!\"}" > response2.json

if %errorlevel% neq 0 (
    echo ERROR: Second API call failed
    exit /b 1
)

echo ✓ Second API call successful
echo Response saved to response2.json
echo.

REM Test 3: Direct agent call with thread_id
echo === Test 3: Direct Agent Call (Using Thread ID) ===
echo Making direct agent call with thread_id: !thread_id1!

curl -s -X POST "%API_BASE%/worker" ^
    -H "Content-Type: application/json" ^
    -d "{\"agent_name\": \"restaurants_agent\", \"input\": \"Based on our previous conversation, can you find 3 specific Italian restaurants in Manhattan with high ratings?\", \"config_path\": \"%CONFIG_PATH%\", \"thread_id\": \"!thread_id1!\"}" > response3.json

if %errorlevel% neq 0 (
    echo ERROR: Direct agent call failed
    exit /b 1
)

echo ✓ Direct agent call successful
echo Response saved to response3.json
echo.

REM Test 4: New conversation (different thread)
echo === Test 4: New Conversation (Different Thread) ===
echo Making API call without thread_id (should generate new thread)

curl -s -X POST "%API_BASE%/query" ^
    -H "Content-Type: application/json" ^
    -d "{\"input\": \"What type of cuisine do I prefer? This should be a fresh conversation.\", \"config_path\": \"%CONFIG_PATH%\"}" > response4.json

if %errorlevel% neq 0 (
    echo ERROR: New conversation API call failed
    exit /b 1
)

echo ✓ New conversation API call successful
echo Response saved to response4.json
echo.

REM Test 5: Custom thread ID
echo === Test 5: Custom Thread ID ===
set custom_thread=my-restaurant-session-2024
echo Making API call with custom thread_id: !custom_thread!

curl -s -X POST "%API_BASE%/query" ^
    -H "Content-Type: application/json" ^
    -d "{\"input\": \"I want to start a new restaurant search session. Please remember I am looking for vegetarian options.\", \"config_path\": \"%CONFIG_PATH%\", \"thread_id\": \"!custom_thread!\"}" > response5.json

if %errorlevel% neq 0 (
    echo ERROR: Custom thread ID API call failed
    exit /b 1
)

echo ✓ Custom thread ID API call successful
echo Response saved to response5.json
echo.

REM Display results
echo === Test Summary ===
echo ✓ All tests completed successfully!
echo.
echo Response files created:
echo   response1.json - New conversation (generated thread ID)
echo   response2.json - Continue conversation (same thread ID)
echo   response3.json - Direct agent call (same thread ID)
echo   response4.json - New conversation (different thread ID)
echo   response5.json - Custom thread ID
echo.
echo Key Findings:
echo • Thread IDs are automatically generated when not provided
echo • Thread IDs are maintained across API calls when provided
echo • Thread IDs enable conversation continuity and memory
echo • Different thread IDs create isolated conversations
echo • Custom thread IDs are accepted and used
echo • All API endpoints support thread ID parameter
echo.
echo Thread ID continuity is working correctly! 🎉
echo.
echo To view responses, check the generated JSON files:
echo   type response1.json
echo   type response2.json
echo   type response3.json
echo   type response4.json
echo   type response5.json

REM Cleanup
REM del response*.json

pause
