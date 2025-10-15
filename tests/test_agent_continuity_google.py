"""
Test script for Google Gemini multi-turn conversation continuity with file attachments.

This script tests the Google Gemini agent's ability to maintain conversation context
across multiple turns while handling file attachments.
"""

import os
import sys
import unittest
import asyncio
import json
import tempfile
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.agent_builder import build_agent
from app.mcp_loader import load_mcp_tools
from app.simple_conversation_memory_fixed import inject_conversation_context, store_conversation_turn


class TestAgentContinuityGoogle(unittest.TestCase):
    """Test multi-turn conversation continuity with Google Gemini models."""

    def setUp(self):
        """Set up the test environment."""
        # Check for Google API key (try both GOOGLE_API_KEY and GEMINI_API_KEY)
        self.google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.google_api_key:
            self.skipTest("GOOGLE_API_KEY or GEMINI_API_KEY environment variable not set. Skipping Google Gemini tests.")
        
        # Load the Google-specific config
        self.config_path = "config/python_exec_agent_working_google.yaml"
        try:
            self.app_config = load_app_config(Path(self.config_path))
        except Exception as e:
            self.fail(f"Failed to load config: {e}")
        
        # Create test thread ID
        self.thread_id = "test_google_gemini_thread"
        
        # Create temporary files
        self.temp_files = self._create_temp_files_for_testing()
            
    def _create_temp_files_for_testing(self):
        """Create temporary test files for multimodal testing."""
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create a CSV file with student data
        csv_file = temp_dir / "students.csv"
        csv_data = "student_id,name,age\n1,Alice,20\n2,Bob,22\n3,Charlie,21"
        csv_file.write_text(csv_data)
        
        # Create a text file
        text_file = temp_dir / "notes.txt"
        text_file.write_text("Important notes:\n- Alice is interested in computer science\n- Bob is majoring in physics\n- Charlie wants to study mathematics")
        
        # Return file paths and directory
        return {
            "csv_file": str(csv_file),
            "text_file": str(text_file),
            "temp_dir": temp_dir  # Keep track of directory for cleanup
        }

    def tearDown(self):
        """Clean up resources."""
        # Clean up temporary files if they exist
        if hasattr(self, 'temp_files') and 'temp_dir' in self.temp_files:
            import shutil
            try:
                shutil.rmtree(self.temp_files["temp_dir"])
            except Exception as e:
                print(f"Failed to clean up temp directory: {e}")

    async def _run_conversation_turn(self, user_input, files=None, turn_number=1):
        """Run a single conversation turn with the supervisor and agents."""
        # Build the supervisor
        supervisor = build_supervisor_compiled(
            self.app_config.supervisor,
            self.app_config.agents,
            self.app_config.models.get("default", "gemini/gemini-1.5-pro"),
            self.app_config.business_context,
            original_user_question=user_input,
            config_path=self.config_path,
            default_temperature=self.app_config.temperature,
            thread_id=self.thread_id,
        )
        
        # Build agents map
        agents_map = {}
        for agent_config in self.app_config.agents:
            agent, mcp_client = await build_agent(
                agent_config,
                default_model="gemini/gemini-1.5-pro",
                business_context=self.app_config.business_context,
                original_user_question=user_input,
                config_path=self.config_path,
                app_config=self.app_config.dict(),
            )
            agents_map[agent_config.name] = agent
        
        # Inject conversation context from previous turns
        if turn_number > 1:
            user_input = await inject_conversation_context(
                user_input=user_input, 
                thread_id=self.thread_id, 
                app_config=self.app_config
            )
            
        # Add file information if provided
        if files:
            input_text = user_input
            input_text += "\n\nAttached files:"
            for file_path in files:
                input_text += f"\n- {Path(file_path).name}"
        else:
            input_text = user_input
            
        # Execute the plan
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=input_text,
            business_context=self.app_config.business_context,
            default_model_for_verifier="google:gemini-2.5-flash-lite",  # Use Google Gemini for verification
            thread_id=self.thread_id,
        )
        
        # Store conversation turn
        await store_conversation_turn(
            thread_id=self.thread_id,
            user_message=user_input,
            assistant_response=result,
            app_config=self.app_config,
        )
        
        return result

    async def run_multi_turn_conversation_with_files(self):
        """Run a multi-turn conversation with file attachments."""
        # Turn 1: Initial request with student data CSV
        turn1_input = "Parse the CSV file and create a Python dictionary with student information"
        turn1_result = await self._run_conversation_turn(
            turn1_input, 
            files=[self.temp_files["csv_file"]], 
            turn_number=1
        )
        
        print(f"\n--- Turn 1 Result ---\n{turn1_result}\n")
        
        # Turn 2: Add student majors from text file
        turn2_input = "Add the major information from the text file to each student"
        turn2_result = await self._run_conversation_turn(
            turn2_input, 
            files=[self.temp_files["text_file"]], 
            turn_number=2
        )
        
        print(f"\n--- Turn 2 Result ---\n{turn2_result}\n")
        
        # Turn 3: Analyze all data without files (should use context)
        turn3_input = "Create a summary of all student data including their majors"
        turn3_result = await self._run_conversation_turn(
            turn3_input, 
            files=None, 
            turn_number=3
        )
        
        print(f"\n--- Turn 3 Result ---\n{turn3_result}\n")
        
        return {
            "turn1": {
                "input": turn1_input,
                "result": turn1_result
            },
            "turn2": {
                "input": turn2_input,
                "result": turn2_result
            },
            "turn3": {
                "input": turn3_input,
                "result": turn3_result
            }
        }

    def test_google_multi_turn_conversation_with_files(self):
        """Test multi-turn conversation with Google Gemini and file attachments."""
        results = asyncio.run(self.run_multi_turn_conversation_with_files())
        
        # Validate Turn 1 result
        self.assertIsNotNone(results["turn1"]["result"])
        self.assertTrue("dictionary" in results["turn1"]["result"].lower() or 
                        "student" in results["turn1"]["result"].lower())
        
        # Validate Turn 2 result
        self.assertIsNotNone(results["turn2"]["result"])
        self.assertTrue("major" in results["turn2"]["result"].lower() or 
                        "computer science" in results["turn2"]["result"].lower())
        
        # Validate Turn 3 result - check for data continuity
        self.assertIsNotNone(results["turn3"]["result"])
        # The result should mention all students and their majors
        self.assertTrue("alice" in results["turn3"]["result"].lower() and 
                        "bob" in results["turn3"]["result"].lower() and
                        "charlie" in results["turn3"]["result"].lower())
        self.assertTrue("computer science" in results["turn3"]["result"].lower() or
                        "physics" in results["turn3"]["result"].lower() or
                        "mathematics" in results["turn3"]["result"].lower())
        
        print("\n✅ Google Gemini multi-turn conversation test with file attachments completed successfully!")


if __name__ == "__main__":
    unittest.main()
