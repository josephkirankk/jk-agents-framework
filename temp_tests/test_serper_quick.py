"""
Quick Serper MCP Configuration Test
Verifies the configuration is correct without full agent execution.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.main import load_app_config

load_dotenv()


def check_serper_config():
    """Check Serper MCP configuration"""
    print("\n" + "=" * 80)
    print("  SERPER MCP CONFIGURATION CHECK")
    print("=" * 80 + "\n")
    
    # Check API key
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key or api_key == "your-serper-api-key-here":
        print("❌ SERPER_API_KEY not configured in .env file")
        print("   Please add: SERPER_API_KEY=your-actual-key")
        return False
    
    print(f"✓ SERPER_API_KEY configured (length: {len(api_key)} chars)")
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    print(f"✓ Config file found: {config_path.name}")
    
    try:
        app_config = load_app_config(config_path)
        print(f"✓ Configuration loaded successfully")
        
        # Find agent with Serper MCP
        serper_agent = None
        for agent in app_config.agents:
            if hasattr(agent, 'mcp_servers') and agent.mcp_servers and "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
        
        if not serper_agent:
            print("❌ No agent with 'serper-search' MCP server found")
            return False
        
        print(f"✓ Found agent: {serper_agent.name}")
        print(f"  Agent type: {serper_agent.agent_type}")
        
        # Check MCP server config
        serper_mcp = serper_agent.mcp_servers["serper-search"]
        
        # Convert to dict
        if hasattr(serper_mcp, 'model_dump'):
            mcp_dict = serper_mcp.model_dump()
        elif hasattr(serper_mcp, 'dict'):
            mcp_dict = serper_mcp.dict()
        else:
            mcp_dict = serper_mcp
        
        print(f"\n✓ MCP Server Configuration:")
        print(f"  Command: {mcp_dict.get('command')}")
        print(f"  Transport: {mcp_dict.get('transport')}")
        print(f"  Args: {mcp_dict.get('args')}")
        print(f"  Description: {mcp_dict.get('description')}")
        
        # Check environment variables
        env_config = mcp_dict.get('env', {})
        if 'SERPER_API_KEY' not in env_config:
            print("❌ SERPER_API_KEY not in MCP server env config")
            return False
        
        print(f"  Env vars: SERPER_API_KEY = {env_config['SERPER_API_KEY']}")
        
        # Verify command and args
        expected_command = "npx"
        expected_args = ["-y", "serper-search-scrape-mcp-server"]
        
        if mcp_dict.get('command') != expected_command:
            print(f"⚠️  Warning: Command is '{mcp_dict.get('command')}', expected '{expected_command}'")
        
        if mcp_dict.get('args') != expected_args:
            print(f"⚠️  Warning: Args are {mcp_dict.get('args')}, expected {expected_args}")
        
        print(f"\n✓ Configuration is correct!")
        print(f"\nExpected tools from this MCP server:")
        print(f"  - google_search: Perform web searches via Serper API")
        print(f"  - scrape: Extract content from web pages")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = check_serper_config()
    print("\n" + "=" * 80)
    if success:
        print("✓ Configuration check passed!")
    else:
        print("✗ Configuration check failed!")
    print("=" * 80 + "\n")
    sys.exit(0 if success else 1)
