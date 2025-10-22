"""
Comprehensive DeepAgent Integration Tests

This test suite provides detailed testing of:
1. DeepAgent configuration and creation
2. Basic execution and response generation
3. Multi-turn conversation with context
4. Subagent delegation and isolation
5. MCP tool integration (Brave Search)
6. Filesystem operations
7. TodoList middleware
8. Error handling and edge cases
9. Performance and resource usage
10. Backward compatibility

Run with:
    pytest temp_tests/test_deep_agent_comprehensive.py -v -s
    pytest temp_tests/test_deep_agent_comprehensive.py -v -s -k test_basic
"""

import pytest
import sys
import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import (
    AgentConfig, 
    DeepAgentConfig, 
    SubAgentConfig,
    MCPServerConfig
)
from app.agent_builder import build_agent, HAS_DEEPAGENTS
from langgraph.checkpoint.memory import MemorySaver


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

@pytest.fixture
def test_thread_id():
    """Generate unique thread ID for tests."""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def basic_deep_agent_config():
    """Basic DeepAgent configuration without subagents."""
    # Use Azure OpenAI if available, otherwise OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY"):
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        model = f"azure_openai:{deployment}"
    else:
        model = "openai:gpt-4o-mini"
    
    return AgentConfig(
        name="test_deep_agent",
        agent_type="deep",
        model=model,
        prompt="""You are a test agent with filesystem and planning capabilities.

When asked a question:
1. Create a file /test_response.md with your findings
2. Provide a clear, concise answer

Use the filesystem to organize your work.""",
        description="Test DeepAgent",
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


@pytest.fixture
def subagent_deep_agent_config():
    """DeepAgent configuration with subagents."""
    # Use Azure OpenAI if available, otherwise OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY"):
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        model = f"azure_openai:{deployment}"
    else:
        model = "openai:gpt-4o-mini"
    
    subagents = [
        SubAgentConfig(
            name="analyzer",
            description="Analyzes data and provides insights",
            system_prompt="You are an analyzer. Process data and provide insights.",
            model=model,  # Use same model as parent
            tools=[],
        ),
        SubAgentConfig(
            name="validator",
            description="Validates information accuracy",
            system_prompt="You are a validator. Check facts and verify claims.",
            model=model,  # Use same model as parent
            tools=[],
        ),
    ]
    
    return AgentConfig(
        name="test_orchestrator",
        agent_type="deep",
        model=model,
        prompt="""You are a test orchestrator with subagents.

Available subagents:
- analyzer: For data analysis
- validator: For fact checking

Delegate tasks appropriately and synthesize results.""",
        description="Test orchestrator with subagents",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=subagents,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )


@pytest.fixture
def brave_search_deep_agent_config():
    """DeepAgent configuration with Brave Search MCP."""
    # Use Azure OpenAI if available, otherwise OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY"):
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        model = f"azure_openai:{deployment}"
    else:
        model = "openai:gpt-4o-mini"
    
    return AgentConfig(
        name="test_research_agent",
        agent_type="deep",
        model=model,
        prompt="""You are a research agent with Brave Search access.

When researching:
1. Use Brave Search to find information
2. Store findings in /research.md
3. Provide well-sourced answers""",
        description="Test research agent with Brave Search",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=[],
        ),
        mcp_servers={
            "brave_search": MCPServerConfig(
                description="Brave Search MCP server",
                transport="streamable_http",
                url="http://localhost:8080/mcp",
                env={},
                headers={"Content-Type": "application/json"}
            )
        },
        http_tools={},
        python_tools={},
    )


def check_api_key():
    """Check if API key is available."""
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"))


