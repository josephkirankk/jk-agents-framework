"""
Memory Monitoring and Auto-Cleanup System

Provides comprehensive memory monitoring, automatic cleanup triggers, and system health
reporting for the JK-Agents Framework.
"""

import threading
import time
import gc
import logging
import weakref
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

logger = logging.getLogger(__name__)


@dataclass
class MemoryThresholds:
    """Memory usage thresholds for triggering cleanup actions."""
    warning_mb: float = 1000.0      # Log warning
    cleanup_mb: float = 1500.0      # Trigger cleanup
    critical_mb: float = 2000.0     # Aggressive cleanup
    emergency_mb: float = 3000.0    # Emergency cleanup + GC


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a point in time."""
    timestamp: datetime
    process_memory_mb: float
    virtual_memory_mb: float
    system_memory_percent: float
    python_objects_count: int
    storage_stats: Dict[str, Any]
    tool_stats: Dict[str, Any]


class MemoryMonitor:
    """
    Memory monitoring and auto-cleanup system for the JK-Agents Framework.
    
    Features:
    - Continuous memory monitoring
    - Automatic cleanup triggers based on thresholds
    - Memory usage history and reporting
    - Integration with LargeDataStorage and SmartToolWrapper
    - System health monitoring
    """
    
    def __init__(self,
                 storage_manager=None,
                 tool_wrapper=None,
                 monitoring_interval: int = 30,
                 thresholds: Optional[MemoryThresholds] = None,
                 history_size: int = 100,
                 enable_auto_cleanup: bool = True):
        
        self.storage_manager = storage_manager
        self.tool_wrapper = tool_wrapper
        self.monitoring_interval = monitoring_interval
        self.thresholds = thresholds or MemoryThresholds()
        self.history_size = history_size
        self.enable_auto_cleanup = enable_auto_cleanup
        
        # State management
        self._monitoring = False
        self._monitor_thread = None
        self._lock = threading.RLock()
        
        # Memory snapshots history
        self._memory_history: List[MemorySnapshot] = []
        
        # Cleanup callbacks
        self._cleanup_callbacks: List[Callable[[], Dict[str, Any]]] = []
        
        # Statistics
        self._stats = {
            "monitoring_started": None,
            "total_snapshots": 0,
            "cleanup_triggers": 0,
            "gc_triggers": 0,
            "emergency_cleanups": 0,
            "last_cleanup": None,
            "memory_warnings": 0
        }
        
        # Register default cleanup callbacks
        self._register_default_callbacks()
        
        if not HAS_PSUTIL:
            logger.warning("psutil not available - memory monitoring will be limited")
        
        logger.info(f"MemoryMonitor initialized with {monitoring_interval}s interval, "
                   f"auto-cleanup: {enable_auto_cleanup}")
    
    def _register_default_callbacks(self):
        """Register default cleanup callbacks for storage and tools."""
        if self.storage_manager:
            self._cleanup_callbacks.append(
                lambda: {"storage_cache_cleared": self.storage_manager.clear_cache()}
            )
            self._cleanup_callbacks.append(
                lambda: {"storage_optimized": self.storage_manager.optimize_cache()}
            )
        
        if self.tool_wrapper:
            self._cleanup_callbacks.append(
                lambda: {"expired_tools_cleaned": self.tool_wrapper.cleanup_expired_tools()}
            )
            self._cleanup_callbacks.append(
                lambda: self.tool_wrapper.force_cleanup(keep_recent_hours=0.5)
            )
    
    def start_monitoring(self):
        """Start the memory monitoring thread."""
        with self._lock:
            if self._monitoring:
                logger.warning("Memory monitoring is already running")
                return
            
            self._monitoring = True
            self._stats["monitoring_started"] = datetime.now()
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            
            logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop the memory monitoring thread."""
        with self._lock:
            if not self._monitoring:
                return
            
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=5)
            
            logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        while self._monitoring:
            try:
                # Take memory snapshot
                snapshot = self._take_memory_snapshot()
                
                # Add to history
                with self._lock:
                    self._memory_history.append(snapshot)
                    if len(self._memory_history) > self.history_size:
                        self._memory_history.pop(0)
                    self._stats["total_snapshots"] += 1
                
                # Check thresholds and trigger actions
                if self.enable_auto_cleanup:
                    self._check_and_respond_to_thresholds(snapshot)
                
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
            
            # Wait for next interval
            time.sleep(self.monitoring_interval)
    
    def _take_memory_snapshot(self) -> MemorySnapshot:
        """Take a snapshot of current memory usage."""
        # Get process memory info
        process_memory_mb = 0.0
        virtual_memory_mb = 0.0
        system_memory_percent = 0.0
        
        if HAS_PSUTIL:
            try:
                import os
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                
                process_memory_mb = memory_info.rss / (1024 * 1024)
                virtual_memory_mb = memory_info.vms / (1024 * 1024)
                
                # System memory
                system_memory = psutil.virtual_memory()
                system_memory_percent = system_memory.percent
                
            except Exception as e:
                logger.debug(f"Error getting memory info: {e}")
        
        # Get Python object count
        python_objects_count = len(gc.get_objects())
        
        # Get storage statistics
        storage_stats = {}
        if self.storage_manager and hasattr(self.storage_manager, 'get_performance_stats'):
            try:
                storage_stats = self.storage_manager.get_performance_stats()
            except Exception as e:
                logger.debug(f"Error getting storage stats: {e}")
        
        # Get tool statistics
        tool_stats = {}
        if self.tool_wrapper and hasattr(self.tool_wrapper, 'get_tool_stats'):
            try:
                tool_stats = self.tool_wrapper.get_tool_stats()
            except Exception as e:
                logger.debug(f"Error getting tool stats: {e}")
        
        return MemorySnapshot(
            timestamp=datetime.now(),
            process_memory_mb=process_memory_mb,
            virtual_memory_mb=virtual_memory_mb,
            system_memory_percent=system_memory_percent,
            python_objects_count=python_objects_count,
            storage_stats=storage_stats,
            tool_stats=tool_stats
        )
    
    def _check_and_respond_to_thresholds(self, snapshot: MemorySnapshot):
        """Check memory thresholds and trigger appropriate responses."""
        memory_mb = snapshot.process_memory_mb
        
        if memory_mb >= self.thresholds.emergency_mb:
            # Emergency cleanup
            logger.critical(f"EMERGENCY: Memory usage at {memory_mb:.1f}MB, triggering aggressive cleanup")
            self._trigger_emergency_cleanup()
            self._stats["emergency_cleanups"] += 1
            
        elif memory_mb >= self.thresholds.critical_mb:
            # Critical cleanup
            logger.error(f"CRITICAL: Memory usage at {memory_mb:.1f}MB, triggering critical cleanup")
            self._trigger_critical_cleanup()
            self._stats["cleanup_triggers"] += 1
            
        elif memory_mb >= self.thresholds.cleanup_mb:
            # Standard cleanup
            logger.warning(f"HIGH: Memory usage at {memory_mb:.1f}MB, triggering cleanup")
            self._trigger_cleanup()
            self._stats["cleanup_triggers"] += 1
            
        elif memory_mb >= self.thresholds.warning_mb:
            # Just log warning
            logger.info(f"Memory usage at {memory_mb:.1f}MB (warning threshold)")
            self._stats["memory_warnings"] += 1
    
    def _trigger_cleanup(self) -> Dict[str, Any]:
        """Trigger standard cleanup procedures."""
        cleanup_results = {}
        
        # Run registered cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                result = callback()
                if isinstance(result, dict):
                    cleanup_results.update(result)
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")
        
        self._stats["last_cleanup"] = datetime.now()
        return cleanup_results
    
    def _trigger_critical_cleanup(self) -> Dict[str, Any]:
        """Trigger critical cleanup (more aggressive)."""
        cleanup_results = self._trigger_cleanup()
        
        # Force garbage collection
        collected = gc.collect()
        cleanup_results["gc_collected_objects"] = collected
        self._stats["gc_triggers"] += 1
        
        logger.info(f"Critical cleanup completed: {cleanup_results}")
        return cleanup_results
    
    def _trigger_emergency_cleanup(self) -> Dict[str, Any]:
        """Trigger emergency cleanup (most aggressive)."""
        cleanup_results = self._trigger_critical_cleanup()
        
        # Additional emergency measures
        if self.storage_manager and hasattr(self.storage_manager, 'clear_cache'):
            try:
                self.storage_manager.clear_cache()
                cleanup_results["emergency_cache_clear"] = True
            except Exception as e:
                logger.error(f"Emergency cache clear failed: {e}")
        
        if self.tool_wrapper and hasattr(self.tool_wrapper, 'force_cleanup'):
            try:
                tool_cleanup = self.tool_wrapper.force_cleanup(keep_recent_hours=0.1)
                cleanup_results.update(tool_cleanup)
            except Exception as e:
                logger.error(f"Emergency tool cleanup failed: {e}")
        
        # Multiple garbage collection passes
        for i in range(3):
            collected = gc.collect()
            cleanup_results[f"gc_pass_{i+1}"] = collected
        
        logger.critical(f"Emergency cleanup completed: {cleanup_results}")
        return cleanup_results
    
    def register_cleanup_callback(self, callback: Callable[[], Dict[str, Any]]):
        """Register a custom cleanup callback."""
        self._cleanup_callbacks.append(callback)
        logger.info("Registered custom cleanup callback")
    
    def get_current_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        snapshot = self._take_memory_snapshot()
        
        return {
            "process_memory_mb": snapshot.process_memory_mb,
            "virtual_memory_mb": snapshot.virtual_memory_mb,
            "system_memory_percent": snapshot.system_memory_percent,
            "python_objects_count": snapshot.python_objects_count,
            "thresholds": {
                "warning_mb": self.thresholds.warning_mb,
                "cleanup_mb": self.thresholds.cleanup_mb,
                "critical_mb": self.thresholds.critical_mb,
                "emergency_mb": self.thresholds.emergency_mb
            },
            "storage_stats": snapshot.storage_stats,
            "tool_stats": snapshot.tool_stats
        }
    
    def get_memory_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get memory usage history."""
        with self._lock:
            history = self._memory_history[-limit:] if limit > 0 else self._memory_history
            
            return [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "process_memory_mb": snapshot.process_memory_mb,
                    "virtual_memory_mb": snapshot.virtual_memory_mb,
                    "system_memory_percent": snapshot.system_memory_percent,
                    "python_objects_count": snapshot.python_objects_count
                }
                for snapshot in history
            ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring and cleanup statistics."""
        with self._lock:
            stats = self._stats.copy()
            
            if stats["monitoring_started"]:
                uptime = datetime.now() - stats["monitoring_started"]
                stats["uptime_hours"] = uptime.total_seconds() / 3600
            
            if stats["last_cleanup"]:
                stats["last_cleanup"] = stats["last_cleanup"].isoformat()
            
            if stats["monitoring_started"]:
                stats["monitoring_started"] = stats["monitoring_started"].isoformat()
            
            # Add current status
            stats["monitoring_active"] = self._monitoring
            stats["cleanup_callbacks_count"] = len(self._cleanup_callbacks)
            stats["memory_history_size"] = len(self._memory_history)
            
            return stats
    
    def force_cleanup(self, level: str = "standard") -> Dict[str, Any]:
        """Manually trigger cleanup at specified level."""
        if level == "standard":
            return self._trigger_cleanup()
        elif level == "critical":
            return self._trigger_critical_cleanup()
        elif level == "emergency":
            return self._trigger_emergency_cleanup()
        else:
            raise ValueError(f"Invalid cleanup level: {level}. Use 'standard', 'critical', or 'emergency'")
    
    def update_thresholds(self, **kwargs):
        """Update memory thresholds."""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                logger.info(f"Updated threshold {key} to {value}")
            else:
                logger.warning(f"Unknown threshold: {key}")
    
    def generate_memory_report(self) -> Dict[str, Any]:
        """Generate a comprehensive memory usage report."""
        current_usage = self.get_current_memory_usage()
        history = self.get_memory_history(10)
        stats = self.get_statistics()
        
        # Calculate trends if we have history
        trends = {}
        if len(history) >= 2:
            recent_memory = [h["process_memory_mb"] for h in history[-5:]]
            if recent_memory:
                trends["memory_trend_mb"] = recent_memory[-1] - recent_memory[0]
                trends["avg_memory_last_5"] = sum(recent_memory) / len(recent_memory)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "current_usage": current_usage,
            "statistics": stats,
            "trends": trends,
            "recent_history": history,
            "health_status": self._assess_health_status(current_usage),
            "recommendations": self._generate_recommendations(current_usage, trends)
        }
    
    def _assess_health_status(self, usage: Dict[str, Any]) -> str:
        """Assess overall memory health status."""
        memory_mb = usage["process_memory_mb"]
        
        if memory_mb >= self.thresholds.emergency_mb:
            return "EMERGENCY"
        elif memory_mb >= self.thresholds.critical_mb:
            return "CRITICAL"
        elif memory_mb >= self.thresholds.cleanup_mb:
            return "HIGH"
        elif memory_mb >= self.thresholds.warning_mb:
            return "ELEVATED"
        else:
            return "HEALTHY"
    
    def _generate_recommendations(self, usage: Dict[str, Any], trends: Dict[str, Any]) -> List[str]:
        """Generate memory optimization recommendations."""
        recommendations = []
        memory_mb = usage["process_memory_mb"]
        
        if memory_mb >= self.thresholds.cleanup_mb:
            recommendations.append("Consider running manual cleanup to free memory")
        
        if trends.get("memory_trend_mb", 0) > 100:
            recommendations.append("Memory usage is trending upward - monitor closely")
        
        if usage.get("python_objects_count", 0) > 100000:
            recommendations.append("High number of Python objects - check for memory leaks")
        
        # Storage-specific recommendations
        storage_stats = usage.get("storage_stats", {})
        if storage_stats.get("cache_hit_rate", 1.0) < 0.5:
            recommendations.append("Low cache hit rate - consider optimizing data access patterns")
        
        # Tool-specific recommendations
        tool_stats = usage.get("tool_stats", {})
        if tool_stats.get("active_tools", 0) > 500:
            recommendations.append("High number of active dynamic tools - consider more aggressive cleanup")
        
        if not recommendations:
            recommendations.append("Memory usage is healthy - no immediate action required")
        
        return recommendations


# Global memory monitor instance
_global_memory_monitor: Optional[MemoryMonitor] = None


def get_global_memory_monitor() -> Optional[MemoryMonitor]:
    """Get the global memory monitor instance."""
    return _global_memory_monitor


def initialize_global_memory_monitor(storage_manager=None, tool_wrapper=None, **kwargs) -> MemoryMonitor:
    """Initialize the global memory monitor."""
    global _global_memory_monitor
    
    if _global_memory_monitor:
        logger.warning("Global memory monitor already initialized")
        return _global_memory_monitor
    
    _global_memory_monitor = MemoryMonitor(
        storage_manager=storage_manager,
        tool_wrapper=tool_wrapper,
        **kwargs
    )
    
    logger.info("Global memory monitor initialized")
    return _global_memory_monitor