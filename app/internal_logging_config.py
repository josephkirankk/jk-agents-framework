"""
Internal Logging Configuration Management

This module provides configuration management for the internal LLM logging system,
including environment variable loading, validation, and runtime configuration updates.
"""

from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

from .internal_logger import LogLevel, InternalLogConfig

log = logging.getLogger("internal_logging_config")


class ConfigSource(Enum):
    """Sources for configuration values."""
    ENVIRONMENT = "environment"
    FILE = "file"
    RUNTIME = "runtime"
    DEFAULT = "default"


@dataclass
class ConfigValue:
    """Represents a configuration value with its source and metadata."""
    value: Any
    source: ConfigSource
    description: str
    is_sensitive: bool = False
    validation_func: Optional[callable] = None


class InternalLoggingConfigManager:
    """
    Configuration manager for internal LLM logging system.
    
    Supports:
    - Environment variable configuration
    - JSON file configuration
    - Runtime configuration updates
    - Configuration validation
    - Sensitive data handling
    """
    
    # Configuration schema with defaults and validation
    CONFIG_SCHEMA = {
        "enabled": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Enable/disable internal LLM logging",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "log_level": ConfigValue(
            value=LogLevel.INFO,
            source=ConfigSource.DEFAULT,
            description="Logging level (disabled, error, info, debug)",
            validation_func=lambda x: isinstance(x, (LogLevel, str)) and (
                x in LogLevel if isinstance(x, LogLevel) else x.lower() in [l.value for l in LogLevel]
            )
        ),
        "log_directory": ConfigValue(
            value="logs",
            source=ConfigSource.DEFAULT,
            description="Directory for storing internal log files",
            validation_func=lambda x: isinstance(x, str) and len(x.strip()) > 0
        ),
        "max_file_size_mb": ConfigValue(
            value=100,
            source=ConfigSource.DEFAULT,
            description="Maximum size of each log file in MB",
            validation_func=lambda x: isinstance(x, (int, float)) and x > 0
        ),
        "max_files": ConfigValue(
            value=10,
            source=ConfigSource.DEFAULT,
            description="Maximum number of log files to keep",
            validation_func=lambda x: isinstance(x, int) and x > 0
        ),
        "compress_old_files": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Compress old log files with gzip",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "include_request_headers": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Include HTTP request headers in logs",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "include_response_headers": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Include HTTP response headers in logs",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "include_payload_content": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Include request/response payload content in logs",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "mask_sensitive_data": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Mask sensitive data in logs (API keys, tokens, etc.)",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "sensitive_keys": ConfigValue(
            value=["api-key", "authorization", "ocp-apim-subscription-key", "x-api-key", 
                   "bearer", "token", "key", "secret", "password"],
            source=ConfigSource.DEFAULT,
            description="List of sensitive keys to mask in logs",
            validation_func=lambda x: isinstance(x, list) and all(isinstance(k, str) for k in x)
        ),
        "correlation_id_header": ConfigValue(
            value="X-Correlation-ID",
            source=ConfigSource.DEFAULT,
            description="HTTP header name for correlation ID",
            validation_func=lambda x: isinstance(x, str) and len(x.strip()) > 0
        ),
        "enable_performance_metrics": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Enable performance metrics collection",
            validation_func=lambda x: isinstance(x, bool)
        ),
        "enable_error_tracking": ConfigValue(
            value=True,
            source=ConfigSource.DEFAULT,
            description="Enable detailed error tracking and logging",
            validation_func=lambda x: isinstance(x, bool)
        )
    }
    
    # Environment variable mappings
    ENV_VAR_MAPPING = {
        "enabled": "INTERNAL_LOGGING_ENABLED",
        "log_level": "INTERNAL_LOGGING_LEVEL",
        "log_directory": "INTERNAL_LOGGING_DIR",
        "max_file_size_mb": "INTERNAL_LOGGING_MAX_FILE_SIZE_MB",
        "max_files": "INTERNAL_LOGGING_MAX_FILES",
        "compress_old_files": "INTERNAL_LOGGING_COMPRESS",
        "include_request_headers": "INTERNAL_LOGGING_INCLUDE_REQUEST_HEADERS",
        "include_response_headers": "INTERNAL_LOGGING_INCLUDE_RESPONSE_HEADERS",
        "include_payload_content": "INTERNAL_LOGGING_INCLUDE_PAYLOAD",
        "mask_sensitive_data": "INTERNAL_LOGGING_MASK_SENSITIVE",
        "sensitive_keys": "INTERNAL_LOGGING_SENSITIVE_KEYS",
        "correlation_id_header": "INTERNAL_LOGGING_CORRELATION_HEADER",
        "enable_performance_metrics": "INTERNAL_LOGGING_PERFORMANCE_METRICS",
        "enable_error_tracking": "INTERNAL_LOGGING_ERROR_TRACKING"
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager."""
        self.config_file = Path(config_file) if config_file else None
        self.config_values = self.CONFIG_SCHEMA.copy()
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load configuration from all sources in priority order."""
        # 1. Load from file if specified
        if self.config_file and self.config_file.exists():
            self._load_from_file()
        
        # 2. Load from environment variables (higher priority)
        self._load_from_environment()
        
        # 3. Validate all configuration values
        self._validate_configuration()
    
    def _load_from_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            internal_logging_config = file_config.get("internal_logging", {})
            
            for key, value in internal_logging_config.items():
                if key in self.config_values:
                    self.config_values[key].value = value
                    self.config_values[key].source = ConfigSource.FILE
                    log.debug(f"Loaded config from file: {key} = {value}")
                else:
                    log.warning(f"Unknown configuration key in file: {key}")
                    
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Failed to load configuration from file {self.config_file}: {e}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        for config_key, env_var in self.ENV_VAR_MAPPING.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    # Parse environment value based on expected type
                    parsed_value = self._parse_env_value(config_key, env_value)
                    self.config_values[config_key].value = parsed_value
                    self.config_values[config_key].source = ConfigSource.ENVIRONMENT
                    log.debug(f"Loaded config from env: {config_key} = {parsed_value}")
                except ValueError as e:
                    log.error(f"Invalid environment variable {env_var}: {e}")
    
    def _parse_env_value(self, config_key: str, env_value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        config_item = self.config_values[config_key]
        default_value = config_item.value
        
        # Boolean values
        if isinstance(default_value, bool):
            return env_value.lower() in ("true", "1", "yes", "on")
        
        # Integer values
        elif isinstance(default_value, int):
            return int(env_value)
        
        # Float values
        elif isinstance(default_value, float):
            return float(env_value)
        
        # LogLevel enum
        elif isinstance(default_value, LogLevel):
            return LogLevel(env_value.lower())
        
        # List values (comma-separated)
        elif isinstance(default_value, list):
            return [item.strip() for item in env_value.split(",") if item.strip()]
        
        # String values
        else:
            return env_value
    
    def _validate_configuration(self) -> None:
        """Validate all configuration values."""
        for key, config_item in self.config_values.items():
            if config_item.validation_func:
                try:
                    if not config_item.validation_func(config_item.value):
                        log.error(f"Invalid configuration value for {key}: {config_item.value}")
                        # Reset to default
                        default_config = self.CONFIG_SCHEMA[key]
                        config_item.value = default_config.value
                        config_item.source = ConfigSource.DEFAULT
                except Exception as e:
                    log.error(f"Validation error for {key}: {e}")
    
    def get_config(self) -> InternalLogConfig:
        """Get the current configuration as InternalLogConfig object."""
        config_dict = {}

        for key, config_item in self.config_values.items():
            value = config_item.value
            # Convert string log_level to LogLevel enum
            if key == "log_level" and isinstance(value, str):
                value = LogLevel(value.lower())
            config_dict[key] = value

        return InternalLogConfig(**config_dict)
    
    def get_config_value(self, key: str) -> Any:
        """Get a specific configuration value."""
        if key not in self.config_values:
            raise KeyError(f"Unknown configuration key: {key}")
        return self.config_values[key].value
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value at runtime."""
        if key not in self.config_values:
            raise KeyError(f"Unknown configuration key: {key}")
        
        config_item = self.config_values[key]
        
        # Validate the new value
        if config_item.validation_func and not config_item.validation_func(value):
            raise ValueError(f"Invalid value for {key}: {value}")
        
        config_item.value = value
        config_item.source = ConfigSource.RUNTIME
        log.info(f"Updated configuration: {key} = {value}")
    
    def get_config_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all configuration values."""
        config_info = {}
        
        for key, config_item in self.config_values.items():
            config_info[key] = {
                "value": "***MASKED***" if config_item.is_sensitive else config_item.value,
                "source": config_item.source.value,
                "description": config_item.description,
                "is_sensitive": config_item.is_sensitive,
                "env_var": self.ENV_VAR_MAPPING.get(key)
            }
        
        return config_info
    
    def export_config_template(self, file_path: str) -> None:
        """Export a configuration template file."""
        template = {
            "internal_logging": {
                key: {
                    "value": config_item.value,
                    "description": config_item.description,
                    "env_var": self.ENV_VAR_MAPPING.get(key)
                }
                for key, config_item in self.config_values.items()
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, default=str)
        
        log.info(f"Configuration template exported to {file_path}")
    
    def reload_configuration(self) -> None:
        """Reload configuration from all sources."""
        log.info("Reloading internal logging configuration")
        self._load_configuration()
    
    def validate_log_directory(self) -> bool:
        """Validate that the log directory exists and is writable."""
        log_dir = Path(self.get_config_value("log_directory"))
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = log_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
            return True
            
        except (OSError, PermissionError) as e:
            log.error(f"Log directory validation failed: {e}")
            return False


# Global configuration manager instance
_config_manager: Optional[InternalLoggingConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> InternalLoggingConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = InternalLoggingConfigManager(config_file)
    return _config_manager


def get_internal_logging_config(config_file: Optional[str] = None) -> InternalLogConfig:
    """Get the current internal logging configuration."""
    return get_config_manager(config_file).get_config()


def update_internal_logging_config(**kwargs) -> None:
    """Update internal logging configuration at runtime."""
    config_manager = get_config_manager()
    for key, value in kwargs.items():
        config_manager.set_config_value(key, value)


def reload_internal_logging_config() -> None:
    """Reload internal logging configuration from all sources."""
    global _config_manager
    if _config_manager:
        _config_manager.reload_configuration()


def export_config_template(file_path: str) -> None:
    """Export a configuration template file."""
    get_config_manager().export_config_template(file_path)
