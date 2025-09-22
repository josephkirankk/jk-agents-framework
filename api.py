"""
FastAPI web server for jk-agents system.

Provides HTTP endpoints to interact with the multi-agent system.
"""
from __future__ import annotations

import logging
import base64
import mimetypes
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.config import AppConfig, AgentConfig
from app.main import load_app_config, build_agents_map
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.mcp_loader import close_mcp_client
from app.agent_builder import build_react_agent
from app.direct_agent_logger import create_direct_agent_logger
from app.thread_manager import get_or_create_thread_id

# Import structured models for defect analysis
from gemba_agents.defect_analysis.models.data_models import RootCause, CorrectiveAction
from app.checkpointer_manager import get_memory_stats, clear_thread_memory, reset_all_memory

# Import defect analysis pipeline
from gemba_agents.defect_analysis import DefectAnalysisPipeline, DefectAnalysisConfig

# Import pilger processing pipeline
from gemba_agents.pilger_processing import PilgerProcessingPipeline, PilgerProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("api")

# FastAPI app instance
app = FastAPI(
    title="JK-Agents API",
    description="Multi-agent system with supervisor planning and execution",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global configuration - will be loaded on startup
_app_config: Optional[AppConfig] = None


async def download_file_from_openai(file_id: str) -> bytes:
    """
    Download file content from OpenAI/Azure OpenAI using file ID.

    Args:
        file_id: The file ID from OpenAI

    Returns:
        The file content as bytes
    """
    import os
    from openai import OpenAI

    # Try to import Azure components, fall back to regular OpenAI if not available
    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        azure_available = True
    except ImportError:
        log.warning("Azure SDK not available, falling back to regular OpenAI")
        azure_available = False

    # Determine which client to use based on environment variables
    if azure_available and os.getenv("AZURE_OPENAI_ENDPOINT"):
        # Use Azure OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            # API Key authentication
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-10-21",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            # Token-based authentication
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            client = AzureOpenAI(
                azure_ad_token_provider=token_provider,
                api_version="2024-10-21",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
    else:
        # Use regular OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Download the file content
    file_response = client.files.content(file_id)
    return file_response.read()


async def upload_file_to_openai(file_content: bytes, filename: str, purpose: str = "vision") -> str:
    """
    Upload a file to OpenAI/Azure OpenAI and return the file ID.

    Args:
        file_content: The file content as bytes
        filename: The original filename
        purpose: The purpose for the file (vision, assistants, etc.)

    Returns:
        The file ID from OpenAI
    """
    import os
    from openai import OpenAI

    # Try to import Azure components, fall back to regular OpenAI if not available
    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        azure_available = True
    except ImportError:
        log.warning("Azure SDK not available, falling back to regular OpenAI")
        azure_available = False

    # Determine which client to use based on environment variables
    if azure_available and os.getenv("AZURE_OPENAI_ENDPOINT"):
        # Use Azure OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY"):
            # API Key authentication
            client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version="2024-10-21",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
        else:
            # Token-based authentication
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            client = AzureOpenAI(
                azure_ad_token_provider=token_provider,
                api_version="2024-10-21",
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
    else:
        # Use regular OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Create a temporary file to upload
    import io

    # Use BytesIO to avoid file system issues on Windows
    file_like = io.BytesIO(file_content)
    file_like.name = filename  # Set name attribute for OpenAI API

    # Upload the file directly from memory
    file_response = client.files.create(
        file=file_like,
        purpose=purpose
    )
    return file_response.id


async def run_direct_agent_with_files(
    agent_name: str,
    user_input: str,
    app_cfg: AppConfig,
    file_ids: List[str],
    file_info: List[Dict[str, Any]],
    config_path: Optional[str] = None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a direct agent with file attachments.

    This is a modified version of run_direct_agent_api that handles file attachments
    by constructing multimodal messages with file references.
    """
    from langchain_core.runnables import RunnableConfig

    # Initialize logger
    logger = create_direct_agent_logger(
        agent_name=agent_name,
        user_input=user_input,
        business_context=app_cfg.business_context or ""
    )

    success = False
    error_message = ""

    try:
        default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")

        # Find agent config
        target: Optional[AgentConfig] = next(
            (a for a in app_cfg.agents if a.name == agent_name), None
        )
        if not target:
            raise ValueError(f"Agent '{agent_name}' not found in config")

        compiled, mcp_client = await build_react_agent(
            target,
            default_model,
            business_context=app_cfg.business_context or "",
            original_user_question=user_input,
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=True,
            llm_payload_logger=logger.get_llm_payload_logger(),
            default_temperature=app_cfg.temperature,
        )

        try:
            system_context = (
                "Business context:\n"
                f"{app_cfg.business_context or ''}\n\n"
                "Previous step results:\n(none)"
            )

            # Create multimodal message content
            message_content = []

            # Add text content
            message_content.append({
                "type": "text",
                "text": user_input
            })

            # Add file references for non-CSV files (CSV data is already in user_input)
            for file_id, info in zip(file_ids, file_info):
                mime_type = info.get("mime_type", "")
                filename = info.get("filename", "")

                if info.get("purpose") == "local_processing":
                    # CSV files are already processed and included in user_input
                    continue
                elif mime_type and mime_type.startswith("image/"):
                    # For images, use image_url type with file_id
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"file_id": file_id}
                    })
                else:
                    # For other files, reference them in text
                    message_content.append({
                        "type": "text",
                        "text": f"Please analyze the attached file: {filename} (File ID: {file_id})"
                    })

            # Log the request with file information
            logger.log_agent_request(
                compiled_agent=compiled,
                system_context=system_context,
                user_task=user_input,
                file_info=file_info
            )

            # Create the message with multimodal content
            # human_message = HumanMessage(content=message_content)  # For future use

            state = {
                "messages": [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": message_content},
                ]
            }
            # Get or create thread ID
            actual_thread_id = get_or_create_thread_id(thread_id)
            config: RunnableConfig = {"configurable": {"thread_id": actual_thread_id}}

            try:
                out = await compiled.ainvoke(state, config=config)
            except AttributeError:
                out = compiled.invoke(state, config=config)

            msgs = out.get("messages", [])
            if msgs:
                # LangGraph messages are objects with .content attribute
                last_msg = msgs[-1]
                text = getattr(last_msg, "content", "")
            else:
                text = ""

            # Log the response
            logger.log_agent_response(response_text=text, raw_output=out)
            success = True

            return {
                "success": True,
                "response": text,
                "agent_name": agent_name,
                "raw_output": out,
                "log_file": logger.get_log_file_path(),
                "llm_payload_log_file": logger.get_llm_payload_log_path(),
                "thread_id": actual_thread_id,
            }

        finally:
            await close_mcp_client(mcp_client)

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        # Log execution summary
        logger.log_execution_summary(success=success, error_message=error_message)


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    input: str = Field(..., description="User question or prompt", min_length=1)
    config_path: Optional[str] = Field(
        None, description="Optional path to config file"
    )
    raw_output: bool = Field(
        False,
        description="If True, returns only the raw agent response content "
                    "as plain text with no JSON wrapping or metadata"
    )
    thread_id: Optional[str] = Field(
        None,
        description="Optional thread ID for conversation continuity. "
                    "If not provided, a new thread will be created."
    )
    custom_placeholders: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional custom placeholders to use in agent prompts. "
                    "These will be available as {{placeholder_name}} in templates."
    )


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    success: bool = Field(..., description="Whether the query was successful")
    response: str = Field(..., description="The human responder's final answer")
    error: Optional[str] = Field(
        None, description="Error message if success is False"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the execution"
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Raw unprocessed execution result when raw_output=True"
    )
    thread_id: str = Field(
        ..., description="Thread ID used for this conversation"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")


class WorkerRequest(BaseModel):
    """Request model for worker endpoint."""
    agent_name: str = Field(
        ..., description="Name of the agent/worker to execute", min_length=1
    )
    input: str = Field(
        ..., description="User question or prompt for the agent", min_length=1
    )
    config_path: Optional[str] = Field(
        None, description="Optional path to config file"
    )
    raw_output: bool = Field(
        False,
        description="If True, returns only the raw agent response content "
                    "as plain text with no JSON wrapping or metadata"
    )
    thread_id: Optional[str] = Field(
        None,
        description="Optional thread ID for conversation continuity. "
                    "If not provided, a new thread will be created."
    )
    custom_placeholders: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional custom placeholders to use in agent prompts. "
                    "These will be available as {{placeholder_name}} in templates."
    )


class WorkerResponse(BaseModel):
    """Response model for worker endpoint."""
    success: bool = Field(
        ..., description="Whether the worker execution was successful"
    )
    response: str = Field(..., description="The agent's response")
    agent_name: str = Field(
        ..., description="Name of the agent that was executed"
    )
    error: Optional[str] = Field(
        None, description="Error message if success is False"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the execution"
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Raw unprocessed execution result when raw_output=True"
    )
    thread_id: str = Field(
        ..., description="Thread ID used for this conversation"
    )


# Submit Selection API Models
class SubmitRootCause(BaseModel):
    """Root cause model for submit selection."""
    root_cause_code: str = Field(..., description="Unique identifier for the root cause")
    root_cause_text: str = Field(..., description="Human-readable description of the root cause")
    is_primary: bool = Field(..., description="Boolean indicating if this is the primary/recommended root cause")


class SubmitCorrectiveAction(BaseModel):
    """Corrective action model for submit selection."""
    action_code: str = Field(..., description="Unique identifier for the corrective action")
    action_text: str = Field(..., description="Human-readable description of the corrective action")
    is_primary: bool = Field(..., description="Boolean indicating if this is the primary/recommended corrective action")


class SelectedPair(BaseModel):
    """Selected pair model containing root cause and corrective action."""
    root_cause: SubmitRootCause = Field(..., description="Root cause object")
    corrective_action: SubmitCorrectiveAction = Field(..., description="Corrective action object")
    pair_id: str = Field(..., description="Unique identifier for the pair")


class SelectedDefect(BaseModel):
    """Selected defect model for submit selection."""
    defect_code: str = Field(..., description="Unique identifier code for the defect")
    defect_text: str = Field(..., description="Human-readable description of the defect")
    confidence_score: float = Field(..., description="AI confidence score (0.0 to 1.0) for the defect identification", ge=0.0, le=1.0)
    mapping_status: str = Field(..., description="Status of defect mapping")
    curator_action: str = Field(..., description="Recommended curator action")


class AnalysisMetadata(BaseModel):
    """Analysis metadata model for submit selection."""
    agent_name: str = Field(..., description="Name of the AI agent used for analysis")
    config_path: str = Field(..., description="Path to the configuration file used")
    submission_source: str = Field(..., description="Source component identifier")
    total_pairs_selected: int = Field(..., description="Total number of pairs selected by the user", ge=0)


class SubmitSelectionRequest(BaseModel):
    """Request model for submit selection endpoint."""
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp when the submission was made")
    original_input: str = Field(..., description="The original user input text that was analyzed")
    remarks: Optional[str] = Field(None, description="Optional user comments or additional context about the selection", max_length=500)
    selected_defect: SelectedDefect = Field(..., description="Object containing the defect selected by the user")
    selected_pairs: List[SelectedPair] = Field(..., description="Array of root cause and corrective action pairs selected by the user", min_items=1)
    analysis_metadata: AnalysisMetadata = Field(..., description="Metadata about the analysis session")

    @field_validator('remarks')
    @classmethod
    def validate_remarks(cls, v):
        if v is not None:
            return v.strip()
        return v

    @field_validator('selected_pairs')
    @classmethod
    def validate_selected_pairs(cls, v):
        if not v:
            raise ValueError("At least one pair must be selected")

        # Check for unique pair_ids
        pair_ids = [pair.pair_id for pair in v]
        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("pair_id must be unique within the selected_pairs array")

        # Check that at least one primary pair exists
        has_primary = any(pair.root_cause.is_primary and pair.corrective_action.is_primary for pair in v)
        if not has_primary:
            raise ValueError("At least one pair should have both is_primary: true for root_cause and corrective_action")

        return v

    @model_validator(mode='after')
    def validate_total_pairs_selected(self):
        actual_count = len(self.selected_pairs)
        if self.analysis_metadata.total_pairs_selected != actual_count:
            raise ValueError(f"total_pairs_selected ({self.analysis_metadata.total_pairs_selected}) must match actual array length ({actual_count})")
        return self


class SubmitSelectionResponse(BaseModel):
    """Success response model for submit selection endpoint."""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Success message")
    submission_id: str = Field(..., description="Unique identifier for the submission")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp")
    processed_pairs: int = Field(..., description="Number of pairs processed")


class ErrorResponse(BaseModel):
    """Error response model for submit selection endpoint."""
    status: str = Field(..., description="Response status")
    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Error message")
    timestamp: Optional[str] = Field(None, description="ISO 8601 formatted timestamp")
    details: Optional[Dict[str, str]] = Field(None, description="Additional error details")


class ConsolidatedResponsesRequest(BaseModel):
    """Request model for consolidated responses endpoint."""
    start_date: Optional[str] = Field(
        None,
        description="Start date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). "
                    "If not provided, returns all submissions."
    )
    end_date: Optional[str] = Field(
        None,
        description="End date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). "
                    "If not provided, returns all submissions."
    )

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """Validate that the date is in proper ISO 8601 format."""
        if v is None:
            return v
        try:
            # Try to parse the date to validate format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(
                "Date must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)"
            )

    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate that start_date is before end_date if both provided."""
        if self.start_date and self.end_date:
            try:
                start = datetime.fromisoformat(
                    self.start_date.replace('Z', '+00:00')
                )
                end = datetime.fromisoformat(
                    self.end_date.replace('Z', '+00:00')
                )
                if start > end:
                    raise ValueError(
                        "start_date must be before or equal to end_date"
                    )
            except ValueError as e:
                if "start_date must be before" in str(e):
                    raise e
                # Re-raise date format errors
                raise ValueError(
                    "Invalid date format in date range validation"
                )
        return self


class ConsolidatedResponsesResponse(BaseModel):
    """Response model for consolidated responses endpoint."""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    query_metadata: Dict[str, Any] = Field(
        ..., description="Metadata about the query"
    )
    submissions: List[Dict[str, Any]] = Field(
        ..., description="List of all matching submissions"
    )
    total_count: int = Field(
        ..., description="Total number of submissions returned"
    )


# Defect Analysis API Models
class DefectAnalysisRequest(BaseModel):
    """Request model for defect analysis endpoint."""
    user_input: str = Field(
        ...,
        description="Raw user input describing equipment issues",
        min_length=1,
        max_length=1000
    )
    top_n: Optional[int] = Field(
        10,
        description="Number of top results to return from vector search",
        ge=1,
        le=50
    )
    min_score: Optional[float] = Field(
        0.6,
        description="Minimum similarity score for vector search results",
        ge=0.0,
        le=1.0
    )
    enable_logging: Optional[bool] = Field(
        True,
        description="Enable detailed logging for the analysis"
    )
    enable_caching: Optional[bool] = Field(
        True,
        description="Enable caching for repeated queries"
    )
    parallel_search: Optional[bool] = Field(
        True,
        description="Enable parallel vector search execution"
    )

    @field_validator('user_input')
    @classmethod
    def validate_user_input(cls, v):
        """Validate and clean user input."""
        if v:
            return v.strip()
        return v


class DefectAnalysisResponse(BaseModel):
    """Response model for defect analysis endpoint."""
    success: bool = Field(..., description="Whether the analysis was successful")
    original_input: str = Field(..., description="Original user input")
    intent_data: Dict[str, Any] = Field(
        ..., description="Extracted intent information"
    )
    total_unique_results: int = Field(
        ..., description="Number of unique defects found"
    )
    defects: List[Dict[str, Any]] = Field(
        ..., description="List of matching defects with details"
    )
    root_causes: List[RootCause] = Field(
        ..., description="Consolidated root causes with structured format"
    )
    corrective_actions: List[CorrectiveAction] = Field(
        ..., description="Consolidated corrective actions with structured format"
    )
    processing_time_ms: float = Field(
        ..., description="Total processing time in milliseconds"
    )
    error: Optional[str] = Field(
        None, description="Error message if analysis failed"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the analysis"
    )

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )


# Enhanced Defect Analysis with Pilger Processing API Models
class EnhancedDefectAnalysisRequest(BaseModel):
    """Request model for enhanced defect analysis with Pilger processing endpoint."""
    user_input: str = Field(
        ...,
        description="Raw user input describing equipment issues",
        min_length=1,
        max_length=1000
    )
    # Defect analysis configuration
    top_n: Optional[int] = Field(
        10,
        description="Number of top results to return from vector search",
        ge=1,
        le=50
    )
    min_score: Optional[float] = Field(
        0.6,
        description="Minimum similarity score for vector search results",
        ge=0.0,
        le=1.0
    )
    enable_logging: Optional[bool] = Field(
        True,
        description="Enable detailed logging for the analysis"
    )
    enable_caching: Optional[bool] = Field(
        True,
        description="Enable caching for repeated queries"
    )
    parallel_search: Optional[bool] = Field(
        True,
        description="Enable parallel vector search execution"
    )
    # Pilger processing configuration
    pilger_timeout_seconds: Optional[int] = Field(
        120,
        description="Timeout for Pilger agent processing in seconds",
        ge=30,
        le=300
    )
    pilger_format: Optional[str] = Field(
        "structured",
        description="Format for agent input: 'structured' or 'text'",
        pattern="^(structured|text)$"
    )
    skip_pilger_processing: Optional[bool] = Field(
        False,
        description="Skip Pilger processing and return only defect analysis results"
    )

    @field_validator('user_input')
    @classmethod
    def validate_user_input(cls, v):
        """Validate and clean user input."""
        if v:
            return v.strip()
        return v


class EnhancedDefectAnalysisResponse(BaseModel):
    """Response model for enhanced defect analysis with Pilger processing endpoint."""
    success: bool = Field(..., description="Whether the complete analysis was successful")
    original_input: str = Field(..., description="Original user input")

    # Defect analysis results
    defect_analysis: Dict[str, Any] = Field(
        ..., description="Complete defect analysis results"
    )

    # Pilger processing results (optional if skipped or failed)
    pilger_processing: Optional[Dict[str, Any]] = Field(
        None, description="Pilger processing results if successful"
    )

    # Combined insights and actions
    total_insights: List[str] = Field(
        ..., description="Combined insights from both stages"
    )
    total_recommended_actions: List[str] = Field(
        ..., description="Combined recommended actions from both stages"
    )

    # Processing metadata
    processing_stages: Dict[str, Any] = Field(
        ..., description="Status and timing for each processing stage"
    )
    total_processing_time_ms: float = Field(
        ..., description="Total processing time for both stages in milliseconds"
    )

    # Error handling
    error: Optional[str] = Field(
        None, description="Error message if analysis failed"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Warning messages from processing"
    )

    # Metadata
    metadata: Dict[str, Any] = Field(
        ..., description="Additional metadata about the complete analysis"
    )


async def extract_human_response(result: Dict[str, Any]) -> str:
    """
    Extract the human responder's final answer from the execution result.

    Args:
        result: The result dictionary from execute_plan

    Returns:
        The final human response text
    """
    try:
        # Look for the human_response_agent step in the results
        steps = result.get("steps", {})

        # Find the last step that was executed by human_response_agent
        human_response = None
        for step_id, step_data in steps.items():
            if (step_data.get("agent") == "human_response_agent" and
                    step_data.get("ok", False)):
                # Use 'raw' field which contains the actual response text
                human_response = step_data.get("raw", "")

        if human_response:
            return human_response.strip()

        # Fallback: look for any completed step's response
        for step_id, step_data in steps.items():
            if step_data.get("ok", False):
                response = step_data.get("raw", "")
                if response:
                    human_response = response

        if human_response:
            return human_response.strip()
        else:
            return "No response generated"

    except Exception as e:
        log.error(f"Error extracting human response: {e}")
        return f"Error extracting response: {str(e)}"


async def run_direct_agent_api(
    agent_name: str,
    user_input: str,
    app_cfg: AppConfig,
    config_path: Optional[str] = None,
    thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a direct agent and return structured results for API use.

    This is a modified version of run_direct_agent that returns data
    instead of printing.
    """
    from langchain_core.runnables import RunnableConfig

    # Initialize logger
    logger = create_direct_agent_logger(
        agent_name=agent_name,
        user_input=user_input,
        business_context=app_cfg.business_context or ""
    )

    success = False
    error_message = ""

    try:
        default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")

        # Find agent config
        target: Optional[AgentConfig] = next(
            (a for a in app_cfg.agents if a.name == agent_name), None
        )
        if not target:
            raise ValueError(f"Agent '{agent_name}' not found in config")

        compiled, mcp_client = await build_react_agent(
            target,
            default_model,
            business_context=app_cfg.business_context or "",
            original_user_question=user_input,
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=True,
            llm_payload_logger=logger.get_llm_payload_logger(),
            default_temperature=app_cfg.temperature,
        )

        try:
            system_context = (
                "Business context:\n"
                f"{app_cfg.business_context or ''}\n\n"
                "Previous step results:\n(none)"
            )

            # Log the request
            logger.log_agent_request(
                compiled_agent=compiled,
                system_context=system_context,
                user_task=user_input
            )

            state = {
                "messages": [
                    {"role": "system", "content": system_context},
                    {"role": "user", "content": user_input},
                ]
            }
            # Get or create thread ID
            actual_thread_id = get_or_create_thread_id(thread_id)
            config: RunnableConfig = {"configurable": {"thread_id": actual_thread_id}}

            try:
                out = await compiled.ainvoke(state, config=config)
            except AttributeError:
                out = compiled.invoke(state, config=config)

            msgs = out.get("messages", [])
            if msgs:
                # LangGraph messages are objects with .content attribute
                last_msg = msgs[-1]
                text = getattr(last_msg, "content", "")
            else:
                text = ""

            # Log the response
            logger.log_agent_response(response_text=text, raw_output=out)
            success = True

            return {
                "success": True,
                "response": text,
                "agent_name": agent_name,
                "raw_output": out,
                "log_file": logger.get_log_file_path(),
                "llm_payload_log_file": logger.get_llm_payload_log_path(),
                "thread_id": actual_thread_id,
            }

        finally:
            await close_mcp_client(mcp_client)

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        # Log execution summary
        logger.log_execution_summary(success=success, error_message=error_message)


async def run_supervised_api(
    user_input: str, app_cfg: AppConfig, config_path: Optional[str] = None, thread_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the supervised multi-agent system and return structured results.

    This is a modified version of run_supervised that returns data
    instead of printing.
    """
    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")

    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_cfg.supervisor,
        app_cfg.agents,
        default_model,
        app_cfg.business_context or "",
        original_user_question=user_input,
        config_path=config_path,
        default_temperature=app_cfg.temperature,
    )

    # Build workers
    agents_map, mcp_clients = await build_agents_map(
        app_cfg, user_input=user_input, config_path=config_path
    )

    try:
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=user_input,
            business_context=app_cfg.business_context or "",
            default_model_for_verifier=default_model,
            agents_configs=app_cfg.agents,
            default_model=default_model,
            thread_id=thread_id,
        )
        return result

    finally:
        # Cleanup MCP clients
        for client in mcp_clients.values():
            await close_mcp_client(client)


@app.on_event("startup")
async def startup_event():
    """Load default configuration on startup."""
    global _app_config
    try:
        _app_config = load_app_config()
        log.info("Default configuration loaded successfully")
    except Exception as e:
        log.warning(f"Could not load default configuration: {e}")
        _app_config = None


@app.get("/", response_model=Dict[str, Any])
async def root():
    """
    Default root endpoint that returns API status and basic information.

    Returns:
        Dict containing API status, version, available endpoints, and
        service health
    """
    import datetime

    # Check if configuration is loaded
    config_status = "loaded" if _app_config is not None else "not_loaded"

    # Get available agent names if config is loaded
    available_agents = []
    if _app_config:
        available_agents = [agent.name for agent in _app_config.agents]

    return {
        "status": "success",
        "message": "JK-Agents API is running and live",
        "service": "jk-agents",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "config_status": config_status,
        "available_agents": available_agents,
        "endpoints": {
            "health": "/health - Health check endpoint",
            "query": "/query - Main multi-agent query endpoint",
            "query_form": "/query/form - Form-based query endpoint",
            "worker": "/worker - Direct agent execution endpoint",
            "worker_upload": "/worker/upload - Agent execution with files",
            "defect_analysis": "/defect-analysis - Defect analysis pipeline endpoint",
            "defect_analysis_form": "/defect-analysis/form - Form-based defect analysis endpoint",
            "enhanced_defect_analysis": "/defect-analysis-with-pilger - Enhanced defect analysis with Pilger processing",
            "enhanced_defect_analysis_form": "/defect-analysis-with-pilger/form - Form-based enhanced defect analysis",
            "submit_selection": "/submit-selection - Submit defect analysis selections",
            "consolidated_responses": "/consolidated-responses - Get consolidated user responses with date filtering",
            "consolidated_responses_form": "/consolidated-responses/form - Form-based consolidated responses endpoint",
            "docs": "/docs - Interactive API documentation",
            "redoc": "/redoc - Alternative API documentation"
        },
        "documentation": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics from the global checkpointer."""
    try:
        stats = get_memory_stats()
        return {
            "status": "success",
            "memory_stats": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        log.error(f"Error getting memory stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


@app.post("/query/form")
async def query_form_endpoint(
    input: str = Form(..., description="User question or prompt",
                      min_length=1),
    config_path: Optional[str] = Form(None,
                                      description="Optional path to config file"),
    raw_output: bool = Form(False,
                            description="If True, returns only raw response"),
    thread_id: Optional[str] = Form(None,
                                    description="Optional thread ID for conversation continuity")
):
    """
    Query endpoint that accepts form data instead of JSON.

    Args:
        input: User question or prompt
        config_path: Optional path to config file
        raw_output: If True, returns only raw response as plain text

    Returns:
        QueryResponse with the human responder's final answer
    """
    # Convert form data to QueryRequest object
    request = QueryRequest(
        input=input,
        config_path=config_path,
        raw_output=raw_output,
        thread_id=thread_id
    )

    # Use the existing query logic
    return await query_endpoint(request)


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Main query endpoint that processes user input through multi-agent system.

    Args:
        request: QueryRequest containing user input and optional config path

    Returns:
        QueryResponse with the human responder's final answer
    """
    try:
        # Load configuration
        if request.config_path:
            try:
                app_cfg = load_app_config(Path(request.config_path))
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load config from {request.config_path}: {str(e)}"
                )
        else:
            if _app_config is None:
                raise HTTPException(
                    status_code=500,
                    detail="No default configuration available. Please provide config_path."
                )
            app_cfg = _app_config

        # Get or create thread ID
        thread_id = get_or_create_thread_id(request.thread_id)
        log.info(f"Using thread ID: {thread_id}")

        # Execute the multi-agent system
        log.info(f"Processing query: {request.input[:100]}...")
        log.info(f"Raw output requested: {request.raw_output}")
        result = await run_supervised_api(
            request.input, app_cfg, request.config_path, thread_id
        )

        # Prepare metadata
        metadata = {
            "total_steps": len(result.get("steps", {})),
            "execution_time": result.get("execution_time"),
            "model_used": app_cfg.models.get("default", "unknown")
        }

        if request.raw_output:
            # Return raw text content only - no JSON wrapping
            log.info("Returning raw text content without JSON wrapping")
            human_response = await extract_human_response(result)
            # Return plain text response directly
            return PlainTextResponse(
                content=human_response, media_type="text/plain"
            )
        else:
            # Extract human response for formatted output
            human_response = await extract_human_response(result)
            return QueryResponse(
                success=True,
                response=human_response,
                metadata=metadata,
                thread_id=thread_id
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except BaseExceptionGroup as e:
        # Handle Python 3.11+ TaskGroup exceptions
        log.error(f"TaskGroup error processing query: {e}")
        log.error(f"TaskGroup error type: {type(e)}")
        log.error(f"TaskGroup error args: {e.args}")

        # Extract underlying exceptions for better error messages
        underlying_errors = []
        if hasattr(e, 'exceptions'):
            log.error(f"TaskGroup has {len(e.exceptions)} underlying exceptions:")
            for i, exc in enumerate(e.exceptions):
                log.error(f"  Exception {i}: {type(exc).__name__}: {str(exc)}")
                underlying_errors.append(f"{type(exc).__name__}: {str(exc)}")

        if underlying_errors:
            error_msg = "Execution failed: " + "; ".join(underlying_errors)
        else:
            error_msg = f"Execution failed with TaskGroup error: {str(e)}"

        return QueryResponse(
            success=False,
            response="",
            error=error_msg,
            thread_id=thread_id if 'thread_id' in locals() else get_or_create_thread_id()
        )
    except Exception as e:
        log.error(f"Error processing query: {e}")
        return QueryResponse(
            success=False,
            response="",
            error=str(e),
            thread_id=thread_id if 'thread_id' in locals() else get_or_create_thread_id()
        )


@app.post("/worker", response_model=WorkerResponse)
async def worker_endpoint(request: WorkerRequest):
    """
    Direct worker endpoint that executes a specific agent without planning.

    Args:
        request: WorkerRequest containing agent name, input, and optional config

    Returns:
        WorkerResponse with the agent's direct response
    """
    try:
        # Load configuration
        if request.config_path:
            try:
                app_cfg = load_app_config(Path(request.config_path))
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load config from {request.config_path}: {str(e)}"
                )
        else:
            if _app_config is None:
                raise HTTPException(
                    status_code=500,
                    detail="No default configuration available. Please provide config_path."
                )
            app_cfg = _app_config

        # Validate agent exists
        agent_names = [agent.name for agent in app_cfg.agents]
        if request.agent_name not in agent_names:
            # Check if agent exists in other config files
            config_suggestions = []
            config_dir = Path("config")
            if config_dir.exists():
                for config_file in config_dir.glob("*.yaml"):
                    try:
                        other_cfg = load_app_config(config_file)
                        other_agent_names = [a.name for a in other_cfg.agents]
                        if request.agent_name in other_agent_names:
                            config_suggestions.append(str(config_file))
                    except Exception:
                        continue

            error_msg = (f"Agent '{request.agent_name}' not found in current config. "
                         f"Available agents: {', '.join(agent_names)}")
            if config_suggestions:
                error_msg += (f". However, '{request.agent_name}' was found in: "
                              f"{', '.join(config_suggestions)}")

            raise HTTPException(status_code=400, detail=error_msg)

        # Get or create thread ID
        thread_id = get_or_create_thread_id(request.thread_id)
        log.info(f"Using thread ID: {thread_id}")

        # Execute the agent directly
        log.info(f"Executing agent '{request.agent_name}' with input: {request.input[:100]}...")
        result = await run_direct_agent_api(
            request.agent_name, request.input, app_cfg, request.config_path, thread_id
        )

        # Prepare metadata
        metadata = {
            "agent_name": request.agent_name,
            "model_used": app_cfg.models.get("default", "unknown"),
            "business_context": bool(app_cfg.business_context)
        }

        if request.raw_output:
            # Return raw text content only - no JSON wrapping
            log.info("Returning raw text content without JSON wrapping")
            # For direct agents, return the response text directly
            agent_response_text = result.get("response", "")
            return PlainTextResponse(
                content=agent_response_text, media_type="text/plain"
            )
        else:
            # Return formatted response
            return WorkerResponse(
                success=True,
                response=result["response"],
                agent_name=request.agent_name,
                error=None,
                metadata=metadata,
                raw_data=None,
                thread_id=thread_id
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except BaseExceptionGroup as e:
        # Handle Python 3.11+ TaskGroup exceptions
        log.error(f"TaskGroup error executing worker '{request.agent_name}': {e}")
        # Extract underlying exceptions for better error messages
        underlying_errors = []
        if hasattr(e, 'exceptions'):
            for exc in e.exceptions:
                underlying_errors.append(str(exc))

        if underlying_errors:
            error_msg = ("Worker execution failed: " +
                         "; ".join(underlying_errors))
        else:
            error_msg = ("Worker execution failed with TaskGroup error: " +
                         str(e))

        return WorkerResponse(
            success=False,
            response="",
            agent_name=request.agent_name,
            error=error_msg,
            metadata=None,
            raw_data=None,
            thread_id=thread_id if 'thread_id' in locals() else get_or_create_thread_id()
        )
    except Exception as e:
        log.error(f"Error executing worker '{request.agent_name}': {e}")
        return WorkerResponse(
            success=False,
            response="",
            agent_name=request.agent_name,
            error=str(e),
            metadata=None,
            raw_data=None,
            thread_id=thread_id if 'thread_id' in locals() else get_or_create_thread_id()
        )


@app.post("/worker/upload")
async def worker_upload_endpoint(
    agent_name: str = Form(..., description="Name of the agent to execute"),
    input: str = Form(..., description="User question or prompt for the agent"),
    config_path: Optional[str] = Form(None, description="Optional path to config file"),
    raw_output: bool = Form(
        False,
        description="If True, returns only raw agent response as plain text"
    ),
    thread_id: Optional[str] = Form(
        None,
        description="Optional thread ID for conversation continuity. "
                    "If not provided, a new thread will be created."
    ),
    files: Optional[List[UploadFile]] = File(
        None, description="Optional files to upload and attach to the request"
    )
):
    """
    Worker endpoint that accepts file uploads and executes a specific agent.

    Args:
        agent_name: Name of the agent to execute
        input: User question or prompt for the agent
        config_path: Optional path to config file
        files: List of files to upload and attach to the request

    Returns:
        WorkerResponse with the agent's response including file analysis
    """
    try:
        # Load configuration
        if config_path:
            try:
                app_cfg = load_app_config(Path(config_path))
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to load config from {config_path}: {str(e)}"
                )
        else:
            if _app_config is None:
                raise HTTPException(
                    status_code=500,
                    detail="No default configuration available. Please provide config_path."
                )
            app_cfg = _app_config

        # Validate agent exists
        agent_names = [agent.name for agent in app_cfg.agents]
        if agent_name not in agent_names:
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{agent_name}' not found. Available agents: {', '.join(agent_names)}"
            )

        # Get or create thread ID
        actual_thread_id = get_or_create_thread_id(thread_id)
        log.info(f"Using thread ID: {actual_thread_id}")

        # Process uploaded files
        file_ids = []
        file_info = []
        csv_data_sections = []

        # Handle optional files parameter
        if files is None:
            files = []

        for file in files:
            # Read file content
            file_content = await file.read()

            # Determine file purpose based on MIME type
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]

            # Handle CSV files specially - don't upload to Azure OpenAI, process directly
            is_csv_file = (
                file.filename.lower().endswith('.csv') or
                mime_type in ['text/csv', 'application/csv', 'text/plain'] or
                (mime_type == 'application/octet-stream' and file.filename.lower().endswith('.csv'))
            )

            if is_csv_file:
                try:
                    csv_text = file_content.decode('utf-8')

                    # Limit CSV content to prevent token overflow
                    lines = csv_text.split('\n')
                    if len(lines) > 100:
                        csv_preview = '\n'.join(lines[:100]) + f"\n... (showing first 100 rows of {len(lines)} total rows)"
                    else:
                        csv_preview = csv_text

                    csv_data_sections.append(f"""
                                        **CSV File: {file.filename}**
                                        ```csv
                                        {csv_preview}
                                        ```
                                        """)

                    # Add to file info without uploading
                    file_info.append({
                        "filename": file.filename,
                        "file_id": "local_csv_data",
                        "mime_type": mime_type or "text/csv",
                        "purpose": "local_processing",
                        "size": len(file_content)
                    })
                    log.info(f"Processed CSV file {file.filename} locally ({len(lines)} rows)")

                except Exception as e:
                    log.error(f"Failed to process CSV file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to process CSV file {file.filename}: {str(e)}"
                    )
            else:
                # For non-CSV files, upload to Azure OpenAI as before
                purpose = "assistants"
                try:
                    # Upload file to OpenAI/Azure OpenAI
                    file_id = await upload_file_to_openai(file_content, file.filename, purpose)
                    file_ids.append(file_id)
                    file_info.append({
                        "filename": file.filename,
                        "file_id": file_id,
                        "mime_type": mime_type,
                        "purpose": purpose,
                        "size": len(file_content)
                    })
                    log.info(f"Uploaded file {file.filename} with ID {file_id}")
                except Exception as e:
                    log.error(f"Failed to upload file {file.filename}: {e}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload file {file.filename}: {str(e)}"
                    )

        # Enhance the input with file information and CSV data
        enhanced_input = input
        if file_info:
            file_descriptions = []
            for info in file_info:
                if info.get('purpose') == 'local_processing':
                    file_descriptions.append(f"- {info['filename']} (CSV data processed locally, Type: {info['mime_type']})")
                else:
                    file_descriptions.append(f"- {info['filename']} (ID: {info['file_id']}, Type: {info['mime_type']})")

            enhanced_input = f"""{input}

Attached files:
{chr(10).join(file_descriptions)}"""

            # Add CSV data if any were processed
            if csv_data_sections:
                csv_section = "\n\n**ATTACHED CSV DATA:**\n" + "\n".join(csv_data_sections)
                enhanced_input += csv_section

            enhanced_input += "\n\nPlease analyze the attached files and incorporate their content into your response."

        # Execute the agent with enhanced input
        files_count = len(files) if files else 0
        log.info(
            f"Executing agent '{agent_name}' with {files_count} attached files"
        )
        result = await run_direct_agent_with_files(
            agent_name, enhanced_input, app_cfg, file_ids, file_info,
            config_path, actual_thread_id
        )

        # Prepare metadata
        metadata = {
            "agent_name": agent_name,
            "model_used": app_cfg.models.get("default", "unknown"),
            "business_context": bool(app_cfg.business_context),
            "files_uploaded": files_count,
            "file_info": file_info
        }

        if raw_output:
            # Return raw text content only - no JSON wrapping
            log.info("Returning raw text content without JSON wrapping")
            # For direct agents, return the response text directly
            agent_response_text = result.get("response", "")
            return PlainTextResponse(
                content=agent_response_text, media_type="text/plain"
            )
        else:
            # Return formatted response
            return {
                "success": True,
                "response": result["response"],
                "agent_name": agent_name,
                "metadata": metadata,
                "thread_id": actual_thread_id
            }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except BaseExceptionGroup as e:
        # Handle Python 3.11+ TaskGroup exceptions
        log.error("TaskGroup error executing worker '%s' with files: %s",
                  agent_name, e)
        # Extract underlying exceptions for better error messages
        underlying_errors = []
        if hasattr(e, 'exceptions'):
            for exc in e.exceptions:
                underlying_errors.append(str(exc))

        if underlying_errors:
            error_msg = ("Worker execution failed: " +
                         "; ".join(underlying_errors))
        else:
            error_msg = ("Worker execution failed with TaskGroup error: " +
                         str(e))

        return {
            "success": False,
            "response": "",
            "agent_name": agent_name,
            "error": error_msg,
            "thread_id": actual_thread_id if 'actual_thread_id' in locals() else get_or_create_thread_id()
        }
    except Exception as e:
        log.error(f"Error executing worker '{agent_name}' with files: {e}")
        return {
            "success": False,
            "response": "",
            "agent_name": agent_name,
            "error": str(e),
            "thread_id": actual_thread_id if 'actual_thread_id' in locals() else get_or_create_thread_id()
        }


