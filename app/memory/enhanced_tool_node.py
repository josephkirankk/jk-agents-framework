"""
Enhanced Tool Node for JK Agents Framework

Integrates with SmartToolWrapper to automatically handle large tool responses
in React agents. Dynamically adds tools to agent context when references are created.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import ToolMessage, AIMessage, BaseMessage
from langchain_core.tools import BaseTool

from .smart_tool_wrapper import SmartToolWrapper
from .large_data_storage import LargeDataStorage

log = logging.getLogger(__name__)

class EnhancedToolNode:
    """Enhanced tool node that handles large data intelligently"""
    
    def __init__(self, tools: List[BaseTool], config: Optional[Dict[str, Any]] = None):
        self.original_tools = tools
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.config = config or {}
        
        # Initialize large data handling - check if enabled in parent config
        self.large_data_enabled = self.config.get("enabled", False)
        
        if self.large_data_enabled:
            # Get nested large_data config
            storage_config = self.config.get("large_data", {})
            token_threshold = self.config.get("token_threshold", 1000)
            
            self.data_storage = LargeDataStorage(storage_config)
            self.smart_wrapper = SmartToolWrapper(self.data_storage, token_threshold)
            log.info(f"Enhanced tool node initialized with large data handling (threshold: {token_threshold})")
        else:
            self.data_storage = None
            self.smart_wrapper = None
            log.info("Enhanced tool node initialized without large data handling")
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, List[BaseMessage]]:
        """Execute tools with intelligent large data handling"""
        
        outputs = []
        last_message = state["messages"][-1]
        
        # Track dynamic tools added in this execution
        new_dynamic_tools = []
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            
            # Check if this is a dynamic tool (from previous large data references)
            if self.smart_wrapper and tool_name in self.smart_wrapper.dynamic_tools:
                # Execute dynamic tool
                dynamic_tool = self.smart_wrapper.dynamic_tools[tool_name]
                try:
                    result = dynamic_tool.invoke(tool_args)
                    response_content = str(result)
                    log.debug(f"Executed dynamic tool '{tool_name}': {len(response_content)} chars")
                except Exception as e:
                    response_content = f"❌ Dynamic tool error: {e}"
                    log.error(f"Dynamic tool '{tool_name}' failed: {e}")
            
            elif tool_name in self.tools_by_name:
                # Execute original tool
                tool = self.tools_by_name[tool_name]
                
                try:
                    # Execute the tool
                    tool_result = tool.invoke(tool_args)
                    log.debug(f"Tool '{tool_name}' executed successfully")
                    
                    # Handle large data if enabled
                    if self.large_data_enabled and self.smart_wrapper:
                        wrapped_result = self.smart_wrapper.wrap_tool_response(
                            tool_name=tool_name,
                            tool_result=tool_result,
                            metadata={
                                "step_count": state.get("step_count", 0),
                                "agent_name": state.get("agent_name", "unknown"),
                                "execution_time": state.get("execution_time")
                            }
                        )
                        
                        if wrapped_result["type"] == "reference":
                            # Large data - create optimized response
                            response_content = self._create_reference_response(wrapped_result)
                            
                            # Register new dynamic tools for future use
                            new_tools = wrapped_result.get("tools_available", [])
                            new_dynamic_tools.extend(new_tools)
                            
                            log.info(f"Created reference {wrapped_result['reference_id']} for {tool_name}, "
                                   f"saved {wrapped_result['optimization']['tokens_saved']} tokens")
                        else:
                            # Small data - return directly
                            response_content = json.dumps(tool_result, default=str, indent=2)
                            log.debug(f"Tool '{tool_name}' returned small data directly")
                    else:
                        # No large data handling - return directly
                        response_content = json.dumps(tool_result, default=str, indent=2)
                        
                except Exception as e:
                    response_content = f"❌ Tool execution failed: {str(e)}"
                    log.error(f"Tool '{tool_name}' execution failed: {e}")
            
            else:
                response_content = f"❌ Tool '{tool_name}' not found"
                log.error(f"Tool '{tool_name}' not found in available tools")
            
            # Filter out base64 content from tool messages to prevent token bloat
            filtered_content = self._filter_large_content(response_content, tool_name)
            
            # Create tool message with filtered content
            outputs.append(
                ToolMessage(
                    content=filtered_content,
                    name=tool_name,
                    tool_call_id=tool_call_id
                )
            )
        
        # Add information about new dynamic tools if any were created
        if new_dynamic_tools:
            info_message = self._create_dynamic_tools_info(new_dynamic_tools)
            outputs.append(
                ToolMessage(
                    content=info_message,
                    name="system_info",
                    tool_call_id="dynamic_tools_info"
                )
            )
        
        return {"messages": outputs}
    
    def _create_reference_response(self, wrapped_result: Dict[str, Any]) -> str:
        """Create a comprehensive response for referenced data"""
        
        ref_id = wrapped_result["reference_id"]
        summary = wrapped_result["summary"]
        size_info = wrapped_result["size_info"]
        tools = wrapped_result["tools_available"]
        optimization = wrapped_result["optimization"]
        
        response_parts = [
            f"✅ **Large Data Reference Created**",
            f"",
            f"**Reference ID**: `{ref_id}`",
            f"**Summary**: {summary}",
            f"",
            f"**Size Information**:",
            f"• Category: {size_info['category'].upper()}",
            f"• Size: {size_info['size_mb']:.2f} MB ({size_info['token_count']:,} tokens)",
            f"• Storage: {size_info['storage_type']}",
            f"",
            f"**Optimization Results**:",
            f"• Tokens saved: {optimization['tokens_saved']:,}",
            f"• Cost saved: ~${optimization['estimated_cost_saved']:.4f}",
            f"• Compression: {optimization['compression_ratio']}",
            f"",
            f"**Available Data Access Tools**:",
        ]
        
        for i, tool_name in enumerate(tools, 1):
            tool_description = self._get_tool_description(tool_name)
            response_parts.append(f"{i}. `{tool_name}` - {tool_description}")
        
        response_parts.extend([
            f"",
            f"💡 **Next Steps**: Use the above tools to access specific parts of the data as needed for your analysis.",
            f"The large dataset has been efficiently stored and is ready for targeted queries."
        ])
        
        return "\n".join(response_parts)
    
    def _get_tool_description(self, tool_name: str) -> str:
        """Get human-readable description for dynamic tools"""
        if "get_subset" in tool_name:
            return "Get filtered subsets of the data (first_N, last_N, contains:term, etc.)"
        elif "search_data" in tool_name:
            return "Search within the data using text queries"
        elif "get_stats" in tool_name:
            return "Get statistical summary and analysis of the data"
        else:
            return "Access the referenced data"
    
    def _create_dynamic_tools_info(self, new_tools: List[str]) -> str:
        """Create informational message about new dynamic tools"""
        
        if len(new_tools) == 0:
            return ""
        
        info_parts = [
            f"🔧 **Dynamic Tools Added**: {len(new_tools)} new data access tools are now available:",
            f""
        ]
        
        for tool_name in new_tools:
            description = self._get_tool_description(tool_name)
            info_parts.append(f"• `{tool_name}` - {description}")
        
        info_parts.extend([
            f"",
            f"These tools will remain available throughout this conversation for accessing the referenced data."
        ])
        
        return "\n".join(info_parts)
    
    def get_all_available_tools(self) -> List[BaseTool]:
        """Get all available tools including dynamic ones"""
        all_tools = self.original_tools.copy()
        
        if self.smart_wrapper:
            # Add dynamic tools
            for tool_name, tool_func in self.smart_wrapper.dynamic_tools.items():
                # Convert function to BaseTool if needed
                if hasattr(tool_func, 'name') and hasattr(tool_func, 'invoke'):
                    all_tools.append(tool_func)
        
        return all_tools
    
    def get_available_tool_names(self) -> List[str]:
        """Get names of all available tools"""
        names = list(self.tools_by_name.keys())
        
        if self.smart_wrapper:
            names.extend(self.smart_wrapper.dynamic_tools.keys())
        
        return names
    
    def cleanup_expired_references(self) -> Dict[str, Any]:
        """Clean up expired data references"""
        if not self.data_storage:
            return {"message": "Large data handling disabled"}
        
        try:
            cleanup_stats = self.data_storage.cleanup_expired_data()
            
            # Also clean up references from smart wrapper
            if self.smart_wrapper:
                # Get expired reference IDs (this would need to be implemented)
                # For now, we'll just return the storage cleanup stats
                pass
            
            return {
                "cleaned_records": cleanup_stats.get("cleaned_records", 0),
                "cleaned_files": cleanup_stats.get("cleaned_files", 0),
                "message": f"Cleaned up {cleanup_stats.get('cleaned_records', 0)} expired references"
            }
        
        except Exception as e:
            log.error(f"Error during cleanup: {e}")
            return {"error": str(e)}
    
    def _filter_large_content(self, content: str, tool_name: str) -> str:
        """
        Filter out large base64 content from tool results to prevent token bloat in message history.
        
        This is critical for vision workflows where base64 images can be 50K+ tokens each.
        The base64 content is used by the LLM during tool execution, but should NOT
        be preserved in message history.
        
        Args:
            content: The tool result content (possibly containing base64)
            tool_name: Name of the tool that produced this content
            
        Returns:
            Filtered content with base64 data replaced by metadata
        """
        # Check if this is a JSON response that might contain base64
        try:
            if content.startswith('{') or content.startswith('['):
                data = json.loads(content)
                
                # Check for base64_content field (from get_image_base64 tool)
                if isinstance(data, dict) and 'base64_content' in data:
                    base64_len = len(data.get('base64_content', ''))
                    estimated_tokens = base64_len // 3  # Rough estimate: 3 chars per token
                    
                    # Remove base64 content and replace with metadata
                    filtered_data = data.copy()
                    filtered_data['base64_content'] = f"[BASE64_REMOVED: {base64_len} chars, ~{estimated_tokens:,} tokens]"
                    filtered_data['_note'] = "Base64 content was used for vision processing and removed from history to save tokens"
                    
                    log.info(
                        f"Filtered base64 content from {tool_name} tool result: "
                        f"removed {base64_len} chars (~{estimated_tokens:,} tokens)"
                    )
                    
                    return json.dumps(filtered_data, indent=2)
                
                # Check for other large content fields that might need filtering
                if isinstance(data, dict):
                    for key in ['content', 'data', 'body']:
                        if key in data and isinstance(data[key], str) and len(data[key]) > 10000:
                            content_len = len(data[key])
                            estimated_tokens = content_len // 4
                            
                            filtered_data = data.copy()
                            filtered_data[key] = f"[LARGE_CONTENT_REMOVED: {content_len} chars, ~{estimated_tokens:,} tokens]"
                            filtered_data['_note'] = "Large content was removed from history to save tokens"
                            
                            log.info(
                                f"Filtered large content from {tool_name} tool result: "
                                f"removed {content_len} chars (~{estimated_tokens:,} tokens) from '{key}' field"
                            )
                            
                            return json.dumps(filtered_data, indent=2)
        
        except (json.JSONDecodeError, Exception) as e:
            # If not valid JSON or any error, check for inline base64 patterns
            if len(content) > 10000:
                log.debug(f"Large non-JSON content in {tool_name}: {len(content)} chars, checking for base64 patterns")
        
        return content
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics"""
        if not self.data_storage:
            return {"message": "Large data handling disabled"}
        
        try:
            storage_stats = self.data_storage.get_storage_stats()
            
            # Add wrapper stats
            if self.smart_wrapper:
                wrapper_stats = {
                    "active_references": len(self.smart_wrapper.references),
                    "dynamic_tools": len(self.smart_wrapper.dynamic_tools),
                    "references": {
                        ref_id: {
                            "summary": ref.summary[:100] + "..." if len(ref.summary) > 100 else ref.summary,
                            "size_category": ref.size_category.value,
                            "token_count": ref.token_count,
                            "tools_count": len(ref.tools_available)
                        }
                        for ref_id, ref in list(self.smart_wrapper.references.items())[:10]  # Show first 10
                    }
                }
                storage_stats["smart_wrapper"] = wrapper_stats
            
            return storage_stats
        
        except Exception as e:
            log.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}
