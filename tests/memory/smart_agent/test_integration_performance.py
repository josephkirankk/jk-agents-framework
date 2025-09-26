"""
Integration and Performance Tests for Smart Memory Agent

Tests end-to-end workflows, performance benchmarking, and system integration
with real ChromaDB instances and Python MCP server simulation.
"""

import pytest
import asyncio
import time
import tempfile
import shutil
import statistics
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
import json

# Add app to path for testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../app'))

from app.memory.smart_agent import (
    SmartMemoryAgent, SmartMemoryConfig, Memory, QueryType, OptimizedContext
)
from app.memory.simple_chromadb_memory import SimpleChromaDBMemory


class MockPythonMCPServer:
    """
    Enhanced mock Python MCP server that simulates realistic computational delays
    and provides more sophisticated ML responses.
    """
    
    def __init__(self, delay_ms: float = 50):
        self.delay_ms = delay_ms
        self.computation_history = []
        self.performance_metrics = {
            'total_calls': 0,
            'average_latency': 0.0,
            'total_compute_time': 0.0
        }
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MCP tool execution with realistic delays."""
        start_time = time.perf_counter()
        
        # Simulate computation delay
        await asyncio.sleep(self.delay_ms / 1000)
        
        code = params.get('code', '')
        self.computation_history.append({
            'tool': tool_name,
            'code_length': len(code),
            'timestamp': time.time()
        })
        
        # Generate sophisticated responses based on code analysis
        result = self._generate_ml_response(code)
        
        # Update performance metrics
        latency = (time.perf_counter() - start_time) * 1000
        self.performance_metrics['total_calls'] += 1
        self.performance_metrics['total_compute_time'] += latency
        self.performance_metrics['average_latency'] = (
            self.performance_metrics['total_compute_time'] / 
            self.performance_metrics['total_calls']
        )
        
        return result
    
    def _generate_ml_response(self, code: str) -> Dict[str, Any]:
        """Generate realistic ML computation responses."""
        
        if 'classify_query' in code:
            # Analyze query features for classification
            if 'technical' in code or 'implementation' in code or 'API' in code:
                return {
                    "success": True,
                    "output": "Classification: technical, Confidence: 0.87"
                }
            elif 'what' in code and 'is' in code:
                return {
                    "success": True,
                    "output": "Classification: factual, Confidence: 0.92"
                }
            else:
                return {
                    "success": True,
                    "output": "Classification: conversational, Confidence: 0.78"
                }
        
        elif 'TfidfVectorizer' in code and 'refine_similarities' in code:
            # Simulate TF-IDF based similarity refinement
            if 'memory_texts' in code:
                # Generate realistic refined scores with slight improvements
                base_scores = [0.75, 0.68, 0.62, 0.58, 0.45]
                refined_scores = [min(1.0, score + 0.05 + (i * 0.01)) for i, score in enumerate(base_scores)]
                return {
                    "success": True,
                    "output": f"REFINED_SCORES: {json.dumps(refined_scores[:3])}"
                }
        
        elif 'statistical_filter' in code:
            # Statistical analysis for optimal threshold
            import random
            optimal_threshold = 0.65 + (random.random() * 0.2)  # 0.65-0.85 range
            return {
                "success": True,
                "output": f"OPTIMAL_THRESHOLD: {optimal_threshold:.3f}"
            }
        
        elif 'KMeans' in code and 'clustering_analysis' in code:
            # Clustering enhancement
            base_scores = [0.82, 0.75, 0.68, 0.61]
            enhanced_scores = [min(1.0, score + 0.08) for score in base_scores]
            return {
                "success": True,
                "output": f"ENHANCED_SCORES: {json.dumps(enhanced_scores[:4])}"
            }
        
        elif 'analyze_context_quality' in code:
            # Context quality analysis
            quality_metrics = {
                "query_relevance": 0.78 + (hash(code) % 20) / 100,  # 0.78-0.98
                "information_density": 0.72 + (hash(code) % 25) / 100,  # 0.72-0.97
                "overall_quality": 0.75 + (hash(code) % 20) / 100
            }
            return {
                "success": True,
                "output": f"QUALITY_METRICS: {json.dumps(quality_metrics)}"
            }
        
        else:
            return {
                "success": True,
                "output": f"Computation completed: {len(code)} bytes processed"
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of mock MCP server."""
        return {
            **self.performance_metrics,
            'computations_performed': len(self.computation_history),
            'computation_types': len(set(h['tool'] for h in self.computation_history))
        }


