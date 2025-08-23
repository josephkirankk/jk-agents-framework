"""
Internal LLM Interaction Logger

This module provides comprehensive logging for all LLM API interactions including
raw requests, responses, token usage, and error handling. Supports multiple
LLM providers (OpenAI, Azure AI, Google Gemini, etc.) with structured JSON logging.
"""

from __future__ import annotations
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import os
import gzip
from contextlib import contextmanager

# Configure module logger
log = logging.getLogger("internal_logger")


class LogLevel(Enum):
    """Log levels for internal logging."""
    DISABLED = "disabled"
    ERROR = "error"
    INFO = "info"
    DEBUG = "debug"


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GOOGLE_GEMINI = "google_gemini"
    ANTHROPIC = "anthropic"
    UNKNOWN = "unknown"


@dataclass
class RequestLogEntry:
    """Structure for logging LLM requests."""
    timestamp: str
    request_id: str
    provider: str
    model: str
    endpoint: str
    method: str
    headers: Dict[str, Any]
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    agent_name: Optional[str] = None
    user_input: Optional[str] = None


@dataclass
class ResponseLogEntry:
    """Structure for logging LLM responses."""
    timestamp: str
    request_id: str
    provider: str
    model: str
    status_code: int
    headers: Dict[str, Any]
    payload: Dict[str, Any]
    response_time_ms: float
    token_usage: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class InternalLogConfig:
    """Configuration for internal logging."""
    enabled: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_directory: str = "logs"
    max_file_size_mb: int = 100
    max_files: int = 10
    compress_old_files: bool = True
    include_request_headers: bool = True
    include_response_headers: bool = True
    include_payload_content: bool = True
    mask_sensitive_data: bool = True
    sensitive_keys: List[str] = None
    correlation_id_header: str = "X-Correlation-ID"
    enable_performance_metrics: bool = True
    enable_error_tracking: bool = True

    def __post_init__(self):
        if self.sensitive_keys is None:
            self.sensitive_keys = [
                "api-key", "authorization", "ocp-apim-subscription-key",
                "x-api-key", "bearer", "token", "key", "secret", "password"
            ]


