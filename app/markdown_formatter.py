from __future__ import annotations
import re
from typing import Dict, Any, Optional
from datetime import datetime


def format_result_as_markdown(
    result: Dict[str, Any],
    user_input: str,
    business_context: Optional[str] = None
) -> str:
    """
    Format the execution result into user-friendly Markdown.
    
    Args:
        result: The result dictionary from execute_plan
        user_input: The original user question
        business_context: Optional business context for personalization
    
    Returns:
        Formatted Markdown string
    """
    if not result:
        return "# Error\n\nNo results were generated."
    
    # Extract components
    plan = result.get("plan", {})
    final_result = result.get("final_result", {})
    status = result.get("status", "unknown")
    
    # Start building markdown
    markdown_parts = []
    
    # Header with user question
    markdown_parts.append("# Response to Your Query")
    markdown_parts.append(f"\n**Your Question:** {user_input}\n")
    
    # Add timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    markdown_parts.append(f"*Generated on {timestamp}*\n")
    
    # Status indicator
    if status == "completed":
        markdown_parts.append("✅ **Status:** Successfully completed\n")
    elif status == "paused_for_human":
        markdown_parts.append("⏸️ **Status:** Paused for human intervention\n")
    else:
        markdown_parts.append(f"ℹ️ **Status:** {status}\n")
    
    # Main results section
    if final_result:
        markdown_parts.append("## Summary\n")
        
        # Check if we have multiple steps or just one
        step_items = list(final_result.items())
        
        if len(step_items) == 1:
            # Single step - show content directly
            step_id, step_data = step_items[0]
            content = step_data.get("raw", step_data.get("summary", ""))
            markdown_parts.append(f"{content}\n")
        else:
            # Multiple steps - organize by step
            for i, (step_id, step_data) in enumerate(step_items, 1):
                content = step_data.get("raw", step_data.get("summary", ""))
                
                # Try to extract a meaningful title from the content
                title = _extract_step_title(content, step_id, i)
                markdown_parts.append(f"### {title}\n")
                markdown_parts.append(f"{content}\n")
    
    # Plan details (collapsible section for transparency)
    if plan and plan.get("plan"):
        markdown_parts.append("---\n")
        markdown_parts.append("<details>\n")
        markdown_parts.append("<summary>📋 Execution Plan Details ")
        markdown_parts.append("(Click to expand)</summary>\n")
        goal = plan.get('goal', 'Not specified')
        markdown_parts.append(f"\n**Goal:** {goal}\n")
        markdown_parts.append("\n**Steps Executed:**\n")
        
        for step in plan.get("plan", []):
            step_id = step.get("id", "unknown")
            agent = step.get("agent", "unknown")
            task = step.get("task", "No task description")
            depends_on = step.get("depends_on", [])
            
            markdown_parts.append(f"- **{step_id}** ({agent}): {task}")
            if depends_on:
                dep_list = ', '.join(depends_on)
                markdown_parts.append(f" *[depends on: {dep_list}]*")
            markdown_parts.append("\n")
        
        markdown_parts.append("</details>\n")
    
    # Footer note about sources
    content_str = "".join(markdown_parts)
    if _contains_urls(content_str):
        markdown_parts.append("---\n")
        note = "*Please click on the provided links to access the most "
        note += "current information.*\n"
        markdown_parts.append(note)
    
    return "".join(markdown_parts)


def _extract_step_title(content: str, step_id: str, step_number: int) -> str:
    """Extract a meaningful title from step content."""
    if not content:
        return f"{step_number}. Step {step_id}"
    
    # Look for common patterns that might indicate what the step is about
    content_lower = content.lower()
    
    if "weather" in content_lower:
        return f"{step_number}. Weather Information"
    elif "news" in content_lower:
        return f"{step_number}. News Updates"
    elif "search" in content_lower:
        return f"{step_number}. Search Results"
    elif "calculate" in content_lower or "math" in content_lower:
        return f"{step_number}. Calculations"
    else:
        # Try to extract the first sentence or meaningful phrase
        first_line = content.split('\n')[0].strip()
        if len(first_line) > 5 and len(first_line) < 80:
            # Clean up common prefixes
            pattern = r'^(Here are?|To |For |The )'
            first_line = re.sub(pattern, '', first_line, flags=re.IGNORECASE)
            first_line = first_line.rstrip('.:')
            return f"{step_number}. {first_line}"
        else:
            return f"{step_number}. Step {step_id}"


def _contains_urls(text: str) -> bool:
    """Check if the text contains URLs."""
    url_pattern = r'https?://[^\s\)]+|www\.[^\s\)]+'
    return bool(re.search(url_pattern, text))


def format_direct_agent_result(
    content: str, agent_name: str, user_input: str
) -> str:
    """
    Format result from direct agent execution as Markdown.
    
    Args:
        content: The agent's response content
        agent_name: Name of the agent that provided the response
        user_input: The original user question
    
    Returns:
        Formatted Markdown string
    """
    markdown_parts = []
    
    # Header with user question
    agent_display = agent_name.title().replace('_', ' ')
    markdown_parts.append(f"# Response from {agent_display}")
    markdown_parts.append(f"\n**Your Question:** {user_input}\n")
    
    # Add timestamp
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    markdown_parts.append(f"*Generated on {timestamp}*\n")
    
    # Main content
    markdown_parts.append("## Response\n")
    markdown_parts.append(f"{content}\n")
    
    # Footer note about sources if URLs are present
    if _contains_urls(content):
        markdown_parts.append("---\n")
        note = "*Please click on the provided links to access the most "
        note += "current information.*\n"
        markdown_parts.append(note)
    
    return "".join(markdown_parts)
