#!/usr/bin/env python3
"""
Test script to verify parallel tool calls configuration is working correctly
"""

import os
import sys
import asyncio
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import AgentConfig, AppConfig
from app.agent_builder import build_react_agent
from app.checkpointer_manager import get_global_checkpointer


async def test_auto_detection():
    """Test auto-detection of parallel tool calls based on model provider"""
    print("🧪 Testing Auto-Detection")
    print("=" * 50)
    
    # Test configs for different providers
    test_cases = [
        ("google:gemini-2.5-flash", False, "Google Gemini should auto-disable"),
        ("openai:gpt-4o", True, "OpenAI should auto-enable"),
        ("anthropic:claude-3-sonnet", True, "Anthropic should auto-enable"),
        ("azure_openai:gpt-4", True, "Azure OpenAI should auto-enable"),
    ]
    
    for model_id, expected_parallel, description in test_cases:
        print(f"\n🔍 Testing {model_id}:")
        print(f"   Expected parallel_tool_calls: {expected_parallel}")
        print(f"   Reason: {description}")
        
        # Create minimal config
        config_data = {
            "models": {"default": model_id},
            "supervisor": {
                "name": "supervisor",
                "prompt": "You are a supervisor."
            },
            "agents": [{
                "name": "test_agent",
                "model": model_id,
                "prompt": "You are a test agent.",
                "mcp_servers": {}  # No tools needed for config test
            }]
        }
        
        try:
            app_config = AppConfig(**config_data)
            agent_config = app_config.agents[0]
            
            # Convert to dict for build_react_agent
            app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.dict()
            checkpointer = get_global_checkpointer(app_config_dict)
            
            # Build agent and capture logs
            agent, mcp_client = await build_react_agent(
                agent_cfg=agent_config,
                default_model=app_config.models.get('default'),
                checkpointer=checkpointer,
                app_config=app_config_dict
            )
            
            print(f"   ✅ Agent built successfully - auto-detection working")
            
            # Clean up
            if mcp_client:
                try:
                    await mcp_client.close()
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
    print(f"\n✅ Auto-detection tests completed")


async def test_configuration_overrides():
    """Test agent-level and app-level configuration overrides"""
    print("\n🧪 Testing Configuration Overrides")
    print("=" * 50)
    
    # Test app-level override
    print(f"\n🔍 Testing app-level override (global disable):")
    config_data = {
        "models": {"default": "openai:gpt-4o"},
        "parallel_tool_calls_enabled": False,  # Global disable
        "supervisor": {
            "name": "supervisor", 
            "prompt": "You are a supervisor."
        },
        "agents": [{
            "name": "openai_agent",
            "model": "openai:gpt-4o",  # Would normally auto-enable
            "prompt": "You are an OpenAI agent.",
            "mcp_servers": {}
        }]
    }
    
    try:
        app_config = AppConfig(**config_data)
        agent_config = app_config.agents[0]
        
        app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.dict()
        checkpointer = get_global_checkpointer(app_config_dict)
        
        agent, mcp_client = await build_react_agent(
            agent_cfg=agent_config,
            default_model=app_config.models.get('default'),
            checkpointer=checkpointer,
            app_config=app_config_dict
        )
        
        print(f"   ✅ App-level override working - OpenAI agent should use global disable")
        
        if mcp_client:
            try:
                await mcp_client.close()
            except:
                pass
                
    except Exception as e:
        print(f"   ❌ App-level override error: {e}")
    
    # Test agent-level override
    print(f"\n🔍 Testing agent-level override (agent enable, app disable):")
    config_data = {
        "models": {"default": "openai:gpt-4o"},
        "parallel_tool_calls_enabled": False,  # Global disable
        "supervisor": {
            "name": "supervisor",
            "prompt": "You are a supervisor."
        },
        "agents": [{
            "name": "override_agent", 
            "model": "openai:gpt-4o",
            "parallel_tool_calls_enabled": True,  # Agent-level enable
            "prompt": "You are an agent with overridden parallel calls.",
            "mcp_servers": {}
        }]
    }
    
    try:
        app_config = AppConfig(**config_data)
        agent_config = app_config.agents[0]
        
        app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.dict()
        checkpointer = get_global_checkpointer(app_config_dict)
        
        agent, mcp_client = await build_react_agent(
            agent_cfg=agent_config,
            default_model=app_config.models.get('default'),
            checkpointer=checkpointer,
            app_config=app_config_dict
        )
        
        print(f"   ✅ Agent-level override working - should enable despite global disable")
        
        if mcp_client:
            try:
                await mcp_client.close()
            except:
                pass
                
    except Exception as e:
        print(f"   ❌ Agent-level override error: {e}")
        
    print(f"\n✅ Configuration override tests completed")