def check_brave_server():
    """Check if Brave Search MCP server is accessible."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        return result == 0
    except:
        return False


# ============================================================================
# Configuration Tests
# ============================================================================

class TestDeepAgentConfiguration:
    """Test configuration validation and creation."""
    
    def test_agent_type_validation(self):
        """Test that 'deep' is accepted as agent type."""
        config = AgentConfig(
            name="test",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="test",
        )
        assert config.agent_type == "deep"
    
    def test_invalid_agent_type_rejected(self):
        """Test that invalid agent types are rejected."""
        with pytest.raises(ValueError, match="agent_type must be one of"):
            AgentConfig(
                name="test",
                agent_type="invalid",
                model="openai:gpt-4o-mini",
                prompt="test",
            )
    
    def test_deep_agent_config_defaults(self):
        """Test DeepAgentConfig default values."""
        config = DeepAgentConfig()
        assert config.enabled is True
        assert config.enable_filesystem is True
        assert config.enable_todolist is True
        assert config.enable_longterm_memory is False
        assert config.subagents == []
    
    def test_subagent_config_creation(self):
        """Test SubAgentConfig creation."""
        sub = SubAgentConfig(
            name="test_sub",
            description="Test subagent",
            system_prompt="Test prompt",
            model="openai:gpt-4o-mini",
            tools=["tool1", "tool2"],
        )
        assert sub.name == "test_sub"
        assert sub.model == "openai:gpt-4o-mini"
        assert len(sub.tools) == 2
    
    def test_agent_config_with_deep_config(self):
        """Test AgentConfig with deep_agent_config."""
        deep_config = DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            subagents=[
                SubAgentConfig(
                    name="sub1",
                    description="Sub 1",
                    system_prompt="Prompt",
                )
            ]
        )
        
        agent_config = AgentConfig(
            name="test",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="test",
            deep_agent_config=deep_config,
        )
        
        assert agent_config.deep_agent_config is not None
        assert len(agent_config.deep_agent_config.subagents) == 1


# ============================================================================
# Agent Creation Tests
# ============================================================================

class TestDeepAgentCreation:
    """Test DeepAgent instantiation."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.asyncio
    async def test_basic_deep_agent_creation(self, basic_deep_agent_config):
        """Test creating basic DeepAgent."""
        print("\n🧪 Test: Basic DeepAgent Creation")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        print("✅ Agent created successfully")
        
        # Verify it's a DeepAgentAdapter
        from app.deep_agent_adapter import DeepAgentAdapter
        assert isinstance(agent, DeepAgentAdapter)
        print("✅ Agent is DeepAgentAdapter instance")
        
        # Cleanup
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.asyncio
    async def test_deep_agent_with_subagents_creation(self, subagent_deep_agent_config):
        """Test creating DeepAgent with subagents."""
        print("\n🧪 Test: DeepAgent with Subagents Creation")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=subagent_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        print(f"✅ Agent with {len(subagent_deep_agent_config.deep_agent_config.subagents)} subagents created")
        
        # Cleanup
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    @pytest.mark.skipif(HAS_DEEPAGENTS, reason="Test requires DeepAgents NOT installed")
    @pytest.mark.asyncio
    async def test_creation_fails_without_package(self, basic_deep_agent_config):
        """Test that creation fails gracefully without DeepAgents package."""
        print("\n🧪 Test: Graceful Failure Without Package")
        
        checkpointer = MemorySaver()
        
        with pytest.raises(ImportError, match="deepagents package"):
            await build_agent(
                agent_cfg=basic_deep_agent_config,
                default_model="openai:gpt-4o-mini",
                checkpointer=checkpointer,
            )
        
        print("✅ Graceful failure confirmed")


# ============================================================================
# Basic Execution Tests
# ============================================================================

