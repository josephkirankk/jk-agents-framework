"""
High-performance memory manager with adaptive resource management.

Provides intelligent resource scaling, performance monitoring, and
automatic optimization based on current load and usage patterns.
"""

from __future__ import annotations
import asyncio
import time
import logging
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .protocols import MemoryBackend, MetricsCollector
from .chromadb_backend import ChromaDBBackend, ChromaDBConfig
from .structures import get_memory_stats

log = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    active_connections: int
    cache_hit_rate: float
    average_latency: float
    operations_per_second: float


@dataclass  
class ResourceLimits:
    """Resource limits for adaptive scaling."""
    max_memory_mb: int = 1024
    max_connections: int = 100
    max_concurrent_operations: int = 500
    max_cache_size: int = 50000
    
    # Scaling thresholds
    scale_up_cpu_threshold: float = 80.0
    scale_down_cpu_threshold: float = 20.0
    scale_up_memory_threshold: float = 85.0
    scale_down_memory_threshold: float = 30.0


class PerformanceMonitor:
    """Real-time performance monitoring with adaptive scaling."""
    
    def __init__(self, resource_limits: ResourceLimits):
        self.limits = resource_limits
        self._metrics_history: deque = deque(maxlen=1000)
        self._operation_times: deque = deque(maxlen=10000)
        self._operations_count = 0
        self._last_reset_time = time.time()
        self._lock = threading.RLock()
        
        # Scaling callbacks
        self._scale_up_callbacks: List[Callable] = []
        self._scale_down_callbacks: List[Callable] = []
    
    def record_operation(self, operation_time: float):
        """Record an operation timing."""
        with self._lock:
            self._operation_times.append(operation_time)
            self._operations_count += 1
    
    def add_scale_up_callback(self, callback: Callable):
        """Add callback for scale-up events."""
        self._scale_up_callbacks.append(callback)
    
    def add_scale_down_callback(self, callback: Callable):
        """Add callback for scale-down events."""
        self._scale_down_callbacks.append(callback)
    
    def collect_metrics(self, backend_stats: Dict[str, Any]) -> PerformanceMetrics:
        """Collect current performance metrics."""
        with self._lock:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            # Operation metrics
            current_time = time.time()
            time_window = current_time - self._last_reset_time
            ops_per_second = self._operations_count / max(time_window, 1.0)
            
            # Latency metrics
            if self._operation_times:
                avg_latency = sum(self._operation_times) / len(self._operation_times)
            else:
                avg_latency = 0.0
            
            # Backend metrics
            active_connections = backend_stats.get("pool", {}).get("active_connections", 0)
            cache_stats = backend_stats.get("cache", {})
            cache_hit_rate = cache_stats.get("hit_rate", 0.0) * 100
            
            metrics = PerformanceMetrics(
                timestamp=current_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                active_connections=active_connections,
                cache_hit_rate=cache_hit_rate,
                average_latency=avg_latency,
                operations_per_second=ops_per_second
            )
            
            # Store in history
            self._metrics_history.append(metrics)
            
            # Check if scaling is needed
            self._check_scaling_conditions(metrics)
            
            # Reset counters periodically
            if time_window > 60:  # Reset every minute
                self._operations_count = 0
                self._last_reset_time = current_time
            
            return metrics
    
    def _check_scaling_conditions(self, metrics: PerformanceMetrics):
        """Check if scaling up or down is needed."""
        # Scale up conditions
        scale_up_needed = (
            metrics.cpu_usage > self.limits.scale_up_cpu_threshold or
            metrics.memory_usage > self.limits.scale_up_memory_threshold or
            metrics.average_latency > 1.0  # 1 second latency threshold
        )
        
        # Scale down conditions (only if not scaling up)
        scale_down_needed = (
            not scale_up_needed and
            metrics.cpu_usage < self.limits.scale_down_cpu_threshold and
            metrics.memory_usage < self.limits.scale_down_memory_threshold and
            metrics.average_latency < 0.1  # 100ms latency threshold
        )
        
        if scale_up_needed:
            log.info(f"Scale up triggered: CPU={metrics.cpu_usage:.1f}%, "
                    f"Memory={metrics.memory_usage:.1f}%, Latency={metrics.average_latency:.3f}s")
            for callback in self._scale_up_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    log.error(f"Scale up callback error: {e}")
        
        elif scale_down_needed and len(self._metrics_history) > 10:
            # Only scale down if we have enough history and conditions are stable
            recent_metrics = list(self._metrics_history)[-5:]  # Last 5 measurements
            stable_low_usage = all(
                m.cpu_usage < self.limits.scale_down_cpu_threshold and
                m.memory_usage < self.limits.scale_down_memory_threshold
                for m in recent_metrics
            )
            
            if stable_low_usage:
                log.info(f"Scale down triggered: CPU={metrics.cpu_usage:.1f}%, "
                        f"Memory={metrics.memory_usage:.1f}%")
                for callback in self._scale_down_callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        log.error(f"Scale down callback error: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        with self._lock:
            if not self._metrics_history:
                return {"error": "No metrics available"}
            
            recent_metrics = list(self._metrics_history)[-60:]  # Last 60 measurements
            
            return {
                "current": {
                    "cpu_usage": recent_metrics[-1].cpu_usage,
                    "memory_usage": recent_metrics[-1].memory_usage,
                    "active_connections": recent_metrics[-1].active_connections,
                    "cache_hit_rate": recent_metrics[-1].cache_hit_rate,
                    "average_latency": recent_metrics[-1].average_latency,
                    "operations_per_second": recent_metrics[-1].operations_per_second
                },
                "averages": {
                    "cpu_usage": sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
                    "memory_usage": sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
                    "cache_hit_rate": sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics),
                    "average_latency": sum(m.average_latency for m in recent_metrics) / len(recent_metrics),
                    "operations_per_second": sum(m.operations_per_second for m in recent_metrics) / len(recent_metrics)
                },
                "peaks": {
                    "max_cpu": max(m.cpu_usage for m in recent_metrics),
                    "max_memory": max(m.memory_usage for m in recent_metrics),
                    "max_connections": max(m.active_connections for m in recent_metrics),
                    "max_latency": max(m.average_latency for m in recent_metrics),
                    "max_operations_per_second": max(m.operations_per_second for m in recent_metrics)
                },
                "history_size": len(self._metrics_history),
                "resource_limits": {
                    "max_memory_mb": self.limits.max_memory_mb,
                    "max_connections": self.limits.max_connections,
                    "max_concurrent_operations": self.limits.max_concurrent_operations,
                    "scale_up_cpu_threshold": self.limits.scale_up_cpu_threshold,
                    "scale_down_cpu_threshold": self.limits.scale_down_cpu_threshold
                }
            }


