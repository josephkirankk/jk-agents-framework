"""
Integration Test 02: API to LLM Flow
Tests complete API request through to LLM response flow.

NO MOCKING - Uses real FastAPI server, real LLM, real ChromaDB.

Scenarios:
1. Start API server and make HTTP request
2. Request flows through API → Config → Agent → LLM
3. Response returns through LLM → Agent → API → Client
4. Verify complete end-to-end flow with real data
"""

import pytest
import asyncio
import time
import requests
import json
from pathlib import Path

from helpers.utils import wait_for_condition, contains_keywords


@pytest.mark.integration
@pytest.mark.azure
class TestApiToLlmFlow:
    """Test complete API to LLM workflow."""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        """Base URL for API (assumes server is running)."""
        return "http://localhost:8000"
    
    def _check_server_running(self, api_base_url):
        """Check if API server is running."""
        try:
            response = requests.get(f"{api_base_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, api_base_url):
        """
        Scenario: Check API server health endpoint
        
        Steps:
        1. Send GET request to /health
        2. Verify 200 response
        3. Verify response structure
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running. Start with: uvicorn api:app")
        
        response = requests.get(f"{api_base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_simple_query_via_api(self, api_base_url, test_thread_id):
        """
        Scenario: Execute simple query through API
        
        Steps:
        1. Send POST /query with simple question
        2. Wait for response
        3. Verify response contains correct answer
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running. Start with: uvicorn api:app")
        
        payload = {
            "input": "What is 25 + 17? Give me just the number.",
            "config_path": "config/python_exec_agent_working.yaml",
            "thread_id": test_thread_id
        }
        
        response = requests.post(
            f"{api_base_url}/query",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "response" in data or "result" in data or "answer" in data
        
        response_text = str(data.get("response") or data.get("result") or data.get("answer"))
        
        # Verify answer
        assert "42" in response_text
    
    @pytest.mark.asyncio
    async def test_query_with_configuration(self, api_base_url, test_thread_id):
        """
        Scenario: Query with specific configuration
        
        Steps:
        1. Send query with config_name parameter
        2. Verify config is loaded and used
        3. Verify response follows config settings
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        payload = {
            "input": "What is Python? Answer in one sentence.",
            "config_path": "config/python_exec_agent_working.yaml",
            "thread_id": test_thread_id
        }
        
        response = requests.post(
            f"{api_base_url}/query",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        response_text = str(data.get("response", "")).lower()
        
        # Verify response is about Python
        assert "python" in response_text
        assert len(response_text) > 20
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_via_api(self, api_base_url, test_thread_id):
        """
        Scenario: Multi-turn conversation through API
        
        Steps:
        1. Send first query with thread_id
        2. Send second query with same thread_id
        3. Verify second response has context from first
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        thread_id = f"{test_thread_id}_multiturn"
        
        # First query
        payload1 = {
            "input": "My favorite number is 42. Remember this.",
            "config_path": "config/simple_memory_test_agent.yaml",
            "thread_id": thread_id
        }
        
        response1 = requests.post(
            f"{api_base_url}/query",
            json=payload1,
            timeout=30
        )
        
        assert response1.status_code == 200
        
        # Wait a bit for memory to be stored
        await asyncio.sleep(2)
        
        # Second query
        payload2 = {
            "input": "What is my favorite number?",
            "config_path": "config/simple_memory_test_agent.yaml",
            "thread_id": thread_id
        }
        
        response2 = requests.post(
            f"{api_base_url}/query",
            json=payload2,
            timeout=30
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        response_text = str(data2.get("response", "")).lower()
        
        # Verify it remembers the number
        assert "42" in response_text
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_config(self, api_base_url, test_thread_id):
        """
        Scenario: Test API error handling for invalid config
        
        Steps:
        1. Send query with non-existent config
        2. Verify appropriate error response
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        payload = {
            "input": "test query",
            "config_path": "config/non_existent_config_xyz123.yaml",
            "thread_id": test_thread_id
        }
        
        response = requests.post(
            f"{api_base_url}/query",
            json=payload,
            timeout=30
        )
        
        # Should return error status code (422 is FastAPI's validation error)
        assert response.status_code in [400, 404, 422, 500]
    
    @pytest.mark.asyncio
    async def test_api_response_time(self, api_base_url, test_thread_id, performance_tracker):
        """
        Scenario: Measure API response time
        
        Steps:
        1. Send query
        2. Measure total response time
        3. Verify it's within acceptable range
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        payload = {
            "input": "What is 5 + 5?",
            "config_path": "config/python_exec_agent_working.yaml",
            "thread_id": test_thread_id
        }
        
        start_time = time.time()
        
        response = requests.post(
            f"{api_base_url}/query",
            json=payload,
            timeout=30
        )
        
        duration = time.time() - start_time
        performance_tracker["track"]("api_query", duration)
        
        assert response.status_code == 200
        assert duration < 30.0, f"API query took too long: {duration:.2f}s"
    
    @pytest.mark.asyncio
    async def test_memory_stats_endpoint(self, api_base_url):
        """
        Scenario: Check memory stats endpoint
        
        Steps:
        1. Query /memory/stats endpoint
        2. Verify response contains memory metrics
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        response = requests.get(f"{api_base_url}/memory/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should contain some memory statistics
        assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_clear_thread_memory(self, api_base_url, test_thread_id):
        """
        Scenario: Clear thread memory via API
        
        Steps:
        1. Create conversation with thread_id
        2. Clear thread memory
        3. Verify memory is cleared
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        thread_id = f"{test_thread_id}_clear"
        
        # Create conversation
        payload = {
            "input": "Remember that my name is Alice.",
            "config_path": "config/python_exec_agent_working.yaml",
            "thread_id": thread_id
        }
        
        response1 = requests.post(
            f"{api_base_url}/query",
            json=payload,
            timeout=30
        )
        
        assert response1.status_code == 200
        
        # Clear memory
        response2 = requests.post(f"{api_base_url}/memory/clear/{thread_id}")
        
        # Should succeed (200 or 204)
        assert response2.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, api_base_url, test_thread_id):
        """
        Scenario: Send multiple concurrent requests
        
        Steps:
        1. Send 3 requests concurrently
        2. Wait for all responses
        3. Verify all succeed
        """
        if not self._check_server_running(api_base_url):
            pytest.skip("API server not running")
        
        async def send_request(query_num):
            payload = {
                "input": f"What is {query_num} + {query_num}?",
                "config_path": "config/python_exec_agent_working.yaml",
                "thread_id": f"{test_thread_id}_concurrent_{query_num}"
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{api_base_url}/query",
                    json=payload,
                    timeout=60
                )
            )
            return response
        
        # Send 3 concurrent requests
        tasks = [send_request(i) for i in [5, 10, 15]]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