class InternalLogger:
    """
    Comprehensive internal logger for LLM interactions.
    
    Features:
    - Structured JSON logging
    - Multi-provider support
    - Thread-safe operations
    - Log rotation and compression
    - Configurable sensitivity masking
    - Request/response correlation
    """

    def __init__(self, config: Optional[InternalLogConfig] = None):
        """Initialize the internal logger."""
        self.config = config or InternalLogConfig()
        self._lock = threading.Lock()
        self._current_log_file: Optional[Path] = None
        self._current_file_size = 0
        
        # Create logs directory if it doesn't exist
        self.log_dir = Path(self.config.log_directory)
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize current log file
        self._initialize_log_file()

    def _initialize_log_file(self) -> None:
        """Initialize a new log file with timestamp."""
        if not self.config.enabled:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self._current_log_file = self.log_dir / f"internal_logs_{timestamp}.log"
        self._current_file_size = 0
        
        # Write initial metadata
        metadata = {
            "log_type": "internal_llm_logger",
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "config": {
                "log_level": self.config.log_level.value,
                "max_file_size_mb": self.config.max_file_size_mb,
                "max_files": self.config.max_files
            }
        }
        self._write_log_entry(metadata)

    def _should_rotate_log(self) -> bool:
        """Check if log file should be rotated."""
        if not self._current_log_file or not self._current_log_file.exists():
            return True
        
        size_mb = self._current_file_size / (1024 * 1024)
        return size_mb >= self.config.max_file_size_mb

    def _rotate_log_file(self) -> None:
        """Rotate the current log file."""
        if self._current_log_file and self._current_log_file.exists():
            # Compress old file if configured
            if self.config.compress_old_files:
                self._compress_log_file(self._current_log_file)
        
        # Clean up old files
        self._cleanup_old_files()
        
        # Initialize new log file
        self._initialize_log_file()

    def _compress_log_file(self, file_path: Path) -> None:
        """Compress a log file using gzip."""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            file_path.unlink()  # Remove original file
        except Exception as e:
            log.warning(f"Failed to compress log file {file_path}: {e}")

    def _cleanup_old_files(self) -> None:
        """Remove old log files beyond the configured limit."""
        try:
            log_files = list(self.log_dir.glob("internal_logs_*.log*"))
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only the most recent files
            for old_file in log_files[self.config.max_files:]:
                old_file.unlink()
        except Exception as e:
            log.warning(f"Failed to cleanup old log files: {e}")

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in the payload."""
        if not self.config.mask_sensitive_data:
            return data
        
        masked_data = data.copy()
        
        def mask_recursive(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {
                    key: "***MASKED***" if any(sensitive in key.lower() 
                                            for sensitive in self.config.sensitive_keys)
                    else mask_recursive(value)
                    for key, value in obj.items()
                }
            elif isinstance(obj, list):
                return [mask_recursive(item) for item in obj]
            else:
                return obj
        
        return mask_recursive(masked_data)

    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        """Write a log entry to the current log file."""
        if not self.config.enabled or not self._current_log_file:
            return
        
        try:
            log_line = json.dumps(entry, ensure_ascii=False, separators=(',', ':'))
            log_line += '\n'
            
            with open(self._current_log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
            self._current_file_size += len(log_line.encode('utf-8'))
            
            # Check if rotation is needed
            if self._should_rotate_log():
                self._rotate_log_file()
                
        except Exception as e:
            log.error(f"Failed to write log entry: {e}")

    @contextmanager
    def log_llm_interaction(
        self,
        provider: Union[LLMProvider, str],
        model: str,
        agent_name: Optional[str] = None,
        user_input: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Context manager for logging LLM interactions.
        
        Usage:
            with logger.log_llm_interaction(LLMProvider.OPENAI, "gpt-4") as ctx:
                # Make API call
                response = api_call()
                ctx.log_response(response)
        """
        if isinstance(provider, str):
            try:
                provider = LLMProvider(provider.lower())
            except ValueError:
                provider = LLMProvider.UNKNOWN
        
        request_id = str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())
        
        class InteractionContext:
            def __init__(self, logger_instance):
                self.logger = logger_instance
                self.request_id = request_id
                self.correlation_id = correlation_id
                self.provider = provider
                self.model = model
                self.agent_name = agent_name
                self.user_input = user_input
                self.start_time = datetime.now(timezone.utc)
            
            def log_request(
                self,
                endpoint: str,
                method: str,
                headers: Dict[str, Any],
                payload: Dict[str, Any]
            ) -> None:
                """Log the outgoing request."""
                if self.logger.config.log_level == LogLevel.DISABLED:
                    return
                
                request_entry = RequestLogEntry(
                    timestamp=self.start_time.isoformat(),
                    request_id=self.request_id,
                    provider=self.provider.value,
                    model=self.model,
                    endpoint=endpoint,
                    method=method,
                    headers=self.logger._mask_sensitive_data(headers) if self.logger.config.include_request_headers else {},
                    payload=self.logger._mask_sensitive_data(payload) if self.logger.config.include_payload_content else {},
                    correlation_id=self.correlation_id,
                    agent_name=self.agent_name,
                    user_input=self.user_input
                )
                
                log_entry = {
                    "log_type": "llm_request",
                    **asdict(request_entry)
                }
                
                with self.logger._lock:
                    self.logger._write_log_entry(log_entry)
            
            def log_response(
                self,
                status_code: int,
                headers: Dict[str, Any],
                payload: Dict[str, Any],
                token_usage: Optional[Dict[str, Any]] = None,
                error_message: Optional[str] = None
            ) -> None:
                """Log the incoming response."""
                if self.logger.config.log_level == LogLevel.DISABLED:
                    return
                
                end_time = datetime.now(timezone.utc)
                response_time_ms = (end_time - self.start_time).total_seconds() * 1000
                
                response_entry = ResponseLogEntry(
                    timestamp=end_time.isoformat(),
                    request_id=self.request_id,
                    provider=self.provider.value,
                    model=self.model,
                    status_code=status_code,
                    headers=self.logger._mask_sensitive_data(headers) if self.logger.config.include_response_headers else {},
                    payload=self.logger._mask_sensitive_data(payload) if self.logger.config.include_payload_content else {},
                    response_time_ms=response_time_ms,
                    token_usage=token_usage,
                    error_message=error_message,
                    correlation_id=self.correlation_id
                )
                
                log_entry = {
                    "log_type": "llm_response",
                    **asdict(response_entry)
                }
                
                with self.logger._lock:
                    self.logger._write_log_entry(log_entry)
        
        ctx = InteractionContext(self)
        try:
            yield ctx
        except Exception as e:
            # Log any exceptions that occur during the interaction
            ctx.log_response(
                status_code=500,
                headers={},
                payload={},
                error_message=str(e)
            )
            raise

    def get_current_log_file(self) -> Optional[str]:
        """Get the path to the current log file."""
        return str(self._current_log_file) if self._current_log_file else None

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about the logging system."""
        log_files = list(self.log_dir.glob("internal_logs_*.log*"))
        total_size = sum(f.stat().st_size for f in log_files if f.exists())

        return {
            "enabled": self.config.enabled,
            "log_level": self.config.log_level.value,
            "current_log_file": self.get_current_log_file(),
            "total_log_files": len(log_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "log_directory": str(self.log_dir)
        }


# Global logger instance
_global_logger: Optional[InternalLogger] = None


def get_internal_logger() -> InternalLogger:
    """Get the global internal logger instance."""
    global _global_logger
    if _global_logger is None:
        # Load configuration from environment variables
        config = InternalLogConfig(
            enabled=os.getenv("INTERNAL_LOGGING_ENABLED", "true").lower() == "true",
            log_level=LogLevel(os.getenv("INTERNAL_LOGGING_LEVEL", "info").lower()),
            log_directory=os.getenv("INTERNAL_LOGGING_DIR", "logs"),
            max_file_size_mb=int(os.getenv("INTERNAL_LOGGING_MAX_FILE_SIZE_MB", "100")),
            max_files=int(os.getenv("INTERNAL_LOGGING_MAX_FILES", "10")),
            compress_old_files=os.getenv("INTERNAL_LOGGING_COMPRESS", "true").lower() == "true",
            mask_sensitive_data=os.getenv("INTERNAL_LOGGING_MASK_SENSITIVE", "true").lower() == "true"
        )
        _global_logger = InternalLogger(config)
    return _global_logger


def configure_internal_logger(config: InternalLogConfig) -> None:
    """Configure the global internal logger."""
    global _global_logger
    _global_logger = InternalLogger(config)
