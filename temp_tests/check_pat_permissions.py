#!/usr/bin/env python3
"""
Check Azure DevOps PAT token permissions and provide guidance.
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


REQUIRED_PERMISSIONS = {
    "Project and Team (Read)": {
        "tool": "core_list_projects",
        "critical": True,
        "description": "List projects in the organization"
    },
    "Work Items (Read)": {
        "tool": "wit_list_work_items",
        "critical": True,
        "description": "Query and view work items"
    },
    "Code (Read)": {
        "tool": "repo_list_repositories",
        "critical": True,
        "description": "View repositories and code"
    },
}


async def check_pat_token():
    """Check PAT token and its permissions."""
    
    print("="*70)
    print("Azure DevOps PAT Token Permission Checker")
    print("="*70)
    print()
    
    # Check if PAT exists
    pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if not pat:
        print("❌ ERROR: AZURE_DEVOPS_EXT_PAT not found in environment")
        print()
        print("Please add your PAT token to .env file:")
        print("  AZURE_DEVOPS_EXT_PAT=your-token-here")
        print()
        print("To generate a PAT token:")
        print("  1. Go to: https://dev.azure.com/PepsiCoIT/_usersSettings/tokens")
        print("  2. Click 'New Token'")
        print("  3. Select required scopes (see README)")
        print("  4. Copy token and add to .env")
        return False
    
    # Check token format
    print(f"✓ PAT token found")
    print(f"  Length: {len(pat)} characters")
    print(f"  Preview: {pat[:20]}...")
    
    if len(pat) < 50:
        print()
        print("⚠️  WARNING: Token seems too short (expected 52+ characters)")
        print("   This might be a placeholder or invalid token.")
        print()
    
    # Check if it's a placeholder
    if pat.lower() in ['your-azure-devops-pat-token-here', 'your-pat-here', 'xx', 'xxx', 'placeholder']:
        print()
        print("❌ ERROR: PAT token is a placeholder")
        print("   Please replace with actual token from Azure DevOps")
        return False
    
    print()
    print("Loading MCP server and tools...")
    print()
    
    # Load config and tools
    try:
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
        
        # Load MCP tools
        mcp_client, tools = await load_mcp_tools(ado_agent.mcp_servers)
        print(f"✓ MCP server started successfully")
        print(f"✓ Loaded {len(tools)} tools")
        print()
        
        # Test each permission
        print("="*70)
        print("Testing PAT Token Permissions")
        print("="*70)
        print()
        
        results = {}
        
        for permission_name, info in REQUIRED_PERMISSIONS.items():
            tool_name = info["tool"]
            critical = info["critical"]
            description = info["description"]
            
            # Find tool
            tool = None
            for t in tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                print(f"⚠️  {permission_name}")
                print(f"   Tool '{tool_name}' not found (may not be available in this version)")
                print()
                results[permission_name] = "unknown"
                continue
            
            # Test tool
            print(f"Testing: {permission_name}")
            print(f"  Tool: {tool_name}")
            print(f"  Purpose: {description}")
            
            try:
                result = await tool.arun({})
                result_str = str(result)
                
                # Check for errors
                if "TF400813" in result_str or "not authorized" in result_str.lower():
                    print(f"  ❌ FAILED: Permission denied")
                    print(f"     Error: User not authorized to access this resource")
                    results[permission_name] = False
                elif "error" in result_str.lower() and "authentication" in result_str.lower():
                    print(f"  ❌ FAILED: Authentication error")
                    results[permission_name] = False
                else:
                    print(f"  ✅ PASSED: Permission granted")
                    results[permission_name] = True
                    
            except Exception as e:
                error_str = str(e)
                if "TF400813" in error_str or "not authorized" in error_str.lower():
                    print(f"  ❌ FAILED: Permission denied")
                    print(f"     Error: {error_str[:100]}")
                    results[permission_name] = False
                elif "authentication" in error_str.lower():
                    print(f"  ❌ FAILED: Authentication error")
                    print(f"     Error: {error_str[:100]}")
                    results[permission_name] = False
                else:
                    print(f"  ⚠️  ERROR: {error_str[:100]}")
                    results[permission_name] = "error"
            
            print()
        
        # Cleanup
        if mcp_client:
            await close_mcp_client(mcp_client)
        
        # Summary
        print("="*70)
        print("Summary")
        print("="*70)
        print()
        
        passed = sum(1 for v in results.values() if v is True)
        failed = sum(1 for v in results.values() if v is False)
        unknown = sum(1 for v in results.values() if v in ["unknown", "error"])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Unknown: {unknown}")
        print()
        
        if failed > 0:
            print("="*70)
            print("❌ PAT TOKEN PERMISSIONS INSUFFICIENT")
            print("="*70)
            print()
            print("Your PAT token is missing required permissions.")
            print()
            print("To fix this:")
            print("  1. Go to: https://dev.azure.com/PepsiCoIT/_usersSettings/tokens")
            print("  2. Find your token or create a new one")
            print("  3. Ensure these scopes are selected (READ permission):")
            print()
            for perm, info in REQUIRED_PERMISSIONS.items():
                if results.get(perm) is False:
                    status = "❌ MISSING"
                else:
                    status = "✅ OK"
                print(f"     {status} {perm}")
            print()
            print("  4. Copy the token and update .env file:")
            print("     AZURE_DEVOPS_EXT_PAT=your-new-token-here")
            print()
            return False
        else:
            print("="*70)
            print("✅ PAT TOKEN PERMISSIONS VERIFIED")
            print("="*70)
            print()
            print("Your PAT token has all required permissions!")
            print("You can now run Azure DevOps integration tests.")
            print()
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(check_pat_token())
    sys.exit(0 if result else 1)
