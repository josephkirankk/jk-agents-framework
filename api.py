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

# Import conversation memory modules
from app.memory.memory_integration import (
    initialize_conversation_memory, 
    enhance_system_message_with_memory, 
    store_conversation_memory,
    is_conversation_memory_enabled
)

from app.checkpointer_manager import get_memory_stats, clear_thread_memory, reset_all_memory

# Import memory metrics API
try:
    from app.memory_metrics_api import memory_metrics_router
    HAS_MEMORY_METRICS = True
except ImportError:
    HAS_MEMORY_METRICS = False

# Import advanced memory agent
try:
    from advanced_memory_agent import AdvancedMemoryAgent
    HAS_ADVANCED_MEMORY = True
except ImportError:
    HAS_ADVANCED_MEMORY = False

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

# Include memory metrics API if available
if HAS_MEMORY_METRICS:
    app.include_router(memory_metrics_router)
    log.info("Memory metrics API endpoints enabled")

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
            
            # Get or create thread ID
            actual_thread_id = get_or_create_thread_id(thread_id)
            
            # Enhance system context with conversation memory
            system_context = await enhance_system_message_with_memory(
                original_message=system_context,
                thread_id=actual_thread_id,
                app_config=app_cfg
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
            
            # Store conversation in memory
            await store_conversation_memory(
                thread_id=actual_thread_id,
                user_message=user_input,
                assistant_response=text,
                app_config=app_cfg,
                metadata={"agent_name": agent_name, "has_files": True}
            )

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


class SelectedIssue(BaseModel):
    """Selected issue model for submit selection."""
    issue_code: str = Field(..., description="Unique identifier code for the issue")
    issue_text: str = Field(..., description="Human-readable description of the issue")
    confidence_score: float = Field(..., description="AI confidence score (0.0 to 1.0) for the issue identification", ge=0.0, le=1.0)
    mapping_status: str = Field(..., description="Status of issue mapping")
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
    selected_issue: SelectedIssue = Field(..., description="Object containing the issue selected by the user")
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
            
            # Get or create thread ID
            actual_thread_id = get_or_create_thread_id(thread_id)
            
            # Enhance system context with conversation memory
            system_context = await enhance_system_message_with_memory(
                original_message=system_context,
                thread_id=actual_thread_id,
                app_config=app_cfg
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
            
            # Store conversation in memory
            await store_conversation_memory(
                thread_id=actual_thread_id,
                user_message=user_input,
                assistant_response=text,
                app_config=app_cfg,
                metadata={"agent_name": agent_name}
            )

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
    
    # Get or create thread ID for conversation context
    actual_thread_id = get_or_create_thread_id(thread_id)
    
    # Enhance business context with conversation memory
    enhanced_business_context = await enhance_system_message_with_memory(
        original_message=app_cfg.business_context or "",
        thread_id=actual_thread_id,
        app_config=app_cfg
    )

    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_cfg.supervisor,
        app_cfg.agents,
        default_model,
        enhanced_business_context,
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
            business_context=enhanced_business_context,
            default_model_for_verifier=default_model,
            agents_configs=app_cfg.agents,
            default_model=default_model,
            thread_id=actual_thread_id,
        )
        
        # Store conversation in memory after successful execution
        human_response = await extract_human_response(result)
        await store_conversation_memory(
            thread_id=actual_thread_id,
            user_message=user_input,
            assistant_response=human_response,
            app_config=app_cfg,
            metadata={"execution_type": "supervised"}
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
        
        # Initialize conversation memory if enabled
        if _app_config and is_conversation_memory_enabled(_app_config):
            memory_initialized = await initialize_conversation_memory(_app_config)
            if memory_initialized:
                log.info("Conversation memory initialized successfully")
            else:
                log.warning("Failed to initialize conversation memory")
                
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
            "issue_analysis": "/issue-analysis - Issue analysis pipeline endpoint",
            "issue_analysis_form": "/issue-analysis/form - Form-based issue analysis endpoint",
            "enhanced_issue_analysis": "/issue-analysis-enhanced - Enhanced issue analysis processing",
            "enhanced_issue_analysis_form": "/issue-analysis-enhanced/form - Form-based enhanced issue analysis",
            "submit_selection": "/submit-selection - Submit issue analysis selections",
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


# Legacy endpoint for backward compatibility
@app.post("/plan_and_run")
async def plan_and_run_endpoint(request: QueryRequest):
    """Legacy endpoint for backward compatibility."""
    return await query_endpoint(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
