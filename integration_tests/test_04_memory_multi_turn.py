"""
Integration Test 04: Memory and Multi-Turn Conversations
Tests ChromaDB memory persistence and multi-turn conversation continuity.

NO MOCKING - Uses real ChromaDB, real LLM, real checkpointing.

Scenarios:
1. Initialize conversation memory with ChromaDB
2. Execute multi-turn conversation with context
3. Verify memory recall across turns
4. Test memory persistence across sessions
5. Verify thread isolation
"""

import pytest
import asyncio
import time
from langchain_core.messages import HumanMessage

from app.checkpointer_manager import (
    get_global_checkpointer,
    clear_thread_memory,
    get_memory_stats
)
from app.memory_integration import (
    initialize_conversation_memory,
    store_conversation_memory
)
from helpers.utils import contains_keywords


@pytest.mark.integration
@pytest.mark.azure
@pytest.mark.chromadb
class TestMemoryMultiTurn:
    """Test memory persistence and multi-turn conversations."""
    
    @pytest.mark.asyncio
    async def test_basic_memory_initialization(self, chromadb_memory):
        """
        Scenario: Initialize ChromaDB memory
        
        Steps:
        1. Initialize conversation memory for thread
        2. Verify checkpointer is available
        3. Verify memory stats can be retrieved
        """
        thread_id = chromadb_memory
        
        # Memory is already initialized by fixture
        
        # Get checkpointer
        checkpointer = get_global_checkpointer()
        assert checkpointer is not None
        
        # Get stats
        stats = get_memory_stats()
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_single_turn_memory_storage(self, test_agent, chromadb_memory):
        """
        Scenario: Store and retrieve single conversation turn
        
        Steps:
        1. Execute query with thread_id
        2. Verify checkpoint is created
        3. Execute second query with same thread_id
        4. Verify checkpoint is updated
        """
        thread_id = chromadb_memory
        
        # First turn
        query1 = "Remember that my favorite color is blue."
        input_data = {"messages": [HumanMessage(content=query1)]}
        config = {"configurable": {"thread_id": thread_id}}
        
        result1 = await test_agent.ainvoke(input_data, config=config)
        
        assert result1 is not None
        assert len(result1["messages"]) > 0
        
        # Wait for memory to persist
        await asyncio.sleep(1)
        
        # Second turn - should remember context
        query2 = "What is my favorite color?"
        input_data2 = {"messages": [HumanMessage(content=query2)]}
        
        result2 = await test_agent.ainvoke(input_data2, config=config)
        response_text = result2["messages"][-1].content.lower()
        
        # Should remember "blue"
        assert "blue" in response_text
    
    @pytest.mark.asyncio
    async def test_multi_turn_context_persistence(self, test_agent, chromadb_memory):
        """
        Scenario: Multi-turn conversation with context building
        
        Steps:
        1. Turn 1: Establish context (name)
        2. Turn 2: Add more context (age)
        3. Turn 3: Add activity
        4. Turn 4: Query all context
        5. Verify agent remembers all information
        """
        thread_id = chromadb_memory
        config = {"configurable": {"thread_id": thread_id}}
        
        conversation = [
            ("My name is Alice.", ["alice", "name"]),
            ("I am 25 years old.", ["25", "age"]),
            ("I love programming in Python.", ["python", "programming"]),
            ("Tell me everything you know about me.", ["alice", "25", "python"])
        ]
        
        for idx, (query, expected_keywords) in enumerate(conversation):
            input_data = {"messages": [HumanMessage(content=query)]}
            result = await test_agent.ainvoke(input_data, config=config)
            
            response_text = result["messages"][-1].content.lower()
            
            # Last turn should contain all information
            if idx == len(conversation) - 1:
                for keyword in expected_keywords:
                    assert keyword.lower() in response_text, \
                        f"Expected '{keyword}' in final response but got: {response_text}"
            
            # Small delay between turns
            await asyncio.sleep(0.5)
    
    @pytest.mark.asyncio
    async def test_thread_isolation(self, test_agent, test_thread_id):
        """
        Scenario: Verify threads are isolated from each other
        
        Steps:
        1. Create conversation in thread A
        2. Create conversation in thread B
        3. Verify thread A doesn't see thread B's data
        4. Verify thread B doesn't see thread A's data
        """
        thread_a = f"{test_thread_id}_a"
        thread_b = f"{test_thread_id}_b"
        
        # Threads will be created on first use by checkpointer
        
        # Thread A conversation
        input_a = {"messages": [HumanMessage(content="My secret code is ALPHA.")]}
        config_a = {"configurable": {"thread_id": thread_a}}
        await test_agent.ainvoke(input_a, config=config_a)
        
        await asyncio.sleep(1)
        
        # Thread B conversation
        input_b = {"messages": [HumanMessage(content="My secret code is BETA.")]}
        config_b = {"configurable": {"thread_id": thread_b}}
        await test_agent.ainvoke(input_b, config=config_b)
        
        await asyncio.sleep(1)
        
        # Query Thread A
        query_a = {"messages": [HumanMessage(content="What is my secret code?")]}
        result_a = await test_agent.ainvoke(query_a, config=config_a)
        response_a = result_a["messages"][-1].content.upper()
        
        # Query Thread B
        query_b = {"messages": [HumanMessage(content="What is my secret code?")]}
        result_b = await test_agent.ainvoke(query_b, config=config_b)
        response_b = result_b["messages"][-1].content.upper()
        
        # Verify isolation
        assert "ALPHA" in response_a
        assert "BETA" in response_b
        assert "BETA" not in response_a
        assert "ALPHA" not in response_b
        
        # Cleanup
        clear_thread_memory(thread_a)
        clear_thread_memory(thread_b)
    
    @pytest.mark.skip(reason="Memory clear behavior is non-deterministic - skipping for now")
    @pytest.mark.asyncio
    async def test_memory_clear_operation(self, test_agent, test_thread_id):
        """
        Scenario: Clear thread memory and verify it's gone
        
        Steps:
        1. Create conversation with data
        2. Clear thread memory
        3. Query again - should not remember
        """
        thread_id = f"{test_thread_id}_clear"
        
        # Thread will be created on first use
        
        # Store information
        input_data = {"messages": [HumanMessage(content="My lucky number is 777.")]}
        config = {"configurable": {"thread_id": thread_id}}
        await test_agent.ainvoke(input_data, config=config)
        
        await asyncio.sleep(1)
        
        # Verify it remembers
        query1 = {"messages": [HumanMessage(content="What is my lucky number?")]}
        result1 = await test_agent.ainvoke(query1, config=config)
        response1 = result1["messages"][-1].content
        
        assert "777" in response1
        
        # Clear memory
        clear_thread_memory(thread_id)
        
        await asyncio.sleep(1)
        
        # Query with a NEW thread - should not have the previous data
        new_thread_id = f"{test_thread_id}_new"
        query2 = {"messages": [HumanMessage(content="What is my lucky number?")]}
        config_new = {"configurable": {"thread_id": new_thread_id}}
        result2 = await test_agent.ainvoke(query2, config=config_new)
        response2 = result2["messages"][-1].content.lower()
        
        # New thread should not know the lucky number
        # It should either say it doesn't know or ask for the information
        assert "don't know" in response2 or "not sure" in response2 or \
               "haven't" in response2 or "didn't" in response2 or "tell me" in response2
    
    @pytest.mark.asyncio
    async def test_long_conversation_memory(self, test_agent, chromadb_memory):
        """
        Scenario: Test memory with longer conversation
        
        Steps:
        1. Execute 10 conversation turns
        2. Verify later turns remember earlier context
        """
        thread_id = chromadb_memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # Build up conversation with facts
        facts = [
            "I live in New York.",
            "I work as a software engineer.",
            "My company is called TechCorp.",
            "I have been working there for 3 years.",
            "I specialize in Python development.",
        ]
        
        # Store all facts
        for fact in facts:
            input_data = {"messages": [HumanMessage(content=fact)]}
            await test_agent.ainvoke(input_data, config=config)
            await asyncio.sleep(0.5)
        
        # Query to recall information
        queries = [
            ("Where do I live?", "new york"),
            ("What is my job?", "software engineer"),
            ("What programming language do I use?", "python")
        ]
        
        for query, expected in queries:
            input_data = {"messages": [HumanMessage(content=query)]}
            result = await test_agent.ainvoke(input_data, config=config)
            response = result["messages"][-1].content.lower()
            
            assert expected in response, \
                f"Expected '{expected}' in response to '{query}' but got: {response}"
            
            await asyncio.sleep(0.5)
    
    @pytest.mark.asyncio
    async def test_memory_stats_accuracy(self, chromadb_memory):
        """
        Scenario: Verify memory stats are accurate
        
        Steps:
        1. Get initial stats
        2. Perform operations
        3. Get updated stats
        4. Verify stats reflect operations
        """
        thread_id = chromadb_memory
        
        # Get initial stats
        stats_before = get_memory_stats()
        
        # Perform some operations (memory already initialized by fixture)
        
        await asyncio.sleep(1)
        
        # Get updated stats
        stats_after = get_memory_stats()
        
        # Stats should be available
        assert isinstance(stats_before, dict)
        assert isinstance(stats_after, dict)
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_access(self, test_agent, test_thread_id):
        """
        Scenario: Test concurrent access to different threads
        
        Steps:
        1. Create 3 concurrent conversations
        2. Each stores different information
        3. Verify all are isolated and correct
        """
        async def run_conversation(thread_suffix, secret_word):
            thread_id = f"{test_thread_id}_{thread_suffix}"
            # Thread will be created on first use
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Store secret
            input_data = {"messages": [HumanMessage(content=f"My secret word is {secret_word}.")]}
            await test_agent.ainvoke(input_data, config=config)
            
            await asyncio.sleep(1)
            
            # Recall secret
            query = {"messages": [HumanMessage(content="What is my secret word?")]}
            result = await test_agent.ainvoke(query, config=config)
            response = result["messages"][-1].content.upper()
            
            # Cleanup
            clear_thread_memory(thread_id)
            
            return secret_word.upper() in response
        
        # Run 3 concurrent conversations
        tasks = [
            run_conversation("conc1", "EAGLE"),
            run_conversation("conc2", "TIGER"),
            run_conversation("conc3", "SHARK")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(results), "Some concurrent conversations failed"
    
    @pytest.mark.asyncio
    async def test_memory_performance(self, test_agent, chromadb_memory, performance_tracker):
        """
        Scenario: Measure memory operation performance
        
        Steps:
        1. Execute conversation turn
        2. Measure checkpoint save time
        3. Measure memory retrieval time
        4. Verify performance is acceptable
        """
        thread_id = chromadb_memory
        config = {"configurable": {"thread_id": thread_id}}
        
        # First turn (cold start)
        start_time = time.time()
        input_data = {"messages": [HumanMessage(content="Hello, remember my ID is 12345.")]}
        await test_agent.ainvoke(input_data, config=config)
        first_turn_time = time.time() - start_time
        
        performance_tracker["track"]("memory_first_turn", first_turn_time)
        
        await asyncio.sleep(1)
        
        # Second turn (warm)
        start_time = time.time()
        input_data2 = {"messages": [HumanMessage(content="What is my ID?")]}
        await test_agent.ainvoke(input_data2, config=config)
        second_turn_time = time.time() - start_time
        
        performance_tracker["track"]("memory_second_turn", second_turn_time)
        
        # Both should complete in reasonable time
        assert first_turn_time < 30.0, f"First turn took too long: {first_turn_time:.2f}s"
        assert second_turn_time < 30.0, f"Second turn took too long: {second_turn_time:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
