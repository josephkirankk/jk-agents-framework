"""
Smart Tool Wrapper

Automatically detects large tool outputs, stores them efficiently, generates intelligent
summaries, and creates dynamic tools for data exploration.
"""

import json
import sys
import time
import weakref
import threading
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

class SmartToolWrapper:
    """
    Smart wrapper that automatically handles large tool outputs by:
    1. Detecting large data (based on token threshold)
    2. Storing data in optimized storage
    3. Generating intelligent summaries
    4. Creating dynamic tools for data exploration
    """
    
    def __init__(self, 
                 storage,
                 token_threshold: int = 5000,
                 summarization_max_tokens: int = 500,
                 custom_summarizer: Optional[Callable] = None,
                 tool_expiry_hours: int = 24,
                 max_dynamic_tools: int = 1000):
        
        self.storage = storage
        self.token_threshold = token_threshold
        self.summarization_max_tokens = summarization_max_tokens
        self.custom_summarizer = custom_summarizer
        self.tool_expiry_hours = tool_expiry_hours
        self.max_dynamic_tools = max_dynamic_tools
        
        # Enhanced dynamic tools storage with metadata
        self.dynamic_tools = {}  # tool_name -> function
        self.tool_metadata = {}  # tool_name -> {created_at, last_used, usage_count, reference_id}
        self.tool_lock = threading.RLock()
        
        # Statistics
        self._stats = {
            "tools_created": 0,
            "tools_expired": 0,
            "tools_evicted": 0,
            "total_tool_calls": 0,
        }
        
        logger.info(f"SmartToolWrapper initialized with token threshold: {token_threshold}, "+ 
                   f"tool expiry: {tool_expiry_hours}h, max tools: {max_dynamic_tools}")
    
    def _estimate_tokens(self, data: Any) -> int:
        """Estimate number of tokens in data (rough approximation)"""
        try:
            data_str = json.dumps(data, default=str)
            # Rough estimate: ~4 characters per token
            return len(data_str) // 4
        except:
            # Fallback for non-JSON serializable data
            return len(str(data)) // 4
    
    def _generate_summary(self, data: Any, data_type: str) -> str:
        """Generate intelligent summary of data"""
        
        # Use custom summarizer if provided
        if self.custom_summarizer:
            try:
                return self.custom_summarizer(data, data_type, self.summarization_max_tokens)
            except Exception as e:
                logger.warning(f"Custom summarizer failed: {e}, falling back to default")
        
        # Default summarization logic
        try:
            if isinstance(data, list):
                return self._summarize_list(data, data_type)
            elif isinstance(data, dict):
                return self._summarize_dict(data, data_type)
            else:
                return f"{data_type}: {type(data).__name__} with {len(str(data))} characters"
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"{data_type}: Large dataset (summarization failed)"
    
    def _summarize_list(self, data: List, data_type: str) -> str:
        """Summarize list/array data"""
        count = len(data)
        
        if count == 0:
            return f"{data_type}: Empty list"
        
        # Sample first few items to understand structure
        sample_size = min(3, count)
        sample_items = data[:sample_size]
        
        # Analyze structure
        if all(isinstance(item, dict) for item in sample_items):
            # List of dictionaries (like records)
            if sample_items:
                keys = list(sample_items[0].keys())
                key_summary = ", ".join(keys[:5]) + ("..." if len(keys) > 5 else "")
                
                # Try to identify common patterns
                patterns = []
                if any(key in keys for key in ['id', 'ID', '_id']):
                    patterns.append("records with IDs")
                if any(key in keys for key in ['date', 'timestamp', 'created_at']):
                    patterns.append("time-series data")
                if any(key in keys for key in ['amount', 'price', 'value', 'total']):
                    patterns.append("financial data")
                if any(key in keys for key in ['name', 'title', 'description']):
                    patterns.append("descriptive records")
                
                pattern_desc = f" ({', '.join(patterns)})" if patterns else ""
                return f"{data_type}: {count:,} records{pattern_desc} with fields: {key_summary}"
            
        elif all(isinstance(item, (int, float)) for item in sample_items):
            # Numeric data
            try:
                min_val = min(data)
                max_val = max(data)
                avg_val = sum(data) / len(data)
                return f"{data_type}: {count:,} numbers (min: {min_val}, max: {max_val}, avg: {avg_val:.2f})"
            except:
                return f"{data_type}: {count:,} numeric values"
                
        elif all(isinstance(item, str) for item in sample_items):
            # String data
            avg_length = sum(len(str(item)) for item in sample_items) / sample_size
            return f"{data_type}: {count:,} text items (avg length: {avg_length:.0f} chars)"
        
        return f"{data_type}: {count:,} items of mixed types"
    
    def _summarize_dict(self, data: Dict, data_type: str) -> str:
        """Summarize dictionary data"""
        keys = list(data.keys())
        key_count = len(keys)
        
        if key_count == 0:
            return f"{data_type}: Empty dictionary"
        
        # Show first few keys
        key_summary = ", ".join(keys[:5]) + ("..." if key_count > 5 else "")
        
        # Analyze structure and identify patterns
        patterns = []
        large_collections = []
        
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 100:
                large_collections.append(f"{key} ({len(value)} items)")
            elif isinstance(value, dict) and len(value) > 20:
                large_collections.append(f"{key} ({len(value)} fields)")
        
        # Common data patterns
        if any(key in keys for key in ['summary', 'metadata', 'info']):
            patterns.append("structured report")
        if any(key in keys for key in ['data', 'records', 'results']):
            patterns.append("data container")
        if any(key in keys for key in ['total', 'count', 'statistics', 'stats']):
            patterns.append("analytical data")
        if any(key in keys for key in ['date', 'timestamp', 'period']):
            patterns.append("time-based data")
        
        pattern_desc = f" ({', '.join(patterns)})" if patterns else ""
        collection_desc = f" - Large collections: {', '.join(large_collections)}" if large_collections else ""
        
        return f"{data_type}: Dictionary with {key_count} keys{pattern_desc} - Keys: {key_summary}{collection_desc}"
    
    def _create_dynamic_tools(self, reference_id: str, data_type: str, data_structure_info: Dict) -> List[str]:
        """Create dynamic tools for exploring the stored data"""
        
        tools = []
        
        # Always create these basic tools
        basic_tools = [
            f"get_data_details_{reference_id}",
            f"get_data_stats_{reference_id}"
        ]
        
        # Create search tool for complex data structures
        if data_structure_info.get('is_searchable', False):
            basic_tools.append(f"search_data_{reference_id}")
        
        # Generate tool functions with lifecycle management
        current_time = time.time()
        
        with self.tool_lock:
            # Check if we need to cleanup expired tools first
            self._cleanup_expired_tools()
            
            # Check if we need to evict tools due to size limit
            if len(self.dynamic_tools) + len(basic_tools) > self.max_dynamic_tools:
                self._evict_least_used_tools(len(basic_tools))
            
            for tool_name in basic_tools:
                # Create the tool function
                tool_func = self._create_tool_function(tool_name, reference_id, data_type)
                self.dynamic_tools[tool_name] = tool_func
                
                # Store metadata
                self.tool_metadata[tool_name] = {
                    "created_at": current_time,
                    "last_used": current_time,
                    "usage_count": 0,
                    "reference_id": reference_id,
                    "data_type": data_type
                }
                
                tools.append(tool_name)
                self._stats["tools_created"] += 1
        
        return tools
    
    def _create_tool_function(self, tool_name: str, reference_id: str, data_type: str) -> Callable:
        """Create a dynamic tool function for data exploration"""
        
        if "get_data_details" in tool_name:
            def get_details(max_items: int = 10, filter_by: Optional[str] = None, filter_value: Optional[str] = None):
                """Get detailed information about specific parts of the data"""
                try:
                    full_data = self.storage.get_data(reference_id)
                    if not full_data:
                        return {"error": "Data not found"}
                    
                    if isinstance(full_data, list):
                        # Handle list data
                        result_data = full_data[:max_items]
                        if filter_by and filter_value:
                            result_data = [item for item in result_data 
                                         if isinstance(item, dict) and str(item.get(filter_by)) == filter_value]
                        return {
                            "sample_data": result_data,
                            "total_items": len(full_data),
                            "showing_items": len(result_data),
                            "data_type": type(full_data).__name__
                        }
                    
                    elif isinstance(full_data, dict):
                        # Handle dictionary data
                        if filter_by:
                            filtered = {k: v for k, v in full_data.items() if filter_by.lower() in k.lower()}
                            return {"filtered_data": dict(list(filtered.items())[:max_items]), "total_keys": len(full_data)}
                        else:
                            return {"sample_data": dict(list(full_data.items())[:max_items]), "total_keys": len(full_data)}
                    
                    else:
                        return {"data": str(full_data)[:1000], "type": type(full_data).__name__}
                
                except Exception as e:
                    return {"error": f"Failed to get data details: {str(e)}"}
            
            return get_details
        
        elif "get_data_stats" in tool_name:
            def get_stats():
                """Get statistical summary of the data"""
                try:
                    full_data = self.storage.get_data(reference_id)
                    metadata = self.storage.get_metadata(reference_id)
                    
                    if not full_data:
                        return {"error": "Data not found"}
                    
                    stats = {
                        "data_type": type(full_data).__name__,
                        "storage_info": metadata,
                        "structure_analysis": {}
                    }
                    
                    if isinstance(full_data, list):
                        stats["structure_analysis"] = {
                            "type": "list",
                            "length": len(full_data),
                            "item_types": list(set(type(item).__name__ for item in full_data[:100])),
                            "sample_keys": list(full_data[0].keys()) if full_data and isinstance(full_data[0], dict) else None
                        }
                    
                    elif isinstance(full_data, dict):
                        stats["structure_analysis"] = {
                            "type": "dictionary", 
                            "key_count": len(full_data),
                            "keys": list(full_data.keys())[:20],  # First 20 keys
                            "value_types": list(set(type(v).__name__ for v in full_data.values()))
                        }
                    
                    return stats
                
                except Exception as e:
                    return {"error": f"Failed to get data stats: {str(e)}"}
            
            return get_stats
        
        elif "search_data" in tool_name:
            def search_data(query: str, max_results: int = 10):
                """Search within the data for specific patterns or values"""
                try:
                    full_data = self.storage.get_data(reference_id)
                    if not full_data:
                        return {"error": "Data not found"}
                    
                    results = []
                    query_lower = query.lower()
                    
                    if isinstance(full_data, list):
                        for i, item in enumerate(full_data):
                            if len(results) >= max_results:
                                break
                            
                            item_str = str(item).lower()
                            if query_lower in item_str:
                                results.append({"index": i, "item": item, "match_type": "content"})
                    
                    elif isinstance(full_data, dict):
                        for key, value in full_data.items():
                            if len(results) >= max_results:
                                break
                            
                            if query_lower in key.lower() or query_lower in str(value).lower():
                                results.append({"key": key, "value": value, "match_type": "key_or_value"})
                    
                    return {
                        "query": query,
                        "results": results,
                        "total_matches": len(results),
                        "search_completed": len(results) < max_results
                    }
                
                except Exception as e:
                    return {"error": f"Search failed: {str(e)}"}
            
            return search_data
        
        else:
            # Default function
            def default_func():
                return {"error": f"Tool {tool_name} not implemented"}
            return default_func
    
    def get_dynamic_tool_function(self, tool_name: str) -> Optional[Callable]:
        """Get a dynamic tool function by name with usage tracking"""
        with self.tool_lock:
            tool_func = self.dynamic_tools.get(tool_name)
            if tool_func and tool_name in self.tool_metadata:
                # Update usage tracking
                self.tool_metadata[tool_name]["last_used"] = time.time()
                self.tool_metadata[tool_name]["usage_count"] += 1
                self._stats["total_tool_calls"] += 1
            return tool_func
    
    def wrap_tool_result(self, result: Any, tool_name: str) -> Any:
        """
        Main wrapper function that decides whether to store data or return directly
        
        Args:
            result: Tool execution result
            tool_name: Name of the tool that generated the result
            
        Returns:
            Either the original result (if small) or a reference object (if large)
        """
        try:
            # Estimate size in tokens
            estimated_tokens = self._estimate_tokens(result)
            
            if estimated_tokens <= self.token_threshold:
                # Small result - return directly
                logger.debug(f"Tool {tool_name} result is small ({estimated_tokens} tokens), returning directly")
                return result
            
            # Large result - store and create reference
            logger.info(f"Tool {tool_name} result is large ({estimated_tokens:,} tokens), creating reference")
            
            # Store the data
            reference_id = self.storage.store_data(result, f"{tool_name}_result")
            
            # Generate summary
            summary = self._generate_summary(result, tool_name)
            
            # Analyze data structure for dynamic tool creation
            data_structure_info = self._analyze_data_structure(result)
            
            # Create dynamic tools
            dynamic_tools = self._create_dynamic_tools(reference_id, tool_name, data_structure_info)
            
            # Create reference object
            reference_object = {
                "type": "large_data_reference",
                "reference_id": reference_id,
                "tool_name": tool_name,
                "summary": summary,
                "estimated_tokens": estimated_tokens,
                "created_at": datetime.now().isoformat(),
                "dynamic_tools": dynamic_tools,
                "data_structure": data_structure_info,
                "instructions": {
                    "how_to_access": f"Use the dynamic tools to explore this data: {', '.join(dynamic_tools)}",
                    "get_details": f"Call get_data_details_{reference_id}(max_items=N) to see specific data samples",
                    "get_stats": f"Call get_data_stats_{reference_id}() to see data statistics", 
                    "search": f"Call search_data_{reference_id}('query') to search within the data" if f"search_data_{reference_id}" in dynamic_tools else None
                }
            }
            
            # Remove None instructions
            reference_object["instructions"] = {k: v for k, v in reference_object["instructions"].items() if v is not None}
            
            return reference_object
            
        except Exception as e:
            logger.error(f"Error wrapping tool result: {e}")
            # Return original result if wrapping fails
            return result
    
    def _analyze_data_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure to determine what tools to create"""
        
        structure_info = {
            "type": type(data).__name__,
            "is_searchable": False,
            "has_records": False,
            "has_time_data": False,
            "has_numeric_data": False,
            "complexity": "simple"
        }
        
        try:
            if isinstance(data, list):
                structure_info["length"] = len(data)
                structure_info["is_searchable"] = True
                
                if data and isinstance(data[0], dict):
                    structure_info["has_records"] = True
                    structure_info["complexity"] = "complex"
                    
                    # Sample first record to understand structure
                    sample = data[0]
                    keys = list(sample.keys()) if isinstance(sample, dict) else []
                    
                    # Check for time data
                    if any(key in keys for key in ['date', 'timestamp', 'created_at', 'time']):
                        structure_info["has_time_data"] = True
                    
                    # Check for numeric data
                    if any(isinstance(sample.get(key), (int, float)) for key in keys):
                        structure_info["has_numeric_data"] = True
            
            elif isinstance(data, dict):
                structure_info["key_count"] = len(data)
                structure_info["is_searchable"] = True
                structure_info["complexity"] = "medium" if len(data) > 10 else "simple"
                
                # Check for nested structures
                for value in list(data.values())[:5]:  # Sample first 5 values
                    if isinstance(value, (list, dict)):
                        structure_info["complexity"] = "complex"
                        break
        
        except Exception as e:
            logger.warning(f"Error analyzing data structure: {e}")
        
        return structure_info
    
    def _cleanup_expired_tools(self) -> int:
        """
        Clean up expired dynamic tools.
        
        Returns:
            Number of tools cleaned up
        """
        if not self.tool_expiry_hours:
            return 0
        
        current_time = time.time()
        expiry_threshold = current_time - (self.tool_expiry_hours * 3600)
        
        expired_tools = []
        for tool_name, metadata in self.tool_metadata.items():
            if metadata["created_at"] < expiry_threshold:
                expired_tools.append(tool_name)
        
        # Remove expired tools
        for tool_name in expired_tools:
            del self.dynamic_tools[tool_name]
            del self.tool_metadata[tool_name]
            self._stats["tools_expired"] += 1
        
        if expired_tools:
            logger.info(f"Cleaned up {len(expired_tools)} expired dynamic tools")
        
        return len(expired_tools)
    
    def _evict_least_used_tools(self, slots_needed: int) -> int:
        """
        Evict least recently used tools to make room for new ones.
        
        Args:
            slots_needed: Number of slots needed for new tools
        
        Returns:
            Number of tools evicted
        """
        if not self.tool_metadata:
            return 0
        
        # Sort tools by usage (least used first)
        sorted_tools = sorted(
            self.tool_metadata.items(),
            key=lambda x: (x[1]["usage_count"], x[1]["last_used"])
        )
        
        evicted_count = 0
        for tool_name, _ in sorted_tools:
            if evicted_count >= slots_needed:
                break
            
            # Remove the tool
            del self.dynamic_tools[tool_name]
            del self.tool_metadata[tool_name]
            evicted_count += 1
            self._stats["tools_evicted"] += 1
        
        if evicted_count > 0:
            logger.info(f"Evicted {evicted_count} least used dynamic tools")
        
        return evicted_count
    
    def cleanup_expired_tools(self) -> int:
        """
        Public method to clean up expired tools.
        
        Returns:
            Number of tools cleaned up
        """
        with self.tool_lock:
            return self._cleanup_expired_tools()
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """
        Get statistics about dynamic tools.
        
        Returns:
            Dictionary with tool statistics
        """
        with self.tool_lock:
            stats = self._stats.copy()
            
            # Add current state info
            stats.update({
                "active_tools": len(self.dynamic_tools),
                "max_tools": self.max_dynamic_tools,
                "tool_utilization": len(self.dynamic_tools) / max(1, self.max_dynamic_tools),
            })
            
            # Tool usage distribution
            if self.tool_metadata:
                usage_counts = [meta["usage_count"] for meta in self.tool_metadata.values()]
                stats["usage_distribution"] = {
                    "min_usage": min(usage_counts),
                    "max_usage": max(usage_counts),
                    "avg_usage": sum(usage_counts) / len(usage_counts),
                    "total_usage": sum(usage_counts)
                }
            
            return stats
    
    def list_active_tools(self) -> List[Dict[str, Any]]:
        """
        List all currently active dynamic tools with their metadata.
        
        Returns:
            List of tool information dictionaries
        """
        with self.tool_lock:
            tools_info = []
            current_time = time.time()
            
            for tool_name, metadata in self.tool_metadata.items():
                age_hours = (current_time - metadata["created_at"]) / 3600
                last_used_hours = (current_time - metadata["last_used"]) / 3600
                
                tools_info.append({
                    "tool_name": tool_name,
                    "reference_id": metadata["reference_id"],
                    "data_type": metadata["data_type"],
                    "usage_count": metadata["usage_count"],
                    "age_hours": round(age_hours, 2),
                    "last_used_hours": round(last_used_hours, 2),
                    "created_at": datetime.fromtimestamp(metadata["created_at"]).isoformat()
                })
            
            # Sort by usage count (most used first)
            tools_info.sort(key=lambda x: x["usage_count"], reverse=True)
            return tools_info
    
    def force_cleanup(self, keep_recent_hours: int = 1) -> Dict[str, int]:
        """
        Force cleanup of dynamic tools, keeping only recently used ones.
        
        Args:
            keep_recent_hours: Keep tools used within this many hours
        
        Returns:
            Dictionary with cleanup statistics
        """
        with self.tool_lock:
            current_time = time.time()
            recent_threshold = current_time - (keep_recent_hours * 3600)
            
            tools_to_remove = []
            for tool_name, metadata in self.tool_metadata.items():
                if metadata["last_used"] < recent_threshold:
                    tools_to_remove.append(tool_name)
            
            # Remove old tools
            for tool_name in tools_to_remove:
                del self.dynamic_tools[tool_name]
                del self.tool_metadata[tool_name]
            
            cleanup_stats = {
                "tools_removed": len(tools_to_remove),
                "tools_remaining": len(self.dynamic_tools),
                "memory_freed_estimate": len(tools_to_remove) * 1024,  # Rough estimate
            }
            
            logger.info(f"Force cleanup removed {len(tools_to_remove)} tools, {len(self.dynamic_tools)} remaining")
            return cleanup_stats
    
    def cleanup_expired_tools(self, max_age_hours: int = 24):
        """Clean up expired dynamic tools"""
        # This could be enhanced to track tool creation times and clean up old ones
        pass
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about dynamic tools"""
        return {
            "total_dynamic_tools": len(self.dynamic_tools),
            "active_tools": list(self.dynamic_tools.keys()),
            "storage_stats": self.storage.get_storage_stats() if self.storage else None
        }

# Example usage and testing
if __name__ == "__main__":
    from large_data_storage import LargeDataStorage
    
    # Initialize storage and wrapper
    storage = LargeDataStorage()
    wrapper = SmartToolWrapper(storage, token_threshold=1000)  # Low threshold for testing
    
    # Test with small data
    small_data = {"test": "small data"}
    result = wrapper.wrap_tool_result(small_data, "test_tool")
    print(f"Small data test: {type(result)}")
    
    # Test with large data
    large_data = {"records": [{"id": i, "data": "x" * 100} for i in range(100)]}
    result = wrapper.wrap_tool_result(large_data, "large_test_tool")
    print(f"Large data test: {type(result)}")
    
    if isinstance(result, dict) and result.get("type") == "large_data_reference":
        print(f"Reference ID: {result['reference_id']}")
        print(f"Summary: {result['summary']}")
        print(f"Dynamic tools: {result['dynamic_tools']}")
        
        # Test dynamic tool
        tool_name = result['dynamic_tools'][0]
        tool_func = wrapper.get_dynamic_tool_function(tool_name)
        if tool_func:
            tool_result = tool_func()
            print(f"Dynamic tool result: {tool_result}")