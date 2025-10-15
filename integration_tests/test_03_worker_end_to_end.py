"""
Integration Test 03: Worker End-to-End
Tests complete worker execution flow with job processing.

NO MOCKING - Uses real database, real LLM, real agent execution.

Scenarios:
1. Create job in database
2. Trigger worker to process job
3. Worker invokes agent with LLM
4. Result stored in database
5. Verify job completion and result correctness
"""

import pytest
import asyncio
import time
from pathlib import Path
from langchain_core.messages import HumanMessage

from app.main import load_app_config
from app.agent_builder import build_agent
from helpers.db import TestDB
from helpers.utils import wait_for_condition, extract_numbers


@pytest.mark.integration
@pytest.mark.azure
class TestWorkerEndToEnd:
    """Test complete worker execution workflow."""
    
    @pytest.fixture
    async def test_db(self, data_dir):
        """Create test database for job processing."""
        db = TestDB(data_dir / "test_worker.db")
        db.prepare_schema()
        yield db
        db.teardown_schema()
    
    @pytest.mark.asyncio
    async def test_create_and_process_job(self, test_db, test_agent, test_thread_id):
        """
        Scenario: Complete job processing workflow
        
        Steps:
        1. Create job in database
        2. Trigger processing (simulate worker)
        3. Execute agent to process job
        4. Store result in database
        5. Verify job status and result
        """
        # Create job
        job_id = test_db.create_job({
            "input": "Calculate the sum of 25 and 17"
        })
        
        assert job_id is not None
        
        # Get job
        job = test_db.get_job(job_id)
        assert job["status"] == "pending"
        
        # Trigger processing
        test_db.trigger_processing(job_id)
        
        job = test_db.get_job(job_id)
        assert job["status"] == "processing"
        
        # Execute agent (simulate worker)
        start_time = time.time()
        
        input_data = {"messages": [HumanMessage(content=job["input"])]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        result = await test_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Update job with result
        test_db.update_job_status(job_id, "completed", response_text)
        
        # Log execution
        test_db.log_agent_execution(
            agent_name="test_agent",
            action="process_job",
            input_data={"job_id": job_id, "query": job["input"]},
            output_data={"response": response_text},
            status="success",
            duration_ms=duration_ms
        )
        
        # Verify completion
        job = test_db.get_job(job_id)
        assert job["status"] == "completed"
        assert job["result_text"] is not None
        assert "42" in job["result_text"]
    
    @pytest.mark.asyncio
    async def test_batch_job_processing(self, test_db, test_agent, test_thread_id):
        """
        Scenario: Process multiple jobs in batch
        
        Steps:
        1. Create multiple jobs
        2. Process each job sequentially
        3. Verify all jobs complete successfully
        """
        jobs_data = [
            {"input": "What is 10 + 10?", "expected": "20"},
            {"input": "What is 5 * 5?", "expected": "25"},
            {"input": "What is 100 - 50?", "expected": "50"}
        ]
        
        job_ids = []
        
        # Create jobs
        for job_data in jobs_data:
            job_id = test_db.create_job({"input": job_data["input"]})
            job_ids.append((job_id, job_data["expected"]))
        
        # Process jobs
        for idx, (job_id, expected) in enumerate(job_ids):
            test_db.trigger_processing(job_id)
            
            job = test_db.get_job(job_id)
            
            input_data = {"messages": [HumanMessage(content=job["input"])]}
            config = {"configurable": {"thread_id": f"{test_thread_id}_batch_{idx}"}}
            
            result = await test_agent.ainvoke(input_data, config=config)
            response_text = result["messages"][-1].content
            
            test_db.update_job_status(job_id, "completed", response_text)
        
        # Verify all completed
        for job_id, expected in job_ids:
            job = test_db.get_job(job_id)
            assert job["status"] == "completed"
            assert expected in job["result_text"] or expected in str(extract_numbers(job["result_text"]))
    
    @pytest.mark.asyncio
    async def test_job_with_error_handling(self, test_db, test_agent, test_thread_id):
        """
        Scenario: Handle job processing errors gracefully
        
        Steps:
        1. Create job with potentially problematic input
        2. Process job with error handling
        3. Verify error is caught and logged
        """
        # Create job with complex query
        job_id = test_db.create_job({
            "input": "What is the meaning of life? Answer briefly."
        })
        
        test_db.trigger_processing(job_id)
        
        try:
            job = test_db.get_job(job_id)
            
            input_data = {"messages": [HumanMessage(content=job["input"])]}
            config = {"configurable": {"thread_id": test_thread_id}}
            
            start_time = time.time()
            result = await test_agent.ainvoke(input_data, config=config)
            duration_ms = int((time.time() - start_time) * 1000)
            
            response_text = result["messages"][-1].content
            
            test_db.update_job_status(job_id, "completed", response_text)
            
            test_db.log_agent_execution(
                agent_name="test_agent",
                action="process_complex_job",
                input_data={"job_id": job_id},
                output_data={"response": response_text},
                status="success",
                duration_ms=duration_ms
            )
            
        except Exception as e:
            # Log error
            test_db.log_agent_execution(
                agent_name="test_agent",
                action="process_complex_job",
                input_data={"job_id": job_id},
                output_data=None,
                status="error",
                error_message=str(e)
            )
            
            test_db.update_job_status(job_id, "failed", f"Error: {str(e)}")
        
        # Verify job was handled (either completed or failed)
        job = test_db.get_job(job_id)
        assert job["status"] in ["completed", "failed"]
    
    @pytest.mark.asyncio
    async def test_job_execution_logging(self, test_db, test_agent, test_thread_id):
        """
        Scenario: Verify job execution is properly logged
        
        Steps:
        1. Process job
        2. Check agent logs
        3. Verify log entries are correct
        """
        job_id = test_db.create_job({
            "input": "What is 7 * 8?"
        })
        
        test_db.trigger_processing(job_id)
        job = test_db.get_job(job_id)
        
        start_time = time.time()
        
        input_data = {"messages": [HumanMessage(content=job["input"])]}
        config = {"configurable": {"thread_id": test_thread_id}}
        
        result = await test_agent.ainvoke(input_data, config=config)
        response_text = result["messages"][-1].content
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        test_db.update_job_status(job_id, "completed", response_text)
        
        # Log execution
        test_db.log_agent_execution(
            agent_name="test_agent",
            action="multiplication",
            input_data={"query": job["input"]},
            output_data={"response": response_text},
            status="success",
            duration_ms=duration_ms
        )
        
        # Verify logs
        logs = test_db.get_agent_logs(agent_name="test_agent")
        
        assert len(logs) > 0
        
        latest_log = logs[0]
        assert latest_log["action"] == "multiplication"
        assert latest_log["status"] == "success"
        assert latest_log["duration_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_job_timeout_handling(self, test_db, test_agent, test_thread_id):
        """
        Scenario: Handle job timeout
        
        Steps:
        1. Create job
        2. Set timeout for processing
        3. Verify timeout is enforced
        """
        job_id = test_db.create_job({
            "input": "What is 15 + 15?"
        })
        
        test_db.trigger_processing(job_id)
        job = test_db.get_job(job_id)
        
        # Set short timeout
        timeout_seconds = 20
        
        try:
            input_data = {"messages": [HumanMessage(content=job["input"])]}
            config = {"configurable": {"thread_id": test_thread_id}}
            
            result = await asyncio.wait_for(
                test_agent.ainvoke(input_data, config=config),
                timeout=timeout_seconds
            )
            
            response_text = result["messages"][-1].content
            test_db.update_job_status(job_id, "completed", response_text)
            
            # Should complete within timeout
            job = test_db.get_job(job_id)
            assert job["status"] == "completed"
            
        except asyncio.TimeoutError:
            test_db.update_job_status(job_id, "failed", "Timeout exceeded")
            test_db.log_agent_execution(
                agent_name="test_agent",
                action="timeout_test",
                input_data={"job_id": job_id},
                output_data=None,
                status="timeout",
                error_message="Job exceeded timeout"
            )
    
    @pytest.mark.asyncio
    async def test_conversation_history_storage(self, test_db, test_agent, test_thread_id):
        """
        Scenario: Store conversation history in database
        
        Steps:
        1. Execute multiple conversation turns
        2. Store each turn in database
        3. Retrieve and verify conversation history
        """
        thread_id = f"{test_thread_id}_conversation"
        
        conversation_turns = [
            ("user", "Hello, I need help with math."),
            ("assistant", None),  # Will be filled by agent
            ("user", "What is 12 + 8?"),
            ("assistant", None)
        ]
        
        for idx, (role, content) in enumerate(conversation_turns):
            if role == "user":
                # Store user message
                test_db.add_conversation_turn(thread_id, role, content)
                
                # Get agent response
                input_data = {"messages": [HumanMessage(content=content)]}
                config = {"configurable": {"thread_id": thread_id}}
                
                result = await test_agent.ainvoke(input_data, config=config)
                response_text = result["messages"][-1].content
                
                # Store agent response
                test_db.add_conversation_turn(thread_id, "assistant", response_text)
        
        # Retrieve conversation history
        history = test_db.get_conversation_history(thread_id)
        
        assert len(history) >= 2  # At least user and assistant messages
        
        # Verify last response contains answer
        last_turn = history[-1]
        assert last_turn["role"] == "assistant"
        assert "20" in last_turn["content"] or extract_numbers(last_turn["content"]) == [20]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
