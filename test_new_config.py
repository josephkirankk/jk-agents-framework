#!/usr/bin/env python3
"""
Test script for new_agents.yaml configuration
Tests supervisor and search agent setup
"""
import asyncio
from pathlib import Path
from app.main import load_app_config
from app.agent_builder import build_react_agent
from app.supervisor_builder import build_supervisor_compiled
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_new_config():
    """Test the new simplified agent configuration"""
    print("Testing New Agent Configuration")
    print("=" * 50)
    
    try:
        # Load the new config
        config_path = Path(__file__).resolve().parent / "config" / "new_agents.yaml"
        config = load_app_config(config_path)
        print(f"✓ Loaded new config with {len(config.agents)} agents")
        
        # Display configuration summary
        print(f"✓ Default model: {config.models.get('default')}")
        print(f"✓ Supervisor model: {config.supervisor.model or config.models.get('default')}")
        print(f"✓ Business context: {config.business_context[:100]}...")
        
        # List agents
        print(f"\nConfigured agents:")
        for agent in config.agents:
            print(f"  - {agent.name}: {agent.description}")
            print(f"    MCP servers: {list(agent.mcp_servers.keys())}")
        
        # Build supervisor
        print(f"\nBuilding supervisor...")
        supervisor = build_supervisor_compiled(
            config.supervisor,
            config.agents,
            config.models.get("default"),
            config.business_context
        )
        print("✓ Supervisor built successfully")
        
        # Test supervisor planning
        print(f"\nTesting supervisor planning...")
        test_query = "Search for the latest news about artificial intelligence developments"
        
        try:
            supervisor_response = await supervisor.ainvoke(
                {"messages": [{"role": "user", "content": test_query}]},
                config={"configurable": {"thread_id": "test-thread"}}
            )
            
            print("✓ Supervisor responded:")
            if hasattr(supervisor_response, 'content'):
                print(f"Response: {supervisor_response.content}")
            elif isinstance(supervisor_response, dict) and 'messages' in supervisor_response:
                last_message = supervisor_response['messages'][-1]
                print(f"Response: {last_message.content if hasattr(last_message, 'content') else last_message}")
            else:
                print(f"Response: {supervisor_response}")
                
        except Exception as e:
            print(f"✗ Supervisor test failed: {e}")
            return False
        
        # Build search agent (but don't test MCP connection yet since server might not be running)
        print(f"\nBuilding search agent...")
        search_agent_config = None
        for agent in config.agents:
            if agent.name == "search_agent":
                search_agent_config = agent
                break
        
        if not search_agent_config:
            print("✗ Search agent not found in config")
            return False
            
        try:
            # Note: This will fail if MCP server isn't running, but we can still test the build process
            compiled_agent, mcp_client = await build_react_agent(
                search_agent_config, 
                config.models.get("default")
            )
            print("✓ Search agent built successfully")
            
            # Clean up MCP client if created
            if mcp_client:
                await mcp_client.close()
                
        except Exception as e:
            print(f"⚠ Search agent build failed (expected if MCP server not running): {e}")
            print("  This is normal if the Brave search MCP server isn't running on localhost:8000")
        
        print(f"\n" + "=" * 50)
        print("✓ Configuration validation completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Start the Brave search MCP server on localhost:8000")
        print(f"2. Run full integration tests")
        print(f"3. Test with real queries")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config_loading_only():
    """Test just the config loading without building agents"""
    print("Testing Configuration Loading Only")
    print("=" * 30)
    
    try:
        config_path = Path(__file__).resolve().parent / "config" / "new_agents.yaml"
        config = load_app_config(config_path)
        
        print(f"✓ Config loaded successfully")
        print(f"  Models: {config.models}")
        print(f"  Agents: {[a.name for a in config.agents]}")
        print(f"  Supervisor: {config.supervisor.name}")
        
        # Validate required fields
        assert len(config.agents) > 0, "No agents configured"
        assert config.supervisor.name == "supervisor", "Supervisor not properly configured"
        assert "search_agent" in [a.name for a in config.agents], "Search agent not found"
        
        search_agent = next(a for a in config.agents if a.name == "search_agent")
        assert "brave_search" in search_agent.mcp_servers, "Brave search MCP server not configured"
        
        print("✓ All validation checks passed")
        return True
        
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False

if __name__ == "__main__":
    print("JK-Agents New Configuration Test")
    print("=" * 40)
    
    # First test just config loading
    success = asyncio.run(test_config_loading_only())
    
    if success:
        print(f"\n")
        # Then test full agent building
        success = asyncio.run(test_new_config())
    
    exit(0 if success else 1)
