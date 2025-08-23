"""
Python Function Tool Loader for JK Agents
==========================================

This module provides functionality to load Python function-based tools
from modules and integrate them with the LangChain agent system.
"""

import importlib
import logging
from typing import List, Dict, Any, Optional

from langchain.tools.base import BaseTool

log = logging.getLogger("python_tool_loader")


def load_python_function_tools(
    python_tools_config: Dict[str, Any]
) -> List[BaseTool]:
    """Load Python function tools from configuration.

    Args:
        python_tools_config: Dictionary containing Python tool configurations

    Returns:
        List of LangChain BaseTool instances

    Example config:
        python_tools:
          business_tools:
            module_path: "tools.python_function_tools"
            tool_names: ["calculate_percentage", "format_currency"]
            description: "Business calculation tools"

          data_tools:
            module_path: "tools.python_function_tools"
            tool_names: ["data_analyzer", "generate_random_data"]
            description: "Data analysis and generation tools"
    """
    tools = []

    for tool_set_name, config in python_tools_config.items():
        try:
            # Handle both dict and PythonFunctionToolConfig objects
            if hasattr(config, 'dict'):
                # Pydantic model - convert to dict
                config_dict = config.dict()
            elif hasattr(config, '__dict__'):
                # Object with attributes
                config_dict = config.__dict__
            else:
                # Already a dict
                config_dict = config

            module_path = config_dict.get("module_path")
            if not module_path:
                log.warning(
                    f"No module_path specified for tool set '{tool_set_name}'"
                )
                continue

            # Import the module
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                log.error(
                    f"Failed to import module '{module_path}' for tool set "
                    f"'{tool_set_name}': {e}"
                )
                continue

            # Get specific tools or all tools from module
            tool_names = config_dict.get("tool_names")
            function_name = config_dict.get("function_name")

            if tool_names:
                # Load specific tools by name
                loaded_tools = _load_specific_tools(
                    module, tool_names, tool_set_name
                )
                tools.extend(loaded_tools)

            elif function_name:
                # Load a specific function from the module
                tool = _load_single_function(
                    module, function_name, tool_set_name
                )
                if tool:
                    tools.append(tool)

            else:
                # Load all tools from module
                loaded_tools = _load_all_tools_from_module(
                    module, tool_set_name
                )
                tools.extend(loaded_tools)

        except Exception as e:
            log.error(
                f"Error loading Python tools for set '{tool_set_name}': {e}"
            )
            continue

    log.info(f"Loaded {len(tools)} Python function tools")
    return tools


def _load_specific_tools(
    module, tool_names: List[str], tool_set_name: str
) -> List[BaseTool]:
    """Load specific tools from a module by name."""
    tools = []
    
    # Try to use the module's load_tools_from_config function if available
    if hasattr(module, 'load_tools_from_config'):
        try:
            tools = module.load_tools_from_config(tool_names)
            log.info(
                f"Loaded {len(tools)} tools from {tool_set_name} using "
                "load_tools_from_config"
            )
            return tools
        except Exception as e:
            log.warning(
                f"Failed to use load_tools_from_config for {tool_set_name}: {e}"
            )
    
    # Fallback: try to get tools from TOOL_REGISTRY
    if hasattr(module, 'TOOL_REGISTRY'):
        registry = module.TOOL_REGISTRY
        for tool_name in tool_names:
            if tool_name in registry:
                tools.append(registry[tool_name])
            else:
                log.warning(
                    f"Tool '{tool_name}' not found in registry for "
                    f"{tool_set_name}"
                )
    else:
        # Fallback: try to get tools by attribute name
        for tool_name in tool_names:
            if hasattr(module, tool_name):
                tool = getattr(module, tool_name)
                if hasattr(tool, 'name') and hasattr(tool, 'run'):
                    tools.append(tool)
                else:
                    log.warning(
                        f"Attribute '{tool_name}' in {tool_set_name} is not "
                        "a valid tool"
                    )
            else:
                log.warning(
                    f"Tool '{tool_name}' not found in module for "
                    f"{tool_set_name}"
                )
    
    return tools


def _load_single_function(
    module, function_name: str, tool_set_name: str
) -> Optional[BaseTool]:
    """Load a single function as a tool from a module."""
    if hasattr(module, function_name):
        func = getattr(module, function_name)
        if hasattr(func, 'name') and hasattr(func, 'run'):
            log.info(f"Loaded function '{function_name}' from {tool_set_name}")
            return func
        else:
            log.warning(
                f"Function '{function_name}' in {tool_set_name} is not a "
                "valid tool"
            )
    else:
        log.warning(
            f"Function '{function_name}' not found in module for "
            f"{tool_set_name}"
        )
    return None


def _load_all_tools_from_module(
    module, tool_set_name: str
) -> List[BaseTool]:
    """Load all available tools from a module."""
    tools = []
    
    # Try to use the module's get_all_function_tools function if available
    if hasattr(module, 'get_all_function_tools'):
        try:
            tools = module.get_all_function_tools()
            log.info(
                f"Loaded {len(tools)} tools from {tool_set_name} using "
                "get_all_function_tools"
            )
            return tools
        except Exception as e:
            log.warning(
                f"Failed to use get_all_function_tools for {tool_set_name}: {e}"
            )
    
    # Fallback: try to get all tools from TOOL_REGISTRY
    if hasattr(module, 'TOOL_REGISTRY'):
        registry = module.TOOL_REGISTRY
        tools = list(registry.values())
        log.info(
            f"Loaded {len(tools)} tools from {tool_set_name} registry"
        )
    else:
        log.warning(
            f"No standard tool loading method found for {tool_set_name}"
        )
    
    return tools


def validate_python_tools(tools: List[BaseTool]) -> List[BaseTool]:
    """Validate that loaded tools are proper LangChain tools."""
    valid_tools = []
    
    for tool in tools:
        if not hasattr(tool, 'name'):
            log.warning(f"Tool {tool} missing 'name' attribute")
            continue
            
        if not (hasattr(tool, 'run') or hasattr(tool, '_run')):
            log.warning(f"Tool {tool.name} missing 'run' or '_run' method")
            continue
            
        if not hasattr(tool, 'description'):
            log.warning(f"Tool {tool.name} missing 'description' attribute")
            continue
            
        valid_tools.append(tool)
    
    log.info(f"Validated {len(valid_tools)} Python function tools")
    return valid_tools
