"""
Smart Tool Response Wrapper for JK Agents Framework

Automatically detects large tool responses and creates efficient references
instead of sending massive data to LLMs. Includes intelligent summarization
and dynamic tool generation for data access.
"""

import json
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from langchain_core.tools import tool
from dataclasses import dataclass

from .large_data_storage import LargeDataStorage, DataSize

log = logging.getLogger(__name__)

@dataclass
class DataReference:
    """Reference to stored large data with intelligent summary"""
    reference_id: str
    summary: str
    size_category: DataSize
    token_count: int
    tools_available: List[str]
    metadata: Dict[str, Any]

class SmartToolWrapper:
    """Intelligently wraps tool calls to handle large data efficiently"""
    
    def __init__(self, storage: LargeDataStorage, token_threshold: int = 1000):
        self.storage = storage
        self.token_threshold = token_threshold
        self.references: Dict[str, DataReference] = {}
        self.dynamic_tools: Dict[str, Callable] = {}
        
        log.info(f"Smart tool wrapper initialized with {token_threshold} token threshold")
    
    def wrap_tool_response(self, tool_name: str, tool_result: Any, 
                          metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Intelligently wrap tool responses based on size"""
        
        # Estimate token count
        serialized = json.dumps(tool_result, default=str)
        token_count = self._estimate_tokens(serialized)
        
        log.debug(f"Tool '{tool_name}' returned {token_count} tokens")
        
        if token_count <= self.token_threshold:
            # Small data - return directly
            return {
                "type": "direct",
                "data": tool_result,
                "token_count": token_count,
                "message": f"✅ Direct response ({token_count} tokens)"
            }
        
        # Large data - create reference
        reference_id = self._generate_reference_id(tool_name)
        summary = self._create_intelligent_summary(tool_result, tool_name)
        
        # Store the full data
        storage_info = self.storage.store_large_data(
            reference_id=reference_id,
            tool_name=tool_name,
            data=tool_result,
            metadata=metadata
        )
        
        # Generate dynamic tools for data access
        dynamic_tools = self._generate_dynamic_tools(reference_id, tool_name, tool_result)
        tool_names = [tool.__name__ for tool in dynamic_tools]
        
        # Create and store reference
        reference = DataReference(
            reference_id=reference_id,
            summary=summary,
            size_category=storage_info.size_category,
            token_count=token_count,
            tools_available=tool_names,
            metadata={
                **(metadata or {}),
                "tool_name": tool_name,
                "storage_info": storage_info.__dict__
            }
        )
        
        self.references[reference_id] = reference
        
        # Register dynamic tools
        for tool_func in dynamic_tools:
            self.dynamic_tools[tool_func.__name__] = tool_func
        
        # Calculate cost savings
        cost_saved = self._calculate_cost_savings(token_count)
        
        return {
            "type": "reference",
            "reference_id": reference_id,
            "summary": summary,
            "size_info": {
                "category": storage_info.size_category.value,
                "size_mb": storage_info.size_mb,
                "token_count": token_count,
                "storage_type": storage_info.storage_type
            },
            "tools_available": tool_names,
            "optimization": {
                "tokens_saved": token_count - 200,  # Approximate reference size
                "estimated_cost_saved": cost_saved,
                "compression_ratio": f"{storage_info.size_mb:.1f}MB → 200 tokens"
            },
            "message": f"🚀 Large data optimized: {storage_info.size_mb:.1f}MB stored, ~${cost_saved:.3f} saved"
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple heuristic"""
        # Rough estimation: 1 token ≈ 4 characters for most models
        return len(text) // 4
    
    def _generate_reference_id(self, tool_name: str) -> str:
        """Generate unique reference ID"""
        timestamp = int(time.time() * 1000)
        hash_input = f"{tool_name}_{timestamp}_{id(self)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _create_intelligent_summary(self, data: Any, tool_name: str) -> str:
        """Create context-aware summaries based on data type and tool"""
        
        try:
            if isinstance(data, list):
                return self._summarize_list_data(data, tool_name)
            elif isinstance(data, dict):
                return self._summarize_dict_data(data, tool_name)
            else:
                return self._summarize_text_data(str(data), tool_name)
        except Exception as e:
            log.warning(f"Error creating summary: {e}")
            return f"{tool_name} returned large dataset (summary generation failed)"
    
    def _summarize_list_data(self, data: list, tool_name: str) -> str:
        """Summarize list/array data intelligently"""
        count = len(data)
        
        if count == 0:
            return f"{tool_name} returned empty dataset"
        
        # Sample first few items to understand structure
        sample_size = min(3, count)
        sample_items = data[:sample_size]
        
        if all(isinstance(item, dict) for item in sample_items):
            # Database/API records
            all_keys = set()
            for item in sample_items:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            key_list = sorted(list(all_keys))[:8]  # Show max 8 keys
            keys_display = ', '.join(key_list)
            if len(all_keys) > 8:
                keys_display += f" ... (+{len(all_keys) - 8} more)"
            
            # Show sample record
            sample_record = json.dumps(sample_items[0], default=str)[:150]
            if len(sample_record) >= 150:
                sample_record += "..."
            
            return f"{tool_name} returned {count:,} records with fields: {keys_display}. Sample: {sample_record}"
        
        elif all(isinstance(item, str) for item in sample_items):
            # Text data
            avg_length = sum(len(item) for item in sample_items) / len(sample_items)
            samples_preview = ', '.join([f'"{item[:30]}..."' if len(item) > 30 else f'"{item}"' 
                                       for item in sample_items[:2]])
            return f"{tool_name} returned {count:,} text items (avg {avg_length:.0f} chars). Samples: {samples_preview}"
        
        elif all(isinstance(item, (int, float)) for item in sample_items):
            # Numeric data
            min_val = min(sample_items)
            max_val = max(sample_items)
            return f"{tool_name} returned {count:,} numeric values (range: {min_val} to {max_val})"
        
        else:
            # Mixed types
            type_counts = {}
            for item in data[:100]:  # Sample first 100 items
                item_type = type(item).__name__
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            type_summary = ', '.join([f"{k}({v})" for k, v in sorted(type_counts.items())])
            return f"{tool_name} returned {count:,} items of mixed types: {type_summary}"
    
    def _summarize_dict_data(self, data: dict, tool_name: str) -> str:
        """Summarize dictionary/object data"""
        keys = list(data.keys())
        key_count = len(keys)
        
        # Show first few keys
        display_keys = keys[:8]
        if key_count > 8:
            key_display = ', '.join(display_keys) + f" ... (+{key_count - 8} more)"
        else:
            key_display = ', '.join(display_keys)
        
        # Analyze data structure
        summary_parts = [f"{tool_name} returned structured data with {key_count} fields"]
        summary_parts.append(f"Fields: {key_display}")
        
        # Sample a few key-value pairs for context
        sample_pairs = []
        for key in display_keys[:3]:
            value = data[key]
            if isinstance(value, (list, dict)):
                sample_pairs.append(f"{key}: {type(value).__name__}({len(value) if hasattr(value, '__len__') else '?'})")
            else:
                value_str = str(value)[:50]
                if len(str(value)) > 50:
                    value_str += "..."
                sample_pairs.append(f"{key}: {value_str}")
        
        if sample_pairs:
            summary_parts.append(f"Sample: {'; '.join(sample_pairs)}")
        
        return ". ".join(summary_parts)
    
    def _summarize_text_data(self, data: str, tool_name: str) -> str:
        """Summarize large text data"""
        char_count = len(data)
        word_count = len(data.split())
        lines = data.split('\n')
        line_count = len(lines)
        
        # Show preview
        preview = data[:200]
        if len(data) > 200:
            preview += "..."
        
        return f"{tool_name} returned large text: {char_count:,} chars, {word_count:,} words, {line_count} lines. Preview: {preview}"
    
    def _generate_dynamic_tools(self, reference_id: str, tool_name: str, data: Any) -> List[Callable]:
        """Generate specific tools to access the referenced data"""
        
        tools = []
        
        # 1. Get data subset tool
        def get_subset(subset_filter: str = "first_10") -> str:
            f"""Get a subset of data from {tool_name} result (Reference: {reference_id}).
            
            Args:
                subset_filter: Filter to apply - 'first_N', 'last_N', 'random_N', 'contains:term', 'range:start-end'
            """
            full_data = self.storage.retrieve_large_data(reference_id)
            if not full_data:
                return "❌ Data not found or expired"
            
            try:
                result = self._apply_filter(full_data, subset_filter)
                return f"✅ Filtered data ({subset_filter}):\n{json.dumps(result, indent=2, default=str)[:2000]}"
            except Exception as e:
                return f"❌ Filter error: {e}"
        
        # 2. Search within data tool  
        def search_data(query: str, max_results: int = 10) -> str:
            f"""Search within the data from {tool_name} (Reference: {reference_id}).
            
            Args:
                query: Search term or JSON path
                max_results: Maximum results to return
            """
            full_data = self.storage.retrieve_large_data(reference_id)
            if not full_data:
                return "❌ Data not found or expired"
            
            try:
                results = self._search_within_data(full_data, query, max_results)
                return f"🔍 Search results for '{query}':\n{json.dumps(results, indent=2, default=str)[:2000]}"
            except Exception as e:
                return f"❌ Search error: {e}"
        
        # 3. Get statistics tool
        def get_stats() -> str:
            f"""Get statistical summary of {tool_name} data (Reference: {reference_id})"""
            full_data = self.storage.retrieve_large_data(reference_id)
            if not full_data:
                return "❌ Data not found or expired"
            
            try:
                stats = self._generate_statistics(full_data)
                return f"📊 Data Statistics:\n{stats}"
            except Exception as e:
                return f"❌ Stats error: {e}"
        
        # Set unique names and convert to LangChain tools
        get_subset.__name__ = f"get_subset_{reference_id}"
        search_data.__name__ = f"search_data_{reference_id}"  
        get_stats.__name__ = f"get_stats_{reference_id}"
        
        # Convert to proper tools
        tools.extend([
            tool(get_subset),
            tool(search_data), 
            tool(get_stats)
        ])
        
        return tools
    
    def _apply_filter(self, data: Any, filter_expr: str) -> Any:
        """Apply filtering to data based on filter expression"""
        
        if filter_expr.startswith("first_"):
            n = int(filter_expr.split("_")[1])
            if isinstance(data, list):
                return data[:n]
            elif isinstance(data, dict):
                items = list(data.items())[:n]
                return dict(items)
        
        elif filter_expr.startswith("last_"):
            n = int(filter_expr.split("_")[1])
            if isinstance(data, list):
                return data[-n:]
            elif isinstance(data, dict):
                items = list(data.items())[-n:]
                return dict(items)
        
        elif filter_expr.startswith("random_"):
            import random
            n = int(filter_expr.split("_")[1])
            if isinstance(data, list):
                return random.sample(data, min(n, len(data)))
            elif isinstance(data, dict):
                keys = random.sample(list(data.keys()), min(n, len(data)))
                return {k: data[k] for k in keys}
        
        elif filter_expr.startswith("contains:"):
            search_term = filter_expr.split(":", 1)[1].lower()
            if isinstance(data, list):
                return [item for item in data 
                       if search_term in str(item).lower()]
            elif isinstance(data, dict):
                return {k: v for k, v in data.items() 
                       if search_term in str(k).lower() or search_term in str(v).lower()}
        
        elif filter_expr.startswith("range:"):
            range_part = filter_expr.split(":", 1)[1]
            start, end = map(int, range_part.split("-"))
            if isinstance(data, list):
                return data[start:end]
        
        return data
    
    def _search_within_data(self, data: Any, query: str, max_results: int) -> Any:
        """Search within data structure"""
        
        query_lower = query.lower()
        results = []
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                if len(results) >= max_results:
                    break
                    
                if query_lower in str(item).lower():
                    results.append({"index": i, "data": item})
        
        elif isinstance(data, dict):
            for key, value in data.items():
                if len(results) >= max_results:
                    break
                    
                if (query_lower in key.lower() or 
                    query_lower in str(value).lower()):
                    results.append({"key": key, "value": value})
        
        return results[:max_results]
    
    def _generate_statistics(self, data: Any) -> str:
        """Generate statistical summary of data"""
        
        stats = []
        
        if isinstance(data, list):
            stats.append(f"Type: List/Array")
            stats.append(f"Count: {len(data):,} items")
            
            if data:
                # Analyze item types
                types = {}
                for item in data[:1000]:  # Sample first 1000
                    item_type = type(item).__name__
                    types[item_type] = types.get(item_type, 0) + 1
                
                stats.append(f"Item types: {dict(types)}")
                
                # Numeric analysis if applicable
                if all(isinstance(item, (int, float)) for item in data[:100]):
                    numeric_data = [x for x in data if isinstance(x, (int, float))][:1000]
                    if numeric_data:
                        stats.append(f"Numeric range: {min(numeric_data)} to {max(numeric_data)}")
                        stats.append(f"Average: {sum(numeric_data) / len(numeric_data):.2f}")
        
        elif isinstance(data, dict):
            stats.append(f"Type: Object/Dictionary")
            stats.append(f"Keys: {len(data):,}")
            
            if data:
                # Analyze value types
                value_types = {}
                for value in list(data.values())[:1000]:
                    value_type = type(value).__name__
                    value_types[value_type] = value_types.get(value_type, 0) + 1
                
                stats.append(f"Value types: {dict(value_types)}")
                
                # Sample keys
                sample_keys = list(data.keys())[:10]
                if len(data) > 10:
                    stats.append(f"Sample keys: {sample_keys} ... (+{len(data) - 10} more)")
                else:
                    stats.append(f"Keys: {sample_keys}")
        
        else:
            stats.append(f"Type: {type(data).__name__}")
            stats.append(f"Size: {len(str(data)):,} characters")
        
        return "\n".join(stats)
    
    def _calculate_cost_savings(self, token_count: int) -> float:
        """Calculate estimated cost savings based on token count"""
        # Rough estimates for different models (per 1K tokens)
        # GPT-4: ~$0.03 input, GPT-3.5: ~$0.002 input
        cost_per_1k_tokens = 0.015  # Average estimate
        return (token_count / 1000) * cost_per_1k_tokens
    
    def get_dynamic_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a dynamically generated tool by name"""
        return self.dynamic_tools.get(tool_name)
    
    def get_all_dynamic_tools(self) -> Dict[str, Callable]:
        """Get all dynamically generated tools"""
        return self.dynamic_tools.copy()
    
    def cleanup_reference(self, reference_id: str) -> bool:
        """Clean up a specific reference and its tools"""
        try:
            # Remove from references
            if reference_id in self.references:
                reference = self.references[reference_id]
                
                # Remove associated dynamic tools
                for tool_name in reference.tools_available:
                    self.dynamic_tools.pop(tool_name, None)
                
                del self.references[reference_id]
                return True
        except Exception as e:
            log.error(f"Error cleaning up reference {reference_id}: {e}")
        
        return False