"""
Agent enhancement stage for the TsDefects pipeline.

This stage takes processed TsDefectResult objects and enhances each one
with curator_action and rationale fields using the jk_pilger_new_entries_agent.
This is adapted from the pilger_processing pipeline.
"""

import json
import logging
import time
from typing import List, Dict, Any

from pipefunc import pipefunc
from vectordb_wrapper.ts_models import TsDefectResult

from gemba_agents.defect_analysis.models.data_models import IntentData
from ..models.data_models import TsDefectsConfig, EnhancedTsDefectResult
from ..utils.agent_utils import load_and_build_agent_with_placeholders, invoke_agent_async, parse_json_response

logger = logging.getLogger(__name__)


async def _enhance_with_agent_async(
    processed_results: List[TsDefectResult],
    intent_data: IntentData,
    config: TsDefectsConfig = TsDefectsConfig()
) -> List[EnhancedTsDefectResult]:
    """
    Enhance each TsDefectResult with curator_action and rationale using the agent.
    
    This function processes each defect result through the jk_pilger_new_entries_agent
    to generate curator actions and rationale for each defect.
    
    Args:
        processed_results: List of processed TsDefectResult objects
        intent_data: Extracted intent data for context
        config: Configuration for the TsDefects pipeline
        
    Returns:
        List of EnhancedTsDefectResult objects with curator actions
        
    Raises:
        Exception: If agent enhancement fails
    """
    start_time = time.time()
    
    try:
        if config.enable_logging:
            logger.info(f"Starting agent enhancement for {len(processed_results)} defect results")
        
        if not processed_results:
            logger.info("No results to enhance, returning empty list")
            return []
        
        # Prepare data for the agent
        # Format all defects and intent data for agent processing
        defects_data = [result.model_dump() for result in processed_results]
        
        # Create custom placeholders for the agent
        custom_placeholders = {
            "ontology": json.dumps({
                "defects": defects_data,
                "total_results": len(defects_data)
            }, indent=2, ensure_ascii=False),
            "user_intent": intent_data.model_dump()
        }

        if config.enable_logging:
            logger.debug(f"Prepared custom placeholders with {len(defects_data)} defects")

        # Load and build the agent with custom placeholders
        agent, mcp_client, direct_logger = await load_and_build_agent_with_placeholders(
            agent_name=config.processing_agent_name,
            custom_placeholders=custom_placeholders,
            config_path=config.config_path
        )
        
        try:
            # Invoke the agent with a trigger message
            trigger_message = "Analyze the provided defect search results and generate curator actions with rationale for each defect based on the user intent."

            # Log the agent request
            system_context = f"Business context:\n\nPrevious step results:\n(none)"
            direct_logger.log_agent_request(agent, system_context, trigger_message)

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
            
            # Create enhanced results
            enhanced_results = _create_enhanced_results(
                processed_results, 
                parsed_response, 
                config
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            if config.enable_logging:
                logger.info(
                    f"Agent enhancement completed in {processing_time:.2f}ms. "
                    f"Enhanced {len(enhanced_results)} defect results"
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
        error_msg = f"Agent enhancement failed after {processing_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        # Return enhanced results with error information
        return _create_fallback_enhanced_results(processed_results, str(e))


def _create_enhanced_results(
    original_results: List[TsDefectResult],
    agent_response: Dict[str, Any],
    config: TsDefectsConfig
) -> List[EnhancedTsDefectResult]:
    """
    Create enhanced results from original results and agent response.
    
    Args:
        original_results: Original TsDefectResult objects
        agent_response: Parsed agent response
        config: Pipeline configuration
        
    Returns:
        List of EnhancedTsDefectResult objects
    """
    enhanced_results = []
    
    try:
        # Try to extract enhancement data from agent response
        # The agent response should contain curator actions and rationale for each defect
        enhancements = _extract_enhancements_from_response(agent_response, len(original_results))
        
        for i, original_result in enumerate(original_results):
            # Get enhancement data for this result (if available)
            enhancement = enhancements.get(i, {})
            
            # Create enhanced result
            enhanced_result = EnhancedTsDefectResult(
                **original_result.model_dump(),
                curator_action=enhancement.get("curator_action", "REVIEW_REQUIRED"),
                rationale=enhancement.get("rationale", "Automated analysis completed")
            )
            
            enhanced_results.append(enhanced_result)
            
    except Exception as e:
        logger.warning(f"Error creating enhanced results: {e}")
        # Fallback: create enhanced results with default values
        enhanced_results = _create_fallback_enhanced_results(original_results, str(e))
    
    return enhanced_results


def _extract_enhancements_from_response(
    agent_response: Dict[str, Any],
    expected_count: int
) -> Dict[int, Dict[str, str]]:
    """
    Extract enhancement data from curator agent response.

    Args:
        agent_response: Parsed curator agent response
        expected_count: Expected number of enhancements

    Returns:
        Dictionary mapping result index to enhancement data
    """
    enhancements = {}

    try:
        # Handle new curator agent response format
        if "defect_enhancements" in agent_response and isinstance(agent_response["defect_enhancements"], list):
            # New format: {"defect_enhancements": [{"defect_code": "...", "curator_action": "...", "rationale": "..."}, ...]}
            defect_enhancements = agent_response["defect_enhancements"]
            for i, enhancement in enumerate(defect_enhancements):
                if i < expected_count:
                    enhancements[i] = {
                        "curator_action": enhancement.get("curator_action", "REVIEW_REQUIRED"),
                        "rationale": enhancement.get("rationale", "Automated analysis completed")
                    }

        # Legacy formats for backward compatibility
        elif "enhancements" in agent_response and isinstance(agent_response["enhancements"], list):
            # Format: {"enhancements": [{"curator_action": "...", "rationale": "..."}, ...]}
            for i, enhancement in enumerate(agent_response["enhancements"]):
                if i < expected_count:
                    enhancements[i] = enhancement

        elif "results" in agent_response and isinstance(agent_response["results"], list):
            # Format: {"results": [{"curator_action": "...", "rationale": "..."}, ...]}
            for i, result in enumerate(agent_response["results"]):
                if i < expected_count:
                    enhancements[i] = result

        elif "curator_action" in agent_response:
            # Single enhancement for all results
            single_enhancement = {
                "curator_action": agent_response.get("curator_action", "REVIEW_REQUIRED"),
                "rationale": agent_response.get("rationale", "Automated analysis completed")
            }
            for i in range(expected_count):
                enhancements[i] = single_enhancement

        else:
            # Default enhancement for all results
            default_enhancement = {
                "curator_action": "REVIEW_REQUIRED",
                "rationale": "Agent response format not recognized"
            }
            for i in range(expected_count):
                enhancements[i] = default_enhancement

    except Exception as e:
        logger.warning(f"Error extracting enhancements: {e}")
        # Fallback to default enhancements
        default_enhancement = {
            "curator_action": "REVIEW_REQUIRED",
            "rationale": f"Enhancement extraction failed: {str(e)}"
        }
        for i in range(expected_count):
            enhancements[i] = default_enhancement

    return enhancements


def _create_fallback_enhanced_results(
    original_results: List[TsDefectResult],
    error_message: str
) -> List[EnhancedTsDefectResult]:
    """
    Create fallback enhanced results when agent processing fails.
    
    Args:
        original_results: Original TsDefectResult objects
        error_message: Error message to include in rationale
        
    Returns:
        List of EnhancedTsDefectResult objects with fallback values
    """
    enhanced_results = []
    
    for result in original_results:
        enhanced_result = EnhancedTsDefectResult(
            **result.model_dump(),
            curator_action="REVIEW_REQUIRED",
            rationale=f"Agent enhancement failed: {error_message}"
        )
        enhanced_results.append(enhanced_result)
    
    return enhanced_results


@pipefunc(output_name="enhanced_results", cache=True)
def enhance_with_agent(
    processed_results: List[TsDefectResult],
    intent_data: IntentData,
    config: TsDefectsConfig = TsDefectsConfig()
) -> List[EnhancedTsDefectResult]:
    """
    Synchronous wrapper for agent enhancement.

    This function wraps the async agent enhancement logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        processed_results: List of processed TsDefectResult objects
        intent_data: Extracted intent data for context
        config: Configuration for the TsDefects pipeline

    Returns:
        List of EnhancedTsDefectResult objects with curator actions
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
