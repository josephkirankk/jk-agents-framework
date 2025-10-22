"""
DeepAgents Integration Example

This script demonstrates how to use DeepAgents within the jk-agents-core framework.
It showcases:
1. Basic DeepAgent with filesystem and todolist
2. DeepAgent with multiple subagents
3. Context management and file operations
4. Comparison with standard ReAct agents

Usage:
    python examples/deep_agent_example.py --mode basic
    python examples/deep_agent_example.py --mode advanced
    python examples/deep_agent_example.py --mode comparison
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent_builder import build_agent
from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
from app.checkpointer_manager import get_global_checkpointer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)


async def example_basic_deep_agent():
    """
    Example 1: Basic DeepAgent with filesystem and todolist.
    
    This example demonstrates:
    - Creating a DeepAgent from configuration
    - Using virtual filesystem for context management
    - TodoList middleware for planning
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic DeepAgent")
    print("="*60)
    
    # Create agent configuration
    agent_config = AgentConfig(
        name="research_assistant",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="""You are a research assistant with advanced capabilities.
        
You have access to:
- Virtual filesystem (ls, read_file, write_file, edit_file)
- Task planning via todo list
- Multiple research tools

When given a research task:
1. Create a plan in your todo list
2. Store findings in organized files
3. Use the filesystem to manage context
4. Provide a final summary

Be thorough and well-organized.""",
        description="Research assistant with filesystem and planning",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=[]
        ),
        mcp_servers={},  # No MCP servers for basic example
        http_tools={},
        python_tools={},
    )
    
    try:
        # Build the agent
        log.info("Building basic DeepAgent...")
        checkpointer = get_global_checkpointer()
        agent, mcp_client = await build_agent(
            agent_cfg=agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        log.info("✅ DeepAgent created successfully!")
        
        # Test invocation
        thread_id = "basic_example_thread"
        config = {"configurable": {"thread_id": thread_id}}
        
        test_query = "Research the top 3 benefits of using LangGraph for building AI agents. Organize your findings in a file."
        
        print(f"\n📝 Query: {test_query}")
        print("\n🤖 Agent working...\n")
        
        result = agent.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config=config
        )
        
        # Extract final response
        final_message = result["messages"][-1]
        print(f"✅ Response:\n{final_message.content}\n")
        
        # Show files created (if accessible)
        if "files" in result:
            print(f"📁 Files created: {list(result['files'].keys())}")
        
    except Exception as e:
        log.error(f"Error in basic example: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


async def example_advanced_deep_agent():
    """
    Example 2: Advanced DeepAgent with subagents.
    
    This example demonstrates:
    - Multiple specialized subagents
    - Hierarchical task decomposition
    - Context isolation between subagents
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Advanced DeepAgent with Subagents")
    print("="*60)
    
    # Create subagent configurations
    subagents = [
        SubAgentConfig(
            name="web-researcher",
            description="Conducts focused web research on specific topics",
            system_prompt="You are a web research specialist. Gather information thoroughly and cite sources.",
            model="openai:gpt-4o-mini",
            tools=[],
        ),
        SubAgentConfig(
            name="synthesizer",
            description="Synthesizes information from multiple sources",
            system_prompt="You are an information synthesis expert. Create coherent summaries from multiple sources.",
            model="openai:gpt-4o-mini",
            tools=[],
        ),
    ]
    
    # Create agent configuration
    agent_config = AgentConfig(
        name="research_orchestrator",
        agent_type="deep",
        model="openai:gpt-4o",
        prompt="""You are a master research orchestrator with specialized subagents.

Available subagents:
- web-researcher: For gathering online information
- synthesizer: For combining and synthesizing findings

Your workflow:
1. Delegate focused research to web-researcher
2. Store findings in files
3. Use synthesizer to create final report
4. Present well-organized results

Use your filesystem to manage context efficiently.""",
        description="Master orchestrator with specialized subagents",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=subagents,
        ),
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    try:
        # Build the agent
        log.info("Building advanced DeepAgent with subagents...")
        checkpointer = get_global_checkpointer()
        agent, mcp_client = await build_agent(
            agent_cfg=agent_config,
            default_model="openai:gpt-4o",
            checkpointer=checkpointer,
        )
        
        log.info("✅ DeepAgent with subagents created successfully!")
        
        # Test invocation
        thread_id = "advanced_example_thread"
        config = {"configurable": {"thread_id": thread_id}}
        
        test_query = "Compare Python and JavaScript for backend development. Use subagents for research and synthesis."
        
        print(f"\n📝 Query: {test_query}")
        print("\n🤖 Agent orchestrating subagents...\n")
        
        result = agent.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config=config
        )
        
        # Extract final response
        final_message = result["messages"][-1]
        print(f"✅ Response:\n{final_message.content}\n")
        
    except Exception as e:
        log.error(f"Error in advanced example: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


async def example_comparison():
    """
    Example 3: Comparison between ReAct and DeepAgent.
    
    This demonstrates the differences in:
    - Response quality
    - Context management
    - Task organization
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: ReAct vs DeepAgent Comparison")
    print("="*60)
    
    test_query = "Explain the key differences between microservices and monolithic architecture. Provide examples."
    
    # Create ReAct agent
    print("\n1️⃣  Testing with standard ReAct agent...")
    react_config = AgentConfig(
        name="react_agent",
        agent_type="react",
        model="openai:gpt-4o-mini",
        prompt="You are a helpful software architecture expert.",
        description="Standard ReAct agent",
        mcp_servers={},
        http_tools={},
        python_tools={},
    )
    
    try:
        checkpointer = get_global_checkpointer()
        react_agent, _ = await build_agent(
            agent_cfg=react_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        react_result = react_agent.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config={"configurable": {"thread_id": "react_comparison"}}
        )
        
        print(f"\n✅ ReAct Response:\n{react_result['messages'][-1].content[:200]}...\n")
        
    except Exception as e:
        print(f"❌ ReAct Error: {e}")
    
    # Create DeepAgent
    print("\n2️⃣  Testing with DeepAgent...")
    deep_config = AgentConfig(
        name="deep_agent",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="""You are a software architecture expert with advanced organization.
        
Use your filesystem to:
1. Store architecture patterns in /patterns.md
2. Organize examples in /examples.md
3. Create a final summary

Be thorough and well-organized.""",
        description="DeepAgent with filesystem",
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
    
    try:
        deep_agent, _ = await build_agent(
            agent_cfg=deep_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        deep_result = deep_agent.invoke(
            {"messages": [{"role": "user", "content": test_query}]},
            config={"configurable": {"thread_id": "deep_comparison"}}
        )
        
        print(f"\n✅ DeepAgent Response:\n{deep_result['messages'][-1].content[:200]}...\n")
        
    except Exception as e:
        print(f"❌ DeepAgent Error: {e}")
    
    print("\n📊 Comparison Summary:")
    print("  • ReAct: Fast, direct response, single-loop reasoning")
    print("  • DeepAgent: Structured, organized with files, planning-based")
    print("  • Use ReAct for: Quick Q&A, simple tool calls")
    print("  • Use DeepAgent for: Research, complex reasoning, context management")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepAgents Integration Examples")
    parser.add_argument(
        "--mode",
        choices=["basic", "advanced", "comparison", "all"],
        default="basic",
        help="Example mode to run"
    )
    
    args = parser.parse_args()
    
    print("\n🧠 DeepAgents Integration Examples")
    print("==================================")
    
    if args.mode == "basic" or args.mode == "all":
        await example_basic_deep_agent()
    
    if args.mode == "advanced" or args.mode == "all":
        await example_advanced_deep_agent()
    
    if args.mode == "comparison" or args.mode == "all":
        await example_comparison()
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
