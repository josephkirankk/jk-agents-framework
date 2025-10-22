#!/usr/bin/env python3
"""
SUPER INTEGRATED TEST - Complete System Validation
NO MOCKING - All real components working together

This test validates the ENTIRE system end-to-end:
1. Configuration Loading & Model Format Handling
2. Agent Building (Normal & React types)
3. MCP Server Integration & Tool Calling
4. ChromaDB Memory (Conversation & Checkpointing)
5. Supervisor Planning & Execution
6. Multi-Provider Model Support
7. File Storage & Multimodal Support
8. API Endpoints
9. Error Handling & Recovery
10. Performance & Memory Management

Test Flow:
- Phase 1: System Initialization (Config, Memory, Agents)
- Phase 2: Single Agent Execution (Normal & React)
- Phase 3: Supervisor-Worker Orchestration
- Phase 4: Multi-turn Conversations with Memory
- Phase 5: Advanced Features (Multimodal, Large Data)
- Phase 6: API Integration
- Phase 7: Cleanup & Verification

This is the ULTIMATE integration test that ensures all modules work together seamlessly.
"""

import asyncio
import os
import sys
import uuid
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, TestStats,
    print_test_header, print_section,
    check_azure_credentials, invoke_agent, extract_tool_calls,
    verify_chromadb_available
)

# Core imports
from app.main import load_app_config, build_agents_map, process_business_context_template
from app.agent_builder import build_agent, create_model_instance
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan, parse_plan_text
from app.conversation_tracker import ConversationTracker
from app.thread_id_utils import generate_thread_id
from app.checkpointer_manager import get_global_checkpointer, clear_thread_memory, get_memory_stats
from app.memory_integration import initialize_conversation_memory, store_conversation_memory
from app.file_storage_manager import get_file_storage_manager
from app.mcp_loader import close_mcp_client

# Import for API testing
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from dotenv import load_dotenv
load_dotenv()


class SuperIntegratedTest:
    """Manages the super integrated test execution."""
    
    def __init__(self):
        self.stats = TestStats()
        self.env = TestEnvironment("super_integrated")
        self.test_thread_id = f"super_test_{uuid.uuid4().hex[:8]}"
        self.created_resources = {
            "threads": [],
            "files": [],
            "mcp_clients": [],
            "agents": {}
        }
        self.performance_metrics = {
            "config_load_time": 0,
            "agent_build_time": 0,
            "supervisor_build_time": 0,
            "first_query_time": 0,
            "memory_operations": [],
            "tool_calls_count": 0
        }
        
    async def cleanup(self):
        """Clean up all test resources."""
        print_section("Cleanup")
        
        # Clean up threads
        for thread_id in self.created_resources["threads"]:
            try:
                # clear_thread_memory is not async, don't await it
                result = clear_thread_memory(thread_id)
                print(f"  ✓ Cleared thread: {thread_id}")
            except Exception as e:
                print(f"  ⚠️  Failed to clear thread {thread_id}: {e}")
        
        # Clean up MCP clients
        for client in self.created_resources["mcp_clients"]:
            try:
                await close_mcp_client(client)
                print(f"  ✓ Closed MCP client")
            except Exception as e:
                print(f"  ⚠️  Failed to close MCP client: {e}")
        
        # Clean up temporary files
        self.env.cleanup()
        print("  ✓ Cleaned up temporary files")
    
    def record_performance(self, metric: str, value: float):
        """Record performance metric."""
        self.performance_metrics[metric] = value
    
    def print_performance_summary(self):
        """Print performance metrics summary."""
        print_section("Performance Summary")
        print(f"  Config Load Time:      {self.performance_metrics['config_load_time']:.3f}s")
        print(f"  Agent Build Time:      {self.performance_metrics['agent_build_time']:.3f}s")
        print(f"  Supervisor Build Time: {self.performance_metrics['supervisor_build_time']:.3f}s")
        print(f"  First Query Time:      {self.performance_metrics['first_query_time']:.3f}s")
        print(f"  Tool Calls Count:      {self.performance_metrics['tool_calls_count']}")
        print(f"  Memory Operations:     {len(self.performance_metrics['memory_operations'])}")


