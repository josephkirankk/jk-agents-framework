"""
FastAPI web server for jk-agents system.

Provides HTTP endpoints to interact with the multi-agent system.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import AppConfig
from .main import load_app_config, build_agents_map
from .supervisor_builder import build_supervisor_compiled
from .planner_executor import execute_plan
from .mcp_loader import close_mcp_client

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


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    input: str = Field(..., description="User question or prompt", min_length=1)
    config_path: Optional[str] = Field(
        None, description="Optional path to config file"
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


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")


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
        result = await run_supervised_api(request.input, app_cfg)
        
        # Extract human response
        human_response = await extract_human_response(result)
        
        # Prepare metadata
        metadata = {
            "total_steps": len(result.get("steps", {})),
            "execution_time": result.get("execution_time"),
            "model_used": app_cfg.models.get("default", "unknown")
        }
        
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


# Legacy endpoint for backward compatibility
@app.post("/plan_and_run")
async def plan_and_run_endpoint(request: QueryRequest):
    """Legacy endpoint - redirects to /query."""
    return await query_endpoint(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
