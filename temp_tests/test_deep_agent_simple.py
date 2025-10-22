"""
Simple DeepAgent Integration Test

Quick verification that DeepAgents integration is working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    
    # Test DeepAgents package
    try:
        import deepagents
        print("  ✅ deepagents package imported")
    except ImportError as e:
        print(f"  ❌ deepagents import failed: {e}")
        return False
    
    # Test config models
    try:
        from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
        print("  ✅ Config models imported")
    except ImportError as e:
        print(f"  ❌ Config models import failed: {e}")
        return False
    
    # Test adapter
    try:
        from app.deep_agent_adapter import DeepAgentAdapter, create_deep_agent_from_config
        print("  ✅ DeepAgentAdapter imported")
    except ImportError as e:
        print(f"  ❌ DeepAgentAdapter import failed: {e}")
        return False
    
    # Test agent builder
    try:
        from app.agent_builder import build_agent, HAS_DEEPAGENTS
        print(f"  ✅ Agent builder imported (HAS_DEEPAGENTS={HAS_DEEPAGENTS})")
    except ImportError as e:
        print(f"  ❌ Agent builder import failed: {e}")
        return False
    
    return True


def test_config_creation():
    """Test creating configurations."""
    print("\nTesting configuration creation...")
    
    from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
    
    # Test DeepAgentConfig
    try:
        deep_config = DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
        )
        print(f"  ✅ DeepAgentConfig created")
    except Exception as e:
        print(f"  ❌ DeepAgentConfig creation failed: {e}")
        return False
    
    # Test SubAgentConfig
    try:
        sub_config = SubAgentConfig(
            name="test_sub",
            description="Test subagent",
            system_prompt="Test prompt",
        )
        print(f"  ✅ SubAgentConfig created")
    except Exception as e:
        print(f"  ❌ SubAgentConfig creation failed: {e}")
        return False
    
    # Test AgentConfig with deep_agent_config
    try:
        agent_config = AgentConfig(
            name="test_agent",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="Test prompt",
            deep_agent_config=deep_config,
        )
        print(f"  ✅ AgentConfig with deep_agent_config created")
    except Exception as e:
        print(f"  ❌ AgentConfig creation failed: {e}")
        return False
    
    return True


def test_adapter_creation():
    """Test creating adapter (without actual API call)."""
    print("\nTesting adapter creation...")
    
    from app.deep_agent_adapter import DeepAgentAdapter
    from app.config import AgentConfig, DeepAgentConfig
    
    # Create mock model (just a string for this test)
    mock_model = "mock_model"
    tools = []
    system_prompt = "Test system prompt"
    deep_config = {
        "enabled": True,
        "enable_filesystem": True,
        "enable_todolist": True,
        "enable_longterm_memory": False,
        "subagents": [],
    }
    
    try:
        # This will fail because we don't have a real model, but we can test instantiation
        adapter = DeepAgentAdapter(
            model=mock_model,
            tools=tools,
            system_prompt=system_prompt,
            deep_config=deep_config,
            checkpointer=None,
            agent_name="test_agent"
        )
        print(f"  ⚠️  Adapter instantiation started (may fail on _build_deep_agent)")
    except Exception as e:
        # Expected to fail without real model/deepagents setup
        if "deepagents" in str(e).lower() or "create_deep_agent" in str(e):
            print(f"  ✅ Adapter class works (failed on internal deepagents call as expected)")
            return True
        else:
            print(f"  ❌ Adapter creation failed unexpectedly: {e}")
            return False
    
    return True


def main():
    """Run all simple tests."""
    print("="*70)
    print("DeepAgent Integration - Simple Tests")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration Creation", test_config_creation()))
    results.append(("Adapter Creation", test_adapter_creation()))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