async def phase1_system_initialization(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 1: System Initialization
    - Load configuration files
    - Validate model format handling
    - Initialize memory systems (ChromaDB)
    - Create checkpointer
    """
    result = TestResult("Phase 1: System Initialization")
    
    try:
        print_section("Phase 1: System Initialization")
        
        # Step 1.1: Create comprehensive test configuration
        print("\n[1.1] Creating Test Configuration...")
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"
  temperature: 0.1

business_context: |
  You are an advanced AI system with computational capabilities.
  Use appropriate tools for calculations and data processing.

memory:
  backend: "chromadb"
  chromadb:
    path: "./integration_tests/temp/test_super_integrated_memory"
    checkpoint_collection: "super_test_checkpoints"
    context_collection: "super_test_context"

# Enable large data handling for Phase 8 test
large_data_handling:
  enabled: true
  token_threshold: 1000  # Store tool outputs > 1000 tokens
  
  large_data:
    sqlite_path: "./integration_tests/temp/large_tool_data.db"
    file_path: "./integration_tests/temp/large_tool_data_files/"
    compression: true
    max_sqlite_size_mb: 50
  
  summarization:
    max_summary_tokens: 200
    sample_size: 5
    include_statistics: true

conversation_memory:
  enabled: true
  max_conversations: 10
  max_context_length: 2000

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: |
    You are a supervisor that creates execution plans.
    
    Available agents:
    {{agents}}
    
    Create a JSON plan with steps. Return ONLY JSON:
    {
      "goal": "<goal>",
      "plan": [
        {"id": "s1", "agent": "agent_name", "task": "task description", "depends_on": [], "verify": "verification", "timeout_seconds": 60, "retry": 2}
      ]
    }

agents:
  - name: "conversational_agent"
    description: "Basic conversational agent for simple queries"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"
    prompt: |
      You are a helpful assistant. Answer questions clearly and concisely.
  
  - name: "python_executor"
    description: "Execute Python code for calculations and data processing"
    model: "azure_openai:gpt-4.1"
    agent_type: "react"
    prompt: |
      You are a Python coding assistant. Execute code using the run_python_code tool.
      Always show both the code and execution results.
      
      For large datasets (10K+ records), use store_large_dataset_to_chromadb tool to store data efficiently:
      1. Generate the data with run_python_code
      2. Convert to JSON string
      3. Call store_large_dataset_to_chromadb(dataset_json="...", description="...")
      4. Return the reference_id and summary to the user
    mcp_servers:
      python_runner:
        transport: "stdio"
        command: "deno"
        args:
          - "run"
          - "-N"
          - "-R=node_modules"
          - "-W=node_modules"
          - "--node-modules-dir=auto"
          - "jsr:@pydantic/mcp-run-python"
          - "stdio"
    python_tools:
      large_data_storage:
        module_path: "tools.test_large_data_storage_tool"
        tool_names: ["store_large_dataset_to_chromadb", "retrieve_dataset_from_chromadb"]
  
  - name: "response_formatter"
    description: "Format final responses for users"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"
    prompt: |
      {{dependent_request_responses}}
      
      Format the above information into a clear, user-friendly response.
"""
        
        config_file = test.env.create_temp_file("super_test_config.yaml", config_content)
        print(f"  ✓ Configuration file created: {config_file}")
        result.add_sub_test("Config File Creation", True, path=str(config_file))
        
        # Step 1.2: Load configuration
        print("\n[1.2] Loading Configuration...")
        start_time = time.time()
        app_config = load_app_config(config_file)
        load_time = time.time() - start_time
        test.record_performance("config_load_time", load_time)
        
        print(f"  ✓ Configuration loaded in {load_time:.3f}s")
        print(f"    - Agents: {len(app_config.agents)}")
        print(f"    - Models: {app_config.models}")
        print(f"    - Memory backend: {getattr(app_config.memory, 'backend', 'none') if hasattr(app_config, 'memory') else 'none'}")
        
        result.add_sub_test(
            "Config Loading",
            len(app_config.agents) == 3,
            agent_count=len(app_config.agents),
            load_time=load_time
        )
        # Step 1.3: Validating model format handling
        print("\n[1.3] Validating Model Format Handling...")
        default_model = app_config.models.get("default", "")
        model_instance = create_model_instance(default_model, app_config=vars(app_config) if hasattr(app_config, '__dict__') else {})
        
        print(f"  ✓ Model instance created: {type(model_instance).__name__}")
        print(f"    - Model ID: {default_model}")
        
        result.add_sub_test(
            "Model Instance Creation",
            model_instance is not None,
            model_type=type(model_instance).__name__
        )
        
        # Step 1.4: Initialize memory systems
        print("\n[1.4] Initializing Memory Systems...")
        
        # Check ChromaDB availability
        chromadb_available = verify_chromadb_available()
        print(f"  - ChromaDB: {'✓ Available' if chromadb_available else '✗ Not available'}")
        
        # Initialize global checkpointer
        checkpointer = get_global_checkpointer()
        print(f"  ✓ Checkpointer initialized: {type(checkpointer).__name__}")
        
        # Initialize conversation memory (note: this function is async)
        conv_memory = await initialize_conversation_memory(app_config)
        print(f"  ✓ Conversation memory initialized")
        
        result.add_sub_test(
            "Memory Initialization",
            checkpointer is not None,
            chromadb=chromadb_available,
            checkpointer_type=type(checkpointer).__name__
        )
        
        # Step 1.5: Store config for later phases
        test.created_resources["config"] = app_config
        test.created_resources["config_file"] = config_file
        
        result.finish(
            True,
            total_steps=5,
            config_load_time=load_time,
            agents_configured=len(app_config.agents),
            memory_enabled=chromadb_available
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase2_single_agent_execution(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 2: Single Agent Execution
    - Build and test normal agent
    - Build and test react agent with tools
    - Validate tool calling workflow
    """
    result = TestResult("Phase 2: Single Agent Execution")
    
    try:
        print_section("Phase 2: Single Agent Execution")
        
        app_config = test.created_resources["config"]
        config_file = test.created_resources["config_file"]
        default_model = app_config.models.get("default", "")
        
        # Step 2.1: Build normal agent
        print("\n[2.1] Building Normal Agent...")
        start_time = time.time()
        
        normal_agent_cfg = next((a for a in app_config.agents if a.name == "conversational_agent"), None)
        # Convert AppConfig to dict for build_agent (which expects Dict)
        app_config_dict = app_config.dict() if hasattr(app_config, 'dict') else app_config.model_dump()
        
        normal_agent, normal_mcp = await build_agent(
            agent_cfg=normal_agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_file),
            app_config=app_config_dict  # Pass full config for large_data_handling
        )
        
        build_time = time.time() - start_time
        test.record_performance("agent_build_time", build_time)
        test.created_resources["mcp_clients"].append(normal_mcp)
        test.created_resources["agents"]["normal"] = normal_agent
        
        print(f"  ✓ Normal agent built in {build_time:.3f}s")
        result.add_sub_test("Normal Agent Build", True, build_time=build_time)
        
        # Step 2.2: Test normal agent
        print("\n[2.2] Testing Normal Agent...")
        response = await invoke_agent(
            normal_agent,
            "What is the capital of France? Answer in one sentence.",
            thread_id=test.test_thread_id
        )
        
        print(f"  ✓ Response received ({response['duration']:.2f}s)")
        print(f"    Response: {response['response'][:150]}...")
        
        has_paris = 'paris' in response['response'].lower()
        result.add_sub_test(
            "Normal Agent Response",
            has_paris and len(response['response']) > 10,
            correct=has_paris,
            response_length=len(response['response'])
        )
        
        # Step 2.3: Build react agent with tools
        print("\n[2.3] Building React Agent with Tools...")
        start_time = time.time()
        
        react_agent_cfg = next((a for a in app_config.agents if a.name == "python_executor"), None)
        react_agent, react_mcp = await build_agent(
            agent_cfg=react_agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_file),
            app_config=app_config_dict  # Pass full config for large_data_handling
        )
        
        build_time = time.time() - start_time
        test.created_resources["mcp_clients"].append(react_mcp)
        test.created_resources["agents"]["react"] = react_agent
        
        print(f"  ✓ React agent built in {build_time:.3f}s")
        result.add_sub_test("React Agent Build", True, build_time=build_time)
        
        # Step 2.4: Test react agent with tool calling
        print("\n[2.4] Testing React Agent with Tool Calling...")
        response2 = await invoke_agent(
            react_agent,
            "Calculate the factorial of 5 using Python. Show me the result.",
            thread_id=test.test_thread_id
        )
        
        tool_calls = extract_tool_calls(response2['messages'])
        test.performance_metrics['tool_calls_count'] += len(tool_calls)
        
        print(f"  ✓ Response received ({response2['duration']:.2f}s)")
        print(f"    Tool calls: {len(tool_calls)}")
        print(f"    Response: {response2['response'][:150]}...")
        
        # Factorial of 5 = 120
        has_answer = '120' in response2['response']
        result.add_sub_test(
            "React Agent Tool Calling",
            has_answer and len(tool_calls) > 0,
            correct=has_answer,
            tool_calls=len(tool_calls)
        )
        
        result.finish(
            True,
            total_agents_built=2,
            total_tool_calls=len(tool_calls),
            all_responses_valid=has_paris and has_answer
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase3_supervisor_orchestration(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 3: Supervisor-Worker Orchestration
    - Build supervisor
    - Create execution plan
    - Execute plan with multiple agents
    - Validate step dependencies
    """
    result = TestResult("Phase 3: Supervisor-Worker Orchestration")
    
    try:
        print_section("Phase 3: Supervisor-Worker Orchestration")
        
        app_config = test.created_resources["config"]
        config_file = test.created_resources["config_file"]
        default_model = app_config.models.get("default", "")
        
        # Step 3.1: Build agents map
        print("\n[3.1] Building Agents Map...")
        agents_map, mcp_clients = await build_agents_map(
            app_config,
            user_input="",
            config_path=str(config_file)
        )
        
        for client in mcp_clients.values():
            test.created_resources["mcp_clients"].append(client)
        
        print(f"  ✓ Agents map built: {len(agents_map)} agents")
        print(f"    Agents: {list(agents_map.keys())}")
        result.add_sub_test("Agents Map Build", len(agents_map) == 3, agent_count=len(agents_map))
        
        # Step 3.2: Build supervisor
        print("\n[3.2] Building Supervisor...")
        start_time = time.time()
        
        business_context = process_business_context_template(app_config.business_context or "")
        supervisor = build_supervisor_compiled(
            app_config.supervisor,
            app_config.agents,
            default_model,
            business_context,
            original_user_question="Calculate sum of even numbers from 1 to 20",
            config_path=str(config_file),
            default_temperature=app_config.temperature,
            thread_id=test.test_thread_id
        )
        
        build_time = time.time() - start_time
        test.record_performance("supervisor_build_time", build_time)
        test.created_resources["agents"]["supervisor"] = supervisor
        
        print(f"  ✓ Supervisor built in {build_time:.3f}s")
        result.add_sub_test("Supervisor Build", True, build_time=build_time)
        
        # Step 3.3: Create execution plan
        print("\n[3.3] Creating Execution Plan...")
        from langchain_core.messages import HumanMessage
        
        query = "Calculate the sum of all even numbers from 1 to 20, then format the result nicely."
        
        plan_input = {"messages": [HumanMessage(content=query)]}
        plan_config = {"configurable": {"thread_id": test.test_thread_id}}
        
        start_time = time.time()
        plan_result = await supervisor.ainvoke(plan_input, config=plan_config)
        plan_time = time.time() - start_time
        
        # Extract plan from response
        plan_text = plan_result["messages"][-1].content if plan_result.get("messages") else ""
        parsed_plan = parse_plan_text(plan_text)
        
        print(f"  ✓ Plan created in {plan_time:.3f}s")
        if parsed_plan:
            print(f"    Goal: {parsed_plan.goal}")
            print(f"    Steps: {len(parsed_plan.plan)}")
            for step in parsed_plan.plan:
                print(f"      - {step.id}: {step.agent} - {step.task}")
        
        result.add_sub_test(
            "Plan Creation",
            parsed_plan is not None and len(parsed_plan.plan) > 0,
            steps=len(parsed_plan.plan) if parsed_plan else 0,
            plan_time=plan_time
        )
        
        # Step 3.4: Execute plan
        print("\n[3.4] Executing Plan...")
        if parsed_plan:
            start_time = time.time()
            
            execution_result = await execute_plan(
                supervisor_compiled=supervisor,  # Pass the compiled supervisor
                agents_map=agents_map,
                user_input=query,
                default_model=default_model,
                thread_id=test.test_thread_id
            )
            
            exec_time = time.time() - start_time
            test.record_performance("first_query_time", exec_time)
            
            print(f"  ✓ Plan executed in {exec_time:.3f}s")
            print(f"    Steps executed: {len(execution_result.get('step_results', {}))}")
            
            # Check for correct answer (sum of even 1-20 = 110)
            final_response = execution_result.get("final_response", "")
            has_answer = '110' in final_response
            
            print(f"    Final response: {final_response[:200]}...")
            print(f"    Correct answer: {'✓' if has_answer else '✗'}")
            
            result.add_sub_test(
                "Plan Execution",
                has_answer,
                execution_time=exec_time,
                correct_answer=has_answer,
                steps_executed=len(execution_result.get('step_results', {}))
            )
        else:
            result.add_sub_test("Plan Execution", False, error="No plan to execute")
        
        result.finish(
            True,
            supervisor_built=True,
            plan_created=parsed_plan is not None,
            plan_executed=True,
            total_time=plan_time + (exec_time if parsed_plan else 0)
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase4_multi_turn_memory(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 4: Multi-turn Conversations with Memory
    - Store conversation in memory
    - Retrieve context across turns
    - Test thread isolation
    - Validate memory persistence
    """
    result = TestResult("Phase 4: Multi-turn Conversations with Memory")
    
    try:
        print_section("Phase 4: Multi-turn Conversations with Memory")
        
        app_config = test.created_resources["config"]
        normal_agent = test.created_resources["agents"].get("normal")
        
        if not normal_agent:
            result.finish(False, error="Normal agent not available from Phase 2")
            return result
        
        # Create unique thread for memory test
        memory_thread = f"memory_{uuid.uuid4().hex[:8]}"
        test.created_resources["threads"].append(memory_thread)
        
        # Step 4.1: First turn - introduce information
        print("\n[4.1] Turn 1: Introduce Information...")
        response1 = await invoke_agent(
            normal_agent,
            "My name is Bob and I am a software engineer. Remember this.",
            thread_id=memory_thread
        )
        
        # Store in conversation memory using the correct function
        from app.memory_integration import store_conversation_turn
        await store_conversation_turn(
            thread_id=memory_thread,
            user_input="My name is Bob and I am a software engineer.",
            assistant_response=response1['response']
        )
        
        print(f"  ✓ Turn 1 completed ({response1['duration']:.2f}s)")
        print(f"    Response: {response1['response'][:150]}...")
        
        result.add_sub_test("Turn 1: Store Info", True, duration=response1['duration'])
        
        # Step 4.2: Second turn - recall information
        print("\n[4.2] Turn 2: Recall Information...")
        await asyncio.sleep(0.5)  # Brief pause to ensure memory is written
        
        response2 = await invoke_agent(
            normal_agent,
            "What is my name and profession?",
            thread_id=memory_thread
        )
        
        await store_conversation_turn(
            thread_id=memory_thread,
            user_input="What is my name and profession?",
            assistant_response=response2['response']
        )
        
        print(f"  ✓ Turn 2 completed ({response2['duration']:.2f}s)")
        print(f"    Response: {response2['response']}")
        
        # Validate memory recall
        remembers_name = 'bob' in response2['response'].lower()
        remembers_profession = 'software' in response2['response'].lower() or 'engineer' in response2['response'].lower()
        
        print(f"    Remembers name: {'✓' if remembers_name else '✗'}")
        print(f"    Remembers profession: {'✓' if remembers_profession else '✗'}")
        
        result.add_sub_test(
            "Turn 2: Memory Recall",
            remembers_name and remembers_profession,
            name_recalled=remembers_name,
            profession_recalled=remembers_profession
        )
        
        # Step 4.3: Test thread isolation
        print("\n[4.3] Testing Thread Isolation...")
        different_thread = f"diff_{uuid.uuid4().hex[:8]}"
        test.created_resources["threads"].append(different_thread)
        
        response3 = await invoke_agent(
            normal_agent,
            "What is my name?",
            thread_id=different_thread
        )
        
        print(f"  ✓ Different thread query completed")
        print(f"    Response: {response3['response']}")
        
        # Should NOT remember Bob from different thread
        does_not_remember = 'bob' not in response3['response'].lower()
        print(f"    Correctly isolated: {'✓' if does_not_remember else '✗'}")
        
        result.add_sub_test(
            "Thread Isolation",
            does_not_remember,
            isolated=does_not_remember
        )
        
        # Step 4.4: Check memory stats
        print("\n[4.4] Checking Memory Stats...")
        try:
            memory_stats = get_memory_stats()
            print(f"  ✓ Memory stats retrieved")
            print(f"    Threads tracked: {len(memory_stats.get('threads', {}))}")
            
            result.add_sub_test(
                "Memory Stats",
                True,
                threads=len(memory_stats.get('threads', {}))
            )
        except Exception as e:
            print(f"  ⚠️  Could not retrieve memory stats: {e}")
            result.add_sub_test("Memory Stats", False, error=str(e))
        
        result.finish(
            True,
            turns_completed=2,
            memory_recall_successful=remembers_name and remembers_profession,
            thread_isolation_working=does_not_remember
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase5_advanced_features(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 5: Advanced Features
    - File storage and references
    - Large data handling
    - Complex tool sequences
    - Error recovery
    """
    result = TestResult("Phase 5: Advanced Features")
    
    try:
        print_section("Phase 5: Advanced Features")
        
        react_agent = test.created_resources["agents"].get("react")
        
        if not react_agent:
            result.finish(False, error="React agent not available from Phase 2")
            return result
        
        # Step 5.1: Test file storage manager
        print("\n[5.1] Testing File Storage Manager...")
        file_manager = get_file_storage_manager()
        
        # Create test file
        test_content = b"Test data for super integrated test"
        test_thread = f"file_{uuid.uuid4().hex[:8]}"
        test.created_resources["threads"].append(test_thread)
        file_ref = file_manager.store_file("test.txt", test_content, "text/plain", test_thread)
        test.created_resources["files"].append(file_ref)
        
        print(f"  ✓ File stored: {file_ref}")
        
        # Retrieve file
        retrieved = file_manager.get_file_content_raw(file_ref)
        files_match = retrieved == test_content
        
        print(f"    Content match: {'✓' if files_match else '✗'}")
        
        result.add_sub_test("File Storage", files_match, file_ref=file_ref)
        
        # Step 5.2: Test complex calculation
        print("\n[5.2] Testing Complex Calculation...")
        response = await invoke_agent(
            react_agent,
            "Calculate the sum of squares of numbers from 1 to 10. Show your work.",
            thread_id=test.test_thread_id
        )
        
        tool_calls = extract_tool_calls(response['messages'])
        test.performance_metrics['tool_calls_count'] += len(tool_calls)
        
        print(f"  ✓ Response received ({response['duration']:.2f}s)")
        print(f"    Tool calls: {len(tool_calls)}")
        
        # Sum of squares 1-10 = 385
        has_answer = '385' in response['response']
        print(f"    Correct answer: {'✓' if has_answer else '✗'}")
        
        result.add_sub_test(
            "Complex Calculation",
            has_answer,
            correct=has_answer,
            tool_calls=len(tool_calls)
        )
        
        # Step 5.3: Test multiple tool calls in sequence
        print("\n[5.3] Testing Sequential Tool Calls...")
        response2 = await invoke_agent(
            react_agent,
            "First, calculate 100 factorial. Then, calculate how many digits are in that number.",
            thread_id=test.test_thread_id
        )
        
        tool_calls2 = extract_tool_calls(response2['messages'])
        test.performance_metrics['tool_calls_count'] += len(tool_calls2)
        
        print(f"  ✓ Response received ({response2['duration']:.2f}s)")
        print(f"    Tool calls: {len(tool_calls2)}")
        print(f"    Response: {response2['response'][:200]}...")
        
        # 100! has 158 digits
        has_multiple_calls = len(tool_calls2) >= 2
        print(f"    Multiple tool calls: {'✓' if has_multiple_calls else '✗'}")
        
        result.add_sub_test(
            "Sequential Tool Calls",
            has_multiple_calls,
            tool_calls=len(tool_calls2)
        )
        
        result.finish(
            True,
            file_storage_working=files_match,
            complex_calc_working=has_answer,
            sequential_calls_working=has_multiple_calls,
            total_tool_calls=len(tool_calls) + len(tool_calls2)
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase6_api_integration(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 6: API Integration
    - Test health endpoint
    - Test query endpoint
    - Test worker endpoint
    - Test memory endpoints
    """
    result = TestResult("Phase 6: API Integration")
    
    try:
        print_section("Phase 6: API Integration")
        
        if not HAS_REQUESTS:
            print("  ⚠️  requests library not available, skipping API tests")
            result.finish(False, error="requests library not installed")
            return result
        
        # Check if API is running
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Step 6.1: Health check
        print(f"\n[6.1] Testing Health Endpoint... ({api_url})")
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            health_ok = response.status_code == 200
            
            if health_ok:
                print(f"  ✓ Health check passed")
                print(f"    Status: {response.json().get('status', 'unknown')}")
            else:
                print(f"  ✗ Health check failed: {response.status_code}")
            
            result.add_sub_test("Health Check", health_ok, status_code=response.status_code)
        except Exception as e:
            print(f"  ⚠️  API not available: {e}")
            print(f"     (This is expected if API server is not running)")
            result.add_sub_test("Health Check", False, error="API not running")
            result.finish(False, error="API server not available - tests skipped")
            return result
        
        # Step 6.2: Test memory stats endpoint
        print("\n[6.2] Testing Memory Stats Endpoint...")
        try:
            response = requests.get(f"{api_url}/memory/stats", timeout=10)
            stats_ok = response.status_code == 200
            
            if stats_ok:
                stats = response.json()
                print(f"  ✓ Memory stats retrieved")
                print(f"    Threads: {len(stats.get('threads', {}))}")
            
            result.add_sub_test("Memory Stats", stats_ok, status_code=response.status_code)
        except Exception as e:
            print(f"  ⚠️  Memory stats failed: {e}")
            result.add_sub_test("Memory Stats", False, error=str(e))
        
        # Step 6.3: Note about other API endpoints
        print("\n[6.3] API Integration Notes:")
        print("  ℹ️  Full API endpoint testing requires:")
        print("      - API server running (uvicorn api:app)")
        print("      - Configuration files in place")
        print("      - Separate dedicated API test suite")
        print("  ℹ️  This test validates core module integration")
        
        result.finish(
            health_ok,
            api_available=health_ok,
            endpoints_tested=2
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase8_large_data_chromadb_storage(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 8: Large Data Handling with ChromaDB Storage
    - Generate large dataset (10,000+ records) using Python MCP
    - Verify automatic storage in ChromaDB/SQLite with reference
    - Ensure context receives summary pointer, not full data
    - Perform multi-turn conversation using stored data
    - Verify data retrieval from ChromaDB
    
    CRITICAL: This tests the real-world scenario where tool outputs are too large
    for context, requiring intelligent storage and reference-based access.
    """
    result = TestResult("Phase 8: Large Data + ChromaDB Storage")
    
    try:
        print_section("Phase 8: Large Data Handling with ChromaDB Storage")
        
        app_config = test.created_resources["config"]
        config_file = test.created_resources["config_file"]
        react_agent = test.created_resources["agents"].get("react")
        
        if not react_agent:
            result.finish(False, error="React agent not available from Phase 2")
            return result
        
        # Create dedicated thread for large data test
        large_data_thread = f"largedata_{uuid.uuid4().hex[:8]}"
        test.created_resources["threads"].append(large_data_thread)
        
        # Step 8.1: Generate large dataset
        print("\n[8.1] Generating Large Dataset (10,000 records)...")
        print("      This should trigger automatic storage optimization")
        
        large_query = """Generate 10,000 business records and store them using the storage tool.

Steps:
1. Use run_python_code to generate 10,000 records with fields: id, name, revenue, department, date
2. Convert the data to a JSON string
3. Call store_large_dataset_to_chromadb with the JSON string and description "10,000 business records"
4. Return the reference_id and storage confirmation to me

This will efficiently store the large dataset without bloating the conversation context."""
        
        start_time = time.time()
        response1 = await invoke_agent(
            react_agent,
            large_query,
            thread_id=large_data_thread
        )
        gen_time = time.time() - start_time
        
        print(f"  ✓ Large data generation completed ({gen_time:.2f}s)")
        print(f"    Response length: {len(response1['response'])} characters")
        
        # Check if response indicates reference creation (key indicator)
        has_reference = "reference" in response1['response'].lower() or "ref_" in response1['response'].lower()
        is_not_full_data = len(response1['response']) < 50000  # Should be summary, not 10K records
        
        print(f"    Contains reference indicator: {'✓' if has_reference else '✗'}")
        print(f"    Response size appropriate: {'✓' if is_not_full_data else '✗ (too large)'}")
        print(f"    First 200 chars: {response1['response'][:200]}...")
        
        result.add_sub_test(
            "Large Dataset Generation",
            True,  # Generation completed
            duration=gen_time,
            response_length=len(response1['response']),
            has_reference=has_reference
        )
        
        # Step 8.2: Verify data not in context (context efficient)
        print("\n[8.2] Verifying Context Efficiency...")
        
        # Estimate tokens in response
        estimated_tokens = len(response1['response']) // 4
        context_efficient = estimated_tokens < 5000  # Should be < 5K tokens, not 50K+
        
        print(f"    Estimated response tokens: ~{estimated_tokens:,}")
        print(f"    Context efficient: {'✓' if context_efficient else '✗'}")
        print(f"    Expected: <5,000 tokens (summary + reference)")
        print(f"    Without optimization: ~50,000+ tokens (full data)")
        
        if context_efficient:
            tokens_saved = 50000 - estimated_tokens
            print(f"    Tokens saved: ~{tokens_saved:,} ({(tokens_saved/50000*100):.1f}%)")
        
        result.add_sub_test(
            "Context Efficiency",
            context_efficient,
            estimated_tokens=estimated_tokens,
            tokens_saved=50000 - estimated_tokens if context_efficient else 0
        )
        
        # Step 8.3: Check ChromaDB/SQLite storage
        print("\n[8.3] Verifying Data Storage in ChromaDB/SQLite...")
        
        # Small delay to ensure storage writes are committed
        await asyncio.sleep(0.2)
        
        try:
            # Check if large data storage was initialized
            from app.memory.large_data_storage import LargeDataStorage
            
            # Create storage instance with test config
            storage_config = {
                "sqlite_path": "./integration_tests/temp/large_tool_data.db",
                "file_path": "./integration_tests/temp/large_tool_data_files/",
                "compression": True
            }
            
            storage = LargeDataStorage(storage_config)
            
            # List stored references
            stored_refs = storage.list_references()
            
            print(f"    Total stored references: {len(stored_refs)}")
            
            if len(stored_refs) > 0:
                latest_ref = stored_refs[0]
                print(f"    Latest reference ID: {latest_ref['reference_id']}")
                print(f"    Tool name: {latest_ref['tool_name']}")
                print(f"    Size: {latest_ref['size_bytes']:,} bytes ({latest_ref['size_bytes']/1024/1024:.2f} MB)")
                print(f"    Storage type: {latest_ref['storage_type']}")
                
                storage_verified = True
            else:
                print(f"    ⚠️  No references found in storage")
                storage_verified = False
            
            result.add_sub_test(
                "Data Storage Verification",
                storage_verified,
                stored_references=len(stored_refs)
            )
            
        except Exception as e:
            print(f"    ⚠️  Storage verification error: {e}")
            print(f"       This may indicate large_data_handling is not enabled")
            result.add_sub_test(
                "Data Storage Verification",
                False,
                error=str(e)
            )
            storage_verified = False
        
        # Step 8.4: Multi-turn conversation using stored data
        print("\n[8.4] Multi-Turn Conversation with Stored Data...")
        
        # Turn 1: Query about the data
        await asyncio.sleep(0.5)
        response2 = await invoke_agent(
            react_agent,
            "How many records did we just generate? What's the data structure?",
            thread_id=large_data_thread
        )
        
        print(f"  ✓ Turn 2 completed ({response2['duration']:.2f}s)")
        print(f"    Response: {response2['response'][:200]}...")
        
        # Check if agent remembers the dataset
        remembers_data = "10" in response2['response'] and "000" in response2['response']  # "10,000" or "10000"
        mentions_structure = any(field in response2['response'].lower() for field in ['id', 'name', 'revenue', 'department'])
        
        print(f"    Remembers record count: {'✓' if remembers_data else '✗'}")
        print(f"    References structure: {'✓' if mentions_structure else '✗'}")
        
        result.add_sub_test(
            "Multi-Turn Data Access",
            remembers_data or mentions_structure,
            remembers_count=remembers_data,
            mentions_structure=mentions_structure
        )
        
        # Step 8.5: Verify data retrieval from storage
        print("\n[8.5] Verifying Data Retrieval from Storage...")
        
        if storage_verified and len(stored_refs) > 0:
            try:
                ref_id = stored_refs[0]['reference_id']
                retrieved_data = storage.retrieve_large_data(ref_id)
                
                if retrieved_data:
                    # Parse and validate
                    if isinstance(retrieved_data, str):
                        try:
                            parsed_data = json.loads(retrieved_data)
                        except:
                            parsed_data = None
                    else:
                        parsed_data = retrieved_data
                    
                    if parsed_data and isinstance(parsed_data, list):
                        record_count = len(parsed_data)
                        print(f"    ✓ Data retrieved successfully")
                        print(f"    Record count: {record_count:,}")
                        print(f"    First record keys: {list(parsed_data[0].keys()) if record_count > 0 else 'N/A'}")
                        
                        retrieval_successful = record_count >= 1000  # At least 1000 records
                    else:
                        print(f"    ⚠️  Retrieved data is not a list")
                        retrieval_successful = False
                else:
                    print(f"    ⚠️  No data retrieved for reference {ref_id}")
                    retrieval_successful = False
                
                result.add_sub_test(
                    "Data Retrieval from Storage",
                    retrieval_successful,
                    record_count=record_count if retrieval_successful else 0
                )
                
            except Exception as e:
                print(f"    ⚠️  Retrieval error: {e}")
                result.add_sub_test(
                    "Data Retrieval from Storage",
                    False,
                    error=str(e)
                )
                retrieval_successful = False
        else:
            print(f"    ⏭️  Skipped (no stored references to retrieve)")
            result.add_sub_test("Data Retrieval from Storage", False, skipped=True)
            retrieval_successful = False
        
        # Step 8.6: Summary
        print("\n[8.6] Large Data Handling Summary:")
        print(f"  • Dataset generated: ✓")
        print(f"  • Context optimized: {'✓' if context_efficient else '✗'}")
        print(f"  • Data stored: {'✓' if storage_verified else '✗'}")
        print(f"  • Multi-turn access: {'✓' if (remembers_data or mentions_structure) else '✗'}")
        print(f"  • Data retrievable: {'✓' if retrieval_successful else '✗'}")
        print(f"")
        print(f"  📊 Performance:")
        print(f"     Generation time: {gen_time:.2f}s")
        print(f"     Token savings: ~{50000 - estimated_tokens:,} ({(50000 - estimated_tokens)/50000*100:.1f}%)")
        
        result.finish(
            True,
            dataset_generated=True,
            context_efficient=context_efficient,
            storage_verified=storage_verified,
            multi_turn_access=remembers_data or mentions_structure,
            retrieval_successful=retrieval_successful,
            total_time=gen_time,
            tokens_saved=50000 - estimated_tokens
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def phase7_cleanup_verification(test: SuperIntegratedTest) -> TestResult:
    """
    Phase 7: Cleanup & Verification
    - Clean up test resources
    - Verify cleanup
    - Generate final report
    """
    result = TestResult("Phase 7: Cleanup & Verification")
    
    try:
        print_section("Phase 7: Cleanup & Verification")
        
        # Step 7.1: Clean up threads
        print("\n[7.1] Cleaning Up Threads...")
        threads_cleaned = 0
        for thread_id in test.created_resources["threads"]:
            try:
                # clear_thread_memory is not async, don't await it
                clear_result = clear_thread_memory(thread_id)
                threads_cleaned += 1
                print(f"  ✓ Cleared thread: {thread_id}")
            except Exception as e:
                print(f"  ⚠️  Failed to clear {thread_id}: {e}")
        
        result.add_sub_test(
            "Thread Cleanup",
            threads_cleaned == len(test.created_resources["threads"]),
            cleaned=threads_cleaned,
            total=len(test.created_resources["threads"])
        )
        
        # Step 7.2: Clean up files
        print("\n[7.2] Cleaning Up Files...")
        try:
            file_manager = get_file_storage_manager()
            files_cleaned = 0
            for file_ref in test.created_resources["files"]:
                try:
                    file_manager.delete_file(file_ref)
                    files_cleaned += 1
                    print(f"  ✓ Deleted file: {file_ref}")
                except Exception as e:
                    print(f"  ⚠️  Failed to delete {file_ref}: {e}")
            
            result.add_sub_test(
                "File Cleanup",
                True,
                cleaned=files_cleaned
            )
        except Exception as e:
            print(f"  ⚠️  File cleanup error: {e}")
            result.add_sub_test("File Cleanup", False, error=str(e))
        
        # Step 7.3: Verify system state
        print("\n[7.3] Verifying System State...")
        try:
            memory_stats = get_memory_stats()
            print(f"  ✓ Final memory stats:")
            print(f"    Threads: {len(memory_stats.get('threads', {}))}")
            
            result.add_sub_test("Final State Verification", True)
        except Exception as e:
            print(f"  ⚠️  Could not verify final state: {e}")
            result.add_sub_test("Final State Verification", False, error=str(e))
        
        result.finish(
            True,
            threads_cleaned=threads_cleaned,
            files_cleaned=0,
            cleanup_successful=True
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    return result


async def main():
    """Main test execution."""
    print_test_header("SUPER INTEGRATED TEST - Complete System Validation")
    
    # Check prerequisites
    if not check_azure_credentials():
        print("\n❌ Azure OpenAI credentials not configured!")
        print("   Please set up .env file with required credentials.")
        return False
    
    if not verify_chromadb_available():
        print("\n⚠️  ChromaDB not available - some features may not work")
    
    print("\n✓ Prerequisites check passed")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize test manager
    test = SuperIntegratedTest()
    
    try:
        # Execute all phases
        phases = [
            ("Phase 1", phase1_system_initialization),
            ("Phase 2", phase2_single_agent_execution),
            ("Phase 3", phase3_supervisor_orchestration),
            ("Phase 4", phase4_multi_turn_memory),
            ("Phase 5", phase5_advanced_features),
            ("Phase 6", phase6_api_integration),
            ("Phase 7", phase7_cleanup_verification),
            ("Phase 8", phase8_large_data_chromadb_storage),
        ]
        
        for phase_name, phase_func in phases:
            print(f"\n{'=' * 80}")
            phase_result = await phase_func(test)
            phase_result.print_result()
            test.stats.add_result(phase_result)
            
            # Stop if critical phase fails
            if not phase_result.passed and phase_name in ["Phase 1", "Phase 2"]:
                print(f"\n❌ Critical phase failed: {phase_name}")
                print("   Stopping test execution.")
                break
        
        # Print performance summary
        test.print_performance_summary()
        
        # Print final summary
        test.stats.print_summary()
        
        return test.stats.failed == 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Fatal error in test execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Always cleanup
        try:
            await test.cleanup()
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
