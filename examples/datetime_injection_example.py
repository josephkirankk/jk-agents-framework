#!/usr/bin/env python3
"""
Example demonstrating datetime injection functionality in the JK-Agents Framework.

This example shows how datetime placeholders are automatically resolved
in agent configurations and templates.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from placeholder_system import PlaceholderContext, SystemPlaceholderProvider
from template_utils import render_prompt_with_placeholders


def demonstrate_datetime_placeholders():
    """Demonstrate all available datetime placeholders."""
    print("🕒 JK-Agents Framework - DateTime Injection Demo")
    print("=" * 50)
    
    # Create a provider to show supported placeholders
    provider = SystemPlaceholderProvider()
    supported = provider.get_supported_placeholders()
    
    # Filter datetime-related placeholders
    datetime_placeholders = [
        p for p in supported 
        if any(keyword in p for keyword in ['time', 'date', 'year', 'month', 'day', 'quarter', 'week', 'timestamp'])
    ]
    
    print(f"\n📅 Available DateTime Placeholders: {len(datetime_placeholders)}")
    print("-" * 30)
    
    # Show current values for key placeholders
    context = PlaceholderContext()
    built_context = context.build_context()
    
    key_placeholders = [
        'datetime', 'date', 'time', 'date_long', 'time_12h',
        'year', 'quarter', 'month_name', 'day_name', 'week_number'
    ]
    
    for placeholder in key_placeholders:
        if placeholder in built_context:
            value = built_context[placeholder]
            print(f"{{{{%s}}}} = %s" % (placeholder, value))


def demonstrate_config_template():
    """Demonstrate datetime injection in configuration templates."""
    print("\n🎯 Configuration Template Example")
    print("-" * 35)
    
    # Sample configuration template with datetime placeholders
    config_template = """
**CURRENT SESSION**: {{datetime}} ({{day_name}}, {{date_long}})
**ANALYSIS PERIOD**: {{month_name}} {{year}}, Week {{week_number}}

You are an Azure DevOps Intelligence System analyzing data for the current period.

Key Context:
- Current Date/Time: {{date}} {{time}}  
- Quarter: Q{{quarter}} {{year}}
- Session ID: {{timestamp_ms}}
- Business Hours: {{time_12h}}

Your mission is to provide accurate, time-aware analysis.
    """.strip()
    
    # Render the template with datetime placeholders
    rendered = render_prompt_with_placeholders(config_template)
    
    print("Template:")
    print(config_template[:200] + "..." if len(config_template) > 200 else config_template)
    print("\nRendered Output:")
    print(rendered)


def demonstrate_agent_prompt():
    """Demonstrate datetime injection in agent prompts."""
    print("\n🤖 Agent Prompt Example")
    print("-" * 25)
    
    # Agent prompt template
    agent_prompt = """
**ANALYSIS TIMESTAMP**: {{datetime}} ({{day_name}})
**CURRENT PERIOD**: Q{{quarter}} {{year}}, Week {{week_number}} of {{month_name}}

You are the ADO Data Analysis Expert processing a request on {{date_short}}.

Context for this analysis session:
- Started at: {{time_12h}}
- Current year: {{year}}
- Current quarter: Q{{quarter}}
- Day of week: {{day_name}}

Execute analysis with temporal awareness for the current period.
    """.strip()
    
    rendered = render_prompt_with_placeholders(agent_prompt)
    print("Rendered Agent Prompt:")
    print(rendered)


def demonstrate_performance():
    """Demonstrate performance of datetime placeholder resolution."""
    print("\n⚡ Performance Demonstration")
    print("-" * 28)
    
    import time
    
    context = PlaceholderContext()
    
    # Measure time for multiple resolutions
    start_time = time.time()
    
    iterations = 100
    for i in range(iterations):
        built_context = context.build_context()
        # Access several datetime placeholders
        _ = built_context.get('datetime')
        _ = built_context.get('date')
        _ = built_context.get('time')
        _ = built_context.get('year')
        _ = built_context.get('quarter')
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / iterations
    
    print(f"Performance Results:")
    print(f"- {iterations} context builds with 5 datetime placeholders each")
    print(f"- Total time: {total_time:.4f} seconds")
    print(f"- Average per build: {avg_time*1000:.2f} ms")
    print(f"- Performance: {'✅ Excellent' if avg_time < 0.001 else '✅ Good' if avg_time < 0.01 else '⚠️  Needs optimization'}")


def demonstrate_custom_placeholders():
    """Demonstrate adding custom datetime-related placeholders."""
    print("\n🔧 Custom DateTime Placeholders")
    print("-" * 32)
    
    context = PlaceholderContext()
    
    # Add some custom datetime-related placeholders
    now = datetime.now()
    context.add_custom_placeholders({
        'financial_quarter': f"FY{now.year}-Q{(now.month - 1) // 3 + 1}",
        'session_id': now.strftime("%Y%m%d_%H%M%S"),
        'business_day_type': 'Weekday' if now.weekday() < 5 else 'Weekend',
        'time_period': 'Morning' if 5 <= now.hour < 12 else 'Afternoon' if 12 <= now.hour < 17 else 'Evening' if 17 <= now.hour < 21 else 'Night'
    })
    
    template = """
Custom DateTime Context:
- Financial Quarter: {{financial_quarter}}
- Session ID: {{session_id}}
- Business Day Type: {{business_day_type}}
- Time Period: {{time_period}}
- Standard Date: {{date_long}}
    """.strip()
    
    rendered = render_prompt_with_placeholders(template, placeholder_context=context)
    print("Custom Placeholders in Action:")
    print(rendered)


if __name__ == "__main__":
    # Run all demonstrations
    demonstrate_datetime_placeholders()
    demonstrate_config_template()
    demonstrate_agent_prompt()
    demonstrate_performance()
    demonstrate_custom_placeholders()
    
    print("\n🎉 DateTime Injection Demo Complete!")
    print("=" * 50)
    print("\nNext Steps:")
    print("- Update your config files with datetime placeholders")
    print("- Run tests: python test/test_datetime_injection.py")
    print("- Check documentation: docs/datetime-injection-guide.md")