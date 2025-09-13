#!/usr/bin/env python3
"""
Production startup script for PepGenX OpenAI Wrapper.

This script provides a production-ready way to start the application
with proper configuration validation and error handling.
"""

import os
import sys
import signal
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, using system environment variables only")

try:
    import uvicorn
    from app.core.config import settings
    from app.core.logging import setup_logging, get_logger
    from app.core.auth import check_auth_health
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    sys.exit(1)


def validate_environment():
    """
    Validate that all required environment variables and files are present.
    
    Raises:
        SystemExit: If validation fails
    """
    print("🔍 Validating environment configuration...")
    
    errors = []
    warnings = []
    
    # Check required environment variables
    required_vars = [
        "PEPGENX_API_URL",
        "PEPGENX_PROJECT_ID", 
        "PEPGENX_TEAM_ID",
        "PEPGENX_API_KEY",
        "OPENAI_WRAPPER_API_KEYS",
        "SECRET_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Check OKTA token file
    token_file = settings.okta_token_file_path
    if not token_file.exists():
        errors.append(f"OKTA token file not found: {token_file}")
    elif not token_file.is_file():
        errors.append(f"OKTA token path is not a file: {token_file}")
    else:
        try:
            import json
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            if 'access_token' not in token_data:
                errors.append("OKTA token file missing 'access_token' field")
            else:
                print(f"✅ OKTA token file validated: {token_file}")
        except json.JSONDecodeError:
            errors.append(f"OKTA token file is not valid JSON: {token_file}")
        except Exception as e:
            errors.append(f"Error reading OKTA token file: {e}")
    
    # Check API keys format
    try:
        api_keys = settings.api_keys_list
        if not api_keys:
            errors.append("No API keys configured")
        else:
            for i, key in enumerate(api_keys):
                if not key.startswith("sk-"):
                    errors.append(f"API key {i+1} has invalid format (must start with 'sk-')")
            print(f"✅ {len(api_keys)} API key(s) configured")
    except Exception as e:
        errors.append(f"Error validating API keys: {e}")
    
    # Check log level
    if settings.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        warnings.append(f"Invalid log level: {settings.log_level}, using INFO")
    
    # Check ports
    if not (1 <= settings.openai_wrapper_port <= 65535):
        errors.append(f"Invalid port number: {settings.openai_wrapper_port}")
    
    # Print results
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if errors:
        print("\n❌ Validation failed with errors:")
        for error in errors:
            print(f"   - {error}")
        print("\nPlease fix the above errors and try again.")
        sys.exit(1)
    
    print("✅ Environment validation passed!")


def check_dependencies():
    """
    Check that all required dependencies are available.
    
    Raises:
        SystemExit: If dependencies are missing
    """
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import uvicorn
        print(f"✅ Uvicorn {uvicorn.__version__}")
    except ImportError:
        missing_deps.append("uvicorn")
    
    try:
        import httpx
        print(f"✅ HTTPX {httpx.__version__}")
    except ImportError:
        missing_deps.append("httpx")
    
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__}")
    except ImportError:
        missing_deps.append("pydantic")
    
    try:
        import structlog
        print(f"✅ Structlog {structlog.__version__}")
    except ImportError:
        missing_deps.append("structlog")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ All dependencies available!")


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main startup function."""
    print("🚀 Starting PepGenX OpenAI Wrapper")
    print("=" * 50)
    
    # Setup signal handlers
    setup_signal_handlers()
    
    # Check dependencies
    check_dependencies()
    
    # Validate environment
    validate_environment()
    
    # Setup logging
    print("📝 Setting up logging...")
    setup_logging()
    logger = get_logger("startup")
    logger.info("Logging configured", level=settings.log_level, format=settings.log_format)
    
    # Check authentication system
    print("🔐 Checking authentication system...")
    try:
        auth_health = check_auth_health()
        logger.info("Authentication system status", **auth_health)
        print("✅ Authentication system ready")
    except Exception as e:
        logger.error("Authentication system check failed", error=str(e))
        print(f"❌ Authentication system error: {e}")
        sys.exit(1)
    
    # Print configuration summary
    print("\n📋 Configuration Summary:")
    print(f"   Host: {settings.openai_wrapper_host}")
    print(f"   Port: {settings.openai_wrapper_port}")
    print(f"   Log Level: {settings.log_level}")
    print(f"   Log Format: {settings.log_format}")
    print(f"   PepGenX API: {settings.pepgenx_api_url}")
    print(f"   CORS Origins: {settings.cors_origins}")
    print(f"   Rate Limit: {settings.rate_limit_requests_per_minute} req/min")
    print(f"   Metrics Enabled: {settings.enable_metrics}")
    
    # Start the server
    print("\n🌟 Starting server...")
    logger.info("Starting PepGenX OpenAI Wrapper server")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=settings.openai_wrapper_host,
            port=settings.openai_wrapper_port,
            log_level=settings.log_level.lower(),
            access_log=True,
            server_header=False,
            date_header=False,
            # Production settings
            loop="uvloop" if os.name != "nt" else "asyncio",  # Use uvloop on Unix
            http="httptools" if os.name != "nt" else "h11",   # Use httptools on Unix
            workers=1,  # Single worker for now, can be increased
            backlog=2048,
            timeout_keep_alive=5,
            timeout_graceful_shutdown=30,
        )
    except Exception as e:
        logger.error("Failed to start server", error=str(e), exc_info=True)
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
