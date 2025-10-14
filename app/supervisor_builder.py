from __future__ import annotations
import logging
from typing import List, Optional
from pathlib import Path

from langgraph.prebuilt import create_react_agent
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

    sup_agent = create_react_agent(
        model=supervisor_model_instance,
        tools=[],
        prompt=prompt_filled.strip(),
        name="supervisor",
        version="v2",
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
