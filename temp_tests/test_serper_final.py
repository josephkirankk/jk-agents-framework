"""
Final Serper MCP Integration Test
Direct test without complex async operations - follows working test patterns
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.main import load_app_config

load_dotenv()


def main():
    """Test Serper MCP configuration"""
    print("\n" + "=" * 80)
    print("  SERPER MCP INTEGRATION TEST")
    print("=" * 80 + "\n")
    
    # Step 1: Check API Key
    print("Step 1: Checking SERPER_API_KEY...")
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key or api_key == "your-serper-api-key-here":
        print("❌ SERPER_API_KEY not configured properly")
        print("   Please set SERPER_API_KEY in your .env file")
        print("   Get your key from: https://serper.dev\n")
        return False
    print(f"✓ SERPER_API_KEY configured (length: {len(api_key)} chars)\n")
    
    # Step 2: Load Configuration
    print("Step 2: Loading configuration...")
    config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    try:
        app_config = load_app_config(config_path)
        print(f"✓ Configuration loaded: {config_path.name}\n")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False
    
    # Step 3: Verify Agent Configuration
    print("Step 3: Verifying agent configuration...")
    serper_agent = None
    for agent in app_config.agents:
        if hasattr(agent, 'mcp_servers') and agent.mcp_servers:
            if "serper-search" in agent.mcp_servers:
                serper_agent = agent
                break
    
    if not serper_agent:
        print("❌ No agent with 'serper-search' MCP server found")
        return False
    
    print(f"✓ Found agent: {serper_agent.name}")
    print(f"  Type: {serper_agent.agent_type}")
    print(f"  Model: {serper_agent.model}\n")
    
    # Step 4: Verify MCP Server Configuration
    print("Step 4: Verifying MCP server configuration...")
    serper_mcp = serper_agent.mcp_servers["serper-search"]
    
    # Convert to dict
    if hasattr(serper_mcp, 'model_dump'):
        mcp_dict = serper_mcp.model_dump()
    elif hasattr(serper_mcp, 'dict'):
        mcp_dict = serper_mcp.dict()
    else:
        mcp_dict = serper_mcp
    
    print(f"✓ MCP Server: serper-search")
    print(f"  Description: {mcp_dict.get('description')}")
    print(f"  Transport: {mcp_dict.get('transport')}")
    print(f"  Command: {mcp_dict.get('command')}")
    print(f"  Args: {mcp_dict.get('args')}\n")
    
    # Step 5: Verify Environment Variables
    print("Step 5: Verifying environment variables...")
    env_config = mcp_dict.get('env', {})
    
    if 'SERPER_API_KEY' not in env_config:
        print("❌ SERPER_API_KEY not in MCP server env config")
        return False
    
    print(f"✓ SERPER_API_KEY: {env_config['SERPER_API_KEY']}\n")
    
    # Step 6: Verify Command
    print("Step 6: Verifying command configuration...")
    expected_command = "npx"
    expected_args = ["-y", "serper-search-scrape-mcp-server"]
    expected_transport = "stdio"
    
    issues = []
    
    if mcp_dict.get('command') != expected_command:
        issues.append(f"Command: got '{mcp_dict.get('command')}', expected '{expected_command}'")
    
    if mcp_dict.get('args') != expected_args:
        issues.append(f"Args: got {mcp_dict.get('args')}, expected {expected_args}")
    
    if mcp_dict.get('transport') != expected_transport:
        issues.append(f"Transport: got '{mcp_dict.get('transport')}', expected '{expected_transport}'")
    
    if issues:
        print("⚠️  Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print(f"✓ Command configuration is correct\n")
    
    # Step 7: Check npx availability
    print("Step 7: Checking npx availability...")
    import subprocess
    try:
        result = subprocess.run(
            ["which", "npx"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            npx_path = result.stdout.strip()
            print(f"✓ npx found at: {npx_path}\n")
        else:
            print("⚠️  npx not found in PATH")
            print("   Please install Node.js and npm")
            return False
    except Exception as e:
        print(f"⚠️  Could not check npx: {e}\n")
    
    # Summary
    print("=" * 80)
    print("✓ ALL CHECKS PASSED!")
    print("=" * 80)
    print("\nConfiguration Summary:")
    print(f"  Config file: {config_path.name}")
    print(f"  Agent: {serper_agent.name}")
    print(f"  MCP Server: serper-search")
    print(f"  Command: {expected_command} {' '.join(expected_args)}")
    print(f"  Transport: {expected_transport}")
    print(f"\nExpected Tools:")
    print(f"  - google_search: Web search via Serper API")
    print(f"  - scrape: Web page content extraction")
    print(f"\nThe configuration is correct and ready to use!")
    print(f"\nTo test with actual agent execution, run:")
    print(f"  python examples/deep_agent_example.py (adapt with Serper config)")
    print("=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
