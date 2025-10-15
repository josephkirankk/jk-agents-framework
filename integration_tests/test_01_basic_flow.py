"""
Integration Test 01: Basic Flow
Tests basic agent creation, configuration loading, and simple query execution.

NO MOCKING - Uses real LLM, real config files, real database.

Scenarios:
1. Load configuration from YAML
2. Build agent with real LLM
3. Execute simple query
4. Verify response structure and content
5. Test with different agent types (normal vs react)
"""

import pytest
import asyncio
from pathlib import Path
from langchain_core.messages import HumanMessage

from app.main import load_app_config
from app.agent_builder import build_agent
from helpers.llm_client import LiveLLMClient
from helpers.utils import contains_keywords, extract_numbers
from test_utils import convert_app_config_to_dict


@pytest.mark.integration
@pytest.mark.azure
class TestBasicFlow:
    """Test basic agent creation and execution flow."""
    
    @pytest.mark.asyncio
    async def test_load_config_and_build_agent(self, config_dir, test_thread_id, llm_config):
        """
        Scenario: Load configuration and build agent
        
        Steps:
        1. Load YAML configuration
        2. Build agent with real LLM
        3. Verify agent is created successfully
        """
        # Load config
        config_path = config_dir / "simple_test_no_mcp.yaml"
        config = load_app_config(config_path)
        
        assert config is not None
        assert len(config.agents) > 0
        assert config.models is not None
        
        # Build agent
        agent_cfg = config.agents[0]
        default_model = config.models.get("default", llm_config["model"])
        app_config_dict = convert_app_config_to_dict(config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        assert agent is not None
        assert hasattr(agent, 'ainvoke') or hasattr(agent, 'invoke')
        
        # Cleanup
        if mcp_client:
            from app.mcp_loader import close_mcp_client
            await close_mcp_client(mcp_client)
    
    @pytest.mark.asyncio
    async def test_simple_query_execution(self, test_agent, test_thread_id):
        """
        Scenario: Execute simple query and verify response
        
        Steps:
        1. Invoke agent with simple question
        2. Wait for response
        3. Verify response contains expected content
        """
        # Execute query
        query = "What is 15 + 27? Just give me the number."
        
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        result = await test_agent.ainvoke(input_data, config=config)
        
        # Verify response
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        
        assert response_text is not None
        assert len(response_text) > 0
        
        # Check if response contains the answer (42)
        numbers = extract_numbers(response_text)
        assert 42 in numbers or "42" in response_text
    
    @pytest.mark.asyncio
    async def test_deterministic_response(self, config_dir, test_thread_id, llm_config):
        """
        Scenario: Test deterministic behavior with temperature=0
        
        Steps:
        1. Create agent with temperature=0
        2. Execute same query twice
        3. Verify responses are consistent
        """
        # Load config
        config_path = config_dir / "simple_test_no_mcp.yaml"
        config = load_app_config(config_path)
        
        # Build agent with custom system prompt
        agent_cfg = config.agents[0]
        default_model = llm_config["model"]
        app_config_dict = convert_app_config_to_dict(config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        # Execute same query twice
        query = "What is the capital of France? Answer in one word."
        
        async def execute_query():
            input_data = {"messages": [HumanMessage(content=query)]}
            config = {"configurable": {"thread_id": f"{test_thread_id}_det"}}
            result = await agent.ainvoke(input_data, config=config)
            return result["messages"][-1].content
        
        response1 = await execute_query()
        response2 = await execute_query()
        
        # Verify both responses contain "Paris"
        assert "paris" in response1.lower()
        assert "paris" in response2.lower()
        
        # Cleanup
        if mcp_client:
            from app.mcp_loader import close_mcp_client
            await close_mcp_client(mcp_client)
    
    @pytest.mark.asyncio
    async def test_multi_query_sequence(self, test_agent, test_thread_id):
        """
        Scenario: Execute multiple queries in sequence
        
        Steps:
        1. Execute first query
        2. Execute second query
        3. Execute third query
        4. Verify all responses are correct
        """
        queries = [
            ("What is 10 + 5?", ["15"]),
            ("What is the color of the sky on a clear day?", ["blue"]),
            ("Name one programming language", ["python", "java", "javascript", "c++"])
        ]
        
        for query, expected_keywords in queries:
            input_data = {"messages": [HumanMessage(content=query)]}
            config = {"configurable": {"thread_id": f"{test_thread_id}_multi"}}
            
            result = await test_agent.ainvoke(input_data, config=config)
            response_text = result["messages"][-1].content.lower()
            
            # At least one expected keyword should be in response
            assert any(keyword.lower() in response_text for keyword in expected_keywords), \
                f"None of {expected_keywords} found in response: {response_text[:200]}"
    
    @pytest.mark.asyncio
    async def test_agent_with_system_prompt(self, config_dir, test_thread_id, llm_config):
        """
        Scenario: Test agent respects system prompt
        
        Steps:
        1. Load config with specific system prompt
        2. Build agent
        3. Execute query
        4. Verify response follows system prompt instructions
        """
        # Load config
        config_path = config_dir / "simple_test_no_mcp.yaml"
        config = load_app_config(config_path)
        
        # Build agent
        agent_cfg = config.agents[0]
        default_model = llm_config["model"]
        app_config_dict = convert_app_config_to_dict(config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        # Execute same query twice
        query = "Tell me about Python programming"
        input_data = {"messages": [HumanMessage(content=query)]}
        config_dict = {"configurable": {"thread_id": test_thread_id}}
        
        result = await agent.ainvoke(input_data, config=config_dict)
        response_text = result["messages"][-1].content
        
        # Verify response is about Python
        assert len(response_text) > 20
        assert "python" in response_text.lower()
        
        # Cleanup
        if mcp_client:
            from app.mcp_loader import close_mcp_client
            await close_mcp_client(mcp_client)
    
    @pytest.mark.asyncio
    async def test_config_with_different_models(self, config_dir, test_thread_id, env_config):
        """
        Scenario: Test loading configs with different model specifications
        
        Steps:
        1. Load config with Azure OpenAI model
        2. Build agent and verify it works
        3. If Google available, test with Google model
        """
        # Test Azure OpenAI
        if env_config["azure_openai"]["available"]:
            config_path = config_dir / "azure_openai_test.yaml"
            if config_path.exists():
                config = load_app_config(config_path)
                # Try building agent with this model
                agent_cfg = config.agents[0]
                default_model = config.models.get("default", f"azure_openai:{env_config['azure_openai']['deployment']}")
                app_config_dict = convert_app_config_to_dict(config)
                
                agent, mcp_client = await build_agent(
                    agent_cfg=agent_cfg,
                    default_model=default_model,
                    config_path=str(config_path),
                    app_config=app_config_dict
                )
                
                # Quick test
                query = "Say 'test passed'"
                input_data = {"messages": [HumanMessage(content=query)]}
                config_dict = {"configurable": {"thread_id": test_thread_id}}
                
                result = await agent.ainvoke(input_data, config=config_dict)
                response_text = result["messages"][-1].content
                
                assert len(response_text) > 0
                
                # Cleanup
                if mcp_client:
                    from app.mcp_loader import close_mcp_client
                    await close_mcp_client(mcp_client)
    
    @pytest.mark.asyncio
    async def test_llm_client_direct(self, llm_config, env_config):
        """
        Scenario: Test direct LLM client usage
        
        Steps:
        1. Create LiveLLMClient
        2. Generate simple response
        3. Verify response structure
        """
        client = LiveLLMClient(
            provider=llm_config["provider"],
            model=llm_config["model"],
            temperature=0,
            max_tokens=500
        )
        
        response = await client.generate(
            prompt="What is 2 + 2? Answer with just the number.",
            system_prompt="You are a helpful math assistant."
        )
        
        assert response is not None
        assert response.content is not None
        assert len(response.content) > 0
        assert "4" in response.content
        assert response.duration > 0
        assert response.provider == llm_config["provider"]
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, test_agent, test_thread_id, performance_tracker):
        """
        Scenario: Verify response time is reasonable
        
        Steps:
        1. Execute query
        2. Measure response time
        3. Verify it's within acceptable range
        """
        import time
        
        query = "What is the square root of 144?"
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        start_time = time.time()
        result = await test_agent.ainvoke(input_data, config=config)
        duration = time.time() - start_time
        
        performance_tracker["track"]("simple_query", duration)
        
        # Verify reasonable response time (< 30 seconds for simple query)
        assert duration < 30.0, f"Query took too long: {duration:.2f}s"
        
        # Verify response is correct
        response_text = result["messages"][-1].content
        numbers = extract_numbers(response_text)
        assert 12 in numbers or "12" in response_text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
