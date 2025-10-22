"""
DeepAgent Research Example with Serper Search MCP

This example demonstrates:
1. DeepAgent with Serper Search & Scrape MCP integration
2. Using google_search and scrape tools via MCP
3. Organizing research with virtual filesystem
4. Multi-turn conversations with context

Requirements:
- SERPER_API_KEY environment variable set
- Azure OpenAI or OpenAI API key configured
- Node.js with npx installed

Usage:
    # Simple search
    python examples/deep_agent_serper_example.py --query "Latest AI developments"
    
    # Interactive mode
    python examples/deep_agent_serper_example.py --mode interactive
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set tokenizer parallelism to false to avoid fork warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from app.main import load_app_config
from app.agent_builder import build_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging with file output
from app.logging_config import quick_setup, get_log_directory

# Configure logging (creates file in agentlogs/ directory)
log_file_path = quick_setup(verbose=False)
log = logging.getLogger(__name__)

# Show where logs are being written
log_dir = get_log_directory()
print(f"\n📋 Logs being written to: {log_file_path}")
print(f"📂 Log directory: {log_dir}\n")


def check_prerequisites():
    """Check if all prerequisites are met."""
    issues = []
    
    # Check for OpenAI/Azure API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"):
        issues.append("❌ No OpenAI or Azure OpenAI API key found")
    
    # Check for Serper API key
    serper_key = os.getenv("SERPER_API_KEY")
    if not serper_key or serper_key == "your-serper-api-key-here":
        issues.append("❌ SERPER_API_KEY not set properly")
    
    if issues:
        print("\n⚠️  Prerequisites Check Failed:")
        for issue in issues:
            print(f"  {issue}")
        print("\n💡 To fix:")
        print("  1. Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY in .env")
        print("  2. Set SERPER_API_KEY in .env (get from https://serper.dev)")
        return False
    
    print("✅ Prerequisites check passed")
    return True


async def create_serper_research_agent() -> tuple:
    """
    Create a DeepAgent configured with Serper Search MCP.
    
    Returns:
        Tuple of (agent, mcp_client)
    """
    print("\n🔧 Building DeepAgent with Serper Search integration...")
    
    # Load the pre-configured Serper config
    config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    app_config = load_app_config(config_path)
    
    # Find agent with Serper MCP
    serper_agent = None
    for agent in app_config.agents:
        if hasattr(agent, 'mcp_servers') and agent.mcp_servers:
            if "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
    
    if not serper_agent:
        raise ValueError("No agent with serper-search MCP server found in config")
    
    # Convert app_config to dict
    if hasattr(app_config, 'model_dump'):
        app_config_dict = app_config.model_dump()
    elif hasattr(app_config, 'dict'):
        app_config_dict = app_config.dict()
    else:
        app_config_dict = {}
    
    # Get default model
    default_model = app_config.models.get('default') if isinstance(app_config.models, dict) else app_config.models.default
    
    try:
        agent, mcp_client = await build_agent(
            agent_cfg=serper_agent,
            default_model=default_model,
            business_context="",
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print(f"✅ DeepAgent created successfully!")
        print(f"   - Agent: {serper_agent.name}")
        print(f"   - Type: {serper_agent.agent_type}")
        print(f"   - Filesystem: ✓")
        print(f"   - TodoList: ✓")
        print(f"   - Serper MCP: ✓")
        
        return agent, mcp_client
        
    except Exception as e:
        log.error(f"Failed to create agent: {e}", exc_info=True)
        raise


async def simple_search(query: str):
    """Execute a simple search query."""
    print(f"\n{'='*70}")
    print(f"🔍 SIMPLE SEARCH")
    print(f"{'='*70}")
    print(f"\n📝 Query: {query}\n")
    
    agent, mcp_client = await create_serper_research_agent()
    
    thread_id = f"search_{hash(query) % 10000}"
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        print("🤖 Agent searching...\n")
        
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config=config
        )
        
        # Extract response
        if isinstance(result, dict) and 'messages' in result:
            final_message = result["messages"][-1]
            response = final_message.content if hasattr(final_message, 'content') else str(final_message)
            
            print(f"✅ SEARCH COMPLETE\n")
            print(f"{'='*70}")
            print(response)
            print(f"{'='*70}")
        else:
            print(f"Unexpected response format: {type(result)}")
        
        return result
        
    except Exception as e:
        log.error(f"Search failed: {e}", exc_info=True)
        print(f"\n❌ Search failed: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass


async def research_with_scraping():
    """Demonstrate search + web scraping workflow."""
    print(f"\n{'='*70}")
    print(f"🔬 RESEARCH WITH WEB SCRAPING")
    print(f"{'='*70}\n")
    
    agent, mcp_client = await create_serper_research_agent()
    
    thread_id = "research_scraping_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    query = """Research the latest developments in quantum computing.
    
