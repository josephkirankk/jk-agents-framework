"""
DeepAgent Multi-Turn Research Example with Brave Search MCP

This comprehensive example demonstrates:
1. DeepAgent with real Brave Search MCP integration
2. Multi-turn conversation with context management
3. Virtual filesystem for organizing research findings
4. Subagents for specialized research tasks
5. Real-world research workflow

Requirements:
- Brave Search MCP server running on localhost:8080
- BRAVE_API_KEY environment variable set
- OpenAI API key configured

Usage:
    # Basic research
    python examples/deep_agent_brave_search_example.py --query "What is quantum computing?"
    
    # Multi-turn research
    python examples/deep_agent_brave_search_example.py --mode multiturn
    
    # With subagents
    python examples/deep_agent_brave_search_example.py --mode advanced
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agent_builder import build_agent
from app.config import (
    AgentConfig, 
    DeepAgentConfig, 
    SubAgentConfig,
    MCPServerConfig
)
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


def check_prerequisites():
    """Check if all prerequisites are met."""
    issues = []
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        issues.append("❌ No OpenAI or Azure OpenAI API key found")
    
    # Check for Brave API key
    if not os.getenv("BRAVE_API_KEY"):
        issues.append("⚠️  BRAVE_API_KEY not set (MCP server needs this)")
    
    if issues:
        print("\n⚠️  Prerequisites Check:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 To fix:")
        print("  1. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY in .env")
        print("  2. Set BRAVE_API_KEY in .env")
        print("  3. Ensure Brave Search MCP server is running on localhost:8080")
        return False
    
    print("✅ Prerequisites check passed")
    return True


async def create_deep_research_agent(use_subagents: bool = False) -> tuple:
    """
    Create a DeepAgent configured for research with Brave Search.
    
    Args:
        use_subagents: Whether to include specialized subagents
        
    Returns:
        Tuple of (agent, mcp_client)
    """
    print("\n🔧 Building DeepAgent with Brave Search integration...")
    
    # Configure MCP server for Brave Search
    mcp_servers = {
        "brave_search": MCPServerConfig(
            description="Brave Search MCP server for web research",
            transport="streamable_http",
            url="http://localhost:8080/mcp",
            env={},
            headers={"Content-Type": "application/json"}
        )
    }
    
    # Configure subagents if requested
    subagents = []
    if use_subagents:
        subagents = [
            SubAgentConfig(
                name="fact-checker",
                description="Verifies factual claims through additional searches",
                system_prompt="""You are a fact-checking specialist.
                
Your task is to verify specific claims by:
1. Conducting targeted searches for each claim
2. Cross-referencing multiple sources
3. Assessing source credibility
4. Providing confidence scores

Store your verification results in /fact_checks.md""",
                model="openai:gpt-4o-mini",
                tools=[],
            ),
            SubAgentConfig(
                name="synthesizer",
                description="Creates structured, well-cited final reports",
                system_prompt="""You are a research synthesis specialist.

Your task is to:
1. Read all research files from the filesystem
2. Organize findings by theme
3. Create a comprehensive, well-structured report
4. Include proper citations and sources

Store your synthesis in /final_report.md""",
                model="openai:gpt-4o",
                tools=[],
            ),
        ]
    
    # Create agent configuration
    agent_config = AgentConfig(
        name="research_agent",
        agent_type="deep",
        model=os.getenv("OPENAI_MODEL", "openai:gpt-4o-mini"),
        prompt=f"""You are an advanced research agent with the following capabilities:

**AVAILABLE TOOLS:**
- Brave Search API (via MCP) - for web research
- Virtual filesystem - for organizing findings
- Task planning - for systematic research

**RESEARCH METHODOLOGY:**

1. **Planning Phase:**
   - Break down the research question into subtopics
   - Create a research plan in your todo list
   - Identify what information you need

2. **Research Phase:**
   - Conduct systematic searches using Brave Search
   - Store findings in organized files:
     * /research_notes.md - raw findings
     * /sources.md - source citations
     * /analysis.md - your analysis
   
3. **Analysis Phase:**
   - Cross-reference information
   - Assess source credibility
   - Identify gaps or contradictions
   