# Test endpoint to verify server is working
@app.post("/test-endpoint")
async def test_endpoint():
    """Simple test endpoint."""
    return {"status": "success", "message": "Test endpoint works"}


@app.post("/defect-analysis", response_model=DefectAnalysisResponse)
async def defect_analysis_endpoint(request: DefectAnalysisRequest):
    """
    Defect analysis endpoint that processes equipment issues through the pipeline.

    Args:
        request: DefectAnalysisRequest containing user input and configuration

    Returns:
        DefectAnalysisResponse with structured analysis results
    """
    try:
        log.info(f"Processing defect analysis: {request.user_input[:100]}...")

        # Create configuration from request parameters
        config = DefectAnalysisConfig(
            top_n=request.top_n or 10,
            min_score=request.min_score or 0.6,
            enable_logging=request.enable_logging if request.enable_logging is not None else True,
            enable_caching=request.enable_caching if request.enable_caching is not None else True,
            parallel_search=request.parallel_search if request.parallel_search is not None else True
        )

        # Create and run the defect analysis pipeline
        pipeline = DefectAnalysisPipeline(config)
        result = await pipeline.run(request.user_input)

        # Convert result to response format
        return DefectAnalysisResponse(
            success=True,
            original_input=result.original_input,
            intent_data={
                "component": result.intent_data.component,
                "sub_component": result.intent_data.sub_component,
                "related_component": result.intent_data.related_component,
                "issue": result.intent_data.issue
            },
            total_unique_results=result.total_unique_results,
            defects=[
                {
                    "id": defect.id,
                    "defect_code": defect.defect_code,
                    "defect_text": defect.defect_text,
                    "score": defect.score,
                    "subsystem": defect.subsystem,
                    "severity": defect.severity,
                    "symptoms": defect.symptoms,
                    "detection_methods": defect.detection_methods,
                    "tags": defect.tags,
                    "likely_root_causes": defect.likely_root_causes,
                    "recommended_actions": defect.recommended_actions
                }
                for defect in result.defects
            ],
            root_causes=result.root_causes,
            corrective_actions=result.corrective_actions,
            processing_time_ms=result.processing_time_ms,
            error=None,
            metadata={
                "pipeline_version": "1.0.0",
                "agent_name": config.agent_name,
                "vector_search_config": {
                    "top_n": config.top_n,
                    "min_score": config.min_score,
                    "parallel_search": config.parallel_search
                },
                "caching_enabled": config.enable_caching,
                "logging_enabled": config.enable_logging
            }
        )

    except Exception as e:
        log.error(f"Error in defect analysis: {e}")
        return DefectAnalysisResponse(
            success=False,
            original_input=request.user_input,
            intent_data={},
            total_unique_results=0,
            defects=[],
            root_causes=[],
            corrective_actions=[],
            processing_time_ms=0.0,
            error=str(e),
            metadata={
                "pipeline_version": "1.0.0",
                "error_occurred": True
            }
        )


