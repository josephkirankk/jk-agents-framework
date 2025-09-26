"""
Relevance Filter

Implements advanced relevance filtering for memory retrieval optimization.
Provides sophisticated filtering based on semantic similarity, contextual relevance,
and adaptive thresholds.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .memory_types import Memory, MemoryList, SmartMemoryConfig, QueryType

log = logging.getLogger(__name__)


class RelevanceFilter:
    """
    Advanced relevance filtering system for memory optimization.
    
    Features:
    - Adaptive threshold adjustment
    - Multi-criteria relevance scoring
    - Context-aware filtering
    - Quality preservation guarantees
    """
    
    def __init__(self, config: SmartMemoryConfig):
        """
        Initialize the Relevance Filter.
        
        Args:
            config: Smart memory configuration
        """
        self.config = config
        
        # Filter statistics
        self.filter_stats = {
            'total_filters': 0,
            'memories_filtered': 0,
            'average_threshold_used': 0.0,
            'quality_improvements': 0
        }
        
        log.info("Relevance Filter initialized")
    
    def filter_memories(self, 
                       memories: MemoryList, 
                       query: str,
                       query_type: Optional[QueryType] = None) -> MemoryList:
        """
        Filter memories based on relevance criteria.
        
        Args:
            memories: List of memories to filter
            query: Original search query
            query_type: Classified query type
            
        Returns:
            Filtered list of relevant memories
        """
        if not memories:
            return memories
        
        try:
            # Calculate adaptive threshold
            adaptive_threshold = self._calculate_adaptive_threshold(memories, query, query_type)
            
            # Apply multi-criteria filtering
            filtered_memories = self._apply_multi_criteria_filter(memories, adaptive_threshold, query)
            
            # Ensure minimum quality preservation
            final_memories = self._ensure_quality_preservation(memories, filtered_memories, query)
            
            # Update statistics
            self._update_filter_stats(len(memories), len(final_memories), adaptive_threshold)
            
            log.info(f"Relevance filtering: {len(final_memories)}/{len(memories)} memories passed "
                    f"(threshold: {adaptive_threshold:.3f})")
            
            return final_memories
            
        except Exception as e:
            log.error(f"Relevance filtering failed: {e}")
            return memories  # Return unfiltered if filtering fails
    
    def _calculate_adaptive_threshold(self, 
                                    memories: MemoryList, 
                                    query: str,
                                    query_type: Optional[QueryType] = None) -> float:
        """
        Calculate adaptive relevance threshold based on memory distribution and query type.
        
        Args:
            memories: List of memories
            query: Search query
            query_type: Query classification
            
        Returns:
            Adaptive threshold value
        """
        base_threshold = self.config.relevance_threshold
        
        if not memories:
            return base_threshold
        
        try:
            # Get relevance scores
            relevance_scores = [m.score.relevance_score for m in memories if m.score.relevance_score > 0]
            
            if not relevance_scores:
                return base_threshold
            
            # Calculate score distribution statistics
            mean_score = np.mean(relevance_scores)
            std_score = np.std(relevance_scores)
            median_score = np.median(relevance_scores)
            
            # Adaptive threshold based on distribution
            if std_score > 0.2:  # High variance - use stricter threshold
                adaptive_threshold = max(base_threshold, mean_score - 0.5 * std_score)
            else:  # Low variance - use more permissive threshold
                adaptive_threshold = max(base_threshold * 0.8, median_score * 0.9)
            
            # Adjust based on query type
            type_adjustments = {
                QueryType.FACTUAL: 1.1,      # Factual queries need higher relevance
                QueryType.CONVERSATIONAL: 0.9, # Conversational can be more permissive
                QueryType.TECHNICAL: 1.05,    # Technical needs good relevance
                QueryType.CREATIVE: 0.85,     # Creative can be more exploratory
                QueryType.ANALYTICAL: 1.0,    # Analytical uses balanced approach
                QueryType.PROCEDURAL: 1.0     # Procedural uses standard approach
            }
            
            adjustment = type_adjustments.get(query_type, 1.0) if query_type else 1.0
            adaptive_threshold *= adjustment
            
            # Ensure reasonable bounds
            adaptive_threshold = max(0.3, min(0.9, adaptive_threshold))
            
            log.debug(f"Adaptive threshold: base={base_threshold:.3f}, calculated={adaptive_threshold:.3f}, "
                     f"mean={mean_score:.3f}, std={std_score:.3f}")
            
            return adaptive_threshold
            
        except Exception as e:
            log.warning(f"Adaptive threshold calculation failed: {e}")
            return base_threshold
    
    def _apply_multi_criteria_filter(self, 
                                   memories: MemoryList, 
                                   threshold: float, 
                                   query: str) -> MemoryList:
        """
        Apply multi-criteria filtering to memories.
        
        Args:
            memories: List of memories to filter
            threshold: Relevance threshold
            query: Search query
            
        Returns:
            Filtered memories
        """
        filtered_memories = []
        
        for memory in memories:
            # Primary criterion: relevance score
            relevance_pass = memory.score.relevance_score >= threshold
            
            # Secondary criteria
            recency_boost = memory.score.recency_score > 0.7  # Recent memories get boost
            importance_boost = memory.score.importance_score > 0.5  # Important memories get boost
            
            # Content quality checks
            content_quality_pass = self._check_content_quality(memory.content, query)
            
            # Combined decision
            if relevance_pass or (content_quality_pass and (recency_boost or importance_boost)):
                filtered_memories.append(memory)
        
        return filtered_memories
    
    def _check_content_quality(self, content: str, query: str) -> bool:
        """
        Check content quality for relevance filtering.
        
        Args:
            content: Memory content
            query: Search query
            
        Returns:
            True if content meets quality standards
        """
        try:
            # Minimum content length
            if len(content.strip()) < 10:
                return False
            
            # Check for keyword overlap (simple heuristic)
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            
            overlap = len(query_words & content_words)
            overlap_ratio = overlap / len(query_words) if query_words else 0
            
            # Content quality based on overlap and structure
            has_good_overlap = overlap_ratio >= 0.2  # At least 20% keyword overlap
            has_structure = any(marker in content for marker in ['Q:', 'A:', '?', '.'])
            
            return has_good_overlap and has_structure
            
        except Exception as e:
            log.warning(f"Content quality check failed: {e}")
            return True  # Default to pass if check fails
    
    def _ensure_quality_preservation(self, 
                                   original_memories: MemoryList,
                                   filtered_memories: MemoryList, 
                                   query: str) -> MemoryList:
        """
        Ensure minimum quality preservation by adding back high-quality memories if needed.
        
        Args:
            original_memories: Original memory list
            filtered_memories: Filtered memory list
            query: Search query
            
        Returns:
            Quality-preserved memory list
        """
        # Ensure we have at least one memory if original list wasn't empty
        if not filtered_memories and original_memories:
            # Add back the highest scoring memory
            best_memory = max(original_memories, key=lambda m: m.score.relevance_score)
            filtered_memories = [best_memory]
            log.info("Added back highest scoring memory to ensure quality preservation")
        
        # Ensure we don't filter too aggressively (keep at least 30% if we had good memories)
        high_quality_originals = [m for m in original_memories if m.score.relevance_score > 0.6]
        
        if len(high_quality_originals) > 3 and len(filtered_memories) < len(high_quality_originals) * 0.3:
            # Add back some high-quality memories
            missing_count = int(len(high_quality_originals) * 0.3) - len(filtered_memories)
            
            # Find high-quality memories not in filtered set
            filtered_ids = {m.memory_id for m in filtered_memories}
            candidates = [m for m in high_quality_originals if m.memory_id not in filtered_ids]
            
            # Sort by score and add back top candidates
            candidates.sort(key=lambda m: m.score.relevance_score, reverse=True)
            filtered_memories.extend(candidates[:missing_count])
            
            log.info(f"Added back {len(candidates[:missing_count])} high-quality memories for preservation")
        
        return filtered_memories
    
    def get_filter_insights(self, 
                           original_memories: MemoryList,
                           filtered_memories: MemoryList) -> Dict[str, Any]:
        """
        Get insights about filtering performance and quality.
        
        Args:
            original_memories: Original memory list
            filtered_memories: Filtered memory list
            
        Returns:
            Dictionary of filtering insights
        """
        if not original_memories:
            return {'status': 'no_memories'}
        
        try:
            # Basic statistics
            filter_ratio = len(filtered_memories) / len(original_memories)
            
            # Quality metrics
            if filtered_memories:
                avg_filtered_relevance = sum(m.score.relevance_score for m in filtered_memories) / len(filtered_memories)
            else:
                avg_filtered_relevance = 0.0
            
            if original_memories:
                avg_original_relevance = sum(m.score.relevance_score for m in original_memories) / len(original_memories)
            else:
                avg_original_relevance = 0.0
            
            quality_improvement = avg_filtered_relevance - avg_original_relevance
            
            insights = {
                'original_count': len(original_memories),
                'filtered_count': len(filtered_memories),
                'filter_ratio': filter_ratio,
                'memories_removed': len(original_memories) - len(filtered_memories),
                'average_original_relevance': avg_original_relevance,
                'average_filtered_relevance': avg_filtered_relevance,
                'quality_improvement': quality_improvement,
                'filtering_effectiveness': quality_improvement > 0.05  # 5% improvement threshold
            }
            
            return insights
            
        except Exception as e:
            log.warning(f"Failed to generate filter insights: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _update_filter_stats(self, original_count: int, filtered_count: int, threshold_used: float):
        """Update filtering performance statistics."""
        self.filter_stats['total_filters'] += 1
        self.filter_stats['memories_filtered'] += (original_count - filtered_count)
        
        # Update average threshold
        current_avg = self.filter_stats['average_threshold_used']
        new_avg = ((current_avg * (self.filter_stats['total_filters'] - 1)) + threshold_used) / self.filter_stats['total_filters']
        self.filter_stats['average_threshold_used'] = new_avg
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """Get current filtering performance statistics."""
        total_processed = self.filter_stats['total_filters'] * 10  # Rough estimate of memories processed
        filter_rate = self.filter_stats['memories_filtered'] / max(1, total_processed)
        
        return {
            **self.filter_stats,
            'filter_rate': filter_rate,
            'average_memories_filtered_per_operation': (
                self.filter_stats['memories_filtered'] / max(1, self.filter_stats['total_filters'])
            )
        }
    
    def update_filter_effectiveness(self, memory_id: str, was_useful: bool):
        """
        Update filter effectiveness based on memory usage feedback.
        
        Args:
            memory_id: ID of the memory that was used
            was_useful: Whether the memory was useful in the context
        """
        if was_useful:
            self.filter_stats['quality_improvements'] += 1
        
        # Could implement more sophisticated learning here
        log.debug(f"Filter effectiveness update: memory {memory_id} was {'useful' if was_useful else 'not useful'}")