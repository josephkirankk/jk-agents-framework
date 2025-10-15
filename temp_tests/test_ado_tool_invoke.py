#!/usr/bin/env python3
"""
Test actual ADO tool invocation to see if authentication works.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from app.main import load_app_config
from app.mcp_loader import load_mcp_tools, close_mcp_client


async def test_ado_tool_invocation():
    """Test actual tool invocation."""
    
    # Check PAT token
    pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if not pat:
        print("❌ AZURE_DEVOPS_EXT_PAT not set")
        return False
    
    print(f"✓ PAT token loaded (length: {len(pat)})")
    
    # Load config
    config_path = project_root / "config" / "ado_working_v1.yaml"
    config = load_app_config(config_path)
    
    # Find ADO agent
    ado_agent = None
    for agent in config.agents:
        if "azure_devops" in agent.name.lower() or "feature_analyzer" in agent.name.lower():
            ado_agent = agent
            break
    
    if not ado_agent or not ado_agent.mcp_servers:
        print("❌ ADO agent or MCP servers not configured")
        return False
    
    print(f"✓ Found agent: {ado_agent.name}")
    
    try:
        # Load MCP tools
        print("\nLoading MCP tools...")
        mcp_client, tools = await load_mcp_tools(ado_agent.mcp_servers)
        
        print(f"✓ Loaded {len(tools)} tools")
        
        # Find a simple read-only tool to test
        test_tool = None
        for tool in tools:
            if tool.name == 'core_list_projects':
                test_tool = tool
                break
        
        if not test_tool:
            print("⚠ core_list_projects tool not found, trying any tool")
            test_tool = tools[0] if tools else None
        
        if not test_tool:
            print("❌ No tools available to test")
            if mcp_client:
                await close_mcp_client(mcp_client)
            return False
        
        print(f"\n✓ Testing tool: {test_tool.name}")
        print(f"  Description: {test_tool.description[:100] if hasattr(test_tool, 'description') else 'N/A'}")
        
        # Invoke the tool
        print("\nInvoking tool...")
        try:
            result = await test_tool.arun({})
            print(f"✓ Tool invocation succeeded!")
            print(f"\nResult preview (first 500 chars):")
            print("-" * 60)
            result_str = str(result)
            print(result_str[:500])
            if len(result_str) > 500:
                print("...")
            print("-" * 60)
            
            # Check for authentication errors in result
            if any(keyword in result_str.lower() for keyword in ['authentication', 'unauthorized', 'login', 'credentials']):
                print("\n⚠ Warning: Result contains authentication-related keywords")
                print("This might indicate the PAT token is not working properly")
                return False
            else:
                print("\n✅ SUCCESS: Tool invocation worked, no authentication errors!")
                return True
                
        except Exception as e:
            error_str = str(e)
            print(f"❌ Tool invocation failed: {e}")
            
            # Check error type
            if any(keyword in error_str.lower() for keyword in ['authentication', 'unauthorized', '401', 'forbidden', '403']):
                print("\n❌ AUTHENTICATION ERROR DETECTED!")
                print("The PAT token is not working with Azure DevOps API")
                print("\nPossible causes:")
                print("  1. PAT token has expired")
                print("  2. PAT token doesn't have required permissions")
                print("  3. PAT token format is incorrect")
                print("  4. Azure DevOps organization name is incorrect")
            
            return False
        
    finally:
        # Cleanup
        if mcp_client:
            await close_mcp_client(mcp_client)
            print("\n✓ MCP client closed")


async def main():
    print("="*60)
    print("ADO Tool Invocation Test")
    print("="*60)
    print("\nThis test will invoke an actual ADO tool to verify")
    print("that authentication works end-to-end.\n")
    
    result = await test_ado_tool_invocation()
    
    print("\n" + "="*60)
    if result:
        print("✅ SUCCESS: ADO tool invocation works with PAT token!")
    else:
        print("❌ FAILURE: ADO tool invocation failed")
        print("\nNext steps:")
        print("  1. Verify PAT token is valid and not expired")
        print("  2. Check PAT token has required permissions")
        print("  3. Verify organization name is correct (PepsiCoIT)")
    print("="*60)
    
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
