# Module: Placeholder System

## Purpose & Responsibilities

The Placeholder System provides a comprehensive, extensible framework for dynamic template rendering with custom placeholders in the JK-Agents Framework. It enables context-aware prompt generation, supports multiple provider types, and maintains backward compatibility while adding powerful new features for personalized agent interactions.

**Evidence**: `app/placeholder_system/__init__.py:1-78` - "Enhanced Placeholder System for JK-Agents Framework" with dynamic placeholder registration and resolution.

## Public Interfaces

### 1. PlaceholderContext
**File**: `app/placeholder_system/context.py:33-50`
```python
class PlaceholderContext:
    """Context builder for template rendering with enhanced placeholder support."""
    
    def __init__(self, registry: Optional[PlaceholderRegistry] = None)
    def add_custom_placeholders(self, placeholders: Dict[str, Any])
    def build_context(self, agent_name: str, business_context: str, 
                     original_user_question: str, **kwargs) -> Dict[str, Any]
```

**Evidence**: `app/placeholder_system/__init__.py:17-33` - Usage example showing context creation and template rendering integration.

### 2. PlaceholderRegistry
**File**: `app/placeholder_system/registry.py` (inferred from imports)
```python
class PlaceholderRegistry:
    """Registry for managing placeholder providers."""
    
    def register_provider(self, provider: PlaceholderProvider)
    def get_provider(self, placeholder_name: str) -> PlaceholderProvider
    def resolve_placeholder(self, name: str, context: Dict[str, Any]) -> Any

def get_default_registry() -> PlaceholderRegistry
```

**Evidence**: `app/placeholder_system/__init__.py:36` - Registry import and default registry function.

### 3. PlaceholderProvider (Abstract Base)
**File**: `app/placeholder_system/providers.py:25-50`
```python
class PlaceholderProvider(ABC):
    """Abstract base class for placeholder providers."""
    
    @abstractmethod
    def get_name(self) -> str
    
    @abstractmethod
    def get_supported_placeholders(self) -> Set[str]
    
    @abstractmethod
    def can_provide(self, placeholder_name: str) -> bool
    
    @abstractmethod
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any
```

## Data Models and Flows

### 1. Placeholder Resolution Flow
**Evidence**: `app/placeholder_system/__init__.py:17-33` - Template rendering workflow:

```
Template Request → PlaceholderContext → Registry Lookup → Provider Resolution → Value Substitution
       ↓                ↓                    ↓                   ↓                    ↓
User Input → Context Building → Provider Selection → Value Generation → Rendered Template
```

### 2. Provider Types and Hierarchy
**Evidence**: `app/placeholder_system/__init__.py:37-43` - Built-in provider types:

```python
# Built-in providers
SystemPlaceholderProvider    # System info (timestamp, platform, python_version)
AgentPlaceholderProvider     # Agent context (agent_name, agent_model, agent_description)
ContextPlaceholderProvider   # Business context (business_context, original_user_question)
UserPlaceholderProvider      # Custom user-defined placeholders
```

### 3. Configuration Integration Flow
**Evidence**: `config/placeholder_example.yaml:1-173` - YAML configuration with placeholder usage:

```
YAML Config → Placeholder Detection → Context Building → Provider Resolution → Dynamic Prompt
     ↓              ↓                      ↓                   ↓                    ↓
{{timestamp}} → System Provider → Current Time → Value Substitution → "2025-09-29T23:01:04"
{{user_name}} → User Provider → Custom Value → Default Handling → "John" or "Not specified"
```

## Key Algorithms and Complexity

### 1. Placeholder Detection Algorithm
**Evidence**: `config/placeholder_example.yaml:34-37` - Placeholder syntax with default values:
```yaml
- User name: {{user_name|default("Not specified")}}
- Project name: {{project_name|default("Default Project")}}
```

- **Algorithm**: Regex-based placeholder detection with pipe syntax for defaults
- **Complexity**: O(n) where n = template length
- **Features**: Default value support, validation, transformation functions

### 2. Provider Resolution Algorithm
**Evidence**: `app/placeholder_system/providers.py:44-46` - Provider capability checking:
```python
def can_provide(self, placeholder_name: str) -> bool
```

- **Algorithm**: Provider chain traversal with capability matching
- **Complexity**: O(p) where p = number of registered providers
- **Features**: First-match resolution, fallback mechanisms, error handling

### 3. Context Building Algorithm
**Evidence**: `app/placeholder_system/context.py:33-50` - Context builder implementation:

- **Algorithm**: Merge built-in providers with custom placeholders
- **Complexity**: O(k) where k = number of placeholders to resolve
- **Features**: Validation rules, custom transformations, error recovery

## Configuration and Default Values

### 1. Built-in System Placeholders
**Evidence**: `config/placeholder_example.yaml:17-21` - System information placeholders:

```yaml
# System Information
- Current time: {{timestamp}}           # Current ISO timestamp
- Platform: {{platform}}               # OS platform (Windows/macOS/Linux)
- Python version: {{python_version}}   # Python interpreter version
- Working directory: {{working_directory}}  # Current working directory
```

### 2. Agent Context Placeholders
**Evidence**: `config/placeholder_example.yaml:23-27` - Agent-specific placeholders:

```yaml
# Agent Information
- Agent name: {{agent_name}}           # Current agent name
- Agent description: {{agent_description}}  # Agent description
- Model: {{agent_model}}               # AI model being used
```

### 3. Business Context Placeholders
**Evidence**: `config/placeholder_example.yaml:28-32`, `config/python_exec_agent_working.yaml:68-69` - Business and context placeholders:

```yaml
# Context Information
- Business context: {{business_context}}        # Business context string
- Original question: {{original_user_question}} # User's original query
- Available MCP servers: {{mcpservers}}         # Available MCP servers list
- Available agents: {{agents}}                  # List of all available agents with descriptions
```

### 4. MCP Server Tools Placeholder
**Evidence**: `app/agent_builder.py:271-283` - MCP servers formatting:

```python
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
```

**Usage in Configuration**: `config/python_exec_agent_working.yaml:165`

```yaml
Available MCP servers: {{mcpservers}}
```

**Result**: Formatted list of available MCP servers with details:

```text
- python_runner: Python code execution (transport=stdio, command: python)
- data_analyzer: Data analysis tools (transport=http, url: http://localhost:3001)
- file_manager: File operations (transport=stdio, command: ./file_tools.sh)
```

**Use Case**: Agents that need to know what external tools and services are available to them for executing tasks.

### 5. Custom Placeholder Defaults
**Evidence**: `config/placeholder_example.yaml:34-37` - Custom placeholders with defaults:

```yaml
# Custom Placeholders (if provided)
- User name: {{user_name|default("Not specified")}}
- Project name: {{project_name|default("Default Project")}}
- Priority level: {{priority|default("normal")}}
- Department: {{department|default("General")}}
```

## Internal & External Dependencies

### Internal Dependencies
**File**: `app/placeholder_system/__init__.py:36-50`
```python
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
```

### External Dependencies
**File**: `app/placeholder_system/providers.py:8-16`
```python
import logging
import os
import platform
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Set, Optional, List
from pathlib import Path
```

### Integration Points
**Evidence**: Memory `f1b15904` - Dynamic summarization system integration:
- **Template System**: Integration with existing template rendering
- **Supervisor Builder**: `{{conversation_context_metadata}}` placeholder replacement
- **Configuration Loading**: YAML configuration with placeholder support

## Tests Exercising the Module

### 1. Placeholder Example Configuration
**File**: `config/placeholder_example.yaml:1-173`
- **Purpose**: Comprehensive demonstration of placeholder system capabilities
- **Coverage**: All built-in providers, custom placeholders, default values
- **Scenarios**: Multiple agent types with different placeholder usage patterns

### 2. Integration with Existing Configurations
**Evidence**: `grep_search` results - `{{conversation_context_metadata}}` usage:
- `config/azure_openai_test.yaml`
- `config/multi_provider_agent.yaml`
- `config/python_exec_agent_working.yaml`
- `config/python_exec_agent_working_google.yaml`
- `config/python_exec_agent_working_litellm.yaml`

### 3. Memory System Integration Tests
**Evidence**: Memory `f1b15904` - Metadata template replacement testing:
- Tests placeholder replacement in supervisor prompts
- Validates thread_id parameter passing
- Verifies conversation context metadata generation

## Migration/Cleanup Notes

### 1. Backward Compatibility
**Evidence**: `app/placeholder_system/__init__.py:4-6` - Maintains backward compatibility:
```python
# This module provides a comprehensive, extensible placeholder system that allows
# dynamic template rendering with custom placeholders. It maintains backward
# compatibility while adding powerful new features.
```

**Status**: System designed to work with existing template rendering without breaking changes.

### 2. Configuration Migration
**Evidence**: `config/placeholder_example.yaml` vs existing configurations:

**Current State**: Existing configurations use basic `{{placeholder}}` syntax
**Enhanced State**: New system supports `{{placeholder|default("value")}}` syntax with validation

**Migration Path**: Gradual adoption - existing placeholders continue working, new features optional.

### 3. Provider System Evolution
**Evidence**: `app/placeholder_system/providers.py:25-50` - Extensible provider architecture:

**Current Providers**: System, Agent, Context, User providers
**Future Expansion**: Database providers, API providers, external service providers

## Suggested Improvements