@app.post("/defect-analysis/form")
async def defect_analysis_form_endpoint(
    user_input: str = Form(..., description="Equipment issue description", min_length=1),
    top_n: int = Form(10, description="Number of top results to return", ge=1, le=50),
    min_score: float = Form(0.6, description="Minimum similarity score", ge=0.0, le=1.0),
    enable_logging: bool = Form(True, description="Enable detailed logging"),
    enable_caching: bool = Form(True, description="Enable caching"),
    parallel_search: bool = Form(True, description="Enable parallel search")
):
    """
    Form-based defect analysis endpoint that accepts form data instead of JSON.

    Args:
        user_input: Equipment issue description
        top_n: Number of top results to return from vector search
        min_score: Minimum similarity score for results
        enable_logging: Enable detailed logging
        enable_caching: Enable caching for repeated queries
        parallel_search: Enable parallel vector search execution

    Returns:
        DefectAnalysisResponse with structured analysis results
    """
    # Convert form data to DefectAnalysisRequest object
    request = DefectAnalysisRequest(
        user_input=user_input,
        top_n=top_n,
        min_score=min_score,
        enable_logging=enable_logging,
        enable_caching=enable_caching,
        parallel_search=parallel_search
    )

    # Use the existing defect analysis logic
    return await defect_analysis_endpoint(request)


