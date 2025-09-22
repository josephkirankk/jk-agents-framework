from __future__ import annotations
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .checkpointer_manager import get_global_checkpointer
from .mcp_loader import load_mcp_tools, build_http_tools
from .python_tool_loader import (
    load_python_function_tools,
    validate_python_tools
)
from .config import AgentConfig
from .template_utils import render_prompt, render_prompt_with_placeholders
from .placeholder_system import PlaceholderContext
from .gemini_schema_filter import apply_gemini_schema_filtering
from .prompt_loader import load_prompt_content, get_config_directory
from .llm_payload_logger import LoggingModelWrapper, LLMPayloadLogger

log = logging.getLogger("agent_builder")


def create_model_instance(
    model_id: str, default_temperature: float = 0.2
) -> Any:
    """
    Create a model instance based on the model ID prefix.

    Args:
        model_id: Model ID string like "google:gemini-2.0-flash-exp",
                 "openai:gpt-4o", "anthropic:claude-sonnet-4", etc.
                 Can also include temperature like
                 "google:gemini-2.5-flash-lite:0.2"
        default_temperature: Default temperature to use if not specified
                           in model_id

    Returns:
        Either the original model_id string (for LangGraph built-in support)
        or a model instance (for custom providers like Google Gemini)
    """
    if not isinstance(model_id, str):
        return model_id

    # Parse temperature from model_id if present
    # Format: "provider:model:temperature" or "provider:model"
    parts = model_id.split(":")
    temperature = default_temperature

    if len(parts) >= 3:
        try:
            # Try to parse the last part as temperature
            temperature = float(parts[-1])
            # Reconstruct model_id without temperature for processing
            model_id_without_temp = ":".join(parts[:-1])
            log.info(
                "Parsed temperature %s from model ID %s", temperature, model_id
            )
        except ValueError:
            # Last part is not a valid float, treat as part of model name
            model_id_without_temp = model_id
            log.debug(
                "No temperature found in model ID %s, using default %s",
                model_id, default_temperature
            )
    else:
        model_id_without_temp = model_id
        log.debug(
            "Using default temperature %s for model ID %s",
            default_temperature, model_id
        )

    # Handle Google Gemini models
    if model_id_without_temp.startswith("google:"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            # Extract the model name after the prefix
            model_name = model_id_without_temp.split("google:", 1)[1]

            # Get API key from environment
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                log.warning(
                    "GOOGLE_API_KEY not found in environment. "
                    "Google Gemini model %s may not work properly.",
                    model_id
                )
                # Return the original string and let LangGraph handle the error
                return model_id

            # Create and return the Google Gemini model instance with temperature
            model_instance = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=temperature,
            )

            log.info(
                "Created Google Gemini model instance: %s with temperature %s",
                model_name, temperature
            )
            return model_instance

        except ImportError:
            log.error(
                "langchain-google-genai not installed. "
                "Cannot create Google Gemini model %s",
                model_id
            )
            return model_id
        except Exception as e:
            log.error(
                "Failed to create Google Gemini model %s: %s",
                model_id, e
            )
            return model_id

    # For all other model types (openai:, azure_openai:, anthropic:, etc.)
    # return the original string - LangGraph handles these natively
    # Note: Temperature for these providers is typically handled by
    # LangGraph/LangChain
    return model_id_without_temp


def _format_mcp_summary(servers_cfg: Dict[str, Dict]) -> str:
    if not servers_cfg:
        return "(no MCP servers configured)"
    lines = []
    for sid, s in servers_cfg.items():
        desc = s.get("description", "")
        transport = s.get("transport", "")
        if transport == "stdio":
            location = f"command: {s.get('command')}"
        else:
            location = f"url: {s.get('url')}"
        lines.append(f"- {sid}: {desc} (transport={transport}, {location})")
    return "\n".join(lines)


