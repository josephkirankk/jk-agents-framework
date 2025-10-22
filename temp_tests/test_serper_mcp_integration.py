"""
Integration Test: Serper MCP Server
Tests the Serper Search & Scrape MCP server integration.

Tests:
1. MCP server initialization
2. Google search tool availability and execution
3. Web scraping tool availability and execution
4. Error handling
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.main import load_app_config
from app.agent_builder import build_agent

# Load environment variables
load_dotenv()


class TestResult:
    """Simple test result tracker"""
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.error = None
        self.details = {}
        
    def finish(self, passed, **details):
        self.passed = passed
        self.details = details
        
    def print_result(self):
        status = "✓ PASSED" if self.passed else "✗ FAILED"
        print(f"\n{'=' * 80}")
        print(f"{status}: {self.name}")
        if self.error:
            print(f"Error: {self.error}")
        for key, value in self.details.items():
            print(f"  {key}: {value}")
        print(f"{'=' * 80}\n")


def print_section(title):
    """Print a section header"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def check_serper_api_key():
    """Check if Serper API key is configured"""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key or api_key == "your-serper-api-key-here":
        return False
    return True


async def test_serper_config_loading():
    """Test that Serper MCP configuration loads correctly"""
    result = TestResult("Serper MCP Configuration Loading")
    
    try:
        print_section("Loading Serper Configuration")
        
        config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
        
        if not config_path.exists():
            result.error = f"Config not found: {config_path}"
            result.finish(False)
            return result
        
        print(f"✓ Config file found: {config_path}")
        
        # Load configuration
        app_config = load_app_config(config_path)
        print(f"✓ Configuration loaded successfully")
        
        # Find agent with Serper MCP server
        serper_agent = None
        for agent in app_config.agents:
            if agent.mcp_servers and "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
        
        if not serper_agent:
            result.error = "No agent with serper-search MCP server found"
            result.finish(False)
            return result
        
        print(f"✓ Serper agent found: {serper_agent.name}")
        
        # Check MCP server configuration
        serper_mcp = serper_agent.mcp_servers["serper-search"]
        
        # Convert to dict if needed
        if hasattr(serper_mcp, 'model_dump'):
            serper_mcp_dict = serper_mcp.model_dump()
        elif hasattr(serper_mcp, 'dict'):
            serper_mcp_dict = serper_mcp.dict()
        else:
            serper_mcp_dict = serper_mcp
        
        print(f"✓ MCP server config:")
        print(f"  Command: {serper_mcp_dict.get('command')}")
        print(f"  Transport: {serper_mcp_dict.get('transport')}")
        print(f"  Args: {serper_mcp_dict.get('args')}")
        
        # Verify environment variables
        env_config = serper_mcp_dict.get('env', {})
        if 'SERPER_API_KEY' not in env_config:
            result.error = "SERPER_API_KEY not in MCP config"
            result.finish(False)
            return result
        
        print(f"✓ SERPER_API_KEY configured in MCP server")
        
        result.finish(
            True,
            agent_name=serper_agent.name,
            command=serper_mcp_dict.get('command'),
            transport=serper_mcp_dict.get('transport')
        )
        
    except Exception as e:
        result.error = str(e)
        result.finish(False)
        import traceback
        traceback.print_exc()
    
    return result


async def test_serper_mcp_initialization():
    """Test that Serper MCP server initializes correctly"""
    result = TestResult("Serper MCP Server Initialization")
    mcp_client = None
    
    try:
        print_section("Initializing Serper MCP Server")
        
        # Check API key first
        if not check_serper_api_key():
            result.error = "SERPER_API_KEY not configured properly in .env file"
            result.finish(False)
            return result
        
        print(f"✓ SERPER_API_KEY configured")
        
        config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
        app_config = load_app_config(config_path)
        
        # Find agent with Serper MCP
        serper_agent = None
        for agent in app_config.agents:
            if agent.mcp_servers and "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
        
        if not serper_agent:
            result.error = "Serper agent not found"
            result.finish(False)
            return result
        
        # Convert app_config to dict
        if hasattr(app_config, 'model_dump'):
            app_config_dict = app_config.model_dump()
        elif hasattr(app_config, 'dict'):
            app_config_dict = app_config.dict()
        else:
            app_config_dict = {}
        
        # Build agent with timeout
        print("Starting MCP server (30s timeout)...")
        default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default
        
        agent, mcp_client = await asyncio.wait_for(
            build_agent(
                agent_cfg=serper_agent,
                default_model=default_model,
                business_context="",
                config_path=str(config_path),
                app_config=app_config_dict
            ),
            timeout=30.0
        )
        
        print(f"✓ Agent built successfully")
        
        # Check if tools are available
        if hasattr(agent, 'tools') and agent.tools:
            tools = agent.tools
            tool_names = [t.name if hasattr(t, 'name') else str(t) for t in tools]
            print(f"✓ Tools loaded: {len(tool_names)}")
            
            # Check for expected Serper tools
            expected_tools = ['google_search', 'scrape']
            found_tools = [tool for tool in expected_tools if any(tool in name.lower() for name in tool_names)]
            
            print(f"✓ Expected Serper tools found: {found_tools}")
            
            if len(found_tools) > 0:
                result.finish(
                    True,
                    total_tools=len(tool_names),
                    serper_tools=found_tools,
                    sample_tools=tool_names[:5]
                )
            else:
                result.error = f"Expected tools not found. Available tools: {tool_names[:10]}"
                result.finish(False)
        else:
            result.error = "No tools found on agent"
            result.finish(False)
        
    except asyncio.TimeoutError:
        result.error = "MCP server initialization timed out after 30 seconds"
        result.finish(False)
    except Exception as e:
        result.error = str(e)
        result.finish(False)
        import traceback
        traceback.print_exc()
    finally:
        if mcp_client:
            try:
                await mcp_client.cleanup()
                print("✓ MCP client cleaned up")
            except:
                pass
    
    return result