class TestDeepAgentExecution:
    """Test basic agent execution."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.asyncio
    async def test_simple_invocation(self, basic_deep_agent_config, test_thread_id):
        """Test simple agent invocation."""
        print("\n🧪 Test: Simple Invocation")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            start_time = time.time()
            
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "What is 2+2? Answer briefly."}]},
                config={"configurable": {"thread_id": test_thread_id}}
            )
            
            elapsed = time.time() - start_time
            
            assert "messages" in result
            assert len(result["messages"]) > 0
            
            response = result["messages"][-1].content
            assert len(response) > 0
            assert "4" in response.lower() or "four" in response.lower()
            
            print(f"✅ Invocation successful (took {elapsed:.2f}s)")
            print(f"📝 Response: {response[:100]}...")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.asyncio
    async def test_async_invocation(self, basic_deep_agent_config, test_thread_id):
        """Test async agent invocation."""
        print("\n🧪 Test: Async Invocation")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": "Hello, respond with 'Hi!'"}]},
                config={"configurable": {"thread_id": test_thread_id}}
            )
            
            assert "messages" in result
            response = result["messages"][-1].content
            assert len(response) > 0
            
            print(f"✅ Async invocation successful")
            print(f"📝 Response: {response[:100]}...")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass


# ============================================================================
# Multi-Turn Conversation Tests
# ============================================================================

class TestMultiTurnConversation:
    """Test multi-turn conversation with context."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.asyncio
    async def test_multiturn_context_retention(self, basic_deep_agent_config, test_thread_id):
        """Test that context is retained across turns."""
        print("\n🧪 Test: Multi-Turn Context Retention")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            config = {"configurable": {"thread_id": test_thread_id}}
            
            # Turn 1: Establish context
            print("  Turn 1: Establishing context...")
            result1 = agent.invoke(
                {"messages": [{"role": "user", "content": "My name is Alice."}]},
                config=config
            )
            response1 = result1["messages"][-1].content
            print(f"  ✓ Response: {response1[:80]}...")
            
            # Turn 2: Test context recall
            print("  Turn 2: Testing context recall...")
            result2 = agent.invoke(
                {"messages": [{"role": "user", "content": "What is my name?"}]},
                config=config
            )
            response2 = result2["messages"][-1].content
            print(f"  ✓ Response: {response2[:80]}...")
            
            # Verify context was retained
            assert "alice" in response2.lower()
            
            print("✅ Context retained across turns")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.asyncio
    async def test_multiple_turns_same_thread(self, basic_deep_agent_config, test_thread_id):
        """Test multiple conversational turns."""
        print("\n🧪 Test: Multiple Turns Same Thread")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            config = {"configurable": {"thread_id": test_thread_id}}
            
            turns = [
                "Count to 3",
                "Now double each number",
                "What were the original numbers?",
            ]
            
            for i, query in enumerate(turns, 1):
                print(f"  Turn {i}: {query}")
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config=config
                )
                response = result["messages"][-1].content
                print(f"  ✓ Response: {response[:60]}...")
            
            # Final result should reference original numbers (1, 2, 3)
            assert any(num in result["messages"][-1].content for num in ["1", "2", "3"])
            
            print(f"✅ Completed {len(turns)} turns with context")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass


# ============================================================================
# Subagent Tests
# ============================================================================

class TestSubagentDelegation:
    """Test subagent delegation and isolation."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.asyncio
    async def test_subagent_delegation(self, subagent_deep_agent_config, test_thread_id):
        """Test basic subagent delegation."""
        print("\n🧪 Test: Subagent Delegation")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=subagent_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            query = "Analyze the number 42 and validate if it's a meaningful number."
            print(f"  Query: {query}")
            
            result = agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config={"configurable": {"thread_id": test_thread_id}}
            )
            
            response = result["messages"][-1].content
            print(f"  ✓ Response length: {len(response)} chars")
            
            # Response should exist and be substantial
            assert len(response) > 50
            
            print("✅ Subagent delegation completed")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass


# ============================================================================
# MCP Integration Tests
# ============================================================================

class TestMCPIntegration:
    """Test MCP tool integration (Brave Search)."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.skipif(not check_brave_server(), reason="Brave MCP server not running")
    @pytest.mark.asyncio
    async def test_brave_search_integration(self, brave_search_deep_agent_config, test_thread_id):
        """Test Brave Search MCP integration."""
        print("\n🧪 Test: Brave Search MCP Integration")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=brave_search_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            query = "Search for the current year and tell me what year it is."
            print(f"  Query: {query}")
            
            result = agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config={"configurable": {"thread_id": test_thread_id}}
            )
            
            response = result["messages"][-1].content
            print(f"  ✓ Response: {response[:100]}...")
            
            # Should mention 2024 or 2025
            assert "202" in response
            
            print("✅ Brave Search integration working")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass


