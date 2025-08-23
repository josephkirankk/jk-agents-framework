"""
FastAPI web server for jk-agents system.

Provides HTTP endpoints to interact with the multi-agent system.
"""
from __future__ import annotations

import logging
import base64
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .config import AppConfig, AgentConfig
from .main import load_app_config, build_agents_map
from .supervisor_builder import build_supervisor_compiled
from .planner_executor import execute_plan
from .mcp_loader import close_mcp_client
from .agent_builder import build_react_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("app.api")

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
    file_info: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run a direct agent with file attachments.

    This is a modified version of run_direct_agent_api that handles file attachments
    by constructing multimodal messages with file references.
    """
    from langchain_core.runnables import RunnableConfig

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

        # Create the message with multimodal content
        # human_message = HumanMessage(content=message_content)  # For future use

        state = {
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": message_content},
            ]
        }
        config: RunnableConfig = {"configurable": {"thread_id": "test-thread"}}

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

        return {
            "success": True,
            "response": text,
            "agent_name": agent_name,
            "raw_output": out,
        }

    finally:
        await close_mcp_client(mcp_client)


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
    agent_name: str, user_input: str, app_cfg: AppConfig
) -> Dict[str, Any]:
    """
    Run a direct agent and return structured results for API use.

    This is a modified version of run_direct_agent that returns data
    instead of printing.
    """
    from langchain_core.runnables import RunnableConfig

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
    )

    try:
        system_context = (
            "Business context:\n"
            f"{app_cfg.business_context or ''}\n\n"
            "Previous step results:\n(none)"
        )
        state = {
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_input},
            ]
        }
        config: RunnableConfig = {"configurable": {"thread_id": "test-thread"}}

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

        return {
            "success": True,
            "response": text,
            "agent_name": agent_name,
            "raw_output": out,
        }

    finally:
        await close_mcp_client(mcp_client)


async def run_supervised_api(
    user_input: str, app_cfg: AppConfig
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
    )

    # Build workers
    agents_map, mcp_clients = await build_agents_map(
        app_cfg, user_input=user_input
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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


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
        
        # Execute the multi-agent system
        log.info(f"Processing query: {request.input[:100]}...")
        log.info(f"Raw output requested: {request.raw_output}")
        result = await run_supervised_api(request.input, app_cfg)

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
                metadata=metadata
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error processing query: {e}")
        return QueryResponse(
            success=False,
            response="",
            error=str(e)
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
    files: List[UploadFile] = File(..., description="Files to upload and attach to the request")
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

        # Process uploaded files
        file_ids = []
        file_info = []

        csv_data_sections = []

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
        log.info(f"Executing agent '{agent_name}' with {len(files)} attached files")
        result = await run_direct_agent_with_files(
            agent_name, enhanced_input, app_cfg, file_ids, file_info
        )

        # Prepare metadata
        metadata = {
            "agent_name": agent_name,
            "model_used": app_cfg.models.get("default", "unknown"),
            "business_context": bool(app_cfg.business_context),
            "files_uploaded": len(files),
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
                "metadata": metadata
            }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error executing worker '{agent_name}' with files: {e}")
        return {
            "success": False,
            "response": "",
            "agent_name": agent_name,
            "error": str(e)
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
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{request.agent_name}' not found. Available agents: {', '.join(agent_names)}"
            )

        # Execute the agent directly
        log.info(f"Executing agent '{request.agent_name}' with input: {request.input[:100]}...")
        result = await run_direct_agent_api(
            request.agent_name, request.input, app_cfg
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
                raw_data=None
            )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error executing worker '{request.agent_name}': {e}")
        return WorkerResponse(
            success=False,
            response="",
            agent_name=request.agent_name,
            error=str(e),
            metadata=None,
            raw_data=None
        )


# Legacy endpoint for backward compatibility
@app.post("/plan_and_run")
async def plan_and_run_endpoint(request: QueryRequest):
    """Legacy endpoint - redirects to /query."""
    return await query_endpoint(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
