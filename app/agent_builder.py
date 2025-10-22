from __future__ import annotations
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Use compatibility layer for create_react_agent (removed in LangGraph 0.6.7+)
from .react_agent_compat import create_react_agent
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from .memory.enhanced_tool_node import EnhancedToolNode
from .memory.tool_message_filter import patch_agent_with_message_filter

from .checkpointer_manager import get_global_checkpointer
from .mcp_loader import load_mcp_tools, build_http_tools
from .python_tool_loader import (
    load_python_function_tools,
    validate_python_tools
)
from .config import AgentConfig
from .template_utils import render_prompt, render_prompt_with_placeholders
from .placeholder_system import PlaceholderContext
from .gemini_schema_filter import apply_gemini_schema_filtering, is_gemini_model
from .prompt_loader import load_prompt_content, get_config_directory
from .llm_payload_logger import LoggingModelWrapper, LLMPayloadLogger

# Import DeepAgents adapter for advanced agent features
try:
    from .deep_agent_adapter import create_deep_agent_from_config
    HAS_DEEPAGENTS = True
except ImportError:
    HAS_DEEPAGENTS = False

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
    from .enhanced_litellm_wrapper import EnhancedLiteLLMChat, is_litellm_model, get_tool_compatible_model, get_fallback_tool_binding, create_litellm_model
    HAS_ENHANCED_LITELLM = True
except ImportError:
    HAS_ENHANCED_LITELLM = False

log = logging.getLogger("agent_builder")


# Import model format utilities
try:
    from .config_model_format import parse_model_id, convert_to_litellm_format
    HAS_MODEL_FORMAT = True
except ImportError:
    HAS_MODEL_FORMAT = False

