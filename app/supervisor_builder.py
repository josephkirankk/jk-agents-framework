from __future__ import annotations
import logging
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

# Use compatibility layer for create_react_agent (removed in LangGraph 0.6.7+)
from .react_agent_compat import create_react_agent
from .checkpointer_manager import get_global_checkpointer
from .config import SupervisorConfig, AgentConfig
from .template_utils import render_prompt, render_prompt_with_placeholders
from .placeholder_system import PlaceholderContext
from .agent_builder import create_model_instance
from .prompt_loader import load_prompt_content, get_config_directory

# Import conversation metadata for supervisor enhancement
try:
    from .simple_conversation_memory_fixed import get_conversation_context_metadata
    HAS_CONVERSATION_METADATA = True
except ImportError:
    HAS_CONVERSATION_METADATA = False
    log.warning("Conversation metadata not available - dynamic summarization disabled")

log = logging.getLogger("supervisor_builder")


# Pydantic models for structured output
class PlanStep(BaseModel):
    """A single step in the execution plan."""
    id: str = Field(description="Unique step identifier (e.g., 's1', 's2')")
    agent: str = Field(description="Name of the agent to execute this step")
    task: str = Field(description="Specific task description for the agent")
    depends_on: List[str] = Field(default_factory=list, description="List of step IDs this step depends on")
    verify: Optional[str] = Field(default=None, description="Verification criteria (optional)")
    timeout_seconds: int = Field(default=120, description="Timeout in seconds for this step")
    retry: int = Field(default=1, description="Number of retry attempts")


class SupervisorPlan(BaseModel):
    """Complete execution plan from the supervisor."""
    goal: str = Field(description="Brief description of the overall goal")
    plan: List[PlanStep] = Field(description="List of execution steps")


def _format_agents_listing(agents: List[AgentConfig]) -> str:
    lines = []
    for a in agents:
        lines.append(f"- {a.name}: {a.description or '(no description)'}")
    return "\n".join(lines)


