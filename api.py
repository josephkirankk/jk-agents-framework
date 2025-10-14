"""
FastAPI web server for jk-agents system.

Provides HTTP endpoints to interact with the multi-agent system.
"""
from __future__ import annotations

import asyncio
import logging
import base64
import mimetypes
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading
    pass

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.main import load_app_config, build_agents_map, process_business_context_template
from app.supervisor_builder import build_supervisor_compiled
from app.planner_executor import execute_plan
from app.mcp_loader import close_mcp_client
from app.agent_builder import build_react_agent
from app.conversation_tracker import ConversationTracker
from app.thread_id_utils import generate_thread_id, get_or_create_thread_id
from app.memory_monitor import monitor_memory_usage, get_memory_stats

# Import enhanced LiteLLM functionality
try:
    from app.enhanced_litellm_wrapper import EnhancedLiteLLMChat, is_litellm_model, test_litellm_model
    HAS_ENHANCED_LITELLM = True
except ImportError:
    HAS_ENHANCED_LITELLM = False

from app.memory_integration import (
    initialize_conversation_memory, 
    enhance_system_message_with_memory, 
    store_conversation_memory,
    is_conversation_memory_enabled
)

# Import file storage manager
from app.file_storage_manager import get_file_storage_manager

from app.checkpointer_manager import get_memory_stats, clear_thread_memory, reset_all_memory

# Import simple conversation memory for bypass - FIXED: Using enhanced version
from app.simple_conversation_memory_fixed import inject_conversation_context, store_conversation_turn

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

# Configure logging with performance tracking
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("api")
perf_log = logging.getLogger("api.performance")

# Performance metrics storage
_performance_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "thread_contexts": {},  # thread_id -> {turns: int, first_seen: timestamp, last_seen: timestamp}
    "response_times": [],
    "memory_operations": []
}
_metrics_lock = asyncio.Lock()

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
)

# Global configuration - will be loaded on startup
_app_config: Optional[AppConfig] = None

# Global cache for preloaded components to improve performance
# Structure: {config_path: {agents: Dict, supervisor: Any, mcp_clients: Dict}}
_preloaded_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = asyncio.Lock()
_preload_initialized = False


