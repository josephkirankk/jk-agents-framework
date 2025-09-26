"""
Comprehensive Unit Tests for Smart Memory Agent

Tests all components of the Smart Memory Agent system including:
- Vector Search Optimizer
- Semantic Context Ranker  
- Token Optimizer
- Relevance Filter
- Main Smart Memory Agent
- Python MCP integration
"""

import pytest
import asyncio
import time
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import List, Dict, Any

# Add app to path for testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../app'))

from app.memory.smart_agent import (
    SmartMemoryAgent, VectorSearchOptimizer, SemanticContextRanker,
    TokenOptimizer, RelevanceFilter, SmartMemoryConfig,
    Memory, MemoryScore, OptimizedContext, QueryType, MemoryType
)
from app.memory.simple_chromadb_memory import SimpleChromaDBMemory


class TestMemoryTypes:
    """Test memory data structures and types."""
    
    def test_memory_creation(self):
        """Test Memory object creation and methods."""
        memory = Memory(
            content="Test content for memory",
            memory_id="test_001",
            thread_id="thread_123",
            user_id="user_456",
            memory_type=MemoryType.QA_INTERACTION
        )
        
        assert memory.content == "Test content for memory"
        assert memory.memory_id == "test_001"
        assert memory.thread_id == "thread_123"
        assert memory.user_id == "user_456"
        assert memory.memory_type == MemoryType.QA_INTERACTION
        assert memory.access_count == 0
        
        # Test access tracking
        memory.update_access()
        assert memory.access_count == 1
        
        # Test age calculation
        age = memory.calculate_age_hours()
        assert age >= 0
        
        # Test recency score
        recency = memory.calculate_recency_score()
        assert 0 <= recency <= 1
    
    def test_memory_score_calculation(self):
        """Test MemoryScore calculations."""
        score = MemoryScore(
            relevance_score=0.8,
            recency_score=0.6,
            importance_score=0.7,
            coherence_score=0.5
        )
        
        # Test default weights
        final_score = score.calculate_final_score()
        expected = 0.4 * 0.8 + 0.2 * 0.6 + 0.2 * 0.7 + 0.2 * 0.5
        assert abs(final_score - expected) < 0.001
        assert score.final_score == final_score
        
        # Test custom weights
        custom_weights = {'relevance': 0.5, 'recency': 0.2, 'importance': 0.2, 'coherence': 0.1}
        final_score_custom = score.calculate_final_score(custom_weights)
        expected_custom = 0.5 * 0.8 + 0.2 * 0.6 + 0.2 * 0.7 + 0.1 * 0.5
        assert abs(final_score_custom - expected_custom) < 0.001
    
    def test_smart_memory_config(self):
        """Test SmartMemoryConfig creation and serialization."""
        config = SmartMemoryConfig(
            max_candidate_memories=15,
            relevance_threshold=0.75,
            max_context_tokens=3000
        )
        
        assert config.max_candidate_memories == 15
        assert config.relevance_threshold == 0.75
        assert config.max_context_tokens == 3000
        
        # Test serialization
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict['max_candidate_memories'] == 15
        
        # Test deserialization
        config_restored = SmartMemoryConfig.from_dict(config_dict)
        assert config_restored.max_candidate_memories == 15
        assert config_restored.relevance_threshold == 0.75