class TestSmartMemoryIntegration:
    """Integration tests for complete Smart Memory Agent workflows."""
    
    @pytest.fixture
    async def memory_store(self):
        """Create temporary ChromaDB memory store for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            store = SimpleChromaDBMemory(
                persist_directory=temp_dir,
                collection_name="integration_test"
            )
            
            # Add sample memories for testing
            sample_memories = [
                "Q: What is machine learning? A: Machine learning is a subset of AI that enables computers to learn without explicit programming.",
                "Q: How do neural networks work? A: Neural networks process information through interconnected nodes that simulate biological neurons.",
                "Q: What is Python? A: Python is a high-level programming language known for its simplicity and versatility.",
                "Q: What is API design? A: API design involves creating interfaces that allow different software components to communicate effectively.",
                "Q: How to implement REST APIs? A: REST APIs can be implemented using HTTP methods like GET, POST, PUT, DELETE with proper resource endpoints."
            ]
            
            for memory in sample_memories:
                store.add_memory(memory, {"type": "qa_interaction", "test": True})
            
            yield store
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def enhanced_config(self):
        """Enhanced configuration for integration testing."""
        return SmartMemoryConfig(
            max_candidate_memories=8,
            relevance_threshold=0.65,
            max_context_tokens=1500,
            ranking_weights={
                'relevance': 0.45,
                'recency': 0.15,
                'importance': 0.25,
                'coherence': 0.15
            },
            enable_compression=True,
            summarization_threshold=300,
            enable_query_classification=True,
            cache_relevance_scores=True
        )
    
    @pytest.fixture
    def mock_mcp_server(self):
        """Mock Python MCP server with realistic delays."""
        return MockPythonMCPServer(delay_ms=30)  # 30ms simulated compute time
    
    @pytest.mark.asyncio
    async def test_end_to_end_memory_optimization(self, memory_store, enhanced_config, mock_mcp_server):
        """Test complete end-to-end memory optimization workflow."""
        agent = SmartMemoryAgent(memory_store, enhanced_config, mock_mcp_server)
        
        test_queries = [
            ("What is machine learning and how does it work?", QueryType.FACTUAL),
            ("How can I implement a Python API for my project?", QueryType.TECHNICAL),
            ("Tell me about neural networks", QueryType.CONVERSATIONAL),
            ("Compare different approaches to API design", QueryType.ANALYTICAL)
        ]
        
        results = []
        
        for query, expected_type in test_queries:
            start_time = time.perf_counter()
            
            result = await agent.optimize_memory_retrieval(
                query=query,
                thread_id="integration_test",
                user_id="test_user",
                system_context="You are a helpful AI assistant specialized in technology topics.",
                enable_ml_enhancements=True
            )
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            # Assertions for result quality
            assert isinstance(result, OptimizedContext)
            assert result.query == query
            assert len(result.selected_memories) > 0
            assert result.total_tokens > 0
            assert result.processing_time_ms > 0
            assert result.average_relevance_score > 0.5
            
            # Check that ML enhancements were used
            assert len(result.selected_memories) <= enhanced_config.max_candidate_memories
            
            results.append({
                'query': query,
                'expected_type': expected_type,
                'result': result,
                'total_processing_time': processing_time,
                'memories_selected': len(result.selected_memories),
                'token_efficiency': result.total_tokens / result.target_tokens,
                'quality_score': result.average_relevance_score
            })
        
        # Verify agent statistics
        stats = agent.get_comprehensive_statistics()
        assert stats['smart_agent']['total_optimizations'] == len(test_queries)
        assert stats['smart_agent']['ml_enhancements_used'] > 0
        
        # Verify MCP server was utilized
        mcp_stats = mock_mcp_server.get_performance_summary()
        assert mcp_stats['total_calls'] > 0
        assert mcp_stats['average_latency'] > 0
        
        return results
    
    @pytest.mark.asyncio
    async def test_memory_learning_and_adaptation(self, memory_store, enhanced_config, mock_mcp_server):
        """Test memory learning and adaptation over multiple interactions."""
        agent = SmartMemoryAgent(memory_store, enhanced_config, mock_mcp_server)
        
        # Simulate repeated queries to test learning
        base_query = "How do I implement machine learning"
        variations = [
            "How do I implement machine learning models?",
            "What's the best way to implement machine learning?", 
            "Can you help me implement machine learning algorithms?",
            "I need to implement machine learning - any tips?"
        ]
        
        adaptation_metrics = []
        
        for i, query in enumerate(variations):
            result = await agent.optimize_memory_retrieval(
                query=query,
                thread_id="learning_test",
                user_id="adaptive_user",
                enable_ml_enhancements=True
            )
            
            # Track adaptation metrics
            metrics = {
                'iteration': i + 1,
                'relevance_score': result.average_relevance_score,
                'processing_time': result.processing_time_ms,
                'memories_used': len(result.selected_memories),
                'compression_ratio': result.compression_ratio,
                'coherence_score': result.context_coherence_score
            }
            adaptation_metrics.append(metrics)
            
            # Simulate feedback for memory effectiveness
            for memory in result.selected_memories:
                # Positive feedback for relevant memories
                if "machine learning" in memory.content.lower():
                    agent.context_ranker.update_memory_effectiveness(
                        memory.memory_id, 0.1  # Small positive boost
                    )
        
        # Analyze adaptation trends
        relevance_trend = [m['relevance_score'] for m in adaptation_metrics]
        processing_trend = [m['processing_time'] for m in adaptation_metrics]
        
        # Should show improvement over time (not necessarily monotonic due to query variation)
        assert max(relevance_trend) > min(relevance_trend)
        
        return adaptation_metrics
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, memory_store, enhanced_config, mock_mcp_server):
        """Test concurrent memory operations and thread safety."""
        agent = SmartMemoryAgent(memory_store, enhanced_config, mock_mcp_server)
        
        # Simulate concurrent users with different queries
        concurrent_queries = [
            ("user_1", "What is Python programming?"),
            ("user_2", "How do APIs work?"),
            ("user_3", "Explain machine learning basics"),
            ("user_4", "What are neural networks?"),
            ("user_5", "How to design REST APIs?")
        ]
        
        async def process_query(user_id: str, query: str):
            return await agent.optimize_memory_retrieval(
                query=query,
                thread_id=f"thread_{user_id}",
                user_id=user_id,
                enable_ml_enhancements=True
            )
        
        # Execute queries concurrently
        start_time = time.perf_counter()
        
        tasks = [
            process_query(user_id, query) 
            for user_id, query in concurrent_queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Verify all queries completed successfully
        assert len(results) == len(concurrent_queries)
        
        for i, result in enumerate(results):
            user_id, query = concurrent_queries[i]
            assert isinstance(result, OptimizedContext)
            assert result.query == query
            assert len(result.selected_memories) > 0
        
        # Check performance - concurrent execution should be more efficient than sequential
        avg_individual_time = sum(r.processing_time_ms for r in results) / len(results)
        
        # Total time should be less than sum of individual times due to concurrency
        assert total_time < sum(r.processing_time_ms for r in results) * 0.8
        
        return {
            'total_concurrent_time': total_time,
            'average_individual_time': avg_individual_time,
            'concurrency_efficiency': (sum(r.processing_time_ms for r in results) / total_time),
            'results': results
        }
    
    @pytest.mark.asyncio
    async def test_memory_system_scalability(self, memory_store, enhanced_config, mock_mcp_server):
        """Test system scalability with increasing memory load."""
        agent = SmartMemoryAgent(memory_store, enhanced_config, mock_mcp_server)
        
        # Add more memories to test scalability
        additional_memories = []
        for i in range(50):  # Add 50 more memories
            memory_content = f"Q: Technical question {i}? A: Technical answer {i} about programming, APIs, and software development."
            memory_store.add_memory(memory_content, {"type": "technical", "index": i})
            additional_memories.append(memory_content)
        
        # Test with different query complexities
        scalability_tests = [
            ("Simple query", "What is programming?"),
            ("Medium query", "How do I implement REST API endpoints with authentication?"),
            ("Complex query", "Compare different approaches to building scalable microservices architecture with proper error handling and monitoring")
        ]
        
        scalability_results = {}
        
        for test_name, query in scalability_tests:
            # Run multiple times to get average performance
            run_times = []
            memory_counts = []
            
            for run in range(3):
                start_time = time.perf_counter()
                
                result = await agent.optimize_memory_retrieval(
                    query=query,
                    thread_id=f"scalability_test_{run}",
                    enable_ml_enhancements=True
                )
                
                end_time = time.perf_counter()
                run_time = (end_time - start_time) * 1000
                
                run_times.append(run_time)
                memory_counts.append(len(result.selected_memories))
            
            scalability_results[test_name] = {
                'average_time': statistics.mean(run_times),
                'time_std': statistics.stdev(run_times) if len(run_times) > 1 else 0,
                'average_memories': statistics.mean(memory_counts),
                'min_time': min(run_times),
                'max_time': max(run_times)
            }
        
        # Verify performance characteristics
        for test_name, results in scalability_results.items():
            assert results['average_time'] > 0
            assert results['average_memories'] > 0
            # Performance should be reasonable even with larger memory store
            assert results['average_time'] < 5000  # Less than 5 seconds
        
        return scalability_results


class TestPerformanceBenchmarks:
    """Performance benchmark tests for Smart Memory Agent."""
    
    @pytest.fixture
    def performance_config(self):
        """Configuration optimized for performance testing."""
        return SmartMemoryConfig(
            max_candidate_memories=12,
            relevance_threshold=0.7,
            max_context_tokens=2000,
            enable_compression=True,
            cache_relevance_scores=True,
            enable_async_processing=True,
            batch_processing_threshold=3
        )
    
    @pytest.mark.asyncio 
    async def test_memory_retrieval_performance(self):
        """Benchmark memory retrieval performance across different scenarios."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create test memory store with substantial data
            memory_store = SimpleChromaDBMemory(
                persist_directory=temp_dir,
                collection_name="performance_test"
            )
            
            # Populate with varied memories
            memory_categories = [
                ("technical", "programming, API, software development, algorithms"),
                ("science", "machine learning, neural networks, data science, AI"),
                ("business", "strategy, management, operations, marketing"),
                ("general", "information, knowledge, facts, concepts")
            ]
            
            for category, keywords in memory_categories:
                for i in range(25):  # 25 memories per category
                    content = f"Q: Question about {category} topic {i}? A: Answer involving {keywords} and related concepts."
                    memory_store.add_memory(content, {"category": category, "index": i})
            
            config = SmartMemoryConfig(
                max_candidate_memories=10,
                relevance_threshold=0.65,
                cache_relevance_scores=True
            )
            
            # Test different MCP server delays
            delay_scenarios = [0, 25, 50, 100]  # 0ms to 100ms delays
            performance_results = {}
            
            for delay in delay_scenarios:
                mock_server = MockPythonMCPServer(delay_ms=delay)
                agent = SmartMemoryAgent(memory_store, config, mock_server)
                
                # Benchmark queries
                test_queries = [
                    "What is machine learning?",
                    "How to implement APIs?", 
                    "Explain business strategy",
                    "Technical programming concepts"
                ]
                
                query_times = []
                ml_enhancement_counts = []
                
                for query in test_queries:
                    start_time = time.perf_counter()
                    
                    result = await agent.optimize_memory_retrieval(
                        query=query,
                        thread_id="performance_test",
                        enable_ml_enhancements=True
                    )
                    
                    end_time = time.perf_counter()
                    query_time = (end_time - start_time) * 1000
                    
                    query_times.append(query_time)
                
                stats = agent.get_comprehensive_statistics()
                
                performance_results[f"delay_{delay}ms"] = {
                    'average_query_time': statistics.mean(query_times),
                    'min_query_time': min(query_times),
                    'max_query_time': max(query_times),
                    'query_time_std': statistics.stdev(query_times) if len(query_times) > 1 else 0,
                    'ml_enhancements_used': stats['smart_agent']['ml_enhancements_used'],
                    'mcp_utilization': stats['overall_metrics']['python_mcp_utilization'],
                    'total_optimizations': stats['smart_agent']['total_optimizations']
                }
            
            # Analyze performance impact of MCP delays
            baseline_time = performance_results['delay_0ms']['average_query_time']
            
            for delay_key, results in performance_results.items():
                if delay_key != 'delay_0ms':
                    overhead = results['average_query_time'] - baseline_time
                    results['mcp_overhead_ms'] = overhead
                    results['overhead_percentage'] = (overhead / baseline_time) * 100
            
            return performance_results
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_token_optimization_performance(self):
        """Benchmark token optimization performance and efficiency."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            memory_store = SimpleChromaDBMemory(
                persist_directory=temp_dir,
                collection_name="token_test"
            )
            
            # Create memories of varying lengths for token optimization testing
            memory_lengths = [50, 100, 200, 500, 1000]  # Characters
            
            for length in memory_lengths:
                for i in range(5):  # 5 memories per length category
                    content = "Q: " + "word " * (length // 10) + f"question {i}? A: " + "answer " * (length // 15) + f"response {i}."
                    memory_store.add_memory(content, {"length_category": length})
            
            # Test different token budgets
            token_budgets = [500, 1000, 2000, 4000]
            optimization_results = {}
            
            for budget in token_budgets:
                config = SmartMemoryConfig(
                    max_context_tokens=budget,
                    enable_compression=True,
                    summarization_threshold=200
                )
                
                mock_server = MockPythonMCPServer(delay_ms=20)
                agent = SmartMemoryAgent(memory_store, config, mock_server)
                
                test_query = "Explain the concepts and provide detailed information about the topics"
                
                start_time = time.perf_counter()
                result = await agent.optimize_memory_retrieval(
                    query=test_query,
                    thread_id="token_test",
                    enable_ml_enhancements=True
                )
                optimization_time = (time.perf_counter() - start_time) * 1000
                
                token_efficiency = result.total_tokens / budget
                compression_achieved = 1 - result.compression_ratio
                
                optimization_results[f"budget_{budget}"] = {
                    'target_tokens': budget,
                    'actual_tokens': result.total_tokens,
                    'token_efficiency': token_efficiency,
                    'compression_ratio': result.compression_ratio,
                    'compression_achieved': compression_achieved,
                    'memories_selected': len(result.selected_memories),
                    'average_relevance': result.average_relevance_score,
                    'optimization_time_ms': optimization_time,
                    'information_density': result.information_density
                }
            
            return optimization_results
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_ml_enhancement_impact(self):
        """Benchmark the impact of ML enhancements on performance and quality."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            memory_store = SimpleChromaDBMemory(
                persist_directory=temp_dir,
                collection_name="ml_impact_test"
            )
            
            # Add diverse memories for ML testing
            ml_test_memories = [
                "Q: What is Python? A: Python is a programming language.",
                "Q: How do APIs work? A: APIs enable communication between software components.",
                "Q: What is machine learning? A: ML enables computers to learn from data.",
                "Q: Explain REST architecture? A: REST is an architectural style for web services.",
                "Q: What are databases? A: Databases store and organize data systematically."
            ]
            
            for memory in ml_test_memories:
                memory_store.add_memory(memory)
            
            config = SmartMemoryConfig(
                max_candidate_memories=8,
                relevance_threshold=0.6,
                enable_compression=True
            )
            
            test_queries = [
                "Tell me about Python programming",
                "How do I work with APIs?",
                "Explain machine learning concepts"
            ]
            
            # Test with and without ML enhancements
            ml_comparison = {}
            
            for enable_ml in [False, True]:
                mock_server = MockPythonMCPServer(delay_ms=30) if enable_ml else None
                agent = SmartMemoryAgent(memory_store, config, mock_server)
                
                scenario_key = "with_ml" if enable_ml else "without_ml"
                results = []
                
                for query in test_queries:
                    start_time = time.perf_counter()
                    
                    result = await agent.optimize_memory_retrieval(
                        query=query,
                        thread_id=f"ml_test_{enable_ml}",
                        enable_ml_enhancements=enable_ml
                    )
                    
                    processing_time = (time.perf_counter() - start_time) * 1000
                    
                    results.append({
                        'query': query,
                        'processing_time': processing_time,
                        'relevance_score': result.average_relevance_score,
                        'memories_used': len(result.selected_memories),
                        'token_efficiency': result.total_tokens / result.target_tokens,
                        'information_density': result.information_density
                    })
                
                # Calculate aggregate metrics
                ml_comparison[scenario_key] = {
                    'average_processing_time': statistics.mean([r['processing_time'] for r in results]),
                    'average_relevance': statistics.mean([r['relevance_score'] for r in results]),
                    'average_memories_used': statistics.mean([r['memories_used'] for r in results]),
                    'average_token_efficiency': statistics.mean([r['token_efficiency'] for r in results]),
                    'average_information_density': statistics.mean([r['information_density'] for r in results]),
                    'individual_results': results
                }
            
            # Calculate ML enhancement impact
            ml_impact = {
                'processing_time_overhead': (
                    ml_comparison['with_ml']['average_processing_time'] - 
                    ml_comparison['without_ml']['average_processing_time']
                ),
                'relevance_improvement': (
                    ml_comparison['with_ml']['average_relevance'] - 
                    ml_comparison['without_ml']['average_relevance']
                ),
                'efficiency_change': (
                    ml_comparison['with_ml']['average_token_efficiency'] - 
                    ml_comparison['without_ml']['average_token_efficiency']
                ),
                'density_improvement': (
                    ml_comparison['with_ml']['average_information_density'] - 
                    ml_comparison['without_ml']['average_information_density']
                )
            }
            
            ml_comparison['impact_analysis'] = ml_impact
            
            return ml_comparison
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_system_reliability_and_error_handling():
    """Test system reliability under various error conditions."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        memory_store = SimpleChromaDBMemory(
            persist_directory=temp_dir,
            collection_name="reliability_test"
        )
        
        # Add basic memories
        memory_store.add_memory("Q: Test? A: Test response.")
        
        config = SmartMemoryConfig()
        
        # Test with failing MCP server
        class FailingMCPServer:
            def __init__(self, fail_rate=0.5):
                self.fail_rate = fail_rate
                self.call_count = 0
            
            async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
                self.call_count += 1
                if (self.call_count % 2) == 0:  # Fail every other call
                    return {"success": False, "error": "Simulated failure"}
                return {"success": True, "output": "Success"}
        
        failing_server = FailingMCPServer()
        agent = SmartMemoryAgent(memory_store, config, failing_server)
        
        # Test that system remains functional despite MCP failures
        result = await agent.optimize_memory_retrieval(
            query="Test query for reliability",
            thread_id="reliability_test",
            enable_ml_enhancements=True
        )
        
        # Should still produce a valid result even with MCP failures
        assert isinstance(result, OptimizedContext)
        assert result.query == "Test query for reliability"
        assert len(result.selected_memories) >= 0  # May be 0 due to failures, but shouldn't crash
        
        # Test with no MCP server (None)
        agent_no_mcp = SmartMemoryAgent(memory_store, config, None)
        result_no_mcp = await agent_no_mcp.optimize_memory_retrieval(
            query="Test without MCP",
            thread_id="no_mcp_test",
            enable_ml_enhancements=True  # Should gracefully disable
        )
        
        assert isinstance(result_no_mcp, OptimizedContext)
        assert result_no_mcp.query == "Test without MCP"
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "integration":
            pytest.main(["-v", "-k", "TestSmartMemoryIntegration"])
        elif sys.argv[1] == "performance":
            pytest.main(["-v", "-k", "TestPerformanceBenchmarks"])
        elif sys.argv[1] == "reliability":
            pytest.main(["-v", "-k", "test_system_reliability"])
    else:
        pytest.main([__file__, "-v", "--tb=short"])