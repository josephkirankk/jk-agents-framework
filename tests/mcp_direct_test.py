#!/usr/bin/env python3
"""
Direct MCP Server Test

Tests MCP servers directly without timeout wrappers to isolate issues.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_mcp_adapters.client import MultiServerMCPClient


async def test_direct_mcp():
    """Test MCP servers directly"""
    print("🔧 Direct MCP Server Test")
    print("=" * 40)
    
    # Configure math server
    math_server_path = Path(__file__).parent.parent / "examples/mcp_servers/math_server.py"
    
    servers_cfg = {
        "math": {
            "transport": "stdio",
            "command": "python",
            "args": [str(math_server_path), "stdio"]
        }
    }
    
    try:
        # Create MCP client
        print("Creating MCP client...")
        mcp_client = MultiServerMCPClient(servers_cfg)
        
        # Get tools
        print("Getting tools...")
        tools = await mcp_client.get_tools()
        
        print(f"✅ Loaded {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Test a tool directly
        if tools:
            add_tool = next((t for t in tools if t.name == 'add'), None)
            if add_tool:
                print(f"\n🧮 Testing add tool...")
                print(f"Tool args schema: {getattr(add_tool, 'args_schema', 'None')}")
                
                try:
                    # Test with structured input
                    result = await add_tool.arun({"a": 5, "b": 3})
                    print(f"✅ 5 + 3 = {result}")
                except Exception as e:
                    print(f"❌ Structured input failed: {e}")
                    
                    try:
                        # Test with direct parameters
                        result = await add_tool.arun(a=5, b=3)
                        print(f"✅ 5 + 3 = {result} (direct params)")
                    except Exception as e2:
                        print(f"❌ Direct params failed: {e2}")
        
        # Close client
        await mcp_client.aclose()
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct_mcp())
