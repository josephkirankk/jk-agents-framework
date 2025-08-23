from __future__ import annotations
from typing import Any, Dict

from jinja2 import Environment, StrictUndefined


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

