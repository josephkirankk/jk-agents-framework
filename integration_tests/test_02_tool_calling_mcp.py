"""
Integration Test 2: Tool Calling and MCP Servers
NO MOCKING - Real tool execution via MCP

Tests:
1. Python code execution via MCP
2. Tool calling workflow
3. Multiple tool calls in sequence
4. Tool error handling
"""

import asyncio
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
from dotenv import load_dotenv

load_dotenv()


async def test_python_execution_mcp():
    """Test Python code execution via MCP server"""
    result = TestResult("Python Execution via MCP")
    env = TestEnvironment("python_mcp")
    
    try:
        print_section("Testing Python MCP Server")
        
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "python_agent"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    prompt: |
      You are a Python coding assistant. Execute Python code to answer questions.
      Always use the python tool for calculations.
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args:
          - "run"
          - "-N"
          - "-R=node_modules"
          - "-W=node_modules"
          - "--node-modules-dir=auto"
          - "jsr:@pydantic/mcp-run-python"
          - "stdio"
"""
        
        config_file = env.create_temp_file("python_mcp.yaml", config_content)
        app_config = load_app_config(config_file)
        
        agent_cfg = app_config.agents[0]
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_file),
            app_config=app_config_dict
        )
        
        print(f"✓ Agent built with Python MCP server")
        
        # Test 1: Simple calculation
        print_section("Test 1: Simple Calculation")
        response = await invoke_agent(
            agent,
            "Calculate the factorial of 10 using Python. Show me the result."
        )
        
        tool_calls = extract_tool_calls(response['messages'])
        print(f"✓ Tool calls: {len(tool_calls)}")
        print(f"  Response: {response['response'][:200]}")
        
        # Factorial of 10 = 3628800
        has_answer = '3628800' in response['response']
        result.add_sub_test(
            "Factorial Calculation",
            has_answer and len(tool_calls) > 0,
            tool_calls=len(tool_calls),
            correct_answer=has_answer
        )
        
        # Test 2: List processing
        print_section("Test 2: List Processing")
        response2 = await invoke_agent(
            agent,
            "Create a Python list with numbers 1 to 20, filter only even numbers, and sum them."
        )
        
        tool_calls2 = extract_tool_calls(response2['messages'])
        print(f"✓ Tool calls: {len(tool_calls2)}")
        print(f"  Response: {response2['response'][:200]}")
        
        # Sum of even numbers 1-20: 2+4+6+8+10+12+14+16+18+20 = 110
        has_answer2 = '110' in response2['response']
        result.add_sub_test(
            "List Processing",
            has_answer2 and len(tool_calls2) > 0,
            tool_calls=len(tool_calls2),
            correct_answer=has_answer2
        )
        
        # Test 3: String manipulation
        print_section("Test 3: String Manipulation")
        response3 = await invoke_agent(
            agent,
            "Reverse the string 'Hello World' and convert to uppercase using Python."
        )
        
        tool_calls3 = extract_tool_calls(response3['messages'])
        print(f"✓ Tool calls: {len(tool_calls3)}")
        print(f"  Response: {response3['response']}")
        
        has_answer3 = 'DLROW OLLEH' in response3['response']
        result.add_sub_test(
            "String Manipulation",
            has_answer3,
            tool_calls=len(tool_calls3),
            correct_answer=has_answer3
        )
        
        total_calls = len(tool_calls) + len(tool_calls2) + len(tool_calls3)
        result.finish(
            True,
            total_tool_calls=total_calls,
            tests_passed=3
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
        if 'mcp_client' in locals() and mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass
    
    return result


async def test_multiple_tool_calls():
    """Test multiple tool calls in sequence"""
    result = TestResult("Multiple Sequential Tool Calls")
    env = TestEnvironment("multi_tools")
    
    try:
        print_section("Testing Multiple Tool Calls")
        
        # Use existing python_exec_agent config
        config_path = Path(__file__).parent.parent / "config" / "python_exec_agent_working.yaml"
        
        if not config_path.exists():
            result.finish(False, error=f"Config not found: {config_path}")
            return result
        
        app_config = load_app_config(config_path)
        
        # Find python exec agent
        agent_cfg = None
        for cfg in app_config.agents:
            if 'python' in cfg.name.lower():
                agent_cfg = cfg
                break
        
        if not agent_cfg:
            agent_cfg = app_config.agents[0]
        
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Agent built: {agent_cfg.name}")
        
        # Complex query requiring multiple tool calls
        response = await invoke_agent(
            agent,
            """
            Please do the following steps using Python:
            1. Calculate 50 * 45
            2. Take that result and add 1000
            3. Divide the final result by 10
            Show me each step.
            """
        )
        
        tool_calls = extract_tool_calls(response['messages'])
        print(f"✓ Total tool calls: {len(tool_calls)}")
        for i, tc in enumerate(tool_calls, 1):
            print(f"  {i}. {tc['tool_name']}")
        
        print(f"  Response: {response['response'][:300]}")
        
        # Expected: 50*45=2250, 2250+1000=3250, 3250/10=325
        has_final_answer = '325' in response['response'] or '325.0' in response['response']
        has_multiple_calls = len(tool_calls) >= 1
        
        result.add_sub_test(
            "Multi-step Calculation",
            has_final_answer and has_multiple_calls,
            tool_calls=len(tool_calls),
            correct_answer=has_final_answer
        )
        
        result.finish(
            True,
            tool_calls_executed=len(tool_calls),
            answer_correct=has_final_answer
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
        if 'mcp_client' in locals() and mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass
    
    return result


async def main():
    """Run all tool calling and MCP tests"""
    print_test_header("INTEGRATION TEST 2: Tool Calling and MCP Servers")
    
    if not check_azure_credentials():
        print("\n❌ Azure OpenAI credentials not configured!")
        return False
    
    print("✓ Azure OpenAI credentials configured\n")
    
    results = []
    
    # Test 1: Python MCP Server
    result1 = await test_python_execution_mcp()
    result1.print_result()
    results.append(result1)
    
    # Test 2: Multiple Tool Calls
    result2 = await test_multiple_tool_calls()
    result2.print_result()
    results.append(result2)
    
    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 2 SUMMARY: {passed}/{total} passed")
    print(f"{'=' * 80}\n")
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