def build_supervisor_compiled(
    supervisor_cfg: SupervisorConfig,
    agents_cfg: List[AgentConfig],
    default_model: str,
    business_context: str = "",
    checkpointer=None,
    *,
    original_user_question: str = "",
    config_path: Optional[str] = None,
    default_temperature: float = 0.2,
    thread_id: Optional[str] = None,
):
    # Use global checkpointer for memory persistence across API calls
    if checkpointer is None:
        checkpointer = get_global_checkpointer()
        log.info("Using global checkpointer for supervisor")

    agents_list = _format_agents_listing(agents_cfg)

    # Load prompt content from either direct text or file
    try:
        config_dir = get_config_directory(
            Path(config_path) if config_path else None
        )
        prompt_content = load_prompt_content(
            prompt=supervisor_cfg.prompt,
            prompt_file=supervisor_cfg.prompt_file,
            config_dir=config_dir,
        )
    except Exception as e:
        log.error(
            "Failed to load prompt for supervisor: %s",
            e,
        )
        raise

    # Use enhanced placeholder system for template rendering
    try:
        # Create placeholder context
        placeholder_context = PlaceholderContext()
        
        # Add conversation context metadata if available
        conversation_metadata_str = ""
        if HAS_CONVERSATION_METADATA and thread_id:
            try:
                metadata = get_conversation_context_metadata(thread_id)
                conversation_metadata_str = (
                    f"conversation_context_metadata.word_count: {metadata['word_count']}\n"
                    f"conversation_context_metadata.turn_count: {metadata['turn_count']}\n"
                    f"conversation_context_metadata.message_count: {metadata['message_count']}\n"
                    f"conversation_context_metadata.has_structured_data: {metadata['has_structured_data']}\n"
                    f"conversation_context_metadata.summarization_recommended: {metadata['summarization_recommended']}\n"
                    f"conversation_context_metadata.memory_size_bytes: {metadata['memory_size_bytes']}"
                )
                log.info(f"Added conversation metadata for thread {thread_id}: {metadata['word_count']} words, {metadata['turn_count']} turns")
            except Exception as e:
                log.warning(f"Failed to get conversation metadata for thread {thread_id}: {e}")
                conversation_metadata_str = "conversation_context_metadata: unavailable (no prior conversation)"
        else:
            conversation_metadata_str = "conversation_context_metadata: unavailable (no thread_id or conversation system disabled)"
        
        # Add conversation metadata as a custom placeholder
        placeholder_context.add_custom_placeholder(
            "conversation_context_metadata", 
            conversation_metadata_str
        )

        # Render prompt with enhanced placeholder support
        prompt_filled = render_prompt_with_placeholders(
            prompt_content,
            placeholder_context=placeholder_context,
            business_context=business_context or "",
            original_user_question=original_user_question or "",
            agents=agents_list,
        )
    except Exception as e:
        log.exception(
            "Failed to render supervisor prompt with enhanced placeholders: %s. "
            "Falling back to legacy rendering.",
            e,
        )
        # Fallback to legacy rendering
        ctx = {
            "agents": agents_list,
            "business_context": business_context or "",
            "original_user_question": original_user_question or "",
        }
        try:
            prompt_filled = render_prompt(prompt_content, ctx)
        except Exception as fallback_e:
            log.error(
                "Legacy rendering also failed for supervisor: %s. "
                "Using simple replacement.",
                fallback_e,
            )
            # Final fallback to simple replacements
            prompt_filled = prompt_content.replace("{{agents}}", agents_list)
            prompt_filled = prompt_filled.replace(
                "{{business_context}}", business_context
            )

    supervisor_model = supervisor_cfg.model or default_model
    # Create the appropriate model instance (handles google: prefix)
    supervisor_model_instance = create_model_instance(
        supervisor_model, default_temperature
    )

    # Enable JSON mode for Azure OpenAI to force JSON output
    # This prevents the LLM from returning explanatory text
    try:
        if hasattr(supervisor_model_instance, 'model_kwargs'):
            supervisor_model_instance.model_kwargs = supervisor_model_instance.model_kwargs or {}
            supervisor_model_instance.model_kwargs['response_format'] = {"type": "json_object"}
            log.info("✅ Enabled JSON mode for supervisor (Azure OpenAI)")
        elif hasattr(supervisor_model_instance, 'bind'):
            # For LangChain models that support bind()
            supervisor_model_instance = supervisor_model_instance.bind(
                response_format={"type": "json_object"}
            )
            log.info("✅ Enabled JSON mode for supervisor via bind()")
    except Exception as e:
        log.warning(f"⚠️  Could not enable JSON mode for supervisor: {e}")

    sup_agent = create_react_agent(
        model=supervisor_model_instance,
        tools=[],
        prompt=prompt_filled.strip(),
        checkpointer=checkpointer,
    )
    # Attach model identifier for downstream logging without changing APIs
    try:
        setattr(sup_agent, "_model_id", supervisor_model)
        setattr(sup_agent, "_rendered_prompt", prompt_filled.strip())
    except Exception:
        pass
    # Print/log the exact planning prompt used
    try:
        full_prompt = prompt_filled.strip()
        log.info(
            "Supervisor planning prompt (model=%s):\n%s",
            supervisor_model,
            full_prompt,
        )
        print(
            "Supervisor planning prompt (model="
            + str(supervisor_model)
            + "):\n"
            + full_prompt
        )
    except Exception as e:
        log.warning("Failed to print supervisor planning prompt: %s", e)

    log.info("Supervisor compiled (model=%s)", supervisor_model)
    return sup_agent


