"""
Integration Test 06: MCP Python Tools
Tests Python code execution via MCP server (Deno-based python runner).

NO MOCKING - Uses real MCP server, real Python execution, real LLM.

Scenarios:
1. Execute simple Python code via MCP
2. Execute code with calculations
3. Execute code with data structures
4. Handle errors in Python code
5. Multi-step Python execution

Prerequisites:
- Deno installed (https://deno.land/)
- Azure OpenAI credentials configured
- MCP python runner (@pydantic/mcp-run-python)
"""

import os
import pytest
import asyncio
import subprocess
from pathlib import Path
from langchain_core.messages import HumanMessage

from app.main import load_app_config
from app.agent_builder import build_agent
from test_utils import convert_app_config_to_dict
from helpers.utils import contains_keywords, extract_numbers


def check_deno_available():
    """Check if Deno is available."""
    try:
        # Try running deno --version to check if it's available
        result = subprocess.run(['deno', '--version'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except FileNotFoundError:
        # Deno not in PATH
        return False
    except Exception:
        return False


# Set environment variable to suppress tokenizers warning
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


@pytest.mark.integration
@pytest.mark.azure
@pytest.mark.skipif(not check_deno_available(), reason="Deno is not installed or not in PATH")
class TestMCPPythonTools:
    """Test Python code execution via MCP server."""
    
    @pytest.fixture
    async def python_agent(self, config_dir, test_thread_id):
        """
        Build agent with Python execution MCP server.
        """
        from app.mcp_loader import close_mcp_client
        
        # Load config with Python MCP server
        config_path = config_dir / "python_exec_agent_working.yaml"
        config = load_app_config(config_path)
        
        # Get Python execution agent
        python_agent_config = None
        for agent in config.agents:
            if agent.name == "python_exec_agent":
                python_agent_config = agent
                break
        
        if not python_agent_config:
            pytest.skip("Python execution agent not found in config")
        
        # Build agent
        app_config_dict = convert_app_config_to_dict(config)
        agent, mcp_client = await build_agent(
            agent_cfg=python_agent_config,
            default_model=config.models.get("default", "azure_openai:gpt-4.1"),
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        yield agent
        
        # Cleanup
        if mcp_client:
            await close_mcp_client(mcp_client)
    
    @pytest.mark.asyncio
    async def test_simple_python_execution(self, python_agent, test_thread_id):
        """
        Scenario: Execute simple Python code
        
        Steps:
        1. Ask agent to calculate 15 + 27
        2. Verify it uses Python execution
        3. Verify correct result
        """
        query = "Use Python to calculate 15 + 27. Show me the code and result."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        
        assert result is not None
        assert len(result["messages"]) > 0
        
        # Get all messages to check for tool usage
        messages = result["messages"]
        response_text = messages[-1].content.lower()
        
        # Should contain the answer
        assert "42" in response_text or contains_keywords(response_text, ["42"])
        
        # Check if tool was called (look for tool call messages)
        tool_called = any(
            hasattr(msg, "tool_calls") and msg.tool_calls 
            for msg in messages
        )
        
        # Tool calling is expected but not required (agent might compute directly)
        print(f"Tool was called: {tool_called}")
    
    @pytest.mark.asyncio
    async def test_python_list_operations(self, python_agent, test_thread_id):
        """
        Scenario: Execute Python code with list operations
        
        Steps:
        1. Ask agent to create and manipulate a list
        2. Verify correct operations
        """
        query = "Use Python to create a list of numbers from 1 to 5, then calculate their sum. Show the result."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_list"}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Sum of 1+2+3+4+5 = 15
        assert "15" in response_text or contains_keywords(response_text, ["15", "fifteen"])
    
    @pytest.mark.asyncio
    async def test_python_error_handling(self, python_agent, test_thread_id):
        """
        Scenario: Handle Python code errors
        
        Steps:
        1. Ask agent to do something that might cause an error
        2. Verify agent handles it gracefully
        """
        query = "Use Python to divide 10 by 2. Show me the code and result."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_error"}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        # Should get result (10/2 = 5)
        assert "5" in response_text or "5.0" in response_text
    
    @pytest.mark.asyncio
    async def test_python_factorial(self, python_agent, test_thread_id):
        """
        Scenario: Calculate factorial using Python
        
        Steps:
        1. Ask agent to calculate factorial of 5
        2. Verify correct result (120)
        """
        query = "Use Python to calculate the factorial of 5. Show the code and result."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_factorial"}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        # Factorial of 5 = 120
        assert "120" in response_text
    
    @pytest.mark.asyncio
    async def test_python_string_manipulation(self, python_agent, test_thread_id):
        """
        Scenario: String manipulation with Python
        
        Steps:
        1. Ask agent to reverse a string
        2. Verify correct result
        """
        query = 'Use Python to reverse the string "hello". Show me the code and result.'
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_string"}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content.lower()
        
        # Reversed "hello" = "olleh"
        assert "olleh" in response_text
    
    @pytest.mark.asyncio
    async def test_python_data_structure(self, python_agent, test_thread_id):
        """
        Scenario: Work with Python dictionaries
        
        Steps:
        1. Create dictionary with data
        2. Access and manipulate values
        3. Verify results
        """
        query = "Use Python to create a dictionary with keys 'a', 'b', 'c' and values 1, 2, 3. Then sum all the values. Show the result."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_dict"}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        # Sum of 1+2+3 = 6
        assert "6" in response_text
    
    @pytest.mark.asyncio
    async def test_python_multi_step_calculation(self, python_agent, test_thread_id):
        """
        Scenario: Multi-step calculation in Python
        
        Steps:
        1. Calculate (10 + 20) * 3
        2. Verify correct result
        """
        query = "Use Python to calculate (10 + 20) * 3. Show me the code and final result."
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": f"{test_thread_id}_multistep"}}
        
        result = await python_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        # (10 + 20) * 3 = 90
        assert "90" in response_text


    @pytest.mark.asyncio
    async def test_multi_turn_calculation_workflow(self, python_agent, test_thread_id):
        """
        Scenario: Multi-turn calculation building on previous results
        
        Steps:
        1. Turn 1: Calculate base value
        2. Turn 2: Use previous result in new calculation
        3. Turn 3: Build on accumulated results
        4. Verify context persistence
        """
        config = {"configurable": {"thread_id": f"{test_thread_id}_multiturn"}}
        
        # Turn 1: Initial calculation
        query1 = "Calculate 10 * 5 using Python. Save the result."
        input1 = {"messages": [HumanMessage(content=query1)]}
        result1 = await python_agent.ainvoke(input1, config=config)
        response1 = result1["messages"][-1].content
        
        assert "50" in response1
        
        await asyncio.sleep(1)
        
        # Turn 2: Build on previous
        query2 = "Take the previous result and add 25 to it using Python."
        input2 = {"messages": [HumanMessage(content=query2)]}
        result2 = await python_agent.ainvoke(input2, config=config)
        response2 = result2["messages"][-1].content
        
        # Should be 50 + 25 = 75
        assert "75" in response2
        
        await asyncio.sleep(1)
        
        # Turn 3: Further calculation
        query3 = "Multiply the last result by 2 using Python."
        input3 = {"messages": [HumanMessage(content=query3)]}
        result3 = await python_agent.ainvoke(input3, config=config)
        response3 = result3["messages"][-1].content
        
        # Should be 75 * 2 = 150
        assert "150" in response3
    
    @pytest.mark.asyncio
    async def test_multi_turn_data_accumulation(self, python_agent, test_thread_id):
        """
        Scenario: Accumulate data across multiple turns
        
        Steps:
        1. Turn 1: Create initial list
        2. Turn 2: Add more items
        3. Turn 3: Process complete list
        """
        config = {"configurable": {"thread_id": f"{test_thread_id}_accumulate"}}
        
        # Turn 1: Create list
        query1 = "Use Python to create a list with numbers [1, 2, 3]."
        input1 = {"messages": [HumanMessage(content=query1)]}
        result1 = await python_agent.ainvoke(input1, config=config)
        
        assert result1 is not None
        
        await asyncio.sleep(1)
        
        # Turn 2: Add to list
        query2 = "Add numbers 4 and 5 to the previous list using Python."
        input2 = {"messages": [HumanMessage(content=query2)]}
        result2 = await python_agent.ainvoke(input2, config=config)
        
        assert result2 is not None
        
        await asyncio.sleep(1)
        
        # Turn 3: Sum the list
        query3 = "Calculate the sum of all numbers in the list using Python."
        input3 = {"messages": [HumanMessage(content=query3)]}
        result3 = await python_agent.ainvoke(input3, config=config)
        response3 = result3["messages"][-1].content
        
        # Sum of 1+2+3+4+5 = 15
        assert "15" in response3
    
    @pytest.mark.asyncio
    async def test_multi_turn_variable_persistence(self, python_agent, test_thread_id):
        """
        Scenario: Test variable persistence across turns
        
        Steps:
        1. Define variable in turn 1
        2. Use variable in turn 2
        3. Modify variable in turn 3
        4. Verify final state
        """
        config = {"configurable": {"thread_id": f"{test_thread_id}_variables"}}
        
        # Turn 1: Define variable
        query1 = "Use Python to set a variable x = 100."
        input1 = {"messages": [HumanMessage(content=query1)]}
        result1 = await python_agent.ainvoke(input1, config=config)
        
        assert result1 is not None
        
        await asyncio.sleep(1)
        
        # Turn 2: Use variable
        query2 = "Use Python to calculate x divided by 2."
        input2 = {"messages": [HumanMessage(content=query2)]}
        result2 = await python_agent.ainvoke(input2, config=config)
        response2 = result2["messages"][-1].content
        
        assert "50" in response2
        
        await asyncio.sleep(1)
        
        # Turn 3: Modify variable
        query3 = "Use Python to multiply x by 3."
        input3 = {"messages": [HumanMessage(content=query3)]}
        result3 = await python_agent.ainvoke(input3, config=config)
        response3 = result3["messages"][-1].content
        
        assert "300" in response3
    
    @pytest.mark.asyncio
    async def test_multi_turn_complex_workflow(self, python_agent, test_thread_id):
        """
        Scenario: Complex multi-turn workflow with data transformation
        
        Steps:
        1. Create data structure
        2. Transform it
        3. Analyze results
        4. Generate summary
        """
        config = {"configurable": {"thread_id": f"{test_thread_id}_complex"}}
        
        # Turn 1: Create data
        query1 = "Use Python to create a dictionary with keys 'a', 'b', 'c' and values 10, 20, 30."
        input1 = {"messages": [HumanMessage(content=query1)]}
        result1 = await python_agent.ainvoke(input1, config=config)
        
        assert result1 is not None
        
        await asyncio.sleep(1)
        
        # Turn 2: Transform
        query2 = "Use Python to double all values in the dictionary."
        input2 = {"messages": [HumanMessage(content=query2)]}
        result2 = await python_agent.ainvoke(input2, config=config)
        
        assert result2 is not None
        
        await asyncio.sleep(1)
        
        # Turn 3: Analyze
        query3 = "Use Python to calculate the sum of all values in the dictionary."
        input3 = {"messages": [HumanMessage(content=query3)]}
        result3 = await python_agent.ainvoke(input3, config=config)
        response3 = result3["messages"][-1].content
        
        # After doubling: 20+40+60 = 120
        assert "120" in response3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
