"""
Agent processing stage for the Pilger processing pipeline.

This stage takes AggregatedResults from the DefectAnalysisPipeline and processes
them through the jk_pilger_new_entries_agent for additional insights and actions.
"""

import json
import logging
import time
from typing import Dict, Any, List

from pipefunc import pipefunc

from gemba_agents.defect_analysis.models.data_models import AggregatedResults
from ..models.data_models import PilgerProcessingConfig
from ..utils import load_and_build_agent_with_placeholders, invoke_agent_async, parse_json_response

logger = logging.getLogger(__name__)


def format_defect_analysis_for_agent(
    defect_analysis: AggregatedResults, 
    format_type: str = "structured"
) -> str:
    """
    Format DefectAnalysisPipeline results for the Pilger agent.
    
    Args:
        defect_analysis: Results from DefectAnalysisPipeline
        format_type: Format type - 'structured' or 'text'
        
    Returns:
        Formatted string for agent input
    """
    if format_type == "text":
        # Simple text format
        return (
            f"Original Input: {defect_analysis.original_input}\n"
            f"Interpreted Meaning: {defect_analysis.intent_data.interpreted_meaning}\n"
            f"Component: {defect_analysis.intent_data.component}\n"
            f"Sub-component: {defect_analysis.intent_data.sub_component}\n"
            f"Issue: {defect_analysis.intent_data.issue}\n"
            f"Found {defect_analysis.total_unique_results} related defects\n"
            f"Root Causes: {', '.join([rc.root_cause_text for rc in defect_analysis.root_causes])}\n"
            f"Corrective Actions: {', '.join([ca.action_text for ca in defect_analysis.corrective_actions])}"
        )
    else:
        # Structured JSON format
        return json.dumps({
            "original_input": defect_analysis.original_input,
            "intent_data": defect_analysis.intent_data.model_dump(),
            "total_unique_results": defect_analysis.total_unique_results,
            "defects": [defect.model_dump() for defect in defect_analysis.defects[:5]],  # Top 5 defects
            "root_causes": [rc.model_dump() for rc in defect_analysis.root_causes],
            "corrective_actions": [ca.model_dump() for ca in defect_analysis.corrective_actions],
            "processing_time_ms": defect_analysis.processing_time_ms
        }, indent=2)


def extract_insights_from_response(agent_response: Any) -> tuple[List[str], List[str], float]:
    """
    Extract insights and actions from agent response.
    
    Args:
        agent_response: Raw response from the agent
        
    Returns:
        Tuple of (insights, actions, confidence_score)
    """
    insights = []
    actions = []
    confidence = 0.0
    
    try:
        # Handle different response formats
        if isinstance(agent_response, dict):
            # Extract insights
            if "insights" in agent_response:
                insights = agent_response["insights"] if isinstance(agent_response["insights"], list) else [agent_response["insights"]]
            elif "analysis" in agent_response:
                insights = [agent_response["analysis"]]
            elif "interpreted_meaning" in agent_response:
                insights = [agent_response["interpreted_meaning"]]

            # Extract actions
            if "recommended_actions" in agent_response:
                actions = agent_response["recommended_actions"] if isinstance(agent_response["recommended_actions"], list) else [agent_response["recommended_actions"]]
            elif "actions" in agent_response:
                actions = agent_response["actions"] if isinstance(agent_response["actions"], list) else [agent_response["actions"]]

            # Extract confidence
            if "confidence_score" in agent_response:
                confidence = float(agent_response["confidence_score"])
            elif "confidence" in agent_response:
                confidence = float(agent_response["confidence"])
        else:
            # Handle non-dict responses (strings, etc.)
            insights = [str(agent_response)]

    except Exception as e:
        logger.warning(f"Error extracting insights from agent response: {e}")
        # Fallback: treat entire response as insight
        insights = [str(agent_response)]
    
    return insights, actions, confidence


