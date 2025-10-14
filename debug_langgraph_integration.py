#!/usr/bin/env python3
"""
Debug LangGraph integration with our ChromaDB system to find the 'v' KeyError.

This test simulates the exact LangGraph usage patterns from planner_executor.py
to reproduce the multi-turn memory failure.
"""

import asyncio
import json
import logging
import traceback
from typing import Dict, Any, Optional

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

log = logging.getLogger(__name__)

async def test_langgraph_integration():
    """Test LangGraph integration patterns that cause the 'v' KeyError."""
    
    print("🔍 Testing LangGraph Integration Patterns")
    print("=" * 60)
    
    try:
        # Import LangGraph components
        from langgraph.graph import StateGraph, END
        from langgraph.checkpoint.memory import MemorySaver
        from langchain_core.messages import HumanMessage, AIMessage
        from typing_extensions import TypedDict
        
        # Try importing our memory system
        from app.memory.langgraph_adapter import HighPerformanceCheckpointer
        
        print("✅ Imported LangGraph and memory components")
        
        # Create a simple state class for testing
        class ConversationState(TypedDict):
            messages: list
            counter: int
        
        # Create a simple agent function
        def simple_agent(state: ConversationState) -> ConversationState:
            messages = state.get("messages", [])
            counter = state.get("counter", 0)
            
            # Add a response message
            new_message = AIMessage(content=f"Response {counter + 1}")
            messages.append(new_message)
            
            return {
                "messages": messages,
                "counter": counter + 1
            }
        
        # Test 1: Using standard MemorySaver (for comparison)
        print("\n📝 Test 1: Standard MemorySaver (baseline)")
        
        # Create graph with standard memory
        standard_graph = StateGraph(ConversationState)
        standard_graph.add_node("agent", simple_agent)
        standard_graph.set_entry_point("agent")
        standard_graph.add_edge("agent", END)
        
        standard_checkpointer = MemorySaver()
        standard_compiled = standard_graph.compile(checkpointer=standard_checkpointer)
        
        # Test standard memory with multi-turn
        thread_id_standard = "standard-test-001"
        config_standard = {"configurable": {"thread_id": thread_id_standard}}
        
        # First turn
        initial_state = {
            "messages": [HumanMessage(content="Hello")],
            "counter": 0
        }
        
        result1 = await standard_compiled.ainvoke(initial_state, config_standard)
        print(f"✅ Standard MemorySaver - Turn 1: {len(result1['messages'])} messages")
        
        # Second turn
        second_state = {
            "messages": result1["messages"] + [HumanMessage(content="How are you?")],
            "counter": result1["counter"]
        }
        
        result2 = await standard_compiled.ainvoke(second_state, config_standard)
        print(f"✅ Standard MemorySaver - Turn 2: {len(result2['messages'])} messages")
        
        # Test 2: Using our HighPerformanceCheckpointer
        print("\n📝 Test 2: HighPerformanceCheckpointer (our system)")
        
        # Create our checkpointer
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": "./debug_langgraph_memory",
                    "max_connections": 5,
                    "batch_size": 10,
                    "enable_batch_processing": False,
                    "l1_cache_size": 100
                }
            }
        }
        
        our_checkpointer = HighPerformanceCheckpointer(config)
        
        # Compile graph with our checkpointer
        our_compiled = standard_graph.compile(checkpointer=our_checkpointer)
        
        # Test with same pattern as planner_executor.py
        thread_id_our = "our-test-001"
        config_our = {"configurable": {"thread_id": thread_id_our, "checkpoint_ns": ""}}
        
        try:
            # First turn
            result1_our = await our_compiled.ainvoke(initial_state, config_our)
            print(f"✅ Our Checkpointer - Turn 1: {len(result1_our['messages'])} messages")
            
            # Second turn (this is where the error likely occurs)
            second_state_our = {
                "messages": result1_our["messages"] + [HumanMessage(content="How are you?")],
                "counter": result1_our["counter"]
            }
            
            result2_our = await our_compiled.ainvoke(second_state_our, config_our)
            print(f"✅ Our Checkpointer - Turn 2: {len(result2_our['messages'])} messages")
            
        except KeyError as e:
            print(f"🚨 CAUGHT KeyError in our checkpointer: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            
            # Analyze the error context
            await analyze_langgraph_error(e, our_checkpointer, thread_id_our)
            
        except Exception as e:
            print(f"🚨 CAUGHT Other Exception in our checkpointer: {type(e).__name__}: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
        
        # Test 3: Direct checkpoint inspection
        print("\n📝 Test 3: Direct checkpoint inspection")
        
        try:
            # Get checkpoint directly
            checkpoint = await our_checkpointer.aget(config_our)
            if checkpoint:
                print(f"✅ Direct checkpoint retrieval successful")
                print(f"   Checkpoint type: {type(checkpoint)}")
                if isinstance(checkpoint, dict):
                    print(f"   Checkpoint keys: {list(checkpoint.keys())}")
                    print(f"   Has 'v' field: {'v' in checkpoint}")
                    if 'v' in checkpoint:
                        print(f"   'v' value: {checkpoint['v']} (type: {type(checkpoint['v'])})")
            else:
                print("❌ No checkpoint found")
                
        except Exception as e:
            print(f"🚨 Error in direct checkpoint inspection: {e}")
            print(traceback.format_exc())
        
        # Test 4: Test with empty checkpoint_ns (potential issue)
        print("\n📝 Test 4: Testing checkpoint_ns variations")
        
        test_configs = [
            {"configurable": {"thread_id": "test-ns-001"}},  # No checkpoint_ns
            {"configurable": {"thread_id": "test-ns-002", "checkpoint_ns": ""}},  # Empty string
            {"configurable": {"thread_id": "test-ns-003", "checkpoint_ns": "default"}},  # Non-empty
        ]
        
        for i, test_config in enumerate(test_configs):
            try:
                print(f"   Test 4.{i+1}: Config {test_config}")
                test_result = await our_compiled.ainvoke(initial_state, test_config)
                print(f"   ✅ Success: {len(test_result['messages'])} messages")
                
                # Try second turn
                second_test_state = {
                    "messages": test_result["messages"] + [HumanMessage(content="Second turn")],
                    "counter": test_result["counter"]
                }
                test_result2 = await our_compiled.ainvoke(second_test_state, test_config)
                print(f"   ✅ Second turn success: {len(test_result2['messages'])} messages")
                
            except KeyError as e:
                print(f"   🚨 KeyError with config {i+1}: {e}")
                if str(e).strip("'\"") == "v":
                    print(f"   ✅ Reproduced the 'v' KeyError!")
                    await analyze_langgraph_error(e, our_checkpointer, test_config["configurable"]["thread_id"])
            except Exception as e:
                print(f"   🚨 Other error with config {i+1}: {type(e).__name__}: {e}")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   LangGraph or dependencies not available")
    except Exception as e:
        print(f"🚨 CRITICAL ERROR in LangGraph integration test: {type(e).__name__}: {e}")
        print("Full traceback:")
        print(traceback.format_exc())

async def analyze_langgraph_error(error: KeyError, checkpointer, thread_id: str):
    """Analyze LangGraph-specific KeyError patterns."""
    
    print(f"\n🔍 Analyzing LangGraph KeyError:")
    print(f"   Thread ID: {thread_id}")
    print(f"   Error: {error}")
    print(f"   Error args: {error.args}")
    
    # Check if this is the 'v' KeyError
    if str(error).strip("'\"") == "v":
        print("   ✅ This is the 'v' KeyError we're investigating!")
        
        # Get the current stack to see where in LangGraph this is failing
        print("\n   📍 Call stack analysis:")
        stack = traceback.extract_tb(error.__traceback__)
        
        for frame in stack:
            print(f"     File: {frame.filename}")
            print(f"     Function: {frame.name}")
            print(f"     Line: {frame.lineno}")
            print(f"     Code: {frame.line}")
            print("     ---")
        
        # Try to understand what LangGraph is expecting
        print("\n   🔬 Checkpoint structure analysis:")
        try:
            # Check if we can get the raw checkpoint data
            raw_data = await checkpointer._manager.retrieve_checkpoint(
                checkpointer._user_id, thread_id
            )
            
            if raw_data:
                print(f"   Raw data found: {len(raw_data)} bytes")
                
                # Parse and examine structure
                parsed_data = json.loads(raw_data.decode('utf-8'))
                print(f"   Parsed data keys: {list(parsed_data.keys())}")
                
                if "checkpoint" in parsed_data:
                    checkpoint_data = parsed_data["checkpoint"]
                    print(f"   Checkpoint data keys: {list(checkpoint_data.keys())}")
                    
                    # Check version field specifically
                    if "v" in checkpoint_data:
                        v_field = checkpoint_data["v"]
                        print(f"   'v' field: {v_field} (type: {type(v_field)})")
                        print(f"   'v' is integer: {isinstance(v_field, int)}")
                        print(f"   'v' is valid: {isinstance(v_field, int) and v_field > 0}")
                    else:
                        print("   ❌ No 'v' field in checkpoint data!")
                        
                        # This might be the issue - let's see what's there
                        print(f"   Full checkpoint structure: {json.dumps(checkpoint_data, indent=2, default=str)}")
        
        except Exception as e:
            print(f"   ❌ Error analyzing checkpoint: {e}")

if __name__ == "__main__":
    print("🚀 Running LangGraph Integration Debug")
    asyncio.run(test_langgraph_integration())
    print("\n✅ LangGraph integration test completed.")
