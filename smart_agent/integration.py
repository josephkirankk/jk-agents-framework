"""
Smart Memory Agent Integration Module

This module provides integration between the Smart Memory Agent and the
existing JK-Agents Framework, enabling seamless adoption of ML-enhanced
memory capabilities while maintaining backward compatibility.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

from .core import SmartMemoryAgent, SmartMemoryConfig, MemoryContext
from .data_structures import MemoryItem, RetrievalResult, SearchQuery
from ..memory import BaseMemory, MemoryItem as BaseMemoryItem
from ..config import ConfigManager
from ..utils.performance import performance_monitor

logger = logging.getLogger(__name__)


@dataclass
class IntegrationConfig:
    """Configuration for Smart Memory Agent integration"""
    enabled: bool = True
    fallback_to_original: bool = True
    migration_enabled: bool = True
    performance_comparison_enabled: bool = True
    gradual_rollout_percentage: float = 1.0  # 100% by default
    compatibility_mode: bool = True
    
    # Performance thresholds for fallback
    max_response_time_ms: float = 5000.0
    max_memory_usage_mb: float = 512.0
    min_success_rate: float = 0.95


@dataclass 
class IntegrationMetrics:
    """Metrics for tracking integration performance"""
    smart_agent_calls: int = 0
    fallback_calls: int = 0
    average_response_time_ms: float = 0.0
    success_rate: float = 1.0
    memory_usage_mb: float = 0.0
    context_improvement_score: float = 0.0
    token_savings_percentage: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class SmartMemoryIntegration:
    """
    Integration layer between Smart Memory Agent and JK-Agents Framework.
    
    Provides seamless integration while maintaining backward compatibility
    and enabling gradual migration from existing memory systems.
    """
    
    def __init__(
        self,
        original_memory: BaseMemory,
        config: Optional[IntegrationConfig] = None,
        smart_config: Optional[SmartMemoryConfig] = None
    ):
        self.original_memory = original_memory
        self.integration_config = config or IntegrationConfig()
        self.smart_config = smart_config or SmartMemoryConfig()
        self.metrics = IntegrationMetrics()
        
        self._smart_agent: Optional[SmartMemoryAgent] = None
        self._migration_state = {"completed": False, "progress": 0.0}
        self._performance_cache = {}
        self._fallback_reasons = []
        
        logger.info("Smart Memory Integration initialized")
    
    async def initialize(self) -> None:
        """Initialize the Smart Memory Agent and perform any necessary setup"""
        try:
            if self.integration_config.enabled:
                self._smart_agent = SmartMemoryAgent(self.smart_config)
                await self._smart_agent.initialize()
                
                if self.integration_config.migration_enabled:
                    await self._migrate_existing_memories()
                    
                logger.info("Smart Memory Agent integration ready")
            else:
                logger.info("Smart Memory Agent integration disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Smart Memory Agent: {e}")
            if not self.integration_config.fallback_to_original:
                raise
    
    async def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation",
        **kwargs
    ) -> str:
        """Store memory with Smart Agent enhancement when available"""
        start_time = datetime.now()
        
        try:
            # Decide whether to use smart agent or fallback
            if await self._should_use_smart_agent():
                memory_item = MemoryItem(
                    content=content,
                    metadata=metadata or {},
                    memory_type=memory_type,
                    timestamp=datetime.now(),
                    **kwargs
                )
                
                memory_id = await self._smart_agent.store_memory(memory_item)
                await self._update_metrics(start_time, True, "store")
                return memory_id
            else:
                # Fallback to original memory system
                result = await self.original_memory.store(content, metadata, **kwargs)
                await self._update_metrics(start_time, True, "store_fallback")
                return result
                
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            await self._update_metrics(start_time, False, "store")
            
            if self.integration_config.fallback_to_original:
                return await self.original_memory.store(content, metadata, **kwargs)
            raise
    
    async def retrieve_memories(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve memories with Smart Agent optimization when available"""
        start_time = datetime.now()
        
        try:
            if await self._should_use_smart_agent():
                search_query = SearchQuery(
                    query_text=query,
                    limit=limit,
                    memory_type=memory_type,
                    filters=filters or {},
                    **kwargs
                )
                
                context = MemoryContext(
                    current_query=query,
                    conversation_history=[],
                    user_preferences={},
                    session_metadata={}
                )
                
                result = await self._smart_agent.retrieve_optimized_context(
                    search_query, context
                )
                
                # Convert to format expected by JK-Agents Framework
                formatted_memories = await self._format_retrieval_results(result)
                await self._update_metrics(start_time, True, "retrieve", len(formatted_memories))
                return formatted_memories
            else:
                # Fallback to original memory system
                result = await self.original_memory.search(query, limit, **kwargs)
                await self._update_metrics(start_time, True, "retrieve_fallback", len(result))
                return result
                
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            await self._update_metrics(start_time, False, "retrieve")
            
            if self.integration_config.fallback_to_original:
                return await self.original_memory.search(query, limit, **kwargs)
            raise
    
    async def get_context_for_query(
        self,
        query: str,
        max_tokens: Optional[int] = None,
        include_metadata: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Get optimized context for a query using Smart Memory Agent"""
        start_time = datetime.now()
        
        try:
            if await self._should_use_smart_agent():
                search_query = SearchQuery(
                    query_text=query,
                    limit=kwargs.get('limit', 10),
                    memory_type=kwargs.get('memory_type'),
                    filters=kwargs.get('filters', {}),
                    max_tokens=max_tokens
                )
                
                context = MemoryContext(
                    current_query=query,
                    conversation_history=kwargs.get('conversation_history', []),
                    user_preferences=kwargs.get('user_preferences', {}),
                    session_metadata=kwargs.get('session_metadata', {})
                )
                
                result = await self._smart_agent.retrieve_optimized_context(
                    search_query, context
                )
                
                # Format as comprehensive context
                formatted_context = {
                    "query": query,
                    "optimized_memories": [
                        {
                            "content": memory.content,
                            "metadata": memory.metadata if include_metadata else {},
                            "relevance_score": memory.relevance_score,
                            "timestamp": memory.timestamp.isoformat(),
                            "memory_type": memory.memory_type
                        }
                        for memory in result.memories
                    ],
                    "context_summary": result.context_summary,
                    "total_tokens": result.total_tokens,
                    "optimization_applied": result.optimization_applied,
                    "relevance_threshold": result.relevance_threshold,
                    "performance_metrics": {
                        "retrieval_time_ms": result.performance_metrics.get("retrieval_time_ms", 0),
                        "ml_enhancement_time_ms": result.performance_metrics.get("ml_enhancement_time_ms", 0),
                        "total_processing_time_ms": result.performance_metrics.get("total_time_ms", 0)
                    }
                }
                
                await self._update_metrics(start_time, True, "context", len(result.memories))
                return formatted_context
            else:
                # Fallback to simplified context retrieval
                memories = await self.original_memory.search(query, kwargs.get('limit', 10))
                formatted_context = {
                    "query": query,
                    "optimized_memories": memories,
                    "context_summary": f"Retrieved {len(memories)} memories for query",
                    "total_tokens": sum(len(m.get('content', '')) for m in memories) // 4,
                    "optimization_applied": False,
                    "relevance_threshold": 0.0,
                    "performance_metrics": {}
                }
                
                await self._update_metrics(start_time, True, "context_fallback", len(memories))
                return formatted_context
                
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            await self._update_metrics(start_time, False, "context")
            
            if self.integration_config.fallback_to_original:
                memories = await self.original_memory.search(query, kwargs.get('limit', 10))
                return {
                    "query": query,
                    "optimized_memories": memories,
                    "context_summary": f"Retrieved {len(memories)} memories (fallback mode)",
                    "total_tokens": sum(len(m.get('content', '')) for m in memories) // 4,
                    "optimization_applied": False,
                    "relevance_threshold": 0.0,
                    "performance_metrics": {}
                }
            raise
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and metrics"""
        return {
            "smart_agent_enabled": self._smart_agent is not None,
            "integration_config": self.integration_config.__dict__,
            "migration_state": self._migration_state,
            "metrics": self.metrics.__dict__,
            "recent_fallback_reasons": self._fallback_reasons[-10:],  # Last 10 reasons
            "performance_comparison": await self._get_performance_comparison()
        }
    
    async def _should_use_smart_agent(self) -> bool:
        """Determine whether to use Smart Agent or fall back to original memory"""
        if not self.integration_config.enabled or self._smart_agent is None:
            return False
            
        # Check gradual rollout percentage
        if self.integration_config.gradual_rollout_percentage < 1.0:
            import random
            if random.random() > self.integration_config.gradual_rollout_percentage:
                self._fallback_reasons.append(f"Gradual rollout: {self.integration_config.gradual_rollout_percentage}")
                return False
        
        # Check performance thresholds
        if self.metrics.average_response_time_ms > self.integration_config.max_response_time_ms:
            self._fallback_reasons.append(f"High response time: {self.metrics.average_response_time_ms}ms")
            return False
            
        if self.metrics.memory_usage_mb > self.integration_config.max_memory_usage_mb:
            self._fallback_reasons.append(f"High memory usage: {self.metrics.memory_usage_mb}MB")
            return False
            
        if self.metrics.success_rate < self.integration_config.min_success_rate:
            self._fallback_reasons.append(f"Low success rate: {self.metrics.success_rate}")
            return False
        
        return True
    
    async def _migrate_existing_memories(self) -> None:
        """Migrate memories from original system to Smart Memory Agent"""
        try:
            logger.info("Starting memory migration to Smart Memory Agent")
            
            # Get all memories from original system
            # This would need to be implemented based on the specific original memory interface
            # For now, we'll assume a method exists to get all memories
            if hasattr(self.original_memory, 'get_all_memories'):
                original_memories = await self.original_memory.get_all_memories()
                total_memories = len(original_memories)
                migrated = 0
                
                for memory in original_memories:
                    try:
                        memory_item = MemoryItem(
                            content=memory.get('content', ''),
                            metadata=memory.get('metadata', {}),
                            memory_type=memory.get('memory_type', 'conversation'),
                            timestamp=datetime.fromisoformat(memory.get('timestamp', datetime.now().isoformat()))
                        )
                        
                        await self._smart_agent.store_memory(memory_item)
                        migrated += 1
                        
                        # Update migration progress
                        self._migration_state["progress"] = migrated / total_memories
                        
                    except Exception as e:
                        logger.warning(f"Failed to migrate memory: {e}")
                
                self._migration_state["completed"] = True
                logger.info(f"Migration completed: {migrated}/{total_memories} memories migrated")
            else:
                logger.warning("Original memory system does not support full migration")
                
        except Exception as e:
            logger.error(f"Memory migration failed: {e}")
    
    async def _format_retrieval_results(self, result: RetrievalResult) -> List[Dict[str, Any]]:
        """Format Smart Agent retrieval results for JK-Agents Framework compatibility"""
        formatted = []
        
        for memory in result.memories:
            formatted.append({
                "id": getattr(memory, 'id', None),
                "content": memory.content,
                "metadata": memory.metadata,
                "timestamp": memory.timestamp.isoformat(),
                "memory_type": memory.memory_type,
                "relevance_score": memory.relevance_score,
                # Additional Smart Agent specific fields
                "smart_agent_enhanced": True,
                "context_optimized": result.optimization_applied,
                "ml_enhanced": result.performance_metrics.get("ml_enhancement_applied", False)
            })
        
        return formatted
    
    async def _update_metrics(
        self,
        start_time: datetime,
        success: bool,
        operation: str,
        result_count: int = 0
    ) -> None:
        """Update integration performance metrics"""
        response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update operation-specific metrics
        if operation.startswith("store"):
            if success:
                self.metrics.smart_agent_calls += 1
            else:
                self.metrics.fallback_calls += 1
        elif operation.startswith("retrieve") or operation.startswith("context"):
            if success:
                self.metrics.smart_agent_calls += 1
            else:
                self.metrics.fallback_calls += 1
        
        # Update response time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        self.metrics.average_response_time_ms = (
            alpha * response_time_ms + 
            (1 - alpha) * self.metrics.average_response_time_ms
        )
        
        # Update success rate
        total_calls = self.metrics.smart_agent_calls + self.metrics.fallback_calls
        if total_calls > 0:
            self.metrics.success_rate = self.metrics.smart_agent_calls / total_calls
        
        self.metrics.last_updated = datetime.now()
    
    async def _get_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between Smart Agent and original system"""
        if not self.integration_config.performance_comparison_enabled:
            return {}
        
        return {
            "smart_agent_usage_percentage": (
                self.metrics.smart_agent_calls / 
                max(self.metrics.smart_agent_calls + self.metrics.fallback_calls, 1) * 100
            ),
            "average_response_time_improvement": f"{max(0, 100 - self.metrics.average_response_time_ms / 100)}%",
            "token_efficiency_improvement": f"{self.metrics.token_savings_percentage}%",
            "context_quality_improvement": f"{self.metrics.context_improvement_score}%"
        }


# Factory functions for easy integration
async def create_smart_memory_integration(
    original_memory: BaseMemory,
    config_path: Optional[str] = None,
    **kwargs
) -> SmartMemoryIntegration:
    """Create and initialize Smart Memory Integration"""
    # Load configuration
    if config_path:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        integration_config = IntegrationConfig(**config_data.get('integration', {}))
        smart_config_data = config_data.get('smart_agent', {})
        smart_config = SmartMemoryConfig(**smart_config_data)
    else:
        integration_config = IntegrationConfig(**kwargs)
        smart_config = SmartMemoryConfig()
    
    integration = SmartMemoryIntegration(
        original_memory=original_memory,
        config=integration_config,
        smart_config=smart_config
    )
    
    await integration.initialize()
    return integration


def wrap_memory_with_smart_agent(
    memory_instance: BaseMemory,
    **config_kwargs
) -> Callable:
    """
    Decorator/wrapper function to enhance existing memory instances with Smart Agent capabilities
    """
    async def enhanced_memory_wrapper():
        integration = await create_smart_memory_integration(
            memory_instance,
            **config_kwargs
        )
        return integration
    
    return enhanced_memory_wrapper


# Compatibility layer for existing code
class SmartMemoryCompatibilityLayer:
    """
    Compatibility layer that provides the same interface as existing memory systems
    while transparently using Smart Memory Agent capabilities when available.
    """
    
    def __init__(self, integration: SmartMemoryIntegration):
        self.integration = integration
    
    async def store(self, content: str, metadata: Optional[Dict] = None, **kwargs) -> str:
        """Store memory - compatible with existing interface"""
        return await self.integration.store_memory(content, metadata, **kwargs)
    
    async def search(self, query: str, limit: int = 10, **kwargs) -> List[Dict]:
        """Search memories - compatible with existing interface"""
        return await self.integration.retrieve_memories(query, limit, **kwargs)
    
    async def get_context(self, query: str, **kwargs) -> Dict:
        """Get context - enhanced method"""
        return await self.integration.get_context_for_query(query, **kwargs)
    
    @property
    def smart_agent_available(self) -> bool:
        """Check if Smart Agent is available and active"""
        return self.integration._smart_agent is not None
    
    async def get_metrics(self) -> Dict:
        """Get performance and usage metrics"""
        return await self.integration.get_integration_status()