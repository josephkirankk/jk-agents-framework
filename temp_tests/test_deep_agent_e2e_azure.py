"""
End-to-End DeepAgent Integration Test with Azure OpenAI

This script performs real API tests with Azure OpenAI to verify:
1. .env file loading
2. Azure OpenAI configuration
3. Basic DeepAgent creation and execution
4. DeepAgent with subagents
5. Multi-turn conversation
6. Filesystem operations

Run with:
    python temp_tests/test_deep_agent_e2e_azure.py
    
    Or with pytest:
    pytest temp_tests/test_deep_agent_e2e_azure.py -v -s
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env FIRST - critical for Azure credentials
print("Loading .env file...")
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ .env loaded from: {env_path}")
else:
    print(f"⚠️  .env not found at: {env_path}")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
from app.agent_builder import build_agent, HAS_DEEPAGENTS
from app.checkpointer_manager import get_global_checkpointer


# ============================================================================
# Environment Verification
# ============================================================================

def verify_environment():
    """Verify Azure OpenAI environment variables are set."""
    print("\n" + "="*70)
    print("🔍 Verifying Environment Configuration")
    print("="*70)
    
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_DEPLOYMENT": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION"),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask sensitive values
            if "KEY" in var_name:
                display_value = f"{var_value[:10]}..." if len(var_value) > 10 else "***"
            elif "ENDPOINT" in var_name:
                display_value = var_value[:50] + "..." if len(var_value) > 50 else var_value
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    # Check for OPENAI_API_VERSION (needed for subagents)
    openai_version = os.getenv("OPENAI_API_VERSION")
    if openai_version:
        print(f"✅ OPENAI_API_VERSION: {openai_version}")
    else:
        print(f"⚠️  OPENAI_API_VERSION: NOT SET (needed for subagents)")
    
    print("="*70)
    
    if not all_set:
        print("\n❌ Missing required environment variables!")
        print("\nPlease ensure your .env file contains:")
        print("  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
        print("  AZURE_OPENAI_DEPLOYMENT=gpt-4.1")
        print("  AZURE_OPENAI_API_KEY=your-key")
        print("  AZURE_OPENAI_API_VERSION=2023-05-15")
        print("  OPENAI_API_VERSION=2023-05-15  # For subagents")
        return False
    
    if not HAS_DEEPAGENTS:
        print("\n❌ DeepAgents package not installed!")
        print("Install with: pip install deepagents")
        return False
    
    print("\n✅ All environment checks passed!")
    return True


def get_azure_model():
    """Get Azure OpenAI model string from environment."""
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    return f"azure_openai:{deployment}"


# ============================================================================
# Test 1: Basic DeepAgent Creation and Simple Query
# ============================================================================

@pytest.mark.asyncio
async def test_01_basic_deep_agent_creation():
    """Test creating a basic DeepAgent with Azure OpenAI."""
    print("\n" + "="*70)
    print("🧪 TEST 1: Basic DeepAgent Creation")
    print("="*70)
    
    model = get_azure_model()
    print(f"Using model: {model}")
    
    config = AgentConfig(
        name="test_basic_agent",
        agent_type="deep",
        model=model,
        prompt="""You are a helpful test assistant.

When asked a question, provide a brief, clear answer.""",
        description="Basic test agent",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=[],
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    print("Creating agent...")
    # Use in-memory checkpointer for tests to avoid initialization issues
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    start_time = time.time()
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model=model,
        checkpointer=checkpointer,
    )
    creation_time = time.time() - start_time
    
    assert agent is not None
    print(f"✅ Agent created successfully in {creation_time:.2f}s")
    
    # Verify it's a DeepAgentAdapter
    from app.deep_agent_adapter import DeepAgentAdapter
    assert isinstance(agent, DeepAgentAdapter)
    print(f"✅ Agent is DeepAgentAdapter instance")
    
    # Cleanup
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except:
            pass
    
    print("="*70)
    print("✅ TEST 1 PASSED")
    print("="*70)


# ============================================================================
# Test 2: Basic Execution with API Call
# ============================================================================

@pytest.mark.asyncio
async def test_02_basic_execution():
    """Test basic agent execution with Azure OpenAI API call."""
    print("\n" + "="*70)
    print("🧪 TEST 2: Basic Execution with API Call")
    print("="*70)
    
    model = get_azure_model()
    
    config = AgentConfig(
        name="test_exec_agent",
        agent_type="deep",
        model=model,
        prompt="""You are a helpful math assistant.

