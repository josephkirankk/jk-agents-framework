from __future__ import annotations
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .mcp_loader import load_mcp_tools, build_http_tools
from .python_tool_loader import (
    load_python_function_tools,
    validate_python_tools
)
from .config import AgentConfig
from .template_utils import render_prompt
from .gemini_schema_filter import apply_gemini_schema_filtering
from .prompt_loader import load_prompt_content, get_config_directory
from .llm_payload_logger import LoggingModelWrapper, LLMPayloadLogger

log = logging.getLogger("agent_builder")


class PepGenXMultimodalWrapper:
    """
    Wrapper for PepGenX models that converts multimodal content to string format.

    This wrapper intercepts messages before they're sent to the PepGenX model
    and converts any multimodal content arrays to string format, since PepGenX
    only supports string content.
    """

    def __init__(self, model):
        self.model = model
        log.info("PepGenXMultimodalWrapper initialized for model: %s", type(model).__name__)

    def _convert_multimodal_content_to_string(self, content):
        """Convert multimodal content array to string format."""
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        image_url = item.get("image_url", {})
                        file_id = image_url.get("file_id", "unknown")
                        text_parts.append(f"[Image File ID: {file_id}]")
                    else:
                        text_parts.append(str(item))
                else:
                    text_parts.append(str(item))
            return "\n".join(text_parts)
        return content

    def _process_messages(self, messages):
        """Process messages to convert multimodal content to strings."""
        processed_messages = []
        for message in messages:
            if isinstance(message, dict):
                processed_message = message.copy()
                if "content" in processed_message:
                    processed_message["content"] = self._convert_multimodal_content_to_string(
                        processed_message["content"]
                    )
                processed_messages.append(processed_message)
            else:
                # Handle LangChain message objects
                if hasattr(message, 'content'):
                    # Create a copy of the message to avoid modifying the original
                    import copy
                    processed_message = copy.deepcopy(message)
                    processed_message.content = self._convert_multimodal_content_to_string(message.content)
                    log.info("Converted message content from %s to %s", message.content, processed_message.content)
                    processed_messages.append(processed_message)
                else:
                    processed_messages.append(message)
        return processed_messages

    def invoke(self, input_data, config=None):
        """Invoke the model with multimodal content conversion."""
        log.info("PepGenXMultimodalWrapper.invoke called with input type: %s", type(input_data))
        if isinstance(input_data, dict) and "messages" in input_data:
            log.info("Processing %d messages for multimodal content", len(input_data["messages"]))
            processed_input = input_data.copy()
            processed_input["messages"] = self._process_messages(input_data["messages"])
            return self.model.invoke(processed_input, config)
        return self.model.invoke(input_data, config)

    async def ainvoke(self, input_data, config=None):
        """Async invoke the model with multimodal content conversion."""
        log.info("PepGenXMultimodalWrapper.ainvoke called with input type: %s", type(input_data))
        log.info("PepGenXMultimodalWrapper.ainvoke input_data: %s", input_data)

        if isinstance(input_data, dict) and "messages" in input_data:
            log.info("Processing %d messages for multimodal content (dict format)", len(input_data["messages"]))
            for i, msg in enumerate(input_data["messages"]):
                log.info("Message %d: %s", i, msg)
            processed_input = input_data.copy()
            processed_input["messages"] = self._process_messages(input_data["messages"])
            log.info("Processed messages: %s", processed_input["messages"])
            return await self.model.ainvoke(processed_input, config)
        elif isinstance(input_data, list):
            log.info("Processing %d messages for multimodal content (list format)", len(input_data))
            for i, msg in enumerate(input_data):
                log.info("Message %d: %s", i, msg)
            processed_messages = self._process_messages(input_data)
            log.info("Processed messages: %s", processed_messages)
            return await self.model.ainvoke(processed_messages, config)

        return await self.model.ainvoke(input_data, config)

    def bind_tools(self, tools, **kwargs):
        """Bind tools to the wrapped model and return a new wrapper instance."""
        log.info("PepGenXMultimodalWrapper.bind_tools called with %d tools", len(tools) if tools else 0)
        bound_model = self.model.bind_tools(tools, **kwargs)
        # Return a new wrapper instance wrapping the bound model
        return PepGenXMultimodalWrapper(bound_model)

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped model."""
        log.info("PepGenXMultimodalWrapper.__getattr__ called for: %s", name)
        return getattr(self.model, name)


def create_model_instance(model_id: str) -> Any:
    """
    Create a model instance based on the model ID prefix.

    Args:
        model_id: Model ID string like "google:gemini-2.0-flash-exp",
                 "openai:gpt-4o", "anthropic:claude-sonnet-4",
                 "pepgenx:gpt-4o", "lmstudio:llama-3.2-3b", etc.

    Returns:
        Either the original model_id string (for LangGraph built-in support)
        or a model instance (for custom providers like Google Gemini)
    """
    if not isinstance(model_id, str):
        return model_id

    # Handle Azure OpenAI environment variable mapping
    if model_id.startswith("azure_openai:"):
        # Map existing environment variables to LangChain expected names
        if os.getenv("AZURE_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
            os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_API_KEY")
            log.info("Mapped AZURE_API_KEY to AZURE_OPENAI_API_KEY")

        if os.getenv("AZURE_API_BASE") and not os.getenv("AZURE_OPENAI_ENDPOINT"):
            # Clean up the endpoint URL - remove chat/completions path if present
            base_url = os.getenv("AZURE_API_BASE")
            if "/chat/completions" in base_url:
                base_url = base_url.split("/chat/completions")[0]
            os.environ["AZURE_OPENAI_ENDPOINT"] = base_url
            log.info("Mapped AZURE_API_BASE to AZURE_OPENAI_ENDPOINT: %s", base_url)

        if os.getenv("AZURE_API_VERSION"):
            if not os.getenv("AZURE_OPENAI_API_VERSION"):
                os.environ["AZURE_OPENAI_API_VERSION"] = os.getenv("AZURE_API_VERSION")
                log.info("Mapped AZURE_API_VERSION to AZURE_OPENAI_API_VERSION")
            if not os.getenv("OPENAI_API_VERSION"):
                os.environ["OPENAI_API_VERSION"] = os.getenv("AZURE_API_VERSION")
                log.info("Mapped AZURE_API_VERSION to OPENAI_API_VERSION")

    # Handle PepGenX models - route to PepGenX wrapper
    if model_id.startswith("pepgenx:"):
        try:
            from langchain_openai import ChatOpenAI

            # Extract the model name after the prefix
            model_name = model_id.split("pepgenx:", 1)[1]

            # Get PepGenX wrapper configuration
            pepgenx_base_url = os.getenv(
                "PEPGENX_WRAPPER_BASE_URL", "http://127.0.0.1:8080/v1"
            )
            pepgenx_api_key = os.getenv(
                "PEPGENX_WRAPPER_API_KEY", "sk-test-key1"
            )

            if not pepgenx_base_url:
                log.warning(
                    "PEPGENX_WRAPPER_BASE_URL not found in environment. "
                    "PepGenX model %s may not work properly.",
                    model_id
                )
                return model_id

            # Create OpenAI-compatible client pointing to PepGenX wrapper
            base_model = ChatOpenAI(
                model=model_name,
                openai_api_key=pepgenx_api_key,
                openai_api_base=pepgenx_base_url,
                temperature=0.0,
            )

            # Wrap with multimodal content converter
            model_instance = PepGenXMultimodalWrapper(base_model)

            log.info(
                "Created PepGenX model instance: %s -> %s",
                model_name, pepgenx_base_url
            )
            return model_instance

        except ImportError:
            log.error(
                "langchain-openai not installed. "
                "Cannot create PepGenX model %s",
                model_id
            )
            return model_id
        except Exception as e:
            log.error(
                "Failed to create PepGenX model %s: %s",
                model_id, e
            )
            return model_id

    # Handle LM Studio models - route to LM Studio
    if model_id.startswith("lmstudio:"):
        try:
            from langchain_openai import ChatOpenAI

            # Extract the model name after the prefix
            model_name = model_id.split("lmstudio:", 1)[1]

            # Get LM Studio configuration
            lmstudio_base_url = os.getenv(
                "LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1"
            )
            lmstudio_api_key = os.getenv("LMSTUDIO_API_KEY", "lm-studio")

            if not lmstudio_base_url:
                log.warning(
                    "LMSTUDIO_BASE_URL not found in environment. "
                    "LM Studio model %s may not work properly.",
                    model_id
                )
                return model_id

            # Create OpenAI-compatible client pointing to LM Studio
            model_instance = ChatOpenAI(
                model=model_name,
                openai_api_key=lmstudio_api_key,
                openai_api_base=lmstudio_base_url,
                temperature=0.0,
            )

            log.info(
                "Created LM Studio model instance: %s -> %s",
                model_name, lmstudio_base_url
            )
            return model_instance

        except ImportError:
            log.error(
                "langchain-openai not installed. "
                "Cannot create LM Studio model %s",
                model_id
            )
            return model_id
        except Exception as e:
            log.error(
                "Failed to create LM Studio model %s: %s",
                model_id, e
            )
            return model_id

    # Handle Google Gemini models
    if model_id.startswith("google:"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            # Extract the model name after the prefix
            model_name = model_id.split("google:", 1)[1]

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

            # Create and return the Google Gemini model instance
            model_instance = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.0,  # Default temperature, can be overridden
            )

            log.info("Created Google Gemini model instance: %s", model_name)
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
    return model_id


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
):
    # Create a fresh MemorySaver instance if none provided to avoid shared state
    if checkpointer is None:
        checkpointer = MemorySaver()

    model_id = agent_cfg.model or default_model
    # Create the appropriate model instance (handles google: prefix)
    model_instance = create_model_instance(model_id)

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

    # Render prompt with Jinja2 so templates can use variables like
    # {{ mcpservers }}, {{ businessContext }}, {{ original_user_question }},
    # {{ agent_name }}, {{ dependent_request_responses }}
    ctx = {
        "mcpservers": summary,
        "businessContext": business_context or "",
        "original_user_question": original_user_question or "",
        "agent_name": agent_cfg.name,
        "dependent_request_responses": dependent_request_responses or "",
    }
    try:
        prompt_filled = render_prompt(prompt_content, ctx)
    except Exception as e:
        log.exception(
            "Failed to render prompt for agent %s with Jinja2: %s. "
            "Falling back to raw prompt.",
            agent_cfg.name,
            e,
        )
        # Fallback to simple replacement for mcpservers
        prompt_filled = prompt_content.replace("{{mcpservers}}", summary)

    # Create actual model instance and bind tools with parallel_tool_calls=False
    try:
        # Import the init_chat_model function from LangChain
        from langchain.chat_models import init_chat_model

        # Check if model_instance is already a model instance (custom prefixes)
        # or if it's a string that needs to be initialized
        if (hasattr(model_instance, 'invoke') or
                hasattr(model_instance, 'ainvoke')):
            # Already a model instance from custom prefix handling
            actual_model = model_instance
            log.info("Using custom model instance: %s",
                     type(actual_model).__name__)
        else:
            # Create the actual model instance using LangChain's init_chat_model
            log.info("Calling init_chat_model with: %s (type: %s)", model_instance, type(model_instance))
            actual_model = init_chat_model(model_instance)
            log.info("Created model instance: %s (type: %s)",
                     actual_model, type(actual_model).__name__)

        # Bind tools first, then wrap with logging
        if tools:
            model_with_tools = actual_model.bind_tools(tools, parallel_tool_calls=False)
            log.info("Disabled parallel tool calls for agent %s", agent_cfg.name)
        else:
            model_with_tools = actual_model

        # Wrap with logging if enabled (after tool binding)
        if enable_llm_payload_logging:
            if llm_payload_logger is None:
                llm_payload_logger = LLMPayloadLogger(agent_cfg.name)
            model_with_tools = LoggingModelWrapper(model_with_tools, llm_payload_logger)
            log.info("Enabled LLM payload logging for agent %s", agent_cfg.name)

    except Exception as e:
        log.warning("Failed to create model instance or bind tools with parallel_tool_calls=False: %s. Using default.", e)
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
