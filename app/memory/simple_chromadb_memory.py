"""
Simple ChromaDB memory implementation for LangGraph agents.

This implementation follows the verified working pattern from the research
and provides a simple, reliable ChromaDB integration with LangGraph.
"""

import logging
from typing import Dict, List, Any, Optional
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import os

log = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State definition for memory-enabled graph."""
    question: str
    memories: List[str]
    response: Optional[str]


class SimpleChromaDBMemory:
    """
    Simple ChromaDB memory implementation for LangGraph.
    
    Based on verified working patterns from community examples.
    """
    
    def __init__(self, persist_directory: str = "./chroma_memory", collection_name: str = "jk_agents_memory"):
        """Initialize ChromaDB memory with embedding function."""
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embedding function
        self.embedding_function = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize vector store
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_function,
            persist_directory=persist_directory
        )
        
        log.info(f"ChromaDB memory initialized at {persist_directory}")
    
    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a memory to the vector store."""
        try:
            # Generate a simple ID
            import time
            doc_id = f"mem_{int(time.time() * 1000)}"
            
            # Add to vector store
            self.vector_store.add_texts(
                texts=[text],
                ids=[doc_id],
                metadatas=[metadata or {}]
            )
            
            log.debug(f"Added memory: {text[:50]}...")
            return doc_id
        except Exception as e:
            log.error(f"Error adding memory: {e}")
            raise
    
    def search_memories(self, query: str, k: int = 3) -> List[str]:
        """Search for relevant memories."""
        try:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
            docs = retriever.get_relevant_documents(query)
            return [doc.page_content for doc in docs]
        except Exception as e:
            log.error(f"Error searching memories: {e}")
            return []
    
    def clear_memories(self):
        """Clear all memories from the collection."""
        try:
            # Get all documents and delete them
            collection = self.vector_store._collection
            collection.delete()
            log.info("All memories cleared")
        except Exception as e:
            log.error(f"Error clearing memories: {e}")
    
    def get_memory_count(self) -> int:
        """Get the number of memories stored."""
        try:
            collection = self.vector_store._collection
            return collection.count()
        except Exception as e:
            log.error(f"Error getting memory count: {e}")
            return 0


def create_memory_retrieval_node(memory_store: SimpleChromaDBMemory):
    """Create a memory retrieval node for LangGraph."""
    
    def retrieve_memory(state: GraphState) -> GraphState:
        """Retrieve relevant memories for the current question."""
        question = state["question"]
        
        # Search for relevant memories
        memories = memory_store.search_memories(question, k=3)
        
        return {
            "question": question,
            "memories": memories,
            "response": state.get("response")
        }
    
    return retrieve_memory


def create_memory_storage_node(memory_store: SimpleChromaDBMemory):
    """Create a memory storage node for LangGraph."""
    
    def store_memory(state: GraphState) -> GraphState:
        """Store the current interaction as memory."""
        question = state["question"]
        response = state.get("response", "")
        
        if question and response:
            # Create memory text combining question and response
            memory_text = f"Q: {question}\nA: {response}"
            
            # Store with metadata
            metadata = {
                "type": "qa_pair",
                "question": question,
                "response": response
            }
            
            memory_store.add_memory(memory_text, metadata)
        
        return state
    
    return store_memory


def create_memory_enabled_graph(memory_store: SimpleChromaDBMemory) -> StateGraph:
    """
    Create a LangGraph workflow with ChromaDB memory integration.
    
    This follows the verified pattern from the research.
    """
    
    # Create retrieval and storage nodes
    retrieve_memory = create_memory_retrieval_node(memory_store)
    store_memory = create_memory_storage_node(memory_store)
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("retrieve_memory", retrieve_memory)
    workflow.add_node("store_memory", store_memory)
    
    # Add edges
    workflow.add_edge(START, "retrieve_memory")
    workflow.add_edge("retrieve_memory", "store_memory")
    workflow.add_edge("store_memory", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# Example usage function
def test_chromadb_memory():
    """Test the ChromaDB memory implementation."""
    
    # Initialize memory store
    memory_store = SimpleChromaDBMemory()
    
    # Add some sample memories
    sample_memories = [
        "The iPhone 12 battery lasts 17 hours.",
        "LangGraph orchestrates agent workflows.",
        "ChromaDB enables fast semantic search.",
        "Python is a popular programming language.",
        "Machine learning models require training data."
    ]
    
    for memory in sample_memories:
        memory_store.add_memory(memory)
    
    # Create memory-enabled graph
    app = create_memory_enabled_graph(memory_store)
    
    # Test queries
    test_queries = [
        "What is the battery life of iPhone 12?",
        "How does LangGraph work?",
        "What is ChromaDB used for?"
    ]
    
    print("Testing ChromaDB Memory Integration:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Run the graph
        inputs = {"question": query, "memories": [], "response": None}
        
        try:
            result = None
            for event in app.stream(inputs):
                result = event
            
            if result and "retrieve_memory" in result:
                memories = result["retrieve_memory"]["memories"]
                print(f"Retrieved memories: {len(memories)}")
                for i, memory in enumerate(memories, 1):
                    print(f"  {i}. {memory}")
            else:
                print("No memories retrieved")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print(f"\nTotal memories stored: {memory_store.get_memory_count()}")


if __name__ == "__main__":
    test_chromadb_memory()