class TestVectorSearchOptimizer:
    """Test Vector Search Optimizer functionality."""
    
    @pytest.fixture
    def mock_memory_store(self):
        """Create mock memory store."""
        mock_store = Mock(spec=SimpleChromaDBMemory)
        mock_store.vector_store = Mock()
        return mock_store
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartMemoryConfig(
            max_candidate_memories=10,
            relevance_threshold=0.7,
            cache_relevance_scores=True
        )
    
    def test_optimizer_initialization(self, mock_memory_store, config):
        """Test VectorSearchOptimizer initialization."""
        optimizer = VectorSearchOptimizer(mock_memory_store, config)
        
        assert optimizer.memory_store == mock_memory_store
        assert optimizer.config == config
        assert isinstance(optimizer.search_stats, dict)
        assert optimizer.search_stats['total_searches'] == 0
    
    def test_dynamic_k_calculation(self, mock_memory_store, config):
        """Test dynamic K calculation logic."""
        optimizer = VectorSearchOptimizer(mock_memory_store, config)
        
        # Test base case
        k = optimizer._calculate_dynamic_k("simple query")
        assert 5 <= k <= 25
        
        # Test query type effects
        k_technical = optimizer._calculate_dynamic_k("how to implement API", QueryType.TECHNICAL)
        k_factual = optimizer._calculate_dynamic_k("what is Python", QueryType.FACTUAL)
        
        # Technical queries should get more candidates than factual
        assert k_technical >= k_factual
        
        # Test long query effect
        long_query = " ".join(["word"] * 20)
        k_long = optimizer._calculate_dynamic_k(long_query)
        k_short = optimizer._calculate_dynamic_k("short")
        assert k_long >= k_short
    
    def test_token_estimation(self, mock_memory_store, config):
        """Test token estimation accuracy."""
        optimizer = VectorSearchOptimizer(mock_memory_store, config)
        
        # Test empty text
        assert optimizer._estimate_tokens("") == 0
        
        # Test simple text
        tokens = optimizer._estimate_tokens("Hello world test")
        assert tokens > 0
        assert tokens < 10  # Should be reasonable for 3 words
        
        # Test longer text
        long_text = " ".join(["word"] * 100)
        long_tokens = optimizer._estimate_tokens(long_text)
        assert long_tokens > tokens
    
    def test_statistics_tracking(self, mock_memory_store, config):
        """Test search statistics tracking."""
        optimizer = VectorSearchOptimizer(mock_memory_store, config)
        
        # Update stats
        optimizer._update_search_stats(150.0, 10, 5)
        
        assert optimizer.search_stats['total_searches'] == 1
        assert optimizer.search_stats['average_retrieval_time'] == 150.0
        
        # Update again
        optimizer._update_search_stats(250.0, 8, 4)
        
        assert optimizer.search_stats['total_searches'] == 2
        assert optimizer.search_stats['average_retrieval_time'] == 200.0  # (150 + 250) / 2


