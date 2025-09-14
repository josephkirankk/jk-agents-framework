@echo off
REM PepGenX CLI Examples for Windows
REM Make sure you have a valid okta_token.json file before running these commands

echo ============================================================
echo PepGenX CLI Examples
echo ============================================================

echo.
echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo 1. List all available models:
echo python scripts\pepgenx_cli.py list
echo.

echo 2. Test OpenAI GPT-4o with default prompts:
echo python scripts\pepgenx_cli.py test --model gpt-4o
echo.

echo 3. Test Anthropic Claude with custom prompt:
echo python scripts\pepgenx_cli.py test --model claude-3-5-sonnet --user-prompt "Write a haiku about AI"
echo.

echo 4. Test with specific system prompt:
echo python scripts\pepgenx_cli.py test --model gpt-4o-mini --system-prompt 1 --user-prompt "Calculate 15 * 23"
echo.

echo 5. Test reasoning model:
echo python scripts\pepgenx_cli.py test --model o1-mini --user-prompt "Solve this: If all roses are flowers and some flowers are red, can we conclude that some roses are red?"
echo.

echo ============================================================
echo To run any of these commands, copy and paste them into your terminal
echo Make sure your okta_token.json file is valid and not expired
echo ============================================================

pause
