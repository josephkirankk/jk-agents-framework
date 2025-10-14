"""
Logging Configuration for the JK-Agents Framework.

This module provides a consistent logging setup across the application.
"""

import logging
import os
import sys
from pathlib import Path

def setup_logging(level=None, log_file=None):
    """
    Configure logging for the application.
    
    Args:
        level: The logging level (default: INFO)
        log_file: Optional path to a log file
    """
    # Determine log level from environment or default to INFO
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    numeric_level = getattr(logging, level, logging.INFO)
    
    # Basic configuration with formatting
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )
    
    # Set up specific loggers with appropriate levels
    for logger_name, logger_level in [
        ("app", numeric_level),
        ("uvicorn", logging.WARNING),
        ("api", numeric_level),
        ("llm_payload_logger", numeric_level),
    ]:
        logging.getLogger(logger_name).setLevel(logger_level)
    
    # Suppress noisy third-party logs
    for logger_name, logger_level in [
        ("httpx", logging.WARNING),
        ("httpcore", logging.WARNING),
        ("chromadb", logging.WARNING),
        ("urllib3", logging.WARNING),
    ]:
        logging.getLogger(logger_name).setLevel(logger_level)
    
    # Log initial setup
    logging.getLogger("app").info(f"Logging configured with level: {level}")
