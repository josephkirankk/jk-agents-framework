"""
Filtered Tool Node for LangGraph React Agents

Wraps the standard ToolNode to filter large base64 content from tool results
BEFORE they're added to LangGraph message history.

This is critical for vision workflows where get_image_base64() returns 50K+ token
base64 strings that would otherwise be repeated in every subsequent LLM call.
"""

import json
import logging
from typing import Union, Sequence, Literal
from langchain_core.messages import ToolMessage, BaseMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.tool_node import ToolNode

log = logging.getLogger(__name__)


class FilteredToolNode(ToolNode):
    """
    ToolNode that automatically filters large base64 content from tool results.
    
    Extends LangGraph's standard ToolNode to intercept ToolMessages and remove
    base64_content fields before they're added to message history.
    """
    
    def __init__(self, tools: Sequence, *, name: str = "tools", tags: list[str] | None = None, **kwargs):
        """
        Initialize FilteredToolNode with automatic base64 filtering.
        
        Args:
            tools: List of tools available to this node
            name: Node name (default: "tools")
            tags: Optional tags for the node
            **kwargs: Additional arguments passed to parent ToolNode
        """
        super().__init__(tools, name=name, tags=tags)
        self.filter_enabled = True
        log.info(f"Initialized FilteredToolNode with {len(tools)} tools (base64 filtering enabled)")
    
    def _filter_tool_message_content(self, content: str, tool_name: str = "unknown") -> tuple[str, int]:
        """
        Filter base64 content from tool message content.
        
        Returns:
            tuple: (filtered_content, tokens_saved)
        """
        if not self.filter_enabled:
            return content, 0
        
        try:
            if content.startswith('{') or content.startswith('['):
                data = json.loads(content)
                
                # Check for base64_content field (from get_image_base64 tool)
                if isinstance(data, dict) and 'base64_content' in data:
                    base64_len = len(data.get('base64_content', ''))
                    estimated_tokens = base64_len // 3  # Rough estimate
                    
                    # Create filtered copy
                    filtered_data = data.copy()
                    filtered_data['base64_content'] = f"[FILTERED: {base64_len} chars, ~{estimated_tokens:,} tokens saved]"
                    filtered_data['_filter_note'] = "Base64 content used for vision processing, removed from history to prevent token bloat"
                    
                    log.info(
                        f"✂️  Filtered base64 from '{tool_name}': "
                        f"removed {base64_len:,} chars (~{estimated_tokens:,} tokens)"
                    )
                    
                    return json.dumps(filtered_data, indent=2), estimated_tokens
                
                # Check for other large content fields
                if isinstance(data, dict):
                    for key in ['content', 'data', 'body', 'text']:
                        if key in data and isinstance(data[key], str) and len(data[key]) > 10000:
                            content_len = len(data[key])
                            estimated_tokens = content_len // 4
                            
                            filtered_data = data.copy()
                            filtered_data[key] = f"[FILTERED: {content_len} chars, ~{estimated_tokens:,} tokens saved]"
                            filtered_data['_filter_note'] = "Large content removed from history to prevent token bloat"
                            
                            log.info(
                                f"✂️  Filtered large content from '{tool_name}.{key}': "
                                f"removed {content_len:,} chars (~{estimated_tokens:,} tokens)"
                            )
                            
                            return json.dumps(filtered_data, indent=2), estimated_tokens
        
        except (json.JSONDecodeError, Exception) as e:
            log.debug(f"Content filtering check failed for '{tool_name}': {e}")
        
        return content, 0
    
    def __call__(self, input: Union[list[AIMessage], dict[str, any]], config: RunnableConfig = None) -> dict:
        """
        Execute tools and filter results before adding to message history.
        
        This method overrides the parent ToolNode.__call__ to intercept tool results
        and filter base64 content BEFORE the ToolMessages are returned to LangGraph.
        """
        # Call parent ToolNode to execute tools
        result = super().__call__(input, config)
        
        # Filter ToolMessages in the result
        if isinstance(result, dict) and 'messages' in result:
            filtered_messages = []
            total_tokens_saved = 0
            
            for msg in result['messages']:
                if isinstance(msg, ToolMessage):
                    original_content = msg.content
                    filtered_content, tokens_saved = self._filter_tool_message_content(
                        original_content, 
                        msg.name
                    )
                    
                    if tokens_saved > 0:
                        total_tokens_saved += tokens_saved
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
            
            if total_tokens_saved > 0:
                log.info(f"💾 Total tokens saved by filtering: ~{total_tokens_saved:,}")
            
            result['messages'] = filtered_messages
        
        return result


def create_filtered_react_agent(model, tools, *, checkpointer=None, prompt=None, **kwargs):
    """
    Create a React agent with automatic base64 content filtering.
    
    This is a drop-in replacement for create_react_agent that
    uses FilteredToolNode instead of the standard ToolNode.
    
    Args:
        model: The language model to use
        tools: List of tools available to the agent
        checkpointer: Optional checkpointer for state persistence
        prompt: Optional system prompt or prompt template
        **kwargs: Additional arguments passed to create_react_agent
        
    Returns:
        Compiled LangGraph agent with filtered tool node
    """
    # Use compatibility layer for create_react_agent (removed in LangGraph 0.6.7+)
    from ..react_agent_compat import create_react_agent as _create_react_agent
    from langgraph.graph import StateGraph
    
    # Create standard agent
    agent = _create_react_agent(
        model, 
        tools, 
        checkpointer=checkpointer,
        prompt=prompt,
        **kwargs
    )
    
    # Replace the tools node with our filtered version
    try:
        # Access the compiled graph's nodes
        if hasattr(agent, 'nodes') and 'tools' in agent.nodes:
            filtered_tool_node = FilteredToolNode(tools, name="tools")
            agent.nodes['tools'] = filtered_tool_node
            log.info("✅ Replaced standard ToolNode with FilteredToolNode")
        else:
            log.warning("⚠️  Could not replace ToolNode - agent structure not as expected")
    except Exception as e:
        log.error(f"❌ Failed to replace ToolNode with FilteredToolNode: {e}")
    
    return agent