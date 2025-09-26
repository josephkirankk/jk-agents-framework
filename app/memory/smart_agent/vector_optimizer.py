"""
Vector Search Optimizer

Implements advanced vector search optimization with dynamic K selection,
relevance filtering, and multi-stage retrieval for optimal memory retrieval.
"""

import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from .memory_types import Memory, MemoryList, SmartMemoryConfig, QueryType
from ..simple_chromadb_memory import SimpleChromaDBMemory

log = logging.getLogger(__name__)


class VectorSearchOptimizer:
    """
    Advanced vector search optimizer for intelligent memory retrieval.
    
    Features:
    - Dynamic K selection based on query complexity
    - Multi-stage retrieval with progressive filtering
    - Relevance threshold-based filtering
    - Query-aware search strategy adaptation
    """
    
    def __init__(self, 
                 memory_store: SimpleChromaDBMemory,
                 config: SmartMemoryConfig,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Vector Search Optimizer.
        
        Args:
            memory_store: ChromaDB memory store instance
            config: Smart memory configuration
            embedding_model: Sentence transformer model for embeddings
        """
        self.memory_store = memory_store
        self.config = config
        self.embedding_model_name = embedding_model
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            log.info(f"Loaded embedding model: {embedding_model}")
        except Exception as e:
            log.warning(f"Failed to load embedding model {embedding_model}: {e}")
            self.embedding_model = None
        
        # Cache for computed embeddings and relevance scores
        self._embedding_cache: Dict[str, np.ndarray] = {}
        self._relevance_cache: Dict[str, Dict[str, float]] = {}
        
        # Performance metrics
        self.search_stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'average_retrieval_time': 0.0,
            'relevance_filter_reductions': 0
        }
    
    def retrieve_memories(self, 
                         query: str,
                         thread_id: str,
                         user_id: str = "default_user",
                         query_type: Optional[QueryType] = None) -> MemoryList:
        """
        Retrieve and optimize memories for the given query.
        
        Args:
            query: Search query
            thread_id: Thread identifier for context
            user_id: User identifier
            query_type: Classified query type for strategy selection
            
        Returns:
            List of optimized memories ranked by relevance
        """
        start_time = time.perf_counter()
        
        try:
            # Stage 1: Dynamic K selection
            dynamic_k = self._calculate_dynamic_k(query, query_type)
            
            # Stage 2: Wide net retrieval
            candidates = self._retrieve_candidates(query, dynamic_k, thread_id)
            
            # Stage 3: Relevance filtering
            filtered_memories = self._filter_by_relevance(candidates, query)
            
            # Stage 4: Convert to Memory objects with enhanced metadata
            enhanced_memories = self._enhance_memory_objects(filtered_memories, query, thread_id, user_id)
            
            # Update performance statistics
            retrieval_time = (time.perf_counter() - start_time) * 1000
            self._update_search_stats(retrieval_time, len(candidates), len(enhanced_memories))
            
            log.info(f"Vector search: {len(enhanced_memories)} memories from {len(candidates)} candidates "
                    f"in {retrieval_time:.2f}ms")
            
            return enhanced_memories
            
        except Exception as e:
            log.error(f"Vector search optimization failed: {e}")
            # Fallback to basic search
            return self._fallback_search(query, thread_id, user_id)
    
    def _calculate_dynamic_k(self, query: str, query_type: Optional[QueryType] = None) -> int:
        """
        Calculate dynamic K value based on query complexity and type.
        
        Args:
            query: Search query
            query_type: Classified query type
            
        Returns:
            Optimized K value for retrieval
        """
        base_k = self.config.max_candidate_memories
        
        # Adjust based on query length (longer queries might need more candidates)
        query_length_factor = min(2.0, len(query.split()) / 10.0)
        
        # Adjust based on query type
        type_multipliers = {
            QueryType.FACTUAL: 0.8,      # Specific facts need fewer candidates
            QueryType.CONVERSATIONAL: 1.2, # Conversational needs more context
            QueryType.TECHNICAL: 1.5,     # Technical queries benefit from more examples
            QueryType.CREATIVE: 1.0,      # Creative is balanced
            QueryType.ANALYTICAL: 1.3,    # Analysis benefits from multiple perspectives  
            QueryType.PROCEDURAL: 1.1     # Procedures need step-by-step context
        }
        
        type_multiplier = type_multipliers.get(query_type, 1.0) if query_type else 1.0
        
        # Calculate dynamic K
        dynamic_k = int(base_k * query_length_factor * type_multiplier)
        
        # Ensure reasonable bounds
        dynamic_k = max(5, min(dynamic_k, 25))
        
        log.debug(f"Dynamic K calculation: base={base_k}, length_factor={query_length_factor:.2f}, "
                 f"type_multiplier={type_multiplier:.2f}, result={dynamic_k}")
        
        return dynamic_k
    
    def _retrieve_candidates(self, query: str, k: int, thread_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve candidate memories using vector similarity search.
        
        Args:
            query: Search query
            k: Number of candidates to retrieve
            thread_id: Thread context
            
        Returns:
            List of candidate memory documents
        """
        try:
            # Use ChromaDB's vector search capabilities
            retriever = self.memory_store.vector_store.as_retriever(
                search_kwargs={"k": k, "filter": {"thread_id": thread_id}}
            )
            
            documents = retriever.get_relevant_documents(query)
            
            # Convert to dictionaries with metadata
            candidates = []
            for doc in documents:
                candidate = {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': getattr(doc, 'similarity_score', 0.0)
                }
                candidates.append(candidate)
            
            return candidates
            
        except Exception as e:
            log.warning(f"Candidate retrieval failed: {e}")
            return []
    
    def _filter_by_relevance(self, candidates: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Filter candidates based on relevance threshold.
        
        Args:
            candidates: List of candidate memories
            query: Original search query
            
        Returns:
            Filtered list of relevant memories
        """
        if not candidates or not self.embedding_model:
            return candidates
        
        try:
            # Get query embedding
            query_embedding = self._get_query_embedding(query)
            if query_embedding is None:
                return candidates
            
            filtered_candidates = []
            
            for candidate in candidates:
                # Calculate semantic similarity
                content = candidate['content']
                content_embedding = self._get_content_embedding(content)
                
                if content_embedding is not None:
                    similarity = cosine_similarity([query_embedding], [content_embedding])[0][0]
                    candidate['relevance_score'] = float(similarity)
                    
                    # Apply relevance threshold
                    if similarity >= self.config.relevance_threshold:
                        filtered_candidates.append(candidate)
                else:
                    # Keep if we can't calculate embedding (fallback)
                    candidate['relevance_score'] = 0.5
                    filtered_candidates.append(candidate)
            
            # Sort by relevance score
            filtered_candidates.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            reduction = len(candidates) - len(filtered_candidates)
            if reduction > 0:
                self.search_stats['relevance_filter_reductions'] += reduction
                log.debug(f"Relevance filtering: {reduction} candidates filtered out "
                         f"(threshold: {self.config.relevance_threshold})")
            
            return filtered_candidates
            
        except Exception as e:
            log.warning(f"Relevance filtering failed: {e}")
            return candidates
    
    def _enhance_memory_objects(self, 
                               filtered_memories: List[Dict[str, Any]], 
                               query: str,
                               thread_id: str,
                               user_id: str) -> MemoryList:
        """
        Convert filtered candidates to enhanced Memory objects.
        
        Args:
            filtered_memories: Filtered memory candidates
            query: Original query
            thread_id: Thread identifier
            user_id: User identifier
            
        Returns:
            List of enhanced Memory objects
        """
        enhanced_memories = []
        
        for i, mem_data in enumerate(filtered_memories):
            try:
                # Create enhanced Memory object
                memory = Memory(
                    content=mem_data['content'],
                    memory_id=mem_data.get('metadata', {}).get('memory_id', f"mem_{int(time.time()*1000)}_{i}"),
                    thread_id=thread_id,
                    user_id=user_id,
                    metadata=mem_data.get('metadata', {}),
                    timestamp=mem_data.get('metadata', {}).get('timestamp', time.time()),
                    tokens=self._estimate_tokens(mem_data['content'])
                )
                
                # Set relevance score from filtering
                memory.score.relevance_score = mem_data.get('relevance_score', 0.0)
                
                enhanced_memories.append(memory)
                
            except Exception as e:
                log.warning(f"Failed to enhance memory object: {e}")
                continue
        
        return enhanced_memories
    
    def _get_query_embedding(self, query: str) -> Optional[np.ndarray]:
        """Get or compute embedding for query with caching."""
        if not self.config.cache_relevance_scores:
            if self.embedding_model:
                return self.embedding_model.encode([query])[0]
            return None
        
        # Check cache
        cache_key = f"query_{hash(query)}"
        if cache_key in self._embedding_cache:
            self.search_stats['cache_hits'] += 1
            return self._embedding_cache[cache_key]
        
        # Compute and cache
        if self.embedding_model:
            embedding = self.embedding_model.encode([query])[0]
            self._embedding_cache[cache_key] = embedding
            return embedding
        
        return None
    
    def _get_content_embedding(self, content: str) -> Optional[np.ndarray]:
        """Get or compute embedding for content with caching."""
        if not self.config.cache_relevance_scores:
            if self.embedding_model:
                return self.embedding_model.encode([content])[0]
            return None
        
        # Check cache
        cache_key = f"content_{hash(content)}"
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # Compute and cache
        if self.embedding_model:
            embedding = self.embedding_model.encode([content])[0]
            self._embedding_cache[cache_key] = embedding
            return embedding
        
        return None
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimation: ~0.75 tokens per word
        words = len(text.split())
        return int(words * 0.75)
    
    def _update_search_stats(self, retrieval_time_ms: float, candidates_count: int, final_count: int):
        """Update performance statistics."""
        self.search_stats['total_searches'] += 1
        
        # Update average retrieval time
        current_avg = self.search_stats['average_retrieval_time']
        new_avg = (current_avg * (self.search_stats['total_searches'] - 1) + retrieval_time_ms) / self.search_stats['total_searches']
        self.search_stats['average_retrieval_time'] = new_avg
    
    def _fallback_search(self, query: str, thread_id: str, user_id: str) -> MemoryList:
        """Fallback to basic search if optimization fails."""
        try:
            log.info("Using fallback search due to optimization failure")
            basic_memories = self.memory_store.search_memories(query, k=3)
            
            fallback_memories = []
            for i, content in enumerate(basic_memories):
                memory = Memory(
                    content=content,
                    memory_id=f"fallback_{int(time.time()*1000)}_{i}",
                    thread_id=thread_id,
                    user_id=user_id,
                    tokens=self._estimate_tokens(content)
                )
                fallback_memories.append(memory)
            
            return fallback_memories
            
        except Exception as e:
            log.error(f"Fallback search also failed: {e}")
            return []
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get current search performance statistics."""
        cache_hit_rate = self.search_stats['cache_hits'] / max(1, self.search_stats['total_searches'])
        
        return {
            **self.search_stats,
            'cache_hit_rate': cache_hit_rate,
            'embedding_cache_size': len(self._embedding_cache),
            'relevance_cache_size': len(self._relevance_cache)
        }
    
    def clear_caches(self):
        """Clear embedding and relevance caches."""
        self._embedding_cache.clear()
        self._relevance_cache.clear()
        log.info("Vector search caches cleared")
    
    def optimize_cache_size(self, max_cache_size: int = 1000):
        """Optimize cache size by removing least recently used items."""
        if len(self._embedding_cache) > max_cache_size:
            # Simple LRU implementation - remove oldest entries
            items_to_remove = len(self._embedding_cache) - max_cache_size
            keys_to_remove = list(self._embedding_cache.keys())[:items_to_remove]
            
            for key in keys_to_remove:
                del self._embedding_cache[key]
                
            log.info(f"Optimized embedding cache: removed {items_to_remove} items")