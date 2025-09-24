"""
Placeholder Registry for managing placeholder providers and resolution.

The registry acts as a central hub for all placeholder providers, allowing
for dynamic registration, lookup, and resolution of placeholders.
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional, List, Set, Callable
from collections import defaultdict

try:
    from .exceptions import (
        PlaceholderNotFoundError,
        PlaceholderRegistrationError,
        PlaceholderProviderError,
    )
except ImportError:
    from exceptions import (
        PlaceholderNotFoundError,
        PlaceholderRegistrationError,
        PlaceholderProviderError,
    )

log = logging.getLogger("placeholder_registry")


class PlaceholderRegistry:
    """
    Central registry for managing placeholder providers and resolution.
    
    The registry maintains a collection of placeholder providers and handles
    the resolution of placeholders by querying providers in priority order.
    """
    
    def __init__(self):
        """Initialize the placeholder registry."""
        self._providers: Dict[str, 'PlaceholderProvider'] = {}
        self._placeholder_cache: Dict[str, Any] = {}
        self._provider_priorities: Dict[str, int] = {}
        self._transformations: Dict[str, Callable[[Any], Any]] = {}
        self._default_values: Dict[str, Any] = {}
        self._documentation: Dict[str, str] = {}
        
    def register_provider(
        self, 
        provider: 'PlaceholderProvider', 
        priority: int = 100
    ) -> None:
        """
        Register a placeholder provider with the registry.
        
        Args:
            provider: The placeholder provider to register
            priority: Priority for provider resolution (lower = higher priority)
            
        Raises:
            PlaceholderRegistrationError: If registration fails
        """
        try:
            provider_name = provider.get_name()
            
            if provider_name in self._providers:
                log.warning(f"Replacing existing provider: {provider_name}")
            
            self._providers[provider_name] = provider
            self._provider_priorities[provider_name] = priority
            
            # Register provider's placeholders
            for placeholder_name in provider.get_supported_placeholders():
                if placeholder_name in self._documentation:
                    log.debug(f"Placeholder '{placeholder_name}' already documented, skipping")
                else:
                    doc = provider.get_placeholder_documentation(placeholder_name)
                    if doc:
                        self._documentation[placeholder_name] = doc
            
            log.info(f"Registered placeholder provider: {provider_name} (priority: {priority})")
            
        except Exception as e:
            raise PlaceholderRegistrationError(
                provider.get_name() if hasattr(provider, 'get_name') else 'unknown',
                str(e)
            )
    
    def unregister_provider(self, provider_name: str) -> None:
        """
        Unregister a placeholder provider.
        
        Args:
            provider_name: Name of the provider to unregister
        """
        if provider_name in self._providers:
            provider = self._providers[provider_name]
            
            # Remove documentation for provider's placeholders
            for placeholder_name in provider.get_supported_placeholders():
                if placeholder_name in self._documentation:
                    del self._documentation[placeholder_name]
            
            del self._providers[provider_name]
            del self._provider_priorities[provider_name]
            
            # Clear cache entries that might be from this provider
            self._placeholder_cache.clear()
            
            log.info(f"Unregistered placeholder provider: {provider_name}")
        else:
            log.warning(f"Provider not found for unregistration: {provider_name}")
    
    def get_providers(self) -> List['PlaceholderProvider']:
        """
        Get all registered providers sorted by priority.
        
        Returns:
            List of providers sorted by priority (lowest priority number first)
        """
        return [
            self._providers[name] 
            for name in sorted(self._providers.keys(), key=lambda x: self._provider_priorities[x])
        ]
    
    def get_available_placeholders(self) -> Set[str]:
        """
        Get all available placeholder names from all providers.
        
        Returns:
            Set of all available placeholder names
        """
        placeholders = set()
        for provider in self._providers.values():
            placeholders.update(provider.get_supported_placeholders())
        return placeholders
    
    def resolve_placeholder(
        self, 
        placeholder_name: str, 
        context: Dict[str, Any],
        use_cache: bool = True
    ) -> Any:
        """
        Resolve a placeholder value by querying providers.
        
        Args:
            placeholder_name: Name of the placeholder to resolve
            context: Context data for placeholder resolution
            use_cache: Whether to use cached values
            
        Returns:
            The resolved placeholder value
            
        Raises:
            PlaceholderNotFoundError: If placeholder cannot be resolved
        """
        # Check cache first if enabled
        cache_key = f"{placeholder_name}:{hash(str(sorted(context.items())))}"
        if use_cache and cache_key in self._placeholder_cache:
            log.debug(f"Using cached value for placeholder: {placeholder_name}")
            return self._placeholder_cache[cache_key]
        
        # Try to resolve from providers in priority order
        for provider in self.get_providers():
            try:
                if provider.can_provide(placeholder_name):
                    value = provider.get_placeholder_value(placeholder_name, context)
                    
                    # Apply transformation if configured
                    if placeholder_name in self._transformations:
                        try:
                            value = self._transformations[placeholder_name](value)
                        except Exception as e:
                            log.error(f"Transformation failed for {placeholder_name}: {e}")
                            # Continue with original value
                    
                    # Cache the result
                    if use_cache:
                        self._placeholder_cache[cache_key] = value
                    
                    log.debug(f"Resolved placeholder '{placeholder_name}' from provider '{provider.get_name()}'")
                    return value
                    
            except Exception as e:
                log.error(f"Provider '{provider.get_name()}' failed to resolve '{placeholder_name}': {e}")
                continue
        
        # Check for default value
        if placeholder_name in self._default_values:
            default_value = self._default_values[placeholder_name]
            log.debug(f"Using default value for placeholder: {placeholder_name}")
            return default_value
        
        # Placeholder not found
        available = list(self.get_available_placeholders())
        raise PlaceholderNotFoundError(placeholder_name, available)
    
    def set_default_value(self, placeholder_name: str, default_value: Any) -> None:
        """Set a default value for a placeholder."""
        self._default_values[placeholder_name] = default_value
        log.debug(f"Set default value for placeholder: {placeholder_name}")
    
    def set_transformation(self, placeholder_name: str, transform_func: Callable[[Any], Any]) -> None:
        """Set a transformation function for a placeholder."""
        self._transformations[placeholder_name] = transform_func
        log.debug(f"Set transformation for placeholder: {placeholder_name}")
    
    def clear_cache(self) -> None:
        """Clear the placeholder cache."""
        self._placeholder_cache.clear()
        log.debug("Cleared placeholder cache")
    
    def get_documentation(self, placeholder_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get documentation for placeholders.
        
        Args:
            placeholder_name: Specific placeholder name, or None for all
            
        Returns:
            Dictionary mapping placeholder names to documentation
        """
        if placeholder_name:
            return {placeholder_name: self._documentation.get(placeholder_name, "No documentation available")}
        return self._documentation.copy()