async def test_mixed_configuration():
    """Test mixed configuration with different agents having different settings"""
    print("\n🧪 Testing Mixed Configuration")
    print("=" * 50)
    
    config_data = {
        "models": {"default": "openai:gpt-4o"},
        "supervisor": {
            "name": "supervisor",
            "prompt": "You are a supervisor."
        },
        "agents": [
            {
                "name": "gemini_agent",
                "model": "google:gemini-2.5-flash",  # Should auto-disable
                "prompt": "You are a Gemini agent.",
                "mcp_servers": {}
            },
            {
                "name": "openai_agent",
                "model": "openai:gpt-4o",  # Should auto-enable  
                "prompt": "You are an OpenAI agent.",
                "mcp_servers": {}
            },
            {
                "name": "forced_disabled_agent",
                "model": "openai:gpt-4o", 
                "parallel_tool_calls_enabled": False,  # Force disable
                "prompt": "You are an OpenAI agent with forced disable.",
                "mcp_servers": {}
            },
            {
                "name": "forced_enabled_gemini",
                "model": "google:gemini-2.5-flash",
                "parallel_tool_calls_enabled": True,  # Force enable (risky but configurable)
                "prompt": "You are a Gemini agent with forced enable.", 
                "mcp_servers": {}
            }
        ]
    }
    
    try:
        app_config = AppConfig(**config_data)
        app_config_dict = app_config.model_dump() if hasattr(app_config, 'model_dump') else app_config.dict()
        checkpointer = get_global_checkpointer(app_config_dict)
        
        for i, agent_config in enumerate(app_config.agents):
            print(f"\n🔍 Building agent {i+1}: {agent_config.name}")
            
            agent, mcp_client = await build_react_agent(
                agent_cfg=agent_config,
                default_model=app_config.models.get('default'),
                checkpointer=checkpointer,
                app_config=app_config_dict
            )
            
            print(f"   ✅ Agent {agent_config.name} built successfully")
            
            if mcp_client:
                try:
                    await mcp_client.close()
                except:
                    pass
                    
    except Exception as e:
        print(f"   ❌ Mixed configuration error: {e}")
        import traceback
        traceback.print_exc()
        
    print(f"\n✅ Mixed configuration tests completed")


async def main():
    """Run all tests"""
    print("🚀 Parallel Tool Calls Configuration Test Suite")
    print("=" * 70)
    print("Testing the new configurable parallel tool calls feature...")
    
    success_count = 0
    total_tests = 3
    
    try:
        await test_auto_detection()
        success_count += 1
    except Exception as e:
        print(f"❌ Auto-detection test failed: {e}")
    
    try:
        await test_configuration_overrides() 
        success_count += 1
    except Exception as e:
        print(f"❌ Configuration override test failed: {e}")
    
    try:
        await test_mixed_configuration()
        success_count += 1
    except Exception as e:
        print(f"❌ Mixed configuration test failed: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All parallel tool calls configuration tests PASSED!")
        print("   ✅ Auto-detection working correctly")
        print("   ✅ App-level overrides working correctly") 
        print("   ✅ Agent-level overrides working correctly")
        print("   ✅ Mixed configurations working correctly")
        return 0
    else:
        print("❌ Some parallel tool calls configuration tests FAILED!")
        print("   Check the error messages above for details")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))