#!/usr/bin/env python3
"""
Test script to verify LLM payload logging with a mock agent execution.
This tests the logging without making actual API calls.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.llm_payload_logger import LoggingModelWrapper, LLMPayloadLogger
from langchain_core.messages import HumanMessage, AIMessage


class MockChatModel:
    """Mock chat model for testing."""
    
    def __init__(self):
        self.model_name = "mock-gpt-4"
        self.temperature = 0.0
        self.max_tokens = None
        
    def invoke(self, messages, **kwargs):
        """Mock invoke method."""
        return AIMessage(
            content="I'll help you find pizza restaurants. Let me search for you.",
            usage_metadata={
                "input_tokens": 45,
                "output_tokens": 12,
                "total_tokens": 57
            }
        )
    
    async def ainvoke(self, messages, **kwargs):
        """Mock async invoke method."""
        return AIMessage(
            content="I'll help you find pizza restaurants. Let me search for you.",
            usage_metadata={
                "input_tokens": 45,
                "output_tokens": 12,
                "total_tokens": 57
            }
        )
    
    def bind_tools(self, tools, **kwargs):
        """Mock bind_tools method."""
        bound = MockChatModel()
        bound.tools = tools
        bound.model_name = self.model_name
        bound.temperature = self.temperature
        return bound


async def test_mock_agent_logging():
    """Test the LLM payload logging with mock agent execution."""
    
    print("🧪 Testing LLM Payload Logging with Mock Agent")
    print("=" * 50)
    
    try:
        # Create logger and mock model
        logger = LLMPayloadLogger("mock_restaurants_agent")
        mock_model = MockChatModel()
        
        # Create some mock tools
        mock_tools = [
            {
                "name": "restaurant_search",
                "description": "Search for restaurants based on criteria",
                "args_schema": {
                    "type": "object",
                    "properties": {
                        "cuisine": {"type": "array", "items": {"type": "string"}},
                        "menu_score_min": {"type": "integer"},
                        "menu_score_max": {"type": "integer"}
                    }
                }
            }
        ]
        
        # Bind tools to mock model
        bound_model = mock_model.bind_tools(mock_tools)
        print(f"✅ Created mock model with {len(mock_tools)} tools")
        
        # Wrap with logging
        wrapped_model = LoggingModelWrapper(bound_model, logger)
        print(f"✅ Created LoggingModelWrapper")
        
        # Test sync invoke
        print(f"\n🔄 Testing sync invoke...")
        messages = [
            HumanMessage(content="Find pizza restaurants with menu score 80-100")
        ]
        
        response = wrapped_model.invoke(messages)
        print(f"✅ Sync response: {response.content}")
        
        # Test async invoke
        print(f"\n🔄 Testing async invoke...")
        response = await wrapped_model.ainvoke(messages)
        print(f"✅ Async response: {response.content}")
        
        # Check log file
        log_file = logger.get_log_file_path()
        print(f"\n📁 Checking log file: {log_file}")
        
        if Path(log_file).exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            
            entries = log_data.get('entries', [])
            print(f"✅ Found {len(entries)} log entries")
            
            if entries:
                print(f"\n📋 Log entries:")
                for i, entry in enumerate(entries):
                    print(f"  {i+1}. {entry['interaction_type']} at {entry['timestamp']}")
                    
                    # Show request details
                    if 'request' in entry:
                        req = entry['request']
                        print(f"     Messages: {len(req.get('messages', []))}")
                        print(f"     Tools: {len(req.get('tools', []))}")
                        
                        # Show first message content
                        messages = req.get('messages', [])
                        if messages:
                            first_msg = messages[0]
                            content = first_msg.get('content', '')
                            if isinstance(content, str) and len(content) > 50:
                                content = content[:50] + "..."
                            print(f"     First message: {content}")
                        
                        # Show model params
                        params = req.get('model_params', {})
                        if params:
                            print(f"     Model: {params.get('model_name', 'unknown')}")
                            print(f"     Temperature: {params.get('temperature', 'unknown')}")
                    
                    # Show response details
                    if 'response' in entry and entry['response']:
                        resp = entry['response']
                        if resp.get('usage'):
                            usage = resp['usage']
                            print(f"     Usage: {usage}")
                        if resp.get('content'):
                            content = resp['content']
                            if isinstance(content, dict) and 'content' in content:
                                print(f"     Response: {content['content'][:50]}...")
                    
                    print()
                
                # Show a sample entry in full
                if entries:
                    print(f"📄 Sample log entry (first one):")
                    print(json.dumps(entries[0], indent=2))
            else:
                print(f"❌ No log entries found")
        else:
            print(f"❌ Log file not found")
        
        print(f"\n✅ Mock agent logging test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mock_agent_logging())