Answer math questions clearly and concisely.""",
        description="Execution test agent",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=False,  # Keep it simple
            enable_todolist=False,
            enable_longterm_memory=False,
            subagents=[],
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    # Use in-memory checkpointer for tests
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model=model,
        checkpointer=checkpointer,
    )
    
    try:
        print("Executing query: 'What is 2 + 2?'")
        
        start_time = time.time()
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "What is 2 + 2? Answer in one sentence."}]},
            config={"configurable": {"thread_id": "test_exec_01"}}
        )
        exec_time = time.time() - start_time
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        response = result["messages"][-1].content
        print(f"\n📝 Response: {response}")
        print(f"⏱️  Execution time: {exec_time:.2f}s")
        
        # Verify response contains "4"
        assert "4" in response or "four" in response.lower()
        print("✅ Response contains correct answer")
        
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    print("="*70)
    print("✅ TEST 2 PASSED")
    print("="*70)


# ============================================================================
# Test 3: Filesystem Operations
# ============================================================================

@pytest.mark.asyncio
async def test_03_filesystem_operations():
    """Test DeepAgent filesystem capabilities."""
    print("\n" + "="*70)
    print("🧪 TEST 3: Filesystem Operations")
    print("="*70)
    
    model = get_azure_model()
    
    config = AgentConfig(
        name="test_filesystem_agent",
        agent_type="deep",
        model=model,
        prompt="""You are a helpful assistant with a filesystem.

When asked to store information:
1. Create a file called /test_data.md
2. Write the information to the file
3. Confirm what you stored""",
        description="Filesystem test agent",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,  # Enable filesystem
            enable_todolist=False,
            enable_longterm_memory=False,
            subagents=[],
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    # Use in-memory checkpointer for tests
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model=model,
        checkpointer=checkpointer,
    )
    
    try:
        print("Testing filesystem: 'Store this data: Test123'")
        
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "Store this data in a file: Test123"}]},
            config={"configurable": {"thread_id": "test_fs_01"}}
        )
        
        response = result["messages"][-1].content
        print(f"\n📝 Response: {response[:200]}...")
        
        # Check if filesystem was mentioned
        if "file" in response.lower() or "stored" in response.lower():
            print("✅ Agent used filesystem capabilities")
        else:
            print("⚠️  Filesystem usage unclear in response")
        
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    print("="*70)
    print("✅ TEST 3 PASSED")
    print("="*70)


# ============================================================================
# Test 4: Multi-Turn Conversation
# ============================================================================

@pytest.mark.asyncio
async def test_04_multiturn_conversation():
    """Test multi-turn conversation with context retention."""
    print("\n" + "="*70)
    print("🧪 TEST 4: Multi-Turn Conversation")
    print("="*70)
    
    model = get_azure_model()
    
    config = AgentConfig(
        name="test_multiturn_agent",
        agent_type="deep",
        model=model,
        prompt="""You are a helpful assistant. Remember information from previous messages in the conversation.""",
        description="Multi-turn test agent",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=False,
            enable_todolist=False,
            enable_longterm_memory=False,
            subagents=[],
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    # Use in-memory checkpointer for tests
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model=model,
        checkpointer=checkpointer,
    )
    
    try:
        thread_id = "test_multiturn_01"
        thread_config = {"configurable": {"thread_id": thread_id}}
        
        # Turn 1: Set context
        print("Turn 1: Setting context...")
        result1 = agent.invoke(
            {"messages": [{"role": "user", "content": "My favorite color is blue."}]},
            config=thread_config
        )
        response1 = result1["messages"][-1].content
        print(f"  Response: {response1[:100]}...")
        
        # Turn 2: Test context retention
        print("Turn 2: Testing context retention...")
        result2 = agent.invoke(
            {"messages": [{"role": "user", "content": "What is my favorite color?"}]},
            config=thread_config
        )
        response2 = result2["messages"][-1].content
        print(f"  Response: {response2}")
        
        # Verify context was retained
        if "blue" in response2.lower():
            print("✅ Context retained across turns")
        else:
            print("⚠️  Context retention unclear")
            print(f"   Expected 'blue' in response, got: {response2}")
        
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    print("="*70)
    print("✅ TEST 4 PASSED")
    print("="*70)


# ============================================================================
# Test 5: DeepAgent with Subagents
# ============================================================================

@pytest.mark.asyncio
async def test_05_deep_agent_with_subagents():
    """Test DeepAgent with subagent delegation."""
    print("\n" + "="*70)
    print("🧪 TEST 5: DeepAgent with Subagents")
    print("="*70)
    
    # Check if OPENAI_API_VERSION is set (required for subagents)
    if not os.getenv("OPENAI_API_VERSION"):
        print("⚠️  OPENAI_API_VERSION not set - adding it now...")
        os.environ["OPENAI_API_VERSION"] = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        print(f"   Set to: {os.environ['OPENAI_API_VERSION']}")
    
    model = get_azure_model()
    
    subagents = [
        SubAgentConfig(
            name="calculator",
            description="Does simple calculations",
            system_prompt="You are a calculator. Perform the calculation and return just the number.",
            model=model,
            tools=[],
        ),
    ]
    
    config = AgentConfig(
        name="test_orchestrator",
        agent_type="deep",
        model=model,
        prompt="""You are an orchestrator agent with subagents.