Please:
1. Search for recent articles about quantum computing
2. Scrape content from the top 2 most relevant articles
3. Summarize the key findings
4. Save your findings to /quantum_research.md"""
    
    try:
        print(f"📝 Query: {query}\n")
        print("🤖 Agent researching (this may take a moment)...\n")
        
        result = await agent.ainvoke(
            {"messages": [("user", query)]},
            config=config
        )
        
        # Extract response
        if isinstance(result, dict) and 'messages' in result:
            final_message = result["messages"][-1]
            response = final_message.content if hasattr(final_message, 'content') else str(final_message)
            
            print(f"\n✅ RESEARCH COMPLETE\n")
            print(f"{'='*70}")
            print(response)
            print(f"{'='*70}")
        
        return result
        
    except Exception as e:
        log.error(f"Research failed: {e}", exc_info=True)
        print(f"\n❌ Research failed: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass


async def multiturn_conversation():
    """Execute a multi-turn research conversation."""
    print(f"\n{'='*70}")
    print(f"🔄 MULTI-TURN RESEARCH CONVERSATION")
    print(f"{'='*70}\n")
    
    agent, mcp_client = await create_serper_research_agent()
    
    thread_id = "multiturn_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Define conversation
    conversation = [
        "Search for information about large language models",
        "What are the main challenges in training these models?",
        "Which companies are leading in LLM development?",
    ]
    
    try:
        for turn, query in enumerate(conversation, 1):
            print(f"\n{'─'*70}")
            print(f"Turn {turn}/{len(conversation)}")
            print(f"{'─'*70}")
            print(f"\n👤 User: {query}\n")
            print("🤖 Agent thinking...\n")
            
            result = await agent.ainvoke(
                {"messages": [("user", query)]},
                config=config
            )
            
            # Extract response
            if isinstance(result, dict) and 'messages' in result:
                final_message = result["messages"][-1]
                response = final_message.content if hasattr(final_message, 'content') else str(final_message)
                
                # Truncate for display
                if len(response) > 400:
                    display_response = response[:400] + "...\n[Response truncated]"
                else:
                    display_response = response
                
                print(f"🤖 Agent: {display_response}\n")
            
            # Small pause between turns
            if turn < len(conversation):
                await asyncio.sleep(1)
        
        print(f"\n{'='*70}")
        print("✅ MULTI-TURN CONVERSATION COMPLETE")
        print(f"{'='*70}")
        print(f"\nCompleted {len(conversation)} turns with maintained context")
        
        return result
        
    except Exception as e:
        log.error(f"Multi-turn conversation failed: {e}", exc_info=True)
        print(f"\n❌ Multi-turn conversation failed: {e}")
        raise
    finally:
        if mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass


async def interactive_mode():
    """Interactive research session."""
    print(f"\n{'='*70}")
    print(f"💬 INTERACTIVE RESEARCH MODE")
    print(f"{'='*70}")
    print("\nType your queries. Commands:")
    print("  'quit' or 'exit' - End session")
    print("  'help' - Show this help\n")
    
    agent, mcp_client = await create_serper_research_agent()
    
    thread_id = "interactive_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    turn = 0
    
    try:
        while True:
            turn += 1
            query = input(f"\n[Turn {turn}] You: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit']:
                print("\n👋 Ending session...")
                break
            
            if query.lower() == 'help':
                print("\nYou can ask the agent to:")
                print("  - Search the web: 'Search for X'")
                print("  - Scrape pages: 'Scrape content from URL'")
                print("  - Research topics: 'Research X and save to file'")
                continue
            
            print("\n🤖 Processing...\n")
            
            try:
                result = await agent.ainvoke(
                    {"messages": [("user", query)]},
                    config=config
                )
                
                if isinstance(result, dict) and 'messages' in result:
                    final_message = result["messages"][-1]
                    response = final_message.content if hasattr(final_message, 'content') else str(final_message)
                    print(f"Agent: {response}\n")
                
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                log.error(f"Query failed: {e}")
        
        print(f"\n✅ Interactive session completed ({turn-1} turns)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user")
    finally:
        if mcp_client:
            try:
                await mcp_client.cleanup()
            except:
                pass


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DeepAgent Research with Serper Search MCP"
    )
    parser.add_argument(
        "--mode",
        choices=["simple", "scrape", "multiturn", "interactive"],
        default="simple",
        help="Execution mode"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What are the latest developments in AI?",
        help="Search query (for simple mode)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🧠 DeepAgent with Serper Search MCP")
    print("="*70)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n⚠️  Please fix prerequisites and try again")
        return 1
    
    try:
        if args.mode == "simple":
            await simple_search(args.query)
        
        elif args.mode == "scrape":
            await research_with_scraping()
        
        elif args.mode == "multiturn":
            await multiturn_conversation()
        
        elif args.mode == "interactive":
            await interactive_mode()
        
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
