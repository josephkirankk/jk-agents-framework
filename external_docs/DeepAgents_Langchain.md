# DeepAgents: Advanced Agentic Framework for Python

DeepAgents is a Python package that implements sophisticated AI agents capable of planning, context management, and hierarchical task decomposition. Inspired by applications like Claude Code, Deep Research, and Manus, it enables agents to tackle complex, multi-step tasks through a combination of planning tools, subagent spawning, filesystem access, and detailed prompting. The framework is built on LangChain and LangGraph, providing a general-purpose architecture that extends beyond simple tool-calling loops to create "deep" agents that plan, act, and manage context over longer, more complex workflows.

At its core, DeepAgents addresses the limitations of shallow agents by providing built-in middleware for task planning (TodoListMiddleware), context management through a virtual filesystem (FilesystemMiddleware), and context isolation via subagent spawning (SubAgentMiddleware). These capabilities work together to prevent context window overflow, enable better organization of complex tasks, and allow agents to go deep on specific subtasks without polluting the main agent's context. The result is a system that can handle research, code analysis, multi-step reasoning, and other demanding workflows that would overwhelm traditional single-loop agents.

## APIs and Key Functions

### Creating a Deep Agent

```python
from deepagents import create_deep_agent
from tavily import TavilyClient
import os

# Initialize external API client
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Define custom tools
def internet_search(query: str, max_results: int = 5) -> dict:
    """Run a web search and return results"""
    return tavily_client.search(query, max_results=max_results)

# Create a deep agent with custom system prompt and tools
system_prompt = """You are an expert researcher. Conduct thorough research
and write polished reports. Use the internet_search tool to gather information."""

agent = create_deep_agent(
    tools=[internet_search],
    system_prompt=system_prompt,
    model="claude-sonnet-4-5-20250929",  # Optional: defaults to Claude Sonnet 4
)

# Invoke the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "What is LangGraph?"}]
})

# Access the final response
final_message = result["messages"][-1].content
print(final_message)
```

### Using Custom Models

```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

# Initialize any LangChain-compatible model
model = init_chat_model("openai:gpt-4o", temperature=0.7)

# Create agent with custom model
agent = create_deep_agent(
    model=model,
    system_prompt="You are a helpful coding assistant.",
)

# The agent works identically with any model
response = agent.invoke({
    "messages": [{"role": "user", "content": "Explain decorators in Python"}]
})
```

### Configuring Subagents for Task Decomposition

```python
from deepagents import create_deep_agent
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city"""
    return f"Weather in {city}: 72°F and sunny"

@tool
def internet_search(query: str) -> str:
    """Search the internet"""
    return f"Search results for: {query}"

# Define specialized subagents
subagents = [
    {
        "name": "weather-specialist",
        "description": "Use this agent to get weather information for any location",
        "system_prompt": "You are a weather specialist. Use the get_weather tool.",
        "tools": [get_weather],
        "model": "openai:gpt-4o",  # Can use different model per subagent
    },
    {
        "name": "research-specialist",
        "description": "Use for deep research requiring multiple searches",
        "system_prompt": "You are a research specialist. Conduct thorough research.",
        "tools": [internet_search],
    }
]

# Create main agent with subagents
agent = create_deep_agent(
    tools=[get_weather, internet_search],
    subagents=subagents,
    system_prompt="You are a helpful assistant. Delegate to specialists when appropriate."
)

# The agent will automatically use subagents for complex tasks
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Research climate change impact on Tokyo and get current weather there"
    }]
})

# Subagents isolate context - main agent only sees final results
print(result["messages"][-1].content)
```

### Using Pre-Compiled Custom Subagents

```python
from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def database_query(sql: str) -> str:
    """Execute SQL query"""
    return f"Query result: {sql}"

# Create a custom LangGraph agent
custom_db_agent = create_agent(
    model="openai:gpt-4o",
    tools=[database_query],
    system_prompt="You are a database specialist. Write and execute SQL queries.",
)

# Wrap as CompiledSubAgent
db_subagent = CompiledSubAgent(
    name="database-expert",
    description="Use for complex database queries and data analysis",
    runnable=custom_db_agent
)

# Use in main agent
agent = create_deep_agent(
    subagents=[db_subagent],
    system_prompt="You coordinate data analysis tasks."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze sales trends from Q4"}]
})
```

### Filesystem Tools for Context Management

