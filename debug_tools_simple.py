#!/usr/bin/env python3
"""
Simple debug script to examine tool structure.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.main import load_app_config
from app.mcp_loader import load_mcp_tools


async def debug_tools():
    """Debug the tool structure."""
    
    print("🔍 Debugging Tool Structure")
    print("=" * 40)
    
    # Load configuration
    config_path = "config/pep_mcp_sample.yaml"
    app_cfg = load_app_config(Path(config_path))
    
    # Find the restaurants agent
    agent_name = "restaurants_agent"
    target_agent = next((a for a in app_cfg.agents if a.name == agent_name), None)
    
    # Load tools
    servers_raw = {
        k: v.dict(exclude_none=True)
        for k, v in target_agent.mcp_servers.items()
    }
    mcp_client, mcp_tools = await load_mcp_tools(servers_raw)
    all_tools = mcp_tools  # Just MCP tools for now
    
    print(f"✅ Loaded {len(all_tools)} total tools")
    
    # Examine first tool in detail
    if all_tools:
        tool = all_tools[0]
        print(f"\n📋 First Tool Details:")
        print(f"   Type: {type(tool)}")
        print(f"   Name: {getattr(tool, 'name', 'N/A')}")
        print(f"   Description: {getattr(tool, 'description', 'N/A')[:100]}...")
        print(f"   Args Schema Type: {type(getattr(tool, 'args_schema', None))}")
        
        if hasattr(tool, 'args_schema') and tool.args_schema:
            if hasattr(tool.args_schema, 'schema'):
                schema = tool.args_schema.schema()
                print(f"   Schema: {schema}")
            else:
                print(f"   Schema: {tool.args_schema}")
    
    # Now test binding
    print(f"\n🔧 Testing Tool Binding...")
    from langchain.chat_models import init_chat_model
    from app.agent_builder import create_model_instance
    
    model_id = app_cfg.models.get("default", "azure_openai:gpt-4.1")
    model_instance = create_model_instance(model_id)
    actual_model = init_chat_model(model_instance)
    
    # Bind just first tool
    bound_model = actual_model.bind_tools([all_tools[0]], parallel_tool_calls=False)
    
    # Check what's in kwargs
    if hasattr(bound_model, 'kwargs') and 'tools' in bound_model.kwargs:
        bound_tools = bound_model.kwargs['tools']
        print(f"✅ Found {len(bound_tools)} bound tools")
        
        bound_tool = bound_tools[0]
        print(f"\n📋 Bound Tool Structure:")
        print(f"   Type: {type(bound_tool)}")
        print(f"   Content: {bound_tool}")
        
        if isinstance(bound_tool, dict):
            print(f"   Keys: {list(bound_tool.keys())}")
            if 'function' in bound_tool:
                func = bound_tool['function']
                print(f"   Function Name: {func.get('name', 'N/A')}")
                print(f"   Function Description: {func.get('description', 'N/A')}")
                print(f"   Function Parameters: {func.get('parameters', 'N/A')}")
    
    # Clean up
    if mcp_client:
        try:
            await mcp_client.close()
        except AttributeError:
            pass


if __name__ == "__main__":
    asyncio.run(debug_tools())
