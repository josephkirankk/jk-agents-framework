"""
Smart Memory Agent Module

This module provides intelligent memory retrieval and context optimization
for the JK-Agents Framework, implementing advanced vector search, semantic
ranking, and token budget management for optimal LLM context delivery.
"""

from typing import TYPE_CHECKING

# Core components
try:
    from .memory_agent import SmartMemoryAgent
    from .vector_optimizer import VectorSearchOptimizer  
    from .context_ranker import SemanticContextRanker
    from .token_optimizer import TokenOptimizer, TokenBudget
    from .relevance_filter import RelevanceFilter
    from .memory_types import (
        Memory, MemoryScore, OptimizedContext, SmartMemoryConfig,
        QueryType, MemoryType, MemoryList, ScoreDict, ContextDict
    )
    
    __all__ = [
        "SmartMemoryAgent",
        "VectorSearchOptimizer", 
        "SemanticContextRanker",
        "TokenOptimizer",
        "TokenBudget",
        "RelevanceFilter",
        "Memory",
        "MemoryScore", 
        "OptimizedContext",
        "SmartMemoryConfig",
        "QueryType",
        "MemoryType",
        "MemoryList",
        "ScoreDict",
        "ContextDict"
    ]
    
except ImportError as e:
    # Graceful fallback if dependencies are missing
    import logging
    log = logging.getLogger(__name__)
    log.warning(f"Smart Memory Agent components unavailable: {e}")
    
    __all__ = []

# Version info
__version__ = "1.0.0"
__author__ = "JK-Agents Framework"