"""
Advanced Memory Agent using High-Performance Memory System

This agent demonstrates the advanced memory capabilities including:
- HighPerformanceMemoryManager with adaptive scaling
- ChromaDBBackend with connection pooling and caching
- Performance monitoring and circuit breaker patterns
- Memory optimization with string interning and buffer pooling
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.memory.manager import HighPerformanceMemoryManager, ResourceLimits
from app.memory.chromadb_backend import ChromaDBBackend, ChromaDBConfig
from app.memory.structures import OptimizedCheckpoint, intern_string, get_memory_stats
from app.agent_builder import build_react_agent
from app.config import AgentConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class AdvancedMemoryAgent:
    """
    Advanced agent using high-performance memory system with:
    - Adaptive resource management
    - Performance monitoring
    - Circuit breaker patterns
    - Memory optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the advanced memory agent."""
        self.config = config or self._get_default_config()
        self.memory_manager: Optional[HighPerformanceMemoryManager] = None
        self.agent = None
        self.mcp_client = None
        self.initialized = False
        
        # Performance tracking
        self.conversation_count = 0
        self.start_time = time.time()
        
        log.info("Advanced Memory Agent created")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the advanced memory system."""
        return {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": "./advanced_agent_memory",
                    "max_connections": 20,
                    "min_connections": 3,
                    "l1_cache_size": 5000,
                    "batch_size": 50,
                    "enable_batch_processing": True,
                    "enable_metrics": True
                }
            },
            "resource_limits": {
                "max_memory_mb": 512,
                "max_connections": 20,
                "max_concurrent_operations": 100,
                "scale_up_cpu_threshold": 70.0,
                "scale_down_cpu_threshold": 30.0
            },
            "agent": {
                "name": "AdvancedMemoryAgent",
                "model": "openai:gpt-4o-mini",
                "description": "An advanced agent with high-performance memory capabilities",
                "prompt": """You are an advanced AI assistant with sophisticated memory capabilities.

You have access to a high-performance memory system that includes:
- Adaptive resource management that scales based on load
- Advanced caching with sub-millisecond retrieval times
- Circuit breaker patterns for graceful degradation
- Memory optimization with string interning and buffer pooling

Your memory system automatically:
- Monitors performance and scales resources up/down as needed
- Caches frequently accessed data for faster retrieval
- Handles failures gracefully with circuit breaker patterns
- Optimizes memory usage through advanced data structures

When responding:
1. Be helpful and informative
2. Remember context from previous conversations
3. Mention when you're using advanced memory features
4. Provide insights about performance when relevant

Available MCP servers: {{mcpservers}}
Business context: {{businessContext}}
"""
            }
        }
    
    async def initialize(self) -> None:
        """Initialize the advanced memory system and agent."""
        if self.initialized:
            return
        
        log.info("Initializing Advanced Memory Agent...")
        
        try:
            # Create resource limits
            resource_config = self.config.get("resource_limits", {})
            resource_limits = ResourceLimits(
                max_memory_mb=resource_config.get("max_memory_mb", 512),
                max_connections=resource_config.get("max_connections", 20),
                max_concurrent_operations=resource_config.get("max_concurrent_operations", 100),
                scale_up_cpu_threshold=resource_config.get("scale_up_cpu_threshold", 70.0),
                scale_down_cpu_threshold=resource_config.get("scale_down_cpu_threshold", 30.0)
            )
            
            # Initialize high-performance memory manager
            self.memory_manager = HighPerformanceMemoryManager(resource_limits)
            await self.memory_manager.initialize(self.config)
            
            # Create agent configuration
            agent_config_dict = self.config.get("agent", {})
            agent_config = AgentConfig(
                name=agent_config_dict.get("name", "AdvancedMemoryAgent"),
                model=agent_config_dict.get("model", "openai:gpt-4o-mini"),
                description=agent_config_dict.get("description", "Advanced memory agent"),
                prompt=agent_config_dict.get("prompt", "You are a helpful assistant."),
                mcp_servers={},
                http_tools={},
                python_tools={}
            )
            
            # Build the agent with advanced memory checkpointer
            # Note: We'll use the memory manager's checkpoint store as the checkpointer
            self.agent, self.mcp_client = await build_react_agent(
                agent_cfg=agent_config,
                default_model="openai:gpt-4o-mini",
                checkpointer=None,  # We'll handle checkpointing through memory manager
                app_config=self.config
            )
            
            self.initialized = True
            log.info("Advanced Memory Agent initialized successfully")
            
        except Exception as e:
            log.error(f"Failed to initialize Advanced Memory Agent: {e}")
            raise
    
    async def chat(self, message: str, user_id: str = "default_user", thread_id: str = "default_thread") -> Dict[str, Any]:
        """
        Chat with the agent using advanced memory capabilities.
        
        Args:
            message: User message
            user_id: User identifier for memory isolation
            thread_id: Thread identifier for conversation context
            
        Returns:
            Response with performance metrics and memory information
        """
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        self.conversation_count += 1
        
        # Intern strings for memory optimization
        user_id = intern_string(user_id)
        thread_id = intern_string(thread_id)
        
        try:
            # Get performance metrics before processing
            pre_stats = await self.memory_manager.get_comprehensive_stats()
            
            # Create conversation state
            conversation_state = {
                "messages": [{"role": "user", "content": message}],
                "user_id": user_id,
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "conversation_count": self.conversation_count
            }
            
            # Store checkpoint before processing
            checkpoint_data = str(conversation_state).encode('utf-8')
            await self.memory_manager.store_checkpoint(user_id, thread_id, checkpoint_data)
            
            # Retrieve previous context if available
            previous_checkpoint = await self.memory_manager.retrieve_checkpoint(user_id, thread_id)
            context = ""
            if previous_checkpoint:
                try:
                    # Simple context extraction (in production, this would be more sophisticated)
                    context = f"Previous conversation data available ({len(previous_checkpoint)} bytes)"
                except Exception as e:
                    log.warning(f"Failed to extract context: {e}")
            
            # Get current performance metrics for the prompt
            current_stats = await self.memory_manager.get_comprehensive_stats()
            performance_summary = self._format_performance_metrics(current_stats)
            
            # Prepare the enhanced prompt with context and performance info
            enhanced_message = f"""
User Message: {message}

Context: {context}
Performance Metrics: {performance_summary}
Conversation Count: {self.conversation_count}
Memory Optimizations Active: String interning, buffer pooling, LRU caching
"""
            
            # Process with the agent (simplified for this example)
            # In a real implementation, this would use the full LangGraph agent
            response = await self._generate_response(enhanced_message, current_stats)
            
            # Store the complete interaction
            interaction_data = {
                "user_message": message,
                "agent_response": response,
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": current_stats
            }
            
            interaction_checkpoint = str(interaction_data).encode('utf-8')
            await self.memory_manager.store_checkpoint(user_id, f"{thread_id}_interaction_{self.conversation_count}", interaction_checkpoint)
            
            # Get final performance metrics
            post_stats = await self.memory_manager.get_comprehensive_stats()
            
            processing_time = time.time() - start_time
            
            return {
                "response": response,
                "user_id": user_id,
                "thread_id": thread_id,
                "conversation_count": self.conversation_count,
                "processing_time_ms": round(processing_time * 1000, 2),
                "memory_stats": {
                    "pre_processing": pre_stats,
                    "post_processing": post_stats,
                    "memory_optimization": get_memory_stats()
                },
                "performance_summary": performance_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Error in chat processing: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "error": str(e),
                "user_id": user_id,
                "thread_id": thread_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_response(self, enhanced_message: str, performance_stats: Dict[str, Any]) -> str:
        """
        Generate response using performance-aware logic.
        
        In a real implementation, this would call the LangGraph agent.
        """
        
        # Extract key performance indicators
        backend_stats = performance_stats.get("backend", {})
        cache_stats = backend_stats.get("cache", {})
        performance = performance_stats.get("performance", {})
        
        cache_hit_rate = cache_stats.get("hit_rate", 0) * 100
        current_perf = performance.get("current", {})
        cpu_usage = current_perf.get("cpu_usage", 0)
        memory_usage = current_perf.get("memory_usage", 0)
        ops_per_second = current_perf.get("operations_per_second", 0)
        
        # Generate performance-aware response
        response_parts = []
        
        # Basic response
        if "hello" in enhanced_message.lower() or "hi" in enhanced_message.lower():
            response_parts.append("Hello! I'm your advanced memory agent with high-performance capabilities.")
        elif "performance" in enhanced_message.lower() or "stats" in enhanced_message.lower():
            response_parts.append("Here are my current performance metrics:")
        elif "memory" in enhanced_message.lower():
            response_parts.append("I'm using an advanced memory system with several optimization layers.")
        else:
            response_parts.append("I understand your message and I'm processing it with my advanced memory system.")
        
        # Add performance insights
        if cache_hit_rate > 80:
            response_parts.append(f"🚀 My cache is performing excellently with a {cache_hit_rate:.1f}% hit rate!")
        elif cache_hit_rate > 50:
            response_parts.append(f"📊 My cache hit rate is {cache_hit_rate:.1f}%, which is good for performance.")
        else:
            response_parts.append(f"🔄 My cache is warming up (hit rate: {cache_hit_rate:.1f}%).")
        
        # Add system performance info
        if cpu_usage > 80:
            response_parts.append("⚡ I'm running at high CPU usage - my system may scale up resources automatically.")
        elif cpu_usage < 30:
            response_parts.append("💚 I'm running efficiently with low resource usage.")
        
        if ops_per_second > 100:
            response_parts.append(f"🏃‍♂️ I'm processing {ops_per_second:.1f} operations per second.")
        
        # Add memory optimization info
        memory_optimization = get_memory_stats()
        string_stats = memory_optimization.get("string_intern", {})
        if string_stats.get("hit_rate", 0) > 0.5:
            response_parts.append("🧠 String interning is saving memory by reusing common strings.")
        
        pool_stats = memory_optimization.get("memory_pool", {})
        if pool_stats.get("reuse_rate", 0) > 0.3:
            response_parts.append("♻️ Memory buffer pooling is reducing garbage collection overhead.")
        
        return " ".join(response_parts)
    
    def _format_performance_metrics(self, stats: Dict[str, Any]) -> str:
        """Format performance metrics for display."""
        try:
            performance = stats.get("performance", {})
            current = performance.get("current", {})
            
            return f"CPU: {current.get('cpu_usage', 0):.1f}%, Memory: {current.get('memory_usage', 0):.1f}%, Ops/sec: {current.get('operations_per_second', 0):.1f}"
        except Exception:
            return "Performance metrics unavailable"
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the agent and memory system."""
        if not self.initialized:
            return {"error": "Agent not initialized"}
        
        try:
            # Get memory manager stats
            memory_stats = await self.memory_manager.get_comprehensive_stats()
            
            # Get health check
            health = await self.memory_manager.health_check()
            
            # Get memory optimization stats
            optimization_stats = get_memory_stats()
            
            # Calculate uptime
            uptime_seconds = time.time() - self.start_time
            
            return {
                "agent_info": {
                    "name": "AdvancedMemoryAgent",
                    "conversation_count": self.conversation_count,
                    "uptime_seconds": round(uptime_seconds, 2),
                    "initialized": self.initialized
                },
                "memory_system": memory_stats,
                "health": health,
                "memory_optimization": optimization_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Error getting comprehensive stats: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.memory_manager:
            await self.memory_manager.cleanup()
        
        if self.mcp_client:
            # Close MCP client if needed
            pass
        
        self.initialized = False
        log.info("Advanced Memory Agent cleaned up")


async def run_advanced_memory_demo():
    """Run a demonstration of the advanced memory agent."""
    
    print("🚀 Advanced Memory Agent Demo")
    print("=" * 60)
    print("This agent uses high-performance memory with:")
    print("- Adaptive resource management")
    print("- Connection pooling and caching")
    print("- Performance monitoring")
    print("- Memory optimization")
    print()
    
    # Create and initialize agent
    agent = AdvancedMemoryAgent()
    
    try:
        await agent.initialize()
        print("✅ Agent initialized successfully!")
        print()
        
        # Demo conversations
        demo_messages = [
            "Hello, I'm testing your advanced memory system",
            "Can you tell me about your performance capabilities?",
            "How is your memory optimization working?",
            "What are your current performance metrics?",
            "Remember that I like advanced AI systems",
            "Do you recall what I mentioned about my preferences?"
        ]
        
        user_id = "demo_user"
        thread_id = "demo_thread"
        
        for i, message in enumerate(demo_messages, 1):
            print(f"Demo {i}/6:")
            print(f"User: {message}")
            
            # Chat with agent
            result = await agent.chat(message, user_id, thread_id)
            
            print(f"Agent: {result['response']}")
            print(f"Processing time: {result['processing_time_ms']}ms")
            print(f"Performance: {result['performance_summary']}")
            print()
            
            # Small delay between messages
            await asyncio.sleep(0.5)
        
        # Show comprehensive stats
        print("📊 Final Comprehensive Statistics:")
        print("-" * 40)
        stats = await agent.get_comprehensive_stats()
        
        # Format and display key stats
        agent_info = stats.get("agent_info", {})
        print(f"Conversations: {agent_info.get('conversation_count', 0)}")
        print(f"Uptime: {agent_info.get('uptime_seconds', 0):.2f} seconds")
        
        health = stats.get("health", {})
        print(f"System Health: {'✅ Healthy' if health.get('healthy') else '❌ Unhealthy'}")
        
        memory_opt = stats.get("memory_optimization", {})
        string_intern = memory_opt.get("string_intern", {})
        memory_pool = memory_opt.get("memory_pool", {})
        
        print(f"String Interning Hit Rate: {string_intern.get('hit_rate', 0) * 100:.1f}%")
        print(f"Memory Pool Reuse Rate: {memory_pool.get('reuse_rate', 0) * 100:.1f}%")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        log.error(f"Demo error: {e}")
    
    finally:
        # Cleanup
        await agent.cleanup()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_advanced_memory_demo())