class TestSemanticContextRanker:
    """Test Semantic Context Ranker functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartMemoryConfig(
            ranking_weights={
                'relevance': 0.4,
                'recency': 0.2,
                'importance': 0.2,
                'coherence': 0.2
            }
        )
    
    @pytest.fixture
    def sample_memories(self):
        """Create sample memories for testing."""
        memories = []
        for i in range(5):
            memory = Memory(
                content=f"Test content {i} about machine learning and AI",
                memory_id=f"test_{i}",
                thread_id="test_thread",
                user_id="test_user",
                timestamp=time.time() - (i * 3600)  # Spread over hours
            )
            # Set some initial scores
            memory.score.relevance_score = 0.8 - (i * 0.1)
            memories.append(memory)
        
        return memories
    
    def test_ranker_initialization(self, config):
        """Test SemanticContextRanker initialization."""
        ranker = SemanticContextRanker(config)
        
        assert ranker.config == config
        assert isinstance(ranker.ranking_stats, dict)
        assert ranker.ranking_stats['total_rankings'] == 0
        assert isinstance(ranker.importance_tracker, dict)
    
    def test_recency_score_calculation(self, config, sample_memories):
        """Test recency score calculation."""
        ranker = SemanticContextRanker(config)
        
        for memory in sample_memories:
            recency = ranker._calculate_recency_score(memory)
            assert 0 <= recency <= 1
        
        # More recent memories should have higher scores
        recent_score = ranker._calculate_recency_score(sample_memories[0])
        old_score = ranker._calculate_recency_score(sample_memories[-1])
        assert recent_score >= old_score
    
    def test_importance_score_calculation(self, config):
        """Test importance score calculation."""
        ranker = SemanticContextRanker(config)
        
        # Create memory with usage data
        memory = Memory(
            content="Important memory content",
            memory_id="important_001",
            thread_id="test_thread",
            user_id="test_user",
            access_count=5,
            effectiveness_score=0.8
        )
        
        importance = ranker._calculate_importance_score(memory)
        assert 0 <= importance <= 1
        
        # Test with different access counts
        memory.access_count = 10
        higher_importance = ranker._calculate_importance_score(memory)
        assert higher_importance >= importance
    
    def test_content_similarity(self, config):
        """Test content similarity calculation."""
        ranker = SemanticContextRanker(config)
        
        # Test identical content
        similarity = ranker._calculate_content_similarity("test content", "test content")
        assert similarity == 1.0
        
        # Test completely different content
        similarity = ranker._calculate_content_similarity("apple banana", "car truck")
        assert similarity < 0.5
        
        # Test partial overlap
        similarity = ranker._calculate_content_similarity("apple banana fruit", "banana orange fruit")
        assert 0.3 < similarity < 0.9
    
    def test_adaptive_weights(self, config):
        """Test adaptive weight adjustment based on query type."""
        ranker = SemanticContextRanker(config)
        
        # Test factual query weights
        factual_weights = ranker._get_adaptive_weights(QueryType.FACTUAL)
        assert factual_weights['relevance'] > factual_weights['coherence']
        
        # Test conversational query weights
        conv_weights = ranker._get_adaptive_weights(QueryType.CONVERSATIONAL)
        assert conv_weights['coherence'] > factual_weights['coherence']
        
        # Test technical query weights
        tech_weights = ranker._get_adaptive_weights(QueryType.TECHNICAL)
        assert tech_weights['coherence'] > factual_weights['coherence']


class TestTokenOptimizer:
    """Test Token Optimizer functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartMemoryConfig(
            max_context_tokens=2000,
            enable_compression=True,
            summarization_threshold=500
        )
    
    @pytest.fixture
    def sample_memories(self):
        """Create sample memories with varying lengths."""
        memories = []
        
        # Short memory
        short_memory = Memory(
            content="Short memory content.",
            memory_id="short_001",
            thread_id="test",
            user_id="test"
        )
        short_memory.score.final_score = 0.9
        short_memory.tokens = 5
        memories.append(short_memory)
        
        # Long memory for compression testing
        long_content = " ".join(["This is a sentence about machine learning."] * 20)
        long_memory = Memory(
            content=long_content,
            memory_id="long_001", 
            thread_id="test",
            user_id="test"
        )
        long_memory.score.final_score = 0.8
        long_memory.tokens = 200
        memories.append(long_memory)
        
        # Medium memory
        medium_memory = Memory(
            content="Medium length memory with some technical content about algorithms.",
            memory_id="medium_001",
            thread_id="test", 
            user_id="test"
        )
        medium_memory.score.final_score = 0.7
        medium_memory.tokens = 15
        memories.append(medium_memory)
        
        return memories
    
    def test_optimizer_initialization(self, config):
        """Test TokenOptimizer initialization."""
        optimizer = TokenOptimizer(config)
        
        assert optimizer.config == config
        assert isinstance(optimizer.optimization_stats, dict)
        assert optimizer.optimization_stats['total_optimizations'] == 0
    
    def test_token_budget_calculation(self, config):
        """Test token budget calculation."""
        optimizer = TokenOptimizer(config)
        
        query = "test query"
        system_context = "system context information"
        
        budget = optimizer._calculate_token_budget(query, system_context, QueryType.TECHNICAL)
        
        assert budget.total_budget > 0
        assert budget.query_tokens > 0
        assert budget.system_tokens > 0
        assert budget.memory_budget > 0
        
        # Technical queries should get more budget
        tech_budget = optimizer._calculate_token_budget(query, system_context, QueryType.TECHNICAL)
        factual_budget = optimizer._calculate_token_budget(query, system_context, QueryType.FACTUAL)
        
        assert tech_budget.total_budget >= factual_budget.total_budget
    
    def test_memory_selection_for_budget(self, config, sample_memories):
        """Test memory selection within token budget."""
        optimizer = TokenOptimizer(config)
        
        # Create tight budget
        budget = optimizer._calculate_token_budget("test", "", QueryType.FACTUAL)
        budget.memory_budget = 50  # Very limited budget
        
        selected = optimizer._select_memories_for_budget(sample_memories, budget)
        
        # Should select memories within budget
        total_tokens = sum(m.tokens or optimizer._estimate_tokens(m.content) for m in selected)
        assert total_tokens <= budget.memory_budget
        
        # Should prefer higher scoring memories
        if len(selected) > 1:
            scores = [m.score.final_score for m in selected]
            assert scores == sorted(scores, reverse=True)
    
    def test_text_compression(self, config):
        """Test text compression functionality."""
        optimizer = TokenOptimizer(config)
        
        # Test with long text that should be compressed
        long_text = " ".join([
            "This is the first sentence about machine learning.",
            "This is the second sentence about deep learning.",
            "This is the third sentence about neural networks.",
            "This is the fourth sentence about artificial intelligence.",
            "This is the fifth sentence about data science."
        ])
        
        compressed = optimizer._compress_text(long_text)
        
        assert len(compressed) < len(long_text)
        assert len(compressed.split('.')) < len(long_text.split('.'))
        
        # Should preserve important sentences (first and last)
        assert "first sentence" in compressed or "fifth sentence" in compressed
    
    def test_context_formatting(self, config, sample_memories):
        """Test context formatting."""
        optimizer = TokenOptimizer(config)
        
        formatted = optimizer._format_context(
            sample_memories[:2], 
            "test query",
            "system context"
        )
        
        assert "System Context:" in formatted
        assert "Relevant Previous Context:" in formatted
        assert sample_memories[0].content in formatted
        assert sample_memories[1].content in formatted


