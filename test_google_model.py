#!/usr/bin/env python3
"""
Simple test to verify Google Gemini model integration
"""
import os
import sys
import asyncio
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.agent_builder import build_react_agent
from app.config import AgentConfig, AppConfig
from app.checkpointer_manager import get_global_checkpointer

async def test_google_model():
    """Test that Google Gemini model is working"""
    print("🧪 Testing Google Gemini Model Integration")
    print("=" * 50)
    
    # Load .env file
    load_dotenv()
    
    # Check if Google API key is available
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        print(f"✅ Google API Key found: {google_api_key[:20]}...")
    else:
        print("❌ Google API Key not found in environment")
    
    try:
        # Load basic test config
        config_path = Path("config/basic_test.yaml")
        if not config_path.exists():
            print("❌ Config file not found: config/basic_test.yaml")
            return False
            
        with config_path.open("r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            
        # Normalize config: move misnested temperature out of models,
        # and ensure string values in the models map
        models = config_data.get("models", {}) or {}
        if "temperature" in models and "temperature" not in config_data:
            config_data["temperature"] = models.get("temperature")
            models.pop("temperature", None)
        # Coerce model map values to strings
        models = {str(k): str(v) for k, v in models.items() if v is not None}
        config_data["models"] = models
            
        app_config = AppConfig(**config_data)
        print(f"✅ Loaded config from {config_path}")
        print(f"   Default model: {app_config.models.get('default', 'N/A')}")
        print(f"   Supervisor model: {app_config.models.get('supervisor', 'N/A')}")
        
        # Get the simple test agent config
        if not app_config.agents or len(app_config.agents) == 0:
            print("❌ No agents found in config")
            return False
            
        simple_agent_config = app_config.agents[0]
        print(f"   Agent: {simple_agent_config.name}")
        print(f"   Agent model: {simple_agent_config.model}")
        
        # Convert AppConfig to dict for compatibility
        app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else (app_config.dict() if hasattr(app_config, 'dict') else app_config.__dict__)
        
        # Initialize checkpointer using the same method as build_react_agent
        checkpointer = get_global_checkpointer(app_config_dict)
        print("✅ Checkpointer initialized")
        
        # Build the agent
        print("🔄 Building agent...")
        
        agent, mcp_client = await build_react_agent(
            agent_cfg=simple_agent_config,
            default_model=app_config.models.get('default', 'google:gemini-2.5-flash-lite'),
            checkpointer=checkpointer,
            app_config=app_config_dict
        )
        print("✅ Agent built successfully")
        
        # Test simple query
        print("\n🔄 Testing simple query...")
        test_query = "Hello! Can you tell me what model you are running on and confirm you're working correctly?"
        
        config = {"configurable": {"thread_id": "test-google-model"}}
        
        print(f"Query: {test_query}")
        print("Processing...")
        
        response = await agent.ainvoke({"messages": [{"role": "user", "content": test_query}]}, config)
        
        if response and "messages" in response:
            messages = response["messages"]
            assistant_messages = [msg for msg in messages if hasattr(msg, 'role') and msg.role == "assistant"]
            if assistant_messages:
                print(f"\n✅ Response received:")
                print(f"   {assistant_messages[-1].content[:200]}...")
            else:
                # Alternative approach - look for any message with content
                all_messages = [msg for msg in messages if hasattr(msg, 'content') and msg.content]
                if all_messages:
                    print(f"\n✅ Response received (last message):")
                    print(f"   {all_messages[-1].content[:200]}...")
                
                # Test mathematical query
                print("\n🔄 Testing mathematical calculation...")
                math_query = "Calculate 17 * 23 and show your work"
                
                math_response = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": math_query}]}, 
                    {"configurable": {"thread_id": "test-google-math"}}
                )
                
                if math_response and "messages" in math_response:
                    math_response_messages = math_response["messages"]
                    math_assistant_messages = [msg for msg in math_response_messages if hasattr(msg, 'role') and msg.role == "assistant"]
                    if math_assistant_messages:
                        print(f"✅ Math response received:")
                        print(f"   {math_assistant_messages[-1].content[:200]}...")
                        return True
                    else:
                        # Alternative approach for math response
                        math_all_messages = [msg for msg in math_response_messages if hasattr(msg, 'content') and msg.content]
                        if math_all_messages:
                            print(f"✅ Math response received (last message):")
                            print(f"   {math_all_messages[-1].content[:200]}...")
                            return True
                
        print("❌ No valid response received")
        return False
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup MCP client if it exists
        if 'mcp_client' in locals() and mcp_client:
            try:
                await mcp_client.close()
                print("✅ MCP client closed")
            except:
                pass

async def main():
    """Main test function"""
    print("🚀 Google Gemini Model Test Suite")
    print("=" * 50)
    
    success = await test_google_model()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Google Gemini model test PASSED!")
        print("   ✅ Model loading successful")  
        print("   ✅ Agent building successful")
        print("   ✅ Basic query successful")
        print("   ✅ Math query successful")
    else:
        print("❌ Google Gemini model test FAILED!")
        print("   Check your Google API credentials and network connection")
    
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))