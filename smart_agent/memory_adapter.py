"""
Memory Adapter for Smart Memory Agent Integration

Simple, production-ready adapter that bridges existing memory systems 
with the Smart Memory Agent interface.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimpleMemoryItem:
    """Simple memory item structure for the adapter"""
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    memory_type: str
    id: Optional[str] = None


class MemoryAdapter:
    """
    Production-ready adapter that provides Smart Memory Agent interface
    while using simple in-memory storage with thread isolation.
    """
    
    def __init__(self, thread_id: Optional[str] = None):
        self.thread_id = thread_id or "default"
        self._memories: Dict[str, List[SimpleMemoryItem]] = {}
        self._counter = 0
        logger.info(f"Memory adapter initialized for thread: {self.thread_id}")
    
    async def store(self, content: str, metadata: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """Store memory item and return ID"""
        memory_type = kwargs.get('memory_type', 'conversation')
        agent_name = kwargs.get('agent_name', 'unknown')
        step_id = kwargs.get('step_id', 'unknown')
        
        if self.thread_id not in self._memories:
            self._memories[self.thread_id] = []
        
        self._counter += 1
        memory_id = f"{self.thread_id}_{self._counter}"
        
        # Add agent and thread info to metadata
        enhanced_metadata = (metadata or {}).copy()
        enhanced_metadata.update({
            'agent_name': agent_name,
            'step_id': step_id,
            'thread_id': self.thread_id,
            'memory_id': memory_id,
            'stored_at': datetime.now().isoformat()
        })
        
        memory_item = SimpleMemoryItem(
            content=content,
            metadata=enhanced_metadata,
            timestamp=datetime.now(),
            memory_type=memory_type,
            id=memory_id
        )
        
        self._memories[self.thread_id].append(memory_item)
        
        # Comprehensive logging
        logger.info(
            f"[MEMORY STORE] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Step: {step_id} | Type: {memory_type} | ID: {memory_id} | "
            f"Content: {content[:80]}{'...' if len(content) > 80 else ''}"
        )
        
        return memory_id
    
    async def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search memories and return matching results"""
        agent_name = kwargs.get('agent_name', 'unknown')
        context_type = kwargs.get('context_type', 'search')
        
        if self.thread_id not in self._memories:
            logger.info(
                f"[MEMORY SEARCH] Thread: {self.thread_id} | Agent: {agent_name} | "
                f"Context: {context_type} | Query: '{query}' | Result: No memories in thread"
            )
            return []
        
        memories = self._memories[self.thread_id]
        total_memories = len(memories)
        
        # Simple keyword-based search
        query_words = query.lower().split()
        results = []
        
        for memory in memories:
            content_words = memory.content.lower()
            # Calculate simple relevance score based on word matches
            matches = sum(1 for word in query_words if word in content_words)
            if matches > 0:
                relevance_score = matches / len(query_words)
                results.append({
                    'id': memory.id,
                    'content': memory.content,
                    'metadata': memory.metadata,
                    'timestamp': memory.timestamp.isoformat(),
                    'memory_type': memory.memory_type,
                    'relevance_score': relevance_score
                })
        
        # Sort by relevance score (descending) and timestamp (recent first)
        results.sort(key=lambda x: (x['relevance_score'], x['timestamp']), reverse=True)
        final_results = results[:limit]
        
        # Comprehensive logging
        logger.info(
            f"[MEMORY SEARCH] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Context: {context_type} | Query: '{query}' | "
            f"Total memories: {total_memories} | Matches: {len(results)} | Returned: {len(final_results)}"
        )
        
        # Log details of returned memories
        for i, result in enumerate(final_results):
            stored_agent = result['metadata'].get('agent_name', 'unknown')
            stored_step = result['metadata'].get('step_id', 'unknown')
            memory_type = result['memory_type']
            relevance = result['relevance_score']
            content_preview = result['content'][:60] + ('...' if len(result['content']) > 60 else '')
            
            logger.debug(
                f"[MEMORY MATCH {i+1}] ID: {result['id']} | From Agent: {stored_agent} | "
                f"Step: {stored_step} | Type: {memory_type} | Relevance: {relevance:.3f} | "
                f"Content: {content_preview}"
            )
        
        return final_results
    
    async def get_context_for_query(
        self,
        query: str,
        max_tokens: Optional[int] = None,
        include_metadata: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Get optimized context for a query"""
        agent_name = kwargs.get('agent_name', 'unknown')
        context_type = kwargs.get('context_type', 'context')
        
        # Pass agent info to search
        search_kwargs = kwargs.copy()
        search_kwargs['agent_name'] = agent_name
        search_kwargs['context_type'] = context_type
        
        memories = await self.search(query, limit=kwargs.get('limit', 10), **search_kwargs)
        
        # Simple token estimation (rough: 1 token ≈ 4 characters)
        total_tokens = 0
        filtered_memories = []
        excluded_count = 0
        
        for memory in memories:
            memory_tokens = len(memory['content']) // 4
            if max_tokens and (total_tokens + memory_tokens > max_tokens):
                excluded_count += 1
                continue
            
            filtered_memories.append(memory)
            total_tokens += memory_tokens
        
        context_summary = ""
        if filtered_memories:
            context_summary = f"Found {len(filtered_memories)} relevant memories for query: {query}"
            if excluded_count > 0:
                context_summary += f" ({excluded_count} excluded due to token limit)"
        
        result = {
            "query": query,
            "optimized_memories": filtered_memories,
            "context_summary": context_summary,
            "total_tokens": total_tokens,
            "optimization_applied": len(filtered_memories) < len(memories),
            "relevance_threshold": 0.1,
            "performance_metrics": {
                "retrieval_time_ms": 5,  # Placeholder
                "total_memories_searched": len(self._memories.get(self.thread_id, [])),
                "memories_returned": len(filtered_memories),
                "excluded_by_token_limit": excluded_count
            },
            "smart_memory_available": True
        }
        
        # Comprehensive logging
        logger.info(
            f"[CONTEXT BUILD] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Context: {context_type} | Query: '{query}' | "
            f"Memories: {len(filtered_memories)} | Tokens: {total_tokens} | "
            f"Token limit: {max_tokens or 'None'} | Excluded: {excluded_count}"
        )
        
        return result
    
    def get_memory_count(self) -> int:
        """Get total number of memories for this thread"""
        return len(self._memories.get(self.thread_id, []))
    
    def get_all_threads(self) -> List[str]:
        """Get all thread IDs with stored memories"""
        return list(self._memories.keys())


class ProductionSmartMemoryIntegration:
    """
    Production-ready Smart Memory integration that focuses on reliability
    over advanced features. Uses simple in-memory storage with thread isolation.
    """
    
    def __init__(self, thread_id: Optional[str] = None):
        self.thread_id = thread_id or "default"
        self.memory_adapter = MemoryAdapter(thread_id)
        self.metrics = {
            "calls": 0,
            "stores": 0,
            "searches": 0,
            "last_used": datetime.now()
        }
        logger.info(f"Production Smart Memory integration ready for thread: {self.thread_id}")
    
    async def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation",
        **kwargs
    ) -> str:
        """Store memory with Smart Agent interface"""
        self.metrics["calls"] += 1
        self.metrics["stores"] += 1
        self.metrics["last_used"] = datetime.now()
        
        agent_name = kwargs.get('agent_name', 'unknown')
        step_id = kwargs.get('step_id', 'unknown')
        
        logger.info(
            f"[SMART MEMORY STORE] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Step: {step_id} | Type: {memory_type} | Starting storage operation"
        )
        
        result = await self.memory_adapter.store(
            content=content,
            metadata=metadata,
            memory_type=memory_type,
            **kwargs
        )
        
        logger.info(
            f"[SMART MEMORY STORE] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Storage completed with ID: {result}"
        )
        
        return result
    
    async def retrieve_memories(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve memories with Smart Agent interface"""
        self.metrics["calls"] += 1
        self.metrics["searches"] += 1
        self.metrics["last_used"] = datetime.now()
        
        agent_name = kwargs.get('agent_name', 'unknown')
        
        logger.info(
            f"[SMART MEMORY RETRIEVE] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Query: '{query}' | Limit: {limit} | Type filter: {memory_type or 'None'}"
        )
        
        results = await self.memory_adapter.search(query, limit, **kwargs)
        
        # Apply memory type filter if specified
        if memory_type:
            original_count = len(results)
            results = [r for r in results if r.get('memory_type') == memory_type]
            logger.info(
                f"[SMART MEMORY RETRIEVE] Applied type filter '{memory_type}': "
                f"{original_count} -> {len(results)} results"
            )
        
        logger.info(
            f"[SMART MEMORY RETRIEVE] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Retrieval completed: {len(results)} memories returned"
        )
        
        return results
    
    async def get_context_for_query(
        self,
        query: str,
        max_tokens: Optional[int] = None,
        include_metadata: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Get optimized context for a query"""
        self.metrics["calls"] += 1
        self.metrics["last_used"] = datetime.now()
        
        agent_name = kwargs.get('agent_name', 'unknown')
        context_type = kwargs.get('context_type', 'unknown')
        
        logger.info(
            f"[SMART MEMORY CONTEXT] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Context: {context_type} | Query: '{query}' | Max tokens: {max_tokens or 'None'}"
        )
        
        result = await self.memory_adapter.get_context_for_query(
            query=query,
            max_tokens=max_tokens,
            include_metadata=include_metadata,
            **kwargs
        )
        
        logger.info(
            f"[SMART MEMORY CONTEXT] Thread: {self.thread_id} | Agent: {agent_name} | "
            f"Context built: {len(result.get('optimized_memories', []))} memories, "
            f"{result.get('total_tokens', 0)} tokens"
        )
        
        return result
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status and metrics"""
        return {
            "smart_agent_enabled": True,
            "thread_id": self.thread_id,
            "metrics": {
                **self.metrics,
                "memory_count": self.memory_adapter.get_memory_count(),
                "last_used": self.metrics["last_used"].isoformat()
            },
            "status": "active",
            "backend": "production_memory_adapter"
        }


# Global registry for thread-specific integrations
_integrations: Dict[str, ProductionSmartMemoryIntegration] = {}


async def get_or_create_smart_memory_integration(thread_id: str) -> ProductionSmartMemoryIntegration:
    """
    Get or create a Smart Memory integration for a specific thread.
    This ensures thread isolation and proper memory separation.
    """
    if thread_id not in _integrations:
        _integrations[thread_id] = ProductionSmartMemoryIntegration(thread_id)
        logger.info(
            f"[INTEGRATION CREATE] Thread: {thread_id} | "
            f"Created new Smart Memory integration | "
            f"Total active threads: {len(_integrations)}"
        )
    else:
        integration = _integrations[thread_id]
        memory_count = integration.memory_adapter.get_memory_count()
        logger.debug(
            f"[INTEGRATION REUSE] Thread: {thread_id} | "
            f"Using existing integration | Stored memories: {memory_count}"
        )
    
    return _integrations[thread_id]


async def initialize_production_smart_memory():
    """Initialize production Smart Memory system"""
    logger.info("Production Smart Memory system initialized")
    return True


async def get_smart_memory_status() -> Dict[str, Any]:
    """Get overall Smart Memory system status"""
    return {
        "smart_memory_available": True,
        "active_threads": len(_integrations),
        "thread_ids": list(_integrations.keys()),
        "system_status": "production_ready",
        "integrations": {
            thread_id: await integration.get_integration_status()
            for thread_id, integration in _integrations.items()
        }
    }