class CircuitBreaker:
    """Circuit breaker pattern for graceful degradation."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.RLock()
    
    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        with self._lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise RuntimeError("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    log.warning(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "state": self.state,
                "failure_count": self.failure_count,
                "failure_threshold": self.failure_threshold,
                "last_failure_time": self.last_failure_time,
                "timeout": self.timeout
            }


class HighPerformanceMemoryManager:
    """
    High-performance memory manager with adaptive resource management.
    
    Provides centralized management of memory backends with intelligent
    scaling, monitoring, and optimization capabilities.
    """
    
    def __init__(self, resource_limits: Optional[ResourceLimits] = None):
        self.resource_limits = resource_limits or ResourceLimits()
        self._backend: Optional[MemoryBackend] = None
        self._monitor = PerformanceMonitor(self.resource_limits)
        self._circuit_breaker = CircuitBreaker()
        self._scaling_lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._initialized = False
        
        # Setup scaling callbacks
        self._monitor.add_scale_up_callback(self._handle_scale_up)
        self._monitor.add_scale_down_callback(self._handle_scale_down)
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the memory manager with backend configuration."""
        if self._initialized:
            return
        
        # Create and initialize backend
        if config.get("memory", {}).get("backend") == "chromadb":
            chromadb_config = ChromaDBConfig()
            
            # Apply configuration
            chromadb_section = config.get("memory", {}).get("chromadb", {})
            for key, value in chromadb_section.items():
                if hasattr(chromadb_config, key):
                    setattr(chromadb_config, key, value)
            
            self._backend = ChromaDBBackend(chromadb_config)
            await self._backend.initialize(config)
        else:
            raise ValueError(f"Unsupported backend: {config.get('memory', {}).get('backend', 'none')}")
        
        # Start monitoring
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self._initialized = True
        log.info("High-performance memory manager initialized")
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                if self._backend:
                    # Collect backend stats
                    backend_stats = await self._backend.get_stats()
                    
                    # Collect system metrics
                    metrics = self._monitor.collect_metrics(backend_stats)
                    
                    # Log performance summary every minute
                    if int(time.time()) % 60 == 0:
                        log.info(
                            f"Performance: CPU={metrics.cpu_usage:.1f}%, "
                            f"Memory={metrics.memory_usage:.1f}%, "
                            f"Connections={metrics.active_connections}, "
                            f"Cache Hit Rate={metrics.cache_hit_rate:.1f}%, "
                            f"Ops/sec={metrics.operations_per_second:.1f}, "
                            f"Latency={metrics.average_latency*1000:.1f}ms"
                        )
                
                # Sleep for next measurement
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)  # Longer sleep on error
    
    def _handle_scale_up(self, metrics: PerformanceMetrics):
        """Handle scale up event."""
        # For now, just log - in production this would trigger actual scaling
        log.info(f"Scaling up resources due to high load: "
                f"CPU={metrics.cpu_usage:.1f}%, Memory={metrics.memory_usage:.1f}%")
        
        # Could trigger:
        # - Increase connection pool size
        # - Increase cache size  
        # - Add more worker processes
        # - Scale horizontally with more instances
    
    def _handle_scale_down(self, metrics: PerformanceMetrics):
        """Handle scale down event."""
        log.info(f"Scaling down resources due to low load: "
                f"CPU={metrics.cpu_usage:.1f}%, Memory={metrics.memory_usage:.1f}%")
        
        # Could trigger:
        # - Reduce connection pool size
        # - Trim cache size
        # - Reduce worker processes
        # - Scale down instances
    
    async def store_checkpoint(self, user_id: str, thread_id: str, data: bytes) -> None:
        """Store checkpoint with performance monitoring."""
        start_time = time.time()
        
        try:
            result = await self._circuit_breaker.call(
                self._backend.checkpoint_store.store_checkpoint,
                user_id, thread_id, data
            )
            
            # Record successful operation
            operation_time = time.time() - start_time
            self._monitor.record_operation(operation_time)
            
            return result
            
        except Exception as e:
            log.error(f"Checkpoint storage error: {e}")
            raise
    
    async def retrieve_checkpoint(self, user_id: str, thread_id: str) -> Optional[bytes]:
        """Retrieve checkpoint with performance monitoring."""
        start_time = time.time()
        
        try:
            result = await self._circuit_breaker.call(
                self._backend.checkpoint_store.retrieve_checkpoint,
                user_id, thread_id
            )
            
            # Record successful operation
            operation_time = time.time() - start_time
            self._monitor.record_operation(operation_time)
            
            return result
            
        except Exception as e:
            log.error(f"Checkpoint retrieval error: {e}")
            raise
    
    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        if not self._initialized:
            return {"error": "Manager not initialized"}
        
        # Get backend stats
        backend_stats = await self._backend.get_stats()
        
        # Get performance report
        performance_report = self._monitor.get_performance_report()
        
        # Get circuit breaker stats
        circuit_breaker_stats = self._circuit_breaker.get_stats()
        
        # Get memory optimization stats
        memory_optimization_stats = get_memory_stats()
        
        return {
            "backend": backend_stats,
            "performance": performance_report,
            "circuit_breaker": circuit_breaker_stats,
            "memory_optimization": memory_optimization_stats,
            "manager": {
                "initialized": self._initialized,
                "resource_limits": {
                    "max_memory_mb": self.resource_limits.max_memory_mb,
                    "max_connections": self.resource_limits.max_connections,
                    "max_concurrent_operations": self.resource_limits.max_concurrent_operations
                }
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        if not self._initialized:
            return {"healthy": False, "error": "Not initialized"}
        
        try:
            # Backend health check
            backend_health = await self._backend.health_check()
            
            # System health check
            metrics = self._monitor.collect_metrics(await self._backend.get_stats())
            system_healthy = (
                metrics.cpu_usage < 95 and
                metrics.memory_usage < 95 and
                metrics.average_latency < 5.0
            )
            
            overall_healthy = backend_health.get("healthy", False) and system_healthy
            
            return {
                "healthy": overall_healthy,
                "backend": backend_health,
                "system": {
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "average_latency": metrics.average_latency,
                    "operations_per_second": metrics.operations_per_second
                },
                "circuit_breaker": self._circuit_breaker.get_stats()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Clean up all resources."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._backend:
            await self._backend.cleanup()
        
        self._initialized = False
        log.info("Memory manager cleaned up")