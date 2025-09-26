"""
Token Optimizer

Implements intelligent token budget management for context optimization.
Ensures optimal context delivery while respecting model token limits
and maintaining information quality.
"""

import logging
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .memory_types import Memory, MemoryList, SmartMemoryConfig, OptimizedContext, QueryType

log = logging.getLogger(__name__)


@dataclass
class TokenBudget:
    """Token budget allocation for different context components."""
    total_budget: int
    system_tokens: int = 0
    query_tokens: int = 0
    memory_budget: int = 0
    safety_margin: int = 100  # Reserve tokens for safety
    
    def calculate_memory_budget(self):
        """Calculate available tokens for memories."""
        used_tokens = self.system_tokens + self.query_tokens + self.safety_margin
        self.memory_budget = max(0, self.total_budget - used_tokens)
        return self.memory_budget


class TokenOptimizer:
    """
    Advanced token budget manager for optimal context delivery.
    
    Features:
    - Dynamic token allocation based on query complexity
    - Content compression with quality preservation
    - Priority-based memory selection
    - Model-aware token counting
    """
    
    def __init__(self, config: SmartMemoryConfig):
        """
        Initialize the Token Optimizer.
        
        Args:
            config: Smart memory configuration
        """
        self.config = config
        
        # Performance tracking
        self.optimization_stats = {
            'total_optimizations': 0,
            'average_compression_ratio': 0.0,
            'average_processing_time': 0.0,
            'tokens_saved': 0,
            'quality_preserved': 0.0
        }
        
        log.info("Token Optimizer initialized")
    
    def optimize_context(self, 
                        memories: MemoryList, 
                        query: str,
                        system_context: str = "",
                        query_type: Optional[QueryType] = None) -> OptimizedContext:
        """
        Optimize context for token budget while preserving quality.
        
        Args:
            memories: Ranked memories to optimize
            query: Original search query  
            system_context: System/business context
            query_type: Classified query type
            
        Returns:
            Optimized context with token budget compliance
        """
        start_time = time.perf_counter()
        
        try:
            # Step 1: Calculate token budget
            token_budget = self._calculate_token_budget(query, system_context, query_type)
            
            # Step 2: Select memories within budget
            selected_memories = self._select_memories_for_budget(memories, token_budget)
            
            # Step 3: Compress content if needed
            if self.config.enable_compression:
                selected_memories = self._compress_memories(selected_memories, token_budget)
            
            # Step 4: Format optimized context
            formatted_context = self._format_context(selected_memories, query, system_context)
            
            # Step 5: Calculate metrics
            total_tokens = self._estimate_tokens(formatted_context)
            optimization_metrics = self._calculate_optimization_metrics(
                memories, selected_memories, total_tokens, token_budget.total_budget
            )
            
            # Create optimized context result
            optimized_context = OptimizedContext(
                formatted_context=formatted_context,
                selected_memories=selected_memories,
                total_tokens=total_tokens,
                target_tokens=token_budget.total_budget,
                compression_ratio=optimization_metrics['compression_ratio'],
                relevance_threshold=self.config.relevance_threshold,
                average_relevance_score=optimization_metrics['avg_relevance'],
                context_coherence_score=optimization_metrics['coherence_score'],
                information_density=optimization_metrics['information_density'],
                query=query,
                query_type=query_type or QueryType.CONVERSATIONAL,
                processing_time_ms=(time.perf_counter() - start_time) * 1000,
                memories_considered=len(memories),
                memories_filtered=len(memories) - len(selected_memories)
            )
            
            # Update performance statistics
            self._update_optimization_stats(optimized_context)
            
            log.info(f"Context optimized: {len(selected_memories)}/{len(memories)} memories, "
                    f"{total_tokens}/{token_budget.total_budget} tokens, "
                    f"{optimization_metrics['compression_ratio']:.2f} compression")
            
            return optimized_context
            
        except Exception as e:
            log.error(f"Context optimization failed: {e}")
            return self._create_fallback_context(memories, query, system_context)
    
    def _calculate_token_budget(self, 
                               query: str, 
                               system_context: str, 
                               query_type: Optional[QueryType] = None) -> TokenBudget:
        """
        Calculate token budget allocation for context components.
        
        Args:
            query: Search query
            system_context: System context string
            query_type: Query classification
            
        Returns:
            Token budget allocation
        """
        base_budget = self.config.max_context_tokens
        
        # Adjust budget based on query type
        type_multipliers = {
            QueryType.FACTUAL: 0.8,      # Factual queries need less context
            QueryType.CONVERSATIONAL: 1.0, # Standard budget
            QueryType.TECHNICAL: 1.2,     # Technical queries need more context
            QueryType.CREATIVE: 1.1,      # Creative needs some extra context
            QueryType.ANALYTICAL: 1.3,    # Analysis benefits from rich context
            QueryType.PROCEDURAL: 1.0     # Procedures are typically focused
        }
        
        multiplier = type_multipliers.get(query_type, 1.0) if query_type else 1.0
        adjusted_budget = int(base_budget * multiplier)
        
        # Calculate component token usage
        query_tokens = self._estimate_tokens(query)
        system_tokens = self._estimate_tokens(system_context)
        
        budget = TokenBudget(
            total_budget=adjusted_budget,
            system_tokens=system_tokens,
            query_tokens=query_tokens
        )
        
        budget.calculate_memory_budget()
        
        log.debug(f"Token budget: total={adjusted_budget}, system={system_tokens}, "
                 f"query={query_tokens}, memory_budget={budget.memory_budget}")
        
        return budget
    
    def _select_memories_for_budget(self, 
                                   memories: MemoryList, 
                                   token_budget: TokenBudget) -> MemoryList:
        """
        Select memories that fit within the token budget.
        
        Args:
            memories: Ranked memories
            token_budget: Available token budget
            
        Returns:
            Selected memories within budget
        """
        if not memories or token_budget.memory_budget <= 0:
            return []
        
        selected_memories = []
        current_tokens = 0
        
        # Sort memories by final score (should already be sorted)
        sorted_memories = sorted(memories, key=lambda m: m.score.final_score, reverse=True)
        
        for memory in sorted_memories:
            memory_tokens = memory.tokens or self._estimate_tokens(memory.content)
            
            # Check if adding this memory would exceed budget
            if current_tokens + memory_tokens <= token_budget.memory_budget:
                selected_memories.append(memory)
                current_tokens += memory_tokens
            else:
                # Try to fit a compressed version if compression is enabled
                if self.config.enable_compression and memory_tokens > 100:
                    compressed_content = self._compress_single_memory(memory.content)
                    compressed_tokens = self._estimate_tokens(compressed_content)
                    
                    if current_tokens + compressed_tokens <= token_budget.memory_budget:
                        # Create compressed memory
                        compressed_memory = Memory(
                            content=compressed_content,
                            memory_id=memory.memory_id,
                            thread_id=memory.thread_id,
                            user_id=memory.user_id,
                            memory_type=memory.memory_type,
                            timestamp=memory.timestamp,
                            metadata={**memory.metadata, 'compressed': True},
                            tokens=compressed_tokens,
                            score=memory.score
                        )
                        selected_memories.append(compressed_memory)
                        current_tokens += compressed_tokens
        
        log.debug(f"Selected {len(selected_memories)}/{len(memories)} memories, "
                 f"using {current_tokens}/{token_budget.memory_budget} tokens")
        
        return selected_memories
    
    def _compress_memories(self, memories: MemoryList, token_budget: TokenBudget) -> MemoryList:
        """
        Apply compression to memories to maximize information density.
        
        Args:
            memories: Selected memories
            token_budget: Token budget constraints
            
        Returns:
            Compressed memories
        """
        compressed_memories = []
        
        for memory in memories:
            content_length = len(memory.content)
            
            # Apply compression if content is above threshold
            if content_length > self.config.summarization_threshold:
                compressed_content = self._compress_single_memory(memory.content)
                
                # Create compressed memory with updated metadata
                compressed_memory = Memory(
                    content=compressed_content,
                    memory_id=memory.memory_id,
                    thread_id=memory.thread_id,
                    user_id=memory.user_id,
                    memory_type=memory.memory_type,
                    timestamp=memory.timestamp,
                    metadata={**memory.metadata, 'compressed': True, 'original_length': content_length},
                    tokens=self._estimate_tokens(compressed_content),
                    score=memory.score
                )
                compressed_memories.append(compressed_memory)
            else:
                compressed_memories.append(memory)
        
        return compressed_memories
    
    def _compress_single_memory(self, content: str) -> str:
        """
        Compress a single memory content while preserving key information.
        
        Args:
            content: Original memory content
            
        Returns:
            Compressed content
        """
        try:
            # Extract key components from Q&A format
            qa_match = re.match(r'Q:\s*(.*?)\s*\nA:\s*(.*)', content, re.DOTALL)
            
            if qa_match:
                question = qa_match.group(1).strip()
                answer = qa_match.group(2).strip()
                
                # Compress answer while keeping question intact
                compressed_answer = self._compress_text(answer)
                return f"Q: {question}\nA: {compressed_answer}"
            else:
                # Compress general content
                return self._compress_text(content)
                
        except Exception as e:
            log.warning(f"Memory compression failed: {e}")
            return content
    
    def _compress_text(self, text: str, max_reduction: float = 0.5) -> str:
        """
        Compress text content using various techniques.
        
        Args:
            text: Text to compress
            max_reduction: Maximum reduction ratio (0.5 = 50% reduction)
            
        Returns:
            Compressed text
        """
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) <= 2:
                return text  # Don't compress very short text
            
            # Calculate target sentence count
            target_sentences = max(2, int(len(sentences) * (1 - max_reduction)))
            
            # Score sentences by importance (length and position bias)
            sentence_scores = []
            for i, sentence in enumerate(sentences):
                # Length score (longer sentences often more important)
                length_score = min(1.0, len(sentence) / 100)
                
                # Position score (first and last sentences often important)
                if i == 0 or i == len(sentences) - 1:
                    position_score = 1.0
                else:
                    position_score = 0.5
                
                # Combined score
                total_score = 0.6 * length_score + 0.4 * position_score
                sentence_scores.append((sentence, total_score))
            
            # Select top sentences
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            selected_sentences = [s[0] for s in sentence_scores[:target_sentences]]
            
            # Maintain original order
            result_sentences = []
            for sentence in sentences:
                if sentence in selected_sentences:
                    result_sentences.append(sentence)
            
            compressed_text = '. '.join(result_sentences)
            if compressed_text and not compressed_text.endswith('.'):
                compressed_text += '.'
            
            return compressed_text
            
        except Exception as e:
            log.warning(f"Text compression failed: {e}")
            return text
    
    def _format_context(self, 
                       memories: MemoryList, 
                       query: str, 
                       system_context: str) -> str:
        """
        Format optimized context for LLM consumption.
        
        Args:
            memories: Selected memories
            query: Original query
            system_context: System context
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add system context if provided
        if system_context.strip():
            context_parts.append(f"System Context:\n{system_context.strip()}")
        
        # Add memory context if available
        if memories:
            memory_lines = ["Relevant Previous Context:"]
            
            for i, memory in enumerate(memories, 1):
                # Format memory with relevance indicator
                relevance_indicator = "🔥" if memory.score.final_score > 0.8 else "📋"
                compressed_indicator = " (compressed)" if memory.metadata.get('compressed') else ""
                
                memory_lines.append(f"{relevance_indicator} Memory {i}{compressed_indicator}:")
                memory_lines.append(f"  {memory.content}")
                
                if i < len(memories):  # Add separator except for last item
                    memory_lines.append("")
            
            context_parts.append("\n".join(memory_lines))
        
        # Join all parts
        formatted_context = "\n\n".join(context_parts)
        
        return formatted_context
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # More accurate estimation than basic word count
        # Account for punctuation, special characters, etc.
        
        # Word-based estimation
        words = len(text.split())
        
        # Character-based adjustment (GPT models use ~4 chars per token on average)
        chars = len(text)
        char_based_tokens = chars / 4
        
        # Use the higher estimate for safety
        estimated_tokens = max(int(words * 0.75), int(char_based_tokens))
        
        return estimated_tokens
    
    def _calculate_optimization_metrics(self, 
                                      original_memories: MemoryList,
                                      selected_memories: MemoryList, 
                                      total_tokens: int,
                                      target_tokens: int) -> Dict[str, float]:
        """Calculate optimization quality metrics."""
        try:
            # Calculate compression ratio
            original_content = " ".join([m.content for m in original_memories])
            selected_content = " ".join([m.content for m in selected_memories])
            
            compression_ratio = len(selected_content) / len(original_content) if original_content else 1.0
            
            # Calculate average relevance
            if selected_memories:
                avg_relevance = sum(m.score.relevance_score for m in selected_memories) / len(selected_memories)
                
                # Calculate coherence score
                coherence_scores = [m.score.coherence_score for m in selected_memories]
                coherence_score = sum(coherence_scores) / len(coherence_scores)
            else:
                avg_relevance = 0.0
                coherence_score = 0.0
            
            # Calculate information density (relevance per token)
            information_density = avg_relevance / max(1, total_tokens) * 1000  # Per 1000 tokens
            
            return {
                'compression_ratio': compression_ratio,
                'avg_relevance': avg_relevance,
                'coherence_score': coherence_score,
                'information_density': information_density
            }
            
        except Exception as e:
            log.warning(f"Metrics calculation failed: {e}")
            return {
                'compression_ratio': 1.0,
                'avg_relevance': 0.5,
                'coherence_score': 0.5,
                'information_density': 0.5
            }
    
    def _create_fallback_context(self, 
                                memories: MemoryList, 
                                query: str, 
                                system_context: str) -> OptimizedContext:
        """Create fallback context if optimization fails."""
        try:
            # Use top 3 memories as fallback
            fallback_memories = memories[:3] if memories else []
            formatted_context = self._format_context(fallback_memories, query, system_context)
            total_tokens = self._estimate_tokens(formatted_context)
            
            return OptimizedContext(
                formatted_context=formatted_context,
                selected_memories=fallback_memories,
                total_tokens=total_tokens,
                target_tokens=self.config.max_context_tokens,
                compression_ratio=1.0,
                relevance_threshold=self.config.relevance_threshold,
                average_relevance_score=0.5,
                context_coherence_score=0.5,
                information_density=0.5,
                query=query,
                query_type=QueryType.CONVERSATIONAL,
                processing_time_ms=0.0,
                memories_considered=len(memories),
                memories_filtered=max(0, len(memories) - len(fallback_memories))
            )
            
        except Exception as e:
            log.error(f"Fallback context creation failed: {e}")
            # Return minimal context
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
                memories_considered=len(memories),
                memories_filtered=len(memories)
            )
    
    def _update_optimization_stats(self, optimized_context: OptimizedContext):
        """Update optimization performance statistics."""
        self.optimization_stats['total_optimizations'] += 1
        
        # Update averages
        total = self.optimization_stats['total_optimizations']
        
        # Compression ratio
        current_compression = self.optimization_stats['average_compression_ratio']
        new_compression = ((current_compression * (total - 1)) + optimized_context.compression_ratio) / total
        self.optimization_stats['average_compression_ratio'] = new_compression
        
        # Processing time
        current_time = self.optimization_stats['average_processing_time']
        new_time = ((current_time * (total - 1)) + optimized_context.processing_time_ms) / total
        self.optimization_stats['average_processing_time'] = new_time
        
        # Tokens saved
        tokens_saved = max(0, optimized_context.target_tokens - optimized_context.total_tokens)
        self.optimization_stats['tokens_saved'] += tokens_saved
        
        # Quality preserved (average relevance)
        current_quality = self.optimization_stats['quality_preserved']
        new_quality = ((current_quality * (total - 1)) + optimized_context.average_relevance_score) / total
        self.optimization_stats['quality_preserved'] = new_quality
    
    def get_optimization_statistics(self) -> Dict[str, Any]:
        """Get current optimization performance statistics."""
        total_tokens_budget = self.optimization_stats['total_optimizations'] * self.config.max_context_tokens
        efficiency = (self.optimization_stats['tokens_saved'] / max(1, total_tokens_budget)) * 100
        
        return {
            **self.optimization_stats,
            'token_efficiency_percentage': efficiency,
            'average_tokens_saved_per_optimization': (
                self.optimization_stats['tokens_saved'] / max(1, self.optimization_stats['total_optimizations'])
            )
        }