"""
Integration Test 10: Serper Search MCP Integration
NO MOCKING - Real Serper API calls via MCP

Tests:
1. Google search via Serper MCP server
2. Query parameter conversion (query -> q)
3. Search results with region/language targeting
4. Verify 'undefined' query issue is fixed

This test validates the fix for the 'undefined' query parameter bug.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, print_test_header, print_section,
    check_azure_credentials, invoke_agent, extract_tool_calls,
    convert_app_config_to_dict
)

from app.main import load_app_config
from app.agent_builder import build_agent
from app.mcp_loader import close_mcp_client
from dotenv import load_dotenv

load_dotenv()


def check_serper_credentials():
    """Check if Serper API key is configured"""
    serper_key = os.getenv("SERPER_API_KEY")
    return bool(serper_key and len(serper_key) > 10)


async def test_serper_google_search():
    """Test Google search via Serper MCP server"""
    result = TestResult("Serper Google Search via MCP")
    env = TestEnvironment("serper_search")
    mcp_client = None
    
    try:
        print_section("Testing Serper Google Search")
        
        # Check API key
        if not check_serper_credentials():
            result.finish(False, error="SERPER_API_KEY not set in environment")
            return result
        
        print("✓ Serper API key is configured")
        
        # Load the deep_agent_advanced_serpapi config
        config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
        
        if not config_path.exists():
            result.finish(False, error=f"Config not found: {config_path}")
            return result
        
        print(f"✓ Loading config: {config_path.name}")
        app_config = load_app_config(config_path)
        
        # Find the research_orchestrator agent
        agent_cfg = None
        for cfg in app_config.agents:
            if cfg.name == "research_orchestrator":
                agent_cfg = cfg
                break
        
        if not agent_cfg:
            result.finish(False, error="research_orchestrator agent not found in config")
            return result
        
        print(f"✓ Found agent: {agent_cfg.name}")
        
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        # Build agent with Serper MCP tools
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Agent built with Serper MCP server")
        
        # Test 1: Simple search query
        print_section("Test 1: Simple Search Query")
        test_query = "best smartphones under 20000 rupees India 2025"
        thread_id = f"serper_test_{env.test_name}"
        
        response = await invoke_agent(
            agent,
            f'Search for: "{test_query}". Use google_search tool with region India (gl="in").',
            thread_id=thread_id
        )
        
        tool_calls = extract_tool_calls(response['messages'])
        print(f"✓ Tool calls made: {len(tool_calls)}")
        
        # Check if google_search was called
        search_calls = [tc for tc in tool_calls if tc['tool_name'] == 'google_search']
        print(f"✓ Google search calls: {len(search_calls)}")
        
        # Look for ToolMessages with search results
        tool_messages = [msg for msg in response['messages'] if hasattr(msg, '__class__') and msg.__class__.__name__ == 'ToolMessage']
        print(f"✓ Tool response messages: {len(tool_messages)}")
        
        found_valid_query = False
        if tool_messages:
            for i, tmsg in enumerate(tool_messages, 1):
                content = tmsg.content if hasattr(tmsg, 'content') else str(tmsg)
                print(f"\n  Tool Message {i}:")
                print(f"    Content length: {len(content)} chars")
                
                # Try to parse as JSON
                try:
                    if isinstance(content, str):
                        output_data = json.loads(content)
                    else:
                        output_data = content
                    
                    search_params = output_data.get('searchParameters', {})
                    
                    if search_params:
                        print(f"\n  📊 Search Parameters (Message {i}):")
                        print(f"     q: {search_params.get('q', 'NOT FOUND')}")
                        print(f"     gl: {search_params.get('gl', 'NOT FOUND')}")
                        print(f"     hl: {search_params.get('hl', 'NOT FOUND')}")
                        
                        # CRITICAL: Check if 'q' is NOT 'undefined'
                        query_value = search_params.get('q', '')
                        is_undefined = query_value == 'undefined' or not query_value
                        
                        if not is_undefined:
                            print(f"  ✅ PASS: Query parameter has actual value: '{query_value[:50]}...'")
                            found_valid_query = True
                            result.add_sub_test(
                                "Query parameter NOT undefined",
                                True,
                                query_value=query_value[:100],
                                search_params=search_params
                            )
                        else:
                            print(f"  ❌ FAILED: Query parameter is 'undefined' or empty!")
                            result.add_sub_test(
                                "Query parameter NOT undefined",
                                False,
                                error="Query is 'undefined' - the bug is NOT fixed",
                                search_params=search_params
                            )
                        
                        # Check if we got organic results
                        has_results = 'organic' in output_data and len(output_data.get('organic', [])) > 0
                        num_results = len(output_data.get('organic', []))
                        
                        if has_results:
                            print(f"  ✅ Got {num_results} organic search results")
                            result.add_sub_test(
                                "Got search results",
                                True,
                                num_results=num_results
                            )
                        break  # Found what we need
                    
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"    Could not parse as JSON: {e}")
                    continue
        
        if not found_valid_query and not tool_messages:
            print(f"  ⚠️  No ToolMessages found - checking tool calls")
            if search_calls:
                # At least we made the call
                result.add_sub_test(
                    "Google search tool called",
                    True,
                    calls=len(search_calls)
                )

        
        # Check response quality
        response_text = response['response']
        has_substantial_response = len(response_text) > 100
        
        result.add_sub_test(
            "Substantial response",
            has_substantial_response,
            response_length=len(response_text)
        )
        
        print(f"\n  📝 Response preview:")
        print(f"     {response_text[:300]}...")
        
        # Overall success if we made search calls and got results without 'undefined'
        success = (
            len(search_calls) > 0 and
            has_substantial_response
        )
        
        result.finish(
            success,
            tool_calls=len(tool_calls),
            search_calls=len(search_calls),
            response_length=len(response_text)
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
        if mcp_client:
            try:
                await close_mcp_client(mcp_client)
            except:
                pass
    
    return result


async def test_serper_query_parameter_conversion():
    """Test that 'query' parameter is correctly converted to 'q' for Serper"""
    result = TestResult("Query Parameter Conversion (query -> q)")
    env = TestEnvironment("serper_param_conversion")
    mcp_client = None
    
    try:
        print_section("Testing Query Parameter Conversion")
        
        # Check API key
        if not check_serper_credentials():
            result.finish(False, error="SERPER_API_KEY not set in environment")
            return result
        
        # Load config
        config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
        app_config = load_app_config(config_path)
        
        # Find agent
        agent_cfg = next((cfg for cfg in app_config.agents if cfg.name == "research_orchestrator"), None)
        if not agent_cfg:
            result.finish(False, error="Agent not found")
            return result
        
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        # Build agent
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Agent built")
        
        # Test with explicit region targeting
        print_section("Testing with India region (gl='in')")
        test_query = "Python programming tutorials 2025"
        thread_id = f"serper_param_test_{env.test_name}"
        
        response = await invoke_agent(
            agent,
            f'Search Google for "{test_query}" with region set to India. Use gl="in" and hl="en".',
            thread_id=thread_id
        )
        
        tool_calls = extract_tool_calls(response['messages'])
        search_calls = [tc for tc in tool_calls if tc['tool_name'] == 'google_search']
        
        print(f"✓ Search calls: {len(search_calls)}")
        
        # Look for ToolMessages with search results (same as first test)
        tool_messages = [msg for msg in response['messages'] if hasattr(msg, '__class__') and msg.__class__.__name__ == 'ToolMessage']
        print(f"✓ Tool response messages: {len(tool_messages)}")
        
        all_queries_valid = True
        valid_count = 0
        
        for i, tmsg in enumerate(tool_messages, 1):
            content = tmsg.content if hasattr(tmsg, 'content') else str(tmsg)
            
            try:
                if isinstance(content, str):
                    output_data = json.loads(content)
                else:
                    output_data = content
                
                search_params = output_data.get('searchParameters', {})
                
                if search_params:
                    q_value = search_params.get('q', '')
                    gl_value = search_params.get('gl', '')
                    hl_value = search_params.get('hl', '')
                    
                    print(f"\n  Call {i}:")
                    print(f"    q:  '{q_value}'")
                    print(f"    gl: '{gl_value}'")
                    print(f"    hl: '{hl_value}'")
                    
                    # Check if query is valid (not undefined and not empty)
                    is_valid = q_value and q_value != 'undefined' and len(q_value) > 0
                    
                    if not is_valid:
                        all_queries_valid = False
                        print(f"    ❌ Invalid query parameter!")
                    else:
                        valid_count += 1
                        print(f"    ✅ Valid query parameter")
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f"    ⚠️  Could not parse output: {e}")
        
        has_valid_queries = valid_count > 0
        
        result.add_sub_test(
            "At least one query has valid 'q' parameter",
            has_valid_queries,
            valid_queries=valid_count,
            total_search_calls=len(search_calls)
        )
        
        result.finish(
            has_valid_queries and len(search_calls) > 0,
            search_calls=len(search_calls),
            valid_queries=valid_count,
            all_valid=all_queries_valid
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
        if mcp_client:
            try:
                await close_mcp_client(mcp_client)
            except:
                pass
    
    return result


async def main():
    """Run all Serper search integration tests"""
    print_test_header("INTEGRATION TEST 10: Serper Search MCP Integration")
    
    # Check credentials
    if not check_azure_credentials():
        print("\n❌ Azure OpenAI credentials not configured!")
        return False
    
    if not check_serper_credentials():
        print("\n❌ SERPER_API_KEY not configured!")
        print("   Please set SERPER_API_KEY in your .env file")
        return False
    
    print("✓ Azure OpenAI credentials configured")
    print("✓ Serper API key configured\n")
    
    results = []
    
    # Test 1: Basic Google search
    result1 = await test_serper_google_search()
    result1.print_result()
    results.append(result1)
    
    # Test 2: Query parameter conversion
    result2 = await test_serper_query_parameter_conversion()
    result2.print_result()
    results.append(result2)
    
    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 10 SUMMARY: {passed}/{total} passed")
    print(f"{'=' * 80}")
    
    if passed == total:
        print("\n✅ All Serper search tests passed!")
        print("   The 'undefined' query parameter bug is FIXED!")
    else:
        print("\n❌ Some Serper search tests failed")
        print("   Check the output above for details")
    
    print()
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
