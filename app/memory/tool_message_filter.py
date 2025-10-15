"""
Tool Message Filter for LangGraph

Automatically filters large base64 content from ToolMessages before they're added
to LangGraph message history, preventing token bloat in vision workflows.

This filter is critical for multimodal agents that use vision models with base64-encoded
images. Without filtering, each base64 string (50K+ tokens) would be repeated in message
history for every subsequent LLM call, quickly exceeding context limits.
"""

import json
import logging
from typing import Dict, Any, List, Union
from langchain_core.messages import ToolMessage, BaseMessage
from langgraph.graph import StateGraph

log = logging.getLogger(__name__)


def filter_tool_message_content(content: str, tool_name: str = "unknown") -> str:
    """
    Filter out large base64 content from tool message content.
    
    This prevents token bloat when vision agents use get_image_base64() tool.
    The base64 content is used for vision processing during tool execution,
    but should NOT be preserved in LangGraph message history.
    
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
                    f"Filtered base64 content from '{tool_name}' tool result: "
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
                            f"Filtered large content from '{tool_name}' tool result: "
                            f"removed {content_len} chars (~{estimated_tokens:,} tokens) from '{key}' field"
                        )
                        
                        return json.dumps(filtered_data, indent=2)
    
    except (json.JSONDecodeError, Exception) as e:
        # If not valid JSON or any error, check for inline base64 patterns
        if len(content) > 10000:
            log.debug(f"Large non-JSON content in '{tool_name}': {len(content)} chars, checking for base64 patterns")
    
    return content


def filter_messages(messages: Union[List[BaseMessage], BaseMessage]) -> List[BaseMessage]:
    """
    Filter messages to remove large base64 content from ToolMessages.
    
    This function should be called before messages are added to LangGraph state.
    
    Args:
        messages: Single message or list of messages to filter
        
    Returns:
        Filtered list of messages
    """
    if isinstance(messages, BaseMessage):
        messages = [messages]
    
    filtered_messages = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            # Filter tool message content
            original_content = msg.content
            filtered_content = filter_tool_message_content(original_content, msg.name)
            
            if filtered_content != original_content:
                # Create new ToolMessage with filtered content
                filtered_msg = ToolMessage(
                    content=filtered_content,
                    name=msg.name,
                    tool_call_id=msg.tool_call_id,
                    additional_kwargs=msg.additional_kwargs
                )
                filtered_messages.append(filtered_msg)
            else:
                filtered_messages.append(msg)
        else:
            filtered_messages.append(msg)
    
    return filtered_messages


def create_message_filter_reducer():
    """
    Create a custom message reducer that filters base64 content from ToolMessages.
    
    This reducer wraps the standard add_messages reducer and applies filtering.
    
    Usage in StateGraph:
        from langgraph.graph.message import add_messages
        from app.memory.tool_message_filter import create_message_filter_reducer
        
        filter_reducer = create_message_filter_reducer()
        
        class State(TypedDict):
            messages: Annotated[List[BaseMessage], filter_reducer]
    """
    from langgraph.graph.message import add_messages
    
    def filtered_add_messages(left: List[BaseMessage], right: Union[List[BaseMessage], BaseMessage]) -> List[BaseMessage]:
        """Add messages with automatic base64 filtering"""
        # Filter incoming messages
        filtered_right = filter_messages(right)
        
        # Apply standard add_messages logic
        return add_messages(left, filtered_right)
    
    return filtered_add_messages


# Convenience function to patch existing agents
def patch_agent_with_message_filter(agent):
    """
    Patch an existing LangGraph agent to filter ToolMessages.
    
    This modifies the agent's graph to apply message filtering.
    
    Args:
        agent: A compiled LangGraph agent
        
    Returns:
        The patched agent (modifies in-place)
    """
    try:
        # Access the agent's internal graph structure
        if hasattr(agent, '_graph') or hasattr(agent, 'graph'):
            graph = getattr(agent, '_graph', None) or getattr(agent, 'graph', None)
            
            if graph and hasattr(graph, 'nodes'):
                # Intercept the tools node
                for node_name in graph.nodes:
                    if 'tool' in node_name.lower():
                        original_node = graph.nodes[node_name]
                        
                        # Wrap the original node function
                        def filtered_node_wrapper(state):
                            # Execute original tool node
                            result = original_node(state)
                            
                            # Filter messages in the result
                            if isinstance(result, dict) and 'messages' in result:
                                result['messages'] = filter_messages(result['messages'])
                            
                            return result
                        
                        graph.nodes[node_name] = filtered_node_wrapper
                        log.info(f"Patched agent node '{node_name}' with message filter")
                        return agent
        
        log.warning("Could not patch agent - graph structure not accessible")
        return agent
        
    except Exception as e:
        log.error(f"Failed to patch agent with message filter: {e}")
        return agent