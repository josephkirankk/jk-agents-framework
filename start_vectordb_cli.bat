@echo off
REM VectorDB CLI Launcher for Windows
REM This script provides easy access to the VectorDB CLI with various options

echo.
echo ========================================
echo    VectorDB Wrapper CLI Launcher
echo ========================================
echo.

REM Check if virtual environment exists and activate it
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo.
)

REM Check command line arguments
if "%1"=="--help" goto :help
if "%1"=="-h" goto :help
if "%1"=="--sample" goto :sample
if "%1"=="--test" goto :test
if "%1"=="--usage" goto :usage

REM Default: Start interactive CLI
echo Starting VectorDB CLI...
echo Type 'help' for available commands or 'quit' to exit.
echo.
python -m vectordb_wrapper.cli %*
goto :end

:help
echo Usage: start_vectordb_cli.bat [OPTIONS]
echo.
echo Options:
echo   --help, -h     Show this help message
echo   --sample       Create sample JSON file for testing
echo   --test         Run CLI functionality test
echo   --usage        Show detailed CLI usage examples
echo   --url URL      Start CLI with custom base URL
echo.
echo Examples:
echo   start_vectordb_cli.bat
echo   start_vectordb_cli.bat --url http://localhost:9000
echo   start_vectordb_cli.bat --sample
echo   start_vectordb_cli.bat --test
goto :end

:sample
echo Creating sample JSON file...
python -m vectordb_wrapper.cli --create-sample
echo.
echo Sample file created! You can now use it with the 'batch' command in CLI.
goto :end

:test
echo Running CLI functionality test...
python test_vectordb_cli.py
goto :end

:usage
echo Showing detailed CLI usage...
python test_vectordb_cli.py --usage
goto :end

:end
echo.
pause
