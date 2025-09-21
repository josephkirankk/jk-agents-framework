"""
Utility functions for the Pilger processing pipeline.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from uuid import uuid4

from app.main import load_app_config
from app.config import AgentConfig
from app.agent_builder import build_react_agent
from langgraph.graph.state import CompiledStateGraph

# Import parse_json_response from defect_analysis to reuse existing functionality
from gemba_agents.defect_analysis.utils.agent_utils import parse_json_response

logger = logging.getLogger(__name__)


async def load_and_build_agent_with_placeholders(
    agent_name: str,
    custom_placeholders: Optional[Dict[str, Any]] = None,
    config_path: str = "config/jk-gemba.yaml"
) -> Tuple[CompiledStateGraph, Optional[Any]]:
    """
    Load and build an agent from configuration with custom placeholder support.

    Args:
        agent_name: Name of the agent to load
        custom_placeholders: Custom placeholders to pass to the agent
        config_path: Path to the configuration file

    Returns:
        Tuple of (compiled_agent, mcp_client)

    Raises:
        ValueError: If agent is not found in configuration
        Exception: If agent building fails
    """
    try:
        # Load configuration
        config_file_path = Path(config_path)
        if not config_file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        app_config = load_app_config(config_file_path)

        # Find the target agent
        target_agent: Optional[AgentConfig] = next(
            (agent for agent in app_config.agents if agent.name == agent_name),
            None
        )

        if not target_agent:
            available_agents = [agent.name for agent in app_config.agents]
            raise ValueError(
                f"Agent '{agent_name}' not found in configuration. "
                f"Available agents: {available_agents}"
            )

        # Build the agent with custom placeholders and logging enabled
        default_model = app_config.models.get(
            "default", "google:gemini-2.5-flash-lite"
        )

        # Create DirectAgentLogger for pipeline execution to match direct API behavior
        from app.direct_agent_logger import create_direct_agent_logger
        direct_logger = create_direct_agent_logger(
            agent_name=agent_name,
            user_input="Pipeline execution",
            business_context=app_config.business_context or ""
        )

        compiled_agent, mcp_client = await build_react_agent(
            target_agent,
            default_model,
            business_context=app_config.business_context or "",
            original_user_question="",
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=True,
            llm_payload_logger=direct_logger.get_llm_payload_logger(),
            custom_placeholders=custom_placeholders
        )

        logger.info(
            f"Successfully built agent: {agent_name} with custom placeholders"
        )
        return compiled_agent, mcp_client, direct_logger

    except Exception as e:
        logger.error(f"Failed to load and build agent '{agent_name}': {str(e)}")
        raise


async def invoke_agent_async(
    compiled_agent: CompiledStateGraph,
    user_input: str,
    business_context: str = ""
) -> str:
    """
    Invoke a compiled agent asynchronously.

    Args:
        compiled_agent: The compiled agent to invoke
        user_input: User input to process
        business_context: Business context for the agent

    Returns:
        Agent response as string

    Raises:
        Exception: If agent invocation fails
    """
    try:
        # Prepare the state
        system_context = (
            f"Business context:\n{business_context}\n\n"
            "Previous step results:\n(none)"
        )

        state = {
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_input},
            ]
        }

        # Generate unique thread ID
        thread_id = str(uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # Invoke the agent
        try:
            result = await compiled_agent.ainvoke(state, config=config)
        except AttributeError:
            # Fallback to synchronous invocation if async is not available
            result = compiled_agent.invoke(state, config=config)

        # Extract the response
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if isinstance(last_message, dict) and "content" in last_message:
                response = last_message["content"]
            elif hasattr(last_message, 'content'):
                # Handle LangChain message objects
                response = last_message.content
            else:
                response = str(last_message)
        else:
            response = str(result)

        logger.debug(f"Agent response: {response[:200]}...")
        return response

    except Exception as e:
        logger.error(f"Failed to invoke agent: {str(e)}")
        raise


__all__ = [
    'load_and_build_agent_with_placeholders',
    'invoke_agent_async',
    'parse_json_response'
]
