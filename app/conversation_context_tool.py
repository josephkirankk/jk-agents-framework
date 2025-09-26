"""
Conversation Context Search Tool

This tool provides agents with the ability to search for relevant context 
from previous conversations using the same thread_id.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

log = logging.getLogger(__name__)


def search_conversation_context(
    thread_id: str,
    query: str,
    checkpointer,
    max_messages: int = 20
) -> List[Dict[str, Any]]:
    """
    Search for relevant context from previous conversation messages.
    
    Args:
        thread_id: The thread ID to search in
        query: Search query (e.g., "user stories", "bug count", "these items")
        checkpointer: The checkpointer instance
        max_messages: Maximum number of recent messages to search through
        
    Returns:
        List of relevant message contexts
    """
    try:
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        
        # Get checkpoint data
        if hasattr(checkpointer, 'get_tuple'):
            checkpoint_tuple = checkpointer.get_tuple(config)
            if not checkpoint_tuple:
                return []
                
            # Extract messages from checkpoint
            checkpoint_data = checkpoint_tuple[1] if isinstance(checkpoint_tuple, tuple) else checkpoint_tuple.checkpoint
            if not checkpoint_data or 'channel_values' not in checkpoint_data:
                return []
                
            messages = checkpoint_data.get('channel_values', {}).get('messages', [])
            if not messages:
                return []
            
            # Get recent messages
            recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
            
            # Simple keyword matching for context relevance
            relevant_messages = []
            query_lower = query.lower()
            
            for i, msg in enumerate(recent_messages):
                content = ""
                msg_type = "unknown"
                
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    msg_type = msg.type
                    content = str(msg.content)
                elif isinstance(msg, dict):
                    msg_type = msg.get('role', msg.get('type', 'unknown'))
                    content = str(msg.get('content', ''))
                
                content_lower = content.lower()
                
                # Check for relevance
                is_relevant = False
                
                # Direct keyword matching
                if any(keyword in content_lower for keyword in ['user stor', 'work item', 'bug', 'task', 'id:', '#']):
                    is_relevant = True
                
                # Context keywords from query
                if 'these' in query_lower or 'them' in query_lower or 'those' in query_lower:
                    # Look for lists, IDs, or specific items in previous messages
                    if any(indicator in content_lower for indicator in ['id:', 'title:', '1.', '2.', '3.', '4.', '5.', 'list', 'following']):
                        is_relevant = True
                
                if is_relevant:
                    relevant_messages.append({
                        "position": i,
                        "type": msg_type,
                        "content": content,
                        "relevance_score": 1.0  # Simple scoring for now
                    })
            
            return relevant_messages
            
    except Exception as e:
        log.warning(f"Failed to search conversation context for thread {thread_id}: {e}")
        return []


@tool
def get_conversation_context(query: str) -> str:
    """
    Search for relevant context from the current conversation.
    
    Use this tool when the user refers to "these", "them", "those", or other 
    context from previous messages in the conversation.
    
    Args:
        query: What you're looking for (e.g., "user stories mentioned earlier", 
               "the items we discussed", "bug count for these")
    
    Returns:
        Relevant context from previous conversation messages
    """
    # This will be injected by the agent builder when the tool is created
    # For now, return a placeholder
    return "Context search tool not properly initialized. Please ensure thread_id and checkpointer are available."


def create_conversation_context_tool(thread_id: str, checkpointer) -> callable:
    """
    Create a conversation context search tool bound to a specific thread and checkpointer.
    
    Args:
        thread_id: The current thread ID
        checkpointer: The checkpointer instance
        
    Returns:
        A tool function that can search conversation context
    """
    @tool
    def get_conversation_context(query: str) -> str:
        """
        Search for relevant context from the current conversation.
        
        Use this tool when the user refers to "these", "them", "those", or other 
        context from previous messages in the conversation.
        
        Args:
            query: What you're looking for (e.g., "user stories mentioned earlier", 
                   "the items we discussed", "bug count for these")
        
        Returns:
            Relevant context from previous conversation messages
        """
        try:
            relevant_messages = search_conversation_context(
                thread_id=thread_id,
                query=query,
                checkpointer=checkpointer,
                max_messages=20
            )
            
            if not relevant_messages:
                return "No relevant context found in previous conversation."
            
            # Format the context for the agent
            context_lines = ["=== Relevant Context from Previous Conversation ==="]
            
            for msg in relevant_messages[-5:]:  # Show last 5 relevant messages
                msg_type = msg["type"]
                content = msg["content"]
                
                # Clean up content for display
                if len(content) > 500:
                    content = content[:497] + "..."
                
                context_lines.append(f"{msg_type.upper()}: {content}")
            
            context_lines.append("=== End Context ===")
            
            result = "\n".join(context_lines)
            log.info(f"Found {len(relevant_messages)} relevant context messages for query: {query}")
            return result
            
        except Exception as e:
            log.error(f"Error searching conversation context: {e}")
            return f"Error searching conversation context: {str(e)}"
    
    # Set the tool name to avoid conflicts
    get_conversation_context.name = "get_conversation_context"
    return get_conversation_context