### 1. Advanced Placeholder Features
- **Conditional Placeholders**: `{{user_name|if_role("admin")}}`
- **Computed Placeholders**: `{{timestamp|format("YYYY-MM-DD")}}`
- **Nested Placeholders**: `{{department_{{user_role}}_config}}`

### 2. Performance Optimizations
- **Placeholder Caching**: Cache resolved values for repeated use
- **Lazy Evaluation**: Only resolve placeholders that are actually used
- **Batch Resolution**: Resolve multiple placeholders in single operation

### 3. Enhanced Validation
- **Type Validation**: Ensure placeholder values match expected types
- **Range Validation**: Validate numeric values within acceptable ranges
- **Format Validation**: Validate string formats (email, phone, etc.)

### 4. Configuration Management Integration
- **Environment-based Defaults**: Different defaults per environment (dev/staging/prod)
- **User Profile Integration**: Automatic user context from authentication system
- **Dynamic Configuration**: Runtime configuration updates without restart

## Potential Regressions

### 1. Template Rendering Performance
**Risk**: Complex placeholder resolution could slow template rendering
**Evidence**: `app/placeholder_system/context.py` - Multiple provider lookups per placeholder
**Mitigation**: Implement caching and lazy evaluation strategies

### 2. Configuration Complexity
**Risk**: Advanced placeholder syntax could make configurations harder to maintain
**Evidence**: `config/placeholder_example.yaml:34-37` - Complex default value syntax
**Mitigation**: Provide configuration validation tools and clear documentation

### 3. Provider Registration Issues
**Risk**: Provider conflicts or missing providers could cause runtime errors
**Evidence**: `app/placeholder_system/providers.py:44-46` - Provider capability checking
**Mitigation**: Comprehensive provider validation and fallback mechanisms

## Real-World Usage Examples

### 1. Personalized Assistant Configuration
**Evidence**: `config/placeholder_example.yaml:50-78` - Personalized assistant example:

```yaml
# Personalized Assistant
Hello {{user_name|default("there")}}! I'm your personalized assistant.

## Your Profile (if available)
- Role: {{user_role|default("User")}}
- Department: {{department|default("Not specified")}}
- Preferences: {{user_preferences|default("Standard")}}
- Access level: {{access_level|default("Basic")}}
```

**Use Case**: Customer service agents that adapt based on user profile and context.

### 2. Project Management Integration
**Evidence**: `config/placeholder_example.yaml:80-119` - Project management agent:

```yaml
## Project Context
- Project: {{project_name|default("Unnamed Project")}}
- Phase: {{project_phase|default("Planning")}}
- Priority: {{priority|default("Medium")}}
- Deadline: {{deadline|default("Not set")}}
- Budget: {{budget|default("Not specified")}}
```

**Use Case**: Project management tools that provide context-aware assistance based on current project state.

### 3. Agent Listing Integration
**Evidence**: `app/supervisor_builder.py:25-29, 49, 128` - Agent list formatting:

```python
def _format_agents_listing(agents: List[AgentConfig]) -> str:
    lines = []
    for a in agents:
        lines.append(f"- {a.name}: {a.description or '(no description)'}")
    return "\n".join(lines)
```

**Usage in Configuration**: `config/python_exec_agent_working.yaml:68-69`

```yaml
Available agents:
{{agents}}
```

**Result**: Formatted list of all agents with descriptions:

```text
- python_exec_agent: Executes Python code and performs calculations
- human_response_agent: Provides human-readable responses and summaries
- conversation_summarizer: Summarizes conversation context when memory is full
```

**Use Case**: Supervisor agents that coordinate multi-agent workflows by delegating tasks to specialized agents.

### 4. Dynamic Conversation Context
**Evidence**: Memory `f1b15904` - Conversation context metadata:

```yaml
supervisor:
  prompt: |
    ## Conversation Analysis
    {{conversation_context_metadata}}
    
    Based on the conversation history above, determine the appropriate response strategy.
```

**Use Case**: Intelligent conversation routing based on conversation history and context analysis.

## Performance Characteristics

### 1. Resolution Performance
- **Placeholder Detection**: O(n) where n = template length
- **Provider Lookup**: O(p) where p = number of providers
- **Value Resolution**: O(1) for cached values, O(k) for computed values

### 2. Memory Usage
- **Provider Registry**: Minimal overhead for provider registration
- **Context Building**: Linear with number of placeholders
- **Caching**: Optional caching for frequently used values

### 3. Scalability Characteristics
- **Concurrent Access**: Thread-safe provider resolution
- **Large Templates**: Efficient processing of templates with many placeholders
- **Provider Extensibility**: Easy addition of new provider types without performance impact

The Placeholder System provides a powerful foundation for dynamic, context-aware prompt generation while maintaining simplicity and backward compatibility with existing configurations.
