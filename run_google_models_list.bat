@echo off
REM Google Models Listing Program - Windows Batch Script
REM This script sets up the environment and runs the Google models listing program

echo ========================================
echo Google Models Listing Program
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Make sure Python is installed and in PATH
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if Google API key is set
if "%GOOGLE_API_KEY%"=="" if "%GEMINI_API_KEY%"=="" (
    echo.
    echo WARNING: No API key found!
    echo Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable
    echo.
    echo Example:
    echo   set GOOGLE_API_KEY=your_api_key_here
    echo.
    echo Or get an API key from: https://aistudio.google.com/
    echo.
    echo Running demo version instead...
    echo.
    python test_google_models_demo.py
    pause
    exit /b 0
)

REM Install required packages
echo Installing required packages...
pip install -q google-genai aiohttp requests python-dotenv

REM Run the main program
echo.
echo Running Google Models Listing Program...
echo.
python list_google_models.py

echo.
echo Program completed. Check the generated files:
echo - JSON file: google_models_*.json
echo - Log file: google_models_list_*.log
echo.
pause