4. **Synthesis Phase:**
   - Create a comprehensive answer
   - Include proper citations
   - Note confidence levels

{"**SUBAGENTS AVAILABLE:**" if use_subagents else ""}
{'''- fact-checker: Delegate specific claims for verification
- synthesizer: Delegate final report creation''' if use_subagents else ""}

**IMPORTANT:**
- Always use the filesystem to store information
- Create separate files for different types of information
- Use Brave Search extensively for research
- Provide well-cited, comprehensive answers""",
        description="Research agent with Brave Search and filesystem capabilities",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            enable_longterm_memory=False,
            subagents=subagents,
        ),
        mcp_servers=mcp_servers,
        http_tools={},
        python_tools={},
    )
    
    try:
        checkpointer = get_global_checkpointer()
        agent, mcp_client = await build_agent(
            agent_cfg=agent_config,
            default_model="openai:gpt-4o-mini",
            checkpointer=checkpointer,
        )
        
        print(f"✅ DeepAgent created successfully!")
        print(f"   - Filesystem: ✓")
        print(f"   - TodoList: ✓")
        print(f"   - Brave Search MCP: ✓")
        print(f"   - Subagents: {len(subagents)}")
        
        return agent, mcp_client
        
    except Exception as e:
        log.error(f"Failed to create agent: {e}", exc_info=True)
        raise


async def single_research_query(query: str):
    """Execute a single research query."""
    print(f"\n{'='*70}")
    print(f"🔍 SINGLE QUERY RESEARCH")
    print(f"{'='*70}")
    print(f"\n📝 Query: {query}\n")
    
    agent, mcp_client = await create_deep_research_agent(use_subagents=False)
    
    thread_id = f"research_{hash(query) % 10000}"
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        print("🤖 Agent researching...\n")
        
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config
        )
        
        # Extract response
        final_message = result["messages"][-1]
        print(f"✅ RESEARCH COMPLETE\n")
        print(f"{'='*70}")
        print(final_message.content)
        print(f"{'='*70}")
        
        # Show filesystem if available
        if "files" in result:
            print(f"\n📁 Files created: {list(result['files'].keys())}")
        
        return result
        
    except Exception as e:
        log.error(f"Research failed: {e}", exc_info=True)
        print(f"\n❌ Research failed: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass


async def multiturn_research():
    """Execute a multi-turn research conversation."""
    print(f"\n{'='*70}")
    print(f"🔄 MULTI-TURN RESEARCH CONVERSATION")
    print(f"{'='*70}\n")
    
    agent, mcp_client = await create_deep_research_agent(use_subagents=False)
    
    thread_id = "multiturn_research_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Define research conversation
    conversation = [
        "What is quantum computing and how does it work?",
        "What are the main challenges in building practical quantum computers?",
        "Which companies are leading in quantum computing development?",
        "Based on what you've researched, when might quantum computers become mainstream?",
    ]
    
    try:
        for turn, query in enumerate(conversation, 1):
            print(f"\n{'─'*70}")
            print(f"Turn {turn}/{len(conversation)}")
            print(f"{'─'*70}")
            print(f"\n👤 User: {query}\n")
            print("🤖 Agent thinking...\n")
            
            result = agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config=config
            )
            
            # Extract response
            final_message = result["messages"][-1]
            response = final_message.content
            
            # Truncate for display
            if len(response) > 500:
                display_response = response[:500] + "...\n[Response truncated for display]"
            else:
                display_response = response
            
            print(f"🤖 Agent: {display_response}\n")
            
            # Small pause between turns
            if turn < len(conversation):
                await asyncio.sleep(1)
        
        print(f"\n{'='*70}")
        print("✅ MULTI-TURN CONVERSATION COMPLETE")
        print(f"{'='*70}")
        print(f"\nCompleted {len(conversation)} research turns with maintained context")
        
        # Show final state
        if hasattr(agent, 'get_state'):
            try:
                state = agent.get_state(config)
                print(f"\n📊 Conversation Statistics:")
                print(f"   - Total messages: {len(result['messages'])}")
                print(f"   - Thread ID: {thread_id}")
            except:
                pass
        
        return result
        
    except Exception as e:
        log.error(f"Multi-turn research failed: {e}", exc_info=True)
        print(f"\n❌ Multi-turn research failed: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass


async def advanced_research_with_subagents():
    """Execute advanced research with subagent delegation."""
    print(f"\n{'='*70}")
    print(f"🚀 ADVANCED RESEARCH WITH SUBAGENTS")
    print(f"{'='*70}\n")
    
    agent, mcp_client = await create_deep_research_agent(use_subagents=True)
    
    thread_id = "advanced_research_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    query = """Research the current state of artificial general intelligence (AGI).