@app.post("/defect-analysis-with-pilger", response_model=EnhancedDefectAnalysisResponse)
async def enhanced_defect_analysis_endpoint(request: EnhancedDefectAnalysisRequest):
    """
    Enhanced defect analysis endpoint that processes equipment issues through both
    DefectAnalysisPipeline and PilgerProcessingPipeline for comprehensive analysis.

    This endpoint provides a two-stage processing workflow:
    1. DefectAnalysisPipeline: Intent extraction, vector search, and result aggregation
    2. PilgerProcessingPipeline: Additional insights and actions via jk_pilger_new_entries_agent

    Args:
        request: EnhancedDefectAnalysisRequest containing user input and configuration

    Returns:
        EnhancedDefectAnalysisResponse with comprehensive analysis results from both stages
    """
    start_time = time.time()
    warnings = []

    try:
        log.info(f"Processing enhanced defect analysis: {request.user_input[:100]}...")

        # Stage 1: Defect Analysis Pipeline
        defect_start_time = time.time()

        # Create defect analysis configuration from request parameters
        defect_config = DefectAnalysisConfig(
            top_n=request.top_n or 10,
            min_score=request.min_score or 0.6,
            enable_logging=request.enable_logging if request.enable_logging is not None else True,
            enable_caching=request.enable_caching if request.enable_caching is not None else True,
            parallel_search=request.parallel_search if request.parallel_search is not None else True
        )

        # Create and run the defect analysis pipeline
        defect_pipeline = DefectAnalysisPipeline(defect_config)
        defect_result = await defect_pipeline.run(request.user_input)

        defect_end_time = time.time()
        defect_processing_time = (defect_end_time - defect_start_time) * 1000

        log.info(f"Defect analysis completed: {defect_result.total_unique_results} results in {defect_processing_time:.2f}ms")

        # Prepare defect analysis data for response
        defect_analysis_data = {
            "success": True,
            "intent_data": {
                "interpreted_meaning": defect_result.intent_data.interpreted_meaning,
                "component": defect_result.intent_data.component,
                "sub_component": defect_result.intent_data.sub_component,
                "related_component": defect_result.intent_data.related_component,
                "issue": defect_result.intent_data.issue
            },
            "total_unique_results": defect_result.total_unique_results,
            "defects": [defect.model_dump() for defect in defect_result.defects],
            "root_causes": [rc.model_dump() for rc in defect_result.root_causes],
            "corrective_actions": [ca.model_dump() for ca in defect_result.corrective_actions],
            "processing_time_ms": defect_result.processing_time_ms
        }

        # Initialize combined results with defect analysis data
        total_insights = []
        total_recommended_actions = [ca.action_text for ca in defect_result.corrective_actions]

        # Stage 2: Pilger Processing Pipeline (if not skipped)
        pilger_processing_data = None
        pilger_processing_time = 0.0
        pilger_agent_time = 0.0

        if not request.skip_pilger_processing:
            try:
                pilger_start_time = time.time()

                # Create Pilger processing configuration
                pilger_config = PilgerProcessingConfig(
                    timeout_seconds=request.pilger_timeout_seconds or 120,
                    format_for_agent=request.pilger_format or "structured",
                    enable_logging=request.enable_logging if request.enable_logging is not None else True,
                    enable_caching=request.enable_caching if request.enable_caching is not None else True
                )

                # Create and run the Pilger processing pipeline
                pilger_pipeline = PilgerProcessingPipeline(pilger_config)
                pilger_result = await pilger_pipeline.run(defect_result)

                pilger_end_time = time.time()
                pilger_processing_time = (pilger_end_time - pilger_start_time) * 1000
                pilger_agent_time = pilger_result.agent_execution_time_ms

                log.info(f"Pilger processing completed: {len(pilger_result.processed_insights)} insights, {len(pilger_result.recommended_actions)} actions in {pilger_processing_time:.2f}ms")

                # Prepare Pilger processing data for response
                pilger_processing_data = {
                    "success": pilger_result.success,
                    "pilger_agent_response": pilger_result.pilger_agent_response,
                    "processed_insights": pilger_result.processed_insights,
                    "recommended_actions": pilger_result.recommended_actions,
                    "confidence_score": pilger_result.confidence_score,
                    "processing_time_ms": pilger_result.processing_time_ms,
                    "agent_execution_time_ms": pilger_result.agent_execution_time_ms,
                    "error_message": pilger_result.error_message
                }

                # Add Pilger insights and actions to combined results
                total_insights.extend(pilger_result.processed_insights)
                total_recommended_actions.extend(pilger_result.recommended_actions)

                if not pilger_result.success and pilger_result.error_message:
                    warnings.append(f"Pilger processing completed with warnings: {pilger_result.error_message}")

            except Exception as e:
                pilger_end_time = time.time()
                pilger_processing_time = (pilger_end_time - pilger_start_time) * 1000

                log.warning(f"Pilger processing failed: {e}")
                warnings.append(f"Pilger processing failed: {str(e)}")

                # Create error response for Pilger processing
                pilger_processing_data = {
                    "success": False,
                    "pilger_agent_response": {},
                    "processed_insights": [],
                    "recommended_actions": [],
                    "confidence_score": None,
                    "processing_time_ms": pilger_processing_time,
                    "agent_execution_time_ms": 0.0,
                    "error_message": str(e)
                }
        else:
            log.info("Pilger processing skipped as requested")

        # Calculate total processing time
        total_end_time = time.time()
        total_processing_time = (total_end_time - start_time) * 1000

        # Prepare processing stages metadata
        processing_stages = {
            "defect_analysis": {
                "success": True,
                "processing_time_ms": defect_processing_time,
                "results_count": defect_result.total_unique_results
            },
            "pilger_processing": {
                "success": pilger_processing_data["success"] if pilger_processing_data else None,
                "processing_time_ms": pilger_processing_time,
                "agent_execution_time_ms": pilger_agent_time,
                "skipped": request.skip_pilger_processing,
                "insights_count": len(pilger_processing_data["processed_insights"]) if pilger_processing_data else 0,
                "actions_count": len(pilger_processing_data["recommended_actions"]) if pilger_processing_data else 0
            }
        }

        # Create comprehensive metadata
        metadata = {
            "pipeline_version": "2.0.0",
            "processing_stages": ["defect_analysis", "pilger_processing"],
            "defect_analysis_config": {
                "agent_name": defect_config.agent_name,
                "top_n": defect_config.top_n,
                "min_score": defect_config.min_score,
                "parallel_search": defect_config.parallel_search
            },
            "pilger_processing_config": {
                "agent_name": pilger_config.agent_name if not request.skip_pilger_processing else None,
                "timeout_seconds": request.pilger_timeout_seconds,
                "format": request.pilger_format,
                "skipped": request.skip_pilger_processing
            } if not request.skip_pilger_processing else {"skipped": True},
            "caching_enabled": request.enable_caching,
            "logging_enabled": request.enable_logging,
            "warnings_count": len(warnings)
        }

        return EnhancedDefectAnalysisResponse(
            success=True,
            original_input=request.user_input,
            defect_analysis=defect_analysis_data,
            pilger_processing=pilger_processing_data,
            total_insights=total_insights,
            total_recommended_actions=total_recommended_actions,
            processing_stages=processing_stages,
            total_processing_time_ms=total_processing_time,
            error=None,
            warnings=warnings,
            metadata=metadata
        )

    except Exception as e:
        total_end_time = time.time()
        total_processing_time = (total_end_time - start_time) * 1000

        log.error(f"Error in enhanced defect analysis: {e}")
        return EnhancedDefectAnalysisResponse(
            success=False,
            original_input=request.user_input,
            defect_analysis={
                "success": False,
                "intent_data": {},
                "total_unique_results": 0,
                "defects": [],
                "root_causes": [],
                "corrective_actions": [],
                "processing_time_ms": 0.0
            },
            pilger_processing=None,
            total_insights=[],
            total_recommended_actions=[],
            processing_stages={
                "defect_analysis": {"success": False, "processing_time_ms": 0.0},
                "pilger_processing": {"success": False, "processing_time_ms": 0.0, "skipped": True}
            },
            total_processing_time_ms=total_processing_time,
            error=str(e),
            warnings=[],
            metadata={
                "pipeline_version": "2.0.0",
                "error_occurred": True,
                "processing_stages": ["defect_analysis", "pilger_processing"]
            }
        )


