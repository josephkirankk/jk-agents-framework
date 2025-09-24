# DateTime Injection Guide - JK-Agents Framework

## Overview

The JK-Agents Framework provides comprehensive datetime injection capabilities that automatically make current date and time information available to all agents. This feature ensures that agents are always aware of the current temporal context, which is crucial for time-sensitive analysis, logging, and business intelligence operations.

## Key Features

- **Automatic Injection**: Datetime information is automatically available in all agent prompts and configurations
- **Multiple Formats**: Support for various datetime formats (ISO, US, EU, Unix timestamps, etc.)
- **Performance Optimized**: Efficient placeholder resolution with minimal overhead
- **Cross-Platform**: Works consistently across Windows, macOS, and Linux
- **Extensible**: Easy to add custom datetime formatting

## Available Datetime Placeholders

### Core Datetime Placeholders

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{timestamp}}` | Current timestamp in ISO format | `2025-09-24T14:30:45` |
| `{{datetime}}` | Current datetime with timezone | `2025-09-24T14:30:45-07:00` |
| `{{datetime_local}}` | Local timezone ISO format | `2025-09-24T14:30:45-07:00` |
| `{{datetime_utc}}` | UTC timezone ISO format | `2025-09-24T21:30:45+00:00` |
| `{{date}}` | Current date in YYYY-MM-DD format | `2025-09-24` |
| `{{time}}` | Current time in 24-hour format | `14:30:45` |
| `{{time_24h}}` | 24-hour format (same as time) | `14:30:45` |
| `{{time_12h}}` | 12-hour format with AM/PM | `02:30:45 PM` |

### Formatted Date Options

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{date_iso}}` | ISO date format | `2025-09-24` |
| `{{date_us}}` | US format (MM/DD/YYYY) | `09/24/2025` |
| `{{date_eu}}` | European format (DD/MM/YYYY) | `24/09/2025` |
| `{{date_long}}` | Long date format | `September 24, 2025` |
| `{{date_short}}` | Short date format | `Sep 24, 2025` |

### Timestamp Variants

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{timestamp_unix}}` | Unix timestamp (seconds) | `1727212245` |
| `{{timestamp_ms}}` | Milliseconds since epoch | `1727212245000` |

### Date/Time Components

| Placeholder | Description | Example Output |
|-------------|-------------|----------------|
| `{{year}}` | Current year as integer | `2025` |
| `{{month}}` | Current month (1-12) | `9` |
| `{{month_name}}` | Full month name | `September` |
| `{{month_short}}` | Short month name | `Sep` |
| `{{day}}` | Day of month | `24` |
| `{{day_name}}` | Full day name | `Tuesday` |
| `{{day_short}}` | Short day name | `Tue` |
| `{{week_number}}` | ISO week number (1-53) | `39` |
| `{{quarter}}` | Quarter of year (1-4) | `3` |

## Usage Examples

### 1. Configuration Files

```yaml
business_context: |
  **CURRENT SESSION**: {{datetime}} ({{day_name}}, {{date_long}})
  **ANALYSIS PERIOD**: {{month_name}} {{year}}, Week {{week_number}}
  
  You are analyzing data for the current time period.
  Current context: {{date}} {{time}}

agents:
  - name: "data_agent"
    prompt: |
      **ANALYSIS TIMESTAMP**: {{datetime}} ({{day_name}})
      **CURRENT PERIOD**: Q{{quarter}} {{year}}, Week {{week_number}}
      
      Perform data analysis for the current period...
```

### 2. Agent Prompts

```python
# In agent configuration
prompt_template = """
**SESSION CONTEXT**: {{datetime}} ({{day_name}}, {{date_long}})
**QUERY TIMESTAMP**: {{timestamp}}

You are processing a request at {{time_12h}} on {{date_short}}.
Current quarter: Q{{quarter}} {{year}}

Your task: Analyze the provided data...
"""
```

### 3. Business Intelligence Context

```yaml
business_context: |
  **CURRENT DATE & TIME**: {{datetime}} ({{day_name}}, {{date_long}})
  **REPORTING PERIOD**: {{month_name}} {{year}}
  
  You are a business intelligence system analyzing data for:
  - Current session: {{datetime}}
  - Time period: Q{{quarter}} {{year}}
  - Week: {{week_number}} of {{month_name}}
  
  Include temporal context in all analysis.
```

### 4. Logging and Tracking

```yaml
supervisor:
  prompt: |
    **SESSION ID**: {{timestamp_ms}}
    **ANALYSIS START**: {{datetime}}
    
    You are coordinating agents for analysis session started at {{time_12h}}.
    Session date: {{date_long}}
    
    Plan and execute the following workflow...
```

## Implementation Details

### Automatic Registration

The datetime placeholders are automatically registered when the framework starts:

```python
from app.placeholder_system import get_default_registry

# The registry automatically includes SystemPlaceholderProvider
# with all datetime placeholders available
registry = get_default_registry()
```

### Performance Characteristics

- **Lazy Evaluation**: Datetime values are calculated only when needed
- **Efficient Resolution**: Multiple placeholder resolutions are optimized
- **Minimal Overhead**: < 1ms per placeholder resolution
- **Memory Efficient**: No long-term caching of time-sensitive data

### Cross-Platform Support

The datetime injection system works identically across:
- **Windows**: Full support for all timezone and formatting operations
- **macOS**: Native timezone and locale support
- **Linux**: Complete compatibility with system datetime libraries

## Best Practices

### 1. Contextual Usage

**✅ Good**: Use datetime placeholders to provide context
```yaml
business_context: |
  **CURRENT ANALYSIS**: {{datetime}} ({{day_name}})
  
  Analyze trends for the current period: Q{{quarter}} {{year}}