I need:
1. A comprehensive overview of AGI development
2. Key claims fact-checked across multiple sources
3. A well-structured final report with citations

Please use your subagents:
- Use fact-checker to verify major claims
- Use synthesizer to create the final report"""
    
    try:
        print(f"📝 Complex Query: {query}\n")
        print("🤖 Main agent orchestrating research with subagents...\n")
        print("⏳ This may take longer as subagents are spawned...\n")
        
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config
        )
        
        # Extract response
        final_message = result["messages"][-1]
        print(f"\n✅ ADVANCED RESEARCH COMPLETE\n")
        print(f"{'='*70}")
        print(final_message.content)
        print(f"{'='*70}")
        
        # Show execution details
        print(f"\n📊 Execution Details:")
        print(f"   - Total messages: {len(result['messages'])}")
        print(f"   - Subagents used: fact-checker, synthesizer")
        
        if "files" in result:
            print(f"   - Files created: {list(result['files'].keys())}")
        
        return result
        
    except Exception as e:
        log.error(f"Advanced research failed: {e}", exc_info=True)
        print(f"\n❌ Advanced research failed: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass


async def interactive_research():
    """Interactive research session."""
    print(f"\n{'='*70}")
    print(f"💬 INTERACTIVE RESEARCH SESSION")
    print(f"{'='*70}")
    print("\nType your research questions. Commands:")
    print("  'quit' - Exit")
    print("  'files' - Show files created")
    print("  'state' - Show conversation state\n")
    
    agent, mcp_client = await create_deep_research_agent(use_subagents=True)
    
    thread_id = "interactive_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    turn = 0
    
    try:
        while True:
            turn += 1
            query = input(f"\n[Turn {turn}] You: ").strip()
            
            if not query:
                continue
            
            if query.lower() == 'quit':
                print("\n👋 Ending research session...")
                break
            
            if query.lower() == 'files':
                print("\n📁 Requesting file list from agent...")
                query = "List all files you've created in the filesystem"
            
            if query.lower() == 'state':
                if hasattr(agent, 'get_state'):
                    try:
                        state = agent.get_state(config)
                        print(f"\n📊 Session State:")
                        print(f"   - Thread ID: {thread_id}")
                        print(f"   - Turn: {turn}")
                    except:
                        print("   State info not available")
                continue
            
            print("\n🤖 Researching...\n")
            
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config=config
                )
                
                final_message = result["messages"][-1]
                print(f"Agent: {final_message.content}\n")
                
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                log.error(f"Query failed: {e}")
        
        print(f"\n✅ Interactive session completed ({turn-1} turns)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user")
    finally:
        if mcp_client:
            try:
                await mcp_client.__aexit__(None, None, None)
            except:
                pass


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DeepAgent Multi-Turn Research with Brave Search"
    )
    parser.add_argument(
        "--mode",
        choices=["single", "multiturn", "advanced", "interactive"],
        default="single",
        help="Execution mode"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What are the latest developments in AI agents?",
        help="Research query (for single mode)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🧠 DeepAgent Multi-Turn Research Example")
    print("   with Brave Search MCP Integration")
    print("="*70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠️  Please fix prerequisites and try again")
        return 1
    
    try:
        if args.mode == "single":
            await single_research_query(args.query)
        
        elif args.mode == "multiturn":
            await multiturn_research()
        
        elif args.mode == "advanced":
            await advanced_research_with_subagents()
        
        elif args.mode == "interactive":
            await interactive_research()
        
        print("\n✅ Example completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        log.error(f"Example failed: {e}", exc_info=True)
        print(f"\n❌ Example failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
