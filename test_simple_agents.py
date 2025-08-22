#!/usr/bin/env python3
"""
Simple test for jk-agents focusing on the test agent and basic functionality
"""
import asyncio
from app.main import load_app_config
from app.agent_builder import build_react_agent
from app.supervisor_builder import build_supervisor_compiled
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_agent():
    """Test building and running a basic agent without MCP dependencies"""
    print("Starting Basic Agent Test")
    print("=" * 50)
    
    try:
        # Load config
        config = load_app_config()
        print(f"✓ Loaded config with {len(config.agents)} agents")
        
        # Find the test agent (should have no MCP servers)
        test_agent = None
        for agent in config.agents:
            if agent.name == "test_agent":
                test_agent = agent
                break
        
        if not test_agent:
            print("✗ Test agent not found in config")
            return False
            
        print(f"✓ Found test agent: {test_agent.name}")
        print(f"  Description: {test_agent.description}")
        print(f"  MCP Servers: {test_agent.mcp_servers}")
        
        # Get default model
        default_model = config.models.get("default", "openai:gpt-4o-mini")
        print(f"✓ Default model: {default_model}")
        
        # Build the test agent
        print("Building test agent...")
        compiled_agent, mcp_client = await build_react_agent(
            test_agent, default_model)
        print("✓ Test agent built successfully")
        
        # Test a simple invoke
        test_input = "Hello! Can you tell me what you are and what you can do?"
        print(f"\nTesting agent with input: {test_input}")
        
        result = await compiled_agent.ainvoke(
            {"messages": [("user", test_input)]},
            config={"configurable": {"thread_id": "test-thread"}})
        
        print("✓ Agent response received:")
        print(f"Response: {result['messages'][-1].content}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in basic agent test: {e}")
        logger.error(f"Basic agent test failed: {e}", exc_info=True)
        return False


async def test_supervisor_basic():
    """Test building a basic supervisor"""
    print("\nTesting Basic Supervisor")
    print("=" * 50)
    
    try:
        # Load config
        config = load_app_config()
        
        # Create a simple agents map with just the test agent
        test_agent = None
        for agent in config.agents:
            if agent.name == "test_agent":
                test_agent = agent
                break
                
        if not test_agent:
            print("✗ Test agent not found")
            return False
            
        # Build test agent
        default_model = config.models.get("default", "openai:gpt-4o-mini")
        compiled_agent, mcp_client = await build_react_agent(
            test_agent, default_model)
        
        # Create simple agents map
        agents_map = {"test_agent": compiled_agent}
        
        print(f"✓ Built agents map with {len(agents_map)} agents")
        
        # Build supervisor
        supervisor = build_supervisor_compiled(
            config.supervisor, config.agents, default_model,
            config.business_context or "")
        print("✓ Supervisor built successfully")
        
        # Test supervisor with a simple routing task
        test_input = "Can you help me with a test task?"
        print(f"\nTesting supervisor with input: {test_input}")
        
        # Test the supervisor routing
        result = await supervisor.ainvoke({
            "messages": [("user", test_input)],
            "next": ""
        }, config={"configurable": {"thread_id": "test-supervisor-thread"}})
        
        print("✓ Supervisor response received:")
        print(f"Next agent: {result.get('next', 'FINISH')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error in supervisor test: {e}")
        logger.error(f"Supervisor test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    print("Starting jk-agents Simple Tests")
    print("=" * 60)
    
    results = []
    
    # Test basic agent
    results.append(await test_basic_agent())
    
    # Test supervisor
    results.append(await test_supervisor_basic())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} tests passed!")
        return True
    else:
        print(f"✗ {total - passed} of {total} tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
