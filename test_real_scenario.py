#!/usr/bin/env python3
"""
Real scenario test for supervisor + search agent workflow
Tests the complete flow: User Query → Supervisor Planning → Agent Execution
"""
import asyncio
from pathlib import Path
from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_search_agent_directly():
    """Test the search agent directly without supervisor"""
    print("=" * 50)
    print("TESTING SEARCH AGENT DIRECTLY")
    print("=" * 50)
    
    try:
        # Load configuration
        config_path = (Path(__file__).resolve().parent / 
                      "config" / "new_agents.yaml")
        config = load_app_config(config_path)
        
        # Build search agent only
        print("\n� Building search agent...")
        agents_map, mcp_clients = await build_agents_map(config)
        
        if "search_agent" not in agents_map:
            print("✗ Search agent not found")
            return False
            
        search_agent = agents_map["search_agent"]
        print("✓ Search agent built successfully")
        
        # Test direct search
        test_query = "Find recent news about Python 3.13 release"
        print(f"\n🔍 Testing direct search: {test_query}")
        
        try:
            response = await search_agent.ainvoke(
                {"messages": [{"role": "user", "content": test_query}]},
                config={"configurable": {"thread_id": "direct-test"}}
            )
            
            if isinstance(response, dict) and 'messages' in response:
                result = response['messages'][-1].content
            else:
                result = str(response)
                
            print(f"✓ Search agent response:")
            print(f"  {result[:500]}..." if len(result) > 500 else f"  {result}")
            
            return True
            
        except Exception as e:
            print(f"✗ Direct search test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"✗ Search agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'mcp_clients' in locals():
            for client in mcp_clients.values():
                if client and hasattr(client, 'close'):
                    try:
                        await client.close()
                    except:
                        pass


async def test_full_workflow():
    """Test the complete supervisor + search agent workflow"""
    print("=" * 60)
    print("TESTING FULL SUPERVISOR + SEARCH AGENT WORKFLOW")
    print("=" * 60)
    
    try:
        # Load configuration
        config_path = (Path(__file__).resolve().parent / 
                      "config" / "new_agents.yaml")
        config = load_app_config(config_path)
        print(f"✓ Loaded config with {len(config.agents)} agents")
        
        # Build all agents
        print("\n📋 Building agents...")
        agents_map, mcp_clients = await build_agents_map(config)
        print(f"✓ Built {len(agents_map)} agents:")
        for name in agents_map.keys():
            print(f"  - {name}")
        
        # Build supervisor
        print("\n🎯 Building supervisor...")
        default_model = config.models.get("default", "openai:gpt-4o-mini")
        business_context = config.business_context or ""
        
        supervisor = build_supervisor_compiled(
            config.supervisor,
            config.agents,
            default_model,
            business_context
        )
        print("✓ Supervisor built successfully")
        
        # Test scenarios
        test_scenarios = [
            "Find the latest news about artificial intelligence in 2025",
            "Search for information about current weather APIs",
            "Look up recent Python web framework developments"
        ]
        
        for i, query in enumerate(test_scenarios, 1):
            print(f"\n" + "=" * 50)
            print(f"TEST SCENARIO {i}: {query}")
            print("=" * 50)
            
            try:
                # Execute the complete workflow
                print(f"\n🔄 Executing workflow...")
                results = await execute_plan(
                    supervisor,
                    agents_map,
                    query,
                    business_context,
                    default_model
                )
                
                print(f"✓ Workflow execution completed!")
                print(f"📊 Results summary:")
                
                for step_id, result in results.items():
                    status = "✓" if result.get("success", False) else "✗"
                    print(f"  {status} {step_id}: {result.get('status', 'Unknown')}")
                    
                    if result.get("success") and result.get("output"):
                        output = result["output"]
                        # Truncate long outputs for readability
                        if len(output) > 300:
                            output = output[:300] + "..."
                        print(f"      Output: {output}")
                
            except Exception as e:
                print(f"✗ Workflow execution failed: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n" + "=" * 60)
        print("🎉 WORKFLOW TEST COMPLETED!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up agents
        if 'mcp_clients' in locals():
            for client in mcp_clients.values():
                if client and hasattr(client, 'close'):
                    try:
                        await client.close()
                    except:
                        pass


async def main():
    """Main test runner"""
    print("JK-AGENTS REAL SCENARIO TESTING")
    print("=" * 40)
    
    # Test 1: Direct search agent test
    print("\n🧪 TEST 1: Direct Search Agent")
    direct_success = await test_search_agent_directly()
    
    if direct_success:
        print("\n🧪 TEST 2: Full Supervisor Workflow")
        # Test 2: Full workflow test
        workflow_success = await test_full_workflow()
        
        if workflow_success:
            print("\n🎉 ALL TESTS PASSED! The system is working correctly.")
        else:
            print("\n⚠️  Direct agent works, but workflow has issues.")
        
        return workflow_success
    else:
        print("\n❌ Search agent not working. Check MCP server connection.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
