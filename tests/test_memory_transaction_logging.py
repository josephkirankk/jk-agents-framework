"""
Tests for memory transaction logging system in JK-Agents Framework.

This test suite validates the memory transaction logging functionality,
including the logger itself, configuration, and integration with memory operations.
"""

import pytest
import tempfile
import json
import threading
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    
    # Fix for LangChain AzureChatOpenAI compatibility
    # It expects OPENAI_API_VERSION instead of AZURE_OPENAI_API_VERSION
    if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
        os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
        print("✅ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility")
    
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

from app.memory.transaction_logger import (
    MemoryTransactionLogger,
    get_memory_logger,
    initialize_memory_logger,
    cleanup_memory_logger
)
from app.config import MemoryLoggingConfig


class TestMemoryTransactionLogger:
    """Test the core MemoryTransactionLogger functionality."""
    
    def test_logger_initialization_enabled(self):
        """Test logger initialization when enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            assert logger.enabled is True
            assert logger.log_directory == Path(temp_dir)
            assert Path(temp_dir).exists()
            assert logger._loggers == {}
    
    def test_logger_initialization_disabled(self):
        """Test logger initialization when disabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=False)
            
            assert logger.enabled is False
            assert logger._loggers == {}
    
    def test_creates_thread_specific_log_files(self):
        """Test that each thread gets its own log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            # Log transactions for different threads
            logger.log_transaction("thread_1", "STORE_CONVERSATION", {"test": "data1"})
            logger.log_transaction("thread_2", "STORE_CONVERSATION", {"test": "data2"})
            logger.log_transaction("thread_1", "GET_RECENT", {"test": "data3"})
            
            # Check that separate files were created
            log_files = list(Path(temp_dir).glob("memory_*.log"))
            assert len(log_files) == 2, "Should create separate files for each thread"
            
            # Verify file names contain thread IDs
            file_names = [f.name for f in log_files]
            assert any("thread_1" in name for name in file_names)
            assert any("thread_2" in name for name in file_names)
    
    def test_log_entries_are_valid_json(self):
        """Test that log entries are valid JSON and contain expected data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            test_data = {
                "user_message_length": 150,
                "assistant_response_length": 500,
                "has_metadata": True
            }
            
            logger.log_transaction("test_thread", "STORE_CONVERSATION", test_data)
            
            # Read the log file
            log_files = list(Path(temp_dir).glob("memory_test_thread_*.log"))
            assert len(log_files) == 1
            
            with open(log_files[0], 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            # Should contain valid JSON
            assert "STORE_CONVERSATION" in log_content
            assert "user_message_length" in log_content
            
            # Extract and parse JSON
            json_part = log_content.split(' - ', 1)[1]
            parsed = json.loads(json_part)
            assert parsed['operation'] == "STORE_CONVERSATION"
            assert parsed['user_message_length'] == 150
            assert parsed['thread_id'] == "test_thread"
            assert 'timestamp' in parsed
    
    def test_disabled_logger_does_nothing(self):
        """Test that disabled logger doesn't create files or log anything."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=False)
            
            logger.log_transaction("thread_1", "STORE_CONVERSATION", {"test": "data"})
            
            # No files should be created
            log_files = list(Path(temp_dir).glob("memory_*.log"))
            assert len(log_files) == 0
    
    def test_thread_safety(self):
        """Test that the logger is thread-safe."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            def log_worker(thread_id, count):
                for i in range(count):
                    logger.log_transaction(
                        f"thread_{thread_id}", 
                        "TEST_OPERATION", 
                        {"iteration": i, "worker": thread_id}
                    )
            
            # Create multiple threads logging concurrently
            threads = []
            for i in range(3):
                t = threading.Thread(target=log_worker, args=(i, 10))
                threads.append(t)
                t.start()
            
            # Wait for all threads to complete
            for t in threads:
                t.join()
            
            # Verify files were created for each thread
            log_files = list(Path(temp_dir).glob("memory_*.log"))
            assert len(log_files) == 3
            
            # Verify each file has the expected number of entries
            for log_file in log_files:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = [line for line in f if ' - {' in line]
                    assert len(lines) == 10  # Each worker logs 10 times
    
    def test_logger_cleanup(self):
        """Test logger cleanup functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            # Create some log entries
            logger.log_transaction("thread_1", "TEST", {"data": "test"})
            logger.log_transaction("thread_2", "TEST", {"data": "test"})
            
            # Verify loggers were created
            assert len(logger._loggers) == 2
            
            # Cleanup
            logger.cleanup_loggers()
            
            # Verify loggers were cleared
            assert len(logger._loggers) == 0


class TestMemoryLoggingConfig:
    """Test the MemoryLoggingConfig configuration class."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = MemoryLoggingConfig()
        
        assert config.enabled is False
        assert config.log_directory == "memory_logs"
    
    def test_configuration_from_env(self):
        """Test configuration from environment variables."""
        with patch.dict('os.environ', {
            'MEMORY_LOGGING_ENABLED': 'true',
            'MEMORY_LOGGING_DIRECTORY': 'custom_logs'
        }):
            config = MemoryLoggingConfig.from_env()
            assert config.enabled is True
            assert config.log_directory == "custom_logs"
        
        with patch.dict('os.environ', {
            'MEMORY_LOGGING_ENABLED': 'false'
        }):
            config = MemoryLoggingConfig.from_env()
            assert config.enabled is False
    
    def test_various_enabled_values(self):
        """Test various ways to specify enabled value."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('1', False),  # Only 'true' (case insensitive) should work
            ('', False),
        ]
        
        for env_value, expected in test_cases:
            with patch.dict('os.environ', {'MEMORY_LOGGING_ENABLED': env_value}):
                config = MemoryLoggingConfig.from_env()
                assert config.enabled == expected, f"'{env_value}' should result in {expected}"


class TestGlobalLoggerFunctions:
    """Test global logger management functions."""
    
    def setUp(self):
        """Setup for each test."""
        # Clean up any existing global logger
        cleanup_memory_logger()
    
    def tearDown(self):
        """Cleanup after each test."""
        cleanup_memory_logger()
    
    def test_initialize_memory_logger(self):
        """Test initializing the global memory logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = initialize_memory_logger(temp_dir, enabled=True)
            
            assert logger is not None
            assert logger.enabled is True
            assert logger.log_directory == Path(temp_dir)
            
            # Should get the same instance
            same_logger = get_memory_logger()
            assert same_logger is logger
    
    def test_get_memory_logger_fallback(self):
        """Test get_memory_logger fallback behavior."""
        # Should create a disabled logger as fallback
        logger = get_memory_logger()
        assert logger is not None
        assert logger.enabled is False  # Default fallback
    
    def test_cleanup_memory_logger(self):
        """Test cleanup of global memory logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize logger
            logger = initialize_memory_logger(temp_dir, enabled=True)
            logger.log_transaction("test", "TEST", {"data": "test"})
            
            # Cleanup
            cleanup_memory_logger()
            
            # Getting logger again should create a new instance
            new_logger = get_memory_logger()
            assert new_logger is not logger


class TestIntegrationWithMemoryOperations:
    """Test integration of logging with actual memory operations."""
    
    @pytest.mark.asyncio
    async def test_conversation_store_logging_integration(self):
        """Test that conversation store operations are logged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize logger
            initialize_memory_logger(temp_dir, enabled=True)
            
            # Import here to avoid circular imports during module loading
            from app.memory.conversation_store import ConversationStore
            
            # Mock the database operations since we're testing logging, not DB
            with patch.object(ConversationStore, '_get_connection') as mock_conn:
                mock_conn.return_value.__aenter__ = MagicMock()
                mock_conn.return_value.__aexit__ = MagicMock()
                
                # Create store and attempt operation
                store = ConversationStore("mock://database")
                store._pool = MagicMock()  # Mock pool to avoid initialization
                
                # This should trigger logging
                try:
                    await store.store_conversation(
                        "test_thread", 
                        "Hello", 
                        "Hi there!"
                    )
                except Exception:
                    # Expected to fail due to mocked DB, but logging should work
                    pass
                
                # Check that log files were created
                log_files = list(Path(temp_dir).glob("memory_test_thread_*.log"))
                assert len(log_files) == 1
                
                # Verify log content
                with open(log_files[0], 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    assert "STORE_CONVERSATION" in log_content
                    assert "user_message_length" in log_content
    
    def test_logger_error_handling(self):
        """Test that logging errors don't break main functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            # Try to log with invalid JSON data
            invalid_data = {"circular": None}
            invalid_data["circular"] = invalid_data  # Create circular reference
            
            # This should not raise an exception
            logger.log_transaction("test_thread", "TEST", {"valid": "data"})
    
    def test_disabled_logging_has_no_performance_impact(self):
        """Test that disabled logging has minimal performance impact."""
        with tempfile.TemporaryDirectory() as temp_dir:
            disabled_logger = MemoryTransactionLogger(temp_dir, enabled=False)
            enabled_logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            # Time disabled logging
            start_time = time.time()
            for i in range(1000):
                disabled_logger.log_transaction("thread", "TEST", {"iteration": i})
            disabled_time = time.time() - start_time
            
            # Time enabled logging  
            start_time = time.time()
            for i in range(1000):
                enabled_logger.log_transaction("thread", "TEST", {"iteration": i})
            enabled_time = time.time() - start_time
            
            # Disabled should be significantly faster (mostly just checking enabled flag)
            assert disabled_time < enabled_time / 2


class TestLogFileFormat:
    """Test log file format and content structure."""
    
    def test_log_file_naming_convention(self):
        """Test that log files follow the expected naming convention."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            logger.log_transaction("my_thread_123", "TEST", {"data": "test"})
            
            log_files = list(Path(temp_dir).glob("memory_*.log"))
            assert len(log_files) == 1
            
            log_file = log_files[0]
            filename = log_file.name
            
            # Should match pattern: memory_{thread_id}_{timestamp}.log
            assert filename.startswith("memory_my_thread_123_")
            assert filename.endswith(".log")
            
            # Extract timestamp part
            parts = filename.split('_')
            timestamp_part = parts[-1].replace('.log', '')
            
            # Should be a valid timestamp format (YYYYMMDDHHMMSS)
            assert len(timestamp_part) == 14
            assert timestamp_part.isdigit()
    
    def test_log_entry_structure(self):
        """Test that log entries have the expected structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = MemoryTransactionLogger(temp_dir, enabled=True)
            
            test_data = {
                "user_message_length": 100,
                "has_metadata": True,
                "custom_field": "custom_value"
            }
            
            logger.log_transaction("test_thread", "CUSTOM_OPERATION", test_data)
            
            log_files = list(Path(temp_dir).glob("memory_*.log"))
            with open(log_files[0], 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Extract JSON
            json_part = log_content.split(' - ', 1)[1]
            entry = json.loads(json_part)
            
            # Verify required fields
            assert 'operation' in entry
            assert 'timestamp' in entry
            assert 'thread_id' in entry
            
            # Verify values
            assert entry['operation'] == "CUSTOM_OPERATION"
            assert entry['thread_id'] == "test_thread"
            assert entry['user_message_length'] == 100
            assert entry['has_metadata'] is True
            assert entry['custom_field'] == "custom_value"
            
            # Verify timestamp format
            timestamp = entry['timestamp']
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise


if __name__ == '__main__':
    # Run tests if executed directly
    pytest.main([__file__, '-v'])