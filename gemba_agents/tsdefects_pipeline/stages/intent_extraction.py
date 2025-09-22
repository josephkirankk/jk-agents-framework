"""
Intent extraction stage for the TsDefects pipeline.

This stage uses the jk_pilger_extract_intent_agent to process raw user input
and extract structured intent data including component, sub-component, 
related component, and issue information.

This is adapted from the defect_analysis pipeline to work with TsDefectsConfig.
"""

import logging
import time
from typing import Dict, Any

from pipefunc import pipefunc

from gemba_agents.defect_analysis.models.data_models import IntentData
from ..models.data_models import TsDefectsConfig
from ..utils.agent_utils import load_and_build_agent, invoke_agent_async, parse_json_response

logger = logging.getLogger(__name__)


async def _extract_intent_async(
    user_input: str,
    config: TsDefectsConfig = TsDefectsConfig()
) -> IntentData:
    """
    Extract structured intent data from user input using the intent extraction agent.
    
    This function loads and invokes the jk_pilger_extract_intent_agent to process
    raw user input describing equipment issues and extract structured information
    about components, issues, and related systems.
    
    Args:
        user_input: Raw user input describing equipment issues
        config: Configuration for the TsDefects pipeline
        
    Returns:
        IntentData object containing extracted intent information
        
    Raises:
        Exception: If intent extraction fails
        
    Example:
        >>> config = TsDefectsConfig()
        >>> intent = await extract_intent(
        ...     "The pump's loading/unloading piston is not operating smoothly",
        ...     config
        ... )
        >>> print(intent.component)  # "Pump"
        >>> print(intent.issue)      # "Not operating smoothly"
    """
    start_time = time.time()
    
    try:
        if config.enable_logging:
            logger.info(f"Starting intent extraction for input: {user_input[:100]}...")
        
        # Load and build the intent extraction agent
        compiled_agent, mcp_client, direct_logger = await load_and_build_agent(
            agent_name=config.intent_agent_name,
            config_path=config.config_path
        )

        try:
            # Log the agent request
            system_context = "Business context:\nPilger machine maintenance and defect analysis\n\nPrevious step results:\n(none)"
            direct_logger.log_agent_request(compiled_agent, system_context, user_input)

            # Invoke the agent with the user input
            response = await invoke_agent_async(
                compiled_agent=compiled_agent,
                user_input=user_input,
                business_context="Pilger machine maintenance and defect analysis"
            )

            # Log the agent response
            direct_logger.log_agent_response(response, {"messages": []})
            
            # Parse the JSON response
            intent_dict = parse_json_response(response)
            
            # Validate and create IntentData object
            intent_data = IntentData(**intent_dict)
            
            execution_time = (time.time() - start_time) * 1000
            
            if config.enable_logging:
                logger.info(
                    f"Intent extraction completed in {execution_time:.2f}ms. "
                    f"Component: {intent_data.component}, Issue: {intent_data.issue}"
                )
            
            return intent_data
            
        finally:
            # Clean up MCP client if it exists
            if mcp_client:
                try:
                    await mcp_client.close()
                except Exception as e:
                    logger.warning(f"Failed to close MCP client: {e}")
    
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Intent extraction failed after {execution_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        # Return a default IntentData object with error information
        return IntentData(
            interpreted_meaning=f"Failed to extract intent: {str(e)}",
            component="Unknown",
            sub_component="Unknown",
            related_component="Unknown",
            issue="Unknown"
        )


@pipefunc(output_name="intent_data", cache=True)
def extract_intent(
    user_input: str,
    config: TsDefectsConfig = TsDefectsConfig()
) -> IntentData:
    """
    Synchronous wrapper for intent extraction.

    This function wraps the async intent extraction logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        user_input: Raw user input describing equipment issues
        config: Configuration for the TsDefects pipeline

    Returns:
        IntentData object containing extracted intent information
    """
    import asyncio

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _extract_intent_async(user_input, config))
                return future.result()
        else:
            # We can use the existing loop
            return loop.run_until_complete(_extract_intent_async(user_input, config))
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(_extract_intent_async(user_input, config))
