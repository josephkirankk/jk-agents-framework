"""
Agent enhancement stage for the TsDefects pipeline.

This stage processes user intent through jk_pilger_new_entries_only_defects_agent
to generate defect suggestions with curator_action and rationale fields.
The agent can either suggest new entries or provide nearest matching results.
"""

import json
import logging
import time
import uuid
from typing import List, Dict, Any

from pipefunc import pipefunc
from vectordb_wrapper.ts_models import TsDefectResult

from gemba_agents.defect_analysis.models.data_models import IntentData
from ..models.data_models import TsDefectsConfig, AgentDefectResult
from ..utils.agent_utils import load_and_build_agent_with_placeholders, invoke_agent_async, parse_json_response

logger = logging.getLogger(__name__)


async def _enhance_with_agent_async(
    processed_results: List[TsDefectResult],
    intent_data: IntentData,
    config: TsDefectsConfig = TsDefectsConfig()
) -> List[AgentDefectResult]:
    """
    Process user intent through jk_pilger_new_entries_only_defects_agent to get defect suggestions.

    This function focuses solely on processing the agent's direct output, which can either:
    1. Suggest new entries for defect analysis, OR
    2. Provide nearest matching results from search operations

    Args:
        processed_results: List of processed TsDefectResult objects (used for ontology context)
        intent_data: Extracted intent data for the agent
        config: Configuration for the TsDefects pipeline

    Returns:
        List of AgentDefectResult objects from agent suggestions

    Raises:
        Exception: If agent enhancement fails
    """
    start_time = time.time()

    try:
        if config.enable_logging:
            logger.info(f"Starting agent enhancement with intent: {intent_data.interpreted_meaning}")

        # Prepare ontology data for the agent
        # Include existing search results as context if available
        if processed_results:
            defects_data = [result.model_dump() for result in processed_results]
            ontology_content = json.dumps({
                "defects": defects_data,
                "total_results": len(defects_data)
            }, indent=2, ensure_ascii=False)
            if config.enable_logging:
                logger.info(f"Providing {len(defects_data)} existing defects as ontology context")
        else:
            ontology_content = "no ontology search results for this user intent"
            if config.enable_logging:
                logger.info("No existing search results, agent will suggest new entries")

        # Prepare user intent for the agent
        user_intent_content = json.dumps(intent_data.model_dump(), indent=2, ensure_ascii=False)

        # Create custom placeholders for the agent
        custom_placeholders = {
            "ontology": ontology_content,
            "user_intent": user_intent_content
        }

        if config.enable_logging:
            logger.debug("Prepared custom placeholders for agent")

        # Load and build the agent with custom placeholders
        agent, mcp_client, direct_logger = (
            await load_and_build_agent_with_placeholders(
                agent_name=config.processing_agent_name,
                custom_placeholders=custom_placeholders,
                config_path=config.config_path
            )
        )

        try:
            # Use a simple trigger message since the real data is in placeholders
            trigger_message = "Process the user intent and provide defect analysis recommendations."

            # Log the agent request
            system_context = (
                "Business context:\n\nPrevious step results:\n(none)"
            )
            direct_logger.log_agent_request(
                agent, system_context, trigger_message
            )

            agent_response = await invoke_agent_async(
                compiled_agent=agent,
                user_input=trigger_message,
                business_context=""
            )

            # Log the agent response
            direct_logger.log_agent_response(agent_response, {"messages": []})

            if config.enable_logging:
                logger.debug(f"Agent response: {agent_response[:200]}...")

            # Parse the agent response
            parsed_response = parse_json_response(agent_response)

            # Create enhanced results directly from agent output
            enhanced_results = _create_enhanced_results_from_agent(
                parsed_response,
                config
            )

            processing_time = (time.time() - start_time) * 1000

            if config.enable_logging:
                logger.info(
                    f"Agent enhancement completed in {processing_time:.2f}ms. "
                    f"Generated {len(enhanced_results)} defect suggestions"
                )

            return enhanced_results

        finally:
            # Clean up MCP client if it exists
            if mcp_client:
                try:
                    await mcp_client.close()
                except Exception as e:
                    logger.warning(f"Failed to close MCP client: {e}")

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        error_msg = (
            f"Agent enhancement failed after {processing_time:.2f}ms: "
            f"{str(e)}"
        )
        logger.error(error_msg)

        # Return empty results on failure
        return []


def _create_enhanced_results_from_agent(
    agent_response: Dict[str, Any],
    config: TsDefectsConfig
) -> List[AgentDefectResult]:
    """
    Create enhanced results directly from agent response.

    This function processes the agent's output which contains defect suggestions
    with all required fields including curator_action and rationale.

    Args:
        agent_response: Parsed agent response containing defects and metadata
        config: Pipeline configuration

    Returns:
        List of AgentDefectResult objects from agent suggestions
    """
    enhanced_results = []

    try:
        # Extract defects from agent response
        agent_defects = agent_response.get("defects", [])

        if not agent_defects:
            if config.enable_logging:
                logger.info("No defects found in agent response")
            return enhanced_results

        if config.enable_logging:
            logger.info(f"Processing {len(agent_defects)} defects from agent")

        # Extract subsystems and components data for descriptions
        subsystems_data = agent_response.get("subsystems", [])
        components_data = agent_response.get("components", [])

        for agent_defect in agent_defects:
            try:
                # KISS: Return agent data exactly as provided
                result = AgentDefectResult(
                    defect_code=agent_defect.get("defect_code", ""),
                    defect_text=agent_defect.get("defect_text", ""),
                    defect_location=agent_defect.get("defect_location", "null"),
                    confidence_score=agent_defect.get("confidence_score", 0.8),
                    mapping_status=agent_defect.get("mapping_status", "NEW_ENTRY"),
                    curator_action=agent_defect.get("curator_action", "REVIEW_REQUIRED"),
                    rationale=agent_defect.get("rationale", "Agent-generated defect")
                )

                enhanced_results.append(result)

                if config.enable_logging:
                    logger.debug(f"Created result for defect: {agent_defect.get('defect_code', 'Unknown')}")

            except Exception as e:
                logger.warning(f"Error processing agent defect: {e}")
                continue

    except Exception as e:
        logger.error(f"Error creating enhanced results from agent: {e}")

    return enhanced_results


@pipefunc(output_name="enhanced_results", cache=True)
def enhance_with_agent(
    processed_results: List[TsDefectResult],
    intent_data: IntentData,
    config: TsDefectsConfig = TsDefectsConfig()
) -> List[AgentDefectResult]:
    """
    Synchronous wrapper for agent enhancement.

    This function wraps the async agent enhancement logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        processed_results: List of processed TsDefectResult objects
        intent_data: Extracted intent data for context
        config: Configuration for the TsDefects pipeline

    Returns:
        List of AgentDefectResult objects with curator actions
    """
    import asyncio

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _enhance_with_agent_async(processed_results, intent_data, config)
                )
                return future.result()
        else:
            # We can use the existing loop
            return loop.run_until_complete(
                _enhance_with_agent_async(processed_results, intent_data, config)
            )
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(
            _enhance_with_agent_async(processed_results, intent_data, config)
        )
