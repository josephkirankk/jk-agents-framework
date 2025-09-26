"""
Semantic Context Ranker

Implements multi-factor semantic ranking for memory relevance optimization.
Uses relevance, recency, importance, and coherence scoring to rank memories
for optimal context delivery to LLMs.
"""

import logging
import time
import math
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

from .memory_types import Memory, MemoryList, MemoryScore, SmartMemoryConfig, QueryType

log = logging.getLogger(__name__)


class SemanticContextRanker:
    """
    Advanced semantic ranking system for memory optimization.
    
    Features:
    - Multi-factor scoring with configurable weights
    - Context coherence analysis 
    - Usage-based importance learning
    - Query-aware ranking adaptation
    """
    
    def __init__(self, config: SmartMemoryConfig):
        """
        Initialize the Semantic Context Ranker.
        
        Args:
            config: Smart memory configuration with ranking weights
        """
        self.config = config
        
        # Performance tracking
        self.ranking_stats = {
            'total_rankings': 0,
            'average_ranking_time': 0.0,
            'coherence_calculations': 0,
            'importance_updates': 0
        }
        
        # Memory importance learning
        self.importance_tracker: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            'usage_count': 0.0,
            'effectiveness_score': 0.0,
            'last_used': time.time()
        })
        
        log.info("Semantic Context Ranker initialized")
    
    def rank_memories(self, 
                     memories: MemoryList, 
                     query: str,
                     query_type: Optional[QueryType] = None) -> MemoryList:
        """
        Rank memories using multi-factor semantic scoring.
        
        Args:
            memories: List of memories to rank
            query: Original search query
            query_type: Classified query type for adaptive weighting
            
        Returns:
            Ranked list of memories with computed scores
        """
        if not memories:
            return memories
        
        start_time = time.perf_counter()
        
        try:
            # Step 1: Calculate individual scores for each memory
            for memory in memories:
                self._calculate_memory_scores(memory, query, query_type)
            
            # Step 2: Calculate context coherence scores
            self._calculate_coherence_scores(memories, query)
            
            # Step 3: Compute final weighted scores
            ranking_weights = self._get_adaptive_weights(query_type)
            for memory in memories:
                memory.score.calculate_final_score(ranking_weights)
            
            # Step 4: Sort by final score
            ranked_memories = sorted(memories, key=lambda m: m.score.final_score, reverse=True)
            
            # Step 5: Update performance stats
            ranking_time = (time.perf_counter() - start_time) * 1000
            self._update_ranking_stats(ranking_time, len(memories))
            
            log.info(f"Ranked {len(memories)} memories in {ranking_time:.2f}ms")
            
            return ranked_memories
            
        except Exception as e:
            log.error(f"Memory ranking failed: {e}")
            return memories  # Return unranked if ranking fails
    
    def _calculate_memory_scores(self, 
                                memory: Memory, 
                                query: str, 
                                query_type: Optional[QueryType] = None):
        """
        Calculate individual scores for a memory.
        
        Args:
            memory: Memory object to score
            query: Search query
            query_type: Query classification
        """
        # Relevance score (already calculated by vector optimizer)
        # memory.score.relevance_score should already be set
        
        # Recency score with exponential decay
        memory.score.recency_score = self._calculate_recency_score(memory)
        
        # Importance score based on usage patterns
        memory.score.importance_score = self._calculate_importance_score(memory)
        
        # Update memory access tracking
        memory.update_access()
    
    def _calculate_recency_score(self, memory: Memory) -> float:
        """
        Calculate recency score with configurable decay.
        
        Args:
            memory: Memory object
            
        Returns:
            Recency score (0-1)
        """
        try:
            # Use memory's built-in recency calculation
            # Default decay is 1 week (168 hours)
            decay_hours = 168.0  # Could be made configurable
            recency_score = memory.calculate_recency_score(decay_hours)
            
            # Apply additional boost for very recent memories (last 24 hours)
            age_hours = memory.calculate_age_hours()
            if age_hours < 24:
                boost = (24 - age_hours) / 24 * 0.2  # Up to 20% boost
                recency_score = min(1.0, recency_score + boost)
            
            return recency_score
            
        except Exception as e:
            log.warning(f"Recency calculation failed for memory {memory.memory_id}: {e}")
            return 0.5  # Default moderate score
    
    def _calculate_importance_score(self, memory: Memory) -> float:
        """
        Calculate importance score based on usage patterns and effectiveness.
        
        Args:
            memory: Memory object
            
        Returns:
            Importance score (0-1)
        """
        try:
            memory_id = memory.memory_id
            
            # Get or initialize importance tracking
            tracker = self.importance_tracker[memory_id]
            
            # Base importance from access count (logarithmic scaling)
            access_importance = min(1.0, math.log(memory.access_count + 1) / math.log(10))
            
            # Effectiveness importance (how useful this memory has been)
            effectiveness_importance = memory.effectiveness_score
            
            # Frequency importance (how often used relative to age)
            age_hours = max(1, memory.calculate_age_hours())
            frequency_importance = min(1.0, memory.access_count / (age_hours / 24))
            
            # Combined importance score
            importance_score = (
                0.4 * access_importance +
                0.4 * effectiveness_importance +
                0.2 * frequency_importance
            )
            
            # Update tracker
            tracker['usage_count'] = memory.access_count
            tracker['effectiveness_score'] = memory.effectiveness_score
            tracker['last_used'] = time.time()
            
            return min(1.0, importance_score)
            
        except Exception as e:
            log.warning(f"Importance calculation failed for memory {memory.memory_id}: {e}")
            return 0.3  # Default low-moderate score
    
    def _calculate_coherence_scores(self, memories: MemoryList, query: str):
        """
        Calculate context coherence scores between memories.
        
        Args:
            memories: List of memories
            query: Original query for context
        """
        if len(memories) < 2:
            # Single memory gets default coherence
            for memory in memories:
                memory.score.coherence_score = 0.8
            return
        
        try:
            # Calculate pairwise coherence matrix
            coherence_matrix = self._compute_coherence_matrix(memories)
            
            # Assign coherence scores based on average coherence with other memories
            for i, memory in enumerate(memories):
                # Average coherence with all other memories
                coherence_scores = [coherence_matrix[i][j] for j in range(len(memories)) if i != j]
                
                if coherence_scores:
                    avg_coherence = sum(coherence_scores) / len(coherence_scores)
                    
                    # Boost memories that form good clusters
                    cluster_boost = self._calculate_cluster_boost(i, coherence_matrix)
                    
                    memory.score.coherence_score = min(1.0, avg_coherence + cluster_boost)
                else:
                    memory.score.coherence_score = 0.5
            
            self.ranking_stats['coherence_calculations'] += len(memories) * (len(memories) - 1) // 2
            
        except Exception as e:
            log.warning(f"Coherence calculation failed: {e}")
            # Fallback to default coherence scores
            for memory in memories:
                memory.score.coherence_score = 0.5
    
    def _compute_coherence_matrix(self, memories: MemoryList) -> List[List[float]]:
        """
        Compute semantic coherence matrix between memories.
        
        Args:
            memories: List of memories
            
        Returns:
            Coherence matrix (similarity scores)
        """
        n = len(memories)
        coherence_matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                # Calculate semantic similarity between memory contents
                similarity = self._calculate_content_similarity(
                    memories[i].content, 
                    memories[j].content
                )
                
                coherence_matrix[i][j] = similarity
                coherence_matrix[j][i] = similarity  # Symmetric matrix
        
        # Self-coherence is always 1.0
        for i in range(n):
            coherence_matrix[i][i] = 1.0
        
        return coherence_matrix
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate semantic similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score (0-1)
        """
        try:
            # Simple word overlap similarity (could be enhanced with embeddings)
            words1 = set(content1.lower().split())
            words2 = set(content2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            # Jaccard similarity
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            jaccard_sim = intersection / union if union > 0 else 0.0
            
            # Length similarity factor (penalize very different lengths)
            len_ratio = min(len(content1), len(content2)) / max(len(content1), len(content2))
            length_factor = 0.8 + 0.2 * len_ratio  # 80-100% based on length similarity
            
            return jaccard_sim * length_factor
            
        except Exception as e:
            log.warning(f"Content similarity calculation failed: {e}")
            return 0.3  # Default moderate similarity
    
    def _calculate_cluster_boost(self, memory_index: int, coherence_matrix: List[List[float]]) -> float:
        """
        Calculate boost for memories that form coherent clusters.
        
        Args:
            memory_index: Index of memory to boost
            coherence_matrix: Precomputed coherence matrix
            
        Returns:
            Cluster boost value (0-0.2)
        """
        try:
            high_coherence_threshold = 0.7
            coherence_row = coherence_matrix[memory_index]
            
            # Count memories with high coherence to this one
            high_coherence_count = sum(1 for score in coherence_row if score >= high_coherence_threshold)
            
            # Boost based on cluster size (excluding self)
            cluster_boost = min(0.2, (high_coherence_count - 1) * 0.05)  # Up to 20% boost
            
            return max(0.0, cluster_boost)
            
        except Exception as e:
            log.warning(f"Cluster boost calculation failed: {e}")
            return 0.0
    
    def _get_adaptive_weights(self, query_type: Optional[QueryType] = None) -> Dict[str, float]:
        """
        Get adaptive ranking weights based on query type.
        
        Args:
            query_type: Classified query type
            
        Returns:
            Dictionary of ranking weights
        """
        base_weights = self.config.ranking_weights.copy()
        
        # Adapt weights based on query type
        if query_type == QueryType.FACTUAL:
            # Factual queries prioritize relevance and recency
            base_weights['relevance'] = 0.5
            base_weights['recency'] = 0.3
            base_weights['importance'] = 0.1
            base_weights['coherence'] = 0.1
            
        elif query_type == QueryType.CONVERSATIONAL:
            # Conversational queries benefit from coherence and importance
            base_weights['relevance'] = 0.3
            base_weights['recency'] = 0.2
            base_weights['importance'] = 0.2
            base_weights['coherence'] = 0.3
            
        elif query_type == QueryType.TECHNICAL:
            # Technical queries need relevant and coherent information
            base_weights['relevance'] = 0.4
            base_weights['recency'] = 0.1
            base_weights['importance'] = 0.2
            base_weights['coherence'] = 0.3
            
        elif query_type == QueryType.ANALYTICAL:
            # Analytical queries benefit from all factors
            base_weights['relevance'] = 0.3
            base_weights['recency'] = 0.2
            base_weights['importance'] = 0.25
            base_weights['coherence'] = 0.25
        
        return base_weights
    
    def update_memory_effectiveness(self, memory_id: str, effectiveness_delta: float):
        """
        Update memory effectiveness based on usage feedback.
        
        Args:
            memory_id: ID of the memory to update
            effectiveness_delta: Change in effectiveness (-1.0 to 1.0)
        """
        try:
            tracker = self.importance_tracker[memory_id]
            
            # Update effectiveness with momentum
            current_effectiveness = tracker['effectiveness_score']
            momentum = 0.7  # 70% momentum, 30% new information
            
            new_effectiveness = momentum * current_effectiveness + (1 - momentum) * effectiveness_delta
            tracker['effectiveness_score'] = max(0.0, min(1.0, new_effectiveness))
            
            self.ranking_stats['importance_updates'] += 1
            
            log.debug(f"Updated effectiveness for memory {memory_id}: {new_effectiveness:.3f}")
            
        except Exception as e:
            log.warning(f"Failed to update memory effectiveness: {e}")
    
    def get_memory_insights(self, memories: MemoryList) -> Dict[str, Any]:
        """
        Get insights about memory ranking and quality.
        
        Args:
            memories: List of ranked memories
            
        Returns:
            Dictionary of insights and metrics
        """
        if not memories:
            return {'status': 'no_memories'}
        
        try:
            relevance_scores = [m.score.relevance_score for m in memories]
            recency_scores = [m.score.recency_score for m in memories] 
            importance_scores = [m.score.importance_score for m in memories]
            coherence_scores = [m.score.coherence_score for m in memories]
            final_scores = [m.score.final_score for m in memories]
            
            insights = {
                'memory_count': len(memories),
                'average_relevance': sum(relevance_scores) / len(relevance_scores),
                'average_recency': sum(recency_scores) / len(recency_scores),
                'average_importance': sum(importance_scores) / len(importance_scores),
                'average_coherence': sum(coherence_scores) / len(coherence_scores),
                'average_final_score': sum(final_scores) / len(final_scores),
                'score_range': max(final_scores) - min(final_scores) if final_scores else 0.0,
                'high_quality_memories': sum(1 for score in final_scores if score > 0.7),
                'low_quality_memories': sum(1 for score in final_scores if score < 0.3)
            }
            
            return insights
            
        except Exception as e:
            log.warning(f"Failed to generate memory insights: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _update_ranking_stats(self, ranking_time_ms: float, memory_count: int):
        """Update ranking performance statistics."""
        self.ranking_stats['total_rankings'] += 1
        
        # Update average ranking time
        current_avg = self.ranking_stats['average_ranking_time']
        new_avg = (current_avg * (self.ranking_stats['total_rankings'] - 1) + ranking_time_ms) / self.ranking_stats['total_rankings']
        self.ranking_stats['average_ranking_time'] = new_avg
    
    def get_ranking_statistics(self) -> Dict[str, Any]:
        """Get current ranking performance statistics."""
        avg_coherence_per_ranking = (
            self.ranking_stats['coherence_calculations'] / max(1, self.ranking_stats['total_rankings'])
        )
        
        return {
            **self.ranking_stats,
            'average_coherence_calculations_per_ranking': avg_coherence_per_ranking,
            'importance_tracker_size': len(self.importance_tracker)
        }
    
    def cleanup_old_importance_data(self, max_age_hours: float = 720):  # 30 days
        """Clean up old importance tracking data."""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        old_keys = [
            key for key, tracker in self.importance_tracker.items()
            if tracker['last_used'] < cutoff_time
        ]
        
        for key in old_keys:
            del self.importance_tracker[key]
        
        if old_keys:
            log.info(f"Cleaned up {len(old_keys)} old importance tracking entries")