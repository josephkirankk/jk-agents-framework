@echo off
echo === JK-Agents Memory Persistence Test ===
echo.

echo === Test 1: Store Information ===
echo Sending: I have 10 restaurants. Please remember this.
curl -X POST "http://localhost:8000/worker" -H "Content-Type: application/json" -d "{\"agent_name\": \"simple_test_agent\", \"input\": \"I have 10 restaurants. Please remember this.\", \"config_path\": \"c:\\\\JK\\\\dev\\\\repo\\\\jk-agents\\\\config\\\\simple_test.yaml\"}" > response1.json
echo.

echo Response from Test 1:
type response1.json
echo.

echo === Test 2: Recall Information (Same Thread) ===
echo Extracting thread_id from response1.json...

REM Extract thread_id using PowerShell
for /f "delims=" %%i in ('powershell -Command "(Get-Content response1.json | ConvertFrom-Json).thread_id"') do set THREAD_ID=%%i

echo Using thread_id: %THREAD_ID%
echo Sending: How many restaurants do I have?

curl -X POST "http://localhost:8000/worker" -H "Content-Type: application/json" -d "{\"agent_name\": \"simple_test_agent\", \"input\": \"How many restaurants do I have?\", \"config_path\": \"c:\\\\JK\\\\dev\\\\repo\\\\jk-agents\\\\config\\\\simple_test.yaml\", \"thread_id\": \"%THREAD_ID%\"}" > response2.json
echo.

echo Response from Test 2:
type response2.json
echo.

echo === Test 3: Memory Isolation (Different Thread) ===
echo Sending: How many restaurants do I have? (using different thread_id)

curl -X POST "http://localhost:8000/worker" -H "Content-Type: application/json" -d "{\"agent_name\": \"simple_test_agent\", \"input\": \"How many restaurants do I have?\", \"config_path\": \"c:\\\\JK\\\\dev\\\\repo\\\\jk-agents\\\\config\\\\simple_test.yaml\", \"thread_id\": \"different-thread-123\"}" > response3.json
echo.

echo Response from Test 3:
type response3.json
echo.

echo === Test 4: Memory Statistics ===
curl -X GET "http://localhost:8000/memory/stats" > memory_stats.json
echo Memory Statistics:
type memory_stats.json
echo.

echo === Test Complete ===
echo Check the responses above to verify memory persistence is working.

REM Clean up temporary files
del response1.json response2.json response3.json memory_stats.json 2>nul