@app.post("/defect-analysis-with-pilger/form")
async def enhanced_defect_analysis_form_endpoint(
    user_input: str = Form(..., description="Equipment issue description", min_length=1),
    top_n: int = Form(10, description="Number of top results to return", ge=1, le=50),
    min_score: float = Form(0.6, description="Minimum similarity score", ge=0.0, le=1.0),
    enable_logging: bool = Form(True, description="Enable detailed logging"),
    enable_caching: bool = Form(True, description="Enable caching"),
    parallel_search: bool = Form(True, description="Enable parallel search"),
    pilger_timeout_seconds: int = Form(120, description="Pilger processing timeout", ge=30, le=300),
    pilger_format: str = Form("structured", description="Pilger input format: structured or text"),
    skip_pilger_processing: bool = Form(False, description="Skip Pilger processing stage")
):
    """
    Form-based enhanced defect analysis endpoint that accepts form data instead of JSON.

    This endpoint provides the same two-stage processing workflow as the JSON endpoint
    but accepts form data for easier integration with HTML forms and testing tools.

    Args:
        user_input: Equipment issue description
        top_n: Number of top results to return from vector search
        min_score: Minimum similarity score for results
        enable_logging: Enable detailed logging
        enable_caching: Enable caching for repeated queries
        parallel_search: Enable parallel vector search execution
        pilger_timeout_seconds: Timeout for Pilger agent processing
        pilger_format: Format for Pilger agent input (structured or text)
        skip_pilger_processing: Skip Pilger processing and return only defect analysis

    Returns:
        EnhancedDefectAnalysisResponse with comprehensive analysis results from both stages
    """
    # Validate pilger_format
    if pilger_format not in ["structured", "text"]:
        raise HTTPException(
            status_code=400,
            detail="pilger_format must be either 'structured' or 'text'"
        )

    # Convert form data to EnhancedDefectAnalysisRequest object
    request = EnhancedDefectAnalysisRequest(
        user_input=user_input,
        top_n=top_n,
        min_score=min_score,
        enable_logging=enable_logging,
        enable_caching=enable_caching,
        parallel_search=parallel_search,
        pilger_timeout_seconds=pilger_timeout_seconds,
        pilger_format=pilger_format,
        skip_pilger_processing=skip_pilger_processing
    )

    # Use the existing enhanced defect analysis logic
    return await enhanced_defect_analysis_endpoint(request)