class TestRelevanceFilter:
    """Test Relevance Filter functionality."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartMemoryConfig(
            relevance_threshold=0.7,
            deduplication_threshold=0.85
        )
    
    @pytest.fixture
    def sample_memories(self):
        """Create sample memories with varying relevance scores."""
        memories = []
        scores = [0.9, 0.8, 0.6, 0.5, 0.3]  # Mix of high and low relevance
        
        for i, score in enumerate(scores):
            memory = Memory(
                content=f"Memory content {i} with relevance {score}",
                memory_id=f"mem_{i}",
                thread_id="test",
                user_id="test"
            )
            memory.score.relevance_score = score
            memory.score.recency_score = 0.5
            memory.score.importance_score = 0.5
            memories.append(memory)
        
        return memories
    
    def test_filter_initialization(self, config):
        """Test RelevanceFilter initialization."""
        filter_obj = RelevanceFilter(config)
        
        assert filter_obj.config == config
        assert isinstance(filter_obj.filter_stats, dict)
        assert filter_obj.filter_stats['total_filters'] == 0
    
    def test_adaptive_threshold_calculation(self, config, sample_memories):
        """Test adaptive threshold calculation."""
        filter_obj = RelevanceFilter(config)
        
        # Test with varied scores
        threshold = filter_obj._calculate_adaptive_threshold(sample_memories, "test query")
        
        assert 0.3 <= threshold <= 0.9
        
        # Test with factual query type (should be stricter)
        factual_threshold = filter_obj._calculate_adaptive_threshold(
            sample_memories, "what is Python", QueryType.FACTUAL
        )
        
        conv_threshold = filter_obj._calculate_adaptive_threshold(
            sample_memories, "tell me about Python", QueryType.CONVERSATIONAL
        )
        
        assert factual_threshold >= conv_threshold
    
    def test_content_quality_check(self, config):
        """Test content quality checking."""
        filter_obj = RelevanceFilter(config)
        
        # Test good quality content
        good_content = "Q: What is machine learning? A: Machine learning is a subset of AI."
        assert filter_obj._check_content_quality(good_content, "machine learning") == True
        
        # Test poor quality content (too short)
        poor_content = "ML is AI"
        assert filter_obj._check_content_quality(poor_content, "machine learning") == False
        
        # Test content with no keyword overlap
        no_overlap = "This is about completely different topics like cooking and recipes."
        assert filter_obj._check_content_quality(no_overlap, "machine learning") == False
    
    def test_quality_preservation(self, config, sample_memories):
        """Test quality preservation in filtering."""
        filter_obj = RelevanceFilter(config)
        
        # Filter aggressively (high threshold)
        high_threshold_memories = [m for m in sample_memories if m.score.relevance_score >= 0.85]
        
        # Should ensure at least one memory is preserved
        preserved = filter_obj._ensure_quality_preservation(
            sample_memories, high_threshold_memories, "test query"
        )
        
        assert len(preserved) >= 1
        
        # If we had good memories but filtered too many, some should be added back
        if len(sample_memories) > 3:
            assert len(preserved) >= len(high_threshold_memories)


class MockMCPClient:
    """Mock MCP client for testing Python MCP integration."""
    
    def __init__(self):
        self.call_count = 0
        self.last_code = None
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock MCP tool call."""
        self.call_count += 1
        self.last_code = params.get('code', '')
        
        # Mock responses based on code content
        if 'Classification:' in self.last_code:
            return {
                "success": True,
                "output": "Classification: technical, Confidence: 0.85"
            }
        elif 'REFINED_SCORES:' in self.last_code:
            return {
                "success": True,
                "output": "REFINED_SCORES: [0.85, 0.75, 0.65]"
            }
        elif 'OPTIMAL_THRESHOLD:' in self.last_code:
            return {
                "success": True,
                "output": "OPTIMAL_THRESHOLD: 0.72"
            }
        elif 'ENHANCED_SCORES:' in self.last_code:
            return {
                "success": True,
                "output": "ENHANCED_SCORES: [0.88, 0.78, 0.68]"
            }
        elif 'QUALITY_METRICS:' in self.last_code:
            return {
                "success": True,
                "output": 'QUALITY_METRICS: {"query_relevance": 0.75, "information_density": 0.82}'
            }
        else:
            return {
                "success": True,
                "output": "Computation completed successfully"
            }


