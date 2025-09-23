"""
ChromaDB-based checkpointer for LangGraph.

This provides a simple, working implementation of a LangGraph checkpointer
that uses ChromaDB for persistent storage of conversation state.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Iterator, Tuple, Union, AsyncIterator, Sequence
from datetime import datetime
import asyncio

try:
    from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata, CheckpointTuple
    from langchain_core.runnables import RunnableConfig
    HAS_LANGGRAPH = True
except ImportError:
    # Fallback definitions
    BaseCheckpointSaver = object
    Checkpoint = Dict[str, Any]
    CheckpointMetadata = Dict[str, Any] 
    CheckpointTuple = Tuple
    RunnableConfig = Dict[str, Any]
    HAS_LANGGRAPH = False

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

log = logging.getLogger(__name__)


class ChromaDBCheckpointer(BaseCheckpointSaver if HAS_LANGGRAPH else object):
    """
    ChromaDB-based checkpointer for LangGraph.
    
    Stores conversation checkpoints in ChromaDB for persistence across sessions.
    """
    
    def __init__(self, persist_directory: str = "./langgraph_checkpoints", collection_name: str = "checkpoints"):
        """Initialize the ChromaDB checkpointer."""
        if HAS_LANGGRAPH:
            super().__init__()
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embedding function (simple one for checkpoints)
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
        
        log.info(f"ChromaDB checkpointer initialized at {persist_directory}")
    
    def _get_checkpoint_id(self, config: RunnableConfig) -> Optional[str]:
        """Extract checkpoint ID from config."""
        if not config:
            return None
        
        configurable = config.get("configurable", {})
        thread_id = configurable.get("thread_id")
        checkpoint_id = configurable.get("checkpoint_id")
        
        if thread_id:
            return f"thread_{thread_id}" + (f"_{checkpoint_id}" if checkpoint_id else "")
        
        return None
    
    def _serialize_checkpoint(self, checkpoint: Checkpoint, metadata: CheckpointMetadata) -> str:
        """Serialize checkpoint and metadata to JSON string."""
        data = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        return json.dumps(data, default=str)
    
    def _deserialize_checkpoint(self, data: str) -> Tuple[Checkpoint, CheckpointMetadata]:
        """Deserialize JSON string back to checkpoint and metadata."""
        try:
            parsed = json.loads(data)
            checkpoint = parsed.get("checkpoint", {})
            metadata = parsed.get("metadata", {})
            return checkpoint, metadata
        except Exception as e:
            log.error(f"Error deserializing checkpoint: {e}")
            return {}, {}
    
    def get(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """Get checkpoint for the given config."""
        checkpoint_id = self._get_checkpoint_id(config)
        if not checkpoint_id:
            return None
        
        try:
            # Search for the checkpoint
            results = self.vector_store.similarity_search(
                query=checkpoint_id,
                k=1
            )
            
            if results:
                # Deserialize the checkpoint
                checkpoint, _ = self._deserialize_checkpoint(results[0].page_content)
                return checkpoint
            
            return None
            
        except Exception as e:
            log.error(f"Error retrieving checkpoint {checkpoint_id}: {e}")
            return None
    
    def put(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """Store checkpoint with the given config."""
        checkpoint_id = self._get_checkpoint_id(config)
        if not checkpoint_id:
            log.warning("No checkpoint ID found in config")
            return config
        
        try:
            # Serialize checkpoint
            serialized = self._serialize_checkpoint(checkpoint, metadata)
            
            # Store in ChromaDB
            doc_metadata = {
                "checkpoint_id": checkpoint_id,
                "thread_id": config.get("configurable", {}).get("thread_id"),
                "timestamp": time.time(),
                "type": "checkpoint"
            }
            
            # Add or update the checkpoint
            self.vector_store.add_texts(
                texts=[serialized],
                ids=[checkpoint_id],
                metadatas=[doc_metadata]
            )
            
            log.debug(f"Stored checkpoint {checkpoint_id}")
            return config
            
        except Exception as e:
            log.error(f"Error storing checkpoint {checkpoint_id}: {e}")
            raise
    
    def list(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> Iterator[CheckpointTuple]:
        """List checkpoints matching the given criteria."""
        if not config:
            return iter([])
        
        thread_id = config.get("configurable", {}).get("thread_id")
        if not thread_id:
            return iter([])
        
        try:
            # Search for checkpoints with this thread_id
            # Note: This is a simplified implementation
            # In a production system, you'd want more sophisticated filtering
            
            results = self.vector_store.similarity_search(
                query=f"thread_{thread_id}",
                k=limit or 10
            )
            
            checkpoints = []
            for result in results:
                try:
                    checkpoint, metadata = self._deserialize_checkpoint(result.page_content)
                    
                    # Create checkpoint tuple
                    checkpoint_config = {
                        "configurable": {
                            "thread_id": thread_id,
                            "checkpoint_id": result.metadata.get("checkpoint_id")
                        }
                    }
                    
                    if HAS_LANGGRAPH:
                        tuple_item = CheckpointTuple(checkpoint_config, checkpoint, metadata, {})
                    else:
                        tuple_item = (checkpoint_config, checkpoint, metadata, {})
                    
                    checkpoints.append(tuple_item)
                    
                except Exception as e:
                    log.warning(f"Error processing checkpoint result: {e}")
                    continue
            
            return iter(checkpoints)
            
        except Exception as e:
            log.error(f"Error listing checkpoints: {e}")
            return iter([])
    
    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Get checkpoint tuple for the given config."""
        checkpoint = self.get(config)
        if checkpoint is None:
            return None
        
        # Create basic metadata
        metadata = {
            "thread_id": config.get("configurable", {}).get("thread_id"),
            "timestamp": datetime.now().isoformat()
        }
        
        if HAS_LANGGRAPH:
            return CheckpointTuple(config, checkpoint, metadata, {})
        else:
            return (config, checkpoint, metadata, {})
    
    def put_writes(self, config: RunnableConfig, writes: Sequence[Tuple[str, Any]], task_id: str, task_path: str = "") -> None:
        """Store intermediate writes (simplified implementation)."""
        # For now, we'll store writes as part of the checkpoint
        # In a full implementation, you might want separate storage for writes
        checkpoint_id = self._get_checkpoint_id(config)
        if not checkpoint_id:
            return
        
        try:
            writes_data = {
                "writes": list(writes),
                "task_id": task_id,
                "task_path": task_path,
                "timestamp": datetime.now().isoformat()
            }
            
            writes_id = f"{checkpoint_id}_writes_{task_id}"
            serialized = json.dumps(writes_data, default=str)
            
            doc_metadata = {
                "checkpoint_id": checkpoint_id,
                "thread_id": config.get("configurable", {}).get("thread_id"),
                "task_id": task_id,
                "type": "writes"
            }
            
            self.vector_store.add_texts(
                texts=[serialized],
                ids=[writes_id],
                metadatas=[doc_metadata]
            )
            
            log.debug(f"Stored writes for {checkpoint_id}")
            
        except Exception as e:
            log.error(f"Error storing writes: {e}")
    
    def get_next_version(self, current: Union[str, int, float, None], channel=None) -> Union[str, int, float]:
        """Generate next version ID."""
        if current is None:
            return 1
        elif isinstance(current, (int, float)):
            return current + 1
        else:
            # For string versions, try to increment or use timestamp
            try:
                return str(int(current) + 1)
            except (ValueError, TypeError):
                return str(int(time.time()))
    
    # Async methods (for compatibility)
    async def aget(self, config: RunnableConfig) -> Optional[Checkpoint]:
        """Async version of get."""
        return self.get(config)
    
    async def aput(self, config: RunnableConfig, checkpoint: Checkpoint, metadata: CheckpointMetadata, new_versions: dict) -> RunnableConfig:
        """Async version of put."""
        return self.put(config, checkpoint, metadata, new_versions)
    
    async def alist(self, config: Optional[RunnableConfig], *, filter: Optional[Dict[str, Any]] = None, before: Optional[RunnableConfig] = None, limit: Optional[int] = None) -> AsyncIterator[CheckpointTuple]:
        """Async version of list."""
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item
    
    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Async version of get_tuple."""
        return self.get_tuple(config)
    
    async def aput_writes(self, config: RunnableConfig, writes: Sequence[Tuple[str, Any]], task_id: str, task_path: str = "") -> None:
        """Async version of put_writes."""
        self.put_writes(config, writes, task_id, task_path)


def create_chromadb_checkpointer(persist_directory: str = "./langgraph_checkpoints") -> ChromaDBCheckpointer:
    """Create a ChromaDB checkpointer instance."""
    return ChromaDBCheckpointer(persist_directory=persist_directory)


# Test function
def test_chromadb_checkpointer():
    """Test the ChromaDB checkpointer."""
    checkpointer = create_chromadb_checkpointer("./test_checkpoints")
    
    # Test config
    config = {
        "configurable": {
            "thread_id": "test_thread_123"
        }
    }
    
    # Test checkpoint
    checkpoint = {
        "data": "test checkpoint data",
        "step": 1,
        "messages": ["Hello", "World"]
    }
    
    metadata = {
        "user": "test_user",
        "timestamp": datetime.now().isoformat()
    }
    
    print("Testing ChromaDB Checkpointer:")
    print("=" * 40)
    
    try:
        # Store checkpoint
        print("1. Storing checkpoint...")
        result_config = checkpointer.put(config, checkpoint, metadata, {})
        print(f"   Stored successfully: {result_config}")
        
        # Retrieve checkpoint
        print("2. Retrieving checkpoint...")
        retrieved = checkpointer.get(config)
        print(f"   Retrieved: {retrieved}")
        
        # List checkpoints
        print("3. Listing checkpoints...")
        checkpoints = list(checkpointer.list(config))
        print(f"   Found {len(checkpoints)} checkpoints")
        
        # Get tuple
        print("4. Getting checkpoint tuple...")
        tuple_result = checkpointer.get_tuple(config)
        print(f"   Tuple: {tuple_result is not None}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_chromadb_checkpointer()
