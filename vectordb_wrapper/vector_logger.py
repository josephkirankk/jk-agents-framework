"""
Vector Operations Logger

This module provides comprehensive logging functionality for VectorDB operations,
including upsert and search operations with detailed performance metrics and
cross-platform compatibility.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class VectorLogger:
    """
    Logger for VectorDB operations with timestamped file logging.

    Creates log files in the format: vector_<YYYYMMDDHHMMSS>.json
    Stores logs in the vectorlogs directory within the vectordb_wrapper folder.
    """
    
    def __init__(self, base_dir: Optional[Path] = None, enabled: bool = True):
        """
        Initialize the VectorLogger.
        
        Args:
            base_dir: Base directory for logs. If None, uses vectordb_wrapper/vectorlogs
            enabled: Whether logging is enabled
        """
        self.enabled = enabled and os.getenv("VECTORDB_VECTOR_LOGGING", "true").lower() == "true"
        
        if base_dir is None:
            # Get the directory where this module is located (vectordb_wrapper)
            module_dir = Path(__file__).parent
            self.log_dir = module_dir / "vectorlogs"
        else:
            self.log_dir = Path(base_dir)
        
        self._ensure_log_directory()
    
    def _ensure_log_directory(self) -> None:
        """Create the log directory if it doesn't exist."""
        if not self.enabled:
            return
            
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Vector log directory ensured: {self.log_dir}")
        except Exception as e:
            logger.error(f"Failed to create vector log directory {self.log_dir}: {e}")
            self.enabled = False
    
    def _generate_log_filename(self, timestamp: datetime) -> str:
        """
        Generate a timestamped log filename.

        Args:
            timestamp: Datetime object for the timestamp

        Returns:
            Filename in format: vector_YYYYMMDDHHMMSS.json
        """
        return f"vector_{timestamp.strftime('%Y%m%d%H%M%S')}.json"
    
    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """
        Write a log entry to the appropriate log file.
        
        Args:
            log_entry: Dictionary containing log data
        """
        if not self.enabled:
            return
            
        try:
            # Use the operation start time for filename consistency
            timestamp = datetime.fromisoformat(log_entry["operation_start"].replace('Z', '+00:00'))
            filename = self._generate_log_filename(timestamp)
            log_file_path = self.log_dir / filename
            
            # Write log entry as JSON line with proper encoding for Windows
            with open(log_file_path, 'a', encoding='utf-8', newline='') as f:
                json.dump(log_entry, f, ensure_ascii=False, separators=(',', ':'))
                f.write('\n')
                
            logger.debug(f"Vector log entry written to {log_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to write vector log entry: {e}")
    
    def log_operation(
        self,
        operation_type: str,
        operation_start: datetime,
        operation_end: datetime,
        input_parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a vector operation with comprehensive details.
        
        Args:
            operation_type: Type of operation (search, upsert, etc.)
            operation_start: When the operation started
            operation_end: When the operation ended
            input_parameters: Input parameters for the operation
            result: Operation result (if successful)
            error: Error message (if failed)
            performance_metrics: Additional performance metrics
        """
        if not self.enabled:
            return
            
        execution_time_ms = (operation_end - operation_start).total_seconds() * 1000
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "operation_start": operation_start.isoformat(),
            "operation_end": operation_end.isoformat(),
            "execution_time_ms": round(execution_time_ms, 3),
            "input_parameters": self._sanitize_parameters(input_parameters),
            "success": error is None,
            "performance_metrics": performance_metrics or {}
        }
        
        if result is not None:
            log_entry["result"] = self._sanitize_result(result)
        
        if error is not None:
            log_entry["error"] = str(error)
            
        self._write_log_entry(log_entry)
    
    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize input parameters for logging (remove sensitive data if any).
        
        Args:
            params: Original parameters
            
        Returns:
            Sanitized parameters
        """
        # For now, just return as-is since VectorDB params don't contain sensitive data
        # In the future, we could filter out specific fields if needed
        return params
    
    def _sanitize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize result data for logging.
        
        Args:
            result: Original result
            
        Returns:
            Sanitized result (may be summarized for large results)
        """
        # For search results, we might want to limit the number of results logged
        if "results" in result and isinstance(result["results"], list):
            result_copy = result.copy()
            results = result_copy["results"]
            if len(results) > 10:  # Limit to first 10 results for logging
                result_copy["results"] = results[:10]
                result_copy["results_truncated"] = True
                result_copy["total_results_count"] = len(results)
            return result_copy
        
        return result


# Global logger instance
_vector_logger: Optional[VectorLogger] = None


def get_vector_logger() -> VectorLogger:
    """
    Get the global VectorLogger instance.
    
    Returns:
        VectorLogger instance
    """
    global _vector_logger
    if _vector_logger is None:
        _vector_logger = VectorLogger()
    return _vector_logger


def log_vector_operation(
    operation_type: str,
    operation_start: datetime,
    operation_end: datetime,
    input_parameters: Dict[str, Any],
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    performance_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Convenience function to log a vector operation.
    
    Args:
        operation_type: Type of operation (search, upsert, etc.)
        operation_start: When the operation started
        operation_end: When the operation ended
        input_parameters: Input parameters for the operation
        result: Operation result (if successful)
        error: Error message (if failed)
        performance_metrics: Additional performance metrics
    """
    vector_logger = get_vector_logger()
    vector_logger.log_operation(
        operation_type=operation_type,
        operation_start=operation_start,
        operation_end=operation_end,
        input_parameters=input_parameters,
        result=result,
        error=error,
        performance_metrics=performance_metrics
    )
