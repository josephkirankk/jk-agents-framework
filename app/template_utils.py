from __future__ import annotations
import logging
from typing import Any, Dict, Optional, List

from jinja2 import Environment, StrictUndefined, UndefinedError

try:
    from .placeholder_system import PlaceholderContext, get_default_registry
    from .placeholder_system.exceptions import PlaceholderError
except ImportError:
    # Handle case when imported directly (not as package)
    from placeholder_system import PlaceholderContext, get_default_registry
    from placeholder_system.exceptions import PlaceholderError

log = logging.getLogger("template_utils")

# Create a global Jinja2 environment tuned for prompts
_jinja_env = Environment(
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,  # fail fast on missing variables
)


def render_prompt(template_text: str, context: Dict[str, Any]) -> str:
    """Render a prompt template string with Jinja2.

    Args:
        template_text: The prompt template text from YAML.
        context: Variables available to the template, e.g. {
            'original_user_question': str,
            'business_context': str,
            'mcpservers': str,
            'agents': str,
            'agent_name': str,
        }
    Returns:
        Rendered prompt string.
    Raises:
        Exception if template rendering fails (StrictUndefined for missing vars).
    """
    try:
        tmpl = _jinja_env.from_string(template_text or "")
        return tmpl.render(**(context or {}))
    except Exception:
        # Let caller handle/log; strict so issues surface early
        raise


def render_prompt_with_placeholders(
    template_text: str,
    placeholder_context: Optional[PlaceholderContext] = None,
    custom_placeholders: Optional[Dict[str, Any]] = None,
    # Core context parameters for backward compatibility
    agent_name: Optional[str] = None,
    agent_description: Optional[str] = None,
    agent_model: Optional[str] = None,
    business_context: Optional[str] = None,
    original_user_question: Optional[str] = None,
    dependent_request_responses: Optional[str] = None,
    mcpservers: Optional[str] = None,
    agents: Optional[str] = None,
    **additional_context: Any
) -> str:
    """
    Render a prompt template with enhanced placeholder support.

    This function provides the new enhanced placeholder functionality while
    maintaining backward compatibility with the existing render_prompt function.

    Args:
        template_text: The prompt template text
        placeholder_context: Optional PlaceholderContext instance
        custom_placeholders: Optional custom placeholders to add
        agent_name: Name of the current agent
        agent_description: Description of the current agent
        agent_model: Model used by the current agent
        business_context: Business context for the session
        original_user_question: The original user question
        dependent_request_responses: Responses from previous steps
        mcpservers: MCP servers summary
        agents: Available agents list
        **additional_context: Any additional context data

    Returns:
        Rendered prompt string

    Raises:
        PlaceholderError: If placeholder resolution fails
        UndefinedError: If template contains undefined variables
    """
    try:
        # Create or use provided placeholder context
        if placeholder_context is None:
            placeholder_context = PlaceholderContext()

        # Add custom placeholders if provided
        if custom_placeholders:
            placeholder_context.add_custom_placeholders(custom_placeholders)

        # Build the complete context
        context = placeholder_context.build_context(
            agent_name=agent_name,
            agent_description=agent_description,
            agent_model=agent_model,
            business_context=business_context,
            original_user_question=original_user_question,
            dependent_request_responses=dependent_request_responses,
            mcpservers=mcpservers,
            agents=agents,
            **additional_context
        )

        # Render the template
        tmpl = _jinja_env.from_string(template_text or "")
        rendered = tmpl.render(**context)

        log.debug(
            f"Successfully rendered template with {len(context)} placeholders"
        )
        return rendered

    except PlaceholderError:
        # Re-raise placeholder errors as-is
        raise
    except UndefinedError as e:
        # Enhance undefined variable errors with helpful information
        if placeholder_context:
            available_placeholders = (
                placeholder_context.get_available_placeholders()
            )
        else:
            available_placeholders = set()
        log.error(f"Template contains undefined variable: {e}")
        available_list = ', '.join(sorted(available_placeholders))
        log.info(f"Available placeholders: {available_list}")
        raise
    except Exception as e:
        log.error(f"Template rendering failed: {e}")
        raise


def validate_template_placeholders(
    template_text: str,
    placeholder_context: Optional[PlaceholderContext] = None
) -> List[str]:
    """
    Validate a template by checking for undefined placeholders.

    Args:
        template_text: The template text to validate
        placeholder_context: Optional PlaceholderContext for validation

    Returns:
        List of undefined placeholder names found in the template
    """
    if placeholder_context is None:
        placeholder_context = PlaceholderContext()

    return placeholder_context.validate_template(template_text)


def get_available_placeholders() -> Dict[str, str]:
    """
    Get documentation for all available placeholders.

    Returns:
        Dictionary mapping placeholder names to documentation
    """
    registry = get_default_registry()
    return registry.get_documentation()