# Global default registry instance
_default_registry: Optional[PlaceholderRegistry] = None


def get_default_registry() -> PlaceholderRegistry:
    """
    Get the default global placeholder registry.
    
    Returns:
        The default PlaceholderRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = PlaceholderRegistry()
        _initialize_default_providers(_default_registry)
    return _default_registry


def _initialize_default_providers(registry: PlaceholderRegistry) -> None:
    """Initialize the default registry with built-in providers."""
    try:
        from .providers import (
            SystemPlaceholderProvider,
            AgentPlaceholderProvider,
            ContextPlaceholderProvider,
            UserPlaceholderProvider,
        )
        from .config_provider import ConfigPlaceholderProvider
    except ImportError:
        from providers import (
            SystemPlaceholderProvider,
            AgentPlaceholderProvider,
            ContextPlaceholderProvider,
            UserPlaceholderProvider,
        )
        from config_provider import ConfigPlaceholderProvider
    
    # Register built-in providers with appropriate priorities
    registry.register_provider(SystemPlaceholderProvider(), priority=10)
    registry.register_provider(ConfigPlaceholderProvider(), priority=15)  # High priority for config vars
    registry.register_provider(AgentPlaceholderProvider(), priority=20)
    registry.register_provider(ContextPlaceholderProvider(), priority=30)
    registry.register_provider(UserPlaceholderProvider(), priority=100)  # Lowest priority
    
    log.info("Initialized default placeholder providers including ConfigProvider")