@app.post("/submit-selection", response_model=SubmitSelectionResponse)
async def submit_selection_endpoint(request: SubmitSelectionRequest):
    """
    Submit selection endpoint that receives user selections from defect analysis.

    Args:
        request: SubmitSelectionRequest containing user selections and metadata

    Returns:
        SubmitSelectionResponse with confirmation details
    """
    try:
        log.info(f"Processing submit selection for input: {request.original_input[:100]}...")

        # Create user_responses directory if it doesn't exist
        user_responses_dir = Path("user_responses")
        user_responses_dir.mkdir(exist_ok=True)

        # Generate submission ID and filename based on timestamp
        try:
            # Parse the timestamp to create a filename
            timestamp_dt = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            filename = f"submit_{timestamp_dt.strftime('%Y%m%d%H%M%S')}.json"
        except ValueError:
            # Fallback to current timestamp if parsing fails
            current_time = datetime.utcnow()
            filename = f"submit_{current_time.strftime('%Y%m%d%H%M%S')}.json"
            log.warning(f"Invalid timestamp format, using current time for filename: {filename}")

        # Create submission data with metadata
        submission_data = {
            **request.model_dump(),
            "submission_metadata": {
                "submission_id": filename.replace('.json', ''),
                "submission_timestamp": datetime.utcnow().isoformat() + "Z",
                "api_version": "1.0.0",
                "source": "api_endpoint"
            }
        }

        # Save to JSON file with proper encoding for Windows
        file_path = user_responses_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(submission_data, f, indent=2, ensure_ascii=False)

        log.info(f"Saved submission to: {file_path}")

        return SubmitSelectionResponse(
            status="success",
            message="Selection submitted successfully",
            submission_id=filename.replace('.json', ''),
            timestamp=datetime.utcnow().isoformat() + "Z",
            processed_pairs=len(request.selected_pairs)
        )

    except Exception as e:
        log.error(f"Error processing submit selection: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status="error",
                error_code="INTERNAL_ERROR",
                message="Internal server error occurred",
                timestamp=datetime.utcnow().isoformat() + "Z",
                details={"error": str(e)}
            ).model_dump()
        )


