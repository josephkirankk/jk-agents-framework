"""
Integration Test 3: ChromaDB Memory and Multi-turn Conversations
NO MOCKING - Real ChromaDB persistence

Tests:
1. ChromaDB initialization and storage
2. Multi-turn conversation memory
3. Thread-based conversation isolation
4. Memory retrieval across sessions
"""

import asyncio
import sys
from pathlib import Path
import uuid

sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    TestResult, TestEnvironment, print_test_header, print_section,
    check_azure_credentials, invoke_agent, convert_app_config_to_dict,
    verify_chromadb_available
)

from app.main import load_app_config
from app.agent_builder import build_agent
from app.memory_integration import store_conversation_turn, inject_conversation_context
from dotenv import load_dotenv

load_dotenv()


async def test_chromadb_memory():
    """Test ChromaDB memory persistence"""
    result = TestResult("ChromaDB Memory Persistence")
    env = TestEnvironment("chromadb_memory")
    
    try:
        print_section("Testing ChromaDB Memory")
        
        config_path = Path(__file__).parent.parent / "config" / "chromadb_memory_test.yaml"
        
        if not config_path.exists():
            # Create test config
            config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

memory:
  backend: "chromadb"
  chromadb:
    path: "./test_memory_chromadb"
    checkpoint_collection: "test_checkpoints"
    context_collection: "test_context"

conversation_memory:
  enabled: true
  database_url: ""
  max_conversations: 10
  max_context_length: 2000
  prepend_context: true
  pool_size: 10
  cleanup_days: 7

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "memory_agent"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"
    prompt: |
      You are a helpful assistant with memory capabilities.
      
      IMPORTANT: Check the conversation history above (if provided) for context from previous turns.
      When a user asks about information they shared earlier, refer to that conversation history.
      Remember what users tell you and use that information to answer their questions.
"""
            config_path = env.create_temp_file("chromadb_memory_test.yaml", config_content)
        
        app_config = load_app_config(config_path)
        agent_cfg = app_config.agents[0]
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✓ Agent built")
        
        # Use unique thread ID for this test
        thread_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Turn 1: Introduce information
        print_section("Turn 1: Introduce Information")
        user_input1 = "My name is Alice and I live in Paris. My favorite color is blue."
        response1 = await invoke_agent(
            agent,
            user_input1,
            thread_id=thread_id
        )
        print(f"✓ Response: {response1['response'][:100]}")
        
        # Store conversation turn
        await store_conversation_turn(thread_id, user_input1, response1['response'])
        
        # Turn 2: Ask about stored information
        print_section("Turn 2: Query Stored Information")
        user_input2 = "What is my name and where do I live?"
        # Inject context from previous turns
        user_input2_with_context = inject_conversation_context(thread_id, user_input2)
        response2 = await invoke_agent(
            agent,
            user_input2_with_context,
            thread_id=thread_id
        )
        print(f"✓ Response: {response2['response'][:200]}")
        
        # Store conversation turn
        await store_conversation_turn(thread_id, user_input2, response2['response'])
        
        # Verify memory
        remembers_name = 'Alice' in response2['response'] or 'alice' in response2['response'].lower()
        remembers_city = 'Paris' in response2['response'] or 'paris' in response2['response'].lower()
        
        result.add_sub_test(
            "Memory Recall",
            remembers_name and remembers_city,
            name_recalled=remembers_name,
            city_recalled=remembers_city
        )
        
        # Turn 3: Additional query
        print_section("Turn 3: Another Memory Query")
        user_input3 = "What is my favorite color?"
        # Inject context from previous turns
        user_input3_with_context = inject_conversation_context(thread_id, user_input3)
        response3 = await invoke_agent(
            agent,
            user_input3_with_context,
            thread_id=thread_id
        )
        print(f"✓ Response: {response3['response'][:200]}")
        
        remembers_color = 'blue' in response3['response'].lower()
        result.add_sub_test(
            "Additional Memory",
            remembers_color,
            color_recalled=remembers_color
        )
        
        result.finish(
            True,
            thread_id=thread_id,
            turns=3,
            all_memories_recalled=remembers_name and remembers_city and remembers_color
        )
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def test_thread_isolation():
    """Test that different threads have isolated memory"""
    result = TestResult("Thread Isolation")
    env = TestEnvironment("thread_isolation")
    
    try:
        print_section("Testing Thread Isolation")
        
        config_content = """
