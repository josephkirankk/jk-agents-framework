"""
LLM Payload Logger - Comprehensive logging wrapper for capturing complete LLM interactions.

This module provides a wrapper around LLM models to capture and log the complete
payload sent to and received from the LLM, including messages, tools, and parameters.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.language_models.chat_models import BaseChatModel

log = logging.getLogger("llm_payload_logger")


class LLMPayloadLogger:
    """Logger for capturing complete LLM request/response payloads."""
    
    def __init__(self, agent_name: str, log_dir: str = "logs"):
        """
        Initialize the LLM payload logger.
        
        Args:
            agent_name: Name of the agent using this logger
            log_dir: Directory to store log files
        """
        self.agent_name = agent_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"llm_payload_{agent_name}_{timestamp}.json"
        
        # Initialize log file with metadata
        self._initialize_log_file()
        
    def _initialize_log_file(self):
        """Initialize the log file with metadata."""
        metadata = {
            "log_type": "llm_payload_log",
            "agent_name": self.agent_name,
            "created_at": datetime.now().isoformat(),
            "entries": []
        }
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def log_llm_interaction(
        self,
        interaction_type: str,
        messages: List[Any],
        tools: Optional[List[Dict[str, Any]]] = None,
        model_params: Optional[Dict[str, Any]] = None,
        response: Optional[Any] = None,
        usage: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log a complete LLM interaction.
        
        Args:
            interaction_type: Type of interaction (invoke, stream, etc.)
            messages: Messages sent to the LLM
            tools: Tool definitions bound to the model
            model_params: Model parameters and configuration
            response: Response from the LLM
            usage: Token usage information
            error: Error message if interaction failed
        """
        try:
            # Read current log file
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # Create interaction entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "interaction_type": interaction_type,
                "request": {
                    "messages": self._serialize_messages(messages),
                    "tools": tools or [],
                    "model_params": model_params or {}
                },
                "response": {
                    "content": self._serialize_response(response) if response else None,
                    "usage": usage or {},
                    "error": error
                }
            }
            
            # Add entry to log
            log_data["entries"].append(entry)
            
            # Write back to file
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
            # Also log to standard logger for immediate visibility
            log.info(f"LLM Interaction [{interaction_type}] - Agent: {self.agent_name}")

            # Determine status based on interaction type and content
            if interaction_type.endswith('_response'):
                status = 'Success' if response and not error else ('Error' if error else 'No Response')
            elif interaction_type.endswith('_error'):
                status = 'Error'
            else:
                status = 'Request'  # For initial request logging

            log.info(f"Messages: {len(messages)} | Tools: {len(tools or [])} | Status: {status}")
            
        except Exception as e:
            log.error(f"Failed to log LLM interaction: {e}")
    
    def _serialize_messages(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Serialize messages to JSON-compatible format."""
        serialized = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                serialized.append({
                    "type": msg.__class__.__name__,
                    "content": msg.content,
                    "role": getattr(msg, 'role', None),
                    "additional_kwargs": getattr(msg, 'additional_kwargs', {}),
                    "tool_calls": getattr(msg, 'tool_calls', [])
                })
            elif isinstance(msg, dict):
                serialized.append(msg)
            else:
                serialized.append({"raw": str(msg)})
        return serialized
    
    def _serialize_response(self, response: Any) -> Dict[str, Any]:
        """Serialize response to JSON-compatible format."""
        if isinstance(response, BaseMessage):
            return {
                "type": response.__class__.__name__,
                "content": response.content,
                "additional_kwargs": getattr(response, 'additional_kwargs', {}),
                "tool_calls": getattr(response, 'tool_calls', []),
                "usage_metadata": getattr(response, 'usage_metadata', {})
            }
        elif hasattr(response, 'dict'):
            return response.dict()
        elif isinstance(response, dict):
            return response
        else:
            return {"raw": str(response)}
    
    def get_log_file_path(self) -> str:
        """Get the path to the log file."""
        return str(self.log_file)


class LoggingModelWrapper(Runnable):
    """
    Wrapper around LLM models to capture complete request/response payloads.

    This wrapper intercepts all calls to the underlying model and logs the
    complete payload including messages, tools, parameters, and responses.
    """

    def __init__(self, wrapped_model: BaseChatModel, payload_logger: LLMPayloadLogger):
        """
        Initialize the logging wrapper.

        Args:
            wrapped_model: The actual LLM model to wrap
            payload_logger: Logger instance for capturing payloads
        """
        super().__init__()
        self._wrapped_model = wrapped_model
        self._payload_logger = payload_logger
    
    def _get_model_params(self) -> Dict[str, Any]:
        """Extract model parameters for logging."""
        params = {}
        for attr in ['model_name', 'temperature', 'max_tokens', 'top_p', 'frequency_penalty', 'presence_penalty']:
            if hasattr(self._wrapped_model, attr):
                value = getattr(self._wrapped_model, attr)
                if value is not None:
                    params[attr] = value
        
        # Add model kwargs if available
        if hasattr(self._wrapped_model, 'model_kwargs'):
            params.update(self._wrapped_model.model_kwargs or {})
            
        return params
    
    def _extract_tools_info(self) -> List[Dict[str, Any]]:
        """Extract bound tools information."""
        tools_info = []

        # Check multiple possible locations for tools
        tools = None

        # Method 1: Check kwargs
        if hasattr(self._wrapped_model, 'kwargs') and 'tools' in self._wrapped_model.kwargs:
            tools = self._wrapped_model.kwargs['tools']

        # Method 2: Check bound_tools attribute
        elif hasattr(self._wrapped_model, 'bound_tools'):
            tools = self._wrapped_model.bound_tools

        # Method 3: Check tools attribute directly
        elif hasattr(self._wrapped_model, 'tools'):
            tools = self._wrapped_model.tools

        # Method 4: Check if it's a bound model with tools in different format
        elif hasattr(self._wrapped_model, '__dict__'):
            for key, value in self._wrapped_model.__dict__.items():
                if 'tool' in key.lower() and isinstance(value, (list, tuple)):
                    tools = value
                    break

        if tools:
            for tool in tools:
                tool_info = {}

                # Handle LangChain bound tool format (most common)
                if isinstance(tool, dict) and tool.get('type') == 'function' and 'function' in tool:
                    func_def = tool['function']
                    tool_info["name"] = func_def.get('name', 'unknown')
                    tool_info["description"] = func_def.get('description', 'No description available')
                    tool_info["args_schema"] = func_def.get('parameters', None)

                # Handle direct tool objects (less common)
                elif hasattr(tool, 'name'):
                    tool_info["name"] = tool.name
                    tool_info["description"] = getattr(tool, 'description', 'No description available')

                    # Handle args_schema
                    args_schema = getattr(tool, 'args_schema', None)
                    if args_schema:
                        if hasattr(args_schema, 'schema'):
                            try:
                                tool_info["args_schema"] = args_schema.schema()
                            except:
                                tool_info["args_schema"] = str(args_schema)
                        elif isinstance(args_schema, dict):
                            tool_info["args_schema"] = args_schema
                        else:
                            tool_info["args_schema"] = str(args_schema)
                    else:
                        tool_info["args_schema"] = None

                # Handle other dictionary formats
                elif isinstance(tool, dict):
                    tool_info["name"] = tool.get('name', str(tool))
                    tool_info["description"] = tool.get('description', 'No description available')
                    tool_info["args_schema"] = tool.get('args_schema', tool.get('parameters', None))

                # Fallback for unknown formats
                else:
                    tool_info["name"] = str(tool)
                    tool_info["description"] = "No description available"
                    tool_info["args_schema"] = None

                tools_info.append(tool_info)

        return tools_info
    
    def invoke(self, input, config=None, **kwargs):
        """Override invoke to log the complete interaction."""
        try:
            # Extract messages from input
            messages = input if isinstance(input, list) else [input]
            
            # Get model parameters and tools
            model_params = self._get_model_params()
            tools_info = self._extract_tools_info()
            
            # Log the request
            self._payload_logger.log_llm_interaction(
                interaction_type="invoke",
                messages=messages,
                tools=tools_info,
                model_params=model_params
            )
            
            # Call the wrapped model
            response = self._wrapped_model.invoke(input, config=config, **kwargs)
            
            # Extract usage information
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = getattr(response, 'usage_metadata', {})
            
            # Log the response
            self._payload_logger.log_llm_interaction(
                interaction_type="invoke_response",
                messages=messages,
                tools=tools_info,
                model_params=model_params,
                response=response,
                usage=usage
            )
            
            return response
            
        except Exception as e:
            # Log the error
            self._payload_logger.log_llm_interaction(
                interaction_type="invoke_error",
                messages=messages if 'messages' in locals() else [],
                tools=tools_info if 'tools_info' in locals() else [],
                model_params=model_params if 'model_params' in locals() else {},
                error=str(e)
            )
            raise
    
    async def ainvoke(self, input, config=None, **kwargs):
        """Override ainvoke to log the complete interaction."""
        try:
            # Extract messages from input
            messages = input if isinstance(input, list) else [input]
            
            # Get model parameters and tools
            model_params = self._get_model_params()
            tools_info = self._extract_tools_info()
            
            # Log the request
            self._payload_logger.log_llm_interaction(
                interaction_type="ainvoke",
                messages=messages,
                tools=tools_info,
                model_params=model_params
            )
            
            # Call the wrapped model
            response = await self._wrapped_model.ainvoke(input, config=config, **kwargs)
            
            # Extract usage information
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = getattr(response, 'usage_metadata', {})
            
            # Log the response
            self._payload_logger.log_llm_interaction(
                interaction_type="ainvoke_response",
                messages=messages,
                tools=tools_info,
                model_params=model_params,
                response=response,
                usage=usage
            )
            
            return response
            
        except Exception as e:
            # Log the error
            self._payload_logger.log_llm_interaction(
                interaction_type="ainvoke_error",
                messages=messages if 'messages' in locals() else [],
                tools=tools_info if 'tools_info' in locals() else [],
                model_params=model_params if 'model_params' in locals() else {},
                error=str(e)
            )
            raise
    
    def bind_tools(self, tools, **kwargs):
        """Bind tools to the wrapped model and return a new wrapper."""
        bound_model = self._wrapped_model.bind_tools(tools, **kwargs)
        return LoggingModelWrapper(bound_model, self._payload_logger)

    def __getattr__(self, name):
        """Delegate all attribute access to the wrapped model."""
        return getattr(self._wrapped_model, name)

    def __setattr__(self, name, value):
        """Handle attribute setting."""
        if name in ('_wrapped_model', '_payload_logger'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._wrapped_model, name, value)