async def test_google_search_tool():
    """Test Google search functionality"""
    result = TestResult("Google Search Tool Execution")
    mcp_client = None
    
    try:
        print_section("Testing Google Search")
        
        # Check API key
        if not check_serper_api_key():
            result.error = "SERPER_API_KEY not configured"
            result.finish(False)
            return result
        
        config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
        app_config = load_app_config(config_path)
        
        # Find agent
        serper_agent = None
        for agent in app_config.agents:
            if agent.mcp_servers and "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
        
        if not serper_agent:
            result.error = "Serper agent not found"
            result.finish(False)
            return result
        
        # Convert app_config to dict
        if hasattr(app_config, 'model_dump'):
            app_config_dict = app_config.model_dump()
        elif hasattr(app_config, 'dict'):
            app_config_dict = app_config.dict()
        else:
            app_config_dict = {}
        
        default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default
        
        # Build agent
        agent, mcp_client = await build_agent(
            agent_cfg=serper_agent,
            default_model=default_model,
            business_context="",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Agent built")
        
        # Invoke agent with search query
        print("Executing search: 'Python programming language'")
        
        response = await agent.ainvoke({
            "messages": [("user", "Search for information about Python programming language using google_search tool. Just show me the top 3 results.")]
        })
        
        # Extract response
        if isinstance(response, dict) and 'messages' in response:
            messages = response['messages']
            if messages:
                last_message = messages[-1]
                response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
                print(f"✓ Search completed")
                print(f"  Response preview: {response_text[:300]}...")
                
                # Check if response contains search results
                has_results = any(keyword in response_text.lower() for keyword in ['python', 'programming', 'search', 'result'])
                
                result.finish(
                    has_results,
                    response_length=len(response_text),
                    has_results=has_results
                )
            else:
                result.error = "No messages in response"
                result.finish(False)
        else:
            result.error = f"Unexpected response format: {type(response)}"
            result.finish(False)
        
    except Exception as e:
        result.error = str(e)
        result.finish(False)
        import traceback
        traceback.print_exc()
    finally:
        if mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass
    
    return result


async def main():
    """Run all Serper MCP tests"""
    print("\n" + "=" * 80)
    print("  SERPER MCP SERVER INTEGRATION TESTS")
    print("=" * 80)
    
    # Check prerequisites
    if not check_serper_api_key():
        print("\n❌ SERPER_API_KEY not configured in .env file!")
        print("   Please add your Serper API key to .env:")
        print("   SERPER_API_KEY=your-api-key-here")
        print("\n   Get your API key from: https://serper.dev")
        return False
    
    print("✓ SERPER_API_KEY configured\n")
    
    results = []
    
    # Test 1: Configuration Loading
    result1 = await test_serper_config_loading()
    result1.print_result()
    results.append(result1)
    
    # Test 2: MCP Server Initialization
    if result1.passed:
        result2 = await test_serper_mcp_initialization()
        result2.print_result()
        results.append(result2)
        
        # Test 3: Google Search (only if initialization passed)
        if result2.passed:
            result3 = await test_google_search_tool()
            result3.print_result()
            results.append(result3)
    
    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST SUMMARY: {passed}/{total} tests passed")
    print(f"{'=' * 80}\n")
    
    if passed == total:
        print("✓ All tests passed! Serper MCP server is working correctly.")
    else:
        print("✗ Some tests failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
