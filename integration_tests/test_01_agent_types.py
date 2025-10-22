"""
Integration Test 1: Normal and React Agents with Azure OpenAI
NO MOCKING - Real Azure OpenAI API calls

Tests:
1. Create and invoke normal agent (conversational, no tools)
2. Create and invoke react agent (with tool calling capability)
3. Verify model selection and configuration
4. Verify response generation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, print_test_header, print_section,
    check_azure_credentials, invoke_agent, convert_app_config_to_dict
)

from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_normal_agent():
    """Test normal agent (conversational) with Azure OpenAI"""
    result = TestResult("Normal Agent with Azure OpenAI")
    env = TestEnvironment("normal_agent")
    
    # Generate unique thread_id (may be needed if agent has checkpointer)
    import uuid
    thread_id = f"test_normal_{uuid.uuid4().hex[:8]}"
    
    try:
        print_section("Testing Normal Agent Creation")
        
        # Create minimal config for normal agent
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  temperature: 0.3

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "test_normal_agent"
    description: "A conversational agent for testing"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"
    prompt: |
      You are a helpful assistant. Answer questions concisely.
      When asked about your type, say you are a normal conversational agent.
"""
        
        config_file = env.create_temp_file("test_normal_agent.yaml", config_content)
        
        # Load config
        app_config = load_app_config(config_file)
        print(f"✓ Config loaded: {len(app_config.agents)} agent(s)")
        
        # Build agent
        agent_cfg = app_config.agents[0]
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_file),
            app_config={"models": {"default": default_model}}
        )
        
        print(f"✓ Agent built: {type(agent).__name__}")
        result.add_sub_test("Agent Creation", True, agent_type=type(agent).__name__)
        
        # Test invocation
        print_section("Testing Normal Agent Invocation")
        
        response = await invoke_agent(
            agent,
            "What type of agent are you? Answer in one sentence.",
            thread_id=thread_id
        )
        
        print(f"✓ Response received ({response['duration']:.2f}s)")
        print(f"  Response: {response['response'][:200]}...")
        print(f"  Messages: {response['message_count']}")
        
        # Verify response
        response_lower = response['response'].lower()
        has_response = len(response['response']) > 10
        mentions_agent = 'agent' in response_lower or 'assistant' in response_lower
        
        result.add_sub_test(
            "Agent Response",
            has_response and mentions_agent,
            response_length=len(response['response']),
            duration=response['duration'],
            has_content=has_response
        )
        
        # Test with multiple queries
        print_section("Testing Multiple Interactions")
        
        response2 = await invoke_agent(
            agent,
            "What is 2+2? Just give the number.",
            thread_id=thread_id
        )
        
        print(f"✓ Second response received")
        print(f"  Response: {response2['response']}")
        
        has_number = '4' in response2['response']
        result.add_sub_test(
            "Math Question",
            has_number,
            response=response2['response']
        )
        
        result.finish(True,
                     agent_type="normal",
                     model="azure_openai:gpt-4.1",
                     total_queries=2)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def test_react_agent():
    """Test react agent (with tools) with Azure OpenAI"""
    result = TestResult("React Agent with Azure OpenAI")
    env = TestEnvironment("react_agent")
    
    # Generate unique thread_id for this test (react agents require checkpointer)
    import uuid
    thread_id = f"test_react_{uuid.uuid4().hex[:8]}"
    
    try:
        print_section("Testing React Agent Creation")
        
        # Create config for react agent with tools
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  temperature: 0.1

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "test_react_agent"
    description: "A react agent with tool calling capability"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    prompt: |
      You are a helpful assistant with access to tools.
      Use the python tool to calculate mathematical expressions.
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
        
        config_file = env.create_temp_file("test_react_agent.yaml", config_content)
        
        # Load config
        app_config = load_app_config(config_file)
        print(f"✓ Config loaded: {len(app_config.agents)} agent(s)")
        
        # Build agent
        agent_cfg = app_config.agents[0]
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_file),
            app_config={"models": {"default": default_model}}
        )
        
        print(f"✓ Agent built: {type(agent).__name__}")
        print(f"  Nodes: {list(agent.nodes.keys()) if hasattr(agent, 'nodes') else 'N/A'}")
        
        has_tools_node = hasattr(agent, 'nodes') and 'tools' in agent.nodes
        result.add_sub_test(
            "Agent Creation", 
            True,
            agent_type=type(agent).__name__,
            has_tools_node=has_tools_node
        )
        
        # Test simple invocation (no tool calling)
        print_section("Testing React Agent - Simple Query")
        
        response = await invoke_agent(
            agent,
            "Hello! Just say 'Hi' back.",
            thread_id=thread_id
        )
        
        print(f"✓ Response received ({response['duration']:.2f}s)")
        print(f"  Response: {response['response']}")
        
        has_greeting = any(word in response['response'].lower() for word in ['hi', 'hello'])
        result.add_sub_test(
            "Simple Query",
            has_greeting,
            response=response['response']
        )
        
        # Test tool calling
        print_section("Testing React Agent - With Tool Calling")
        
        response2 = await invoke_agent(
            agent,
            "Calculate: 15 * 23 + 100. Use Python to compute this.",
            thread_id=thread_id
        )
        
        print(f"✓ Response received ({response2['duration']:.2f}s)")
        print(f"  Response: {response2['response']}")
        print(f"  Messages: {response2['message_count']}")
        
        # Check for tool usage
        from test_utils import extract_tool_calls
        tool_calls = extract_tool_calls(response2['messages'])
        
        print(f"  Tool calls detected: {len(tool_calls)}")
        for tc in tool_calls:
            print(f"    - {tc['tool_name']}")
        
        # Expected answer: 15 * 23 + 100 = 445
        has_correct_answer = '445' in response2['response']
        has_tool_calls = len(tool_calls) > 0
        
        result.add_sub_test(
            "Tool Calling",
            has_tool_calls and has_correct_answer,
            tool_calls_count=len(tool_calls),
            correct_answer=has_correct_answer,
            tools_used=[tc['tool_name'] for tc in tool_calls]
        )
        
        result.finish(
            True,
            agent_type="react",
            model="azure_openai:gpt-4.1",
            total_queries=2,
            tool_calls=len(tool_calls)
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
        # Cleanup MCP client if exists
        if 'mcp_client' in locals() and mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass
    
    return result


async def test_agent_configuration():
    """Test agent configuration options"""
    result = TestResult("Agent Configuration Options")
    env = TestEnvironment("agent_config")
    
    try:
        print_section("Testing Agent Configuration")
        
        # Test different temperatures
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "creative_agent"
    model: "azure_openai:gpt-4.1:0.9"
    agent_type: "normal"
    prompt: "You are a creative assistant."
  
  - name: "precise_agent"
    model: "azure_openai:gpt-4.1:0.1"
    agent_type: "normal"
    prompt: "You are a precise assistant."
"""
        
        config_file = env.create_temp_file("test_config.yaml", config_content)
        app_config = load_app_config(config_file)
        
        print(f"✓ Config loaded with {len(app_config.agents)} agents")
        
        # Verify both agents can be built
        app_config_dict = convert_app_config_to_dict(app_config)
        for agent_cfg in app_config.agents:
            default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
            
            agent, mcp_client = await build_agent(
                agent_cfg=agent_cfg,
                default_model=default_model,
                business_context="",
                config_path=str(config_file),
                app_config=app_config_dict
            )
            
            print(f"✓ Built agent: {agent_cfg.name}")
            
            result.add_sub_test(
                f"Agent: {agent_cfg.name}",
                True,
                model=agent_cfg.model
            )
        
        result.finish(True, agents_tested=len(app_config.agents))
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def main():
    """Run all agent type tests"""
    print_test_header("INTEGRATION TEST 1: Agent Types with Azure OpenAI")
    
    # Check prerequisites
    if not check_azure_credentials():
        print("\n❌ Azure OpenAI credentials not configured!")
        print("Please set the following environment variables:")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_API_KEY")
        print("  - AZURE_OPENAI_DEPLOYMENT")
        print("  - AZURE_OPENAI_API_VERSION")
        return False
    
    print("✓ Azure OpenAI credentials configured\n")
    
    # Run tests
    results = []
    
    # Test 1: Normal Agent
    result1 = await test_normal_agent()
    result1.print_result()
    results.append(result1)
    
    # Test 2: React Agent
    result2 = await test_react_agent()
    result2.print_result()
    results.append(result2)
    
    # Test 3: Configuration
    result3 = await test_agent_configuration()
    result3.print_result()
    results.append(result3)
    
    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 1 SUMMARY: {passed}/{total} passed")
    print(f"{'=' * 80}\n")
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