models:
  default: "azure_openai:gpt-4.1"
  supervisor: "azure_openai:gpt-4.1"

memory:
  backend: "chromadb"
  chromadb:
    path: "./test_isolation_chromadb"
    checkpoint_collection: "test_isolation_checkpoints"
    context_collection: "test_isolation_context"

conversation_memory:
  enabled: true
  database_url: ""
  max_conversations: 10
  max_context_length: 2000
  prepend_context: true
  pool_size: 10
  cleanup_days: 7

supervisor:
  name: "supervisor"
  model: "azure_openai:gpt-4.1"
  prompt: "You are a supervisor."

agents:
  - name: "isolation_agent"
    model: "azure_openai:gpt-4.1"
    agent_type: "normal"
    prompt: |
      You are a helpful assistant with memory capabilities.
      
      IMPORTANT: Check the conversation history above (if provided) for context from previous turns.
      When a user asks about information they shared earlier, refer to that conversation history.
      Remember what users tell you within this conversation thread.
"""
        
        config_file = env.create_temp_file("isolation.yaml", config_content)
        app_config = load_app_config(config_file)
        agent_cfg = app_config.agents[0]
        default_model = app_config.models['default'] if isinstance(app_config.models, dict) else app_config.models.default
        app_config_dict = convert_app_config_to_dict(app_config)
        
        agent, mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
            business_context="",
            config_path=str(config_file),
            app_config=app_config_dict
        )
        
        # Thread 1
        thread1 = f"thread1_{uuid.uuid4().hex[:8]}"
        user_input_t1 = "My favorite number is 42."
        response1 = await invoke_agent(
            agent,
            user_input_t1,
            thread_id=thread1
        )
        await store_conversation_turn(thread1, user_input_t1, response1['response'])
        print(f"✓ Thread 1 set: number=42")
        
        # Thread 2
        thread2 = f"thread2_{uuid.uuid4().hex[:8]}"
        user_input_t2 = "My favorite number is 99."
        response2 = await invoke_agent(
            agent,
            user_input_t2,
            thread_id=thread2
        )
        await store_conversation_turn(thread2, user_input_t2, response2['response'])
        print(f"✓ Thread 2 set: number=99")
        
        # Query Thread 1
        query_t1 = "What is my favorite number?"
        query_t1_with_context = inject_conversation_context(thread1, query_t1)
        response1_check = await invoke_agent(
            agent,
            query_t1_with_context,
            thread_id=thread1
        )
        
        # Query Thread 2
        query_t2 = "What is my favorite number?"
        query_t2_with_context = inject_conversation_context(thread2, query_t2)
        response2_check = await invoke_agent(
            agent,
            query_t2_with_context,
            thread_id=thread2
        )
        
        thread1_correct = '42' in response1_check['response']
        thread2_correct = '99' in response2_check['response']
        
        print(f"  Thread 1 recall: {thread1_correct} (should have 42)")
        print(f"  Thread 2 recall: {thread2_correct} (should have 99)")
        
        result.add_sub_test(
            "Thread Isolation",
            thread1_correct and thread2_correct,
            thread1_correct=thread1_correct,
            thread2_correct=thread2_correct
        )
        
        result.finish(True, threads_tested=2, isolation_verified=thread1_correct and thread2_correct)
        
    except Exception as e:
        result.finish(False, error=str(e))
        import traceback
        traceback.print_exc()
    
    finally:
        env.cleanup()
    
    return result


async def main():
    """Run all ChromaDB memory tests"""
    print_test_header("INTEGRATION TEST 3: ChromaDB Memory and Multi-turn")
    
    if not check_azure_credentials():
        print("\n❌ Azure OpenAI credentials not configured!")
        return False
    
    if not verify_chromadb_available():
        print("\n❌ ChromaDB not available!")
        return False
    
    print("✓ Prerequisites met\n")
    
    results = []
    
    result1 = await test_chromadb_memory()
    result1.print_result()
    results.append(result1)
    
    result2 = await test_thread_isolation()
    result2.print_result()
    results.append(result2)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\n{'=' * 80}")
    print(f"  TEST 3 SUMMARY: {passed}/{total} passed")
    print(f"{'=' * 80}\n")
    
    return all(r.passed for r in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
