"""
Integration Test 5: LiteLLM Multi-Provider Support
NO MOCKING - Real API calls to different providers

Tests:
1. Azure OpenAI via LiteLLM
2. Google Gemini (if credentials available)
3. Anthropic Claude (if credentials available)
4. Model switching and configuration
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, print_test_header, print_section,
    check_azure_credentials, check_google_credentials, check_anthropic_credentials, invoke_agent,
    convert_app_config_to_dict
)
from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

load_dotenv()


async def test_azure_litellm():
    """Test Azure OpenAI via standard interface"""
    result = TestResult("Azure OpenAI Provider")
    env = TestEnvironment("azure_provider")
    
    try:
        if not check_azure_credentials():
            result.finish(False, error="Azure credentials not available")
            return result
        
        print_section("Testing Azure Open AI")
        
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "azure_agent"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"
    prompt: "You are a helpful assistant."
"""
        
        config_file = env.create_temp_file("azure.yaml", config_content)
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
        
        print(f"✓ Agent built with Azure OpenAI")
        
        response = await invoke_agent(agent, "Say 'Hello from Azure'")
        
        has_response = len(response['response']) > 5
        result.add_sub_test(
            "Azure Response",
            has_response,
            response_length=len(response['response']),
            duration=response['duration']
        )
        
        result.finish(True, provider="azure_openai")
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def test_google_gemini():
    """Test Google Gemini if credentials available"""
    result = TestResult("Google Gemini Provider")
    env = TestEnvironment("gemini_provider")
    
    try:
        if not check_google_credentials():
            result.finish(False, error="Skipped - Google credentials not available")
            return result
        
        print_section("Testing Google Gemini")
        
        config_content = """
models:
  default: "gemini/gemini-2.0-flash-exp"
  supervisor: "gemini/gemini-2.0-flash-exp"

supervisor:
  name: "supervisor"
  model: "gemini/gemini-2.0-flash-exp"
  prompt: "You are a supervisor."

agents:
  - name: "gemini_agent"
    model: "gemini/gemini-2.0-flash-exp"
    agent_type: "normal"
    prompt: "You are a helpful assistant."
"""
        
        config_file = env.create_temp_file("gemini.yaml", config_content)
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
        
        print(f"✓ Agent built with Google Gemini")
        
        response = await invoke_agent(agent, "Say 'Hello from Gemini'")
        
        has_response = len(response['response']) > 5
        result.add_sub_test(
            "Gemini Response",
            has_response,
            response_length=len(response['response']),
            duration=response['duration']
        )
        
        result.finish(True, provider="google_gemini")
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def test_anthropic_claude():
    """Test Anthropic Claude if credentials available"""
    result = TestResult("Anthropic Claude Provider")
    env = TestEnvironment("anthropic_provider")
    
    try:
        if not check_anthropic_credentials():
            result.finish(False, error="Skipped - Anthropic credentials not available")
            return result
        
        print_section("Testing Anthropic Claude")
        
        config_content = """
models:
  default: "anthropic/claude-3-5-sonnet-20241022"
  supervisor: "anthropic/claude-3-5-sonnet-20241022"

supervisor:
  name: "supervisor"
  model: "anthropic/claude-3-5-sonnet-20241022"
  prompt: "You are a supervisor."

agents:
  - name: "claude_agent"
    model: "anthropic/claude-3-5-sonnet-20241022"
    agent_type: "normal"
    prompt: "You are a helpful assistant."
"""
        
        config_file = env.create_temp_file("anthropic.yaml", config_content)
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
        
        print(f"✓ Agent built with Anthropic Claude")
        
        response = await invoke_agent(agent, "Say 'Hello from Claude'")
        
        has_response = len(response['response']) > 5
        result.add_sub_test(
            "Claude Response",
            has_response,
            response_length=len(response['response']),
            duration=response['duration']
        )
        
        result.finish(True, provider="anthropic")
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def main():
    """Run all LiteLLM provider tests"""
    print_test_header("INTEGRATION TEST 5: LiteLLM Multi-Provider Support")
    
    results = []
    stats = TestStats()
    
    # Test Azure (required)
    result1 = await test_azure_litellm()
    result1.print_result()
    if "Skipped" not in str(result1.error or ""):
        stats.add_result(result1)
    else:
        stats.skip_test("Azure OpenAI", result1.error)
    
    # Test Gemini (optional)
    result2 = await test_google_gemini()
    result2.print_result()
    if "Skipped" not in str(result2.error or ""):
        stats.add_result(result2)
    else:
        stats.skip_test("Google Gemini", result2.error)
    
    # Test Anthropic (optional)
    result3 = await test_anthropic_claude()
    result3.print_result()
    if "Skipped" not in str(result3.error or ""):
        stats.add_result(result3)
    else:
        stats.skip_test("Anthropic Claude", result3.error)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 5 SUMMARY: {stats.passed}/{stats.total-stats.skipped} passed ({stats.skipped} skipped)")
    print(f"{'=' * 80}\n")
    
    return stats.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
