"""
Integration tests for DeepAgents integration.

Tests cover:
1. Configuration validation
2. Basic DeepAgent creation
3. DeepAgent with subagents
4. Filesystem operations
5. Compatibility with existing framework components
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
from app.agent_builder import build_agent, HAS_DEEPAGENTS
from app.checkpointer_manager import get_global_checkpointer


class TestDeepAgentConfiguration:
    """Test configuration validation for DeepAgents."""
    
    def test_agent_type_validation(self):
        """Test that 'deep' is a valid agent type."""
        config = AgentConfig(
            name="test_agent",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="Test prompt",
        )
        assert config.agent_type == "deep"
    
    def test_deep_agent_config_optional(self):
        """Test that deep_agent_config is optional."""
        config = AgentConfig(
            name="test_agent",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="Test prompt",
            deep_agent_config=None,
        )
        assert config.deep_agent_config is None
    
    def test_deep_agent_config_with_defaults(self):
        """Test DeepAgentConfig with default values."""
        deep_config = DeepAgentConfig()
        assert deep_config.enabled is True
        assert deep_config.enable_filesystem is True
        assert deep_config.enable_todolist is True
        assert deep_config.enable_longterm_memory is False
        assert deep_config.subagents == []
    
    def test_subagent_config(self):
        """Test SubAgentConfig validation."""
        sub_config = SubAgentConfig(
            name="researcher",
            description="Research specialist",
            system_prompt="You are a researcher",
            model="openai:gpt-4o-mini",
            tools=["search"],
        )
        assert sub_config.name == "researcher"
        assert sub_config.model == "openai:gpt-4o-mini"
        assert "search" in sub_config.tools


class TestDeepAgentCreation:
    """Test DeepAgent instance creation."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.asyncio
    async def test_basic_deep_agent_creation(self):
        """Test creating a basic DeepAgent without subagents."""
        config = AgentConfig(
            name="test_deep_agent",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="You are a test agent.",
            deep_agent_config=DeepAgentConfig(
                enabled=True,
                enable_filesystem=True,
                enable_todolist=True,
                subagents=[],
            ),
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = get_global_checkpointer()
        agent, mcp_client = await build_agent(
            agent_cfg=config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        # Verify it's a DeepAgentAdapter
        from app.deep_agent_adapter import DeepAgentAdapter
        assert isinstance(agent, DeepAgentAdapter)
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.asyncio
    async def test_deep_agent_with_subagents(self):
        """Test creating a DeepAgent with subagents."""
        subagents = [
            SubAgentConfig(
                name="sub1",
                description="Subagent 1",
                system_prompt="You are subagent 1",
                tools=[],
            ),
            SubAgentConfig(
                name="sub2",
                description="Subagent 2",
                system_prompt="You are subagent 2",
                tools=[],
            ),
        ]
        
        config = AgentConfig(
            name="test_deep_agent_with_subs",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="You are a test orchestrator.",
            deep_agent_config=DeepAgentConfig(
                enabled=True,
                enable_filesystem=True,
                enable_todolist=True,
                subagents=subagents,
            ),
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = get_global_checkpointer()
        agent, mcp_client = await build_agent(
            agent_cfg=config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        from app.deep_agent_adapter import DeepAgentAdapter
        assert isinstance(agent, DeepAgentAdapter)
    
    @pytest.mark.skipif(HAS_DEEPAGENTS, reason="Test requires DeepAgents NOT installed")
    @pytest.mark.asyncio
    async def test_deep_agent_without_package_fails(self):
        """Test that creating DeepAgent without package raises ImportError."""
        config = AgentConfig(
            name="test_deep_agent_no_pkg",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="Test",
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = get_global_checkpointer()
        
        with pytest.raises(ImportError, match="deepagents package"):
            await build_agent(
                agent_cfg=config,
                default_model="openai:gpt-4o-mini",
                checkpointer=checkpointer,
            )


class TestDeepAgentExecution:
    """Test DeepAgent execution and behavior."""
    
    @pytest.mark.skipif(not HAS_DEEPAGENTS, reason="DeepAgents not installed")
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key required")
    @pytest.mark.asyncio
    async def test_deep_agent_invoke(self):
        """Test invoking a DeepAgent with a simple query."""
        config = AgentConfig(
            name="test_invoke_agent",
            agent_type="deep",
            model="openai:gpt-4o-mini",
            prompt="You are a helpful assistant. Answer questions concisely.",
            deep_agent_config=DeepAgentConfig(
                enabled=True,
                enable_filesystem=True,
                enable_todolist=False,  # Disable for simple test
                subagents=[],
            ),
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = get_global_checkpointer()
        agent, _ = await build_agent(
            agent_cfg=config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        # Simple invocation
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "What is 2+2?"}]},
            config={"configurable": {"thread_id": "test_thread"}}
        )
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        # Should contain answer about 4
        response_text = result["messages"][-1].content.lower()
        assert "4" in response_text or "four" in response_text


class TestBackwardCompatibility:
    """Test that existing agent types still work."""
    
    @pytest.mark.asyncio
    async def test_react_agent_still_works(self):
        """Ensure ReAct agents work after DeepAgents integration."""
        config = AgentConfig(
            name="test_react_agent",
            agent_type="react",
            model="openai:gpt-4o-mini",
            prompt="You are a test agent.",
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = get_global_checkpointer()
        agent, _ = await build_agent(
            agent_cfg=config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        # Should NOT be a DeepAgentAdapter
        from app.deep_agent_adapter import DeepAgentAdapter
        assert not isinstance(agent, DeepAgentAdapter)
    
    @pytest.mark.asyncio
    async def test_normal_agent_still_works(self):
        """Ensure normal agents work after DeepAgents integration."""
        config = AgentConfig(
            name="test_normal_agent",
            agent_type="normal",
            model="openai:gpt-4o-mini",
            prompt="You are a test agent.",
            mcp_servers={},
            http_tools={},
            python_tools={},
        )
        
        checkpointer = get_global_checkpointer()
        agent, _ = await build_agent(
            agent_cfg=config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        assert agent is not None
        from app.deep_agent_adapter import DeepAgentAdapter
        assert not isinstance(agent, DeepAgentAdapter)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
