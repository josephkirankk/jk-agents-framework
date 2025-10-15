"""
React Agent Implementation for LangGraph 0.6.7+

Provides a create_react_agent function that works with the latest LangGraph API,
replacing the deprecated langgraph.prebuilt.create_react_agent.

This implementation follows current LangGraph best practices and patterns.
"""

from typing import Any, Callable, Optional, Sequence, Union, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt.tool_node import ToolNode
import logging

log = logging.getLogger("react_agent_compat")


def create_react_agent(
    model: BaseChatModel,
    tools: Union[Sequence[BaseTool], Sequence[Callable]],
    *,
    prompt: Optional[str] = None,
    checkpointer: Optional[Any] = None,
    state_schema: Optional[type] = None,
    state_modifier: Optional[Union[str, Callable, Runnable]] = None,
) -> Runnable:
    """
    Create a ReAct-style agent using the latest LangGraph 0.6.7+ patterns.
    
    This replaces the deprecated langgraph.prebuilt.create_react_agent and follows
    the current best practices for building agent graphs.
    
    Args:
        model: The language model to use (should have tools bound to it already)
        tools: List of tools the agent can use
        prompt: System prompt for the agent (prepended to messages)
        checkpointer: Optional checkpointer for conversation persistence
        state_schema: Optional custom state schema (defaults to MessagesState)
        state_modifier: Optional state modifier (not implemented)
    
    Returns:
        A compiled LangGraph that can be invoked as a Runnable
    """
    if state_modifier is not None:
        log.warning("state_modifier parameter is not currently supported in this implementation")
    
    # Use custom state schema if provided, otherwise use MessagesState (standard pattern)
    state_cls = state_schema or MessagesState
    
    # Create the tool execution node
    tool_node = ToolNode(tools)
    
    def should_continue(state: Dict[str, Any]) -> str:
        """Route to tools if there are tool calls, otherwise end."""
        messages = state.get("messages", [])
        if not messages:
            return END
        
        last_message = messages[-1]
        
        # Check if last message has tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # No tool calls - conversation complete
        return END
    
    def call_model(state: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the model with the current message history."""
        messages = state.get("messages", [])
        
        # Prepend system prompt if provided
        if prompt:
            # Only add if there's no system message already
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=prompt)] + messages
        
        # Invoke the model (which should have tools bound already)
        response = model.invoke(messages)
        
        # Return state update
        return {"messages": [response]}
    
    # Build the state graph
    workflow = StateGraph(state_cls)
    
    # Add nodes: agent (model) and tools
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional routing from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",  # Route to tools if tool calls present
            END: END,          # End if no tool calls
        }
    )
    
    # After tools execute, always return to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    
    log.info(f"Created react agent with {len(tools)} tools")
    return app


__all__ = ["create_react_agent"]