async def build_react_agent(
    agent_cfg: AgentConfig,
    default_model: str,
    checkpointer=None,
    *,
    business_context: str = "",
    original_user_question: str = "",
    dependent_request_responses: str = "",
    config_path: Optional[str] = None,
    enable_llm_payload_logging: bool = True,
    llm_payload_logger: Optional[LLMPayloadLogger] = None,
    custom_placeholders: Optional[Dict[str, Any]] = None,
    default_temperature: float = 0.2,
):
    # Use global checkpointer for memory persistence across API calls
    if checkpointer is None:
        checkpointer = get_global_checkpointer()
        log.info(f"Using global checkpointer for agent {agent_cfg.name}")

    model_id = agent_cfg.model or default_model
    # Create the appropriate model instance (handles google: prefix)
    model_instance = create_model_instance(model_id, default_temperature)

    servers_raw = {
        k: v.dict(exclude_none=True)
        for k, v in agent_cfg.mcp_servers.items()
    }

    mcp_client, tools = await load_mcp_tools(servers_raw)

    # Merge in HTTP tools (non-MCP) if configured
    try:
        http_tools = build_http_tools(agent_cfg.http_tools)
    except Exception as e:
        log.exception(
            "Failed building HTTP tools for agent %s: %s",
            agent_cfg.name,
            e,
        )
        http_tools = []

    # Merge in Python function tools if configured
    try:
        python_tools = load_python_function_tools(agent_cfg.python_tools)
        python_tools = validate_python_tools(python_tools)
    except Exception as e:
        log.exception(
            "Failed building Python function tools for agent %s: %s",
            agent_cfg.name,
            e,
        )
        python_tools = []

    # Combine all tools
    tools = list(tools) + list(http_tools) + list(python_tools)

    # Apply Gemini schema filtering if using Google Gemini model
    tools = apply_gemini_schema_filtering(tools, model_id)

    summary = _format_mcp_summary(servers_raw)

    # Load prompt content from either direct text or file
    try:
        config_dir = get_config_directory(
            Path(config_path) if config_path else None
        )
        prompt_content = load_prompt_content(
            prompt=agent_cfg.prompt,
            prompt_file=agent_cfg.prompt_file,
            config_dir=config_dir,
        )
    except Exception as e:
        log.error(
            "Failed to load prompt for agent %s: %s",
            agent_cfg.name,
            e,
        )
        raise

    # Use enhanced placeholder system for template rendering
    try:
        # Create placeholder context
        placeholder_context = PlaceholderContext()

        # Add custom placeholders if provided
        if custom_placeholders:
            placeholder_context.add_custom_placeholders(custom_placeholders)

        # Render prompt with enhanced placeholder support
        prompt_filled = render_prompt_with_placeholders(
            prompt_content,
            placeholder_context=placeholder_context,
            agent_name=agent_cfg.name,
            agent_description=agent_cfg.description or "",
            agent_model=model_id,
            business_context=business_context or "",
            original_user_question=original_user_question or "",
            dependent_request_responses=dependent_request_responses or "",
            mcpservers=summary,
        )
    except Exception as e:
        log.exception(
            "Failed to render prompt for agent %s with enhanced placeholders: %s. "
            "Falling back to legacy rendering.",
            agent_cfg.name,
            e,
        )
        # Fallback to legacy rendering
        ctx = {
            "mcpservers": summary,
            "businessContext": business_context or "",
            "original_user_question": original_user_question or "",
            "agent_name": agent_cfg.name,
            "dependent_request_responses": dependent_request_responses or "",
        }
        try:
            prompt_filled = render_prompt(prompt_content, ctx)
        except Exception as fallback_e:
            log.error(
                "Legacy rendering also failed for agent %s: %s. "
                "Using raw prompt with simple replacement.",
                agent_cfg.name,
                fallback_e,
            )
            # Final fallback to simple replacement
            prompt_filled = prompt_content.replace("{{mcpservers}}", summary)

    # Create actual model instance and bind tools with parallel_tool_calls=False
    try:
        # Check if model_instance is already a model object or a string
        if isinstance(model_instance, str):
            # Import the init_chat_model function from LangChain
            from langchain.chat_models import init_chat_model
            # Create the actual model instance using LangChain's init_chat_model
            actual_model = init_chat_model(model_instance)
            log.info(
                "Created model instance from string: %s",
                type(actual_model).__name__
            )
        else:
            # model_instance is already a model object
            # (e.g., ChatGoogleGenerativeAI)
            actual_model = model_instance
            log.info(
                "Using existing model instance: %s",
                type(actual_model).__name__
            )

        # Bind tools first, then wrap with logging
        if tools:
            model_with_tools = actual_model.bind_tools(
                tools, parallel_tool_calls=False
            )
            log.info(
                "Disabled parallel tool calls for agent %s", agent_cfg.name
            )
        else:
            model_with_tools = actual_model

        # Wrap with logging if enabled (after tool binding)
        if enable_llm_payload_logging:
            if llm_payload_logger is None:
                llm_payload_logger = LLMPayloadLogger(agent_cfg.name)
            model_with_tools = LoggingModelWrapper(
                model_with_tools, llm_payload_logger
            )
            log.info(
                "Enabled LLM payload logging for agent %s", agent_cfg.name
            )

    except Exception as e:
        log.warning(
            "Failed to create model instance or bind tools with "
            "parallel_tool_calls=False: %s. Using default.", e
        )
        import traceback
        log.warning("Full traceback: %s", traceback.format_exc())
        model_with_tools = model_instance

    agent = create_react_agent(
        model=model_with_tools,
        tools=tools,
        prompt=prompt_filled,
        name=agent_cfg.name,
        version="v2",
        checkpointer=checkpointer,
    )
    # Attach model identifier for downstream logging without changing APIs
    try:
        setattr(agent, "_model_id", model_id)
        setattr(agent, "_rendered_prompt", prompt_filled)
    except Exception:
        pass
    log.info("Agent prompt:\n%s", prompt_filled)
    log.info("Built agent %s with %d tools", agent_cfg.name, len(tools))
    return agent, mcp_client