@asynccontextmanager
async def track_performance(operation_name: str, thread_id: Optional[str] = None):
    """Context manager for tracking operation performance."""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]

    perf_log.info(f"[{request_id}] Starting {operation_name} (thread: {thread_id})")

    try:
        yield request_id
        elapsed = time.time() - start_time
        perf_log.info(f"[{request_id}] Completed {operation_name} in {elapsed:.3f}s")

        # Update metrics
        async with _metrics_lock:
            _performance_metrics["successful_requests"] += 1
            _performance_metrics["response_times"].append({
                "operation": operation_name,
                "duration": elapsed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "thread_id": thread_id,
                "request_id": request_id
            })

            # Track thread context usage
            if thread_id:
                if thread_id not in _performance_metrics["thread_contexts"]:
                    _performance_metrics["thread_contexts"][thread_id] = {
                        "turns": 1,
                        "first_seen": datetime.now(timezone.utc).isoformat(),
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    _performance_metrics["thread_contexts"][thread_id]["turns"] += 1
                    _performance_metrics["thread_contexts"][thread_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
    except Exception as e:
        elapsed = time.time() - start_time
        perf_log.error(f"[{request_id}] Failed {operation_name} in {elapsed:.3f}s: {str(e)}")

        # Update failure metrics
        async with _metrics_lock:
            _performance_metrics["failed_requests"] += 1
        raise
    finally:
        async with _metrics_lock:
            _performance_metrics["total_requests"] += 1


async def track_memory_operation(operation: str, thread_id: str, details: Dict[str, Any] = None):
    """Track memory-related operations for performance analysis."""
    async with _metrics_lock:
        _performance_metrics["memory_operations"].append({
            "operation": operation,
            "thread_id": thread_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {}
        })

    perf_log.info(f"Memory operation: {operation} for thread {thread_id} - {details}")


async def preload_config(config_path: str) -> bool:
    """
    Preload a specific configuration file.
{{ ... }}
    Returns True if successful, False otherwise.
    """
    try:
        log.info(f"Preloading config: {config_path}")
        start_time = time.time()
        
        # Load the configuration
        app_cfg = load_app_config(Path(config_path))
        
        # Check if memory backend is properly configured (skip if problematic)
        memory_config = getattr(app_cfg, 'memory', None)
        if memory_config and hasattr(memory_config, 'backend') and not memory_config.backend:
            log.warning(f"Skipping {config_path}: Memory backend is not properly configured")
            return False
        
        # Build agents map
        agents_map, mcp_clients = await build_agents_map(
            app_cfg, user_input="", config_path=config_path
        )
        
        # Build supervisor
        default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
        processed_business_context = process_business_context_template(app_cfg.business_context or "")
        
        supervisor = build_supervisor_compiled(
            app_cfg.supervisor,
            app_cfg.agents,
            default_model,
            processed_business_context,
            original_user_question="",
            config_path=config_path,
            default_temperature=app_cfg.temperature,
            thread_id=None,  # No thread context for preload
        )
        
        # Store in cache
        _preloaded_cache[config_path] = {
            "agents": agents_map,
            "supervisor": supervisor,
            "mcp_clients": mcp_clients,
            "app_config": app_cfg
        }
        
        preload_time = time.time() - start_time
        log.info(f"✓ Preloaded {config_path} in {preload_time:.2f}s - agents: {len(agents_map)}")
        return True
        
    except Exception as e:
        log.error(f"✗ Failed to preload {config_path}: {e}")
        log.exception("Preload error details:")
        return False


async def preload_from_environment() -> None:
    """
    Preload configurations specified in PRELOAD_CONFIGS environment variable.
    """
    global _preload_initialized
    
    if _preload_initialized:
        return
    
    async with _cache_lock:
        if _preload_initialized:  # Double-check after acquiring lock
            return
        
        try:
            log.info("Starting multi-config preloading from environment...")
            overall_start = time.time()
            
            # Get configs to preload from environment
            preload_configs_env = os.getenv("PRELOAD_CONFIGS", "")
            if not preload_configs_env:
                log.info("No PRELOAD_CONFIGS specified in environment, skipping preloading")
                _preload_initialized = True
                return
            
            # Parse comma-separated config paths
            config_paths = [path.strip() for path in preload_configs_env.split(",") if path.strip()]
            if not config_paths:
                log.info("No valid config paths found in PRELOAD_CONFIGS")
                _preload_initialized = True
                return
            
            log.info(f"Found {len(config_paths)} configs to preload: {config_paths}")
            
            # Preload each configuration
            successful_preloads = 0
            for config_path in config_paths:
                if await preload_config(config_path):
                    successful_preloads += 1
            
            _preload_initialized = True
            overall_time = time.time() - overall_start
            
            log.info(f"🎉 Preloading completed in {overall_time:.2f}s - {successful_preloads}/{len(config_paths)} configs loaded successfully")
            log.info(f"Cached configs: {list(_preloaded_cache.keys())}")
            
        except Exception as e:
            log.error(f"Failed to preload from environment: {e}")
            log.exception("Environment preload error details:")
            _preload_initialized = True  # Mark as initialized to prevent retries


async def get_cached_agents_and_supervisor(app_cfg: AppConfig, config_path: Optional[str] = None):
    """
    Get preloaded agents and supervisor, with fallback to on-demand building.
    """
    # Ensure preloading is attempted if not done yet
    if not _preload_initialized:
        await preload_from_environment()
    
    # Try to get from cache using exact config path match
    cache_key = config_path
    if cache_key and cache_key in _preloaded_cache:
        cached = _preloaded_cache[cache_key]
        log.debug(f"✓ Using preloaded cache for config: {cache_key}")
        return (
            cached["agents"].copy(),
            cached["supervisor"],
            cached["mcp_clients"].copy(),
            cached["app_config"]  # Return cached app config too
        )
    
    # Try default config if no config_path specified and default is cached
    if config_path is None:
        # Look for a cached default config (could be "config/agents.yaml" or similar)
        for cached_path in _preloaded_cache:
            if "agents.yaml" in cached_path or cached_path == "config/agents.yaml":
                cached = _preloaded_cache[cached_path]
                log.debug(f"✓ Using default config cache: {cached_path}")
                return (
                    cached["agents"].copy(),
                    cached["supervisor"],
                    cached["mcp_clients"].copy(),
                    cached["app_config"]  # Return cached app config too
                )
    
    # Fallback: build on demand
    log.warning(f"Cache miss for config '{config_path}' - building on demand")
    log.debug(f"Available cached configs: {list(_preloaded_cache.keys())}")
    
    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
    processed_business_context = process_business_context_template(app_cfg.business_context or "")
    
    agents_map, mcp_clients = await build_agents_map(app_cfg, user_input="", config_path=config_path)
    supervisor = build_supervisor_compiled(
        app_cfg.supervisor,
        app_cfg.agents,
        default_model,
        processed_business_context,
        original_user_question="",
        config_path=config_path,
        default_temperature=app_cfg.temperature,
        thread_id=None,  # No thread context for preload
    )
    
    return agents_map, supervisor, mcp_clients, app_cfg


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
    # This won't actually be filled when used with /query endpoint, but we'll use it 
    # for typing the files coming through the form or multipart data
    files: Optional[List[UploadFile]] = Field(
        None,
        description="Optional files to upload and attach to the request. "
                   "Note: This field is only used for typing purposes and should "
                   "be passed via form data or multipart/form-data."
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


class OCRImageResult(BaseModel):
    """Result model for a single OCR image."""
    filename: str = Field(..., description="Original filename")
    success: bool = Field(..., description="Whether OCR was successful")
    extracted_text: str = Field(..., description="Extracted text from the image")
    error: Optional[str] = Field(None, description="Error message if OCR failed")
    processing_time: float = Field(..., description="Processing time in seconds")


class FastOCRResponse(BaseModel):
    """Response model for fast OCR endpoint."""
    success: bool = Field(..., description="Overall success status")
    message: str = Field(..., description="Response message")
    structured_cards: List[Dict[str, Any]] = Field(..., description="Structured contact cards (merged/summarized)")
    total_images: int = Field(..., description="Total number of images processed")
    successful_count: int = Field(..., description="Number of successfully processed images")
    failed_count: int = Field(..., description="Number of failed images")
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    summarization_time: float = Field(..., description="Time taken for final summarization in seconds")
    model_used: str = Field(..., description="Model used for OCR")
    timestamp: str = Field(..., description="ISO 8601 timestamp")




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
    
    # Try to use simple conversation memory for context injection
    enhanced_user_input = user_input
    try:
        enhanced_user_input = inject_conversation_context(user_input, actual_thread_id)
        log.debug(f"Enhanced user input with conversation context for thread {actual_thread_id}")
    except Exception as e:
        log.warning(f"Failed to inject conversation context: {e}")
        enhanced_user_input = user_input
    
    # Enhance business context with conversation memory (fallback to existing system)
    enhanced_business_context = app_cfg.business_context or ""
    try:
        enhanced_business_context = await enhance_system_message_with_memory(
            original_message=app_cfg.business_context or "",
            thread_id=actual_thread_id,
            app_config=app_cfg
        )
    except Exception as e:
        log.warning(f"Failed to enhance business context with memory: {e}")

    # Use cached agents and supervisor for improved performance
    try:
        cache_result = await get_cached_agents_and_supervisor(app_cfg, config_path)
        if len(cache_result) == 4:
            agents_map, supervisor, mcp_clients, cached_app_cfg = cache_result
            # Use cached config if available to ensure proper memory backend configuration
            if cached_app_cfg:
                app_cfg = cached_app_cfg
                log.debug("Using cached app config for consistent memory backend")
        else:
            agents_map, supervisor, mcp_clients = cache_result
        log.debug("Using preloaded agents and supervisor")
    except Exception as e:
        log.warning(f"Failed to get cached components, falling back to on-demand building: {e}")
        # Fallback to original method
        supervisor = build_supervisor_compiled(
            app_cfg.supervisor,
            app_cfg.agents,
            default_model,
            enhanced_business_context,
            original_user_question=enhanced_user_input,  # Use enhanced input
            config_path=config_path,
            default_temperature=app_cfg.temperature,
            thread_id=actual_thread_id,
        )
        # Build workers (don't pass user_input to allow caching)
        agents_map, mcp_clients = await build_agents_map(
            app_cfg, user_input="", config_path=config_path  # Empty - will pass dynamically at execution
        )

    try:
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=enhanced_user_input,  # Use enhanced input
            business_context=enhanced_business_context,
            default_model_for_verifier=default_model,
            agents_configs=app_cfg.agents,
            default_model=default_model,
            thread_id=actual_thread_id,
        )
        
        # Store conversation in simple memory system
        human_response = await extract_human_response(result)
        try:
            store_conversation_turn(
                thread_id=actual_thread_id,
                user_input=user_input,  # Store original input
                assistant_response=human_response,
                metadata={"execution_type": "supervised", "enhanced": enhanced_user_input != user_input}
            )
            log.debug(f"Stored conversation turn in simple memory for thread {actual_thread_id}")
        except Exception as e:
            log.warning(f"Failed to store conversation turn: {e}")
        
        # Also try to store in advanced memory system (if available)
        try:
            await store_conversation_memory(
                thread_id=actual_thread_id,
                user_message=user_input,
                assistant_response=human_response,
                app_config=app_cfg,
                metadata={"execution_type": "supervised"}
            )
        except Exception as e:
            log.debug(f"Advanced memory storage failed (expected if LangGraph has issues): {e}")
        
        return result

    finally:
        # Cleanup MCP clients
        for client in mcp_clients.values():
            await close_mcp_client(client)


async def summarize_visiting_cards(
    ocr_results: List[Dict[str, Any]],
    model: str = "gemini/gemini-flash-latest",
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Summarize multiple OCR results into structured JSON format.
    
    Args:
        ocr_results: List of OCR results from individual images
        model: LiteLLM model to use
        temperature: Model temperature (0.0 for deterministic)
    
    Returns:
        Dictionary with structured contact cards
    """
    import time
    start_time = time.time()
    
    try:
        from app.enhanced_litellm_wrapper import create_litellm_model
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Combine all successful OCR results
        combined_text = ""
        for idx, result in enumerate(ocr_results, 1):
            if result["success"]:
                combined_text += f"\n--- Image {idx}: {result['filename']} ---\n"
                combined_text += result["extracted_text"]
                combined_text += "\n"
        
        if not combined_text.strip():
            return {
                "success": False,
                "structured_cards": [],
                "error": "No successful OCR results to summarize",
                "processing_time": 0.0
            }
        
        # Summarization prompt
        SUMMARY_PROMPT = f"""Analyze these visiting card OCR results and create a structured JSON output.

OCR RESULTS:
{combined_text}

Create a JSON array with one object per unique person/card. Combine front and back if they belong to same person.

Output format (JSON only, no markdown):
[
  {{
    "name": "Full Name",
    "role": "Job Title",
    "company": "Company Name",
    "phone": ["phone1", "phone2"],
    "email": ["email1@example.com"],
    "address": "Complete Address",
    "website": ["www.example.com"]
  }}
]

Rules:
- Merge front/back of same card into ONE entry
- Use arrays for multiple phones/emails/websites
- Use "null" for missing fields
- Return ONLY valid JSON array, nothing else"""
        
        # Create LLM model
        llm = create_litellm_model(model_id=model, temperature=temperature)
        
        messages = [
            SystemMessage(content="You are a data structuring expert. Convert OCR text into clean JSON. Output ONLY valid JSON, no explanations."),
            HumanMessage(content=SUMMARY_PROMPT)
        ]
        
        log.info(f"Summarizing {len(ocr_results)} OCR results into structured format...")
        
        # Process with LLM
        try:
            response = await llm.ainvoke(messages)
        except (AttributeError, NotImplementedError):
            import asyncio
            response = await asyncio.to_thread(llm.invoke, messages)
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        processing_time = time.time() - start_time
        
        # Try to parse JSON from response
        import json
        import re
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        if json_match:
            json_text = json_match.group(1)
        else:
            json_text = response_text
        
        # Clean up and parse
        json_text = json_text.strip()
        
        try:
            structured_cards = json.loads(json_text)
            if not isinstance(structured_cards, list):
                structured_cards = [structured_cards]
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON: {e}")
            log.error(f"Response was: {response_text[:500]}")
            return {
                "success": False,
                "structured_cards": [],
                "error": f"Failed to parse JSON: {str(e)}",
                "processing_time": round(processing_time, 2),
                "raw_response": response_text
            }
        
        log.info(f"✅ Summarization complete: {len(structured_cards)} card(s) structured in {processing_time:.2f}s")
        
        return {
            "success": True,
            "structured_cards": structured_cards,
            "error": None,
            "processing_time": round(processing_time, 2)
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        log.error(f"❌ Summarization failed: {e}")
        import traceback
        log.error(traceback.format_exc())
        
        return {
            "success": False,
            "structured_cards": [],
            "error": str(e),
            "processing_time": round(processing_time, 2)
        }


async def process_image_ocr(
    image_data: bytes,
    filename: str,
    mime_type: str,
    model: str = "gemini/gemini-flash-latest",
    temperature: float = 0.1
) -> Dict[str, Any]:
    """
    Process a single image for OCR using LiteLLM.
    
    Args:
        image_data: Raw image bytes
        filename: Original filename
        mime_type: MIME type of the image
        model: LiteLLM model to use
        temperature: Model temperature
    
    Returns:
        Dictionary with OCR results
    """
    import time
    start_time = time.time()
    
    try:
        from app.enhanced_litellm_wrapper import create_litellm_model
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Compact OCR prompt - essential info only for speed
        OCR_PROMPT = """Extract ONLY the essential information from this visiting card:

NAME: [full name]
ROLE: [job title/designation]
COMPANY: [company name]
PHONE: [phone number(s)]
EMAIL: [email address(es)]
ADDRESS: [complete business address]
WEBSITE: [website/URLs if present]

IMPORTANT:
- Extract text EXACTLY as shown
- If field not visible, write "Not found"
- Keep it concise - only core contact information
- For multiple values (phones/emails), separate with comma"""
        
        # Convert image to base64
        base64_content = base64.b64encode(image_data).decode('utf-8')
        
        # Create vision model
        vision_model = create_litellm_model(model_id=model, temperature=temperature)
        
        # Create multimodal message
        content = [
            {"type": "text", "text": f"{OCR_PROMPT}\n\nImage: {filename}"},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_content}"
                }
            }
        ]
        
        messages = [
            SystemMessage(content="You are a fast, accurate OCR system for visiting cards. Extract only: Name, Role, Company, Phone, Email, Address, Website. Be concise and precise."),
            HumanMessage(content=content)
        ]
        
        # Process with LiteLLM (use ainvoke if available, otherwise invoke)
        log.info(f"Processing OCR for {filename} with {model}")
        
        # Try async first, fall back to sync
        try:
            response = await vision_model.ainvoke(messages)
        except (AttributeError, NotImplementedError):
            # If ainvoke is not available, use sync invoke in thread pool
            import asyncio
            response = await asyncio.to_thread(vision_model.invoke, messages)
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        processing_time = time.time() - start_time
        
        log.info(f"✅ OCR completed for {filename} in {processing_time:.2f}s")
        
        return {
            "filename": filename,
            "success": True,
            "extracted_text": response_text,
            "error": None,
            "processing_time": round(processing_time, 2)
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        log.error(f"❌ OCR failed for {filename}: {e}")
        import traceback
        log.error(traceback.format_exc())
        
        return {
            "filename": filename,
            "success": False,
            "extracted_text": "",
            "error": str(e),
            "processing_time": round(processing_time, 2)
        }


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
        else:
            log.info("Conversation memory not enabled in configuration")
        
        # Preload configurations specified in environment for improved performance
        await preload_from_environment()
                
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
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "config_status": config_status,
        "available_agents": available_agents,
        "endpoints": {
            "health": "/health - Health check endpoint",
            "query": "/query - Main multi-agent query endpoint",
            "query_form": "/query/form - Form-based query endpoint",
            "worker": "/worker - Direct agent execution endpoint",
            "worker_upload": "/worker/upload - Agent execution with files",
            "multimodal": "/multimodal - Enhanced multimodal processing with LiteLLM",
            "issue_analysis": "/issue-analysis - Issue analysis pipeline endpoint",
            "issue_analysis_form": "/issue-analysis/form - Form-based issue analysis endpoint",
            "enhanced_issue_analysis": "/issue-analysis-enhanced - Enhanced issue analysis processing",
            "enhanced_issue_analysis_form": "/issue-analysis-enhanced/form - Form-based enhanced issue analysis",
            "submit_selection": "/submit-selection - Submit issue analysis selections",
            "consolidated_responses": "/consolidated-responses - Get consolidated user responses with date filtering",
            "consolidated_responses_form": "/consolidated-responses/form - Form-based consolidated responses endpoint",
            "ocr_fast": "/ocr/fast - Fast OCR processing for multiple images using LiteLLM",
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
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }
    except Exception as e:
        log.error(f"Error getting memory stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }


@app.get("/performance/stats")
async def performance_stats():
    """Get performance statistics including thread context tracking."""
    try:
        async with _metrics_lock:
            # Calculate average response time
            recent_times = [r["duration"] for r in _performance_metrics["response_times"][-50:]]
            avg_response_time = sum(recent_times) / len(recent_times) if recent_times else 0
            
            # Get thread context summary
            thread_summary = {}
            for thread_id, data in _performance_metrics["thread_contexts"].items():
                thread_summary[thread_id] = {
                    "turns": data["turns"],
                    "duration_minutes": (
                        datetime.fromisoformat(data["last_seen"]) - 
                        datetime.fromisoformat(data["first_seen"])
                    ).total_seconds() / 60,
                    "first_seen": data["first_seen"],
                    "last_seen": data["last_seen"]
                }
            
            return {
                "status": "success",
                "performance_stats": {
                    "total_requests": _performance_metrics["total_requests"],
                    "successful_requests": _performance_metrics["successful_requests"],
                    "failed_requests": _performance_metrics["failed_requests"],
                    "success_rate": (_performance_metrics["successful_requests"] / _performance_metrics["total_requests"] * 100) if _performance_metrics["total_requests"] > 0 else 0,
                    "average_response_time": avg_response_time,
                    "total_thread_contexts": len(_performance_metrics["thread_contexts"]),
                    "thread_contexts": thread_summary,
                    "recent_memory_operations": _performance_metrics["memory_operations"][-20:],
                    "recent_response_times": _performance_metrics["response_times"][-10:]
                },
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            }
    except Exception as e:
        log.error(f"Error getting performance stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
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
                                    description="Optional thread ID for conversation continuity"),
    files: List[UploadFile] = File(
        default=[], description="Optional files to upload and attach to the request"
    )
):
    """
    Query endpoint that accepts form data instead of JSON.

    Args:
        input: User question or prompt
        config_path: Optional path to config file
        raw_output: If True, returns only raw response as plain text
        thread_id: Optional thread ID for conversation continuity
        files: Optional files to upload and attach to the request

    Returns:
        QueryResponse with the human responder's final answer
    """
    # Convert form data to QueryRequest object
    request = QueryRequest(
        input=input,
        config_path=config_path,
        raw_output=raw_output,
        thread_id=thread_id,
        files=None  # Files are passed separately
    )

    # Use the existing query logic with files
    return await query_endpoint(request, files=files)


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest, files: List[UploadFile] = File(default=[])):
    """
    Main query endpoint that processes user input through multi-agent system.
    Now supports file uploads via multipart/form-data.

    Args:
        request: QueryRequest containing user input and optional config path
        files: Optional files to upload and attach to the request

    Returns:
        QueryResponse with the human responder's final answer
    """
    thread_id = get_or_create_thread_id(request.thread_id)
    
    async with track_performance("supervised_query", thread_id) as request_id:
        try:
            # Load configuration
            if request.config_path:
                try:
                    app_cfg = load_app_config(Path(request.config_path))
                    await track_memory_operation("config_loaded", thread_id, {"config_path": request.config_path})
                except Exception as e:
                    await track_memory_operation("config_load_failed", thread_id, {"config_path": request.config_path, "error": str(e)})
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

            log.info(f"[{request_id}] Using thread ID: {thread_id}")
            perf_log.info(f"[{request_id}] Processing query: {request.input[:100]}...")
            perf_log.info(f"[{request_id}] Raw output requested: {request.raw_output}")
            
            # Process uploaded files with file storage manager
            enhanced_input = request.input
            file_references = []
            file_info = []
            
            if files:
                log.info(f"[{request_id}] Processing {len(files)} uploaded files")
                file_manager = get_file_storage_manager()
                
                for file in files:
                    # Read file content
                    file_content = await file.read()
                    original_size = len(file_content)
                    
                    # Determine MIME type
                    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
                    
                    # Store file in memory with thread context (compression happens here)
                    reference_id = file_manager.store_file(
                        filename=file.filename,
                        content=file_content,
                        mime_type=mime_type,
                        thread_id=thread_id
                    )
                    
                    # Retrieve the stored file to get actual (compressed) size
                    stored_file = file_manager.get_file(reference_id)
                    actual_size = stored_file.size_bytes if stored_file else original_size
                    
                    # Log compression info if applicable
                    if stored_file and stored_file.compression_metadata:
                        comp_meta = stored_file.compression_metadata
                        log.info(
                            f"File {file.filename} compressed: {original_size:,} -> {actual_size:,} bytes "
                            f"({comp_meta.get('compression_ratio_percent', 0):.1f}% reduction)"
                        )
                    
                    file_references.append({
                        "reference_id": reference_id,
                        "filename": file.filename,
                        "mime_type": mime_type,
                        "size_bytes": actual_size,  # Use compressed size
                        "original_size_bytes": original_size,
                        "compressed": stored_file.compression_metadata is not None if stored_file else False
                    })
                    
                    file_info.append({
                        "reference_id": reference_id,
                        "filename": file.filename,
                        "size_bytes": actual_size,  # Use compressed size
                        "original_size_bytes": original_size,
                        "mime_type": mime_type,
                        "compressed": stored_file.compression_metadata is not None if stored_file else False
                    })
                    
                    log.info(
                        f"Stored file {file.filename} with reference_id={reference_id} "
                        f"(stored_size={actual_size} bytes, original_size={original_size} bytes, thread_id={thread_id})"
                    )
                
                # Enhance input with file reference IDs (NOT content)
                if file_references:
                    file_list = "\n".join([
                        f"- {ref['filename']} (reference_id: {ref['reference_id']}, "
                        f"type: {ref['mime_type']}, size: {ref['size_bytes']} bytes)"
                        for ref in file_references
                    ])
                    
                    enhanced_input = f"""{request.input}

**ATTACHED FILES (Reference IDs):**
{file_list}

**IMPORTANT**: Files are stored in memory. Use the `get_file_content(reference_id)` tool to retrieve file content when needed. DO NOT request file uploads again - files are already available via their reference IDs."""
            
            # Execute the multi-agent system with enhanced input that includes file information
            result = await run_supervised_api(
                enhanced_input, app_cfg, request.config_path, thread_id
            )

            # Prepare metadata
            files_count = len(files) if files else 0
            metadata = {
                "total_steps": len(result.get("steps", {})),
                "execution_time": result.get("execution_time"),
                "model_used": app_cfg.models.get("default", "unknown"),
                "files_uploaded": files_count,
                "file_info": file_info if files_count > 0 else None
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
                thread_id=thread_id
            )
        except Exception as e:
            log.error(f"Error processing query: {e}")
            log.exception("Full traceback for query processing error:")
            return QueryResponse(
                success=False,
                response="",
                error=str(e),
                thread_id=thread_id
            )


@app.post("/v1/query")
async def v1_query_endpoint(
    question: str = Form(..., description="User question or prompt"),
    config_name: str = Form(..., description="Config name to use"),
    file: List[UploadFile] = File(default=[], description="Optional files to upload"),
    thread_id: Optional[str] = Form(None, description="Optional thread ID for conversation continuity")
):
    """
    Legacy v1 endpoint for compatibility with v1/query format.
    Handles file uploads and routes to the supervisor via the main query endpoint.
    
    Args:
        question: User question or prompt
        config_name: Config name to use (without full path)
        file: List of files to upload
        thread_id: Optional thread ID for conversation continuity
        
    Returns:
        Response from query endpoint
    """
    try:
        # Construct full config path if not provided
        if not config_name.startswith("config/"):
            config_path = os.path.join("config", config_name)
        else:
            config_path = config_name
            
        # Create a QueryRequest object
        request = QueryRequest(
            input=question,
            config_path=config_path,
            raw_output=False,
            thread_id=thread_id
        )
        
        # Forward to query_endpoint
        log.info(f"v1/query endpoint called with config: {config_name}, files: {len(file)}")
        return await query_endpoint(request, files=file)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error processing v1/query request: {e}")
        return {
            "status": "error",
            "detail": str(e)
        }


@app.post("/worker", response_model=WorkerResponse)
async def worker_endpoint(request: WorkerRequest):
    """
    Direct worker endpoint that executes a specific agent without planning.

    Args:
        request: WorkerRequest containing agent name, input, and optional config

    Returns:
        WorkerResponse with the agent's direct response
    """
    thread_id = get_or_create_thread_id(request.thread_id)
    
    async with track_performance(f"worker_{request.agent_name}", thread_id) as request_id:
        try:
            # Load configuration
            if request.config_path:
                try:
                    app_cfg = load_app_config(Path(request.config_path))
                    await track_memory_operation("config_loaded", thread_id, {"config_path": request.config_path})
                except Exception as e:
                    await track_memory_operation("config_load_failed", thread_id, {"config_path": request.config_path, "error": str(e)})
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

            # Get or create thread ID and execute the agent
            log.info(f"[{request_id}] Using thread ID: {thread_id}")
            perf_log.info(f"[{request_id}] Executing agent '{request.agent_name}' with input: {request.input[:100]}...")
            
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
                thread_id=thread_id
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
                thread_id=thread_id
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
    files: List[UploadFile] = File(
        default=[], description="Optional files to upload and attach to the request"
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

        # Files parameter is now a list with default empty list
        # No need to check for None

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


@app.post("/multimodal")
async def multimodal_endpoint(
    model: str = Form(..., description="LiteLLM model ID (e.g., 'openai/gpt-4o', 'gemini/gemini-2.5-flash-lite')"),
    prompt: str = Form(..., description="Text prompt for the model"),
    thread_id: Optional[str] = Form(None, description="Optional thread ID for conversation continuity"),
    temperature: float = Form(0.2, description="Model temperature (0.0 to 1.0)"),
    files: List[UploadFile] = File(default=[], description="Optional files to upload (images, documents)"),
    system_message: Optional[str] = Form("You are a helpful assistant.", description="System message for the model")
):
    """
    Enhanced multimodal endpoint using LiteLLM with support for images, files, and conversation continuity.
    
    Supports all LiteLLM providers:
    - OpenAI: openai/gpt-4o, openai/gpt-4o-mini  
    - Google Gemini: gemini/gemini-2.5-flash-lite, google/gemini-2.5-flash-lite
    - Anthropic: anthropic/claude-3-5-sonnet
    - Azure OpenAI: azure/gpt-4.1
    
    Args:
        model: LiteLLM model identifier
        prompt: Text prompt for the model
        thread_id: Optional thread ID for conversation continuity
        temperature: Model temperature setting
        files: List of files to upload (images, documents)
        system_message: System message for the model
        
    Returns:
        Multimodal response with file analysis and conversation context
    """
    if not HAS_ENHANCED_LITELLM:
        raise HTTPException(
            status_code=501,
            detail="Enhanced LiteLLM is not available. Please install litellm package."
        )
    
    try:
        # Validate model format
        if not is_litellm_model(model):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid LiteLLM model format: {model}. Use format: provider/model (e.g., 'openai/gpt-4o')"
            )
        
        # Get or create thread ID
        actual_thread_id = get_or_create_thread_id(thread_id)
        log.info(f"Processing multimodal request with model {model}, thread: {actual_thread_id}")
        
        # Process uploaded files
        temp_files = []
        image_paths = []
        document_paths = []
        file_info = []
        
        try:
            for file in files:
                # Save file to temporary location
                file_content = await file.read()
                import tempfile
                temp_dir = Path(tempfile.mkdtemp())
                temp_file_path = temp_dir / file.filename
                temp_file_path.write_bytes(file_content)
                temp_files.append(temp_file_path)
                
                # Categorize file type
                mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
                
                if mime_type and mime_type.startswith('image/'):
                    image_paths.append(str(temp_file_path))
                    file_info.append({
                        "filename": file.filename,
                        "type": "image",
                        "mime_type": mime_type,
                        "size": len(file_content)
                    })
                else:
                    document_paths.append(str(temp_file_path))
                    file_info.append({
                        "filename": file.filename,
                        "type": "document",
                        "mime_type": mime_type,
                        "size": len(file_content)
                    })
                
                log.info(f"Processed file: {file.filename} ({mime_type})")
            
            # Create enhanced LiteLLM model
            model_instance = EnhancedLiteLLMChat(
                model=model,
                temperature=temperature,
                timeout=60
            )
            
            # Check model capabilities
            capabilities = model_instance.check_capabilities()
            log.info(f"Model capabilities: {capabilities}")
            
            # Inject conversation context if thread exists
            enhanced_prompt = inject_conversation_context(actual_thread_id, prompt)
            
            # Create multimodal message
            multimodal_message = model_instance.create_multimodal_message(
                text=enhanced_prompt,
                images=image_paths if capabilities.get("supports_vision", False) else None,
                files=document_paths if capabilities.get("supports_files", False) else None
            )
            
            # Add system message
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=system_message), multimodal_message]
            
            # Generate response
            import time
            start_time = time.time()
            result = await model_instance._agenerate(messages)
            end_time = time.time()
            
            response_content = result.generations[0].message.content
            processing_time = round(end_time - start_time, 2)
            
            # Store conversation turn
            store_conversation_turn(
                thread_id=actual_thread_id,
                user_message=prompt,
                assistant_response=response_content
            )
            
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        temp_file.parent.rmdir()
                except Exception as e:
                    log.warning(f"Failed to clean up temp file {temp_file}: {e}")
            
            return {
                "success": True,
                "response": response_content,
                "model": model,
                "thread_id": actual_thread_id,
                "processing_time": processing_time,
                "capabilities": capabilities,
                "files_processed": len(files),
                "file_info": file_info,
                "conversation_context_used": enhanced_prompt != prompt
            }
            
        except Exception as file_error:
            # Clean up temporary files in case of error
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        temp_file.parent.rmdir()
                except:
                    pass
            raise file_error
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in multimodal endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal processing failed: {str(e)}"
        )


@app.post("/ocr/fast", response_model=FastOCRResponse)
async def fast_ocr_endpoint(
    files: List[UploadFile] = File(..., description="Visiting card images to process (supports jpg, png, jpeg, webp, etc.) - can include front and back sides"),
    model: str = Form("gemini/gemini-flash-latest", description="LiteLLM model ID to use for OCR (default: Gemini Flash for speed)"),
    temperature: float = Form(0.1, description="Model temperature (0.0 to 1.0, lower is more deterministic)"),
    structured_output: bool = Form(True, description="Return structured output with metadata")
):
    """
    Fast OCR endpoint for visiting cards (business cards) using LiteLLM with Gemini Flash.
    
    This endpoint is optimized for extracting structured information from visiting cards,
    including front and back sides. It processes multiple cards in parallel and returns
    structured text extraction with contact details, addresses, and all visible information.
    
    Features:
    - Specialized for visiting cards (business cards)
    - Extracts structured contact information (name, title, company, phone, email, address)
    - Handles both front and back sides of cards
    - Supports multiple cards in a single request
    - Parallel processing for maximum speed
    - Multi-language support
    - Identifies QR codes, logos, and special elements
    - Uses LiteLLM with Gemini Flash for optimal speed and accuracy
    
    Supported models:
    - gemini/gemini-flash-latest (default, fastest)
    - gemini/gemini-pro-vision
    - openai/gpt-4o
    - openai/gpt-4o-mini
    - anthropic/claude-3-5-sonnet
    
    Args:
        files: List of visiting card images (front/back sides) to process
        model: LiteLLM model identifier (default: gemini/gemini-flash-latest)
        temperature: Model temperature for deterministic output (0.1 recommended)
        structured_output: Return structured JSON response
    
    Returns:
        FastOCRResponse with structured contact information extracted from each card image,
        including name, title, company, phone, email, address, and all visible text
    
    Example Response Structure:
        Each result will contain structured fields like:
        - Full Name, Job Title, Company/Organization
        - Phone Numbers, Email Addresses, Websites
        - Office/Business Address
        - Tagline, Services, QR Code presence
        - Card Side (Front/Back), Language, Quality notes
    """
    import time
    import asyncio
    
    start_time = time.time()
    
    try:
        # Validate files
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="No files provided. Please upload at least one image."
            )
        
        log.info(f"Starting fast OCR for {len(files)} images using {model}")
        
        # Validate file types
        valid_image_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
        
        for file in files:
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            if mime_type not in valid_image_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {file.filename}. Supported types: JPEG, PNG, WEBP, GIF, BMP"
                )
        
        # Process all images in parallel for maximum speed
        tasks = []
        for file in files:
            # Read file content
            file_content = await file.read()
            mime_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            
            # Create OCR task (process_image_ocr is already async)
            task = process_image_ocr(
                image_data=file_content,
                filename=file.filename,
                mime_type=mime_type,
                model=model,
                temperature=temperature
            )
            tasks.append(task)
        
        # Execute all OCR tasks in parallel
        log.info(f"Processing {len(tasks)} images in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions from gather
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                # If task raised an exception, create error result
                log.error(f"Task {idx} raised exception: {result}")
                processed_results.append({
                    "filename": files[idx].filename if idx < len(files) else f"image_{idx}",
                    "success": False,
                    "extracted_text": "",
                    "error": str(result),
                    "processing_time": 0.0
                })
            else:
                processed_results.append(result)
        
        # Calculate statistics
        total_processing_time = time.time() - start_time
        successful_count = sum(1 for r in processed_results if r["success"])
        failed_count = len(processed_results) - successful_count
        
        log.info(
            f"✅ Fast OCR completed: {successful_count}/{len(processed_results)} successful, "
            f"total time: {total_processing_time:.2f}s"
        )
        
        # Summarize all OCR results into structured format (only if successful results exist)
        structured_cards = []
        summarization_time = 0.0
        
        if successful_count > 0:
            log.info("Starting final summarization to combine and structure cards...")
            summary_result = await summarize_visiting_cards(
                ocr_results=processed_results,
                model=model,
                temperature=0.0
            )
            
            if summary_result["success"]:
                structured_cards = summary_result["structured_cards"]
                summarization_time = summary_result["processing_time"]
                log.info(f"✅ Structured {len(structured_cards)} unique card(s)")
            else:
                log.warning(f"⚠️ Summarization failed: {summary_result.get('error')}")
        
        # Update total processing time to include summarization
        total_time_with_summary = total_processing_time + summarization_time
        
        # Build response (without raw results - only structured output)
        response = FastOCRResponse(
            success=successful_count > 0,
            message=f"Processed {len(processed_results)} images: {successful_count} successful, {failed_count} failed. Structured {len(structured_cards)} card(s).",
            structured_cards=structured_cards,
            total_images=len(processed_results),
            successful_count=successful_count,
            failed_count=failed_count,
            total_processing_time=round(total_time_with_summary, 2),
            summarization_time=round(summarization_time, 2),
            model_used=model,
            timestamp=datetime.now(timezone.utc).isoformat() + "Z"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in fast OCR endpoint: {e}")
        import traceback
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Fast OCR processing failed: {str(e)}"
        )


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
