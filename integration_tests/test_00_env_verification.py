"""
Test 00: Environment Variable Verification
Verifies that .env file is loaded correctly and required variables are present.
This test runs first to validate environment setup.
"""
import os
import pytest
from pathlib import Path


class TestEnvironmentSetup:
    """Verify environment variables are loaded correctly."""
    
    def test_env_file_exists(self, test_root_dir):
        """
        Verify .env file exists in project root.
        """
        env_path = test_root_dir / ".env"
        assert env_path.exists(), f".env file not found at {env_path}"
        print(f"✓ .env file found at: {env_path}")
    
    def test_azure_openai_vars_loaded(self, env_config):
        """
        Verify Azure OpenAI environment variables are loaded.
        """
        azure_config = env_config["azure_openai"]
        
        print("\n=== Azure OpenAI Configuration ===")
        print(f"Endpoint: {azure_config['endpoint']}")
        print(f"API Key: {'✓ Set' if azure_config['api_key'] else '✗ Not set'}")
        print(f"Deployment: {azure_config['deployment']}")
        print(f"API Version: {azure_config['api_version']}")
        print(f"Available: {azure_config['available']}")
        
        assert azure_config["endpoint"], "AZURE_OPENAI_ENDPOINT not set"
        assert azure_config["api_key"], "AZURE_OPENAI_API_KEY not set"
        assert azure_config["available"], "Azure OpenAI not available"
    
    def test_azure_devops_pat_loaded(self, env_config):
        """
        Verify Azure DevOps PAT token is loaded.
        This is critical for ADO MCP tests to work without login prompts.
        """
        ado_config = env_config["azure_devops"]
        
        print("\n=== Azure DevOps Configuration ===")
        print(f"PAT Token: {'✓ Set' if ado_config['pat_token'] else '✗ Not set'}")
        print(f"Available: {ado_config['available']}")
        
        if ado_config['pat_token']:
            # Show first 20 chars of token for verification
            token_preview = ado_config['pat_token'][:20] + "..."
            print(f"Token preview: {token_preview}")
        
        # This is a warning, not a failure - some tests don't need ADO
        if not ado_config['available']:
            pytest.skip("AZURE_DEVOPS_EXT_PAT not set (required for ADO tests)")
    
    def test_direct_env_access(self):
        """
        Verify environment variables are accessible via os.getenv().
        """
        print("\n=== Direct Environment Variable Access ===")
        
        # Test Azure OpenAI
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        print(f"AZURE_OPENAI_ENDPOINT: {'✓ Set' if azure_endpoint else '✗ Not set'}")
        print(f"AZURE_OPENAI_API_KEY: {'✓ Set' if azure_key else '✗ Not set'}")
        
        assert azure_endpoint, "AZURE_OPENAI_ENDPOINT not accessible via os.getenv()"
        assert azure_key, "AZURE_OPENAI_API_KEY not accessible via os.getenv()"
        
        # Test Azure DevOps
        ado_pat = os.getenv("AZURE_DEVOPS_EXT_PAT")
        print(f"AZURE_DEVOPS_EXT_PAT: {'✓ Set' if ado_pat else '✗ Not set'}")
        
        if ado_pat:
            print(f"  Token length: {len(ado_pat)} chars")
            print(f"  Token preview: {ado_pat[:20]}...")
    
    def test_env_expansion_in_mcp_loader(self):
        """
        Test that environment variable expansion works in MCP loader.
        """
        from app.mcp_loader import _expand_env_vars
        
        print("\n=== Environment Variable Expansion Test ===")
        
        # Set test variable
        os.environ['TEST_EXPANSION'] = 'test_value_123'
        
        # Test expansion
        test_dict = {
            'var1': '${TEST_EXPANSION}',
            'var2': '$TEST_EXPANSION',
            'var3': 'direct_value'
        }
        
        expanded = _expand_env_vars(test_dict)
        
        print(f"Input: {test_dict}")
        print(f"Expanded: {expanded}")
        
        assert expanded['var1'] == 'test_value_123', "Failed to expand ${VAR} format"
        assert expanded['var2'] == 'test_value_123', "Failed to expand $VAR format"
        assert expanded['var3'] == 'direct_value', "Direct value changed unexpectedly"
        
        print("✓ Environment variable expansion working correctly")
    
    def test_ado_pat_expansion(self):
        """
        Test that Azure DevOps PAT token expansion works.
        This simulates what happens in the MCP server configuration.
        """
        from app.mcp_loader import _expand_env_vars
        
        print("\n=== ADO PAT Token Expansion Test ===")
        
        # Get actual PAT token from environment
        actual_pat = os.getenv("AZURE_DEVOPS_EXT_PAT")
        
        if not actual_pat:
            pytest.skip("AZURE_DEVOPS_EXT_PAT not set")
        
        # Simulate MCP server config
        mcp_env = {
            'AZURE_DEVOPS_EXT_PAT': '${AZURE_DEVOPS_EXT_PAT}'
        }
        
        expanded = _expand_env_vars(mcp_env)
        
        print(f"Original: {mcp_env}")
        print(f"Expanded token (first 20 chars): {expanded['AZURE_DEVOPS_EXT_PAT'][:20]}...")
        print(f"Expected token (first 20 chars): {actual_pat[:20]}...")
        
        assert expanded['AZURE_DEVOPS_EXT_PAT'] == actual_pat, \
            "PAT token expansion failed - MCP server will not authenticate!"
        
        print("✓ ADO PAT token expansion working correctly")
        print("✓ MCP server should receive correct authentication token")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
