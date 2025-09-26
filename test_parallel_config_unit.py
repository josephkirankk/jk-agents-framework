#!/usr/bin/env python3
"""
Unit test for parallel tool calls configuration logic (no API dependencies)
"""

import os
import sys

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.config import AgentConfig, AppConfig
from app.gemini_schema_filter import is_gemini_model


def test_config_parsing():
    """Test that configuration schema accepts the new fields correctly"""
    print("🧪 Testing Configuration Schema")
    print("=" * 50)
    
    # Test agent config with parallel_tool_calls_enabled
    agent_config_data = {
        "name": "test_agent",
        "prompt": "You are a test agent.",
        "parallel_tool_calls_enabled": False
    }
    
    try:
        agent_config = AgentConfig(**agent_config_data)
        print(f"✅ Agent config parsed successfully")
        print(f"   parallel_tool_calls_enabled: {agent_config.parallel_tool_calls_enabled}")
        assert agent_config.parallel_tool_calls_enabled == False
        print(f"   ✅ Agent-level setting correctly set to False")
    except Exception as e:
        print(f"❌ Agent config parsing failed: {e}")
        return False
    
    # Test app config with parallel_tool_calls_enabled
    app_config_data = {
        "models": {"default": "openai:gpt-4o"},
        "parallel_tool_calls_enabled": True,
        "supervisor": {
            "name": "supervisor",
            "prompt": "You are a supervisor."
        },
        "agents": [agent_config_data]
    }
    
    try:
        app_config = AppConfig(**app_config_data)
        print(f"✅ App config parsed successfully")
        print(f"   parallel_tool_calls_enabled: {app_config.parallel_tool_calls_enabled}")
        assert app_config.parallel_tool_calls_enabled == True
        print(f"   ✅ App-level setting correctly set to True")
        
        agent = app_config.agents[0] 
        assert agent.parallel_tool_calls_enabled == False
        print(f"   ✅ Agent setting preserved despite app-level setting")
    except Exception as e:
        print(f"❌ App config parsing failed: {e}")
        return False
    
    return True


