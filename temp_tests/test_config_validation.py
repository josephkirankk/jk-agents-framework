#!/usr/bin/env python3
"""
Test script to validate agent configuration and type validation.
This tests without requiring API credentials.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import AgentConfig, MCPServerConfig
from pydantic import ValidationError


def test_agent_type_validation():
    """Test that agent_type validation works correctly"""
    print("🔄 Testing Agent Type Validation...")
    
    # Test valid agent types
    valid_types = ["react", "normal"]
    
    for agent_type in valid_types:
        try:
            config = AgentConfig(
                name=f"test_{agent_type}_agent",
                description=f"Test {agent_type} agent",
                model="azure_openai:gpt-4.1",
                agent_type=agent_type,
                prompt="Test prompt"
            )
            print(f"   ✅ '{agent_type}' agent type validated successfully")
        except ValidationError as e:
            print(f"   ❌ '{agent_type}' agent type validation failed: {e}")
            return False
    
    # Test invalid agent type
    try:
        config = AgentConfig(
            name="test_invalid_agent",
            description="Test invalid agent",
            model="azure_openai:gpt-4.1",
            agent_type="invalid_type",
            prompt="Test prompt"
        )
        print("   ❌ Invalid agent type 'invalid_type' should have failed validation")
        return False
    except ValidationError:
        print("   ✅ Invalid agent type 'invalid_type' correctly rejected")
    
    return True


def test_default_agent_type():
    """Test that agent_type defaults to 'react'"""
    print("🔄 Testing Default Agent Type...")
    
    try:
        config = AgentConfig(
            name="test_default_agent",
            description="Test default agent type",
            model="azure_openai:gpt-4.1",
            # No agent_type specified
            prompt="Test prompt"
        )
        
        # Check that it defaults to "react"
        actual_type = config.agent_type
        expected_type = "react"
        
        if actual_type == expected_type:
            print(f"   ✅ Default agent type is '{actual_type}' (as expected)")
            return True
        else:
            print(f"   ❌ Default agent type is '{actual_type}', expected '{expected_type}'")
            return False
            
    except Exception as e:
        print(f"   ❌ Default agent type test failed: {e}")
        return False


def test_agent_type_in_config():
    """Test that agent_type field is properly included in config"""
    print("🔄 Testing Agent Type Field Inclusion...")
    
    try:
        # Test react agent
        react_config = AgentConfig(
            name="test_react",
            description="Test react agent",
            model="azure_openai:gpt-4.1",
            agent_type="react",
            prompt="Test prompt"
        )
        
        # Test normal agent
        normal_config = AgentConfig(
            name="test_normal",
            description="Test normal agent", 
            model="azure_openai:gpt-4.1",
            agent_type="normal",
            prompt="Test prompt"
        )
        
        # Verify field is accessible
        print(f"   ✅ React agent type: {react_config.agent_type}")
        print(f"   ✅ Normal agent type: {normal_config.agent_type}")
        
        # Verify in dict representation
        react_dict = react_config.model_dump() if hasattr(react_config, 'model_dump') else react_config.dict()
        normal_dict = normal_config.model_dump() if hasattr(normal_config, 'model_dump') else normal_config.dict()
        
        if 'agent_type' in react_dict and 'agent_type' in normal_dict:
            print(f"   ✅ agent_type field included in serialization")
            return True
        else:
            print(f"   ❌ agent_type field missing from serialization")
            return False
            
    except Exception as e:
        print(f"   ❌ Agent type field inclusion test failed: {e}")
        return False


def test_backward_compatibility():
    """Test that configurations without agent_type work"""
    print("🔄 Testing Backward Compatibility...")
    
    try:
        # Create config without agent_type (old style)
        old_config = AgentConfig(
            name="test_old_style",
            description="Test old style config",
            model="azure_openai:gpt-4.1",
            prompt="Test prompt"
            # No agent_type field
        )
        
        # Should work and default to react
        if old_config.agent_type == "react":
            print(f"   ✅ Backward compatibility: defaults to 'react'")
            return True
        else:
            print(f"   ❌ Backward compatibility failed: got '{old_config.agent_type}'")
            return False
            
    except Exception as e:
        print(f"   ❌ Backward compatibility test failed: {e}")
        return False


def main():
    """Run all configuration validation tests"""
    print("🚀 Starting Agent Type Configuration Validation Tests\n")
    
    tests = [
        test_agent_type_validation,
        test_default_agent_type, 
        test_agent_type_in_config,
        test_backward_compatibility,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
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
        print("✅ All configuration validation tests passed!")
        return True
    else:
        print("❌ Some tests failed. Check configuration setup.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
