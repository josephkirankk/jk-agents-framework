"""
Configuration management for the PepGenX OpenAI Wrapper.

This module handles all configuration settings using Pydantic Settings,
supporting environment variables, .env files, and validation.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation and environment variable support."""
    
    # PepGenX API Configuration
    pepgenx_api_url: str = Field(..., description="PepGenX API endpoint URL")
    pepgenx_project_id: str = Field(..., description="PepGenX project ID")
    pepgenx_team_id: str = Field(..., description="PepGenX team ID")
    pepgenx_api_key: str = Field(..., description="PepGenX API key")
    
    # OKTA Token Configuration
    okta_token_file: str = Field(
        default="okta_token.json",
        description="Path to OKTA token JSON file"
    )
    
    # OpenAI Wrapper Configuration
    openai_wrapper_api_keys: str = Field(
        ...,
        description="Comma-separated list of valid API keys for clients"
    )
    openai_wrapper_host: str = Field(default="0.0.0.0", description="Host to bind to")
    openai_wrapper_port: int = Field(default=8000, description="Port to bind to")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # CORS Configuration
    cors_origins: str = Field(default="*", description="CORS allowed origins")
    cors_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_methods: str = Field(
        default="GET,POST,PUT,DELETE,OPTIONS",
        description="CORS allowed methods"
    )
    cors_headers: str = Field(default="*", description="CORS allowed headers")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Rate limit: requests per minute per client"
    )
    rate_limit_burst: int = Field(
        default=10,
        description="Rate limit: burst allowance"
    )
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT signing")
    token_expire_minutes: int = Field(
        default=30,
        description="Token expiration time in minutes"
    )
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL in seconds"
    )
    okta_token_refresh_threshold_minutes: int = Field(
        default=5,
        description="Minutes before OKTA token expiry to refresh"
    )
    
    # HTTP Client Configuration
    http_timeout_seconds: int = Field(
        default=30,
        description="HTTP client timeout in seconds"
    )
    http_max_retries: int = Field(
        default=3,
        description="Maximum HTTP request retries"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @field_validator("openai_wrapper_api_keys")
    @classmethod
    def validate_api_keys(cls, v):
        """Validate that API keys are provided and properly formatted."""
        if not v or not v.strip():
            raise ValueError("At least one API key must be provided")

        keys = [key.strip() for key in v.split(",") if key.strip()]
        if not keys:
            raise ValueError("At least one valid API key must be provided")

        for key in keys:
            if not key.startswith("sk-"):
                raise ValueError(f"API key must start with 'sk-': {key}")

        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()
    
    @property
    def api_keys_list(self) -> List[str]:
        """Get the list of valid API keys."""
        return [key.strip() for key in self.openai_wrapper_api_keys.split(",") if key.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get the list of CORS origins."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Get the list of CORS methods."""
        return [method.strip() for method in self.cors_methods.split(",") if method.strip()]
    
    @property
    def okta_token_file_path(self) -> Path:
        """Get the full path to the OKTA token file."""
        if os.path.isabs(self.okta_token_file):
            return Path(self.okta_token_file)
        
        # Relative to project root (parent of app directory)
        app_dir = Path(__file__).parent.parent
        project_root = app_dir.parent
        return project_root / self.okta_token_file


# Global settings instance - lazy loaded
_settings = None

def get_settings() -> Settings:
    """Get the global settings instance (lazy loaded)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# For backward compatibility
settings = get_settings()
