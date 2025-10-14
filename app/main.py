"""JK-Agents Framework main module."""

import argparse
import asyncio
import functools
import json
import logging
import os
import re
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda **kwargs: None

# Try to import as a module, otherwise look for the library in parent dir
try:
    from jk_agents_framework.prompt_loader import load_prompt_content
    from jk_agents_framework.render_template import render_prompt_with_placeholders
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

# Local imports
from .log_config import setup_logging
from .types import AppConfig, AgentConfig
from .prompt_loader import load_prompt_content, get_config_directory
from .template_utils import render_prompt_with_placeholders
from .llm_payload_logger import LoggingModelWrapper, LLMPayloadLogger

# Import LiteLLM provider (optional)
try:
    from .litellm_provider import LiteLLMProvider
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

# Import custom Azure LiteLLM wrapper
try:
    from .azure_litellm_wrapper import AzureLiteLLMChat
    HAS_AZURE_LITELLM = True
except ImportError:
    HAS_AZURE_LITELLM = False

# Import enhanced LiteLLM wrapper with multimodal support
try:
    from .enhanced_litellm_wrapper import EnhancedLiteLLMChat, is_litellm_model, create_litellm_model
    HAS_ENHANCED_LITELLM = True
except ImportError:
    HAS_ENHANCED_LITELLM = False

# Import the agent builder function
from .agent_builder import build_react_agent

log = logging.getLogger("app")

def process_business_context_template(
    business_context: str, placeholder_context: Optional[Dict[str, Any]] = None
) -> str:
    """Process the business_context string as a template with placeholders."""
    if not business_context:
        return ""

    try:
        # Render the business context template
        return render_prompt_with_placeholders(
            business_context,
            placeholder_context=placeholder_context,
        )
    except Exception as e:
        log.warning(f"Failed to process business_context template: {e}")
        return business_context  # Return original if processing fails


# Import model format normalizer if available
try:
    from .config_model_format import normalize_model_config
    HAS_MODEL_FORMAT = True
except ImportError:
    HAS_MODEL_FORMAT = False

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
    
    # Normalize model formats if the utility is available
    if HAS_MODEL_FORMAT:
        try:
            data = normalize_model_config(data)
            log.info(f"Model formats normalized for config {cfg_path.name}")
        except Exception as e:
            log.warning(f"Failed to normalize model formats: {e}")

    # If Azure OpenAI env is present, switch provider prefix to azure_openai
    # unless an OpenAI-compatible BASE_URL is explicitly set (e.g., LM Studio)
    is_azure = bool(
        os.getenv("AZURE_OPENAI_API_KEY")
        and os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    openai_base_url = (
        os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
    )
    force_openai = bool(
        openai_base_url
        and not re.search(r"openai\.azure\.com", openai_base_url or "")
    )
    using_azure_without_explicit_custom_url = is_azure and not force_openai

    # Try to load models.supervisor; if not present, load models.default
    # For Google prefix, also add gemini version
    model_names_to_try = [models.get("supervisor"), models.get("default")]
    
    # Automatically handle Google/Gemini format variations 
    if model_names_to_try[0] and 'google:gemini' in model_names_to_try[0]:
        model_names_to_try.append(model_names_to_try[0].replace('google:', 'gemini/'))
    elif model_names_to_try[0] and 'gemini/' in model_names_to_try[0]:
        model_names_to_try.append(model_names_to_try[0].replace('gemini/', 'google:gemini-'))

    for k, v in list(data.items()):
        # Attempt to auto-expand prompt file references
        if isinstance(v, str) and v.startswith("file:"):
            filename = v[5:].strip()
            config_dir = get_config_directory()
            full_path = config_dir / filename
            if full_path.exists():
                data[k] = load_prompt_content(filename)
                log.info(f"Loaded prompt from file: {filename}")
            else:
                log.warning(f"Prompt file not found: {full_path}")
        # Log any overrides from environment
        if k.upper() in os.environ:
            log.info(f"Overriding {k} from environment variable")
            data[k] = os.environ[k.upper()]

    # Attempt to create an AppConfig from the loaded data, defaults as needed
    try:
        app_cfg = AppConfig(**data)
        return app_cfg
    except Exception as e:
        log.warning(f"Failed to parse AppConfig: {e}")
        app_cfg = AppConfig()
        app_cfg.business_context = data.get("business_context", "")
        return app_cfg

async def build_agents_map(app_cfg: AppConfig, user_input: str = "", config_path: Optional[str] = None):
    """
    Build map of agent instances from AppConfig.
    
    Args:
        app_cfg: Application configuration
        user_input: Optional user input to be used as context for agents
        config_path: Optional path to the config file used (for caching)
        
    Returns:
        Tuple of (agents_map, mcp_clients)
    """
    log.info(f"Building agents map with {len(app_cfg.agents)} defined agents")
    
    agents_map = {}
    mcp_clients = {}
    
    # Process business context if available
    processed_business_context = process_business_context_template(app_cfg.business_context or "")
    
    # Create app_config dict for build_agent function
    app_config_dict = app_cfg.model_dump() if hasattr(app_cfg, 'model_dump') else app_cfg.__dict__
    
    for agent_cfg in app_cfg.agents:
        # Set model if not specified in agent config
        if not agent_cfg.model:
            agent_cfg.model = app_cfg.models.get("default", "openai:gpt-4o-mini")
            
        # Create agent instance
        agent, mcp_client = await build_react_agent(
            agent_cfg, 
            default_model=app_cfg.models.get("default", "openai:gpt-4o-mini"),
            business_context=processed_business_context,
            original_user_question=user_input,
            config_path=config_path,
            app_config=app_config_dict
        )
        
        # Add to map
        agents_map[agent_cfg.name] = agent
        
        # Add MCP client if any
        if mcp_client:
            # Handle MultiServerMCPClient object - it doesn't have .items() method
            # Instead, we'll just store it with a default name
            if hasattr(mcp_client, 'servers'):
                # MultiServerMCPClient has 'servers' attribute, extract server names
                for server_name in mcp_client.servers.keys():
                    if server_name not in mcp_clients:
                        mcp_clients[server_name] = mcp_client
            else:
                # Fallback: add the client with a default name
                if 'mcp_default' not in mcp_clients:
                    mcp_clients['mcp_default'] = mcp_client
    
    log.info(f"Built {len(agents_map)} agents")
    return agents_map, mcp_clients
