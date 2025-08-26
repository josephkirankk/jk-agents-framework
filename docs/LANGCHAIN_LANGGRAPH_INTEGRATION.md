# LangChain + LangGraph Integration Guide

This guide shows how to integrate LangChain with LangGraph using the latest documentation from Context7.

## Installation

```bash
pip install -U langgraph langchain
```

## Basic Example: Simple Chain with LangGraph

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from typing import TypedDict

# Define state structure
class State(TypedDict):
    input: str
    output: str

# Initialize your LLM
llm = init_chat_model("openai:gpt-4")

# Define a node function
def chain_action(state: State):
    prompt = state["input"]
    response = llm.invoke(prompt)
    return {"output": response.content}

# Create the workflow graph
graph = StateGraph(State)
graph.add_node("chain_node", chain_action)
graph.set_entry_point("chain_node")
graph.set_finish_point("chain_node")

# Compile the graph
compiled_graph = graph.compile()

# Run the graph
result = compiled_graph.invoke({"input": "What is the capital of France?"})
print(result["output"])
```

## Advanced Example: React Agent with Tools

```python
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain_core.messages import BaseMessage
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Define state with message handling
class State(TypedDict):
    messages: Annotated[list, add_messages]

# Initialize components
llm = init_chat_model("openai:gpt-4")
tool = TavilySearch(max_results=2)
tools = [tool]
llm_with_tools = llm.bind_tools(tools)

# Define the chatbot node
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Create the graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# Add tool node
tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

# Add conditional edges
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.set_entry_point("chatbot")

# Add memory for conversation state
memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Run with conversation memory
config = {"configurable": {"thread_id": "1"}}
events = graph.stream(
    {"messages": [{"role": "user", "content": "Hi there! My name is Will."}]},
    config,
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()
```

## Simple React Agent Creation

```python
from langgraph.prebuilt import create_react_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

# Create a React agent with tools
agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_weather],
    prompt="You are a helpful assistant"
)

# Run the agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)
print(result)
```

## Streaming and State Management

```python
# Stream events with specific thread ID
events = graph.stream(
    {"messages": [{"role": "user", "content": "Remember my name?"}]},
    {"configurable": {"thread_id": "2"}},
    stream_mode="values",
)
for event in events:
    event["messages"][-1].pretty_print()

# Get current state snapshot
snapshot = graph.get_state(config)
print(f"Next node: {snapshot.next}")
```

## Key Features

### Memory and Checkpointing
- Use `MemorySaver()` for in-memory state persistence
- Use `SqliteSaver` or `PostgresSaver` for production
- Thread IDs enable separate conversation contexts

### Tool Integration
- `ToolNode` handles tool execution automatically
- `tools_condition` determines when to use tools
- Tools can be any callable function with proper annotations

### State Management
- `StateGraph` manages conversation state
- `add_messages` helper for message list handling
- Conditional edges for dynamic workflow routing

### Streaming Support
- `stream_mode="values"` for real-time updates
- Event-based processing for responsive UIs
- Resumable connections with event IDs

## Best Practices

1. **Always define clear state types** using TypedDict
2. **Use proper message handling** with add_messages
3. **Implement checkpointing** for production applications
4. **Handle tool errors gracefully** in your node functions
5. **Use thread IDs** for multi-user applications

## Error Handling

```python
def safe_chatbot(state: State):
    try:
        return {"messages": [llm_with_tools.invoke(state["messages"])]}
    except Exception as e:
        return {"messages": [{"role": "assistant", "content": f"Error: {str(e)}"}]}
```

This integration provides a powerful foundation for building sophisticated AI applications that combine LangChain's ecosystem with LangGraph's orchestration capabilities.
