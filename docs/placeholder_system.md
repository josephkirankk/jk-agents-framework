# Enhanced Placeholder System for JK-Agents Framework

The JK-Agents framework now includes a comprehensive, extensible placeholder system that allows dynamic template rendering with custom placeholders while maintaining full backward compatibility.

## Overview

The enhanced placeholder system provides:

- **Dynamic placeholder registration and resolution**
- **Built-in providers for system, agent, and context data**
- **Support for custom user-defined placeholders**
- **Validation and error handling**
- **Default values and transformations**
- **Cross-platform compatibility (Windows/macOS)**
- **Full backward compatibility with existing prompts**

## Key Components

### 1. PlaceholderRegistry
Central registry for managing placeholder providers and resolution.

### 2. PlaceholderProvider
Base class for creating custom placeholder providers.

### 3. PlaceholderContext
High-level interface for building template contexts.

### 4. Built-in Providers
- **SystemPlaceholderProvider**: System-level placeholders (timestamp, platform, etc.)
- **AgentPlaceholderProvider**: Agent-specific placeholders (name, model, etc.)
- **ContextPlaceholderProvider**: Context placeholders (business context, user questions, etc.)
- **UserPlaceholderProvider**: Custom user-defined placeholders

## Available Built-in Placeholders

### System Placeholders
- `{{timestamp}}` - Current timestamp in ISO format
- `{{date}}` - Current date (YYYY-MM-DD)
- `{{time}}` - Current time (HH:MM:SS)
- `{{platform}}` - Operating system platform
- `{{python_version}}` - Python version string
- `{{working_directory}}` - Current working directory
- `{{user_home}}` - User home directory
- `{{hostname}}` - System hostname

### Agent Placeholders
- `{{agent_name}}` - Name of the current agent
- `{{agent_description}}` - Description of the current agent
- `{{agent_model}}` - Model used by the current agent
- `{{mcpservers}}` - Summary of available MCP servers

### Context Placeholders
- `{{business_context}}` - Business context for the session
- `{{original_user_question}}` - The original user question
- `{{dependent_request_responses}}` - Responses from previous agent steps
- `{{agents}}` - List of available agents (for supervisor)

## Usage Examples

### Basic Usage (Backward Compatible)

Existing prompts continue to work without changes:

```yaml
agents:
  - name: "example_agent"
    prompt: |
      You are {{agent_name}}.
      Business context: {{business_context}}
      User question: {{original_user_question}}
      Available MCP servers: {{mcpservers}}
```

### Using Custom Placeholders via API

```python
# Via API request
{
    "input": "Analyze the data",
    "agent_name": "data_agent",
    "custom_placeholders": {
        "user_name": "John Doe",
        "project_name": "Data Analysis Project",
        "version": "1.0.0"
    }
}
```

```yaml
# In agent prompt
agents:
  - name: "data_agent"
    prompt: |
      Hello {{user_name}}!
      Working on project: {{project_name}}
      Version: {{version}}
      
      Agent: {{agent_name}}
      Timestamp: {{timestamp}}
```

### Programmatic Usage

```python
from app.placeholder_system import PlaceholderContext
from app.template_utils import render_prompt_with_placeholders

# Create context
context = PlaceholderContext()

# Add custom placeholders
context.add_custom_placeholders({
    "user_name": "Alice",
    "department": "Engineering",
    "priority": "high"
})

# Render template
template = """
User: {{user_name}}
Department: {{department}}
Priority: {{priority}}
Agent: {{agent_name}}
Time: {{timestamp}}
"""

result = render_prompt_with_placeholders(
    template,
    placeholder_context=context,
    agent_name="support_agent"
)
```

## Advanced Features

### Template Validation

```python
from app.template_utils import validate_template_placeholders

template = "Hello {{user_name}}, your {{undefined_placeholder}} is ready."
undefined = validate_template_placeholders(template)
print(undefined)  # ['undefined_placeholder']
```

### Available Placeholders Documentation

```python
from app.template_utils import get_available_placeholders

docs = get_available_placeholders()
for name, description in docs.items():
    print(f"{name}: {description}")
```

### Custom Placeholder Providers

```python
from app.placeholder_system import PlaceholderProvider, get_default_registry

class DatabasePlaceholderProvider(PlaceholderProvider):
    def get_name(self) -> str:
        return "database"
    
    def get_supported_placeholders(self) -> Set[str]:
        return {"db_status", "db_version", "db_connection_count"}
    
    def can_provide(self, placeholder_name: str) -> bool:
        return placeholder_name in self.get_supported_placeholders()
    
    def get_placeholder_value(self, placeholder_name: str, context: Dict[str, Any]) -> Any:
        if placeholder_name == "db_status":
            return "connected"
        elif placeholder_name == "db_version":
            return "PostgreSQL 14.2"
        elif placeholder_name == "db_connection_count":
            return 42
        else:
            raise PlaceholderProviderError(self.get_name(), f"Unknown placeholder: {placeholder_name}")

# Register the provider
registry = get_default_registry()
registry.register_provider(DatabasePlaceholderProvider(), priority=50)
```

## API Integration

### Query Endpoint

```json
POST /query
{
    "input": "Analyze the user data",
    "custom_placeholders": {
        "analysis_type": "behavioral",
        "time_period": "last_30_days",
        "user_segment": "premium"
    }
}
```

### Worker Endpoint

```json
POST /worker
{
    "agent_name": "data_analyst",
    "input": "Generate report for {{user_segment}} users",
    "custom_placeholders": {
        "user_segment": "premium",
        "report_format": "pdf",
        "include_charts": true
    }
}
```

## Error Handling

The system provides comprehensive error handling:

- **PlaceholderNotFoundError**: When required placeholders are missing
- **PlaceholderValidationError**: When placeholder validation fails
- **PlaceholderTransformationError**: When placeholder transformation fails
- **PlaceholderProviderError**: When a provider encounters an error

## Performance Considerations

- **Caching**: Placeholder values are cached for performance
- **Lazy Loading**: Providers are only queried when needed
- **Priority System**: Higher priority providers are queried first
- **Efficient Resolution**: Minimal overhead for template rendering

## Migration Guide

### For Existing Prompts
No changes required - all existing prompts continue to work as before.

### For New Features
1. Use the new `render_prompt_with_placeholders` function
2. Add custom placeholders via `PlaceholderContext`
3. Leverage built-in system and agent placeholders
4. Create custom providers for specialized needs

## Best Practices

1. **Use descriptive placeholder names**: `{{user_full_name}}` instead of `{{name}}`
2. **Provide default values**: For optional placeholders
3. **Document custom placeholders**: Include descriptions for team members
4. **Validate templates**: Use validation functions during development
5. **Handle errors gracefully**: Implement fallback mechanisms
6. **Cache expensive operations**: In custom providers
7. **Use appropriate priorities**: For custom providers

## Testing

Run the test suite to verify functionality:

```bash
python test_placeholder_system.py
```

The test covers:
- Basic built-in placeholders
- Custom placeholders
- Backward compatibility
- Template validation
- Documentation retrieval

## Conclusion

The enhanced placeholder system provides a powerful, extensible foundation for dynamic template rendering while maintaining full backward compatibility. It enables rich, context-aware prompts that can adapt to different scenarios and user requirements.
