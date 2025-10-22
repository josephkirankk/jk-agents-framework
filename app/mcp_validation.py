"""
MCP Server Environment Validation

This module provides pre-flight validation for MCP server requirements,
checking that necessary environment variables and dependencies are available
before executing agent queries.
"""
from __future__ import annotations
import os
import logging
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("mcp_validation")


def validate_mcp_server_env(agent_config: Dict, agent_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that required environment variables are set for MCP servers.
    
    Args:
        agent_config: Agent configuration dict or object
        agent_name: Name of the agent being validated
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if all requirements are met, False otherwise
        - error_message: None if valid, descriptive error message if invalid
    """
    # Extract MCP servers config
    mcp_servers = None
    
    # Handle both dict and object formats
    if isinstance(agent_config, dict):
        mcp_servers = agent_config.get("mcp_servers", {})
    elif hasattr(agent_config, "mcp_servers"):
        mcp_servers = agent_config.mcp_servers
    
    if not mcp_servers:
        # No MCP servers configured, validation passes
        return True, None
    
    # Convert to dict if it's a Pydantic model
    if hasattr(mcp_servers, "model_dump"):
        mcp_servers = mcp_servers.model_dump()
    elif hasattr(mcp_servers, "dict"):
        mcp_servers = mcp_servers.dict()
    
    # Check each MCP server for required environment variables
    missing_vars = []
    
    for server_name, server_config in mcp_servers.items():
        # Extract environment variables
        env_vars = None
        if isinstance(server_config, dict):
            env_vars = server_config.get("env", {})
        elif hasattr(server_config, "env"):
            env_vars = server_config.env
        
        if not env_vars:
            continue
        
        # Convert env dict to plain dict if needed
        if hasattr(env_vars, "model_dump"):
            env_vars = env_vars.model_dump()
        elif hasattr(env_vars, "dict"):
            env_vars = env_vars.dict()
        
        # Check each environment variable
        for var_name, var_value in env_vars.items():
            # Check if it's a reference to an environment variable (${VAR_NAME})
            if isinstance(var_value, str) and var_value.startswith("${") and var_value.endswith("}"):
                # Extract the actual variable name
                actual_var = var_value[2:-1]
                
                # Check if it's set in the environment
                env_value = os.getenv(actual_var)
                
                if not env_value:
                    missing_vars.append({
                        "server": server_name,
                        "variable": actual_var,
                        "config_ref": var_value
                    })
                    log.warning(
                        f"MCP server '{server_name}' requires environment variable '{actual_var}' "
                        f"but it is not set"
                    )
    
    if missing_vars:
        # Build detailed error message
        error_lines = [
            f"Agent '{agent_name}' requires environment variables that are not set:",
            ""
        ]
        
        for missing in missing_vars:
            error_lines.append(
                f"  • {missing['variable']} (required by MCP server '{missing['server']}')"
            )
        
        error_lines.extend([
            "",
            "Please set the required environment variables in your .env file.",
            ""
        ])
        
        # Add specific hints for common variables
        for missing in missing_vars:
            var_name = missing['variable']
            if "SERPER" in var_name:
                error_lines.extend([
                    f"💡 To get {var_name}:",
                    "   1. Visit https://serper.dev",
                    "   2. Sign up for a free account (2,500 free searches)",
                    "   3. Get your API key from the dashboard",
                    f"   4. Add to .env: {var_name}=your_api_key_here",
                    ""
                ])
        
        error_message = "\n".join(error_lines)
        return False, error_message
    
    # All validations passed
    return True, None


def validate_all_agents_env(agents_configs: List) -> Tuple[bool, Optional[str]]:
    """
    Validate environment variables for all agents in a configuration.
    
    Args:
        agents_configs: List of agent configurations
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    all_errors = []
    
    for agent_config in agents_configs:
        # Get agent name
        agent_name = None
        if isinstance(agent_config, dict):
            agent_name = agent_config.get("name", "unknown")
        elif hasattr(agent_config, "name"):
            agent_name = agent_config.name
        else:
            agent_name = "unknown"
        
        # Validate this agent
        is_valid, error_msg = validate_mcp_server_env(agent_config, agent_name)
        
        if not is_valid and error_msg:
            all_errors.append(error_msg)
    
    if all_errors:
        combined_error = "\n\n".join(all_errors)
        return False, combined_error
    
    return True, None
