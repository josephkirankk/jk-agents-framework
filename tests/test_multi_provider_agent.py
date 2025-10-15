"""
Test script for Multi-Provider Agent with file attachment support.

This script tests the multi-provider agent with different LLM providers
(OpenAI, Anthropic, and Google Gemini) via LiteLLM.
"""

import os
import sys
import unittest
import asyncio
import json
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.agent_builder import build_agent
from app.mcp_loader import load_mcp_tools


class TestMultiProviderAgent(unittest.TestCase):
    """Test the multi-provider agent with different LLM providers."""

    def setUp(self):
        """Set up the test environment."""
        # Check for required API keys
        self.api_keys_available = {}
        self.api_keys_available["openai"] = bool(os.getenv("OPENAI_API_KEY"))
        self.api_keys_available["anthropic"] = bool(os.getenv("ANTHROPIC_API_KEY"))
        self.api_keys_available["gemini"] = bool(os.getenv("GEMINI_API_KEY"))
        
        # Skip the whole test suite if no API keys are available
        if not any(self.api_keys_available.values()):
            self.skipTest("No API keys available for any provider (OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY)")
        
        # Load the multi-provider config
        self.config_path = "config/multi_provider_agent.yaml"
        try:
            self.app_config = load_app_config(Path(self.config_path))
        except Exception as e:
            self.fail(f"Failed to load config: {e}")
            
    def _create_temp_files_for_testing(self):
        """Create temporary test files for multimodal testing."""
        # Create a temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create a text file
        text_file = temp_dir / "sample.txt"
        text_file.write_text("This is a sample text file for testing multi-provider agent.")
        
        # Create a JSON file with structured data
        json_file = temp_dir / "data.json"
        json_data = {
            "name": "Test User",
            "age": 30,
            "skills": ["Python", "AI", "Testing"],
            "projects": [
                {"name": "Project A", "status": "Complete"},
                {"name": "Project B", "status": "In Progress"}
            ]
        }
        json_file.write_text(json.dumps(json_data, indent=2))
        
        # Return file paths
        return {
            "text_file": str(text_file),
            "json_file": str(json_file),
            "temp_dir": temp_dir  # Keep track of the directory for cleanup
        }

    async def _run_agent_test(self, agent_name, user_input, files=None):
        """Run a test for a specific agent."""
        # Check if the agent's provider has an API key available
        provider_prefix = agent_name.split("_")[0]
        if provider_prefix in ["text", "human"]:
            provider = "openai"
        elif provider_prefix == "vision":
            provider = "gemini"
        elif provider_prefix in ["document", "advanced"]:
            provider = "anthropic"
        else:
            provider = "openai"  # Default
        
        if not self.api_keys_available.get(provider, False):
            self.skipTest(f"Skipping {agent_name} test: {provider.upper()}_API_KEY not available")
            return None
        
        # Find the agent config
        agent_config = next((a for a in self.app_config.agents if a.name == agent_name), None)
        if not agent_config:
            self.fail(f"Agent {agent_name} not found in config")
            return None
        
        # Build the agent
        agent, mcp_client = await build_agent(
            agent_config,
            default_model="openai/gpt-4o",  # Default model
            business_context=self.app_config.business_context,
            original_user_question=user_input,
            config_path=self.config_path,
            app_config=self.app_config.dict(),
        )
        
        try:
            # Prepare messages with files if provided
            messages = [{"role": "system", "content": "Business context:\n" + self.app_config.business_context}]
            
            if files:
                # Create multimodal content
                content = []
                content.append({"type": "text", "text": user_input})
                
                for file_path in files:
                    if file_path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                        # This is an image file
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"file://{file_path}"}
                        })
                    else:
                        # This is a document file
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        content.append({
                            "type": "text",
                            "text": f"Content of {Path(file_path).name}:\n{file_content}"
                        })
                
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "user", "content": user_input})
            
            # Call the agent
            state = {"messages": messages}
            response = await agent.ainvoke(state)
            
            # Get the response
            msgs = response.get("messages", [])
            if msgs:
                last_msg = msgs[-1]
                text = getattr(last_msg, "content", "")
                return text
            return None
            
        finally:
            # Clean up
            if mcp_client:
                await mcp_client.aclose()
    
    async def _run_supervisor_test(self, user_input, files=None):
        """Run a test using the supervisor and planner."""
        # Build the supervisor
        supervisor = build_supervisor_compiled(
            self.app_config.supervisor,
            self.app_config.agents,
            self.app_config.models.get("default", "openai/gpt-4o"),
            self.app_config.business_context,
            original_user_question=user_input,
            config_path=self.config_path,
            default_temperature=self.app_config.temperature,
            thread_id="test-thread",
        )
        
        # Build agents map
        agents_map, mcp_clients = await load_mcp_tools({})
        
        for agent_config in self.app_config.agents:
            provider = agent_config.name.split("_")[0]
            if provider in ["text", "human"]:
                provider = "openai"
            elif provider == "vision":
                provider = "gemini"
            elif provider in ["document", "advanced"]:
                provider = "anthropic"
            else:
                provider = "openai"  # Default
                
            if not self.api_keys_available.get(provider, False):
                continue  # Skip agents without API keys
                
            agent, mcp_client = await build_agent(
                agent_config,
                default_model="openai/gpt-4o",  # Default model
                business_context=self.app_config.business_context,
                original_user_question=user_input,
                config_path=self.config_path,
                app_config=self.app_config.dict(),
            )
            
            agents_map[agent_config.name] = agent
            
        try:
            # Prepare the input
            input_text = user_input
            
            # Add file information if provided
            if files:
                input_text += "\n\nAttached files:"
                for file_path in files:
                    input_text += f"\n- {Path(file_path).name}"
            
            # Execute the plan
            result = await execute_plan(
                supervisor=supervisor,
                agents=agents_map,
                user_question=input_text,
                business_context=self.app_config.business_context,
                config_path=self.config_path,
                thread_id="test-thread",
                retry_failed_agents=True,
            )
            
            return result
            
        finally:
            # Clean up
            for client in mcp_clients.values():
                await client.aclose()

    def test_text_processor_agent(self):
        """Test the text processor agent (OpenAI)."""
        if not self.api_keys_available.get("openai", False):
            self.skipTest("Skipping OpenAI test: OPENAI_API_KEY not available")
            return
            
        response = asyncio.run(
            self._run_agent_test(
                "text_processor_agent",
                "Analyze this text: Python is a high-level programming language known for its readability."
            )
        )
        
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)
        print(f"\nOpenAI Text Processor Response:\n{response}")

    def test_document_analyzer_agent(self):
        """Test the document analyzer agent (Anthropic)."""
        if not self.api_keys_available.get("anthropic", False):
            self.skipTest("Skipping Anthropic test: ANTHROPIC_API_KEY not available")
            return
            
        # Create temp files
        files = self._create_temp_files_for_testing()
        
        response = asyncio.run(
            self._run_agent_test(
                "document_analyzer_agent",
                "Analyze the contents of the JSON file.",
                files=[files["json_file"]]
            )
        )
        
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)
        print(f"\nAnthropic Document Analyzer Response:\n{response}")

    def test_supervisor_with_files(self):
        """Test the supervisor with file attachments."""
        # Skip if no API keys are available
        if not any(self.api_keys_available.values()):
            self.skipTest("Skipping supervisor test: No API keys available")
            return
            
        # Create temp files
        files = self._create_temp_files_for_testing()
        
        response = asyncio.run(
            self._run_supervisor_test(
                "Analyze the contents of these files and provide a summary.",
                files=[files["text_file"], files["json_file"]]
            )
        )
        
        self.assertIsNotNone(response)
        print(f"\nSupervisor Response with Files:\n{response}")


if __name__ == "__main__":
    unittest.main()
