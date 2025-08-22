#!/usr/bin/env python3
"""
Test script for the dynamic supervisor and react agents
"""
import asyncio
import logging
from app.main import (
    load_app_config,
    build_agents_map,
    build_supervisor_compiled
)
from app.mcp_loader import close_mcp_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


async def test_basic_functionality():
    """Test basic supervisor and agent functionality"""
    print("=" * 50)
    print("Testing Basic Functionality")
    print("=" * 50)
    
    try:
        # Load configuration
        config = load_app_config()
        print(f"✓ Loaded config with {len(config.agents)} agents")
        
        # Build the application components
        default_model = config.models.get("default", "openai:gpt-4o-mini")
        
        # Build supervisor
        supervisor = build_supervisor_compiled(
            config.supervisor,
            config.agents,
            default_model,
            config.business_context or "",
        )
        
        # Build agents
        agents_map, mcp_clients = await build_agents_map(config)
        print(f"✓ Built supervisor and {len(agents_map)} agents")
        
        # Test a simple query to supervisor
        print("\n--- Testing Simple Query to Supervisor ---")
        result = await supervisor.ainvoke({
            "messages": [
                {"role": "system", "content": config.business_context or ""},
                {"role": "user", "content": "What is 15 + 27?"}
            ]
        })
        
        if result and 'messages' in result:
            last_msg = result['messages'][-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"Supervisor response: {content[:200]}...")
        
        return {
            'supervisor': supervisor,
            'agents_map': agents_map,
            'mcp_clients': mcp_clients,
            'config': config
        }
        
    except Exception as e:
        print(f"✗ Error in basic functionality test: {e}")
        raise


async def test_math_agent():
    """Test the math agent specifically"""
    print("\n" + "=" * 50)
    print("Testing Math Agent")
    print("=" * 50)
    
    try:
        config = load_app_config()
        agents_map, mcp_clients = await build_agents_map(config)
        
        # Test math agent directly
        math_agent = agents_map.get('math_agent')
        if not math_agent:
            print("✗ Math agent not found")
            return mcp_clients
            
        print("--- Testing Math Agent Directly ---")
        result = await math_agent.ainvoke({
            "messages": [
                {"role": "system", "content": "You are a math agent"},
                {"role": "user", "content": "Calculate 123 * 456"}
            ]
        })
        
        if result and 'messages' in result:
            last_msg = result['messages'][-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"Math agent response: {content}")
            
        return mcp_clients
        
    except Exception as e:
        print(f"✗ Error in math agent test: {e}")
        return {}


async def test_test_agent():
    """Test the test agent (no MCP dependencies)"""
    print("\n" + "=" * 50)
    print("Testing Test Agent")
    print("=" * 50)
    
    try:
        config = load_app_config()
        agents_map, mcp_clients = await build_agents_map(config)
        
        # Test test agent directly
        test_agent = agents_map.get('test_agent')
        if not test_agent:
            print("✗ Test agent not found")
            return mcp_clients
            
        print("--- Testing Test Agent Directly ---")
        result = await test_agent.ainvoke({
            "messages": [
                {"role": "system", "content": "You are a helpful test agent"},
                {"role": "user", "content": "Hello! Can you help me with basic questions?"}
            ]
        })
        
        if result and 'messages' in result:
            last_msg = result['messages'][-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"Test agent response: {content}")
            
        return mcp_clients
            
    except Exception as e:
        print(f"✗ Error in test agent test: {e}")
        return {}


async def test_full_execution():
    """Test full execution with supervisor and planner"""
    print("\n" + "=" * 50)
    print("Testing Full Execution")
    print("=" * 50)
    
    try:
        from app.planner_executor import execute_plan
        
        config = load_app_config()
        default_model = config.models.get("default", "openai:gpt-4o-mini")
        
        # Build supervisor
        supervisor = build_supervisor_compiled(
            config.supervisor,
            config.agents,
            default_model,
            config.business_context or "",
        )
        
        # Build agents
        agents_map, mcp_clients = await build_agents_map(config)
        
        # Test full execution with a simple math query
        print("--- Testing Full Execution: Math Query ---")
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input="Calculate the result of 25 * 8",
            business_context=config.business_context or "",
            max_total_retries=1
        )
        
        print(f"Execution status: {result.get('status')}")
        if result.get('final_result'):
            for step_id, step_result in result['final_result'].items():
                print(f"Step {step_id}: {step_result['summary']}")
                
        return result, mcp_clients
        
    except Exception as e:
        print(f"✗ Error in full execution test: {e}")
        return None, {}


async def main():
    """Run all tests"""
    print("Starting jk-agents System Tests")
    print("=" * 60)
    
    mcp_clients_to_cleanup = {}
    
    try:
        # Test 1: Basic functionality
        app_state = await test_basic_functionality()
        mcp_clients_to_cleanup.update(app_state.get('mcp_clients', {}))
        
        # Test 2: Test agent (no MCP dependencies)
        test_clients = await test_test_agent()
        mcp_clients_to_cleanup.update(test_clients)
        
        # Test 3: Math agent (with MCP)
        try:
            math_clients = await test_math_agent()
            mcp_clients_to_cleanup.update(math_clients)
        except Exception as e:
            print(f"⚠ Math agent test failed (possibly due to MCP server not running): {e}")
        
        # Test 4: Full execution
        try:
            result, exec_clients = await test_full_execution()
            if exec_clients:
                mcp_clients_to_cleanup.update(exec_clients)
        except Exception as e:
            print(f"⚠ Full execution test failed: {e}")
        
        print("\n" + "=" * 60)
        print("✓ System tests completed")
        
    except Exception as e:
        print(f"✗ System tests failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup MCP clients
        for client in mcp_clients_to_cleanup.values():
            try:
                if client:
                    await close_mcp_client(client)
            except Exception as e:
                print(f"Warning: Error closing MCP client: {e}")


if __name__ == "__main__":
    asyncio.run(main())
