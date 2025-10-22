# Deep Agents Usage Examples

**Version:** 1.0  
**Last Updated:** October 2025

---

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Basic Usage Patterns](#basic-usage-patterns)
3. [Real-World Scenarios](#real-world-scenarios)
4. [Integration Examples](#integration-examples)
5. [Testing Examples](#testing-examples)

---

## Quick Start Examples

### Example 1: Minimal Deep Agent

**File:** `examples/minimal_deep_agent.py`

```python
"""Minimal Deep Agent Example"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig
from dotenv import load_dotenv

load_dotenv()


async def main():
    # Create agent configuration
    agent_config = AgentConfig(
        name="simple_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="""You are a helpful assistant with filesystem capabilities.
        
        When answering questions:
        1. Store your research in /notes.md
        2. Provide clear, concise answers
        """,
        description="Simple deep agent",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=[],
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    # Build agent
    agent, mcp_client = await build_agent(
        agent_cfg=agent_config,
        default_model="openai:gpt-4o-mini",
    )
    
    # Invoke agent
    result = agent.invoke(
        {"messages": [("user", "Explain what LangGraph is")]},
        config={"configurable": {"thread_id": "test-1"}}
    )
    
    # Print response
    print(result["messages"][-1].content)
    
    # Cleanup
    if mcp_client:
        await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
python examples/minimal_deep_agent.py
```

### Example 2: Using Configuration File

**Configuration:** `config/my_agent.yaml`

```yaml
models:
  default: "openai:gpt-4o-mini"

temperature: 0.2
persistence:
  type: "memory"

supervisor:
  name: "supervisor"
  model: "openai:gpt-4o-mini"
  prompt: "Create execution plans. Return JSON with goal and plan."

agents:
  - name: "my_agent"
    agent_type: "deep"
    model: "openai:gpt-4o-mini"
    description: "My deep agent"
    prompt: "You are a helpful assistant with advanced capabilities."
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
    mcp_servers: {}
    http_tools: {}
    python_tools: {}
```

**Script:** `examples/use_config_file.py`

```python
"""Load Deep Agent from YAML Configuration"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

load_dotenv()


async def main():
    # Load configuration
    config_path = Path("config/my_agent.yaml")
    app_config = load_app_config(config_path)
    
    # Get agent configuration
    agent_cfg = app_config.agents[0]
    default_model = app_config.models.get('default')
    
    # Build agent
    agent, mcp_client = await build_agent(
        agent_cfg=agent_cfg,
        default_model=default_model,
    )
    
    # Test query
    result = await agent.ainvoke(
        {"messages": [("user", "What are the benefits of Deep Agents?")]},
        config={"configurable": {"thread_id": "session-1"}}
    )
    
    print(result["messages"][-1].content)
    
    # Cleanup
    if mcp_client:
        await mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Basic Usage Patterns

### Pattern 1: Multi-Turn Conversation

```python
"""Multi-Turn Conversation with Context"""
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig


async def multiturn_conversation():
    # Build agent
    config = AgentConfig(
        name="conversational_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="You are a helpful conversational assistant.",
        deep_agent_config=DeepAgentConfig(enabled=True),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    agent, _ = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
    )
    
    # Same thread_id maintains context
    thread_id = "conversation-123"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Turn 1
    result1 = await agent.ainvoke(
        {"messages": [("user", "Tell me about quantum computing")]},
        config=config
    )
    print("Turn 1:", result1["messages"][-1].content[:100], "...")
    
    # Turn 2 - Agent remembers previous context
    result2 = await agent.ainvoke(
        {"messages": [("user", "What are its practical applications?")]},
        config=config
    )
    print("Turn 2:", result2["messages"][-1].content[:100], "...")
    
    # Turn 3 - Context still maintained
    result3 = await agent.ainvoke(
        {"messages": [("user", "Which companies are leading in this field?")]},
        config=config
    )
    print("Turn 3:", result3["messages"][-1].content[:100], "...")


asyncio.run(multiturn_conversation())
```

### Pattern 2: Streaming Responses

```python
"""Stream Agent Responses"""
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig


async def streaming_example():
    # Build agent
    config = AgentConfig(
        name="streaming_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="You are a helpful assistant.",
        deep_agent_config=DeepAgentConfig(enabled=True),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    agent, _ = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
    )
    
    # Stream responses
    print("Streaming response:\n")
    
    for chunk in agent.stream(
        {"messages": [("user", "Explain deep learning")]},
        config={"configurable": {"thread_id": "stream-1"}},
        stream_mode="values"
    ):
        if "messages" in chunk:
            latest_message = chunk["messages"][-1]
            if hasattr(latest_message, 'content'):
                print(".", end="", flush=True)
    
    print("\n\nStream complete!")


asyncio.run(streaming_example())
```

### Pattern 3: Accessing Virtual Filesystem

```python
"""Access Virtual Filesystem State"""
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig


async def filesystem_example():
    config = AgentConfig(
        name="fs_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="""Store your findings in organized files:
        - /summary.md for summaries
        - /details.txt for detailed information
        """,
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    agent, _ = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
    )
    
    # Agent creates files during execution
    result = await agent.ainvoke(
        {"messages": [("user", "Research Python async programming and store findings")]},
        config={"configurable": {"thread_id": "fs-test"}}
    )
    
    # Access filesystem state
    if "files" in result:
        print("\nFiles created:")
        for path, content in result["files"].items():
            print(f"  {path}: {len(content)} characters")
            print(f"    Preview: {content[:100]}...")
    
    # Get state from checkpointer
    thread_config = {"configurable": {"thread_id": "fs-test"}}
    state = agent.get_state(thread_config)
    
    if state and "files" in state.values:
        print("\nFiles in state:")
        for path in state.values["files"].keys():
            print(f"  {path}")


asyncio.run(filesystem_example())
```

### Pattern 4: Using Subagents

```python
"""Delegate to Specialized Subagents"""
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig


async def subagent_example():
    # Define subagents
    subagents = [
        SubAgentConfig(
            name="researcher",
            description="Conducts research on specific topics",
            system_prompt="You are a research specialist. Gather information thoroughly.",
            model="openai:gpt-4o-mini",
            tools=[],
        ),
        SubAgentConfig(
            name="analyzer",
            description="Analyzes data and provides insights",
            system_prompt="You are an analysis specialist. Identify patterns and trends.",
            model="openai:gpt-4o-mini",
            tools=[],
        ),
    ]
    
    # Main agent with subagents
    config = AgentConfig(
        name="orchestrator",
        agent_type="deep",
        model="openai:gpt-4o",
        prompt="""You are an orchestrator with specialized subagents:
        - researcher: For information gathering
        - analyzer: For data analysis
        
        Delegate tasks to appropriate subagents and synthesize results.
        """,
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            subagents=subagents,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    agent, _ = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o",
    )
    
    # Complex task requiring multiple subagents
    result = await agent.ainvoke(
        {"messages": [(
            "user",
            "Research AI trends and analyze their impact on software development"
        )]},
        config={"configurable": {"thread_id": "subagent-test"}}
    )
    
    print(result["messages"][-1].content)


asyncio.run(subagent_example())
```

---

## Real-World Scenarios

### Scenario 1: Web Research Assistant

**Configuration:** `config/web_research_agent.yaml`

```yaml
models:
  default: "openai:gpt-4o"

agents:
  - name: "web_researcher"
    agent_type: "deep"
    model: "openai:gpt-4o"
    prompt: |
      You are a web research specialist.
      
      Tools available:
      - google_search(query, gl="region", hl="language")
      - scrape(url)
      
      Workflow:
      1. Use google_search to find information
      2. Scrape relevant pages for details
      3. Store findings in /research.md
      4. Provide comprehensive summary
      
      For India queries: gl="in", hl="en"
      For US queries: gl="us", hl="en"
    
    deep_agent_config:
      enabled: true
      enable_filesystem: true
      enable_todolist: true
    
    mcp_servers:
      serper-search:
        description: "Google Search & Scrape"
        transport: "stdio"
        command: "npx"
        args: ["-y", "serper-search-scrape-mcp-server"]
        env:
          SERPER_API_KEY: "${SERPER_API_KEY}"
```

**Usage:** `examples/web_research_example.py`

```python
"""Web Research with Serper Search"""
import asyncio
from pathlib import Path
from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

load_dotenv()


async def research_topic(topic: str):
    # Load configuration
    config_path = Path("config/web_research_agent.yaml")
    app_config = load_app_config(config_path)
    
    # Build agent
    agent_cfg = app_config.agents[0]
    default_model = app_config.models.get('default')
    
    agent, mcp_client = await build_agent(
        agent_cfg=agent_cfg,
        default_model=default_model,
    )
    
    try:
        # Research query
        result = await agent.ainvoke(
            {"messages": [("user", f"Research {topic} and provide a comprehensive report")]},
            config={"configurable": {"thread_id": f"research-{topic.replace(' ', '-')}"}}
        )
        
        # Print results
        print(f"\n{'='*70}")
        print(f"RESEARCH RESULTS: {topic}")
        print(f"{'='*70}\n")
        print(result["messages"][-1].content)
        
        # Show files created
        if "files" in result:
            print(f"\n\nFiles created: {list(result['files'].keys())}")
        
    finally:
        if mcp_client:
            await mcp_client.cleanup()


# Run
asyncio.run(research_topic("Quantum Computing Applications"))
```

### Scenario 2: Code Analysis Assistant

```python
"""Code Analysis with Subagents"""
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig


async def analyze_codebase():
    # Define specialized subagents
    subagents = [
        SubAgentConfig(
            name="code-reader",
            description="Reads and understands code structure",
            system_prompt="""You are a code reading specialist.
            - Read code files
            - Identify structure and patterns
            - Extract key components
            """,
            model="openai:gpt-4o-mini",
            tools=[],
        ),
        SubAgentConfig(
            name="bug-detector",
            description="Identifies potential bugs and issues",
            system_prompt="""You are a bug detection specialist.
            - Analyze code for common bugs
            - Identify security issues
            - Flag anti-patterns
            """,
            model="openai:gpt-4o",
            tools=[],
        ),
        SubAgentConfig(
            name="optimizer",
            description="Suggests performance optimizations",
            system_prompt="""You are a performance optimization specialist.
            - Identify performance bottlenecks
            - Suggest optimizations
            - Recommend best practices
            """,
            model="openai:gpt-4o",
            tools=[],
        ),
    ]
    
    # Main orchestrator
    config = AgentConfig(
        name="code_analyzer",
        agent_type="deep",
        model="openai:gpt-4o",
        prompt="""You are a code analysis orchestrator.
        
        Subagents:
        - code-reader: Reads and structures code
        - bug-detector: Finds bugs and issues
        - optimizer: Suggests performance improvements
        
        Workflow:
        1. Use code-reader to understand codebase
        2. Store structure in /code_structure.md
        3. Use bug-detector for issue analysis
        4. Use optimizer for performance review
        5. Compile final report in /analysis_report.md
        """,
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            subagents=subagents,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    agent, _ = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o",
    )
    
    # Analyze code
    code_to_analyze = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
    """
    
    result = await agent.ainvoke(
        {"messages": [(
            "user",
            f"Analyze this code and provide feedback:\n\n{code_to_analyze}"
        )]},
        config={"configurable": {"thread_id": "code-analysis-1"}}
    )
    
    print(result["messages"][-1].content)


asyncio.run(analyze_codebase())
```

### Scenario 3: Product Research Agent

**Complete Example:** `examples/product_research.py`

```python
"""Product Research Agent with Price Comparison"""
import asyncio
from pathlib import Path
from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

load_dotenv()


async def research_product(product_name: str, region: str = "in"):
    """
    Research a product including specifications, prices, and reviews.
    
    Args:
        product_name: Product to research
        region: Region code (in, us, uk)
    """
    # Use pre-configured agent
    config_path = Path("config/deep_agent_advanced_serpapi.yaml")
    app_config = load_app_config(config_path)
    
    # Build agent
    agent_cfg = app_config.agents[0]
    default_model = app_config.models.get('default')
    
    agent, mcp_client = await build_agent(
        agent_cfg=agent_cfg,
        default_model=default_model,
    )
    
    try:
        # Research query
        query = f"""Research {product_name} in {region.upper()} market.
        
        Please provide:
        1. Product specifications
        2. Current prices from multiple sellers
        3. User reviews summary
        4. Where to buy (URLs)
        5. Comparison with alternatives
        
        Use gl="{region}" for region-specific results.
        Store findings in organized files.
        """
        
        print(f"\n{'='*70}")
        print(f"RESEARCHING: {product_name}")
        print(f"REGION: {region.upper()}")
        print(f"{'='*70}\n")
        
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config={"configurable": {"thread_id": f"product-{product_name.replace(' ', '-')}"}}
        )
        
        # Display results
        response = result["messages"][-1].content
        print(response)
        
        # Show files created
        if "files" in result:
            print(f"\n\n📁 Files Created:")
            for path in result["files"].keys():
                print(f"  - {path}")
        
        return result
        
    finally:
        if mcp_client:
            await mcp_client.cleanup()


async def main():
    # Example: Research smartphones
    await research_product("Samsung Galaxy S24", region="in")
    
    # Example: Research laptops
    # await research_product("MacBook Pro M3", region="us")


if __name__ == "__main__":
    asyncio.run(main())
```

**Run:**
```bash
export SERPER_API_KEY=your-key
python examples/product_research.py
```

---

## Integration Examples

### Integration 1: FastAPI REST API

```python
"""FastAPI Integration with Deep Agents"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import asyncio

from app.main import load_app_config
from app.agent_builder import build_agent

app = FastAPI(title="Deep Agent API")

# Global agent instance
agent = None
mcp_client = None


class QueryRequest(BaseModel):
    message: str
    thread_id: str = "default"


class QueryResponse(BaseModel):
    response: str
    files: dict = {}


@app.on_event("startup")
async def startup():
    """Initialize agent on startup"""
    global agent, mcp_client
    
    config_path = Path("config/deep_agent_basic_example.yaml")
    app_config = load_app_config(config_path)
    
    agent_cfg = app_config.agents[0]
    default_model = app_config.models.get('default')
    
    agent, mcp_client = await build_agent(
        agent_cfg=agent_cfg,
        default_model=default_model,
    )
    
    print("✅ Deep Agent initialized")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global mcp_client
    if mcp_client:
        await mcp_client.cleanup()


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """Query the deep agent"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent.ainvoke(
            {"messages": [("user", request.message)]},
            config={"configurable": {"thread_id": request.thread_id}}
        )
        
        response_content = result["messages"][-1].content
        files = result.get("files", {})
        
        return QueryResponse(
            response=response_content,
            files=files
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "agent_ready": agent is not None}


# Run with: uvicorn examples.fastapi_integration:app --reload
```

### Integration 2: CLI Tool

```python
"""CLI Tool with Deep Agent"""
import asyncio
import click
from pathlib import Path
from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

load_dotenv()


class DeepAgentCLI:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.agent = None
        self.mcp_client = None
    
    async def initialize(self):
        """Initialize agent"""
        app_config = load_app_config(self.config_path)
        agent_cfg = app_config.agents[0]
        default_model = app_config.models.get('default')
        
        self.agent, self.mcp_client = await build_agent(
            agent_cfg=agent_cfg,
            default_model=default_model,
        )
    
    async def query(self, message: str, thread_id: str = "cli-session"):
        """Execute query"""
        result = await self.agent.ainvoke(
            {"messages": [("user", message)]},
            config={"configurable": {"thread_id": thread_id}}
        )
        return result["messages"][-1].content
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mcp_client:
            await self.mcp_client.cleanup()


@click.group()
def cli():
    """Deep Agent CLI Tool"""
    pass


@cli.command()
@click.argument('query')
@click.option('--config', default='config/deep_agent_basic_example.yaml', help='Config file')
@click.option('--thread-id', default='cli-session', help='Thread ID')
def ask(query, config, thread_id):
    """Ask a question to the deep agent"""
    
    async def run():
        agent_cli = DeepAgentCLI(config)
        try:
            await agent_cli.initialize()
            response = await agent_cli.query(query, thread_id)
            click.echo(f"\n{response}\n")
        finally:
            await agent_cli.cleanup()
    
    asyncio.run(run())


@cli.command()
@click.option('--config', default='config/deep_agent_basic_example.yaml', help='Config file')
def interactive(config):
    """Interactive mode"""
    
    async def run():
        agent_cli = DeepAgentCLI(config)
        try:
            click.echo("Initializing agent...")
            await agent_cli.initialize()
            click.echo("✅ Agent ready! Type 'quit' to exit.\n")
            
            thread_id = "interactive-session"
            turn = 0
            
            while True:
                turn += 1
                query = click.prompt(f"[{turn}] You")
                
                if query.lower() in ['quit', 'exit']:
                    break
                
                response = await agent_cli.query(query, thread_id)
                click.echo(f"\nAgent: {response}\n")
                
        finally:
            await agent_cli.cleanup()
    
    asyncio.run(run())


if __name__ == '__main__':
    cli()


# Usage:
# python examples/cli_tool.py ask "What is LangGraph?"
# python examples/cli_tool.py interactive
```

---

## Testing Examples

### Unit Test Example

```python
"""Unit Tests for Deep Agent"""
import pytest
import asyncio
from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig


@pytest.fixture
async def deep_agent():
    """Create test deep agent"""
    config = AgentConfig(
        name="test_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="You are a test agent.",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
    )
    
    yield agent
    
    if mcp_client:
        await mcp_client.cleanup()


@pytest.mark.asyncio
async def test_basic_invocation(deep_agent):
    """Test basic agent invocation"""
    result = await deep_agent.ainvoke(
        {"messages": [("user", "Hello")]},
        config={"configurable": {"thread_id": "test-1"}}
    )
    
    assert "messages" in result
    assert len(result["messages"]) > 0
    assert result["messages"][-1].content


@pytest.mark.asyncio
async def test_filesystem_creation(deep_agent):
    """Test filesystem file creation"""
    result = await deep_agent.ainvoke(
        {"messages": [("user", "Create a file /test.txt with content 'Hello'")]},
        config={"configurable": {"thread_id": "test-fs"}}
    )
    
    # Check if files were created
    if "files" in result:
        assert "/test.txt" in result["files"]


@pytest.mark.asyncio
async def test_multiturn_context(deep_agent):
    """Test multi-turn conversation context"""
    thread_id = "test-multiturn"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Turn 1
    result1 = await deep_agent.ainvoke(
        {"messages": [("user", "My name is Alice")]},
        config=config
    )
    
    # Turn 2 - should remember name
    result2 = await deep_agent.ainvoke(
        {"messages": [("user", "What's my name?")]},
        config=config
    )
    
    response = result2["messages"][-1].content.lower()
    assert "alice" in response


# Run with: pytest examples/test_deep_agent.py -v
```

---

**Next:** See [Advanced Features](./33_deep_agents_advanced.md) for best practices, optimization, and complex scenarios.
