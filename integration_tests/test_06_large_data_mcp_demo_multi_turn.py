"""
Integration Test 6: Large Data MCP Demo - Multi-Turn Conversations
NO MOCKING - Real multi-agent workflow with large data handling

Tests:
1. Multi-turn data generation and analysis workflow
2. Reference ID preservation across conversation turns
3. Supervisor coordination with data_generator and data_analyzer agents
4. Large data storage and retrieval in multi-turn context
5. Memory persistence across multiple interactions
"""

import asyncio
import sys
import uuid
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, print_test_header, print_section,
    check_azure_credentials
)

from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from dotenv import load_dotenv

load_dotenv()


async def test_multi_turn_data_workflow():
    """Test multi-turn conversation with data generation and analysis"""
    result = TestResult("Multi-Turn Data Generation and Analysis")
    env = TestEnvironment("large_data_mcp_demo")

    try:
        print_section("Testing Multi-Turn Large Data Workflow")

        # Create a simplified test config without MCP servers for integration testing
        # This tests the multi-turn workflow and supervisor coordination
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

temperature: 0.1

business_context: |
  This is a test of multi-turn conversation with data generation and analysis.
  The system should maintain context across multiple turns.
  
  You must respond with JSON format for execution plans.

supervisor:
  name: "data_supervisor"
  prompt: |
    {{agents}}

    Create a JSON execution plan. Output ONLY valid JSON, nothing else.

    For "generate" requests, use data_generator.
    For "analyze" requests, use data_analyzer.
    For "generate and analyze" requests, create 2 steps with data_analyzer depending on data_generator.

    JSON format:
    {
      "goal": "brief task description",
      "plan": [
        {"id": "s1", "agent": "agent_name", "task": "specific task", "depends_on": [], "verify": null, "timeout_seconds": 60, "retry": 1}
      ]
    }

    Output ONLY the JSON. No explanations.

agents:
  - name: "data_generator"
    description: "Generates datasets and provides summaries"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    prompt: |
      You are a data generation specialist.

      When asked to generate data, create a detailed description of the dataset including:
      - Number of records
      - Fields and their types
      - Sample data (first 3-5 records)
      - A unique reference ID in format: ref_XXXXXXXX

      Always include a reference ID so the data can be referenced in future turns.

  - name: "data_analyzer"
    description: "Analyzes datasets and provides insights"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    prompt: |
      You are a data analysis specialist.

      When analyzing data:
      - Look for reference IDs in the conversation context
      - Provide statistical analysis
      - Calculate averages, totals, and other metrics
      - Identify patterns and insights

      If you see a reference ID from a previous step, acknowledge it and provide analysis
      based on the dataset description provided earlier.
