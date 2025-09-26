from __future__ import annotations
import argparse
import asyncio
import logging
from pathlib import Path
import os
import signal
import sys
from dotenv import load_dotenv
from typing import Dict, Optional

import yaml
from langchain_core.runnables import RunnableConfig

from .config import AppConfig, AgentConfig
from .agent_builder import build_react_agent
from .supervisor_builder import build_supervisor_compiled
from .planner_executor import execute_plan
from .mcp_loader import close_mcp_client
from .markdown_formatter import (
    format_result_as_markdown,
    format_direct_agent_result
)
from .direct_agent_logger import create_direct_agent_logger
from .thread_manager import get_or_create_thread_id
from langchain_mcp_adapters.client import MultiServerMCPClient
from .template_utils import render_prompt_with_placeholders
from .placeholder_system import PlaceholderContext


log = logging.getLogger("app.main")
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


def process_business_context_template(business_context: str) -> str:
    """Process template variables in business_context."""
    if not business_context or not isinstance(business_context, str):
        return business_context or ""
    
    try:
        # Create placeholder context
        placeholder_context = PlaceholderContext()
        
        # Render the business context template
        return render_prompt_with_placeholders(
            business_context,
            placeholder_context=placeholder_context,
        )
    except Exception as e:
        log.warning(f"Failed to process business_context template: {e}")
        return business_context  # Return original if processing fails


def load_app_config(cfg_path: Path | None = None) -> AppConfig:
    """Load YAML at config/agents.yaml into AppConfig."""
    # Load .env from repo root if present
    try:
        load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
    except Exception:
        pass
    
    # Ensure OPENAI_API_VERSION is set if we have Azure OpenAI config
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    if azure_api_version and not os.getenv("OPENAI_API_VERSION"):
        os.environ["OPENAI_API_VERSION"] = azure_api_version
    
    if cfg_path is None:
        cfg_path = (
            Path(__file__).resolve().parents[1] / "config" / "agents.yaml"
        )
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found at {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    # Normalize config: move misnested temperature out of models,
    # and ensure string values in the models map
    models = data.get("models", {}) or {}
    if "temperature" in models and "temperature" not in data:
        data["temperature"] = models.get("temperature")
        models.pop("temperature", None)
    # Coerce model map values to strings
    models = {str(k): str(v) for k, v in models.items() if v is not None}
    data["models"] = models

    # If Azure OpenAI env is present, switch provider prefix to azure_openai
    # unless an OpenAI-compatible BASE_URL is explicitly set (e.g., LM Studio)
    is_azure = bool(
        os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    openai_base_url = (
        os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
    )
    if is_azure and not openai_base_url:
        # Normalize endpoint (remove trailing slash) for SDK compatibility
        ep = os.getenv("AZURE_OPENAI_ENDPOINT")
        if ep and ep.endswith("/"):
            os.environ["AZURE_OPENAI_ENDPOINT"] = ep.rstrip("/")

        # If a deployment name is specified, use it as the model id
        # after the provider prefix
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        def _to_azure(mid: str) -> str:
            if not isinstance(mid, str):
                return mid
            if mid.startswith("azure_openai:"):
                return mid
            if mid.startswith("openai:"):
                model_tail = deployment or mid.split("openai:", 1)[1]
                return "azure_openai:" + model_tail
            return mid

        # Rewrite model ids in-place to azure_openai:*
        data["models"] = {
            k: _to_azure(v) for k, v in data["models"].items()
        }

        # Also adjust agent-specific and supervisor model ids if given
        agents_list = data.get("agents") or []
        for a in agents_list:
            if isinstance(a, dict) and a.get("model"):
                a["model"] = _to_azure(str(a["model"]))
        if isinstance(data.get("supervisor"), dict):
            sm = data["supervisor"].get("model")
            if sm:
                data["supervisor"]["model"] = _to_azure(str(sm))
    # Pydantic will coerce nested dicts to proper models
    return AppConfig(**data)


async def build_agents_map(
    app_cfg: AppConfig,
    *,
    user_input: str = "",
    config_path: Optional[str] = None
):
    """Build agents and return agent map and MCP clients for cleanup.

    Pass original user input to allow Jinja2 prompt rendering.
    """
    agents_map: Dict[str, object] = {}
    mcp_clients: Dict[str, Optional[MultiServerMCPClient]] = {}

    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
    
    # Convert AppConfig to dict for memory configuration
    app_config_dict = app_cfg.model_dump() if hasattr(app_cfg, 'model_dump') else (app_cfg.dict() if hasattr(app_cfg, 'dict') else app_cfg.__dict__)
    
    # Process business context template
    processed_business_context = process_business_context_template(app_cfg.business_context or "")
    
    for a in app_cfg.agents:
        compiled, mcp_client = await build_react_agent(
            a,
            default_model,
            business_context=processed_business_context,
            original_user_question=user_input or "",
            dependent_request_responses="",
            config_path=config_path,
            enable_llm_payload_logging=False,  # Disable for supervisor mode to avoid log clutter
            default_temperature=app_cfg.temperature,
            app_config=app_config_dict,
        )
        agents_map[a.name] = compiled
        if mcp_client:
            mcp_clients[a.name] = mcp_client
    return agents_map, mcp_clients


async def run_direct_agent(
    agent_name: str, user_input: str, app_cfg: AppConfig, thread_id: Optional[str] = None
):
    # Convert AppConfig to dict and reset checkpointer with proper config
    app_config_dict = app_cfg.model_dump() if hasattr(app_cfg, 'model_dump') else (app_cfg.dict() if hasattr(app_cfg, 'dict') else app_cfg.__dict__)
    from .checkpointer_manager import reset_checkpointer_with_config
    reset_checkpointer_with_config(app_config_dict)
    
    # Process business context template
    processed_business_context = process_business_context_template(app_cfg.business_context or "")
    
    # Initialize logger
    logger = create_direct_agent_logger(
        agent_name=agent_name,
        user_input=user_input,
        business_context=processed_business_context
    )

    success = False
    error_message = ""

    try:
        default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
        # find agent config
        target: Optional[AgentConfig] = next(
            (a for a in app_cfg.agents if a.name == agent_name), None
        )
        if not target:
            raise SystemExit(f"Agent '{agent_name}' not found in config")

        # Convert AppConfig to dict for memory configuration
        app_config_dict = app_cfg.model_dump() if hasattr(app_cfg, 'model_dump') else (app_cfg.dict() if hasattr(app_cfg, 'dict') else app_cfg.__dict__)
        
        compiled, mcp_client = await build_react_agent(
            target,
            default_model,
            business_context=processed_business_context,
            original_user_question=user_input,
            dependent_request_responses="",
            config_path=None,  # Direct agent calls don't have config path
            enable_llm_payload_logging=True,
            llm_payload_logger=logger.get_llm_payload_logger(),
            default_temperature=app_cfg.temperature,
            app_config=app_config_dict,
        )

        try:
            system_context = (
                "Business context:\n"
                f"{processed_business_context}\n\n"
                "Previous step results:\n(none)"
            )

            # Log the request
            logger.log_agent_request(
                compiled_agent=compiled,
                system_context=system_context,
                user_task=user_input
            )

            state = {"messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": user_input},
            ]}
            # Use provided thread ID or generate unique thread ID for CLI execution
            actual_thread_id = get_or_create_thread_id(thread_id)
            print(f"Using thread ID: {actual_thread_id}")
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

            # Format as user-friendly Markdown
            formatted_output = format_direct_agent_result(
                content=text,
                agent_name=agent_name,
                user_input=user_input
            )
            print(formatted_output)
            success = True

        finally:
            await close_mcp_client(mcp_client)

    except Exception as e:
        error_message = str(e)
        raise
    finally:
        # Log execution summary
        logger.log_execution_summary(success=success, error_message=error_message)
        if logger.get_log_file_path():
            print(f"\nLog saved to: {logger.get_log_file_path()}")


