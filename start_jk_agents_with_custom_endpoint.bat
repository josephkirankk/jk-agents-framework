@echo off
echo Setting up environment for custom OpenAI endpoint integration...

REM Set environment variables for custom OpenAI endpoint
set OPENAI_BASE_URL=http://127.0.0.1:8080/v1
set OPENAI_API_KEY=sk-test-key1

echo OPENAI_BASE_URL=%OPENAI_BASE_URL%
echo OPENAI_API_KEY=%OPENAI_API_KEY%

echo Starting JK-Agents API server...
uvicorn app.api:app --host 0.0.0.0 --port 8001 --reload