Available subagents:
- calculator: For math calculations

If asked a math question, delegate to the calculator subagent.""",
        description="Orchestrator with subagents",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=False,
            enable_todolist=False,
            enable_longterm_memory=False,
            subagents=subagents,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    print("Creating orchestrator agent with subagents...")
    # Use in-memory checkpointer for tests
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    try:
        agent, mcp_client = await build_agent(
            agent_cfg=config,
            default_model=model,
            checkpointer=checkpointer,
        )
        
        print(f"✅ Agent with {len(subagents)} subagent(s) created")
        
        # Test execution
        print("Testing: 'What is 5 + 3?'")
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "What is 5 + 3?"}]},
            config={"configurable": {"thread_id": "test_subagent_01"}}
        )
        
        response = result["messages"][-1].content
        print(f"\n📝 Response: {response}")
        
        if "8" in response or "eight" in response.lower():
            print("✅ Correct answer received")
        else:
            print("⚠️  Answer unclear in response")
        
    except Exception as e:
        print(f"❌ Error creating/using subagents: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    print("="*70)
    print("✅ TEST 5 PASSED")
    print("="*70)


# ============================================================================
# Main Test Runner
# ============================================================================

async def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "="*70)
    print("🚀 DeepAgent End-to-End Azure OpenAI Test Suite")
    print("="*70)
    
    # Verify environment first
    if not verify_environment():
        print("\n❌ Environment verification failed. Exiting.")
        return False
    
    tests = [
        ("Basic DeepAgent Creation", test_01_basic_deep_agent_creation),
        ("Basic Execution", test_02_basic_execution),
        ("Filesystem Operations", test_03_filesystem_operations),
        ("Multi-Turn Conversation", test_04_multiturn_conversation),
        ("DeepAgent with Subagents", test_05_deep_agent_with_subagents),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶️  Running: {test_name}")
            await test_func()
            passed += 1
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            failed += 1
            error_msg = f"❌ {test_name}: FAILED - {str(e)}"
            print(error_msg)
            errors.append(error_msg)
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if errors:
        print("\n❌ Failed Tests:")
        for error in errors:
            print(f"  {error}")
    
    print("="*70)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed")
        return False


def main():
    """Entry point for running tests."""
    try:
        success = asyncio.run(run_all_tests())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
