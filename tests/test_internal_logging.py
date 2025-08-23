"""
Tests for the internal LLM logging system.

This module contains comprehensive tests for the internal logging system,
including configuration, HTTP interception, and integration with various
LLM providers.
"""

import json
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import httpx
import aiohttp

# Import the modules to test
from app.internal_logger import (
    InternalLogger,
    InternalLogConfig,
    LogLevel,
    LLMProvider,
    get_internal_logger
)
from app.internal_logging_config import (
    InternalLoggingConfigManager,
    get_config_manager,
    get_internal_logging_config
)
from app.llm_interceptor import (
    InterceptedHttpxClient,
    InterceptedAsyncHttpxClient,
    InterceptedAioHttpSession
)
from app.internal_logging_integration import (
    AgentLoggingContext,
    initialize_internal_logging,
    get_logging_stats
)


class TestInternalLogConfig:
    """Test the internal logging configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = InternalLogConfig()
        
        assert config.enabled is True
        assert config.log_level == LogLevel.INFO
        assert config.log_directory == "logs"
        assert config.max_file_size_mb == 100
        assert config.max_files == 10
        assert config.compress_old_files is True
        assert config.mask_sensitive_data is True
        assert len(config.sensitive_keys) > 0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = InternalLogConfig(
            enabled=False,
            log_level=LogLevel.DEBUG,
            log_directory="custom_logs",
            max_file_size_mb=50,
            max_files=5,
            compress_old_files=False,
            mask_sensitive_data=False
        )
        
        assert config.enabled is False
        assert config.log_level == LogLevel.DEBUG
        assert config.log_directory == "custom_logs"
        assert config.max_file_size_mb == 50
        assert config.max_files == 5
        assert config.compress_old_files is False
        assert config.mask_sensitive_data is False


class TestInternalLogger:
    """Test the internal logger functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = InternalLogConfig(
            enabled=True,
            log_level=LogLevel.DEBUG,
            log_directory=self.temp_dir,
            max_file_size_mb=1,  # Small size for testing rotation
            max_files=3
        )
        self.logger = InternalLogger(self.config)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        assert self.logger.config == self.config
        assert self.logger.log_dir == Path(self.temp_dir)
        assert self.logger._current_log_file is not None
        assert self.logger._current_log_file.exists()
    
    def test_log_file_creation(self):
        """Test log file creation with metadata."""
        log_files = list(self.logger.log_dir.glob("internal_logs_*.log"))
        assert len(log_files) == 1
        
        # Check metadata in log file
        with open(log_files[0], 'r', encoding='utf-8') as f:
            first_line = f.readline()
            metadata = json.loads(first_line)
            
        assert metadata["log_type"] == "internal_llm_logger"
        assert metadata["version"] == "1.0"
        assert "created_at" in metadata
        assert "config" in metadata
    
    def test_sensitive_data_masking(self):
        """Test sensitive data masking."""
        test_data = {
            "api-key": "secret123",
            "authorization": "Bearer token123",
            "normal_field": "normal_value",
            "nested": {
                "password": "secret456",
                "public_data": "public_value"
            }
        }
        
        masked_data = self.logger._mask_sensitive_data(test_data)
        
        assert masked_data["api-key"] == "***MASKED***"
        assert masked_data["authorization"] == "***MASKED***"
        assert masked_data["normal_field"] == "normal_value"
        assert masked_data["nested"]["password"] == "***MASKED***"
        assert masked_data["nested"]["public_data"] == "public_value"
    
    def test_llm_interaction_context(self):
        """Test LLM interaction logging context."""
        with self.logger.log_llm_interaction(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            agent_name="test_agent",
            user_input="test query"
        ) as ctx:
            # Log a request
            ctx.log_request(
                endpoint="https://api.openai.com/v1/chat/completions",
                method="POST",
                headers={"Authorization": "Bearer test"},
                payload={"model": "gpt-4", "messages": []}
            )
            
            # Log a response
            ctx.log_response(
                status_code=200,
                headers={"Content-Type": "application/json"},
                payload={"choices": [{"message": {"content": "response"}}]},
                token_usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            )
        
        # Check that logs were written
        log_files = list(self.logger.log_dir.glob("internal_logs_*.log"))
        assert len(log_files) == 1
        
        with open(log_files[0], 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Should have metadata + request + response = 3 lines
        assert len(lines) >= 3
        
        # Check request log
        request_log = json.loads(lines[1])
        assert request_log["log_type"] == "llm_request"
        assert request_log["provider"] == "openai"
        assert request_log["model"] == "gpt-4"
        assert request_log["agent_name"] == "test_agent"
        
        # Check response log
        response_log = json.loads(lines[2])
        assert response_log["log_type"] == "llm_response"
        assert response_log["status_code"] == 200
        assert response_log["token_usage"]["total_tokens"] == 15
    
    def test_log_stats(self):
        """Test log statistics."""
        stats = self.logger.get_log_stats()
        
        assert stats["enabled"] is True
        assert stats["log_level"] == "debug"
        assert stats["total_log_files"] >= 1
        assert stats["total_size_bytes"] > 0
        assert stats["log_directory"] == self.temp_dir


class TestConfigManager:
    """Test the configuration manager."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            "INTERNAL_LOGGING_ENABLED": "false",
            "INTERNAL_LOGGING_LEVEL": "error",
            "INTERNAL_LOGGING_DIR": self.temp_dir,
            "INTERNAL_LOGGING_MAX_FILE_SIZE_MB": "50"
        }):
            config_manager = InternalLoggingConfigManager()
            config = config_manager.get_config()
            
            assert config.enabled is False
            assert config.log_level == LogLevel.ERROR
            assert config.log_directory == self.temp_dir
            assert config.max_file_size_mb == 50
    
    def test_file_configuration(self):
        """Test loading configuration from file."""
        config_file = Path(self.temp_dir) / "config.json"
        config_data = {
            "internal_logging": {
                "enabled": False,
                "log_level": "debug",
                "log_directory": self.temp_dir,
                "max_file_size_mb": 25
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config_manager = InternalLoggingConfigManager(str(config_file))
        config = config_manager.get_config()
        
        assert config.enabled is False
        assert config.log_level == LogLevel.DEBUG
        assert config.log_directory == self.temp_dir
        assert config.max_file_size_mb == 25
    
    def test_runtime_configuration_update(self):
        """Test updating configuration at runtime."""
        config_manager = InternalLoggingConfigManager()
        
        # Update a configuration value
        config_manager.set_config_value("max_file_size_mb", 200)
        
        config = config_manager.get_config()
        assert config.max_file_size_mb == 200
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        config_manager = InternalLoggingConfigManager()
        
        # Test invalid value
        with pytest.raises(ValueError):
            config_manager.set_config_value("max_file_size_mb", -1)
        
        # Test invalid key
        with pytest.raises(KeyError):
            config_manager.set_config_value("invalid_key", "value")


class TestHttpInterceptors:
    """Test HTTP request/response interceptors."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = InternalLogConfig(
            enabled=True,
            log_level=LogLevel.DEBUG,
            log_directory=self.temp_dir
        )

        # Mock the global logger
        with patch('app.llm_interceptor.get_internal_logger') as mock_get_logger:
            self.mock_logger = Mock()
            # Make the mock logger support context manager protocol
            self.mock_logger.log_llm_interaction.return_value.__enter__ = Mock()
            self.mock_logger.log_llm_interaction.return_value.__exit__ = Mock()
            mock_get_logger.return_value = self.mock_logger
            self.intercepted_client = InterceptedHttpxClient()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('httpx.Client.request')
    def test_openai_request_interception(self, mock_request):
        """Test interception of OpenAI API requests."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"choices": [{"message": {"content": "test"}}]}'
        mock_response.json.return_value = {"choices": [{"message": {"content": "test"}}]}
        mock_response.is_success = True
        mock_request.return_value = mock_response
        
        # Set agent context
        self.intercepted_client.set_agent_context("test_agent", "test query")
        
        # Make request to OpenAI
        response = self.intercepted_client.request(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            json={"model": "gpt-4", "messages": [{"role": "user", "content": "test"}]},
            headers={"Authorization": "Bearer test-key"}
        )
        
        # Verify the request was intercepted and logged
        assert self.mock_logger.log_llm_interaction.called
        assert response == mock_response
    
    def test_non_llm_request_passthrough(self):
        """Test that non-LLM requests pass through without logging."""
        with patch('httpx.Client.request') as mock_request:
            mock_response = Mock()
            mock_request.return_value = mock_response
            
            response = self.intercepted_client.request(
                "GET",
                "https://example.com/api/data"
            )
            
            # Should not have called the logger
            assert not self.mock_logger.log_llm_interaction.called
            assert response == mock_response


class TestIntegration:
    """Test integration with the agent system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_agent_logging_context(self):
        """Test agent logging context manager."""
        with patch('app.internal_logging_integration.set_agent_context_for_clients') as mock_set_context:
            with AgentLoggingContext("test_agent", "test query", "test-correlation-id"):
                # Context should be set
                mock_set_context.assert_called_with(
                    agent_name="test_agent",
                    user_input="test query",
                    correlation_id="test-correlation-id"
                )

            # Context should be cleared on exit (called with positional args)
            mock_set_context.assert_called_with("", "", None)
    
    @patch('app.internal_logging_integration.get_internal_logger')
    @patch('app.internal_logging_integration.get_internal_logging_config')
    def test_logging_stats(self, mock_get_config, mock_get_logger):
        """Test getting logging statistics."""
        # Mock config
        mock_config = Mock()
        mock_config.enabled = True
        mock_config.log_level = LogLevel.INFO
        mock_config.max_file_size_mb = 100
        mock_config.max_files = 10
        mock_config.compress_old_files = True
        mock_config.mask_sensitive_data = True
        mock_get_config.return_value = mock_config
        
        # Mock logger stats
        mock_logger = Mock()
        mock_logger.get_log_stats.return_value = {
            "enabled": True,
            "log_level": "info",
            "current_log_file": "/path/to/log.log",
            "total_log_files": 2,
            "total_size_bytes": 1024,
            "total_size_mb": 0.001,
            "log_directory": "/path/to/logs"
        }
        mock_get_logger.return_value = mock_logger
        
        stats = get_logging_stats()
        
        assert stats["enabled"] is True
        assert stats["config"]["log_level"] == "info"
        assert stats["total_log_files"] == 2
        assert stats["total_size_bytes"] == 1024


if __name__ == "__main__":
    pytest.main([__file__])
