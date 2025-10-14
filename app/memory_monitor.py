"""
Memory usage monitoring for the application.

This module provides tools for monitoring memory usage during application execution.
"""

import os
import platform
import psutil
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Callable
import time

log = logging.getLogger("memory_monitor")

# Global state for memory monitoring
_memory_usage_data: List[Dict[str, Any]] = []
_monitoring_task: Optional[asyncio.Task] = None
_monitoring_interval: float = 5.0  # seconds
_monitoring_active: bool = False

async def monitor_memory_usage(interval: float = 5.0) -> None:
    """
    Start monitoring memory usage at regular intervals.
    
    Args:
        interval: Time between measurements in seconds
    """
    global _monitoring_interval, _monitoring_active, _monitoring_task
    
    if _monitoring_active:
        log.info("Memory monitoring is already active")
        return
        
    _monitoring_interval = interval
    _monitoring_active = True
    
    log.info(f"Starting memory usage monitoring (interval: {interval}s)")
    
    # Run monitoring in a separate task
    _monitoring_task = asyncio.create_task(_memory_monitoring_loop())

async def _memory_monitoring_loop() -> None:
    """Background task that periodically measures memory usage."""
    global _monitoring_active, _memory_usage_data
    
    while _monitoring_active:
        try:
            # Get current process
            process = psutil.Process(os.getpid())
            
            # Collect memory info
            memory_info = process.memory_info()
            usage_data = {
                "timestamp": time.time(),
                "rss_mb": memory_info.rss / (1024 * 1024),  # RSS in MB
                "vms_mb": memory_info.vms / (1024 * 1024),  # VMS in MB
            }
            
            # Add platform-specific data
            if platform.system() == "Linux":
                usage_data["uss_mb"] = getattr(memory_info, "uss", 0) / (1024 * 1024)
                usage_data["pss_mb"] = getattr(memory_info, "pss", 0) / (1024 * 1024)
            
            # Store the data
            _memory_usage_data.append(usage_data)
            
            # Keep last 1000 measurements to limit memory usage
            if len(_memory_usage_data) > 1000:
                _memory_usage_data = _memory_usage_data[-1000:]
                
            # Log periodically (every 12 measurements = ~60s if interval=5s)
            if len(_memory_usage_data) % 12 == 0:
                current = usage_data["rss_mb"]
                avg = sum(d["rss_mb"] for d in _memory_usage_data[-12:]) / 12
                log.info(f"Memory usage: {current:.1f} MB (RSS), avg last minute: {avg:.1f} MB")
                
        except Exception as e:
            log.error(f"Error in memory monitoring: {e}")
            
        # Wait for next interval
        await asyncio.sleep(_monitoring_interval)

def get_memory_stats() -> Dict[str, Any]:
    """Get memory usage statistics."""
    try:
        # Get current process memory info
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # System memory info
        sys_memory = psutil.virtual_memory()
        
        # Historical data statistics
        if _memory_usage_data:
            rss_values = [d["rss_mb"] for d in _memory_usage_data]
            rss_min = min(rss_values)
            rss_max = max(rss_values)
            rss_avg = sum(rss_values) / len(rss_values)
        else:
            rss_min = rss_max = rss_avg = 0
        
        return {
            "current": {
                "rss_mb": memory_info.rss / (1024 * 1024),
                "vms_mb": memory_info.vms / (1024 * 1024),
                "percent": process.memory_percent()
            },
            "system": {
                "total_gb": sys_memory.total / (1024 * 1024 * 1024),
                "available_gb": sys_memory.available / (1024 * 1024 * 1024),
                "percent_used": sys_memory.percent
            },
            "historical": {
                "samples": len(_memory_usage_data),
                "monitoring_active": _monitoring_active,
                "min_rss_mb": rss_min,
                "max_rss_mb": rss_max,
                "avg_rss_mb": rss_avg
            }
        }
    except Exception as e:
        log.error(f"Error getting memory stats: {e}")
        return {
            "error": str(e),
            "monitoring_active": _monitoring_active,
            "samples": len(_memory_usage_data)
        }