@app.post("/consolidated-responses/form")
async def consolidated_responses_form_endpoint(
    start_date: Optional[str] = Form(
        None,
        description="Start date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). "
                    "If not provided, returns all submissions."
    ),
    end_date: Optional[str] = Form(
        None,
        description="End date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ). "
                    "If not provided, returns all submissions."
    )
):
    """
    Form-based consolidated responses endpoint that accepts form data instead of JSON.

    Args:
        start_date: Optional start date filter (ISO 8601 format)
        end_date: Optional end date filter (ISO 8601 format)

    Returns:
        ConsolidatedResponsesResponse with all matching submissions
    """
    # Convert form data to ConsolidatedResponsesRequest object
    request = ConsolidatedResponsesRequest(
        start_date=start_date,
        end_date=end_date
    )

    # Use the existing consolidated responses logic
    return await consolidated_responses_endpoint(request)


@app.post("/consolidated-responses", response_model=ConsolidatedResponsesResponse)
async def consolidated_responses_endpoint(request: ConsolidatedResponsesRequest):
    """
    Consolidated responses endpoint that retrieves user submissions with optional date filtering.

    Args:
        request: ConsolidatedResponsesRequest with optional date filters

    Returns:
        ConsolidatedResponsesResponse with all matching submissions
    """
    try:
        start_time = time.time()
        query_timestamp = datetime.utcnow().isoformat() + "Z"

        log.info("Processing consolidated responses request")
        if request.start_date:
            log.info(f"Start date filter: {request.start_date}")
        if request.end_date:
            log.info(f"End date filter: {request.end_date}")

        # Check if user_responses directory exists
        user_responses_dir = Path("user_responses")
        directory_exists = user_responses_dir.exists()

        if not directory_exists:
            log.warning("user_responses directory does not exist")
            return ConsolidatedResponsesResponse(
                status="success",
                message="No submissions found - user_responses directory does not exist",
                query_metadata={
                    "query_timestamp": query_timestamp,
                    "start_date_filter": request.start_date,
                    "end_date_filter": request.end_date,
                    "directory_exists": False,
                    "total_files_found": 0,
                    "files_processed": 0,
                    "files_skipped": 0,
                    "processing_time_ms": (time.time() - start_time) * 1000
                },
                submissions=[],
                total_count=0
            )

        # Parse date filters if provided
        start_date_dt = None
        end_date_dt = None

        if request.start_date:
            try:
                start_date_dt = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        status="error",
                        error_code="VALIDATION_ERROR",
                        message="Invalid start_date format. Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
                        timestamp=query_timestamp
                    ).model_dump()
                )

        if request.end_date:
            try:
                end_date_dt = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        status="error",
                        error_code="VALIDATION_ERROR",
                        message="Invalid end_date format. Must be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
                        timestamp=query_timestamp
                    ).model_dump()
                )

        # Find all JSON files in user_responses directory
        json_files = list(user_responses_dir.glob("*.json"))
        total_files_found = len(json_files)

        log.info(f"Found {total_files_found} JSON files in user_responses directory")

        submissions = []
        files_processed = 0
        files_skipped = 0

        for json_file in json_files:
            try:
                # Read and parse JSON file
                with open(json_file, 'r', encoding='utf-8') as f:
                    submission_data = json.load(f)

                # Extract timestamp for filtering
                submission_timestamp = submission_data.get('timestamp')
                if not submission_timestamp:
                    log.warning(f"No timestamp found in {json_file.name}, skipping")
                    files_skipped += 1
                    continue

                # Parse submission timestamp
                try:
                    submission_dt = datetime.fromisoformat(submission_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    log.warning(f"Invalid timestamp format in {json_file.name}: {submission_timestamp}, skipping")
                    files_skipped += 1
                    continue

                # Apply date filters
                if start_date_dt and submission_dt < start_date_dt:
                    files_skipped += 1
                    continue

                if end_date_dt and submission_dt > end_date_dt:
                    files_skipped += 1
                    continue

                # Add to submissions
                submissions.append(submission_data)
                files_processed += 1

            except Exception as e:
                log.error(f"Error processing file {json_file.name}: {e}")
                files_skipped += 1
                continue

        # Sort submissions by timestamp (most recent first)
        submissions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        processing_time_ms = (time.time() - start_time) * 1000

        log.info(f"Processed {files_processed} files, skipped {files_skipped} files")
        log.info(f"Returning {len(submissions)} submissions")

        return ConsolidatedResponsesResponse(
            status="success",
            message=f"Retrieved {len(submissions)} submissions successfully",
            query_metadata={
                "query_timestamp": query_timestamp,
                "start_date_filter": request.start_date,
                "end_date_filter": request.end_date,
                "directory_exists": directory_exists,
                "total_files_found": total_files_found,
                "files_processed": files_processed,
                "files_skipped": files_skipped,
                "processing_time_ms": processing_time_ms
            },
            submissions=submissions,
            total_count=len(submissions)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error processing consolidated responses: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                status="error",
                error_code="INTERNAL_ERROR",
                message="Internal server error occurred",
                timestamp=datetime.utcnow().isoformat() + "Z",
                details={"error": str(e)}
            ).model_dump()
        )


# Legacy endpoint for backward compatibility
@app.post("/plan_and_run")
async def plan_and_run_endpoint(request: QueryRequest):
    """Legacy endpoint - redirects to /query."""
    return await query_endpoint(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