async def run_supervised(user_input: str, app_cfg: AppConfig, thread_id: Optional[str] = None):
    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
    
    # Convert AppConfig to dict and reset checkpointer with proper config
    app_config_dict = app_cfg.model_dump() if hasattr(app_cfg, 'model_dump') else (app_cfg.dict() if hasattr(app_cfg, 'dict') else app_cfg.__dict__)
    from .checkpointer_manager import reset_checkpointer_with_config
    reset_checkpointer_with_config(app_config_dict)
    
    # Process business context template
    processed_business_context = process_business_context_template(app_cfg.business_context or "")
    
    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_cfg.supervisor,
        app_cfg.agents,
        default_model,
        processed_business_context,
        original_user_question=user_input,
        config_path=None,  # CLI calls don't have config path
        default_temperature=app_cfg.temperature,
    )
    # Build workers
    agents_map, mcp_clients = await build_agents_map(
        app_cfg, user_input=user_input, config_path=None
    )
    try:
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=user_input,
            business_context=processed_business_context,
            default_model_for_verifier=default_model,
            agents_configs=app_cfg.agents,
            default_model=default_model,
            thread_id=thread_id,
        )
        # Format as user-friendly Markdown
        formatted_output = format_result_as_markdown(
            result=result,
            user_input=user_input,
            business_context=processed_business_context
        )
        print(20*"**")
        print(formatted_output)
        print(20*"**")
    finally:
        # Cleanup MCP clients
        for client in mcp_clients.values():
            await close_mcp_client(client)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run jk-agents with configured MCP agents."
    )
    p.add_argument("prompt", help="User prompt to execute")
    p.add_argument(
        "--agent",
        help="Run a specific agent directly (skip supervisor)",
    )
    p.add_argument("--config", help="Path to agents.yaml", default=None)
    p.add_argument(
        "--thread-id",
        help="Thread ID for conversation continuity (optional)",
        default=None
    )
    return p.parse_args()


def signal_handler(signum, frame):
    """Handle keyboard interrupt gracefully."""
    print("\n\n⚠️  Operation interrupted by user. Exiting gracefully...")
    sys.exit(0)


def main():
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        args = parse_args()
        cfg = load_app_config(Path(args.config) if args.config else None)
        thread_id = getattr(args, 'thread_id', None)  # Get thread_id from args
        if args.agent:
            asyncio.run(run_direct_agent(args.agent, args.prompt, cfg, thread_id=thread_id))
        else:
            asyncio.run(run_supervised(args.prompt, cfg, thread_id=thread_id))
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        log.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
