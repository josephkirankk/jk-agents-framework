"""
Memory transaction logger for JK-Agents Framework.

This module provides simple, file-based logging of memory operations per conversation 
thread_id for troubleshooting and debugging purposes.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)


def safe_truncate_content(content: str, max_length: int) -> str:
    """
    Safely truncate content for logging.
    
    Args:
        content: Content to truncate
        max_length: Maximum length allowed
        
    Returns:
        Truncated content with indicator if truncated
    """
    if len(content) <= max_length:
        return content
    return content[:max_length] + "... [TRUNCATED]"


def prepare_content_for_logging(content: str, include_content: bool, max_length: int) -> dict:
    """
    Prepare content data for logging.
    
    Args:
        content: Content to prepare
        include_content: Whether to include actual content
        max_length: Maximum content length
        
    Returns:
        Dictionary with content data
    """
    result = {
        'content_length': len(content),
    }
    
    if include_content:
        result['content'] = safe_truncate_content(content, max_length)
        result['truncated'] = len(content) > max_length
    
    return result


class MemoryTransactionLogger:
    """
    Simple file-based logger for memory transactions.
    
    Creates one log file per conversation thread_id with timestamped entries
    in JSON format for easy analysis and debugging.
    """
    
    def __init__(self, log_directory: str = "memory_logs", enabled: bool = True):
        """
        Initialize the memory transaction logger.
        
        Args:
            log_directory: Directory to store log files
            enabled: Whether logging is enabled
        """
        self.log_directory = Path(log_directory)
        self.enabled = enabled
        self._loggers: Dict[str, logging.Logger] = {}
        self._lock = threading.Lock()
        
        if self.enabled:
            # Create log directory if it doesn't exist
            self.log_directory.mkdir(exist_ok=True)
            logger.info(f"MemoryTransactionLogger initialized, logging to: {self.log_directory}")
    
    def get_logger_for_thread(self, thread_id: str) -> Optional[logging.Logger]:
        """
        Get or create a logger for a specific thread.
        
        Args:
            thread_id: Conversation thread identifier
            
        Returns:
            Logger instance for the thread or None if disabled
        """
        if not self.enabled:
            return None
            
        with self._lock:
            if thread_id in self._loggers:
                return self._loggers[thread_id]
            
            # Create thread-specific logger
            logger_name = f"memory_transaction_{thread_id}"
            thread_logger = logging.getLogger(logger_name)
            thread_logger.setLevel(logging.INFO)
            
            # Remove any existing handlers to avoid duplicates
            thread_logger.handlers.clear()
            
            # Create file handler with timestamp in filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            log_filename = f"memory_{thread_id}_{timestamp}.log"
            log_path = self.log_directory / log_filename
            
            # Create file handler
            handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            thread_logger.addHandler(handler)
            
            # Prevent propagation to avoid duplicate logs
            thread_logger.propagate = False
            
            self._loggers[thread_id] = thread_logger
            logger.debug(f"Created logger for thread {thread_id}: {log_path}")
            
            return thread_logger
    
    def log_transaction(self, thread_id: str, operation: str, data: Dict[str, Any]) -> None:
        """
        Log a memory transaction.
        
        Args:
            thread_id: Conversation thread identifier
            operation: Type of operation (e.g., STORE_CONVERSATION, GET_RECENT)
            data: Additional data about the operation
        """
        if not self.enabled:
            return
            
        try:
            thread_logger = self.get_logger_for_thread(thread_id)
            if thread_logger:
                log_entry = {
                    'operation': operation,
                    'timestamp': datetime.now().isoformat(),
                    'thread_id': thread_id,
                    **data
                }
                
                # Log as formatted JSON for readability
                json_str = json.dumps(log_entry, indent=2, default=str)
                thread_logger.info(json_str)
                
        except Exception as e:
            # Never let logging break the main functionality
            logger.error(f"Failed to log transaction for thread {thread_id}: {e}")
    
    def cleanup_loggers(self) -> None:
        """Clean up logger handlers to prevent resource leaks."""
        with self._lock:
            for thread_logger in self._loggers.values():
                for handler in thread_logger.handlers:
                    handler.close()
                    thread_logger.removeHandler(handler)
            self._loggers.clear()


# Global logger instance
_global_logger: Optional[MemoryTransactionLogger] = None
_logger_lock = threading.Lock()


def get_memory_logger() -> MemoryTransactionLogger:
    """
    Get the global memory transaction logger instance.
    
    Returns:
        MemoryTransactionLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        with _logger_lock:
            if _global_logger is None:
                # Check environment variables first, but also enable by default for better UX
                enabled = (
                    os.getenv('MEMORY_LOGGING_ENABLED', 'true').lower() == 'true'
                )
                log_dir = os.getenv('MEMORY_LOGGING_DIRECTORY', 'memory_logs')
                _global_logger = MemoryTransactionLogger(
                    log_directory=log_dir,
                    enabled=enabled
                )
    
    return _global_logger


def initialize_memory_logger(log_directory: str = "memory_logs", enabled: bool = True) -> MemoryTransactionLogger:
    """
    Initialize the global memory transaction logger.
    
    Args:
        log_directory: Directory to store log files
        enabled: Whether logging is enabled
        
    Returns:
        MemoryTransactionLogger instance
    """
    global _global_logger
    
    with _logger_lock:
        if _global_logger is not None:
            _global_logger.cleanup_loggers()
        
        _global_logger = MemoryTransactionLogger(
            log_directory=log_directory,
            enabled=enabled
        )
        
    return _global_logger


def cleanup_memory_logger() -> None:
    """Clean up the global memory logger."""
    global _global_logger
    
    with _logger_lock:
        if _global_logger is not None:
            _global_logger.cleanup_loggers()
            _global_logger = None