```python
from deepagents import create_deep_agent

# Agent automatically has filesystem tools: ls, read_file, write_file, edit_file
agent = create_deep_agent(
    system_prompt="""You are a research assistant. When gathering large amounts
    of information, write it to files to manage context efficiently."""
)

# Agent can write files to manage context
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Research the top 10 programming languages and their use cases"
    }]
})

# Agent automatically writes large results to files like /research_notes.md
# Files persist in agent state for the conversation thread
print(result.get("files", {}).keys())  # Shows created files
```

### Long-Term Memory with Store

```python
from deepagents import create_deep_agent
from langgraph.store.memory import InMemoryStore

# Create a persistent store
store = InMemoryStore()

# Enable long-term memory
agent = create_deep_agent(
    store=store,
    use_longterm_memory=True,
    system_prompt="""You have access to long-term memory. Files prefixed with
    /memories/ persist across conversations."""
)

# First conversation
config1 = {"configurable": {"thread_id": "user-123"}}
agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Remember my favorite color is blue. Write to /memories/preferences.txt"
    }]
}, config=config1)

# Later conversation - different thread, same memory
config2 = {"configurable": {"thread_id": "user-456"}}
result = agent.invoke({
    "messages": [{"role": "user", "content": "What's my favorite color?"}]
}, config2)

# Agent reads from /memories/preferences.txt automatically
print(result["messages"][-1].content)  # "Your favorite color is blue"
```

### Human-in-the-Loop with Tool Interrupts

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool

@tool
def delete_database(name: str) -> str:
    """Delete a database - requires approval"""
    return f"Deleted database: {name}"

@tool
def read_database(name: str) -> str:
    """Read from database - no approval needed"""
    return f"Contents of {name}"

# Configure which tools require human approval
agent = create_deep_agent(
    tools=[delete_database, read_database],
    checkpointer=MemorySaver(),
    interrupt_on={
        "delete_database": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    }
)

config = {"configurable": {"thread_id": "session-1"}}

# Agent will pause before executing delete_database
for event in agent.stream({
    "messages": [{"role": "user", "content": "Delete the old-data database"}]
}, config, stream_mode="values"):
    if "__interrupt__" in event:
        # Human reviews and approves/rejects
        decision = input("Approve deletion? (approve/reject): ")
        agent.update_state(config, {"decision": decision})

# Continues after human decision
final_state = agent.get_state(config)
```

### Custom Middleware for Extended Functionality

```python
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import tool

@tool
def get_temperature(city: str) -> str:
    """Get temperature in a city"""
    return f"Temperature in {city}: 72°F"

@tool
def get_humidity(city: str) -> str:
    """Get humidity in a city"""
    return f"Humidity in {city}: 65%"

# Create custom middleware that adds tools
class WeatherMiddleware(AgentMiddleware):
    tools = [get_temperature, get_humidity]
    system_prompt = """You have access to temperature and humidity tools.
    Use them to provide comprehensive weather information."""

# Add to agent
agent = create_deep_agent(
    middleware=[WeatherMiddleware()],
    system_prompt="You are a weather information assistant."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What's the weather like in Seattle?"}]
})
```

### Streaming Agent Responses

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    system_prompt="You are a helpful assistant."
)

# Stream updates in real-time
for chunk in agent.stream({
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
}, stream_mode="values"):
    if "messages" in chunk:
        # Print latest message as it arrives
        chunk["messages"][-1].pretty_print()

# Alternative: Stream token-by-token
for chunk in agent.stream({
    "messages": [{"role": "user", "content": "Write a haiku about coding"}]
}, stream_mode="messages"):
    print(chunk.content, end="", flush=True)
```

### Using FilesystemMiddleware Independently

```python
from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain.agents import create_agent

# Add only filesystem tools without full deep agent setup
filesystem_middleware = FilesystemMiddleware(
    long_term_memory=False,
    system_prompt="Use files to store and retrieve information during your work."
)

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    middleware=[filesystem_middleware],
    system_prompt="You are a data analyst."
)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Analyze these numbers: 23, 45, 67, 89. Save results to /analysis.txt"
    }]
})
```

### Using SubAgentMiddleware Independently