```

**❌ Avoid**: Overusing datetime in every sentence
```yaml
business_context: |
  At {{time}} on {{date}}, analyze data from {{datetime}} for {{month_name}}...
```

### 2. Appropriate Granularity

**✅ Good**: Use appropriate time granularity
```yaml
# For daily reports
prompt: "Daily report for {{date_long}} ({{day_name}})"

# For session tracking  
prompt: "Session {{timestamp_ms}} started at {{time_12h}}"

# For quarterly analysis
prompt: "Q{{quarter}} {{year}} performance analysis"
```

### 3. Timezone Awareness

**✅ Good**: Be explicit about timezone context
```yaml
business_context: |
  **Analysis Time**: {{datetime_local}} (Local)
  **UTC Reference**: {{datetime_utc}}
```

### 4. Performance Optimization

**✅ Good**: Use specific placeholders when possible
```yaml
# More efficient - specific placeholder
prompt: "Year-end report for {{year}}"

# Less efficient - multiple placeholders when one would do
prompt: "Year-end report for {{month}}/{{day}}/{{year}}"
```

## Advanced Usage

### Custom Datetime Formatting

You can add custom datetime placeholders through the PlaceholderContext:

```python
from app.placeholder_system import PlaceholderContext
from datetime import datetime

context = PlaceholderContext()

# Add custom formatters
context.add_custom_placeholder(
    "financial_quarter", 
    f"FY{datetime.now().year}-Q{(datetime.now().month - 1) // 3 + 1}"
)

context.add_custom_placeholder(
    "session_id",
    datetime.now().strftime("%Y%m%d_%H%M%S")
)
```

### Conditional Datetime Logic

```yaml
business_context: |
  **Business Hours Context**: 
  {% if hour >= 9 and hour <= 17 %}
  Current time {{time_12h}} is during business hours.
  {% else %}
  Current time {{time_12h}} is outside business hours.
  {% endif %}
  
  **Weekend Context**:
  {% if day_name in ['Saturday', 'Sunday'] %}
  Weekend analysis mode for {{date_long}}.
  {% else %}
  Weekday analysis mode for {{day_name}}.
  {% endif %}
```

## Testing

### Running DateTime Tests

```bash
# Run all datetime injection tests
python test/test_datetime_injection.py

# Run with verbose output
pytest test/test_datetime_injection.py -v

# Run specific test categories
pytest test/test_datetime_injection.py::TestSystemPlaceholderProvider -v
```

### Test Coverage

The test suite covers:
- ✅ All datetime placeholder types
- ✅ Edge cases (leap years, timezone boundaries)
- ✅ Performance characteristics
- ✅ Template rendering integration
- ✅ Cross-platform compatibility
- ✅ Error handling

## Troubleshooting

### Common Issues

**Issue**: Placeholder not resolving
```
Error: Placeholder 'datetime' not found
```
**Solution**: Ensure the SystemPlaceholderProvider is registered
```python
from app.placeholder_system import get_default_registry
registry = get_default_registry()  # Auto-registers system providers
```

**Issue**: Timezone issues
```
Error: Timezone not recognized
```
**Solution**: Ensure system timezone is properly configured
```bash
# On macOS/Linux
timedatectl status

# On Windows
tzutil /g
```

**Issue**: Performance concerns
```
Warning: Slow placeholder resolution
```
**Solution**: Use more specific placeholders and avoid excessive datetime calls
```yaml
# Instead of multiple calls
prompt: "{{datetime}} {{datetime}} {{datetime}}"

# Use once and reference
prompt: "Session {{datetime}} - analyzing data for current session"
```

### Debug Mode

Enable debug logging to troubleshoot datetime injection:

```python
import logging
logging.getLogger('placeholder_providers').setLevel(logging.DEBUG)
logging.getLogger('placeholder_registry').setLevel(logging.DEBUG)
```

## Migration Guide

### From Manual Datetime Handling

**Before** (manual datetime in prompts):
```yaml
business_context: |
  # You had to manually update dates
  Analysis for September 2025, Week 39
```

**After** (automatic datetime injection):
```yaml
business_context: |
  **CURRENT ANALYSIS**: {{month_name}} {{year}}, Week {{week_number}}
```

### From Custom Datetime Code

**Before** (custom datetime code):
```python
from datetime import datetime

def build_context():
    return {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "current_time": datetime.now().strftime("%H:%M:%S")
    }
```

**After** (built-in placeholders):
```yaml
# Automatically available in all configs
prompt: |
  Current analysis time: {{date}} {{time}}
  Session: {{datetime}}
```

## Security Considerations

- **No Sensitive Data**: Datetime placeholders don't expose sensitive system information
- **Read-Only**: All datetime operations are read-only with no system modification
- **Timezone Safety**: No exposure of system timezone configuration details
- **Performance Bounds**: Built-in limits prevent excessive datetime calculations

## Conclusion

The datetime injection feature provides a powerful, efficient way to make all agents in the JK-Agents Framework temporally aware. By using the built-in placeholders, you can:

- Ensure consistent datetime context across all agents
- Improve analysis accuracy with temporal awareness
- Simplify configuration management
- Maintain high performance with optimized placeholder resolution

For additional help or custom requirements, refer to the framework's main documentation or create an issue in the project repository.