def create_model_instance(
    model_id: str, default_temperature: float = 0.2, 
    app_config: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Create a model instance based on the model ID prefix.

    Args:
        model_id: Model ID string like "google:gemini-2.0-flash-exp",
                 "openai:gpt-4o", "anthropic:claude-sonnet-4", etc.
                 Can also include temperature like
                 "google:gemini-2.5-flash-lite:0.2"
                 
                 LiteLLM format models use forward slash:
                 "openai/gpt-4o", "anthropic/claude-3-5-sonnet", "gemini/gemini-1.5-pro"
        default_temperature: Default temperature to use if not specified
                           in model_id
        app_config: Optional application config with litellm settings

    Returns:
        Either the original model_id string (for LangGraph built-in support)
        or a model instance (for custom providers like Google Gemini or LiteLLM)
    """
    if not isinstance(model_id, str):
        return model_id

    # Pre-process model_id for consistent format handling
    temperature = default_temperature
    model_id_without_temp = model_id
    
    # Parse model_id using the new utilities if available
    if HAS_MODEL_FORMAT:
        model_info = parse_model_id(model_id)
        if model_info['temperature'] is not None:
            temperature = model_info['temperature']
        
        # If it's in Google format, convert to LiteLLM format for enhanced wrapper
        if model_info['original_format'] == 'google':
            model_id_without_temp = convert_to_litellm_format(model_info)
            log.info(f"Converted Google format to LiteLLM format: {model_id} -> {model_id_without_temp}")
        else:
            # Otherwise, just remove temperature if present
            model_id_without_temp = model_id
            if model_info['temperature'] is not None:
                model_id_parts = model_id.split(':') 
                model_id_without_temp = ':'.join(model_id_parts[:-1])
    
    # Check if enhanced LiteLLM should be used (prioritize enhanced wrapper)
    if HAS_ENHANCED_LITELLM and is_litellm_model(model_id_without_temp):
        # We already parsed the temperature above, so no need to do it again
        log.info(f"Using enhanced LiteLLM wrapper with model {model_id_without_temp} at temperature {temperature}")
        
        log.info(f"Creating Enhanced LiteLLM model for {model_id_without_temp} with temperature {temperature}")
        
        try:
            model_instance = create_litellm_model(
                model_id=model_id_without_temp,
                temperature=temperature
            )
            log.info(f"Successfully created Enhanced LiteLLM model: {type(model_instance).__name__}")
            return model_instance
        except Exception as e:
            log.error(f"Failed to create Enhanced LiteLLM model {model_id}: {e}")
            log.info("Falling back to legacy LiteLLM handling...")
    
    # Check if legacy LiteLLM should be used based on config and format
    use_litellm = False
    if app_config and app_config.get("litellm", {}).get("enabled", False):
        use_litellm = True
        log.info("Legacy LiteLLM integration enabled via configuration")
    elif "/" in model_id and not model_id.startswith(("http://", "https://")):
        # If model uses provider/model format (e.g. "openai/gpt-4o"), assume LiteLLM
        use_litellm = True
        log.info(f"Legacy LiteLLM format model ID detected: {model_id}")
    
    # Handle legacy LiteLLM provider format models
    if use_litellm and HAS_LITELLM:
        try:
            # Parse temperature from model_id if present
            # Format: "provider/model:temperature" or "provider/model"
            temperature = default_temperature
            if ":" in model_id:
                parts = model_id.split(":")
                try:
                    temperature = float(parts[-1])
                    model_id_without_temp = ":".join(parts[:-1])
                except ValueError:
                    model_id_without_temp = model_id
            else:
                model_id_without_temp = model_id
                
            log.info(f"Creating LiteLLM model for {model_id_without_temp} with temperature {temperature}")
            
            # For Azure OpenAI models, use our custom wrapper
            if model_id_without_temp.startswith("azure/") and HAS_AZURE_LITELLM:
                log.info(f"Using custom Azure LiteLLM wrapper for {model_id_without_temp}")
                model_instance = AzureLiteLLMChat(
                    model=model_id_without_temp,
                    temperature=temperature,
                )
                return model_instance
            
            # For other providers, try standard LangChain integration
            try:
                from langchain_community.chat_models import ChatLiteLLM
                litellm_class = ChatLiteLLM
            except ImportError:
                # Fallback: try langchain_litellm if available
                try:
                    from langchain_litellm import LiteLLMChatModel
                    litellm_class = LiteLLMChatModel
                except ImportError:
                    log.warning("No LangChain LiteLLM integration available. Falling back to direct LiteLLM usage.")
                    # For now, return the model_id string and let the framework handle it elsewhere
                    return model_id
            
            # Create and return LangChain-compatible LiteLLM model
            model_instance = litellm_class(
                model=model_id_without_temp,
                temperature=temperature,
            )
            
            return model_instance
            
        except ImportError as e:
            log.error(f"LiteLLM LangChain integration not available: {e}")
            return model_id
        except Exception as e:
            log.error(f"Failed to create LiteLLM model {model_id}: {e}")
            return model_id

    # Parse temperature from model_id if present (legacy format)
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

    # For Azure OpenAI models, create an actual model instance
    if model_id_without_temp.startswith("azure_openai:") or model_id_without_temp.startswith("azure/"):
        try:
            from langchain_openai import AzureChatOpenAI
            
            # Extract deployment name from model_id
            if model_id_without_temp.startswith("azure_openai:"):
                deployment_name = model_id_without_temp.split("azure_openai:", 1)[1]
            else:
                deployment_name = model_id_without_temp.split("azure/", 1)[1]
            
            # Get Azure OpenAI configuration from environment
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
            
            if not azure_endpoint or not azure_api_key:
                log.warning(
                    "AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY not found in environment. "
                    "Azure OpenAI model %s may not work properly.",
                    model_id
                )
                return model_id_without_temp
            
            # Use deployment name from config, or fall back to environment variable
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", deployment_name)
            
            # Create and return the Azure OpenAI model instance
            model_instance = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_api_key,
                api_version=azure_api_version,
                azure_deployment=deployment,
                temperature=temperature,
            )
            
            log.info(
                "Created model instance from string: %s", 
                type(model_instance).__name__
            )
            return model_instance
            
        except ImportError:
            log.error(
                "langchain-openai not installed. "
                "Cannot create Azure OpenAI model %s",
                model_id
            )
            return model_id_without_temp
        except Exception as e:
            log.error(
                "Failed to create Azure OpenAI model %s: %s",
                model_id, e
            )
            return model_id_without_temp
    
    # For OpenAI models
    if model_id_without_temp.startswith("openai:"):
        try:
            from langchain_openai import ChatOpenAI
            
            model_name = model_id_without_temp.split("openai:", 1)[1]
            
            model_instance = ChatOpenAI(
                model=model_name,
                temperature=temperature,
            )
            
            log.info(
                "Created OpenAI model instance: %s with temperature %s",
                model_name, temperature
            )
            return model_instance
            
        except ImportError:
            log.error("langchain-openai not installed. Cannot create OpenAI model %s", model_id)
            return model_id_without_temp
        except Exception as e:
            log.error("Failed to create OpenAI model %s: %s", model_id, e)
            return model_id_without_temp
    
    # For Anthropic models
    if model_id_without_temp.startswith("anthropic:"):
        try:
            from langchain_anthropic import ChatAnthropic
            
            model_name = model_id_without_temp.split("anthropic:", 1)[1]
            
            model_instance = ChatAnthropic(
                model=model_name,
                temperature=temperature,
            )
            
            log.info(
                "Created Anthropic model instance: %s with temperature %s",
                model_name, temperature
            )
            return model_instance
            
        except ImportError:
            log.error("langchain-anthropic not installed. Cannot create Anthropic model %s", model_id)
            return model_id_without_temp
        except Exception as e:
            log.error("Failed to create Anthropic model %s: %s", model_id, e)
            return model_id_without_temp
    
    # For all other model types, return the string (fallback)
    log.warning("Unknown model type %s, returning as string", model_id_without_temp)
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


# State definition for normal agents (non-ReAct)
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def create_normal_agent(
    model_with_tools: Any,
    prompt: str,
    name: str = "agent",
    checkpointer=None,
) -> Any:
    """
    Create a normal (non-ReAct) agent that doesn't use tools but can have conversations.
    
    Args:
        model_with_tools: The language model instance
        prompt: The system prompt for the agent
        name: Agent name for identification
        checkpointer: Optional checkpointer for state persistence
        
    Returns:
        LangGraph StateGraph agent
    """
    log.info("Creating normal agent '%s' without tool calling capabilities", name)
    
    def agent_node(state: AgentState) -> dict:
        """Main agent node that processes messages with the system prompt."""
        messages = state["messages"]
        
        # Add system message with prompt if not already present
        if not messages or not any(msg.type == "system" for msg in messages):
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=prompt)] + messages
        
        # Call the model
        response = model_with_tools.invoke(messages)
        
        return {"messages": [response]}
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add the agent node
    workflow.add_node("agent", agent_node)
    
    # Set the entrypoint
    workflow.set_entry_point("agent")
    
    # Add edge from agent to END
    workflow.add_edge("agent", END)
    
    # Compile the graph
    agent = workflow.compile(checkpointer=checkpointer)
    
    return agent


async def build_agent(
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
    app_config: Optional[Dict[str, Any]] = None,
):
    # Enable checkpointer for memory persistence (required for multi-turn conversations)
    if checkpointer is None:
        checkpointer = get_global_checkpointer(app_config)
        log.info(f"Using global checkpointer for agent {agent_cfg.name}")

    model_id = agent_cfg.model or default_model
    # Create the appropriate model instance (handles google: prefix and litellm provider/model format)
    model_instance = create_model_instance(model_id, default_temperature, app_config)

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

        # Determine parallel tool calls behavior (agent overrides app; otherwise autodetect)
        # app_config here is expected to be a dict (see build_react_agent signature)
        app_parallel = None
        try:
            app_parallel = (app_config or {}).get("parallel_tool_calls_enabled")
        except Exception:
            app_parallel = None

        agent_parallel = getattr(agent_cfg, "parallel_tool_calls_enabled", None)

        # Autodetect default: disable for Google Gemini, enable otherwise
        autodetect_parallel = not is_gemini_model(model_id)

        parallel_tool_calls_flag = (
            agent_parallel if agent_parallel is not None
            else (app_parallel if app_parallel is not None else autodetect_parallel)
        )

        # Bind tools first, then wrap with logging
        if tools:
            # Use our custom tool adapter for Gemini models and handle potential errors
            try:
                # For Google Gemini models, we need special handling
                if is_gemini_model(model_id):
                    log.info(
                        "Using Gemini-specific tool binding for agent %s",
                        agent_cfg.name
                    )
                    # The EnhancedLiteLLMChat.bind_tools method will handle Gemini models
                    model_with_tools = actual_model.bind_tools(tools)
                else:
                    # For other models, use the standard binding with parallel_tool_calls flag
                    model_with_tools = actual_model.bind_tools(
                        tools, parallel_tool_calls=parallel_tool_calls_flag
                    )
                    
                log.info(
                    "Parallel tool calls for agent %s: %s (agent=%s, app=%s, autodetect=%s)",
                    agent_cfg.name,
                    parallel_tool_calls_flag,
                    agent_parallel,
                    app_parallel,
                    autodetect_parallel,
                )
            except NotImplementedError:
                # Use our custom adapter for handling tool binding
                log.warning("NotImplementedError in bind_tools for %s, using custom adapter", model_id)
                model_with_tools = get_tool_compatible_model(actual_model, tools)
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
            "parallel_tool_calls=False: %s. Using fallback binding.", e
        )
        import traceback
        log.warning("Full traceback: %s", traceback.format_exc())
        
        # Try our fallback tool binding approach
        try:
            model_with_tools = get_fallback_tool_binding(model_instance, tools)
            log.info("Using fallback tool binding for %s", model_id)
        except Exception:
            # Last resort: use the model without tools
            log.warning("Fallback tool binding also failed. Using model without tool binding.")
            model_with_tools = model_instance

    # Determine agent type (defaults to "react" for backward compatibility)
    agent_type = getattr(agent_cfg, "agent_type", "react") or "react"
    
    # Create agent based on type
    if agent_type == "deep":
        # Create DeepAgent with advanced features (subagents, planning, context management)
        if not HAS_DEEPAGENTS:
            log.error(
                f"Cannot create DeepAgent '{agent_cfg.name}': deepagents package not installed. "
                "Install with: pip install deepagents"
            )
            raise ImportError(
                "DeepAgents package is required for agent_type='deep'. "
                "Install with: pip install deepagents"
            )
        
        log.info(f"Creating deep agent {agent_cfg.name} with DeepAgents framework")
        
        # DeepAgent uses the base model instance (without tool binding), as it handles tools internally
        # Get the actual model - if model_instance is a string, create the model; otherwise use it directly
        if isinstance(model_instance, str):
            from langchain.chat_models import init_chat_model
            deep_agent_model = init_chat_model(model_instance)
        else:
            deep_agent_model = model_instance
        
        agent = create_deep_agent_from_config(
            model=deep_agent_model,  # Use base model, not model_with_tools
            tools=tools,
            system_prompt=prompt_filled,
            agent_config=agent_cfg,
            checkpointer=checkpointer,
        )
        
        log.info(
            f"DeepAgent '{agent_cfg.name}' created with "
            f"{len(agent_cfg.deep_agent_config.subagents) if agent_cfg.deep_agent_config else 0} subagents"
        )
        
    elif agent_type == "normal":
        # Create normal agent without tool calling
        log.info(f"Creating normal agent {agent_cfg.name} (no tool calling)")
        agent = create_normal_agent(
            model_with_tools=model_with_tools,
            prompt=prompt_filled,
            name=agent_cfg.name,
            checkpointer=checkpointer,
        )
        
    else:  # agent_type == "react" (default)
        # Standard react agent creation
        log.info(f"Creating react agent {agent_cfg.name}")
        agent = create_react_agent(
            model=model_with_tools,
            tools=tools,
            prompt=prompt_filled,
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


# Backward compatibility: alias old function name to new one
build_react_agent = build_agent
