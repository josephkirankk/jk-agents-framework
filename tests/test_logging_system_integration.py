#!/usr/bin/env python3
"""
Integration test file for both logging systems.
Tests that both agentlogs and agents_direct_logs work together correctly.
"""

import os
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta
import sys
import time

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.direct_agent_logger import DirectAgentLogger


class TestLoggingSystemIntegration(unittest.TestCase):
    """Integration test case for both logging systems."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a mock repo structure
        self.repo_root = Path(self.test_dir)
        self.agentlogs_dir = self.repo_root / "agentlogs"
        self.agents_direct_logs_dir = self.repo_root / "agents_direct_logs"
        
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_both_directories_created(self):
        """Test that both log directories can be created simultaneously."""
        # Create both directories
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Verify both exist
        self.assertTrue(self.agentlogs_dir.exists())
        self.assertTrue(self.agents_direct_logs_dir.exists())
        
        # Verify they are separate directories
        self.assertNotEqual(self.agentlogs_dir, self.agents_direct_logs_dir)
    
    def test_log_files_separation(self):
        """Test that different log types go to their respective directories."""
        # Create both directories
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Create sample log files in each directory
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Regular agent log
        regular_log = self.agentlogs_dir / f"agentlog_{ts}.log"
        regular_log.write_text("Regular agent execution log\n")
        
        # Direct agent log  
        direct_log = self.agents_direct_logs_dir / f"direct_agentlog_{ts}.log"
        direct_log.write_text("Direct agent communication log\n")
        
        # Verify files are in correct locations
        self.assertTrue(regular_log.exists())
        self.assertTrue(direct_log.exists())
        
        # Verify content separation
        self.assertEqual(regular_log.read_text(), "Regular agent execution log\n")
        self.assertEqual(direct_log.read_text(), "Direct agent communication log\n")
    
    def test_concurrent_logging_both_systems(self):
        """Test that both logging systems can operate concurrently."""
        # Create both directories
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Simulate concurrent logging operations
        base_ts = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create multiple files in both directories
        for i in range(3):
            ts = f"{base_ts}{i:02d}"
            
            # Regular agent logs
            regular_log = self.agentlogs_dir / f"agentlog_{ts}.log"
            regular_log.write_text(f"Execution log {i}\nTimestamp: {ts}\n")
            
            # Direct agent logs
            direct_log = self.agents_direct_logs_dir / f"direct_agentlog_{ts}.log"
            direct_log.write_text(f"Direct log {i}\nTimestamp: {ts}\n")
        
        # Verify all files were created
        regular_logs = list(self.agentlogs_dir.glob("agentlog_*.log"))
        direct_logs = list(self.agents_direct_logs_dir.glob("direct_agentlog_*.log"))
        
        self.assertEqual(len(regular_logs), 3)
        self.assertEqual(len(direct_logs), 3)
        
        # Verify no cross-contamination
        for log_file in regular_logs:
            self.assertTrue(log_file.parent == self.agentlogs_dir)
            self.assertTrue(log_file.name.startswith('agentlog_'))
            
        for log_file in direct_logs:
            self.assertTrue(log_file.parent == self.agents_direct_logs_dir)
            self.assertTrue(log_file.name.startswith('direct_agentlog_'))
    
    def test_log_directory_isolation(self):
        """Test that the two log directories don't interfere with each other."""
        # Create both directories
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Fill one directory with many files
        ts_base = datetime.now().strftime("%Y%m%d%H%M")
        for i in range(10):
            regular_log = self.agentlogs_dir / f"agentlog_{ts_base}{i:02d}.log"
            regular_log.write_text(f"Regular log content {i}")
        
        # Add few files to the other directory  
        for i in range(3):
            direct_log = self.agents_direct_logs_dir / f"direct_agentlog_{ts_base}{i:02d}.log"
            direct_log.write_text(f"Direct log content {i}")
        
        # Verify counts are correct and isolated
        regular_count = len(list(self.agentlogs_dir.glob("*.log")))
        direct_count = len(list(self.agents_direct_logs_dir.glob("*.log")))
        
        self.assertEqual(regular_count, 10)
        self.assertEqual(direct_count, 3)
        
        # Verify no files leaked between directories
        regular_files = list(self.agentlogs_dir.iterdir())
        direct_files = list(self.agents_direct_logs_dir.iterdir())
        
        for f in regular_files:
            self.assertTrue(f.name.startswith('agentlog_'))
            self.assertFalse(f.name.startswith('direct_agentlog_'))
            
        for f in direct_files:
            self.assertTrue(f.name.startswith('direct_agentlog_'))
            self.assertFalse(f.name.startswith('agentlog_') and not f.name.startswith('direct_agentlog_'))
    
    def test_real_world_scenario(self):
        """Test a realistic scenario with both logging systems active."""
        # Create both directories
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Simulate a real workflow
        workflow_start = datetime.now()
        
        # Step 1: Start agent execution (regular log)
        ts1 = workflow_start.strftime("%Y%m%d%H%M%S")
        execution_log = self.agentlogs_dir / f"agentlog_{ts1}.log"
        execution_log.write_text(f"""
=== Agent Execution Started ===
Timestamp: {ts1}
Request: List 10 names
Supervisor: Analyzing request...
Python Agent: Generating name list...
Human Response: Formatting response...
=== Execution Complete ===
""")
        
        # Step 2: Direct agent communications (direct log)
        ts2 = (workflow_start + timedelta(seconds=1)).strftime("%Y%m%d%H%M%S")
        direct_log = self.agents_direct_logs_dir / f"direct_agentlog_{ts2}.log"
        direct_log.write_text(f"""
[{ts2}] AGENT: supervisor
[{ts2}] ACTION: plan_request
[{ts2}] PAYLOAD: {{"request": "list 10 names", "complexity": "simple"}}
[{ts2}] AGENT: python_exec_agent
[{ts2}] ACTION: execute_code
[{ts2}] PAYLOAD: {{"code": "names = ['Alice', 'Bob', ...]", "result": "success"}}
[{ts2}] AGENT: human_response_agent
[{ts2}] ACTION: format_response
[{ts2}] PAYLOAD: {{"response": "Here are 10 names...", "status": "complete"}}
""")
        
        # Step 3: Another execution (regular log)
        ts3 = (workflow_start + timedelta(seconds=5)).strftime("%Y%m%d%H%M%S")
        execution_log2 = self.agentlogs_dir / f"agentlog_{ts3}.log"
        execution_log2.write_text(f"""
=== Agent Execution Started ===
Timestamp: {ts3}
Request: Assign roll numbers
Context: Using previous names from Turn-1
Supervisor: Context-aware planning...
Python Agent: Assigning roll numbers...
Human Response: Formatting with continuity...
=== Execution Complete ===
""")
        
        # Verify the workflow created the expected files
        execution_logs = list(self.agentlogs_dir.glob("agentlog_*.log"))
        direct_logs = list(self.agents_direct_logs_dir.glob("direct_agentlog_*.log"))
        
        self.assertEqual(len(execution_logs), 2)
        self.assertEqual(len(direct_logs), 1)
        
        # Verify content integrity
        execution_content1 = execution_log.read_text()
        execution_content2 = execution_log2.read_text()
        direct_content = direct_log.read_text()
        
        self.assertIn("List 10 names", execution_content1)
        self.assertIn("Assign roll numbers", execution_content2)
        self.assertIn("Using previous names", execution_content2)
        self.assertIn("python_exec_agent", direct_content)
        self.assertIn("human_response_agent", direct_content)
    
    def test_gitignore_compliance(self):
        """Test that log directories are properly ignored by git."""
        # Create both directories with files
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Create sample files
        (self.agentlogs_dir / "test_log.log").write_text("test")
        (self.agents_direct_logs_dir / "test_direct_log.log").write_text("test")
        
        # Read the actual .gitignore file
        gitignore_path = Path(__file__).resolve().parent.parent / ".gitignore"
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            
            # Verify our directories are in .gitignore
            self.assertIn("agentlogs/", gitignore_content)
            self.assertIn("agents_direct_logs/", gitignore_content)
        else:
            self.skipTest(".gitignore file not found")
    
    def test_cleanup_and_maintenance(self):
        """Test log cleanup scenarios for both directories."""
        # Create both directories
        self.agentlogs_dir.mkdir(exist_ok=True)
        self.agents_direct_logs_dir.mkdir(exist_ok=True)
        
        # Create old and new log files
        old_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d%H%M%S")
        new_date = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create old files
        old_regular = self.agentlogs_dir / f"agentlog_{old_date}.log"
        old_direct = self.agents_direct_logs_dir / f"direct_agentlog_{old_date}.log"
        old_regular.write_text("old regular log")
        old_direct.write_text("old direct log")
        
        # Create new files
        new_regular = self.agentlogs_dir / f"agentlog_{new_date}.log"
        new_direct = self.agents_direct_logs_dir / f"direct_agentlog_{new_date}.log"
        new_regular.write_text("new regular log")
        new_direct.write_text("new direct log")
        
        # Verify all files exist
        self.assertTrue(old_regular.exists())
        self.assertTrue(old_direct.exists())
        self.assertTrue(new_regular.exists())
        self.assertTrue(new_direct.exists())
        
        # Simulate cleanup (remove old files)
        old_regular.unlink()
        old_direct.unlink()
        
        # Verify cleanup worked correctly
        self.assertFalse(old_regular.exists())
        self.assertFalse(old_direct.exists())
        self.assertTrue(new_regular.exists())
        self.assertTrue(new_direct.exists())


if __name__ == '__main__':
    print("🧪 Testing logging system integration...")
    print("=" * 60)
    unittest.main(verbosity=2)
