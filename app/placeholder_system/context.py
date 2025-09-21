"""
PlaceholderContext for building template contexts with enhanced placeholder support.

This module provides the PlaceholderContext class which serves as the main
interface for building template contexts with support for dynamic placeholders,
validation, and extensible provider system.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List, Set, Callable

try:
    from .registry import PlaceholderRegistry, get_default_registry
    from .providers import UserPlaceholderProvider
    from .exceptions import (
        PlaceholderError,
        PlaceholderNotFoundError,
        PlaceholderValidationError,
    )
except ImportError:
    from registry import PlaceholderRegistry, get_default_registry
    from providers import UserPlaceholderProvider
    from exceptions import (
        PlaceholderError,
        PlaceholderNotFoundError,
        PlaceholderValidationError,
    )

log = logging.getLogger("placeholder_context")


class PlaceholderContext:
    """
    Context builder for template rendering with enhanced placeholder support.
    
    This class provides a high-level interface for building template contexts
    by resolving placeholders through the registered provider system.
    """
    
    def __init__(self, registry: Optional[PlaceholderRegistry] = None):
        """
        Initialize the placeholder context.
        
        Args:
            registry: Optional custom registry, uses default if None
        """
        self._registry = registry or get_default_registry()
        self._custom_placeholders: Dict[str, Any] = {}
        self._validation_rules: Dict[str, Callable[[Any], bool]] = {}
        self._required_placeholders: Set[str] = set()
        self._context_cache: Dict[str, Any] = {}
        
    def add_custom_placeholders(self, placeholders: Dict[str, Any]) -> None:
        """
        Add custom placeholders that will be available during template rendering.
        
        Args:
            placeholders: Dictionary of placeholder names to values
        """
        self._custom_placeholders.update(placeholders)
        
        # Add to user provider in registry
        user_providers = [
            p for p in self._registry.get_providers() 
            if isinstance(p, UserPlaceholderProvider)
        ]
        
        if user_providers:
            user_provider = user_providers[0]
            for name, value in placeholders.items():
                user_provider.add_placeholder(name, value)
        
        log.debug(f"Added {len(placeholders)} custom placeholders")
    
    def add_custom_placeholder(
        self, 
        name: str, 
        value: Any, 
        documentation: Optional[str] = None,
        validation_rule: Optional[Callable[[Any], bool]] = None,
        required: bool = False
    ) -> None:
        """
        Add a single custom placeholder with optional validation and documentation.
        
        Args:
            name: Placeholder name
            value: Placeholder value (can be callable)
            documentation: Optional documentation string
            validation_rule: Optional validation function
            required: Whether this placeholder is required
        """
        self._custom_placeholders[name] = value
        
        if validation_rule:
            self._validation_rules[name] = validation_rule
        
        if required:
            self._required_placeholders.add(name)
        
        # Add to user provider in registry
        user_providers = [
            p for p in self._registry.get_providers() 
            if isinstance(p, UserPlaceholderProvider)
        ]
        
        if user_providers:
            user_provider = user_providers[0]
            user_provider.add_placeholder(name, value, documentation)
        
        log.debug(f"Added custom placeholder: {name} (required: {required})")
    
    def remove_custom_placeholder(self, name: str) -> None:
        """Remove a custom placeholder."""
        if name in self._custom_placeholders:
            del self._custom_placeholders[name]
        
        if name in self._validation_rules:
            del self._validation_rules[name]
        
        if name in self._required_placeholders:
            self._required_placeholders.remove(name)
        
        # Remove from user provider
        user_providers = [
            p for p in self._registry.get_providers() 
            if isinstance(p, UserPlaceholderProvider)
        ]
        
        if user_providers:
            user_provider = user_providers[0]
            user_provider.remove_placeholder(name)
        
        log.debug(f"Removed custom placeholder: {name}")
    
    def set_required_placeholders(self, placeholder_names: List[str]) -> None:
        """
        Set which placeholders are required for template rendering.
        
        Args:
            placeholder_names: List of required placeholder names
        """
        self._required_placeholders = set(placeholder_names)
        log.debug(f"Set required placeholders: {placeholder_names}")
    
    def add_validation_rule(self, placeholder_name: str, validation_func: Callable[[Any], bool]) -> None:
        """
        Add a validation rule for a placeholder.
        
        Args:
            placeholder_name: Name of the placeholder
            validation_func: Function that returns True if value is valid
        """
        self._validation_rules[placeholder_name] = validation_func
        log.debug(f"Added validation rule for placeholder: {placeholder_name}")
    
    def build_context(
        self,
        # Core context parameters (backward compatibility)
        agent_name: Optional[str] = None,
        agent_description: Optional[str] = None,
        agent_model: Optional[str] = None,
        business_context: Optional[str] = None,
        original_user_question: Optional[str] = None,
        dependent_request_responses: Optional[str] = None,
        mcpservers: Optional[str] = None,
        agents: Optional[str] = None,
        # Additional context data
        **additional_context: Any
    ) -> Dict[str, Any]:
        """
        Build a complete template context by resolving all placeholders.
        
        Args:
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
            Dictionary containing all resolved placeholder values
            
        Raises:
            PlaceholderNotFoundError: If required placeholders cannot be resolved
            PlaceholderValidationError: If placeholder validation fails
        """
        # Build base context from parameters
        base_context = {
            "agent_name": agent_name or "",
            "agent_description": agent_description or "",
            "agent_model": agent_model or "",
            "business_context": business_context or "",
            "businessContext": business_context or "",  # Backward compatibility
            "original_user_question": original_user_question or "",
            "dependent_request_responses": dependent_request_responses or "",
            "mcpservers": mcpservers or "(no MCP servers configured)",
            "agents": agents or "",
        }
        
        # Add additional context
        base_context.update(additional_context)
        
        # Add custom placeholders
        base_context.update(self._custom_placeholders)
        
        # Build final context by resolving all available placeholders
        final_context = {}
        available_placeholders = self._registry.get_available_placeholders()
        
        for placeholder_name in available_placeholders:
            try:
                value = self._registry.resolve_placeholder(placeholder_name, base_context)
                
                # Apply validation if configured
                if placeholder_name in self._validation_rules:
                    validation_func = self._validation_rules[placeholder_name]
                    if not validation_func(value):
                        raise PlaceholderValidationError(
                            placeholder_name,
                            value,
                            "Custom validation rule failed"
                        )
                
                final_context[placeholder_name] = value
                
            except PlaceholderNotFoundError:
                # Skip placeholders that can't be resolved unless required
                if placeholder_name in self._required_placeholders:
                    raise
                log.debug(f"Skipping unresolvable placeholder: {placeholder_name}")
                continue
            except Exception as e:
                log.error(f"Error resolving placeholder '{placeholder_name}': {e}")
                if placeholder_name in self._required_placeholders:
                    raise
                continue
        
        # Validate that all required placeholders are present
        missing_required = self._required_placeholders - set(final_context.keys())
        if missing_required:
            raise PlaceholderNotFoundError(
                f"Required placeholders missing: {', '.join(missing_required)}",
                list(self._registry.get_available_placeholders())
            )
        
        log.debug(f"Built context with {len(final_context)} placeholders")
        return final_context
    
    def get_available_placeholders(self) -> Set[str]:
        """Get all available placeholder names."""
        return self._registry.get_available_placeholders()
    
    def get_placeholder_documentation(self, placeholder_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get documentation for placeholders.
        
        Args:
            placeholder_name: Specific placeholder name, or None for all
            
        Returns:
            Dictionary mapping placeholder names to documentation
        """
        return self._registry.get_documentation(placeholder_name)
    
    def validate_template(self, template_text: str) -> List[str]:
        """
        Validate a template by checking for undefined placeholders.
        
        Args:
            template_text: The template text to validate
            
        Returns:
            List of undefined placeholder names found in the template
        """
        from jinja2 import Environment, meta
        
        # Parse template to find undefined variables
        env = Environment()
        ast = env.parse(template_text)
        undefined_vars = meta.find_undeclared_variables(ast)
        
        # Check which ones are not available in our registry
        available = self.get_available_placeholders()
        undefined_placeholders = [var for var in undefined_vars if var not in available]
        
        if undefined_placeholders:
            log.warning(f"Template contains undefined placeholders: {undefined_placeholders}")
        
        return undefined_placeholders
    
    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._context_cache.clear()
        self._registry.clear_cache()
        log.debug("Cleared placeholder context cache")
