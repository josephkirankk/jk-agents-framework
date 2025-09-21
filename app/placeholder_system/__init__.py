"""
Enhanced Placeholder System for JK-Agents Framework.

This module provides a comprehensive, extensible placeholder system that allows
dynamic template rendering with custom placeholders. It maintains backward
compatibility while adding powerful new features.

Key Features:
- Dynamic placeholder registration and resolution
- Built-in providers for system, agent, and context data
- Support for custom user-defined placeholders
- Validation and error handling
- Default values and transformations
- Cross-platform compatibility (Windows/macOS)

Usage:
    from app.placeholder_system import PlaceholderContext, get_default_registry
    
    # Create context with built-in and custom placeholders
    context = PlaceholderContext()
    context.add_custom_placeholders({"user_name": "John", "version": "1.0"})
    
    # Build context for template rendering
    template_context = context.build_context(
        agent_name="test_agent",
        business_context="Test context",
        original_user_question="What is the weather?",
        # ... other parameters
    )
    
    # Use with existing template system
    from app.template_utils import render_prompt
    result = render_prompt(template_text, template_context)
"""

from .registry import PlaceholderRegistry, get_default_registry
from .providers import (
    PlaceholderProvider,
    SystemPlaceholderProvider,
    AgentPlaceholderProvider,
    ContextPlaceholderProvider,
    UserPlaceholderProvider,
)
from .context import PlaceholderContext
from .exceptions import (
    PlaceholderError,
    PlaceholderNotFoundError,
    PlaceholderValidationError,
    PlaceholderTransformationError,
)

__all__ = [
    # Core classes
    "PlaceholderRegistry",
    "PlaceholderProvider", 
    "PlaceholderContext",
    
    # Built-in providers
    "SystemPlaceholderProvider",
    "AgentPlaceholderProvider", 
    "ContextPlaceholderProvider",
    "UserPlaceholderProvider",
    
    # Exceptions
    "PlaceholderError",
    "PlaceholderNotFoundError",
    "PlaceholderValidationError",
    "PlaceholderTransformationError",
    
    # Utilities
    "get_default_registry",
]

# Version info
__version__ = "1.0.0"
__author__ = "JK-Agents Framework"
__description__ = "Enhanced placeholder system for dynamic template rendering"
