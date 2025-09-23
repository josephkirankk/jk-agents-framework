"""
Performance Metrics API for High-Performance Memory System

Provides REST endpoints for monitoring memory system performance,
including real-time metrics, historical data, and system health.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import time
import logging
from datetime import datetime, timedelta

try:
    from .memory.manager import HighPerformanceMemoryManager, ResourceLimits
    from .memory.structures import get_memory_stats
    from .memory.langgraph_adapter import get_optimized_checkpointer
    HAS_MEMORY_SYSTEM = True
except ImportError:
    HAS_MEMORY_SYSTEM = False

log = logging.getLogger(__name__)

# Create router for memory metrics endpoints
memory_metrics_router = APIRouter(prefix="/memory", tags=["memory-metrics"])

# Global metrics storage
_metrics_history: List[Dict[str, Any]] = []
_MAX_HISTORY_SIZE = 1000


@memory_metrics_router.get("/health")
async def memory_health_check():
    """Check memory system health status."""
    if not HAS_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        checkpointer = get_optimized_checkpointer()
        if hasattr(checkpointer, 'health_check'):
            health = await checkpointer.health_check()
        else:
            health = {"healthy": True, "status": "basic_checkpointer"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "memory_system": health,
            "available_features": [
                "zero_copy_structures",
                "string_interning", 
                "memory_pooling",
                "performance_monitoring"
            ]
        }
    except Exception as e:
        log.error(f"Memory health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@memory_metrics_router.get("/stats")
async def get_memory_optimization_stats():
    """Get current memory optimization statistics."""
    if not HAS_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        # Get memory optimization stats
        memory_stats = get_memory_stats()
        
        # Get system stats if checkpointer supports it
        checkpointer = get_optimized_checkpointer()
        if hasattr(checkpointer, 'get_stats'):
            system_stats = await checkpointer.get_stats()
        else:
            system_stats = {"note": "Advanced stats not available with basic checkpointer"}
        
        current_stats = {
            "timestamp": datetime.now().isoformat(),
            "memory_optimization": memory_stats,
            "system_stats": system_stats
        }
        
        # Store in history
        global _metrics_history
        _metrics_history.append(current_stats)
        if len(_metrics_history) > _MAX_HISTORY_SIZE:
            _metrics_history = _metrics_history[-_MAX_HISTORY_SIZE:]
        
        return current_stats
        
    except Exception as e:
        log.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@memory_metrics_router.get("/performance")
async def get_performance_metrics():
    """Get comprehensive performance metrics."""
    if not HAS_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        # Import performance tools
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from tools.memory_performance_tools import get_all_performance_data
        
        # Get collected performance data
        performance_data = get_all_performance_data()
        
        # Calculate summary metrics
        checkpoint_operations = performance_data.get("checkpoint_operations", [])
        cache_metrics = performance_data.get("cache_metrics", {})
        concurrent_results = performance_data.get("concurrent_results", [])
        memory_stats = performance_data.get("memory_stats", {})
        
        summary = {
            "total_tests_run": {
                "checkpoint_tests": len(checkpoint_operations),
                "cache_tests": 1 if cache_metrics else 0,
                "concurrent_tests": len(concurrent_results),
                "memory_analyses": 1 if memory_stats else 0
            },
            "performance_highlights": {},
            "optimization_effectiveness": {}
        }
        
        # Add performance highlights if data available
        if checkpoint_operations:
            latest_checkpoint = checkpoint_operations[-1]
            summary["performance_highlights"]["checkpoint_ops_per_second"] = latest_checkpoint.get("operations_per_second", 0)
            summary["performance_highlights"]["checkpoint_success_rate"] = latest_checkpoint.get("success_rate", 0)
        
        if cache_metrics:
            summary["performance_highlights"]["cache_hit_ratio"] = cache_metrics.get("actual_hit_ratio", 0)
            summary["performance_highlights"]["cache_ops_per_second"] = cache_metrics.get("operations_per_second", 0)
        
        if concurrent_results:
            latest_concurrent = concurrent_results[-1]
            summary["performance_highlights"]["concurrent_throughput"] = latest_concurrent.get("overall_throughput_ops_per_second", 0)
            summary["performance_highlights"]["concurrent_success_rate"] = latest_concurrent.get("success_rate", 0)
        
        if memory_stats:
            optimization = memory_stats.get("optimization_effectiveness", {})
            summary["optimization_effectiveness"] = optimization
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "detailed_data": performance_data
        }
        
    except Exception as e:
        log.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")


@memory_metrics_router.get("/history")
async def get_metrics_history(limit: Optional[int] = 100):
    """Get historical memory metrics."""
    try:
        limited_history = _metrics_history[-limit:] if limit else _metrics_history
        
        return {
            "timestamp": datetime.now().isoformat(),
            "history_size": len(_metrics_history),
            "returned_items": len(limited_history),
            "metrics": limited_history
        }
    except Exception as e:
        log.error(f"Failed to get metrics history: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@memory_metrics_router.post("/benchmark")
async def run_memory_benchmark():
    """Run a comprehensive memory system benchmark."""
    if not HAS_MEMORY_SYSTEM:
        raise HTTPException(status_code=503, detail="Memory system not available")
    
    try:
        # Import performance tools
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from tools.memory_performance_tools import (
            create_checkpoint_stress_test,
            measure_cache_performance,
            simulate_concurrent_users,
            analyze_memory_usage,
            benchmark_operations
        )
        
        benchmark_start = time.time()
        
        # Run comprehensive benchmark
        results = {}
        
        log.info("Starting memory system benchmark")
        
        # 1. Checkpoint stress test
        log.info("Running checkpoint stress test")
        results["checkpoint_stress"] = create_checkpoint_stress_test(50, 5)
        
        # 2. Cache performance test
        log.info("Running cache performance test")
        results["cache_performance"] = measure_cache_performance(50, 0.8)
        
        # 3. Concurrent users test
        log.info("Running concurrent users test")
        results["concurrent_users"] = simulate_concurrent_users(10, 10)
        
        # 4. Memory analysis
        log.info("Running memory usage analysis")
        results["memory_analysis"] = analyze_memory_usage()
        
        # 5. Operations benchmark
        log.info("Running operations benchmark")
        results["operations_benchmark"] = benchmark_operations()
        
        benchmark_duration = time.time() - benchmark_start
        
        # Calculate overall score
        scores = []
        if results.get("checkpoint_stress", {}).get("success_rate"):
            scores.append(results["checkpoint_stress"]["success_rate"])
        if results.get("cache_performance", {}).get("actual_hit_ratio"):
            scores.append(results["cache_performance"]["actual_hit_ratio"] * 100)
        if results.get("concurrent_users", {}).get("success_rate"):
            scores.append(results["concurrent_users"]["success_rate"])
        if results.get("operations_benchmark", {}).get("performance_score"):
            scores.append(min(100, results["operations_benchmark"]["performance_score"] / 100))  # Normalize
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        benchmark_summary = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_duration_seconds": round(benchmark_duration, 2),
            "overall_performance_score": round(overall_score, 1),
            "test_results": results,
            "recommendations": []
        }
        
        # Add recommendations based on results
        if results.get("cache_performance", {}).get("actual_hit_ratio", 0) < 0.7:
            benchmark_summary["recommendations"].append("Consider increasing cache size for better hit ratios")
        
        if results.get("memory_analysis", {}).get("optimization_effectiveness", {}).get("overall_optimization_score", 0) < 50:
            benchmark_summary["recommendations"].append("Memory optimizations are not being fully utilized")
        
        if overall_score >= 90:
            benchmark_summary["recommendations"].append("Excellent performance - system is highly optimized")
        elif overall_score >= 70:
            benchmark_summary["recommendations"].append("Good performance - minor optimizations possible")
        else:
            benchmark_summary["recommendations"].append("Performance could be improved - review system configuration")
        
        log.info(f"Memory benchmark completed in {benchmark_duration:.2f}s with score {overall_score:.1f}")
        
        return benchmark_summary
        
    except Exception as e:
        log.error(f"Memory benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@memory_metrics_router.delete("/history")
async def clear_metrics_history():
    """Clear metrics history (for testing/cleanup)."""
    try:
        global _metrics_history
        history_size = len(_metrics_history)
        _metrics_history.clear()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "message": f"Cleared {history_size} historical metrics entries",
            "remaining_entries": len(_metrics_history)
        }
    except Exception as e:
        log.error(f"Failed to clear metrics history: {e}")
        raise HTTPException(status_code=500, detail=f"History cleanup failed: {str(e)}")


# Performance monitoring summary endpoint
@memory_metrics_router.get("/dashboard")
async def get_performance_dashboard():
    """Get a comprehensive performance dashboard view."""
    try:
        # Get current stats
        current_stats = await get_memory_optimization_stats()
        
        # Get recent history (last 10 entries)
        recent_history = _metrics_history[-10:] if _metrics_history else []
        
        # Calculate trends if we have historical data
        trends = {}
        if len(recent_history) >= 2:
            first = recent_history[0]
            last = recent_history[-1]
            
            # String interning trend
            first_intern = first.get("memory_optimization", {}).get("string_intern", {})
            last_intern = last.get("memory_optimization", {}).get("string_intern", {})
            
            if first_intern.get("hit_rate") is not None and last_intern.get("hit_rate") is not None:
                trends["string_interning_hit_rate"] = {
                    "change": last_intern["hit_rate"] - first_intern["hit_rate"],
                    "direction": "improving" if last_intern["hit_rate"] > first_intern["hit_rate"] else "declining"
                }
            
            # Memory pool trend
            first_pool = first.get("memory_optimization", {}).get("memory_pool", {})
            last_pool = last.get("memory_optimization", {}).get("memory_pool", {})
            
            if first_pool.get("reuse_rate") is not None and last_pool.get("reuse_rate") is not None:
                trends["memory_pool_reuse_rate"] = {
                    "change": last_pool["reuse_rate"] - first_pool["reuse_rate"],
                    "direction": "improving" if last_pool["reuse_rate"] > first_pool["reuse_rate"] else "declining"
                }
        
        # System health indicators
        memory_opt = current_stats.get("memory_optimization", {})
        string_intern = memory_opt.get("string_intern", {})
        memory_pool = memory_opt.get("memory_pool", {})
        
        health_indicators = {
            "string_interning_active": string_intern.get("cache_size", 0) > 0,
            "memory_pool_utilized": memory_pool.get("reuse_rate", 0) > 0,
            "system_responsive": True,  # Basic indicator
            "optimizations_effective": (
                string_intern.get("hit_rate", 0) > 0.1 or 
                memory_pool.get("reuse_rate", 0) > 0.1
            )
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "current_stats": current_stats,
            "trends": trends,
            "health_indicators": health_indicators,
            "history_size": len(_metrics_history),
            "system_status": "optimal" if all(health_indicators.values()) else "monitoring"
        }
        
    except Exception as e:
        log.error(f"Failed to get performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")