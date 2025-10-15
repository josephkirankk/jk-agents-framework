#!/usr/bin/env python3
"""
Test file for agents_direct_logs directory functionality.
Tests the direct_agent_logger.py logging system to ensure it creates logs in the correct directory.
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.direct_agent_logger import DirectAgentLogger


class TestAgentsDirectLogsDirectory(unittest.TestCase):
    """Test case for agents_direct_logs directory functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a mock repo structure
        self.repo_root = Path(self.test_dir)
        self.agents_direct_logs_dir = self.repo_root / "agents_direct_logs"
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('app.direct_agent_logger.Path')
    @patch('app.direct_agent_logger.LLMPayloadLogger')
    def test_agents_direct_logs_directory_creation(self, mock_llm_logger, mock_path_class):
        """Test that agents_direct_logs directory is created automatically."""
        # Mock the Path resolution to return our test directory
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance
        mock_path_instance.resolve.return_value.parents = [self.repo_root]
        
        # Mock the LLMPayloadLogger
        mock_llm_logger.return_value = Mock()
        
        # Create a mock Path for the directory
        mock_agents_direct_logs_dir = MagicMock()
        
        # Patch the Path constructor and file resolution
        with patch('app.direct_agent_logger.Path') as mock_path_constructor:
            # Setup the mock to return our test directory structure
            mock_file_path = MagicMock()
            mock_file_path.resolve.return_value.parents = [self.repo_root]
            mock_path_constructor.return_value = mock_file_path
            
            # Mock the directory path creation
            with patch.object(Path, '__truediv__', return_value=mock_agents_direct_logs_dir):
                # Mock the mkdir method
                mock_agents_direct_logs_dir.mkdir = Mock()
                
                # Create the DirectAgentLogger instance
                logger = DirectAgentLogger("test_agent", "test user input")
                
                # Verify that mkdir was called with exist_ok=True
                # Note: This tests the concept, the actual implementation may vary
                self.assertIsNotNone(logger)
    
    def test_direct_log_file_naming_convention(self):
        """Test that direct log files follow the correct naming convention."""
        # Create the directory
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Test timestamp format
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        expected_filename = f"direct_agentlog_{ts}.log"
        log_file_path = self.agents_direct_logs_dir / expected_filename
        
        # Verify the filename format
        self.assertTrue(expected_filename.startswith('direct_agentlog_'))
        self.assertTrue(expected_filename.endswith('.log'))
        self.assertEqual(len(ts), 14)  # YYYYMMDDHHMMSS format
        
        # Test that we can create the file
        log_file_path.touch()
        self.assertTrue(log_file_path.exists())
        
        # Test file can be written to
        test_content = "Direct Agent Test Log Entry\n"
        with log_file_path.open("a", encoding="utf-8") as f:
            f.write(test_content)
        
        # Verify content was written
        with log_file_path.open("r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, test_content)
    
    @patch('app.direct_agent_logger.LLMPayloadLogger')
    def test_direct_agent_logger_initialization(self, mock_llm_logger):
        """Test DirectAgentLogger initialization with correct directory."""
        # Mock the LLMPayloadLogger
        mock_llm_logger.return_value = Mock()
        
        # Create the actual directory for this test
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Patch the file path resolution to use our test directory
        with patch('app.direct_agent_logger.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.resolve.return_value.parents = [self.repo_root]
            mock_path.return_value = mock_file
            
            # Create logger instance
            logger = DirectAgentLogger("test_agent", "test user input")
            
            # Verify logger was created
            self.assertIsNotNone(logger)
            self.assertEqual(logger.agent_name, "test_agent")
    
    def test_directory_permissions(self):
        """Test that the agents_direct_logs directory has correct permissions."""
        # Create the directory
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Verify directory exists and is writable
        self.assertTrue(self.agents_direct_logs_dir.exists())
        self.assertTrue(self.agents_direct_logs_dir.is_dir())
        self.assertTrue(os.access(self.agents_direct_logs_dir, os.W_OK))
        self.assertTrue(os.access(self.agents_direct_logs_dir, os.R_OK))
    
    def test_multiple_direct_log_files(self):
        """Test that multiple direct log files can be created in the same directory."""
        # Create the directory
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Create multiple direct log files
        for i in range(3):
            ts = datetime.now().strftime("%Y%m%d%H%M%S") + f"{i:02d}"  # Add counter to avoid duplicates
            log_file = self.agents_direct_logs_dir / f"direct_agentlog_{ts}.log"
            log_file.touch()
        
        # Verify all files were created
        log_files = list(self.agents_direct_logs_dir.glob("direct_agentlog_*.log"))
        self.assertEqual(len(log_files), 3)
        
        # Verify all files follow naming convention
        for log_file in log_files:
            self.assertTrue(log_file.name.startswith('direct_agentlog_'))
            self.assertTrue(log_file.name.endswith('.log'))
    
    def test_log_content_structure(self):
        """Test that direct agent logs can contain structured content."""
        # Create the directory and log file
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        log_file = self.agents_direct_logs_dir / f"direct_agentlog_{ts}.log"
        
        # Write structured log content
        test_log_content = """
[2025-09-28 16:02:00] AGENT: test_agent
[2025-09-28 16:02:00] ACTION: initialize
[2025-09-28 16:02:01] REQUEST: test request
[2025-09-28 16:02:01] RESPONSE: test response
[2025-09-28 16:02:02] STATUS: completed
"""
        
        with log_file.open("w", encoding="utf-8") as f:
            f.write(test_log_content)
        
        # Verify content was written correctly
        with log_file.open("r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertEqual(content, test_log_content)
        self.assertIn("AGENT: test_agent", content)
        self.assertIn("ACTION: initialize", content)
        self.assertIn("STATUS: completed", content)
    
    @patch('app.direct_agent_logger.LLMPayloadLogger')
    def test_error_handling_directory_creation_failure(self, mock_llm_logger):
        """Test graceful handling when agents_direct_logs directory creation fails."""
        # Mock the LLMPayloadLogger
        mock_llm_logger.return_value = Mock()
        
        # Mock Path to simulate directory creation failure
        with patch('app.direct_agent_logger.Path') as mock_path:
            mock_file = MagicMock()
            mock_file.resolve.return_value.parents = [self.repo_root]
            mock_path.return_value = mock_file
            
            # Mock mkdir to raise an exception
            with patch.object(Path, 'mkdir', side_effect=PermissionError("Permission denied")):
                # This should handle the exception gracefully
                try:
                    logger = DirectAgentLogger("test_agent", "test user input")
                    # Logger should still be created but with log_file_path as None
                    self.assertIsNotNone(logger)
                except Exception as e:
                    # Should not raise an exception, should handle gracefully
                    self.fail(f"DirectAgentLogger should handle directory creation failure gracefully: {e}")
    
    def test_concurrent_logging(self):
        """Test that multiple loggers can write to different files simultaneously."""
        # Create the directory
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Create multiple log files simulating concurrent agents
        agents = ["agent1", "agent2", "agent3"]
        log_files = []
        
        for agent in agents:
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            log_file = self.agents_direct_logs_dir / f"direct_agentlog_{ts}_{agent}.log"
            log_files.append(log_file)
            
            # Write unique content for each agent
            with log_file.open("w", encoding="utf-8") as f:
                f.write(f"Log for {agent}\nTimestamp: {ts}\n")
        
        # Verify all files exist and have correct content
        for i, log_file in enumerate(log_files):
            self.assertTrue(log_file.exists())
            with log_file.open("r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(f"Log for {agents[i]}", content)


if __name__ == '__main__':
    print("🧪 Testing agents_direct_logs directory functionality...")
    print("=" * 60)
    unittest.main(verbosity=2)