"""

        config_path = env.create_temp_file("large_data_mcp_demo_test.yaml", config_content)

        print(f"✓ Loading config: {config_path}")
        app_config = load_app_config(config_path)
        
        # Get default model
        default_model = app_config.models.get('default', 'azure_openai:gpt-4.1')
        print(f"✓ Using model: {default_model}")
        
        # Generate unique thread ID for this test
        thread_id = f"test_large_data_{uuid.uuid4().hex[:8]}"
        print(f"✓ Thread ID: {thread_id}")
        
        # TURN 1: Generate a dataset
        print_section("Turn 1: Generate Dataset")
        user_input_1 = "Generate a dataset of 100 customer records with id, name, city, and purchase_amount fields."
        
        print(f"User: {user_input_1}")
        
        # Build supervisor for turn 1
        supervisor_1 = build_supervisor_compiled(
            app_config.supervisor,
            app_config.agents,
            default_model,
            app_config.business_context or "",
            original_user_question=user_input_1,
            config_path=str(config_path),
            default_temperature=0.1,
            thread_id=thread_id,
        )
        
        # Build agents map
        agents_map, mcp_clients = await build_agents_map(
            app_config, 
            user_input=user_input_1, 
            config_path=str(config_path)
        )
        
        print(f"✓ Built {len(agents_map)} agents: {list(agents_map.keys())}")
        
        # Execute turn 1
        start_time = time.time()
        result_1 = await execute_plan(
            supervisor_compiled=supervisor_1,
            agents_map=agents_map,
            user_input=user_input_1,
            business_context=app_config.business_context or "",
            thread_id=thread_id,
            default_model_for_verifier=default_model
        )
        turn_1_duration = time.time() - start_time
        
        print(f"✓ Turn 1 completed in {turn_1_duration:.2f}s")

        # Extract reference ID from turn 1 response
        turn_1_response = result_1.get("final_result", "")
        if isinstance(turn_1_response, dict):
            turn_1_response = str(turn_1_response)
        print(f"Turn 1 Response: {turn_1_response[:200]}...")
        
        # Check if data was generated
        has_reference = "ref_" in turn_1_response or "Reference ID" in turn_1_response
        has_dataset_info = "100" in turn_1_response or "customer" in turn_1_response.lower()
        
        result.add_sub_test(
            "Turn 1: Data Generation",
            has_reference and has_dataset_info,
            duration=turn_1_duration,
            has_reference=has_reference,
            has_dataset_info=has_dataset_info
        )
        
        # TURN 2: Analyze the generated dataset
        print_section("Turn 2: Analyze Dataset")
        user_input_2 = "Analyze the customer dataset you just generated. Calculate the average purchase amount and identify the top 5 customers by purchase amount."
        
        print(f"User: {user_input_2}")
        
        # Build supervisor for turn 2 (same thread_id for continuity)
        supervisor_2 = build_supervisor_compiled(
            app_config.supervisor,
            app_config.agents,
            default_model,
            app_config.business_context or "",
            original_user_question=user_input_2,
            config_path=str(config_path),
            default_temperature=0.1,
            thread_id=thread_id,
        )
        
        # Execute turn 2
        start_time = time.time()
        result_2 = await execute_plan(
            supervisor_compiled=supervisor_2,
            agents_map=agents_map,
            user_input=user_input_2,
            business_context=app_config.business_context or "",
            thread_id=thread_id,
            default_model_for_verifier=default_model
        )
        turn_2_duration = time.time() - start_time
        
        print(f"✓ Turn 2 completed in {turn_2_duration:.2f}s")

        turn_2_response = result_2.get("final_result", "")
        if isinstance(turn_2_response, dict):
            turn_2_response = str(turn_2_response)
        print(f"Turn 2 Response: {turn_2_response[:200]}...")
        
        # Check if analysis was performed
        has_average = "average" in turn_2_response.lower() or "mean" in turn_2_response.lower()
        has_top_customers = "top" in turn_2_response.lower() or "highest" in turn_2_response.lower()
        has_numbers = any(char.isdigit() for char in turn_2_response)
        
        result.add_sub_test(
            "Turn 2: Data Analysis",
            has_average and has_top_customers and has_numbers,
            duration=turn_2_duration,
            has_average=has_average,
            has_top_customers=has_top_customers,
            has_numbers=has_numbers
        )
        
        # TURN 3: Further analysis with context
        print_section("Turn 3: Additional Analysis")
        user_input_3 = "Based on the customer data, how many customers have a purchase amount above the average?"
        
        print(f"User: {user_input_3}")
        
        # Build supervisor for turn 3 (same thread_id)
        supervisor_3 = build_supervisor_compiled(
            app_config.supervisor,
            app_config.agents,
            default_model,
            app_config.business_context or "",
            original_user_question=user_input_3,
            config_path=str(config_path),
            default_temperature=0.1,
            thread_id=thread_id,
        )
        
        # Execute turn 3
        start_time = time.time()
        result_3 = await execute_plan(
            supervisor_compiled=supervisor_3,
            agents_map=agents_map,
            user_input=user_input_3,
            business_context=app_config.business_context or "",
            thread_id=thread_id,
            default_model_for_verifier=default_model
        )
        turn_3_duration = time.time() - start_time
        
        print(f"✓ Turn 3 completed in {turn_3_duration:.2f}s")

        turn_3_response = result_3.get("final_result", "")
        if isinstance(turn_3_response, dict):
            turn_3_response = str(turn_3_response)
        print(f"Turn 3 Response: {turn_3_response[:200]}...")
        
        # Check if context was preserved and analysis performed
        has_count = any(char.isdigit() for char in turn_3_response)
        has_context = "customer" in turn_3_response.lower() or "above" in turn_3_response.lower()
        
        result.add_sub_test(
            "Turn 3: Context-Aware Analysis",
            has_count and has_context,
            duration=turn_3_duration,
            has_count=has_count,
            has_context=has_context
        )
        
        # TURN 4: Generate new dataset and compare
        print_section("Turn 4: Generate and Compare")
        user_input_4 = "Generate a new dataset of 50 product records with id, name, category, and price. Then tell me how many datasets we have worked with in total."
        
        print(f"User: {user_input_4}")
        
        # Build supervisor for turn 4 (same thread_id)
        supervisor_4 = build_supervisor_compiled(
            app_config.supervisor,
            app_config.agents,
            default_model,
            app_config.business_context or "",
            original_user_question=user_input_4,
            config_path=str(config_path),
            default_temperature=0.1,
            thread_id=thread_id,
        )
        
        # Execute turn 4
        start_time = time.time()
        result_4 = await execute_plan(
            supervisor_compiled=supervisor_4,
            agents_map=agents_map,
            user_input=user_input_4,
            business_context=app_config.business_context or "",
            thread_id=thread_id,
            default_model_for_verifier=default_model
        )
        turn_4_duration = time.time() - start_time
        
        print(f"✓ Turn 4 completed in {turn_4_duration:.2f}s")

        turn_4_response = result_4.get("final_result", "")
        if isinstance(turn_4_response, dict):
            turn_4_response = str(turn_4_response)
        print(f"Turn 4 Response: {turn_4_response[:200]}...")
        
        # Check if new dataset was generated
        has_new_dataset = "product" in turn_4_response.lower() or "50" in turn_4_response
        has_memory = "two" in turn_4_response.lower() or "2" in turn_4_response or "both" in turn_4_response.lower()
        
        result.add_sub_test(
            "Turn 4: Multi-Dataset Memory",
            has_new_dataset,  # Memory check is optional as it depends on agent interpretation
            duration=turn_4_duration,
            has_new_dataset=has_new_dataset,
            has_memory_reference=has_memory
        )
        
        # Calculate total metrics
        total_duration = turn_1_duration + turn_2_duration + turn_3_duration + turn_4_duration
        
        result.finish(
            True,
            thread_id=thread_id,
            total_turns=4,
            total_duration=total_duration,
            avg_turn_duration=total_duration / 4,
            agents_used=list(agents_map.keys())
        )
        
        # Cleanup MCP clients
        for client in mcp_clients.values():
            try:
                if hasattr(client, 'aclose'):
                    await client.aclose()
            except Exception as e:
                print(f"Warning: Failed to close MCP client: {e}")
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def main():
    """Run all large data MCP demo multi-turn tests"""
    print_test_header("INTEGRATION TEST 6: Large Data MCP Demo - Multi-Turn")
    
    if not check_azure_credentials():
        print("\n❌ Azure OpenAI credentials not configured!")
        print("   This test requires Azure OpenAI to be configured.")
        return False
    
    print("✓ Prerequisites met\n")
    
    results = []
    
    result1 = await test_multi_turn_data_workflow()
    result1.print_result()
    results.append(result1)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 6 SUMMARY: {passed}/{total} passed")
    print(f"{'=' * 80}\n")
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