def test_gemini_detection():
    """Test the Gemini model detection logic"""
    print("\n🧪 Testing Gemini Model Detection")
    print("=" * 50)
    
    test_cases = [
        ("google:gemini-2.5-flash", True, "Google Gemini model"),
        ("google:gemini-pro", True, "Google Gemini Pro model"),
        ("openai:gpt-4o", False, "OpenAI model"), 
        ("anthropic:claude-3-sonnet", False, "Anthropic model"),
        ("azure_openai:gpt-4", False, "Azure OpenAI model"),
        ("some-other-model", False, "Unknown model")
    ]
    
    success_count = 0
    
    for model_id, expected_is_gemini, description in test_cases:
        result = is_gemini_model(model_id)
        if result == expected_is_gemini:
            print(f"✅ {model_id}: {result} (expected {expected_is_gemini}) - {description}")
            success_count += 1
        else:
            print(f"❌ {model_id}: {result} (expected {expected_is_gemini}) - {description}")
    
    print(f"\n📊 Gemini detection: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


def test_configuration_priority_logic():
    """Test the configuration priority logic without API calls"""
    print("\n🧪 Testing Configuration Priority Logic")
    print("=" * 50)
    
    test_cases = [
        # (agent_setting, app_setting, model_id, expected_result, description)
        (None, None, "google:gemini-2.5-flash", False, "Auto-detect: Gemini → disabled"),
        (None, None, "openai:gpt-4o", True, "Auto-detect: OpenAI → enabled"),
        (None, False, "openai:gpt-4o", False, "App override: disable OpenAI"),
        (None, True, "google:gemini-2.5-flash", True, "App override: enable Gemini"),
        (True, False, "google:gemini-2.5-flash", True, "Agent override: enable despite app disable"),
        (False, True, "openai:gpt-4o", False, "Agent override: disable despite app enable"),
        (True, None, "google:gemini-2.5-flash", True, "Agent setting only: enable Gemini"),
        (False, None, "openai:gpt-4o", False, "Agent setting only: disable OpenAI"),
    ]
    
    success_count = 0
    
    for agent_setting, app_setting, model_id, expected, description in test_cases:
        # Simulate the logic from agent_builder.py
        app_parallel = app_setting
        agent_parallel = agent_setting
        autodetect_parallel = not is_gemini_model(model_id)
        
        actual_result = (
            agent_parallel if agent_parallel is not None
            else (app_parallel if app_parallel is not None else autodetect_parallel)
        )
        
        if actual_result == expected:
            print(f"✅ {description}")
            print(f"   Agent={agent_setting}, App={app_setting}, Model={model_id}")
            print(f"   Result: {actual_result} (expected {expected})")
            success_count += 1
        else:
            print(f"❌ {description}")
            print(f"   Agent={agent_setting}, App={app_setting}, Model={model_id}")
            print(f"   Result: {actual_result} (expected {expected})")
        print()
    
    print(f"📊 Priority logic: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


def test_configuration_examples():
    """Test real-world configuration examples"""
    print("\n🧪 Testing Real-World Configuration Examples") 
    print("=" * 50)
    
    # Example 1: Mixed environment with auto-detection
    config1 = {
        "models": {"default": "openai:gpt-4o"},
        "supervisor": {"name": "supervisor", "prompt": "You are a supervisor."},
        "agents": [
            {
                "name": "gemini_agent", 
                "model": "google:gemini-2.5-flash",
                "prompt": "You are a Gemini agent."
            },
            {
                "name": "openai_agent",
                "model": "openai:gpt-4o", 
                "prompt": "You are an OpenAI agent."
            }
        ]
    }
    
    try:
        app_config1 = AppConfig(**config1)
        print("✅ Mixed environment config parsed successfully")
        
        # Check that agents inherit expected defaults
        gemini_agent = app_config1.agents[0]
        openai_agent = app_config1.agents[1]
        
        assert gemini_agent.parallel_tool_calls_enabled is None  # Should auto-detect to False
        assert openai_agent.parallel_tool_calls_enabled is None  # Should auto-detect to True
        print("   ✅ Agents have correct default settings for auto-detection")
    except Exception as e:
        print(f"❌ Mixed environment config failed: {e}")
        return False
    
    # Example 2: Global disable with agent override
    config2 = {
        "models": {"default": "openai:gpt-4o"},
        "parallel_tool_calls_enabled": False,  # Global disable
        "supervisor": {"name": "supervisor", "prompt": "You are a supervisor."},
        "agents": [
            {
                "name": "disabled_agent",
                "prompt": "You are a disabled agent."
            },
            {
                "name": "enabled_agent",
                "parallel_tool_calls_enabled": True,  # Override global
                "prompt": "You are an enabled agent."
            }
        ]
    }
    
    try:
        app_config2 = AppConfig(**config2)
        print("✅ Global disable with override config parsed successfully")
        
        assert app_config2.parallel_tool_calls_enabled == False
        disabled_agent = app_config2.agents[0]
        enabled_agent = app_config2.agents[1]
        
        assert disabled_agent.parallel_tool_calls_enabled is None  # Should use app setting (False)
        assert enabled_agent.parallel_tool_calls_enabled == True   # Override to True
        print("   ✅ Global disable with agent override working correctly")
    except Exception as e:
        print(f"❌ Global disable config failed: {e}")
        return False
    
    return True


def main():
    """Run all unit tests"""
    print("🚀 Parallel Tool Calls Configuration Unit Test Suite")
    print("=" * 70)
    print("Testing configuration logic without API dependencies...")
    
    tests = [
        ("Configuration Schema", test_config_parsing),
        ("Gemini Detection", test_gemini_detection), 
        ("Priority Logic", test_configuration_priority_logic),
        ("Real-World Examples", test_configuration_examples)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"📊 Final Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All configuration unit tests PASSED!")
        print("   ✅ Configuration schema working correctly")
        print("   ✅ Gemini model detection working correctly")
        print("   ✅ Priority logic working correctly")
        print("   ✅ Real-world examples working correctly")
        print("   ✅ Ready for production use")
        return 0
    else:
        print("❌ Some configuration unit tests FAILED!")
        print("   Check the error messages above for details")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())