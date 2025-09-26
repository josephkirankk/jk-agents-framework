#!/usr/bin/env python3
"""
Smart Memory Agent Integration Example

This example demonstrates how to integrate and use the Smart Memory Agent
with the JK-Agents Framework for enhanced memory capabilities.
"""

import asyncio
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def basic_smart_memory_example():
    """Basic example of Smart Memory Agent integration."""
    print("🧠 Smart Memory Agent - Basic Example")
    print("=" * 50)
    
    try:
        # Initialize Smart Memory Agent
        from app.smart_memory_utils import init_smart_memory_basic, get_smart_memory_status
        
        print("1. Initializing Smart Memory Agent...")
        integration = await init_smart_memory_basic()
        
        if integration:
            print("✓ Smart Memory Agent initialized successfully!")
            
            # Get status
            status = await get_smart_memory_status()
            print(f"   Status: {status.get('status', 'unknown')}")
            print(f"   Smart Agent Enabled: {status.get('smart_agent_enabled', False)}")
        else:
            print("⚠ Smart Memory Agent not available - using fallback")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def configuration_example():
    """Example showing different configuration options."""
    print("🔧 Smart Memory Agent - Configuration Example")
    print("=" * 50)
    
    try:
        from app.smart_memory_utils import (
            configure_smart_memory_for_development,
            configure_smart_memory_for_production,
            get_smart_memory_status
        )
        
        print("1. Development Configuration:")
        dev_integration = await configure_smart_memory_for_development()
        if dev_integration:
            dev_status = await get_smart_memory_status()
            print(f"   ✓ Development config loaded")
            print(f"   Max response time: {dev_status.get('integration_config', {}).get('max_response_time_ms')}ms")
        
        print("\n2. Production Configuration:")
        prod_integration = await configure_smart_memory_for_production()
        if prod_integration:
            prod_status = await get_smart_memory_status()
            print(f"   ✓ Production config loaded")
            print(f"   Rollout percentage: {prod_status.get('integration_config', {}).get('gradual_rollout_percentage', 0) * 100}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def memory_operations_example():
    """Example showing memory storage and retrieval operations."""
    print("💾 Smart Memory Agent - Memory Operations Example")
    print("=" * 50)
    
    try:
        from app.smart_memory_utils import init_smart_memory_basic
        from app.planner_executor import get_smart_memory_integration
        
        # Initialize
        await init_smart_memory_basic()
        integration = await get_smart_memory_integration()
        
        if not integration:
            print("⚠ Smart Memory Agent not available")
            return
        
        print("1. Storing sample memories...")
        
        # Store some sample memories
        sample_memories = [
            {
                "content": "User asked about machine learning algorithms for recommendation systems",
                "metadata": {"topic": "ML", "complexity": "advanced"},
                "memory_type": "query"
            },
            {
                "content": "Successfully implemented collaborative filtering using Python scikit-learn",
                "metadata": {"topic": "ML", "result": "success", "technology": "Python"},
                "memory_type": "execution_result"
            },
            {
                "content": "Error: Memory usage exceeded limit when processing large dataset",
                "metadata": {"topic": "Performance", "result": "error", "issue": "memory"},
                "memory_type": "execution_result"
            }
        ]
        
        stored_ids = []
        for memory in sample_memories:
            memory_id = await integration.store_memory(**memory)
            stored_ids.append(memory_id)
            print(f"   ✓ Stored memory: {memory_id}")
        
        print(f"\n2. Retrieving memories for query...")
        
        # Retrieve memories with Smart Agent optimization
        query = "machine learning recommendations performance issues"
        context = await integration.get_context_for_query(
            query=query,
            max_tokens=1000,
            include_metadata=True
        )
        
        print(f"   Query: {query}")
        print(f"   Found {len(context.get('optimized_memories', []))} relevant memories")
        print(f"   Total tokens: {context.get('total_tokens', 0)}")
        print(f"   Optimization applied: {context.get('optimization_applied', False)}")
        print(f"   Smart Memory available: {context.get('smart_memory_available', False)}")
        
        # Display retrieved memories
        for i, memory in enumerate(context.get('optimized_memories', [])[:2], 1):
            print(f"\n   Memory {i}:")
            print(f"     Content: {memory.get('content', '')[:100]}...")
            print(f"     Relevance: {memory.get('relevance_score', 0):.3f}")
            print(f"     Type: {memory.get('memory_type', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def performance_monitoring_example():
    """Example showing performance monitoring capabilities."""
    print("📊 Smart Memory Agent - Performance Monitoring Example")
    print("=" * 50)
    
    try:
        from app.smart_memory_utils import get_smart_memory_status
        
        # Get comprehensive status
        status = await get_smart_memory_status()
        
        print("Current Status:")
        print(f"   Smart Agent Enabled: {status.get('smart_agent_enabled', False)}")
        print(f"   Integration Status: {status.get('status', 'unknown')}")
        
        metrics = status.get('metrics', {})
        if metrics:
            print(f"\nPerformance Metrics:")
            print(f"   Smart Agent Calls: {metrics.get('smart_agent_calls', 0)}")
            print(f"   Fallback Calls: {metrics.get('fallback_calls', 0)}")
            print(f"   Success Rate: {metrics.get('success_rate', 0):.1%}")
            print(f"   Avg Response Time: {metrics.get('average_response_time_ms', 0):.1f}ms")
            print(f"   Token Savings: {metrics.get('token_savings_percentage', 0):.1f}%")
            print(f"   Context Improvement: {metrics.get('context_improvement_score', 0):.1f}%")
        
        performance = status.get('performance_comparison', {})
        if performance:
            print(f"\nPerformance Comparison:")
            print(f"   Smart Agent Usage: {performance.get('smart_agent_usage_percentage', 0):.1f}%")
            print(f"   Response Time Improvement: {performance.get('average_response_time_improvement', '0%')}")
            print(f"   Token Efficiency Improvement: {performance.get('token_efficiency_improvement', '0%')}")
            print(f"   Context Quality Improvement: {performance.get('context_quality_improvement', '0%')}")
        
        fallback_reasons = status.get('recent_fallback_reasons', [])
        if fallback_reasons:
            print(f"\nRecent Fallback Reasons:")
            for reason in fallback_reasons[-3:]:  # Show last 3
                print(f"   - {reason}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def integration_with_existing_memory_example():
    """Example showing how to integrate with existing memory systems."""
    print("🔗 Smart Memory Agent - Integration with Existing Memory Example")
    print("=" * 50)
    
    try:
        # Simulate an existing memory system
        class MockMemorySystem:
            def __init__(self):
                self.memories = []
            
            async def store(self, content, metadata=None, **kwargs):
                memory_id = f"mock_{len(self.memories)}"
                self.memories.append({
                    'id': memory_id,
                    'content': content,
                    'metadata': metadata or {}
                })
                return memory_id
            
            async def search(self, query, limit=10, **kwargs):
                # Simple keyword search for demo
                results = []
                query_words = query.lower().split()
                for memory in self.memories:
                    content = memory['content'].lower()
                    if any(word in content for word in query_words):
                        results.append(memory)
                return results[:limit]
        
        print("1. Creating mock existing memory system...")
        existing_memory = MockMemorySystem()
        
        # Add some data to existing system
        await existing_memory.store("Python programming tutorial", {"topic": "programming"})
        await existing_memory.store("Database optimization techniques", {"topic": "database"})
        
        print("   ✓ Mock memory system created with sample data")
        
        print("2. Integrating with Smart Memory Agent...")
        from app.smart_memory_utils import init_smart_memory_with_existing_memory
        
        # Integrate with Smart Memory Agent
        integration = await init_smart_memory_with_existing_memory(existing_memory)
        
        if integration:
            print("   ✓ Smart Memory Agent integrated with existing system")
            
            # Test enhanced retrieval
            context = await integration.get_context_for_query(
                query="programming database optimization",
                max_tokens=500
            )
            
            print(f"3. Enhanced retrieval results:")
            print(f"   Found {len(context.get('optimized_memories', []))} memories")
            print(f"   Smart Memory enhancement: {context.get('smart_memory_available', False)}")
            print(f"   Optimization applied: {context.get('optimization_applied', False)}")
            
        else:
            print("   ⚠ Integration failed - using original system")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    examples = [
        basic_smart_memory_example,
        configuration_example,
        memory_operations_example,
        performance_monitoring_example,
        integration_with_existing_memory_example
    ]
    
    print("🚀 Smart Memory Agent Integration Examples")
    print("=" * 60)
    print()
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
            print()
            if i < len(examples):
                input("Press Enter to continue to next example...")
                print()
        except KeyboardInterrupt:
            print("\n👋 Examples interrupted by user")
            break
        except Exception as e:
            print(f"❌ Example failed: {e}")
            print()
    
    print("✅ Smart Memory Agent examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())