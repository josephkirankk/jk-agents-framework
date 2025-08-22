from __future__ import annotations
import argparse
import asyncio
import logging
from pathlib import Path
import os
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
from langchain_mcp_adapters.client import MultiServerMCPClient


log = logging.getLogger("app.main")
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
)


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
    is_azure = bool(
        os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    if is_azure:
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

        data["models"] = {k: _to_azure(v) for k, v in data["models"].items()}

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


async def build_agents_map(app_cfg: AppConfig):
    """Build agents and return agent map and MCP clients for cleanup."""
    agents_map: Dict[str, object] = {}
    mcp_clients: Dict[str, Optional[MultiServerMCPClient]] = {}

    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
    for a in app_cfg.agents:
        compiled, mcp_client = await build_react_agent(a, default_model)
        agents_map[a.name] = compiled
        if mcp_client:
            mcp_clients[a.name] = mcp_client
    return agents_map, mcp_clients


async def run_direct_agent(
    agent_name: str, user_input: str, app_cfg: AppConfig
):
    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
    # find agent config
    target: Optional[AgentConfig] = next(
        (a for a in app_cfg.agents if a.name == agent_name), None
    )
    if not target:
        raise SystemExit(f"Agent '{agent_name}' not found in config")

    compiled, mcp_client = await build_react_agent(target, default_model)
    try:
        system_context = (
            "Business context:\n"
            f"{app_cfg.business_context or ''}\n\n"
            "User goal:\n"
            f"{user_input}\n\n"
            "Previous step results:\n(none)"
        )
        state = {"messages": [
            {"role": "system", "content": system_context},
            {"role": "user", "content": user_input},
        ]}
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
        
        # Format as user-friendly Markdown
        formatted_output = format_direct_agent_result(
            content=text,
            agent_name=agent_name,
            user_input=user_input
        )
        print(formatted_output)
    finally:
        await close_mcp_client(mcp_client)


async def run_supervised(user_input: str, app_cfg: AppConfig):
    default_model = app_cfg.models.get("default", "openai:gpt-4o-mini")
    # Build supervisor
    supervisor = build_supervisor_compiled(
        app_cfg.supervisor,
        app_cfg.agents,
        default_model,
        app_cfg.business_context or "",
    )
    # Build workers
    agents_map, mcp_clients = await build_agents_map(app_cfg)
    try:
        result = await execute_plan(
            supervisor_compiled=supervisor,
            agents_map=agents_map,
            user_input=user_input,
            business_context=app_cfg.business_context or "",
            default_model_for_verifier=default_model,
        )
        # Format as user-friendly Markdown
        formatted_output = format_result_as_markdown(
            result=result,
            user_input=user_input,
            business_context=app_cfg.business_context
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
    return p.parse_args()


def main():
    args = parse_args()
    cfg = load_app_config(Path(args.config) if args.config else None)
    if args.agent:
        asyncio.run(run_direct_agent(args.agent, args.prompt, cfg))
    else:
        asyncio.run(run_supervised(args.prompt, cfg))


if __name__ == "__main__":
    main()
