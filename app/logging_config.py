"""
Logging Configuration for jk-agents-core

Provides centralized logging configuration with:
- Console output for immediate feedback
- File logging in agentlogs/ directory
- Configurable log levels
- Automatic log rotation
- Structured log format
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    include_timestamp: bool = True
) -> Path:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
        log_dir: Directory for log files (default: agentlogs/)
        console_output: Whether to output to console
        include_timestamp: Whether to include timestamp in log filename
        
    Returns:
        Path to the log file (if file logging is enabled)
    """
    # Determine log directory
    if log_dir is None:
        # Find repository root (go up until we find .git or stop at reasonable depth)
        current = Path(__file__).resolve()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
                log_dir = parent / "agentlogs"
                break
        else:
            # Fallback to current directory
            log_dir = Path.cwd() / "agentlogs"
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with timestamp
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        log_filename = f"agentlog_{timestamp}.log"
    else:
        log_filename = "agentlog.log"
    
    log_file_path = log_dir / log_filename
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s - %(name)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Capture everything to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Log the logging configuration
        root_logger.info(f"Logging configured - File: {log_file_path}")
        root_logger.info(f"Log level: {log_level}, Console: {console_output}, File: {log_to_file}")
    
    return log_file_path


def get_log_directory() -> Path:
    """
    Get the configured log directory path.
    
    Returns:
        Path to the agentlogs directory
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent / "agentlogs"
    return Path.cwd() / "agentlogs"


def list_recent_logs(count: int = 10) -> list[Path]:
    """
    List recent log files.
    
    Args:
        count: Number of recent log files to return
        
    Returns:
        List of Path objects for recent log files
    """
    log_dir = get_log_directory()
    if not log_dir.exists():
        return []
    
    # Get all log files sorted by modification time (newest first)
    log_files = sorted(
        log_dir.glob("agentlog_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    return log_files[:count]


def print_log_info():
    """Print information about log file locations."""
    log_dir = get_log_directory()
    recent_logs = list_recent_logs(5)
    
    print("\n" + "=" * 80)
    print("📋 LOGGING INFORMATION")
    print("=" * 80)
    print(f"\n📂 Log Directory: {log_dir}")
    print(f"   Exists: {'✓' if log_dir.exists() else '✗'}")
    
    if recent_logs:
        print(f"\n📝 Recent Log Files ({len(recent_logs)}):")
        for i, log_file in enumerate(recent_logs, 1):
            size_kb = log_file.stat().st_size / 1024
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"   {i}. {log_file.name}")
            print(f"      Size: {size_kb:.1f} KB | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n⚠️  No log files found")
    
    print("\n💡 Usage:")
    print("   # View latest log")
    print(f"   tail -f {log_dir}/agentlog_*.log | tail -n 100")
    print("\n   # View errors only")
    print(f"   grep ERROR {log_dir}/agentlog_*.log")
    print("=" * 80 + "\n")


def configure_module_log_levels():
    """Configure specific log levels for noisy modules."""
    # Reduce noise from verbose libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Keep important modules at INFO
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("mcp_loader").setLevel(logging.INFO)
    logging.getLogger("deep_agent_adapter").setLevel(logging.INFO)


# Convenience function for quick setup
def quick_setup(verbose: bool = False) -> Path:
    """
    Quick logging setup with sensible defaults.
    
    Args:
        verbose: If True, set log level to DEBUG
        
    Returns:
        Path to the log file
    """
    log_level = "DEBUG" if verbose else "INFO"
    log_file = setup_logging(
        log_level=log_level,
        log_to_file=True,
        console_output=True
    )
    configure_module_log_levels()
    return log_file


if __name__ == "__main__":
    # When run as a script, show log information
    print_log_info()