@pipefunc(output_name="pilger_processing_result")
async def process_with_pilger_agent(
    defect_analysis: AggregatedResults,
    config: PilgerProcessingConfig
) -> Dict[str, Any]:
    """
    Process DefectAnalysisPipeline results through the jk_pilger_new_entries_agent.
    
    This function takes the output from DefectAnalysisPipeline and processes it
    through the configured Pilger agent for additional insights and actions.
    
    Args:
        defect_analysis: Results from DefectAnalysisPipeline
        config: Configuration for the Pilger processing pipeline
        
    Returns:
        Dictionary containing the processing results
        
    Raises:
        Exception: If agent processing fails
    """
    start_time = time.time()
    agent_start_time = None
    
    try:
        if config.enable_logging:
            logger.info(f"Starting Pilger agent processing for defect analysis with {defect_analysis.total_unique_results} results")
        
        # Prepare custom placeholders for the agent
        # {{ontology}} - DefectAnalysisPipeline results as structured data
        ontology_data = {
            "defects": [defect.model_dump() for defect in defect_analysis.defects],
            "root_causes": [rc.model_dump() for rc in defect_analysis.root_causes],
            "corrective_actions": [ca.model_dump() for ca in defect_analysis.corrective_actions],
            "intent_data": defect_analysis.intent_data.model_dump(),
            "total_unique_results": defect_analysis.total_unique_results
        }

        # {{user_input}} - Original user input text
        user_input_text = defect_analysis.original_input

        # Create custom placeholders dictionary
        custom_placeholders = {
            "ontology": json.dumps(ontology_data, indent=2, ensure_ascii=False),
            "user_input": user_input_text
        }

        if config.enable_logging:
            logger.debug(f"Prepared custom placeholders: ontology data with {len(ontology_data['defects'])} defects, user_input: {user_input_text[:100]}...")

        # Load and build the agent with custom placeholders
        agent, mcp_client, direct_logger = await load_and_build_agent_with_placeholders(
            agent_name=config.agent_name,
            custom_placeholders=custom_placeholders,
            config_path=config.config_path
        )
        
        # Invoke the agent with a simple trigger message
        # The actual data is now passed through placeholders in the prompt
        agent_start_time = time.time()
        trigger_message = "Please analyze the provided defect analysis data and generate new entries as needed."

        # Log the agent request
        system_context = f"Business context:\n\nPrevious step results:\n(none)"
        direct_logger.log_agent_request(agent, system_context, trigger_message)

        agent_response = await invoke_agent_async(
            compiled_agent=agent,
            user_input=trigger_message,
            business_context=""
        )
        agent_execution_time = (time.time() - agent_start_time) * 1000

        # Log the agent response
        direct_logger.log_agent_response(agent_response, {"messages": []})
        
        if config.enable_logging:
            logger.debug(f"Agent response: {agent_response}")
        
        # Parse the agent response
        parsed_response = parse_json_response(agent_response)
        
        # Extract insights and actions
        insights, actions, confidence = extract_insights_from_response(parsed_response)
        
        processing_time = (time.time() - start_time) * 1000
        
        if config.enable_logging:
            logger.info(f"Pilger agent processing completed in {processing_time:.2f}ms")
        
        return {
            "original_defect_analysis": defect_analysis,
            "pilger_agent_response": parsed_response,
            "processed_insights": insights,
            "recommended_actions": actions,
            "confidence_score": confidence if confidence > 0 else None,
            "processing_time_ms": processing_time,
            "agent_execution_time_ms": agent_execution_time,
            "success": True,
            "error_message": None
        }
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        agent_execution_time = (time.time() - agent_start_time) * 1000 if agent_start_time else 0.0
        
        error_msg = f"Pilger agent processing failed after {processing_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        return {
            "original_defect_analysis": defect_analysis,
            "pilger_agent_response": {},
            "processed_insights": [],
            "recommended_actions": [],
            "confidence_score": None,
            "processing_time_ms": processing_time,
            "agent_execution_time_ms": agent_execution_time,
            "success": False,
            "error_message": str(e)
        }
