"""
Test 01: ADO MCP Connection Verification
Quick test to verify MCP server starts and receives PAT token correctly.
"""
import os
import pytest
import asyncio
from pathlib import Path

from app.main import load_app_config
from app.mcp_loader import load_mcp_tools, close_mcp_client


@pytest.mark.integration
@pytest.mark.azure
class TestADOMCPConnection:
    """Test ADO MCP server connection and authentication."""
    
    def test_pat_token_in_environment(self):
        """
        Verify PAT token is available in environment before MCP server starts.
        """
        pat_token = os.getenv("AZURE_DEVOPS_EXT_PAT")
        
        print("\n=== PAT Token Verification ===")
        print(f"Token set: {bool(pat_token)}")
        if pat_token:
            print(f"Token length: {len(pat_token)} chars")
            print(f"Token preview: {pat_token[:20]}...")
        
        assert pat_token, "AZURE_DEVOPS_EXT_PAT not set in environment"
        assert len(pat_token) > 50, "PAT token seems too short"
    
    @pytest.mark.asyncio
    async def test_mcp_server_config_loading(self, config_dir):
        """
        Test that MCP server configuration loads correctly.
        """
        config_path = config_dir / "ado_working_v1.yaml"
        
        if not config_path.exists():
            pytest.skip("ADO configuration not found")
        
        print("\n=== Loading ADO Configuration ===")
        config = load_app_config(config_path)
        
        # Find ADO agent
        ado_agent = None
        for agent in config.agents:
            if "azure_devops" in agent.name.lower() or "feature_analyzer" in agent.name.lower():
                ado_agent = agent
                break
        
        assert ado_agent, "ADO agent not found in configuration"
        print(f"✓ ADO agent found: {ado_agent.name}")
        
        # Check MCP servers configured
        assert ado_agent.mcp_servers, "No MCP servers configured for ADO agent"
        print(f"✓ MCP servers configured: {list(ado_agent.mcp_servers.keys())}")
        
        # Check azure_devops server
        assert "azure_devops" in ado_agent.mcp_servers, "azure_devops MCP server not configured"
        
        ado_mcp = ado_agent.mcp_servers["azure_devops"]
        print(f"✓ ADO MCP server config:")
        print(f"  Command: {ado_mcp.get('command')}")
        print(f"  Transport: {ado_mcp.get('transport')}")
        print(f"  Env vars: {list(ado_mcp.get('env', {}).keys())}")
        
        # Check PAT token in config
        env_config = ado_mcp.get('env', {})
        pat_in_config = env_config.get('AZURE_DEVOPS_EXT_PAT', '')
        print(f"  PAT in config: {pat_in_config}")
        
        assert 'AZURE_DEVOPS_EXT_PAT' in env_config, "PAT token not in MCP config"
    
    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self, config_dir):
        """
        Test that MCP server initializes without hanging.
        This is a quick test with 10-second timeout.
        """
        config_path = config_dir / "ado_working_v1.yaml"
        
        if not config_path.exists():
            pytest.skip("ADO configuration not found")
        
        # Check PAT token first
        pat_token = os.getenv("AZURE_DEVOPS_EXT_PAT")
        if not pat_token:
            pytest.skip("AZURE_DEVOPS_EXT_PAT not set")
        
        print("\n=== Initializing MCP Server (10s timeout) ===")
        config = load_app_config(config_path)
        
        # Find ADO agent
        ado_agent = None
        for agent in config.agents:
            if "azure_devops" in agent.name.lower() or "feature_analyzer" in agent.name.lower():
                ado_agent = agent
                break
        
        if not ado_agent or not ado_agent.mcp_servers:
            pytest.skip("ADO agent or MCP servers not configured")
        
        try:
            # Try to load MCP tools with timeout
            print("Starting MCP server...")
            mcp_client, tools = await asyncio.wait_for(
                load_mcp_tools(ado_agent.mcp_servers),
                timeout=10.0
            )
            
            print(f"✓ MCP server started successfully")
            print(f"✓ Loaded {len(tools)} tools")
            
            # Print first few tool names
            if tools:
                print(f"✓ Sample tools: {[t.name for t in tools[:5]]}")
            
            # Cleanup
            if mcp_client:
                await close_mcp_client(mcp_client)
                print("✓ MCP client closed")
            
        except asyncio.TimeoutError:
            pytest.fail("MCP server initialization timed out after 10 seconds - likely authentication issue!")
        except Exception as e:
            pytest.fail(f"MCP server initialization failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
