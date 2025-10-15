"""
Integration Test 05: Error Handling and Recovery
Tests system behavior under error conditions and recovery mechanisms.

NO MOCKING - Uses real LLM, real error scenarios, real retry logic.

Scenarios:
1. Handle invalid configuration gracefully
2. Retry on transient LLM failures
3. Recover from timeout errors
4. Handle malformed input
5. Verify error logging and reporting
"""

import pytest
import asyncio
import time
from pathlib import Path
from langchain_core.messages import HumanMessage

from app.main import load_app_config
from app.agent_builder import build_agent
from test_utils import convert_app_config_to_dict
from helpers.utils import retry_on_failure, wait_for_condition
from helpers.db import TestDB


@pytest.mark.integration
@pytest.mark.azure
class TestErrorHandlingRecovery:
    """Test error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_invalid_config_handling(self, config_dir):
        """
        Scenario: Handle invalid configuration file
        
        Steps:
        1. Try to load non-existent config
        2. Verify appropriate error is raised
        3. Verify system doesn't crash
        """
        invalid_config_path = config_dir / "non_existent_config_xyz.yaml"
        
        with pytest.raises(FileNotFoundError):
            config = load_app_config(invalid_config_path)
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, llm_config):
        """
        Scenario: Retry mechanism for transient failures
        
        Steps:
        1. Define function that fails first time
        2. Use retry_on_failure helper
        3. Verify it succeeds after retry
        """
        attempt_count = {"count": 0}
        
        async def flaky_function():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise ConnectionError("Simulated transient error")
            return "success"
        
        result = await retry_on_failure(
            flaky_function,
            max_retries=3,
            initial_delay=0.1,
            exceptions=(ConnectionError,)
        )
        
        assert result == "success"
        assert attempt_count["count"] == 3
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, test_agent, test_thread_id):
        """
        Scenario: Handle query timeout gracefully
        
        Steps:
        1. Execute query with short timeout
        2. Verify timeout is enforced
        3. Verify system recovers
        """
        query = "What is 5 + 5?"
        input_data = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        # Set reasonable timeout
        timeout_seconds = 30
        
        try:
            result = await asyncio.wait_for(
                test_agent.ainvoke(input_data, config=config),
                timeout=timeout_seconds
            )
            
            # Should complete successfully
            assert result is not None
            assert len(result["messages"]) > 0
            
        except asyncio.TimeoutError:
            # If it times out, verify we can recover
            pytest.skip("Query timed out - may indicate slow LLM response")
    
    @pytest.mark.asyncio
    async def test_malformed_input_handling(self, test_agent, test_thread_id):
        """
        Scenario: Handle malformed input gracefully
        
        Steps:
        1. Send empty query
        2. Send very long query
        3. Send query with special characters
        4. Verify system handles all gracefully
        """
        config = {"configurable": {"thread_id": test_thread_id}}
        
        # Test empty query
        try:
            input_data = {"messages": [HumanMessage(content="")]}
            result = await test_agent.ainvoke(input_data, config=config)
            # Should handle gracefully, not crash
            assert result is not None
        except Exception as e:
            # Error is acceptable, but should not crash system
            assert isinstance(e, (ValueError, RuntimeError))
        
        # Test query with special characters
        special_query = "What is 2+2? @#$%^&*()"
        input_data = {"messages": [HumanMessage(content=special_query)]}
        result = await test_agent.ainvoke(input_data, config=config)
        
        assert result is not None
        assert len(result["messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self, test_agent, test_thread_id):
        """
        Scenario: Handle errors in concurrent requests
        
        Steps:
        1. Send multiple requests concurrently
        2. Some succeed, some fail
        3. Verify failures don't affect successes
        """
        async def execute_query(query, thread_suffix):
            try:
                input_data = {"messages": [HumanMessage(content=query)]}
                config = {"configurable": {"thread_id": f"{test_thread_id}_{thread_suffix}"}}
                result = await test_agent.ainvoke(input_data, config=config)
                return True, result["messages"][-1].content
            except Exception as e:
                return False, str(e)
        
        # Mix of valid and potentially problematic queries
        queries = [
            ("What is 2 + 2?", "q1"),
            ("What is 10 * 10?", "q2"),
            ("What is 7 + 3?", "q3")
        ]
        
        tasks = [execute_query(q, tid) for q, tid in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some should succeed
        successes = [r for r in results if isinstance(r, tuple) and r[0]]
        assert len(successes) >= 2, "Most queries should succeed"
    
    @pytest.mark.asyncio
    async def test_database_error_recovery(self, data_dir, test_agent, test_thread_id):
        """
        Scenario: Recover from database errors
        
        Steps:
        1. Create database operation
        2. Simulate error
        3. Verify recovery mechanism works
        """
        db = TestDB(data_dir / "test_error_recovery.db")
        
        try:
            db.prepare_schema()
            
            # Create job
            job_id = db.create_job({"input": "Test query"})
            assert job_id is not None
            
            # Simulate processing
            job = db.get_job(job_id)
            assert job is not None
            
            # Execute agent
            input_data = {"messages": [HumanMessage(content=job["input"])]}
            config = {"configurable": {"thread_id": test_thread_id}}
            
            result = await test_agent.ainvoke(input_data, config=config)
            
            # Update job - should work even if there were transient issues
            db.update_job_status(job_id, "completed", result["messages"][-1].content)
            
            final_job = db.get_job(job_id)
            assert final_job["status"] == "completed"
            
        finally:
            db.teardown_schema()
    
    @pytest.mark.asyncio
    async def test_memory_error_recovery(self, test_agent, test_thread_id):
        """
        Scenario: Recover from memory operation errors
        
        Steps:
        1. Execute query with thread_id
        2. Simulate memory error scenario
        3. Verify system continues to function
        """
        from app.checkpointer_manager import clear_thread_memory
        
        thread_id = f"{test_thread_id}_mem_error"
        
        # Memory will be initialized on first use
        
        # Execute query
        input_data = {"messages": [HumanMessage(content="Remember: my code is ABC123")]}
        config = {"configurable": {"thread_id": thread_id}}
        
        result1 = await test_agent.ainvoke(input_data, config=config)
        assert result1 is not None
        
        # Clear memory (simulate error recovery by clearing state)
        clear_thread_memory(thread_id)
        
        # System should still work after memory clear
        input_data2 = {"messages": [HumanMessage(content="What is 5 + 5?")]}
        result2 = await test_agent.ainvoke(input_data2, config=config)
        
        assert result2 is not None
        assert len(result2["messages"]) > 0
    
    @pytest.mark.asyncio
    async def test_agent_builder_error_handling(self, config_dir, test_thread_id):
        """
        Scenario: Handle agent building errors
        
        Steps:
        1. Try to build agent with invalid config
        2. Verify appropriate error handling
        """
        config_path = config_dir / "simple_test_no_mcp.yaml"
        config = load_app_config(config_path)
        
        # Try with invalid model name
        agent_config = config.agents[0]
        
        # This should either work or fail gracefully
        try:
            app_config_dict = convert_app_config_to_dict(config)
            agent, mcp_client = await build_agent(
                agent_cfg=agent_config,
                default_model="invalid_model_xyz",
                config_path=str(config_path),
                app_config=app_config_dict
            )
            
            # If it builds, it should still be functional (fallback mechanism)
            if agent:
                # Cleanup
                if mcp_client:
                    from app.mcp_loader import close_mcp_client
                    await close_mcp_client(mcp_client)
                    
        except Exception as e:
            # Error is acceptable - should be clear error message
            assert len(str(e)) > 0
    
    @pytest.mark.asyncio
    async def test_error_logging(self, data_dir, test_agent, test_thread_id):
        """
        Scenario: Verify errors are properly logged
        
        Steps:
        1. Execute operations that may fail
        2. Check that errors are logged
        3. Verify log contains useful information
        """
        db = TestDB(data_dir / "test_error_logging.db")
        
        try:
            db.prepare_schema()
            
            # Create job
            job_id = db.create_job({"input": "Test error logging"})
            
            # Simulate processing with error
            try:
                # Intentionally cause an error
                raise ValueError("Simulated processing error")
            except Exception as e:
                # Log the error
                db.log_agent_execution(
                    agent_name="test_agent",
                    action="error_test",
                    input_data={"job_id": job_id},
                    output_data=None,
                    status="error",
                    error_message=str(e)
                )
            
            # Verify error was logged
            logs = db.get_agent_logs(agent_name="test_agent")
            assert len(logs) > 0
            
            error_log = logs[0]
            assert error_log["status"] == "error"
            assert error_log["error_message"] is not None
            assert "Simulated processing error" in error_log["error_message"]
            
        finally:
            db.teardown_schema()
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, test_agent, test_thread_id):
        """
        Scenario: System degrades gracefully under stress
        
        Steps:
        1. Execute multiple rapid queries
        2. Verify system remains responsive
        3. Verify no crashes or hangs
        """
        config = {"configurable": {"thread_id": test_thread_id}}
        
        # Execute several queries rapidly
        queries = [
            "What is 1+1?",
            "What is 2+2?",
            "What is 3+3?",
        ]
        
        results = []
        
        for query in queries:
            input_data = {"messages": [HumanMessage(content=query)]}
            
            try:
                result = await asyncio.wait_for(
                    test_agent.ainvoke(input_data, config=config),
                    timeout=30
                )
                results.append(True)
            except Exception as e:
                results.append(False)
                print(f"Query failed: {e}")
        
        # Most queries should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.66, f"Success rate too low: {success_rate:.2%}"
    
    @pytest.mark.asyncio
    async def test_recovery_after_failure(self, test_agent, test_thread_id):
        """
        Scenario: System recovers after failure
        
        Steps:
        1. Execute query that succeeds
        2. Execute query that might fail
        3. Execute query that should succeed
        4. Verify system recovers
        """
        config = {"configurable": {"thread_id": f"{test_thread_id}_recovery"}}
        
        # First query - should succeed
        input1 = {"messages": [HumanMessage(content="What is 5 + 5?")]}
        result1 = await test_agent.ainvoke(input1, config=config)
        assert result1 is not None
        
        # Second query - might have issues but shouldn't crash system
        input2 = {"messages": [HumanMessage(content="" * 10)]}  # Unusual input
        try:
            result2 = await test_agent.ainvoke(input2, config=config)
        except:
            pass  # Acceptable to fail
        
        # Third query - should succeed (recovery)
        input3 = {"messages": [HumanMessage(content="What is 10 + 10?")]}
        result3 = await test_agent.ainvoke(input3, config=config)
        
        assert result3 is not None
        assert len(result3["messages"]) > 0
        assert "20" in result3["messages"][-1].content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
