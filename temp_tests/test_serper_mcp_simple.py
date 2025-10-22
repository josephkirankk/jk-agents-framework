"""
Simple Serper MCP Server Test
Tests actual MCP server initialization and tool availability.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.main import load_app_config
from app.mcp_loader import load_mcp_tools, close_mcp_client

load_dotenv()


async def test_mcp_server():
    """Test MCP server initialization"""
    print("\n" + "=" * 80)
    print("  SERPER MCP SERVER INITIALIZATION TEST")
    print("=" * 80 + "\n")
    
    # Check API key
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key or api_key == "your-serper-api-key-here":
        print("❌ SERPER_API_KEY not configured")
        return False
    
    print(f"✓ SERPER_API_KEY configured")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
    
    try:
        app_config = load_app_config(config_path)
        print(f"✓ Configuration loaded")
        
        # Find agent with Serper MCP
        serper_agent = None
        for agent in app_config.agents:
            if hasattr(agent, 'mcp_servers') and agent.mcp_servers and "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
        
        if not serper_agent:
            print("❌ Serper agent not found")
            return False
        
        print(f"✓ Found agent: {serper_agent.name}")
        
        # Initialize MCP server with timeout
        print(f"\nInitializing MCP server (timeout: 30s)...")
        print(f"  This will run: npx -y serper-search-scrape-mcp-server")
        
        mcp_client = None
        try:
            mcp_client, tools = await asyncio.wait_for(
                load_mcp_tools(serper_agent.mcp_servers),
                timeout=30.0
            )
            
            print(f"✓ MCP server initialized successfully!")
            print(f"✓ Loaded {len(tools)} tools")
            
            # List tools
            print(f"\nAvailable tools:")
            for tool in tools:
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                tool_desc = tool.description if hasattr(tool, 'description') else ''
                print(f"  - {tool_name}: {tool_desc[:80]}")
            
            # Check for expected tools
            tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
            tool_names_lower = [name.lower() for name in tool_names]
            
            expected_tools = ['google_search', 'scrape']
            found_tools = []
            for expected in expected_tools:
                if any(expected in name for name in tool_names_lower):
                    found_tools.append(expected)
            
            print(f"\n✓ Expected tools found: {found_tools}")
            
            if len(found_tools) == len(expected_tools):
                print(f"\n✓ All expected tools are available!")
                success = True
            else:
                missing = set(expected_tools) - set(found_tools)
                print(f"\n⚠️  Missing expected tools: {missing}")
                success = False
            
            # Cleanup
            if mcp_client:
                await close_mcp_client(mcp_client)
                print(f"\n✓ MCP client closed")
            
            return success
            
        except asyncio.TimeoutError:
            print(f"❌ MCP server initialization timed out after 30 seconds")
            print(f"   This might indicate:")
            print(f"   - Network issues downloading the package")
            print(f"   - API key authentication issues")
            print(f"   - Node.js or npx issues")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    success = await test_mcp_server()
    
    print("\n" + "=" * 80)
    if success:
        print("✓ TEST PASSED: Serper MCP server is working correctly!")
        print("\nYou can now use the following tools in your agents:")
        print("  - google_search: Search the web using Serper API")
        print("  - scrape: Extract content from web pages")
    else:
        print("✗ TEST FAILED: Please review the errors above")
    print("=" * 80 + "\n")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
