#!/usr/bin/env python3
"""
Simple test to verify the LoggingModelWrapper works correctly.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.llm_payload_logger import LoggingModelWrapper, LLMPayloadLogger


async def test_logging_wrapper():
    """Test the LoggingModelWrapper with a simple model."""
    
    print("🧪 Testing LoggingModelWrapper")
    print("=" * 40)
    
    try:
        # Create a simple mock model for testing
        class MockChatModel:
            def __init__(self):
                self.model_name = "test-model"
                self.temperature = 0.0
                
            def invoke(self, messages, **kwargs):
                return MockResponse("Test response from mock model")
            
            async def ainvoke(self, messages, **kwargs):
                return MockResponse("Async test response from mock model")
            
            def bind_tools(self, tools, **kwargs):
                # Return a new instance with tools bound
                bound = MockChatModel()
                bound.tools = tools
                bound.model_name = self.model_name
                bound.temperature = self.temperature
                return bound
        
        class MockResponse:
            def __init__(self, content):
                self.content = content
                self.usage_metadata = {
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15
                }
        
        # Create logger and wrapper
        logger = LLMPayloadLogger("test_agent")
        mock_model = MockChatModel()
        wrapped_model = LoggingModelWrapper(mock_model, logger)
        
        print("✅ Created LoggingModelWrapper")
        
        # Test attribute access
        print(f"Model name: {wrapped_model.model_name}")
        print(f"Temperature: {wrapped_model.temperature}")
        
        # Test sync invoke
        print("\n🔄 Testing sync invoke...")
        response = wrapped_model.invoke(["Hello, world!"])
        print(f"Response: {response.content}")
        
        # Test async invoke
        print("\n🔄 Testing async invoke...")
        response = await wrapped_model.ainvoke(["Hello, async world!"])
        print(f"Async Response: {response.content}")
        
        # Test tool binding
        print("\n🔧 Testing tool binding...")
        mock_tools = [{"name": "test_tool", "description": "A test tool"}]
        bound_model = wrapped_model.bind_tools(mock_tools)
        print(f"Bound model type: {type(bound_model)}")
        print(f"Bound model has tools: {hasattr(bound_model, 'tools')}")
        
        # Check log file
        log_file = logger.get_log_file_path()
        print(f"\n📁 Log file: {log_file}")
        
        if Path(log_file).exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
            print(f"Log entries: {len(log_data.get('entries', []))}")
            
            if log_data.get('entries'):
                print("✅ Log entries found!")
                for i, entry in enumerate(log_data['entries']):
                    print(f"  Entry {i+1}: {entry['interaction_type']}")
            else:
                print("❌ No log entries found")
        else:
            print("❌ Log file not found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_logging_wrapper())
