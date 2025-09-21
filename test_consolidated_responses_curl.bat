@echo off
REM Test script for the consolidated responses API endpoint using curl (Windows)
REM This script tests the new /consolidated-responses endpoint with various scenarios

set BASE_URL=http://127.0.0.1:8000
set ENDPOINT=/consolidated-responses
set FULL_URL=%BASE_URL%%ENDPOINT%

echo 🚀 Starting Consolidated Responses API Tests with curl
echo ============================================================
echo Testing endpoint: %FULL_URL%
echo.

REM Test 1: Get all submissions (no date filters)
echo 🔍 Test 1: Get all submissions (no filters)
echo 📝 Payload: {}
echo 📊 Response:
curl -X POST "%FULL_URL%" -H "Content-Type: application/json" -H "Accept: application/json" -d "{}" -w "%%{http_code}" --max-time 30
echo.
echo ----------------------------------------
echo.

REM Test 2: Get submissions from today
echo 🔍 Test 2: Get submissions from today
echo 📝 Payload: {"start_date": "2025-09-20T00:00:00Z"}
echo 📊 Response:
curl -X POST "%FULL_URL%" -H "Content-Type: application/json" -H "Accept: application/json" -d "{\"start_date\": \"2025-09-20T00:00:00Z\"}" -w "%%{http_code}" --max-time 30
echo.
echo ----------------------------------------
echo.

REM Test 3: Get submissions for a specific date range
echo 🔍 Test 3: Get submissions for date range
echo 📝 Payload: {"start_date": "2025-09-20T00:00:00Z", "end_date": "2025-09-20T23:59:59Z"}
echo 📊 Response:
curl -X POST "%FULL_URL%" -H "Content-Type: application/json" -H "Accept: application/json" -d "{\"start_date\": \"2025-09-20T00:00:00Z\", \"end_date\": \"2025-09-20T23:59:59Z\"}" -w "%%{http_code}" --max-time 30
echo.
echo ----------------------------------------
echo.

REM Test 4: Test invalid date format
echo 🔍 Test 4: Test invalid date format
echo 📝 Payload: {"start_date": "invalid-date"}
echo 📊 Response:
curl -X POST "%FULL_URL%" -H "Content-Type: application/json" -H "Accept: application/json" -d "{\"start_date\": \"invalid-date\"}" -w "%%{http_code}" --max-time 30
echo.
echo ----------------------------------------
echo.

REM Test 5: Test invalid date range (start > end)
echo 🔍 Test 5: Test invalid date range
echo 📝 Payload: {"start_date": "2025-09-21T00:00:00Z", "end_date": "2025-09-20T00:00:00Z"}
echo 📊 Response:
curl -X POST "%FULL_URL%" -H "Content-Type: application/json" -H "Accept: application/json" -d "{\"start_date\": \"2025-09-21T00:00:00Z\", \"end_date\": \"2025-09-20T00:00:00Z\"}" -w "%%{http_code}" --max-time 30
echo.
echo ----------------------------------------
echo.

REM Test 6: Get submissions from last week
echo 🔍 Test 6: Get submissions from last week
echo 📝 Payload: {"start_date": "2025-09-13T00:00:00Z"}
echo 📊 Response:
curl -X POST "%FULL_URL%" -H "Content-Type: application/json" -H "Accept: application/json" -d "{\"start_date\": \"2025-09-13T00:00:00Z\"}" -w "%%{http_code}" --max-time 30
echo.
echo ----------------------------------------
echo.

echo 🏁 All curl tests completed!
echo ============================================================
pause