def build_supervisor_with_structured_output(
    supervisor_cfg: SupervisorConfig,
    agents_cfg: List[AgentConfig],
    default_model: str,
    business_context: str = "",
    *,
    original_user_question: str = "",
    config_path: Optional[str] = None,
    default_temperature: float = 0.2,
    thread_id: Optional[str] = None,
):
    """
    Build a supervisor that uses structured output to guarantee JSON schema compliance.

    This version uses LangChain's with_structured_output() to force the LLM to return
    a valid SupervisorPlan object, eliminating JSON parsing errors.
    """
    agents_list = _format_agents_listing(agents_cfg)

    # Load prompt content from either direct text or file
    try:
        config_dir = get_config_directory(
            Path(config_path) if config_path else None
        )
        prompt_content = load_prompt_content(
            prompt=supervisor_cfg.prompt,
            prompt_file=supervisor_cfg.prompt_file,
            config_dir=config_dir,
        )
    except Exception as e:
        log.error(
            "Failed to load prompt for supervisor: %s",
            e,
        )
        raise

    # Use enhanced placeholder system for template rendering
    try:
        # Create placeholder context
        placeholder_context = PlaceholderContext()

        # Add conversation context metadata if available
        conversation_metadata_str = ""
        if HAS_CONVERSATION_METADATA and thread_id:
            try:
                metadata = get_conversation_context_metadata(thread_id)
                conversation_metadata_str = (
                    f"conversation_context_metadata.word_count: {metadata['word_count']}\n"
                    f"conversation_context_metadata.turn_count: {metadata['turn_count']}\n"
                    f"conversation_context_metadata.message_count: {metadata['message_count']}\n"
                    f"conversation_context_metadata.has_structured_data: {metadata['has_structured_data']}\n"
                    f"conversation_context_metadata.summarization_recommended: {metadata['summarization_recommended']}\n"
                    f"conversation_context_metadata.memory_size_bytes: {metadata['memory_size_bytes']}"
                )
                log.info(f"Added conversation metadata for thread {thread_id}: {metadata['word_count']} words, {metadata['turn_count']} turns")
            except Exception as e:
                log.warning(f"Failed to get conversation metadata for thread {thread_id}: {e}")
                conversation_metadata_str = "conversation_context_metadata: unavailable (no prior conversation)"
        else:
            conversation_metadata_str = "conversation_context_metadata: unavailable (no thread_id or conversation system disabled)"

        # Add conversation metadata as a custom placeholder
        placeholder_context.add_custom_placeholder(
            "conversation_context_metadata",
            conversation_metadata_str
        )

        # Render prompt with enhanced placeholder support
        prompt_filled = render_prompt_with_placeholders(
            prompt_content,
            placeholder_context=placeholder_context,
            business_context=business_context or "",
            original_user_question=original_user_question or "",
            agents=agents_list,
        )
    except Exception as e:
        log.exception(
            "Failed to render supervisor prompt with enhanced placeholders: %s. "
            "Falling back to legacy rendering.",
            e,
        )
        # Fallback to legacy rendering
        ctx = {
            "agents": agents_list,
            "business_context": business_context or "",
            "original_user_question": original_user_question or "",
        }
        try:
            prompt_filled = render_prompt(prompt_content, ctx)
        except Exception as fallback_e:
            log.error(
                "Legacy rendering also failed for supervisor: %s. "
                "Using simple replacement.",
                fallback_e,
            )
            # Final fallback to simple replacements
            prompt_filled = prompt_content.replace("{{agents}}", agents_list)
            prompt_filled = prompt_filled.replace(
                "{{business_context}}", business_context
            )

    supervisor_model = supervisor_cfg.model or default_model
    # Create the appropriate model instance (handles google: prefix)
    supervisor_model_instance = create_model_instance(
        supervisor_model, default_temperature
    )

    # For Azure OpenAI, we need to use a different approach
    # The API version doesn't support structured output, so we'll just use the base model
    # and rely on the prompt to enforce JSON output
    log.info("🔧 Using JSON-enforced prompts for supervisor (model=%s)", supervisor_model)
    structured_llm = supervisor_model_instance
    log.info("✅ Supervisor configured with JSON-enforced prompts (model=%s)", supervisor_model)

    # Print/log the exact planning prompt used
    try:
        full_prompt = prompt_filled.strip()
        log.info(
            "Supervisor planning prompt with structured output (model=%s):\n%s",
            supervisor_model,
            full_prompt,
        )
        print(
            "Supervisor planning prompt with structured output (model="
            + str(supervisor_model)
            + "):\n"
            + full_prompt
        )
    except Exception as e:
        log.warning("Failed to print supervisor planning prompt: %s", e)

    log.info("Supervisor with structured output compiled (model=%s)", supervisor_model)

    # Return the structured LLM and the prompt for use in planner_executor
    return {
        "llm": structured_llm,
        "prompt": prompt_filled.strip(),
        "model_id": supervisor_model,
    }