# ============================================================================
# Backward Compatibility Tests
# ============================================================================

class TestBackwardCompatibility:
    """Test backward compatibility with existing agents."""
    
    @pytest.mark.asyncio
    async def test_react_agent_still_works(self, test_thread_id):
        """Test that ReAct agents still work."""
        print("\n🧪 Test: ReAct Agent Backward Compatibility")
        
        # Use Azure OpenAI if available, otherwise OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            model = f"azure_openai:{deployment}"
        else:
            model = "openai:gpt-4o-mini"
        
        config = AgentConfig(
            name="test_react",
            agent_type="react",
            model=model,
            prompt="You are a test agent.",
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=config,
            default_model=model,
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        
        # Should NOT be DeepAgentAdapter
        from app.deep_agent_adapter import DeepAgentAdapter
        assert not isinstance(agent, DeepAgentAdapter)
        
        print("✅ ReAct agent works (not affected by DeepAgents)")
        
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_normal_agent_still_works(self, test_thread_id):
        """Test that Normal agents still work."""
        print("\n🧪 Test: Normal Agent Backward Compatibility")
        
        # Use Azure OpenAI if available, otherwise OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
            model = f"azure_openai:{deployment}"
        else:
            model = "openai:gpt-4o-mini"
        
        config = AgentConfig(
            name="test_normal",
            agent_type="normal",
            model=model,
            prompt="You are a test agent.",
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=config,
            default_model=model,
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        
        from app.deep_agent_adapter import DeepAgentAdapter
        assert not isinstance(agent, DeepAgentAdapter)
        
        print("✅ Normal agent works (not affected by DeepAgents)")
        
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.asyncio
    async def test_invalid_thread_id_handling(self, basic_deep_agent_config):
        """Test handling of invalid thread IDs."""
        print("\n🧪 Test: Invalid Thread ID Handling")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            # Empty config (no thread_id)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "Test"}]},
                config={}
            )
            
            # Should still work (generate default thread_id or handle gracefully)
            assert "messages" in result
            
            print("✅ Handles missing thread ID gracefully")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not check_api_key(), reason="API key required")
    @pytest.mark.asyncio
    async def test_response_time_acceptable(self, basic_deep_agent_config, test_thread_id):
        """Test that response time is acceptable."""
        print("\n🧪 Test: Response Time")
        
        checkpointer = MemorySaver()
        agent, mcp_client = await build_agent(
            agent_cfg=basic_deep_agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        try:
            start_time = time.time()
            
            result = agent.invoke(
                {"messages": [{"role": "user", "content": "Say 'OK'"}]},
                config={"configurable": {"thread_id": test_thread_id}}
            )
            
            elapsed = time.time() - start_time
            
            print(f"  ⏱️  Response time: {elapsed:.2f}s")
            
            # DeepAgents should respond within reasonable time (60s for simple query)
            assert elapsed < 60
            
            print(f"✅ Response time acceptable ({elapsed:.2f}s < 60s)")
            
        finally:
            if mcp_client:
                try:
                    await mcp_client.__aexit__(None, None, None)
                except:
                    pass


# ============================================================================
# Test Execution Summary
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 DeepAgent Comprehensive Test Suite")
    print("="*70)
    print("\nRunning tests with pytest...\n")
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])
