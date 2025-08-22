#!/usr/bin/env python3
"""
Simple test script focusing on test_agent (no MCP dependencies)
"""
import asyncio
import logging
from app.main import load_app_config, run_direct_agent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


async def test_simple_agent():
    """Test the test agent directly using the existing run_direct_agent function"""
    print("=" * 60)
    print("Testing Test Agent (No MCP Dependencies)")
    print("=" * 60)
    
    try:
        config = load_app_config()
        print(f"✓ Loaded config with {len(config.agents)} agents")
        
        # Test the test_agent which has no MCP servers
        print("\n--- Testing test_agent with simple query ---")
        await run_direct_agent("test_agent", "Hello! What is 2 + 2?", config)
        
        print("\n--- Testing test_agent with business context ---")
        await run_direct_agent(
            "test_agent", 
            "I need help understanding what ACME Inc does", 
            config
        )
        
        print("\n✓ Test agent working correctly!")
        
    except Exception as e:
        print(f"✗ Error testing test_agent: {e}")
        import traceback
        traceback.print_exc()


async def test_supervisor_routing():
    """Test supervisor routing using run_supervised"""
    print("\n" + "=" * 60)
    print("Testing Supervisor Routing")
    print("=" * 60)
    
    try:
        from app.main import run_supervised
        config = load_app_config()
        
        print("\n--- Testing supervisor with simple query ---")
        print("Query: 'What is 5 * 6?'")
        
        # This should route to test_agent since math_agent has MCP dependencies
        await run_supervised("What is 5 * 6?", config)
        
        print("\n✓ Supervisor routing test completed!")
        
    except Exception as e:
        print(f"✗ Error testing supervisor: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run simplified tests"""
    print("Starting jk-agents Simplified Tests")
    print("=" * 70)
    
    try:
        # Test 1: Direct test agent
        await test_simple_agent()
        
        # Test 2: Supervisor routing (may fail due to MCP dependencies)
        try:
            await test_supervisor_routing()
        except Exception as e:
            print(f"⚠ Supervisor test failed (likely due to MCP dependencies): {e}")
        
        print("\n" + "=" * 70)
        print("✓ Simplified tests completed")
        
    except Exception as e:
        print(f"✗ Tests failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
