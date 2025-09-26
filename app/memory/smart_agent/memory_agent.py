"""
Smart Memory Agent with Python MCP Integration

Main orchestrator for intelligent memory retrieval and context optimization.
Integrates with Python MCP server for advanced vector computations and 
machine learning-enhanced memory operations.
"""

import logging
import time
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from .memory_types import (
    Memory, MemoryList, SmartMemoryConfig, OptimizedContext, QueryType, 
    MemoryType, MemoryScore
)
from .vector_optimizer import VectorSearchOptimizer
from .context_ranker import SemanticContextRanker
from .token_optimizer import TokenOptimizer
from .relevance_filter import RelevanceFilter
from ..simple_chromadb_memory import SimpleChromaDBMemory

log = logging.getLogger(__name__)


class SmartMemoryAgent:
    """
    Advanced memory agent with Python MCP server integration.
    
    Features:
    - Python MCP-enhanced vector computations
    - ML-powered memory analysis and optimization
    - Advanced statistical processing
    - Real-time performance analytics
    - Adaptive learning capabilities
    """
    
    def __init__(self, 
                 memory_store: SimpleChromaDBMemory,
                 config: Optional[SmartMemoryConfig] = None,
                 mcp_server_client = None):
        """
        Initialize the Smart Memory Agent.
        
        Args:
            memory_store: ChromaDB memory store
            config: Smart memory configuration
            mcp_server_client: Python MCP server client for computations
        """
        self.memory_store = memory_store
        self.config = config or SmartMemoryConfig()
        self.mcp_client = mcp_server_client
        
        # Initialize core components
        self.vector_optimizer = VectorSearchOptimizer(memory_store, self.config)
        self.context_ranker = SemanticContextRanker(self.config)
        self.token_optimizer = TokenOptimizer(self.config)
        self.relevance_filter = RelevanceFilter(self.config)
        
        # Performance tracking
        self.agent_stats = {
            'total_optimizations': 0,
            'mcp_computations': 0,
            'average_processing_time': 0.0,
            'quality_improvements': 0.0,
            'ml_enhancements_used': 0
        }
        
        # ML enhancement cache
        self.ml_cache = {
            'embedding_models': {},
            'clustering_results': {},
            'similarity_matrices': {},
            'pattern_analysis': {}
        }
        
        log.info("Smart Memory Agent initialized with Python MCP integration")
    
    async def optimize_memory_retrieval(self, 
                                      query: str,
                                      thread_id: str,
                                      user_id: str = "default_user",
                                      system_context: str = "",
                                      enable_ml_enhancements: bool = True) -> OptimizedContext:
        """
        Main entry point for optimized memory retrieval.
        
        Args:
            query: Search query
            thread_id: Thread identifier
            user_id: User identifier
            system_context: System/business context
            enable_ml_enhancements: Whether to use Python MCP ML features
            
        Returns:
            Optimized context with enhanced vector search
        """
        start_time = time.perf_counter()
        
        try:
            log.info(f"Starting smart memory optimization for query: {query[:50]}...")
            
            # Step 1: Query classification using ML if available
            query_type = await self._classify_query_with_ml(query) if enable_ml_enhancements else None
            
            # Step 2: Enhanced vector search with ML optimization
            candidate_memories = await self._enhanced_vector_search(
                query, thread_id, user_id, query_type, enable_ml_enhancements
            )
            
            # Step 3: ML-enhanced relevance filtering
            if enable_ml_enhancements:
                candidate_memories = await self._ml_enhanced_filtering(candidate_memories, query, query_type)
            else:
                candidate_memories = self.relevance_filter.filter_memories(candidate_memories, query, query_type)
            
            # Step 4: Advanced semantic ranking with ML features
            ranked_memories = await self._ml_enhanced_ranking(candidate_memories, query, query_type, enable_ml_enhancements)
            
            # Step 5: Intelligent token optimization
            optimized_context = self.token_optimizer.optimize_context(
                ranked_memories, query, system_context, query_type
            )
            
            # Step 6: ML-powered quality enhancement
            if enable_ml_enhancements and self.mcp_client:
                optimized_context = await self._enhance_context_with_ml(optimized_context, query)
            
            # Update performance statistics
            processing_time = (time.perf_counter() - start_time) * 1000
            self._update_agent_stats(processing_time, enable_ml_enhancements)
            
            log.info(f"Smart memory optimization completed in {processing_time:.2f}ms: "
                    f"{len(optimized_context.selected_memories)} memories selected")
            
            return optimized_context
            
        except Exception as e:
            log.error(f"Smart memory optimization failed: {e}")
            return await self._create_fallback_context(query, thread_id, user_id, system_context)
    
    async def _classify_query_with_ml(self, query: str) -> Optional[QueryType]:
        """
        Classify query type using Python MCP server machine learning.
        
        Args:
            query: Query to classify
            
        Returns:
            Classified query type or None if classification fails
        """
        if not self.mcp_client:
            return None
        
        try:
            # Python code for query classification
            classification_code = f'''
import re
from typing import Dict, Tuple

def classify_query(query: str) -> Tuple[str, float]:
    """Classify query using ML-based approach."""
    query_lower = query.lower()
    
    # Feature extraction
    features = {{
        "length": len(query.split()),
        "has_question": "?" in query,
        "has_what": any(word in query_lower for word in ["what", "which", "where", "when", "who"]),
        "has_how": any(word in query_lower for word in ["how", "why", "explain"]),
        "has_technical": any(word in query_lower for word in ["code", "function", "api", "implementation", "algorithm"]),
        "has_creative": any(word in query_lower for word in ["create", "generate", "design", "build", "make"]),
        "has_analytical": any(word in query_lower for word in ["analyze", "compare", "evaluate", "assess", "review"]),
        "has_procedural": any(word in query_lower for word in ["step", "process", "procedure", "guide", "tutorial"])
    }}
    
    # Simple ML-based classification logic
    if features["has_technical"] and features["has_how"]:
        return ("technical", 0.85)
    elif features["has_creative"]:
        return ("creative", 0.80)
    elif features["has_analytical"]:
        return ("analytical", 0.82)
    elif features["has_procedural"] or "step" in query_lower:
        return ("procedural", 0.78)
    elif features["has_what"] and features["length"] < 8:
        return ("factual", 0.88)
    else:
        return ("conversational", 0.70)

# Execute classification
query_text = "{query.replace('"', '\\"')}"
classification_result, confidence = classify_query(query_text)
print(f"Classification: {{classification_result}}, Confidence: {{confidence:.2f}}")
'''
            
            # Execute via MCP
            result = await self._execute_python_code(classification_code)
            
            if result and "Classification:" in result:
                # Parse result
                parts = result.split("Classification: ")[1].split(", Confidence: ")
                if len(parts) == 2:
                    query_type_str = parts[0].strip()
                    confidence = float(parts[1].strip())
                    
                    # Map to QueryType enum
                    type_mapping = {
                        "factual": QueryType.FACTUAL,
                        "conversational": QueryType.CONVERSATIONAL,
                        "technical": QueryType.TECHNICAL,
                        "creative": QueryType.CREATIVE,
                        "analytical": QueryType.ANALYTICAL,
                        "procedural": QueryType.PROCEDURAL
                    }
                    
                    classified_type = type_mapping.get(query_type_str)
                    if classified_type and confidence > 0.7:
                        log.info(f"Query classified as {classified_type.value} (confidence: {confidence:.2f})")
                        self.agent_stats['ml_enhancements_used'] += 1
                        return classified_type
            
        except Exception as e:
            log.warning(f"ML query classification failed: {e}")
        
        return None
    
    async def _enhanced_vector_search(self, 
                                    query: str,
                                    thread_id: str,
                                    user_id: str,
                                    query_type: Optional[QueryType],
                                    use_ml: bool) -> MemoryList:
        """
        Enhanced vector search with optional ML optimizations.
        
        Args:
            query: Search query
            thread_id: Thread identifier
            user_id: User identifier
            query_type: Classified query type
            use_ml: Whether to use ML enhancements
            
        Returns:
            List of candidate memories
        """
        # Standard vector search
        memories = self.vector_optimizer.retrieve_memories(query, thread_id, user_id, query_type)
        
        if not use_ml or not self.mcp_client or len(memories) < 2:
            return memories
        
        try:
            # Enhance with ML-based similarity refinement
            enhanced_memories = await self._refine_similarities_with_ml(memories, query)
            return enhanced_memories if enhanced_memories else memories
            
        except Exception as e:
            log.warning(f"ML vector search enhancement failed: {e}")
            return memories
    
    async def _refine_similarities_with_ml(self, memories: MemoryList, query: str) -> Optional[MemoryList]:
        """
        Refine similarity scores using advanced ML techniques via Python MCP.
        
        Args:
            memories: List of memories to refine
            query: Original query
            
        Returns:
            Memories with refined similarity scores or None if failed
        """
        if not self.mcp_client or len(memories) < 2:
            return None
        
        try:
            # Prepare data for ML processing
            memory_texts = [m.content for m in memories]
            current_scores = [m.score.relevance_score for m in memories]
            
            ml_refinement_code = f'''
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json

def refine_similarities(query: str, memory_texts: list, current_scores: list):
    """Refine similarity scores using advanced techniques."""
    
    # Create TF-IDF vectors
    all_texts = [query] + memory_texts
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),
        max_features=1000
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate refined similarities
        query_vector = tfidf_matrix[0]
        memory_vectors = tfidf_matrix[1:]
        
        refined_scores = cosine_similarity(query_vector, memory_vectors)[0]
        
        # Combine with existing scores (weighted average)
        final_scores = []
        for i, (current, refined) in enumerate(zip(current_scores, refined_scores)):
            # Weight: 60% refined TF-IDF, 40% original embedding score
            combined_score = 0.6 * float(refined) + 0.4 * float(current)
            final_scores.append(max(0.0, min(1.0, combined_score)))
        
        return final_scores
        
    except Exception as e:
        print(f"Refinement error: {{e}}")
        return current_scores

# Execute refinement
query_text = "{query.replace('"', '\\"')}"
memory_texts = {json.dumps(memory_texts)}
current_scores = {current_scores}

refined_scores = refine_similarities(query_text, memory_texts, current_scores)
print("REFINED_SCORES:", json.dumps(refined_scores))
'''
            
            # Execute via MCP
            result = await self._execute_python_code(ml_refinement_code)
            
            if result and "REFINED_SCORES:" in result:
                # Parse refined scores
                scores_json = result.split("REFINED_SCORES:")[1].strip()
                refined_scores = json.loads(scores_json)
                
                # Update memory scores
                for i, memory in enumerate(memories):
                    if i < len(refined_scores):
                        memory.score.relevance_score = refined_scores[i]
                
                # Sort by refined scores
                memories.sort(key=lambda m: m.score.relevance_score, reverse=True)
                
                log.info("Applied ML-based similarity refinement")
                self.agent_stats['ml_enhancements_used'] += 1
                return memories
            
        except Exception as e:
            log.warning(f"ML similarity refinement failed: {e}")
        
        return None
    
    async def _ml_enhanced_filtering(self, 
                                   memories: MemoryList, 
                                   query: str,
                                   query_type: Optional[QueryType]) -> MemoryList:
        """
        Apply ML-enhanced filtering using statistical analysis.
        
        Args:
            memories: Memories to filter
            query: Original query
            query_type: Query classification
            
        Returns:
            Filtered memories
        """
        if not self.mcp_client or len(memories) < 3:
            return self.relevance_filter.filter_memories(memories, query, query_type)
        
        try:
            # Use Python MCP for statistical filtering
            scores = [m.score.relevance_score for m in memories]
            
            statistical_filtering_code = f'''
import numpy as np
import json
from scipy import stats

def statistical_filter(scores: list, base_threshold: float = 0.7):
    """Apply statistical filtering to identify optimal threshold."""
    scores_array = np.array(scores)
    
    if len(scores_array) < 3:
        return base_threshold
    
    # Calculate statistics
    mean_score = np.mean(scores_array)
    std_score = np.std(scores_array)
    median_score = np.median(scores_array)
    
    # Detect outliers using IQR
    q75, q25 = np.percentile(scores_array, [75, 25])
    iqr = q75 - q25
    
    # Adaptive threshold based on distribution
    if std_score > 0.2:  # High variance
        adaptive_threshold = max(base_threshold, mean_score - 0.3 * std_score)
    else:  # Low variance
        adaptive_threshold = max(base_threshold * 0.85, median_score * 0.9)
    
    # Ensure we don't filter too aggressively
    high_quality_count = sum(1 for score in scores_array if score > 0.6)
    if high_quality_count > 2:
        adaptive_threshold = min(adaptive_threshold, q25)  # Don't go below 25th percentile
    
    return float(adaptive_threshold)

# Calculate optimal threshold
scores = {scores}
optimal_threshold = statistical_filter(scores, {self.config.relevance_threshold})
print("OPTIMAL_THRESHOLD:", optimal_threshold)
'''
            
            result = await self._execute_python_code(statistical_filtering_code)
            
            if result and "OPTIMAL_THRESHOLD:" in result:
                optimal_threshold = float(result.split("OPTIMAL_THRESHOLD:")[1].strip())
                
                # Apply the ML-calculated threshold
                filtered_memories = [
                    m for m in memories 
                    if m.score.relevance_score >= optimal_threshold
                ]
                
                # Ensure we have at least one memory
                if not filtered_memories and memories:
                    filtered_memories = [max(memories, key=lambda m: m.score.relevance_score)]
                
                log.info(f"Applied ML statistical filtering: {len(filtered_memories)}/{len(memories)} memories "
                        f"(threshold: {optimal_threshold:.3f})")
                self.agent_stats['ml_enhancements_used'] += 1
                return filtered_memories
            
        except Exception as e:
            log.warning(f"ML statistical filtering failed: {e}")
        
        # Fallback to standard filtering
        return self.relevance_filter.filter_memories(memories, query, query_type)
    
    async def _ml_enhanced_ranking(self, 
                                 memories: MemoryList,
                                 query: str,
                                 query_type: Optional[QueryType],
                                 use_ml: bool) -> MemoryList:
        """
        Apply ML-enhanced ranking with advanced scoring.
        
        Args:
            memories: Memories to rank
            query: Original query
            query_type: Query classification
            use_ml: Whether to use ML enhancements
            
        Returns:
            Ranked memories
        """
        # Always apply standard ranking first
        ranked_memories = self.context_ranker.rank_memories(memories, query, query_type)
        
        if not use_ml or not self.mcp_client or len(ranked_memories) < 2:
            return ranked_memories
        
        try:
            # Apply ML-enhanced ranking with clustering analysis
            enhanced_ranking = await self._apply_clustering_analysis(ranked_memories, query)
            return enhanced_ranking if enhanced_ranking else ranked_memories
            
        except Exception as e:
            log.warning(f"ML enhanced ranking failed: {e}")
            return ranked_memories
    
    async def _apply_clustering_analysis(self, memories: MemoryList, query: str) -> Optional[MemoryList]:
        """
        Apply clustering analysis to improve memory ranking.
        
        Args:
            memories: Memories to analyze
            query: Original query
            
        Returns:
            Re-ranked memories based on clustering or None if failed
        """
        if len(memories) < 3:
            return None
        
        try:
            memory_contents = [m.content for m in memories]
            current_scores = [m.score.final_score for m in memories]
            
            clustering_code = f'''
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import json

def clustering_analysis(query: str, memory_contents: list, current_scores: list):
    """Apply clustering analysis to improve ranking."""
    
    try:
        # Create TF-IDF vectors
        all_texts = [query] + memory_contents
        vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Perform clustering if we have enough memories
        n_memories = len(memory_contents)
        n_clusters = min(max(2, n_memories // 3), 5)  # 2-5 clusters
        
        if n_memories >= n_clusters:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            memory_clusters = kmeans.fit_predict(tfidf_matrix[1:])  # Exclude query
            
            # Calculate query similarity to each cluster center
            query_vector = tfidf_matrix[0]
            cluster_similarities = cosine_similarity(query_vector, kmeans.cluster_centers_)[0]
            
            # Boost scores based on cluster relevance
            enhanced_scores = []
            for i, (score, cluster) in enumerate(zip(current_scores, memory_clusters)):
                cluster_boost = float(cluster_similarities[cluster]) * 0.3  # Up to 30% boost
                enhanced_score = min(1.0, score + cluster_boost)
                enhanced_scores.append(enhanced_score)
            
            return enhanced_scores
        else:
            return current_scores
            
    except Exception as e:
        print(f"Clustering error: {{e}}")
        return current_scores

# Execute clustering analysis
query_text = "{query.replace('"', '\\"')}"
memory_contents = {json.dumps(memory_contents)}
current_scores = {current_scores}

enhanced_scores = clustering_analysis(query_text, memory_contents, current_scores)
print("ENHANCED_SCORES:", json.dumps(enhanced_scores))
'''
            
            result = await self._execute_python_code(clustering_code)
            
            if result and "ENHANCED_SCORES:" in result:
                scores_json = result.split("ENHANCED_SCORES:")[1].strip()
                enhanced_scores = json.loads(scores_json)
                
                # Update final scores
                for i, memory in enumerate(memories):
                    if i < len(enhanced_scores):
                        memory.score.final_score = enhanced_scores[i]
                
                # Re-sort by enhanced scores
                memories.sort(key=lambda m: m.score.final_score, reverse=True)
                
                log.info("Applied ML clustering analysis for ranking enhancement")
                self.agent_stats['ml_enhancements_used'] += 1
                return memories
            
        except Exception as e:
            log.warning(f"Clustering analysis failed: {e}")
        
        return None
    
    async def _enhance_context_with_ml(self, 
                                     context: OptimizedContext, 
                                     query: str) -> OptimizedContext:
        """
        Final ML enhancement of optimized context.
        
        Args:
            context: Optimized context to enhance
            query: Original query
            
        Returns:
            Enhanced context with ML improvements
        """
        if not self.mcp_client or not context.selected_memories:
            return context
        
        try:
            # Use ML for final context quality analysis
            quality_analysis_code = f'''
import json

def analyze_context_quality(formatted_context: str, query: str, memory_count: int):
    """Analyze and potentially improve context quality."""
    
    # Quality metrics calculation
    query_words = set(query.lower().split())
    context_words = set(formatted_context.lower().split())
    
    overlap_ratio = len(query_words & context_words) / len(query_words) if query_words else 0
    context_density = len(context_words) / len(formatted_context) if formatted_context else 0
    
    # Quality score calculation
    quality_metrics = {{
        "query_relevance": overlap_ratio,
        "information_density": context_density,
        "memory_utilization": memory_count / 10.0,  # Normalized
        "overall_quality": (overlap_ratio * 0.5 + context_density * 0.3 + min(1.0, memory_count / 5.0) * 0.2)
    }}
    
    return quality_metrics

# Analyze context
formatted_context = """{context.formatted_context.replace('"', '\\"')[:1000]}"""  # Truncate for safety
query_text = "{query.replace('"', '\\"')}"
memory_count = {len(context.selected_memories)}

quality_metrics = analyze_context_quality(formatted_context, query_text, memory_count)
print("QUALITY_METRICS:", json.dumps(quality_metrics))
'''
            
            result = await self._execute_python_code(quality_analysis_code)
            
            if result and "QUALITY_METRICS:" in result:
                metrics_json = result.split("QUALITY_METRICS:")[1].strip()
                quality_metrics = json.loads(metrics_json)
                
                # Update context with ML-derived quality metrics
                context.information_density = quality_metrics.get('information_density', context.information_density)
                
                # Add ML analysis to context metadata (for debugging/monitoring)
                if hasattr(context, 'metadata'):
                    context.metadata = quality_metrics
                
                log.info(f"Applied ML context quality analysis: {quality_metrics.get('overall_quality', 0):.2f}")
                self.agent_stats['ml_enhancements_used'] += 1
            
        except Exception as e:
            log.warning(f"ML context enhancement failed: {e}")
        
        return context
    
    async def _execute_python_code(self, code: str) -> Optional[str]:
        """
        Execute Python code via MCP server.
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result or None if failed
        """
        if not self.mcp_client:
            return None
        
        try:
            # This would be the actual MCP client call
            # Implementation depends on your MCP client setup
            result = await self.mcp_client.call_tool("run_python_code", {"code": code})
            
            if result and result.get("success"):
                self.agent_stats['mcp_computations'] += 1
                return result.get("output", "")
            
        except Exception as e:
            log.warning(f"Python MCP execution failed: {e}")
        
        return None
    
    async def _create_fallback_context(self, 
                                     query: str,
                                     thread_id: str,
                                     user_id: str,
                                     system_context: str) -> OptimizedContext:
        """Create fallback context if smart optimization fails."""
        try:
            # Use basic vector search as fallback
            basic_memories = self.memory_store.search_memories(query, k=3)
            
            fallback_memories = []
            for i, content in enumerate(basic_memories):
                memory = Memory(
                    content=content,
                    memory_id=f"fallback_{int(time.time()*1000)}_{i}",
                    thread_id=thread_id,
                    user_id=user_id
                )
                fallback_memories.append(memory)
            
            return self.token_optimizer.optimize_context(
                fallback_memories, query, system_context
            )
            
        except Exception as e:
            log.error(f"Fallback context creation failed: {e}")
            # Return empty context as last resort
            return OptimizedContext(
                formatted_context="",
                selected_memories=[],
                total_tokens=0,
                target_tokens=self.config.max_context_tokens,
                compression_ratio=1.0,
                relevance_threshold=self.config.relevance_threshold,
                average_relevance_score=0.0,
                context_coherence_score=0.0,
                information_density=0.0,
                query=query,
                query_type=QueryType.CONVERSATIONAL,
                processing_time_ms=0.0,
                memories_considered=0,
                memories_filtered=0
            )
    
    def _update_agent_stats(self, processing_time_ms: float, used_ml: bool):
        """Update agent performance statistics."""
        self.agent_stats['total_optimizations'] += 1
        
        # Update average processing time
        current_avg = self.agent_stats['average_processing_time']
        new_avg = ((current_avg * (self.agent_stats['total_optimizations'] - 1)) + processing_time_ms) / self.agent_stats['total_optimizations']
        self.agent_stats['average_processing_time'] = new_avg
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all components."""
        stats = {
            'smart_agent': self.agent_stats,
            'vector_optimizer': self.vector_optimizer.get_search_statistics(),
            'context_ranker': self.context_ranker.get_ranking_statistics(),
            'token_optimizer': self.token_optimizer.get_optimization_statistics(),
            'relevance_filter': self.relevance_filter.get_filter_statistics()
        }
        
        # Calculate overall ML enhancement rate
        total_ops = self.agent_stats['total_optimizations']
        ml_usage_rate = (self.agent_stats['ml_enhancements_used'] / max(1, total_ops)) * 100
        
        stats['overall_metrics'] = {
            'ml_enhancement_rate': ml_usage_rate,
            'average_memories_per_context': sum(s.get('memories_used', 0) for s in [stats['token_optimizer']] if 'memories_used' in s) / max(1, total_ops),
            'python_mcp_utilization': self.agent_stats['mcp_computations'] / max(1, total_ops)
        }
        
        return stats
    
    async def cleanup(self):
        """Clean up resources and caches."""
        try:
            # Clear ML cache
            self.ml_cache.clear()
            
            # Clean up component caches
            self.vector_optimizer.clear_caches()
            self.context_ranker.cleanup_old_importance_data()
            
            log.info("Smart Memory Agent cleanup completed")
            
        except Exception as e:
            log.warning(f"Cleanup failed: {e}")
    
    def set_mcp_client(self, mcp_client):
        """Set or update the MCP client for Python computations."""
        self.mcp_client = mcp_client
        log.info("Python MCP client updated")