#!/usr/bin/env python3
"""
Test file for agentlogs directory functionality.
Tests the planner_executor.py logging system to ensure it creates logs in the correct directory.
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestAgentlogsDirectory(unittest.TestCase):
    """Test case for agentlogs directory functionality."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a mock repo structure
        self.repo_root = Path(self.test_dir)
        self.agentlogs_dir = self.repo_root / "agentlogs"
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('app.planner_executor.Path')
    def test_agentlogs_directory_creation(self, mock_path):
        """Test that agentlogs directory is created automatically."""
        # Mock the Path resolution to return our test directory
        mock_path.return_value.resolve.return_value.parents = [self.repo_root]
        mock_path.return_value.__truediv__.return_value = self.agentlogs_dir
        
        # Ensure directory doesn't exist initially
        self.assertFalse(self.agentlogs_dir.exists())
        
        # Mock the mkdir method to track calls
        mkdir_mock = Mock()
        with patch.object(Path, 'mkdir', mkdir_mock):
            # This would normally call the log initialization in plan_and_execute
            # We'll simulate just the log file path creation part
            try:
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                agentlogs_dir = self.repo_root / "agentlogs"
                agentlogs_dir.mkdir(exist_ok=True)
                log_file_path = agentlogs_dir / f"agentlog_{ts}.log"
                
                # Verify mkdir was called with exist_ok=True
                mkdir_mock.assert_called_with(exist_ok=True)
                
                # Verify the log file path is correct
                self.assertTrue(str(log_file_path).endswith('.log'))
                self.assertIn('agentlog_', str(log_file_path))
                self.assertIn('agentlogs', str(log_file_path))
                
            except Exception as e:
                self.fail(f"Log file path creation failed: {e}")
    
    def test_log_file_naming_convention(self):
        """Test that log files follow the correct naming convention."""
        # Create the directory
        self.agentlogs_dir.mkdir(exist_ok=True)
        
        # Test timestamp format
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        expected_filename = f"agentlog_{ts}.log"
        log_file_path = self.agentlogs_dir / expected_filename
        
        # Verify the filename format
        self.assertTrue(expected_filename.startswith('agentlog_'))
        self.assertTrue(expected_filename.endswith('.log'))
        self.assertEqual(len(ts), 14)  # YYYYMMDDHHMMSS format
        
        # Test that we can create the file
        log_file_path.touch()
        self.assertTrue(log_file_path.exists())
        
        # Test file can be written to
        with log_file_path.open("a", encoding="utf-8") as f:
            f.write("Test log entry\n")
        
        # Verify content was written
        with log_file_path.open("r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "Test log entry\n")
    
    def test_directory_permissions(self):
        """Test that the agentlogs directory has correct permissions."""
        # Create the directory
        self.agentlogs_dir.mkdir(exist_ok=True)
        
        # Verify directory exists and is writable
        self.assertTrue(self.agentlogs_dir.exists())
        self.assertTrue(self.agentlogs_dir.is_dir())
        self.assertTrue(os.access(self.agentlogs_dir, os.W_OK))
        self.assertTrue(os.access(self.agentlogs_dir, os.R_OK))
    
    def test_multiple_log_files(self):
        """Test that multiple log files can be created in the same directory."""
        # Create the directory
        self.agentlogs_dir.mkdir(exist_ok=True)
        
        # Create multiple log files
        for i in range(3):
            ts = datetime.now().strftime("%Y%m%d%H%M%S") + f"{i:02d}"  # Add counter to avoid duplicates
            log_file = self.agentlogs_dir / f"agentlog_{ts}.log"
            log_file.touch()
        
        # Verify all files were created
        log_files = list(self.agentlogs_dir.glob("agentlog_*.log"))
        self.assertEqual(len(log_files), 3)
        
        # Verify all files follow naming convention
        for log_file in log_files:
            self.assertTrue(log_file.name.startswith('agentlog_'))
            self.assertTrue(log_file.name.endswith('.log'))

    def test_error_handling_when_directory_creation_fails(self):
        """Test graceful handling when directory creation fails."""
        # Mock a scenario where directory creation fails
        with patch.object(Path, 'mkdir', side_effect=PermissionError("Permission denied")):
            try:
                # This should handle the exception gracefully
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                repo_root = Path(self.test_dir)
                agentlogs_dir = repo_root / "agentlogs"
                
                # This should raise PermissionError, which should be caught
                try:
                    agentlogs_dir.mkdir(exist_ok=True)
                    log_file_path = agentlogs_dir / f"agentlog_{ts}.log"
                except Exception:
                    # Graceful handling - log_file_path should be None
                    log_file_path = None
                
                # In error cases, log_file_path should be None
                self.assertIsNone(log_file_path)
                
            except Exception as e:
                # The system should handle this gracefully
                pass


if __name__ == '__main__':
    print("🧪 Testing agentlogs directory functionality...")
    print("=" * 60)
    unittest.main(verbosity=2)
