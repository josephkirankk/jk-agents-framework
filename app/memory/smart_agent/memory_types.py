"""
Memory Types and Data Structures

Defines the core data types used by the Smart Memory Agent for
memory representation, scoring, and context optimization.
"""

import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Types of memories that can be stored."""
    QA_INTERACTION = "qa_interaction"
    TOOL_CALL = "tool_call"  
    SYSTEM_MESSAGE = "system_message"
    USER_CONTEXT = "user_context"
    BUSINESS_CONTEXT = "business_context"
    ERROR_INFO = "error_info"
    PERFORMANCE_METRIC = "performance_metric"


class QueryType(Enum):
    """Classification of query types for context optimization."""
    FACTUAL = "factual"          # Specific facts or information
    CONVERSATIONAL = "conversational"  # General chat or discussion
    TECHNICAL = "technical"       # Technical implementation questions
    CREATIVE = "creative"         # Creative or generative tasks
    ANALYTICAL = "analytical"     # Analysis or reasoning tasks
    PROCEDURAL = "procedural"     # How-to or step-by-step questions


@dataclass
class MemoryScore:
    """Scoring metrics for memory relevance and importance."""
    relevance_score: float = 0.0      # Semantic similarity to query (0-1)
    recency_score: float = 0.0        # Time-based relevance (0-1)
    importance_score: float = 0.0     # Usage-based importance (0-1) 
    coherence_score: float = 0.0      # Context coherence with other memories (0-1)
    final_score: float = 0.0          # Weighted composite score (0-1)
    
    def calculate_final_score(self, weights: Dict[str, float] = None) -> float:
        """Calculate weighted final score."""
        if weights is None:
            weights = {
                'relevance': 0.4,
                'recency': 0.2,
                'importance': 0.2,
                'coherence': 0.2
            }
        
        self.final_score = (
            weights.get('relevance', 0.4) * self.relevance_score +
            weights.get('recency', 0.2) * self.recency_score +
            weights.get('importance', 0.2) * self.importance_score +
            weights.get('coherence', 0.2) * self.coherence_score
        )
        
        return self.final_score


@dataclass 
class Memory:
    """Enhanced memory representation with smart agent capabilities."""
    
    # Core memory data
    content: str
    memory_id: str
    thread_id: str
    user_id: str = "default_user"
    
    # Metadata
    memory_type: MemoryType = MemoryType.QA_INTERACTION
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Smart agent enhancements
    embedding: Optional[List[float]] = None
    tokens: int = 0
    score: MemoryScore = field(default_factory=MemoryScore)
    
    # Usage tracking
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    effectiveness_score: float = 0.0  # How useful this memory has been
    
    # Relationships
    related_memories: List[str] = field(default_factory=list)
    parent_memory: Optional[str] = None
    child_memories: List[str] = field(default_factory=list)
    
    def update_access(self):
        """Update access tracking when memory is retrieved."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def calculate_age_hours(self) -> float:
        """Calculate age of memory in hours."""
        return (time.time() - self.timestamp) / 3600
    
    def calculate_recency_score(self, decay_hours: float = 168) -> float:
        """Calculate recency score with exponential decay (default 1 week)."""
        age_hours = self.calculate_age_hours()
        return max(0.0, 1.0 - (age_hours / decay_hours))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            'content': self.content,
            'memory_id': self.memory_id,
            'thread_id': self.thread_id,
            'user_id': self.user_id,
            'memory_type': self.memory_type.value,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'tokens': self.tokens,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed,
            'effectiveness_score': self.effectiveness_score,
            'related_memories': self.related_memories,
            'parent_memory': self.parent_memory,
            'child_memories': self.child_memories
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        """Create Memory from dictionary."""
        memory_type = MemoryType(data.get('memory_type', 'qa_interaction'))
        
        memory = cls(
            content=data['content'],
            memory_id=data['memory_id'],
            thread_id=data['thread_id'],
            user_id=data.get('user_id', 'default_user'),
            memory_type=memory_type,
            timestamp=data.get('timestamp', time.time()),
            metadata=data.get('metadata', {}),
            tokens=data.get('tokens', 0),
            access_count=data.get('access_count', 0),
            last_accessed=data.get('last_accessed', time.time()),
            effectiveness_score=data.get('effectiveness_score', 0.0),
            related_memories=data.get('related_memories', []),
            parent_memory=data.get('parent_memory'),
            child_memories=data.get('child_memories', [])
        )
        
        return memory


