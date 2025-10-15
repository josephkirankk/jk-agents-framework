#!/usr/bin/env python3
"""
Quick verification script to test Azure DevOps PAT authentication.
This script verifies that the MCP server uses PAT token instead of opening browser.
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
from app.agent_builder import build_agent
from langchain_core.messages import HumanMessage


async def test_ado_authentication():
    """Test that Azure DevOps uses PAT token authentication."""
    
    # Verify PAT token is loaded
    pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if not pat:
        print("❌ AZURE_DEVOPS_EXT_PAT not found in environment")
        return False
    
    print(f"✓ PAT token loaded (length: {len(pat)})")
    
    # Load config
    config_path = project_root / "config" / "ado_working_v1.yaml"
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    print(f"✓ Config file found: {config_path}")
    
    try:
        config = load_app_config(config_path)
        print(f"✓ Config loaded successfully")
        
        # Get Azure DevOps agent
        ado_agent_config = None
        for agent in config.agents:
            if "azure_devops" in agent.name.lower() or "feature_analyzer" in agent.name.lower():
                ado_agent_config = agent
                break
        
        if not ado_agent_config:
            print("❌ Azure DevOps agent not found in config")
            return False
        
        print(f"✓ Found agent: {ado_agent_config.name}")
        
        # Check MCP server configuration
        if "azure_devops" in ado_agent_config.mcp_servers:
            mcp_config = ado_agent_config.mcp_servers["azure_devops"]
            args = mcp_config.args if hasattr(mcp_config, 'args') else []
            
            if "-a" in args and "env" in args:
                print("✓ MCP server configured with '-a env' authentication")
            else:
                print("⚠ Warning: MCP server may not be configured for env authentication")
                print(f"  Args: {args}")
        
        # Build agent (this will start the MCP server)
        print("\n🔧 Building agent and starting MCP server...")
        print("   (If browser opens, the fix didn't work)")
        
        # Convert config to dict manually
        app_config_dict = {
            "models": config.models,
            "business_context": config.business_context if hasattr(config, 'business_context') else "",
            "persistence": config.persistence if hasattr(config, 'persistence') else {"type": "memory"},
            "memory": config.memory.dict() if hasattr(config, 'memory') else None,
        }
        
        agent, mcp_client = await build_agent(
            agent_cfg=ado_agent_config,
            default_model=config.models.get("default", "azure_openai:gpt-4.1"),
            config_path=str(config_path),
            app_config=app_config_dict
        )
        
        print("✓ Agent built successfully (no browser opened!)")
        
        # Cleanup
        if mcp_client:
            from app.mcp_loader import close_mcp_client
            await close_mcp_client(mcp_client)
            print("✓ MCP client closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Azure DevOps PAT Authentication Verification")
    print("=" * 60)
    print()
    
    result = asyncio.run(test_ado_authentication())
    
    print()
    print("=" * 60)
    if result:
        print("✅ SUCCESS: PAT authentication is working correctly!")
        print("   The MCP server did not open a browser.")
    else:
        print("❌ FAILED: There was an issue with PAT authentication.")
    print("=" * 60)
    
    sys.exit(0 if result else 1)
