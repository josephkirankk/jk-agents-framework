"""
Comprehensive example of ChromaDB memory integration with LangGraph.

This example demonstrates:
1. Setting up ChromaDB as a memory store
2. Creating a LangGraph agent with memory
3. Using ChromaDB checkpointer for persistence
4. Testing the complete memory functionality
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.memory.simple_chromadb_memory import SimpleChromaDBMemory, create_memory_enabled_graph
from app.memory.chromadb_checkpointer import ChromaDBCheckpointer
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the memory-enabled agent."""
    messages: List[str]
    question: str
    memories: List[str]
    response: str
    context: str


class ChromaDBMemoryAgent:
    """
    A complete example agent that uses ChromaDB for both memory and checkpointing.
    
    This demonstrates the verified working pattern from the research.
    """
    
    def __init__(self, memory_dir: str = "./agent_memory", checkpoint_dir: str = "./agent_checkpoints"):
        """Initialize the agent with ChromaDB memory and checkpointing."""
        
        # Initialize memory store
        self.memory_store = SimpleChromaDBMemory(
            persist_directory=memory_dir,
            collection_name="agent_memories"
        )
        
        # Initialize checkpointer
        self.checkpointer = ChromaDBCheckpointer(
            persist_directory=checkpoint_dir,
            collection_name="agent_checkpoints"
        )
        
        # Build the agent graph
        self.graph = self._build_agent_graph()
        
        log.info("ChromaDB Memory Agent initialized")
    
    def _build_agent_graph(self) -> StateGraph:
        """Build the agent graph with memory integration."""
        
        def retrieve_memories(state: AgentState) -> AgentState:
            """Retrieve relevant memories for the current question."""
            question = state["question"]
            
            # Search for relevant memories
            memories = self.memory_store.search_memories(question, k=3)
            
            # Create context from memories
            context = ""
            if memories:
                context = "Relevant memories:\n" + "\n".join(f"- {mem}" for mem in memories)
            
            return {
                **state,
                "memories": memories,
                "context": context
            }
        
        def process_question(state: AgentState) -> AgentState:
            """Process the question with memory context."""
            question = state["question"]
            context = state.get("context", "")
            
            # Simple response generation (in real usage, this would call an LLM)
            response = self._generate_response(question, context)
            
            return {
                **state,
                "response": response
            }
        
        def store_interaction(state: AgentState) -> AgentState:
            """Store the current interaction in memory."""
            question = state["question"]
            response = state["response"]
            
            if question and response:
                # Store the Q&A pair
                memory_text = f"Question: {question}\nAnswer: {response}"
                metadata = {
                    "type": "qa_interaction",
                    "timestamp": datetime.now().isoformat(),
                    "question": question[:100],  # Truncated for metadata
                    "response": response[:100]   # Truncated for metadata
                }
                
                self.memory_store.add_memory(memory_text, metadata)
                log.info(f"Stored interaction in memory: {question[:50]}...")
            
            return state
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retrieve_memories", retrieve_memories)
        workflow.add_node("process_question", process_question)
        workflow.add_node("store_interaction", store_interaction)
        
        # Add edges
        workflow.add_edge(START, "retrieve_memories")
        workflow.add_edge("retrieve_memories", "process_question")
        workflow.add_edge("process_question", "store_interaction")
        workflow.add_edge("store_interaction", END)
        
        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _generate_response(self, question: str, context: str) -> str:
        """
        Generate a response to the question using context.
        
        In a real implementation, this would call an LLM with the context.
        """
        
        # Simple rule-based responses for demonstration
        question_lower = question.lower()
        
        if "hello" in question_lower or "hi" in question_lower:
            return "Hello! How can I help you today?"
        
        elif "name" in question_lower:
            return "I'm a ChromaDB-powered memory agent. I can remember our conversations!"
        
        elif "remember" in question_lower or "recall" in question_lower:
            if context:
                return f"Based on what I remember:\n{context}\n\nIs this what you were looking for?"
            else:
                return "I don't have any relevant memories about that topic yet."
        
        elif "weather" in question_lower:
            response = "I don't have real-time weather data, but I can remember weather information you tell me."
            if context:
                response += f"\n\nFrom my memories:\n{context}"
            return response
        
        elif "forget" in question_lower or "clear" in question_lower:
            return "I can help you manage memories. What would you like me to forget?"
        
        else:
            # Generic response with context
            response = f"I understand you're asking about: {question}"
            if context:
                response += f"\n\nBased on my memories:\n{context}"
            else:
                response += "\n\nI don't have specific memories about this topic yet, but I'll remember this conversation."
            
            return response
    
    def chat(self, question: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Chat with the agent using memory and checkpointing.
        
        Args:
            question: The user's question
            thread_id: Thread ID for conversation persistence
            
        Returns:
            Dictionary with response and metadata
        """
        
        # Create config with thread ID
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Create initial state
        initial_state = {
            "messages": [],
            "question": question,
            "memories": [],
            "response": "",
            "context": ""
        }
        
        try:
            # Run the graph
            result = self.graph.invoke(initial_state, config=config)
            
            return {
                "question": question,
                "response": result["response"],
                "memories_used": result["memories"],
                "context": result["context"],
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Error in chat: {e}")
            return {
                "question": question,
                "response": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e),
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory store."""
        return {
            "total_memories": self.memory_store.get_memory_count(),
            "memory_directory": self.memory_store.persist_directory,
            "checkpoint_directory": self.checkpointer.persist_directory
        }
    
    def clear_memories(self):
        """Clear all memories."""
        self.memory_store.clear_memories()
        log.info("All memories cleared")
    
    def search_memories(self, query: str, k: int = 5) -> List[str]:
        """Search memories directly."""
        return self.memory_store.search_memories(query, k)


def run_interactive_demo():
    """Run an interactive demo of the ChromaDB memory agent."""
    
    print("🧠 ChromaDB Memory Agent Demo")
    print("=" * 50)
    print("This agent uses ChromaDB for memory and LangGraph for conversation flow.")
    print("Type 'quit' to exit, 'stats' for memory statistics, 'clear' to clear memories.")
    print()
    
    # Initialize agent
    agent = ChromaDBMemoryAgent()
    
    # Demo thread ID
    thread_id = "demo_session_" + str(int(datetime.now().timestamp()))
    
    print(f"Session ID: {thread_id}")
    print()
    
    while True:
        try:
            # Get user input
            question = input("You: ").strip()
            
            if not question:
                continue
            
            if question.lower() == 'quit':
                break
            
            elif question.lower() == 'stats':
                stats = agent.get_memory_stats()
                print(f"Agent: Memory statistics: {stats}")
                continue
            
            elif question.lower() == 'clear':
                agent.clear_memories()
                print("Agent: All memories cleared!")
                continue
            
            elif question.lower().startswith('search '):
                query = question[7:]  # Remove 'search '
                memories = agent.search_memories(query)
                print(f"Agent: Found {len(memories)} memories:")
                for i, memory in enumerate(memories, 1):
                    print(f"  {i}. {memory}")
                continue
            
            # Chat with agent
            print("Agent: Thinking...")
            result = agent.chat(question, thread_id)
            
            print(f"Agent: {result['response']}")
            
            # Show memory info if relevant
            if result['memories_used']:
                print(f"  (Used {len(result['memories_used'])} memories)")
            
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    print("\nGoodbye! 👋")


def run_automated_test():
    """Run automated tests of the ChromaDB memory functionality."""
    
    print("🧪 Running ChromaDB Memory Tests")
    print("=" * 40)
    
    # Initialize agent
    agent = ChromaDBMemoryAgent(
        memory_dir="./test_memory",
        checkpoint_dir="./test_checkpoints"
    )
    
    # Test cases
    test_cases = [
        ("Hello, my name is Alice", "greeting"),
        ("I like pizza and pasta", "preferences"),
        ("My favorite color is blue", "preferences"),
        ("What do you remember about me?", "recall"),
        ("Do you know what I like to eat?", "recall"),
        ("What's my favorite color?", "recall"),
        ("I also enjoy hiking and reading", "additional_info"),
        ("Tell me about my preferences", "final_recall")
    ]
    
    thread_id = "test_thread_123"
    
    print(f"Test thread: {thread_id}\n")
    
    for i, (question, test_type) in enumerate(test_cases, 1):
        print(f"Test {i} ({test_type}):")
        print(f"  Q: {question}")
        
        result = agent.chat(question, thread_id)
        
        print(f"  A: {result['response']}")
        
        if result['memories_used']:
            print(f"  Memories used: {len(result['memories_used'])}")
            for mem in result['memories_used']:
                print(f"    - {mem[:60]}...")
        
        print()
    
    # Final statistics
    stats = agent.get_memory_stats()
    print(f"Final memory statistics: {stats}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="ChromaDB Memory Agent Example")
    parser.add_argument("--mode", choices=["interactive", "test"], default="interactive",
                       help="Run mode: interactive demo or automated test")
    
    args = parser.parse_args()
    
    if args.mode == "interactive":
        run_interactive_demo()
    else:
        run_automated_test()
