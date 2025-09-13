#!/usr/bin/env python3
"""Debug script to isolate the PepGenX agent issue."""

import asyncio
import sys
import traceback
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import load_app_config
from app.main import build_agents_map


async def debug_pepgenx_issue():
    """Debug the PepGenX agent issue step by step."""
    print("🔍 Debugging PepGenX Agent Issue")
    print("=" * 50)
    
    try:
        # Load the configuration
        print("1. Loading configuration...")
        config_path = Path("config/pepgenx_gpt4o_test.yaml")
        app_cfg = load_app_config(config_path)
        print(f"✅ Configuration loaded: {len(app_cfg.agents)} agents")
        
        # Print agent details
        for agent in app_cfg.agents:
            print(f"   - Agent: {agent.name}")
            print(f"     Model: {agent.model}")
            print(f"     MCP Servers: {list(agent.mcp_servers.keys())}")
        
        print("\n2. Building agents map...")
        agents_map, mcp_clients = await build_agents_map(
            app_cfg,
            user_input="test input",
            config_path=str(config_path)
        )
        print(f"✅ Agents map built: {list(agents_map.keys())}")
        
        # Test the specific agent
        print("\n3. Testing restaurants_agent...")
        restaurants_agent = agents_map.get("restaurants_agent")
        if restaurants_agent:
            print(f"✅ restaurants_agent found: {type(restaurants_agent)}")
            
            # Try to get the tools
            if hasattr(restaurants_agent, 'get_graph'):
                graph = restaurants_agent.get_graph()
                print(f"✅ Graph obtained: {type(graph)}")
            else:
                print("❌ No get_graph method found")
                
        else:
            print("❌ restaurants_agent not found in agents_map")
            
        # Cleanup
        print("\n4. Cleaning up...")
        from app.mcp_loader import close_mcp_client
        for client in mcp_clients.values():
            if client:
                await close_mcp_client(client)
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print(f"Error type: {type(e).__name__}")
        print("Full traceback:")
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(debug_pepgenx_issue())
    if success:
        print("\n🎉 Debug completed successfully!")
    else:
        print("\n💥 Debug failed!")
        sys.exit(1)
