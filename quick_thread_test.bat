@echo off
echo === Quick Thread ID Test ===
echo.

REM Step 1: Start new conversation
echo Step 1: Starting new conversation...
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d "{\"input\": \"Hello! I prefer Italian restaurants. Please remember this.\", \"config_path\": \"c:\\\\JK\\\\dev\\\\repo\\\\jk-agents\\\\config\\\\pep_mcp_sample.yaml\"}" > response1.json
echo Response saved to response1.json
echo.

REM Extract thread_id (you'll need to copy this manually from response1.json)
echo Step 2: Check response1.json and copy the thread_id value
echo Then run the following command with your thread_id:
echo.
echo curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d "{\"input\": \"What cuisine do I prefer?\", \"config_path\": \"c:\\\\JK\\\\dev\\\\repo\\\\jk-agents\\\\config\\\\pep_mcp_sample.yaml\", \"thread_id\": \"YOUR_THREAD_ID_HERE\"}"
echo.
echo Replace YOUR_THREAD_ID_HERE with the actual thread_id from response1.json
echo.

pause