@dataclass
class OptimizedContext:
    """Optimized context result from smart memory agent."""
    
    # Context content
    formatted_context: str
    selected_memories: List[Memory]
    
    # Optimization metrics  
    total_tokens: int
    target_tokens: int
    compression_ratio: float
    relevance_threshold: float
    
    # Quality metrics
    average_relevance_score: float
    context_coherence_score: float
    information_density: float  # Information per token
    
    # Processing info
    query: str
    query_type: QueryType
    processing_time_ms: float
    memories_considered: int
    memories_filtered: int
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization results."""
        return {
            'context_length': len(self.formatted_context),
            'token_count': self.total_tokens,
            'token_efficiency': self.total_tokens / self.target_tokens if self.target_tokens > 0 else 1.0,
            'compression_ratio': self.compression_ratio,
            'average_relevance': self.average_relevance_score,
            'coherence_score': self.context_coherence_score,
            'information_density': self.information_density,
            'memories_used': len(self.selected_memories),
            'selection_ratio': len(self.selected_memories) / self.memories_considered if self.memories_considered > 0 else 0,
            'processing_time_ms': self.processing_time_ms
        }


@dataclass
class SmartMemoryConfig:
    """Configuration for Smart Memory Agent."""
    
    # Search parameters
    max_candidate_memories: int = 10
    relevance_threshold: float = 0.7
    max_context_tokens: int = 2000
    
    # Ranking weights
    ranking_weights: Dict[str, float] = field(default_factory=lambda: {
        'relevance': 0.4,
        'recency': 0.2, 
        'importance': 0.2,
        'coherence': 0.2
    })
    
    # Compression settings
    enable_compression: bool = True
    summarization_threshold: int = 500  # Summarize memories longer than this
    deduplication_threshold: float = 0.85  # Semantic similarity threshold for dedup
    
    # Adaptation settings
    enable_query_classification: bool = True
    enable_context_strategy_selection: bool = True
    enable_adaptive_memory_window: bool = True
    
    # Performance settings
    enable_async_processing: bool = True
    cache_relevance_scores: bool = True
    batch_processing_threshold: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'max_candidate_memories': self.max_candidate_memories,
            'relevance_threshold': self.relevance_threshold,
            'max_context_tokens': self.max_context_tokens,
            'ranking_weights': self.ranking_weights,
            'enable_compression': self.enable_compression,
            'summarization_threshold': self.summarization_threshold,
            'deduplication_threshold': self.deduplication_threshold,
            'enable_query_classification': self.enable_query_classification,
            'enable_context_strategy_selection': self.enable_context_strategy_selection,
            'enable_adaptive_memory_window': self.enable_adaptive_memory_window,
            'enable_async_processing': self.enable_async_processing,
            'cache_relevance_scores': self.cache_relevance_scores,
            'batch_processing_threshold': self.batch_processing_threshold
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SmartMemoryConfig':
        """Create from dictionary."""
        return cls(
            max_candidate_memories=data.get('max_candidate_memories', 10),
            relevance_threshold=data.get('relevance_threshold', 0.7),
            max_context_tokens=data.get('max_context_tokens', 2000),
            ranking_weights=data.get('ranking_weights', {
                'relevance': 0.4, 'recency': 0.2, 'importance': 0.2, 'coherence': 0.2
            }),
            enable_compression=data.get('enable_compression', True),
            summarization_threshold=data.get('summarization_threshold', 500),
            deduplication_threshold=data.get('deduplication_threshold', 0.85),
            enable_query_classification=data.get('enable_query_classification', True),
            enable_context_strategy_selection=data.get('enable_context_strategy_selection', True),
            enable_adaptive_memory_window=data.get('enable_adaptive_memory_window', True),
            enable_async_processing=data.get('enable_async_processing', True),
            cache_relevance_scores=data.get('cache_relevance_scores', True),
            batch_processing_threshold=data.get('batch_processing_threshold', 5)
        )


# Type aliases for convenience
MemoryList = List[Memory]
ScoreDict = Dict[str, float]
ContextDict = Dict[str, Any]