```python
from deepagents.middleware.subagents import SubAgentMiddleware
from langchain.agents import create_agent
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> float:
    """Safely evaluate math expression"""
    return eval(expression)

# Add only subagent spawning capability
subagent_middleware = SubAgentMiddleware(
    default_model="openai:gpt-4o",
    default_tools=[calculate],
    subagents=[
        {
            "name": "math-specialist",
            "description": "Handles complex mathematical computations",
            "system_prompt": "You solve math problems step by step.",
            "tools": [calculate]
        }
    ]
)

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    middleware=[subagent_middleware],
    tools=[calculate]
)

result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Use the math specialist to solve: (45 * 89) + (123 / 4)"
    }]
})
```

### Async Agent Execution

```python
import asyncio
from deepagents import create_deep_agent

async def main():
    agent = create_deep_agent(
        system_prompt="You are a helpful assistant."
    )

    # Async invoke
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "Explain async programming"}]
    })

    # Async stream
    async for chunk in agent.astream({
        "messages": [{"role": "user", "content": "Count to 10"}]
    }, stream_mode="values"):
        if "messages" in chunk:
            print(chunk["messages"][-1].content)

asyncio.run(main())
```

### Integration with MCP Tools

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

async def main():
    # Connect to MCP servers and get tools
    mcp_client = MultiServerMCPClient({
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
        }
    })

    mcp_tools = await mcp_client.get_tools()

    # Create agent with MCP tools
    agent = create_deep_agent(
        tools=mcp_tools,
        system_prompt="You have access to filesystem operations via MCP."
    )

    # Use async methods with MCP
    async for chunk in agent.astream({
        "messages": [{"role": "user", "content": "List files in the workspace"}]
    }, stream_mode="values"):
        if "messages" in chunk:
            chunk["messages"][-1].pretty_print()

asyncio.run(main())
```

### Advanced Research Agent Example

```python
from deepagents import create_deep_agent
from tavily import TavilyClient
import os

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(query: str, max_results: int = 5) -> dict:
    """Search the web"""
    return tavily.search(query, max_results=max_results)

# Research subagent for focused investigation
research_subagent = {
    "name": "research-agent",
    "description": "Conducts deep research on specific topics. Give one topic at a time.",
    "system_prompt": """You are a dedicated researcher. Conduct thorough research
    and return a detailed report. Only your final message goes to the user.""",
    "tools": [internet_search]
}

# Critique subagent for review
critique_subagent = {
    "name": "critique-agent",
    "description": "Reviews and critiques research reports for quality.",
    "system_prompt": """You critique reports. Read the report from final_report.md
    and provide detailed feedback on completeness, accuracy, and clarity."""
}

# Main orchestrator agent
agent = create_deep_agent(
    tools=[internet_search],
    subagents=[research_subagent, critique_subagent],
    system_prompt="""You are an expert researcher. Your workflow:
    1. Write user question to /question.txt
    2. Use research-agent for deep investigation (can call multiple in parallel)
    3. Write findings to /final_report.md
    4. Use critique-agent to review report
    5. Refine report based on feedback
    6. Present final polished report to user"""
)

# Execute complex research task
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Compare the economic impacts of AI on healthcare vs manufacturing"
    }]
})

# Agent orchestrates multiple subagents, manages files, and delivers final report
print(result["messages"][-1].content)
```

## Summary and Integration Patterns

DeepAgents is designed for applications requiring sophisticated reasoning over complex, multi-step tasks where simple tool-calling loops fall short. Primary use cases include research assistants that need to gather, synthesize, and critique information across multiple sources; code analysis tools that must explore large codebases without overwhelming context windows; data analysis workflows that benefit from specialized subagents for different analytical tasks; and any scenario where task decomposition and context isolation improve performance. The framework excels at problems requiring planning, iterative refinement, and the ability to "go deep" on subtasks while maintaining a clean orchestration layer.

Integration patterns typically involve combining DeepAgents with external APIs (like Tavily for search), persistent storage systems (LangGraph Store for long-term memory), and checkpointers for conversation persistence and human-in-the-loop workflows. The middleware architecture allows developers to compose functionality incrementally—start with basic filesystem tools, add subagents for specific domains, layer in custom middleware for specialized capabilities, and configure interrupts for sensitive operations. Because DeepAgents builds on LangGraph, it integrates seamlessly with the LangGraph ecosystem including LangGraph Studio for visualization, LangGraph Cloud for deployment, and all standard LangChain components for models, tools, and retrievers. The result is a flexible, production-ready framework that scales from simple research assistants to complex multi-agent systems with minimal code.