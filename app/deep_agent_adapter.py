"""
DeepAgents Integration Adapter

This module provides an adapter layer to integrate DeepAgents (https://github.com/langchain-ai/deepagents)
into the jk-agents-core framework. It translates between the framework's configuration system
and DeepAgents' API, enabling advanced features like:

- Hierarchical task decomposition via subagents
- Context management through virtual filesystem
- Task planning with TodoListMiddleware  
- Long-term memory across conversation threads
- Human-in-the-loop approval workflows

Architecture:
    Framework Config → DeepAgentAdapter → DeepAgent Instance → LangGraph Execution

The adapter maintains compatibility with existing framework components (tools, checkpointers,
model providers) while exposing DeepAgents' advanced capabilities.
"""

from __future__ import annotations
import logging
import sys
import traceback
from typing import Dict, List, Any, Optional
from langchain_core.runnables import Runnable
from langchain_core.messages import BaseMessage

log = logging.getLogger("deep_agent_adapter")


def _format_exception_for_logging(exc: Exception) -> str:
    """
    Format exception for detailed logging, handling ExceptionGroup.
    
    Returns:
        Formatted string with exception details and traceback
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)
    
    # Handle ExceptionGroup (Python 3.11+)
    if sys.version_info >= (3, 11):
        try:
            from builtins import ExceptionGroup as BuiltinExceptionGroup
            if isinstance(exc, BuiltinExceptionGroup):
                # Extract all exceptions from the group
                details = [f"ExceptionGroup with {len(exc.exceptions)} exception(s):"]
                for i, inner_exc in enumerate(exc.exceptions, 1):
                    inner_type = type(inner_exc).__name__
                    inner_msg = str(inner_exc)
                    inner_tb = ''.join(traceback.format_exception(
                        type(inner_exc), inner_exc, inner_exc.__traceback__
                    ))
                    details.append(f"\n  Exception {i}/{len(exc.exceptions)}:")
                    details.append(f"    Type: {inner_type}")
                    details.append(f"    Message: {inner_msg}")
                    details.append(f"    Traceback:\n{inner_tb}")
                return '\n'.join(details)
        except (ImportError, AttributeError):
            pass
    
    # Standard exception formatting
    tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    return f"{exc_type}: {exc_msg}\nTraceback:\n{tb_str}"


class DeepAgentAdapter:
    """
    Adapter to integrate DeepAgents into the jk-agents-core framework.
    
    This adapter:
    1. Translates framework configuration to DeepAgents parameters
    2. Manages subagent creation and tool binding
    3. Handles middleware configuration (filesystem, todolist, memory)
    4. Provides a unified interface compatible with existing agent patterns
    
    Usage:
        adapter = DeepAgentAdapter(
            model=model_instance,
            tools=tools_list,
            system_prompt="You are a research assistant...",
            deep_config=deep_agent_config,
            checkpointer=checkpointer
        )
        
        result = adapter.invoke({"messages": [...]}, config={"thread_id": "..."})
    """
    
    def __init__(
        self,
        model: Any,
        tools: List[Any],
        system_prompt: str,
        deep_config: Optional[Dict[str, Any]] = None,
        checkpointer: Optional[Any] = None,
        agent_name: str = "deep_agent",
    ):
        """
        Initialize the DeepAgentAdapter.
        
        Args:
            model: LangChain-compatible chat model instance
            tools: List of LangChain tools available to the agent
            system_prompt: System prompt for the main agent
            deep_config: DeepAgents configuration (middleware, subagents, etc.)
            checkpointer: LangGraph checkpointer for conversation persistence
            agent_name: Name for logging and identification
        """
        self.agent_name = agent_name
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.deep_config = deep_config or {}
        self.checkpointer = checkpointer
        
        log.info(f"Initializing DeepAgentAdapter for agent '{agent_name}'")
        
        # Import DeepAgents components
        try:
            from deepagents import create_deep_agent
            self._create_deep_agent = create_deep_agent
            log.info("DeepAgents package loaded successfully")
        except ImportError as e:
            log.error(f"Failed to import DeepAgents: {e}")
            raise ImportError(
                "DeepAgents package is required for agent_type='deep'. "
                "Install with: pip install deepagents"
            ) from e
        
        # Build the DeepAgent instance
        self._agent = self._build_deep_agent()
        
        log.info(f"DeepAgentAdapter initialized for '{agent_name}'")
    
    def _build_deep_agent(self) -> Runnable:
        """
        Build the DeepAgent instance with configured middleware and subagents.
        
        Returns:
            Compiled LangGraph agent with DeepAgents enhancements
        """
        log.info(f"Building DeepAgent '{self.agent_name}' with config: {self.deep_config}")
        
        # Extract configuration
        enable_filesystem = self.deep_config.get("enable_filesystem", True)
        enable_todolist = self.deep_config.get("enable_todolist", True)
        enable_longterm_memory = self.deep_config.get("enable_longterm_memory", False)
        subagents_config = self.deep_config.get("subagents", [])
        interrupt_on = self.deep_config.get("interrupt_on", None)
        store_config = self.deep_config.get("store_config", None)
        
        # Build subagents list
        subagents = self._build_subagents(subagents_config)
        
        # Initialize store for long-term memory if enabled
        store = None
        if enable_longterm_memory:
            store = self._create_store(store_config)
        
        # Build middleware list based on configuration
        middleware = []
        
        # Note: DeepAgents automatically includes middleware based on parameters
        # We'll pass configuration to create_deep_agent instead of manually building middleware
        
        try:
            # Create the deep agent
            agent = self._create_deep_agent(
                tools=self.tools,
                system_prompt=self.system_prompt,
                model=self.model,
                subagents=subagents if subagents else None,
                checkpointer=self.checkpointer,
                store=store,
                use_longterm_memory=enable_longterm_memory,
                interrupt_on=interrupt_on,
            )
            
            log.info(
                f"DeepAgent '{self.agent_name}' created successfully. "
                f"Filesystem: {enable_filesystem}, TodoList: {enable_todolist}, "
                f"Memory: {enable_longterm_memory}, Subagents: {len(subagents)}"
            )
            
            return agent
            
        except Exception as e:
            log.error(f"Failed to create DeepAgent '{self.agent_name}': {e}")
            raise
    
    def _build_subagents(self, subagents_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build subagent configurations from framework config.
        
        Args:
            subagents_config: List of subagent configurations from framework
            
        Returns:
            List of subagent configurations in DeepAgents format
        """
        if not subagents_config:
            return []
        
        subagents = []
        
        for sub_cfg in subagents_config:
            # Extract configuration
            name = sub_cfg.get("name")
            description = sub_cfg.get("description")
            system_prompt = sub_cfg.get("system_prompt")
            model = sub_cfg.get("model")  # Optional, uses parent model if None
            tool_names = sub_cfg.get("tools", [])
            
            # Filter tools for this subagent
            subagent_tools = self._filter_tools(tool_names) if tool_names else self.tools
            
            # Build subagent config in DeepAgents format
            subagent_config = {
                "name": name,
                "description": description,
                "system_prompt": system_prompt,
                "tools": subagent_tools,
            }
            
            # Add model if specified
            if model:
                subagent_config["model"] = model
            
            subagents.append(subagent_config)
            
            log.info(
                f"Configured subagent '{name}' with {len(subagent_tools)} tools"
            )
        
        return subagents
    
    def _filter_tools(self, tool_names: List[str]) -> List[Any]:
        """
        Filter tools by name for subagent.
        
        Args:
            tool_names: List of tool names to include
            
        Returns:
            List of tool instances matching the names
        """
        filtered_tools = []
        
        for tool in self.tools:
            tool_name = getattr(tool, "name", None)
            if tool_name in tool_names:
                filtered_tools.append(tool)
        
        if len(filtered_tools) != len(tool_names):
            log.warning(
                f"Some tools not found. Requested: {tool_names}, "
                f"Found: {[t.name for t in filtered_tools]}"
            )
        
        return filtered_tools
    
    def _create_store(self, store_config: Optional[Dict[str, Any]]) -> Any:
        """
        Create a LangGraph Store for long-term memory.
        
        Args:
            store_config: Optional store configuration
            
        Returns:
            LangGraph Store instance
        """
        try:
            from langgraph.store.memory import InMemoryStore
            
            # For now, use InMemoryStore (can extend to support ChromaDB, PostgreSQL, etc.)
            store = InMemoryStore()
            log.info("Created InMemoryStore for long-term memory")
            return store
            
        except ImportError as e:
            log.warning(f"Failed to create store: {e}")
            return None
    
    def invoke(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Invoke the DeepAgent with the given state.
        
        Args:
            state: Input state (must contain 'messages' key)
            config: Optional configuration (thread_id, etc.)
            
        Returns:
            Output state from the agent
        """
        try:
            result = self._agent.invoke(state, config=config)
            return result
        except Exception as e:
            error_details = _format_exception_for_logging(e)
            log.error(f"Error invoking DeepAgent '{self.agent_name}':\n{error_details}")
            raise
    
    async def ainvoke(
        self, 
        state: Dict[str, Any], 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Async invoke the DeepAgent with the given state.
        
        Args:
            state: Input state (must contain 'messages' key)
            config: Optional configuration (thread_id, etc.)
            
        Returns:
            Output state from the agent
        """
        try:
            result = await self._agent.ainvoke(state, config=config)
            return result
        except Exception as e:
            error_details = _format_exception_for_logging(e)
            log.error(f"Error async invoking DeepAgent '{self.agent_name}':\n{error_details}")
            raise
    
    def stream(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        Stream results from the DeepAgent.
        
        Args:
            state: Input state (must contain 'messages' key)
            config: Optional configuration (thread_id, etc.)
            
        Yields:
            State updates from the agent
        """
        try:
            for chunk in self._agent.stream(state, config=config, stream_mode="values"):
                yield chunk
        except Exception as e:
            log.error(f"Error streaming from DeepAgent '{self.agent_name}': {e}")
            raise
    
    def get_state(self, config: Dict[str, Any]) -> Any:
        """Get the current state from checkpointer."""
        if hasattr(self._agent, "get_state"):
            return self._agent.get_state(config)
        return None
    
    def update_state(self, config: Dict[str, Any], values: Dict[str, Any]) -> Any:
        """Update the state in checkpointer."""
        if hasattr(self._agent, "update_state"):
            return self._agent.update_state(config, values)
        return None


def create_deep_agent_from_config(
    model: Any,
    tools: List[Any],
    system_prompt: str,
    agent_config: Any,
    checkpointer: Optional[Any] = None,
) -> DeepAgentAdapter:
    """
    Factory function to create a DeepAgentAdapter from framework configuration.
    
    Args:
        model: LangChain-compatible chat model
        tools: List of tools
        system_prompt: System prompt
        agent_config: AgentConfig object with deep_agent_config field
        checkpointer: Optional checkpointer
        
    Returns:
        Configured DeepAgentAdapter instance
    """
    # Extract deep agent configuration
    deep_config_obj = agent_config.deep_agent_config
    
    if deep_config_obj is None:
        # Use defaults
        deep_config = {
            "enable_filesystem": True,
            "enable_todolist": True,
            "enable_longterm_memory": False,
            "subagents": [],
        }
    else:
        # Convert Pydantic model to dict
        deep_config = {
            "enable_filesystem": deep_config_obj.enable_filesystem,
            "enable_todolist": deep_config_obj.enable_todolist,
            "enable_longterm_memory": deep_config_obj.enable_longterm_memory,
            "subagents": [
                {
                    "name": sub.name,
                    "description": sub.description,
                    "system_prompt": sub.system_prompt,
                    "model": sub.model,
                    "tools": sub.tools,
                }
                for sub in deep_config_obj.subagents
            ],
            "interrupt_on": deep_config_obj.interrupt_on,
            "store_config": deep_config_obj.store_config,
        }
    
    return DeepAgentAdapter(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        deep_config=deep_config,
        checkpointer=checkpointer,
        agent_name=agent_config.name,
    )


__all__ = ["DeepAgentAdapter", "create_deep_agent_from_config"]
