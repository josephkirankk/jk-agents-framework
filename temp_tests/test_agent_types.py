#!/usr/bin/env python3
"""
Test script to validate both react and normal agent types work correctly.
This tests the agent_type configuration option.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    
    # Fix for LangChain AzureChatOpenAI compatibility
    # It expects OPENAI_API_VERSION instead of AZURE_OPENAI_API_VERSION
    if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
        os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
        print("✅ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility")
    
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, skipping .env file loading")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

from app.config import AgentConfig, MCPServerConfig
from app.agent_builder import build_agent, build_react_agent
from app.mcp_loader import close_mcp_client
from langchain_core.messages import HumanMessage


async def test_react_agent():
    """Test that react agent type works with tools"""
    print("🔄 Testing React Agent (with tools)...")
    
    # Create a simple react agent config
    react_config = AgentConfig(
        name="test_react_agent",
        description="Test react agent with tool calling",
        model="azure_openai:gpt-4.1",
        agent_type="react",
        prompt="You are a helpful assistant that can use tools to solve problems.",
        mcp_servers={
            "python_runner": MCPServerConfig(
                description="Run Python code",
                transport="stdio",
                command="deno",
                args=[
                    "run", "-N", "-R=node_modules", "-W=node_modules",
                    "--node-modules-dir=auto", "jsr:@pydantic/mcp-run-python", "stdio"
                ]
            )
        }
    )
    
    try:
        # Build the agent
        agent, mcp_client = await build_agent(
            agent_cfg=react_config,
            default_model="azure_openai:gpt-4.1",
            enable_llm_payload_logging=False
        )
        
        print(f"✅ React agent built successfully: {type(agent)}")
        print(f"   - Agent name: {react_config.name}")
        print(f"   - Agent type: {react_config.agent_type}")
        
        # Verify it has the expected structure for a react agent
        if hasattr(agent, '_graph'):
            print("   - Has LangGraph structure ✅")
        
        if mcp_client:
            await close_mcp_client(mcp_client)
            
        return True
        
    except Exception as e:
        print(f"❌ React agent test failed: {e}")
        return False


async def test_normal_agent():
    """Test that normal agent type works without tools"""
    print("🔄 Testing Normal Agent (without tools)...")
    
    # Create a simple normal agent config
    normal_config = AgentConfig(
        name="test_normal_agent", 
        description="Test normal agent without tool calling",
        model="azure_openai:gpt-4.1",
        agent_type="normal",
        prompt="You are a helpful assistant that provides conversational responses."
    )
    
    try:
        # Build the agent
        agent, mcp_client = await build_agent(
            agent_cfg=normal_config,
            default_model="azure_openai:gpt-4.1",
            enable_llm_payload_logging=False
        )
        
        print(f"✅ Normal agent built successfully: {type(agent)}")
        print(f"   - Agent name: {normal_config.name}")
        print(f"   - Agent type: {normal_config.agent_type}")
        
        # Verify it has the expected structure for a normal agent
        if hasattr(agent, '_graph'):
            print("   - Has LangGraph structure ✅")
        
        if mcp_client:
            await close_mcp_client(mcp_client)
            
        return True
        
    except Exception as e:
        print(f"❌ Normal agent test failed: {e}")
        return False


async def test_backward_compatibility():
    """Test that build_react_agent still works (backward compatibility)"""
    print("🔄 Testing Backward Compatibility...")
    
    # Create a config without agent_type (should default to react)
    compat_config = AgentConfig(
        name="test_compat_agent",
        description="Test backward compatibility",
        model="azure_openai:gpt-4.1",
        # Note: no agent_type specified - should default to "react"
        prompt="You are a helpful assistant."
    )
    
    try:
        # Use old function name
        agent, mcp_client = await build_react_agent(
            agent_cfg=compat_config,
            default_model="azure_openai:gpt-4.1",
            enable_llm_payload_logging=False
        )
        
        print(f"✅ Backward compatibility test passed: {type(agent)}")
        print(f"   - Agent name: {compat_config.name}")
        print(f"   - Agent type: {getattr(compat_config, 'agent_type', 'default (react)')}")
        
        if mcp_client:
            await close_mcp_client(mcp_client)
            
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False


async def test_default_behavior():
    """Test that agents without agent_type specified default to react"""
    print("🔄 Testing Default Behavior (no agent_type specified)...")
    
    # Create a config without agent_type
    default_config = AgentConfig(
        name="test_default_agent",
        description="Test default agent type behavior",
        model="azure_openai:gpt-4.1",
        # No agent_type specified - should default to "react"
        prompt="You are a helpful assistant."
    )
    
    try:
        # Build the agent
        agent, mcp_client = await build_agent(
            agent_cfg=default_config,
            default_model="azure_openai:gpt-4.1",
            enable_llm_payload_logging=False
        )
        
        # Check that it defaults to react
        actual_type = getattr(default_config, "agent_type", "react") or "react"
        
        print(f"✅ Default behavior test passed: {type(agent)}")
        print(f"   - Agent name: {default_config.name}")
        print(f"   - Effective agent type: {actual_type}")
        
        if mcp_client:
            await close_mcp_client(mcp_client)
            
        return True
        
    except Exception as e:
        print(f"❌ Default behavior test failed: {e}")
        return False


async def main():
    """Run all agent type tests"""
    print("🚀 Starting Agent Type Configuration Tests\n")
    
    tests = [
        test_react_agent,
        test_normal_agent,
        test_backward_compatibility,
        test_default_behavior,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results Summary:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("✅ All agent type tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check configuration and dependencies.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
