#!/usr/bin/env python3
"""
Debug script to examine the actual tool structure being passed to the LLM.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.main import load_app_config
from app.agent_builder import build_react_agent


async def debug_tool_structure():
    """Debug the actual tool structure."""
    
    print("🔍 Debugging Tool Structure")
    print("=" * 40)
    
    # Load configuration
    config_path = "config/pep_mcp_sample.yaml"
    try:
        app_cfg = load_app_config(Path(config_path))
        print(f"✅ Loaded configuration from {config_path}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return
    
    # Find the restaurants agent
    agent_name = "restaurants_agent"
    target_agent = next((a for a in app_cfg.agents if a.name == agent_name), None)
    if not target_agent:
        print(f"❌ Agent '{agent_name}' not found in configuration")
        return
    
    print(f"✅ Found agent: {agent_name}")
    
    # Build agent without logging to examine tools
    try:
        default_model = app_cfg.models.get("default", "azure_openai:gpt-4.1")
        compiled, mcp_client = await build_react_agent(
            target_agent,
            default_model,
            business_context=app_cfg.business_context or "",
            original_user_question="test",
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=False,  # Disable logging for debugging
        )
        print(f"✅ Built agent successfully")
        
        # Get the model from the compiled agent
        # LangGraph agents have a 'model' attribute or similar
        model = None
        
        # Try to find the model in the compiled agent
        if hasattr(compiled, 'nodes'):
            for node_name, node in compiled.nodes.items():
                print(f"📋 Node: {node_name} -> {type(node)}")
                if hasattr(node, 'bound'):
                    model = node.bound
                    print(f"   Found bound model: {type(model)}")
                    break
                elif hasattr(node, 'runnable'):
                    if hasattr(node.runnable, 'bound'):
                        model = node.runnable.bound
                        print(f"   Found bound model in runnable: {type(model)}")
                        break
        
        if model is None:
            print("❌ Could not find model in compiled agent")
            return
        
        # Examine the model's tools
        print(f"\n🔧 Examining model tools...")
        print(f"Model type: {type(model)}")
        print(f"Model attributes: {dir(model)}")
        
        # Check different possible tool locations
        tools = None
        tool_location = None
        
        if hasattr(model, 'kwargs') and 'tools' in model.kwargs:
            tools = model.kwargs['tools']
            tool_location = "model.kwargs['tools']"
        elif hasattr(model, 'bound_tools'):
            tools = model.bound_tools
            tool_location = "model.bound_tools"
        elif hasattr(model, 'tools'):
            tools = model.tools
            tool_location = "model.tools"
        
        if tools:
            print(f"✅ Found {len(tools)} tools in {tool_location}")
            
            # Examine first few tools in detail
            for i, tool in enumerate(tools[:3]):
                print(f"\n📋 Tool {i+1}:")
                print(f"   Type: {type(tool)}")
                print(f"   Attributes: {dir(tool)}")
                
                # Try to extract information
                if hasattr(tool, 'name'):
                    print(f"   Name: {tool.name}")
                if hasattr(tool, 'description'):
                    print(f"   Description: {tool.description}")
                if hasattr(tool, 'args_schema'):
                    print(f"   Args Schema Type: {type(tool.args_schema)}")
                    if hasattr(tool.args_schema, 'schema'):
                        print(f"   Args Schema: {tool.args_schema.schema()}")
                    else:
                        print(f"   Args Schema: {tool.args_schema}")
                
                # Check if it's a dict-like structure
                if hasattr(tool, '__dict__'):
                    print(f"   Dict: {tool.__dict__}")
                
                # Check if it's a string representation
                print(f"   String repr: {str(tool)}")
                print(f"   Raw: {repr(tool)}")
        else:
            print("❌ No tools found")
        
        # Clean up
        if mcp_client:
            try:
                await mcp_client.close()
            except AttributeError:
                pass
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_tool_structure())