class TestSmartMemoryAgent:
    """Test the main Smart Memory Agent functionality."""
    
    @pytest.fixture
    def mock_memory_store(self):
        """Create mock memory store."""
        mock_store = Mock(spec=SimpleChromaDBMemory)
        mock_store.search_memories = Mock(return_value=["test memory 1", "test memory 2"])
        return mock_store
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SmartMemoryConfig(
            max_candidate_memories=10,
            relevance_threshold=0.7,
            max_context_tokens=2000,
            enable_compression=True
        )
    
    @pytest.fixture
    def mock_mcp_client(self):
        """Create mock MCP client."""
        return MockMCPClient()
    
    def test_agent_initialization(self, mock_memory_store, config, mock_mcp_client):
        """Test SmartMemoryAgent initialization."""
        agent = SmartMemoryAgent(mock_memory_store, config, mock_mcp_client)
        
        assert agent.memory_store == mock_memory_store
        assert agent.config == config
        assert agent.mcp_client == mock_mcp_client
        
        # Check component initialization
        assert agent.vector_optimizer is not None
        assert agent.context_ranker is not None
        assert agent.token_optimizer is not None
        assert agent.relevance_filter is not None
        
        assert isinstance(agent.agent_stats, dict)
        assert agent.agent_stats['total_optimizations'] == 0
    
    @pytest.mark.asyncio
    async def test_query_classification_with_ml(self, mock_memory_store, config, mock_mcp_client):
        """Test ML-based query classification."""
        agent = SmartMemoryAgent(mock_memory_store, config, mock_mcp_client)
        
        # Test technical query classification
        query_type = await agent._classify_query_with_ml("how to implement API endpoint")
        
        assert query_type == QueryType.TECHNICAL
        assert mock_mcp_client.call_count == 1
        assert "classify_query" in mock_mcp_client.last_code
    
    @pytest.mark.asyncio
    async def test_ml_similarity_refinement(self, mock_memory_store, config, mock_mcp_client):
        """Test ML-based similarity refinement."""
        agent = SmartMemoryAgent(mock_memory_store, config, mock_mcp_client)
        
        # Create sample memories
        memories = []
        for i in range(3):
            memory = Memory(
                content=f"Memory content {i}",
                memory_id=f"mem_{i}",
                thread_id="test",
                user_id="test"
            )
            memory.score.relevance_score = 0.7 + (i * 0.05)
            memories.append(memory)
        
        refined_memories = await agent._refine_similarities_with_ml(memories, "test query")
        
        assert refined_memories is not None
        assert len(refined_memories) == 3
        assert mock_mcp_client.call_count == 1
        
        # Scores should be updated
        for memory in refined_memories:
            assert memory.score.relevance_score > 0
    
    @pytest.mark.asyncio
    async def test_ml_statistical_filtering(self, mock_memory_store, config, mock_mcp_client):
        """Test ML-based statistical filtering."""
        agent = SmartMemoryAgent(mock_memory_store, config, mock_mcp_client)
        
        # Create memories with varied scores
        memories = []
        scores = [0.9, 0.8, 0.7, 0.6, 0.4]
        for i, score in enumerate(scores):
            memory = Memory(
                content=f"Memory {i}",
                memory_id=f"mem_{i}",
                thread_id="test",
                user_id="test"
            )
            memory.score.relevance_score = score
            memories.append(memory)
        
        filtered_memories = await agent._ml_enhanced_filtering(memories, "test query", QueryType.FACTUAL)
        
        # Should have filtered some memories
        assert len(filtered_memories) <= len(memories)
        assert mock_mcp_client.call_count == 1
    
    @pytest.mark.asyncio
    async def test_clustering_analysis(self, mock_memory_store, config, mock_mcp_client):
        """Test ML clustering analysis."""
        agent = SmartMemoryAgent(mock_memory_store, config, mock_mcp_client)
        
        # Create sample memories
        memories = []
        for i in range(4):
            memory = Memory(
                content=f"Memory about topic {i}",
                memory_id=f"mem_{i}",
                thread_id="test",
                user_id="test"
            )
            memory.score.final_score = 0.6 + (i * 0.1)
            memories.append(memory)
        
        enhanced_memories = await agent._apply_clustering_analysis(memories, "test query")
        
        assert enhanced_memories is not None
        assert len(enhanced_memories) == 4
        assert mock_mcp_client.call_count == 1
        
        # Final scores should be updated
        for memory in enhanced_memories:
            assert memory.score.final_score >= 0.6
    
    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self, mock_memory_store, config, mock_mcp_client):
        """Test complete memory optimization workflow."""
        agent = SmartMemoryAgent(mock_memory_store, config, mock_mcp_client)
        
        # Mock the vector optimizer to return sample memories
        sample_memories = []
        for i in range(3):
            memory = Memory(
                content=f"Sample memory content {i} about machine learning",
                memory_id=f"sample_{i}",
                thread_id="test_thread",
                user_id="test_user"
            )
            memory.score.relevance_score = 0.8 - (i * 0.1)
            sample_memories.append(memory)
        
        agent.vector_optimizer.retrieve_memories = AsyncMock(return_value=sample_memories)
        
        # Run complete optimization
        result = await agent.optimize_memory_retrieval(
            query="How does machine learning work?",
            thread_id="test_thread",
            user_id="test_user",
            system_context="You are an AI assistant",
            enable_ml_enhancements=True
        )
        
        assert isinstance(result, OptimizedContext)
        assert result.query == "How does machine learning work?"
        assert len(result.selected_memories) <= len(sample_memories)
        assert result.total_tokens > 0
        assert result.processing_time_ms > 0
        
        # Should have used ML enhancements
        assert agent.agent_stats['ml_enhancements_used'] > 0
        assert agent.agent_stats['total_optimizations'] == 1
        
        # MCP should have been called for various ML operations
        assert mock_mcp_client.call_count > 0
    
    def test_statistics_collection(self, mock_memory_store, config):
        """Test comprehensive statistics collection."""
        agent = SmartMemoryAgent(mock_memory_store, config)
        
        # Simulate some operations
        agent.agent_stats['total_optimizations'] = 10
        agent.agent_stats['ml_enhancements_used'] = 5
        agent.agent_stats['mcp_computations'] = 8
        
        stats = agent.get_comprehensive_statistics()
        
        assert 'smart_agent' in stats
        assert 'vector_optimizer' in stats
        assert 'context_ranker' in stats
        assert 'token_optimizer' in stats
        assert 'relevance_filter' in stats
        assert 'overall_metrics' in stats
        
        overall = stats['overall_metrics']
        assert 'ml_enhancement_rate' in overall
        assert 'python_mcp_utilization' in overall
        
        # ML enhancement rate should be 50% (5/10)
        assert overall['ml_enhancement_rate'] == 50.0
    
    @pytest.mark.asyncio
    async def test_fallback_behavior(self, mock_memory_store, config):
        """Test fallback behavior when ML fails."""
        agent = SmartMemoryAgent(mock_memory_store, config, None)  # No MCP client
        
        # Should still work without ML enhancements
        result = await agent.optimize_memory_retrieval(
            query="test query",
            thread_id="test_thread",
            enable_ml_enhancements=True  # Should gracefully disable
        )
        
        assert isinstance(result, OptimizedContext)
        assert result.query == "test query"
        
        # Should not have used ML enhancements
        assert agent.agent_stats['ml_enhancements_used'] == 0
    
    def test_mcp_client_management(self, mock_memory_store, config, mock_mcp_client):
        """Test MCP client management."""
        agent = SmartMemoryAgent(mock_memory_store, config, None)
        
        # Initially no client
        assert agent.mcp_client is None
        
        # Set client
        agent.set_mcp_client(mock_mcp_client)
        assert agent.mcp_client == mock_mcp_client
        
        # Update client
        new_client = MockMCPClient()
        agent.set_mcp_client(new_client)
        assert agent.mcp_client == new_client


@pytest.mark.asyncio
async def test_cleanup():
    """Test cleanup functionality."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create agent with temp directory
        mock_store = Mock()
        config = SmartMemoryConfig()
        agent = SmartMemoryAgent(mock_store, config)
        
        # Add some cache data
        agent.ml_cache['test'] = 'data'
        agent.vector_optimizer._embedding_cache['test'] = 'data'
        
        # Cleanup
        await agent.cleanup()
        
        # Caches should be cleared
        assert len(agent.ml_cache) == 0
        assert len(agent.vector_optimizer._embedding_cache) == 0
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])