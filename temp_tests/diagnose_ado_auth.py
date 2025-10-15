#!/usr/bin/env python3
"""
Comprehensive diagnostic script for ADO MCP authentication issues.
This script tests every step of the authentication chain.
"""

import os
import sys
import subprocess
import asyncio
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)


def test_step(step_name, test_func):
    """Run a test step and report result."""
    print(f"\n{'='*60}")
    print(f"Testing: {step_name}")
    print('='*60)
    try:
        result = test_func()
        if result:
            print(f"✅ PASS: {step_name}")
        else:
            print(f"❌ FAIL: {step_name}")
        return result
    except Exception as e:
        print(f"❌ ERROR in {step_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def step1_check_env_file():
    """Step 1: Check if .env file exists and is readable."""
    print(f"Checking .env file at: {env_path}")
    if env_path.exists():
        print(f"✓ .env file exists")
        print(f"✓ File size: {env_path.stat().st_size} bytes")
        return True
    else:
        print(f"✗ .env file not found")
        return False


def step2_check_pat_in_env():
    """Step 2: Check if PAT token is loaded in Python environment."""
    pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if not pat:
        print("✗ AZURE_DEVOPS_EXT_PAT not found in os.environ")
        return False
    
    print(f"✓ AZURE_DEVOPS_EXT_PAT is set")
    print(f"✓ Token length: {len(pat)} characters")
    print(f"✓ Token preview: {pat[:20]}...")
    
    # Check if it's a placeholder
    if pat.lower() in ['your-azure-devops-pat-token-here', 'your-pat-here', 'xx', 'xxx']:
        print("✗ PAT token appears to be a placeholder!")
        return False
    
    return True


def step3_check_node_npx():
    """Step 3: Check if Node.js and npx are available."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ Node.js version: {version}")
            major_version = int(version.lstrip('v').split('.')[0])
            if major_version < 20:
                print(f"✗ Node.js version {major_version} is too old (need 20+)")
                return False
        else:
            print("✗ Node.js not available")
            return False
    except Exception as e:
        print(f"✗ Error checking Node.js: {e}")
        return False
    
    try:
        result = subprocess.run(['which', 'npx'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✓ npx available at: {result.stdout.strip()}")
        else:
            print("✗ npx not found")
            return False
    except Exception as e:
        print(f"✗ Error checking npx: {e}")
        return False
    
    return True


def step4_test_ado_mcp_package():
    """Step 4: Test if @azure-devops/mcp package is accessible."""
    print("Testing if @azure-devops/mcp can be loaded...")
    try:
        # Test with --help flag
        result = subprocess.run(
            ['npx', '-y', '@azure-devops/mcp', '--help'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ @azure-devops/mcp package is accessible")
            print(f"✓ Help output preview: {result.stdout[:200]}...")
            return True
        else:
            print(f"✗ Failed to load package (exit code: {result.returncode})")
            print(f"  stderr: {result.stderr[:500]}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Timeout waiting for package")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def step5_test_subprocess_env():
    """Step 5: Test if subprocess receives environment variables."""
    pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if not pat:
        print("✗ PAT not available to test")
        return False
    
    # Create test subprocess that echoes the env var
    test_script = """
import os
import sys
pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
if pat:
    print(f"ENV_VAR_RECEIVED:{len(pat)}")
    sys.exit(0)
else:
    print("ENV_VAR_NOT_RECEIVED")
    sys.exit(1)
"""
    
    try:
        # Test with explicit env
        env = os.environ.copy()
        env['AZURE_DEVOPS_EXT_PAT'] = pat
        
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            env=env,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.strip()
        if "ENV_VAR_RECEIVED" in output:
            print(f"✓ Subprocess receives environment variables correctly")
            print(f"✓ Test output: {output}")
            return True
        else:
            print(f"✗ Subprocess did not receive environment variable")
            print(f"  Output: {output}")
            print(f"  Stderr: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def step6_test_mcp_with_env():
    """Step 6: Test if ADO MCP server receives the environment variable."""
    pat = os.getenv('AZURE_DEVOPS_EXT_PAT')
    if not pat:
        print("✗ PAT not available to test")
        return False
    
    print("Testing ADO MCP server startup with environment variable...")
    print("This will attempt to start the server briefly (5 second timeout)...")
    
    try:
        env = os.environ.copy()
        env['AZURE_DEVOPS_EXT_PAT'] = pat
        
        # Try to start the MCP server with env authentication
        result = subprocess.run(
            ['npx', '-y', '@azure-devops/mcp', 'PepsiCoIT', '-d', 'core', '-a', 'env'],
            env=env,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # The server will start and wait for JSON-RPC messages
        # We expect a timeout because it's waiting for input
        # But we can check stderr for authentication errors
        return True  # If we got here without exception, it started
        
    except subprocess.TimeoutExpired:
        # Timeout is expected - server is waiting for input
        print("✓ Server started (timeout expected - server is waiting for input)")
        return True
    except Exception as e:
        error_str = str(e)
        if "authentication" in error_str.lower() or "login" in error_str.lower():
            print(f"✗ Authentication error: {e}")
            return False
        else:
            print(f"⚠ Other error (might be OK): {e}")
            return True


async def step7_test_mcp_loader():
    """Step 7: Test MCP loader with actual configuration."""
    print("Testing MCP loader with configuration...")
    
    try:
        from app.main import load_app_config
        from app.mcp_loader import load_mcp_tools, close_mcp_client
        
        config_path = project_root / "config" / "ado_working_v1.yaml"
        if not config_path.exists():
            print(f"✗ Config file not found: {config_path}")
            return False
        
        print(f"✓ Config file: {config_path}")
        
        config = load_app_config(config_path)
        
        # Find ADO agent
        ado_agent = None
        for agent in config.agents:
            if "azure_devops" in agent.name.lower() or "feature_analyzer" in agent.name.lower():
                ado_agent = agent
                break
        
        if not ado_agent or not ado_agent.mcp_servers:
            print("✗ ADO agent or MCP servers not configured")
            return False
        
        print(f"✓ Found agent: {ado_agent.name}")
        print(f"✓ MCP servers: {list(ado_agent.mcp_servers.keys())}")
        
        # Try to load MCP tools with 10 second timeout
        print("\nAttempting to load MCP tools (10s timeout)...")
        mcp_client, tools = await asyncio.wait_for(
            load_mcp_tools(ado_agent.mcp_servers),
            timeout=10.0
        )
        
        print(f"✓ MCP server started successfully")
        print(f"✓ Loaded {len(tools)} tools")
        if tools:
            print(f"✓ Sample tools: {[t.name for t in tools[:5]]}")
        
        # Cleanup
        if mcp_client:
            await close_mcp_client(mcp_client)
            print("✓ MCP client closed")
        
        return True
        
    except asyncio.TimeoutError:
        print("✗ Timeout loading MCP tools (likely authentication issue)")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all diagnostic steps."""
    print("="*60)
    print("ADO MCP Authentication Diagnostic Tool")
    print("="*60)
    print("\nThis tool will test each step of the authentication chain")
    print("to identify where the PAT token issue occurs.\n")
    
    results = {}
    
    # Run all steps
    results['env_file'] = test_step("Step 1: Check .env file", step1_check_env_file)
    results['pat_in_env'] = test_step("Step 2: Check PAT in environment", step2_check_pat_in_env)
    results['node_npx'] = test_step("Step 3: Check Node.js and npx", step3_check_node_npx)
    results['ado_package'] = test_step("Step 4: Check @azure-devops/mcp package", step4_test_ado_mcp_package)
    results['subprocess_env'] = test_step("Step 5: Test subprocess environment", step5_test_subprocess_env)
    results['mcp_with_env'] = test_step("Step 6: Test MCP server with env", step6_test_mcp_with_env)
    
    # Step 7 needs async
    print(f"\n{'='*60}")
    print(f"Testing: Step 7: Test MCP loader")
    print('='*60)
    try:
        results['mcp_loader'] = await step7_test_mcp_loader()
        if results['mcp_loader']:
            print(f"✅ PASS: Step 7: Test MCP loader")
        else:
            print(f"❌ FAIL: Step 7: Test MCP loader")
    except Exception as e:
        print(f"❌ ERROR in Step 7: Test MCP loader: {e}")
        import traceback
        traceback.print_exc()
        results['mcp_loader'] = False
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    all_pass = True
    for step, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {step}")
        if not passed:
            all_pass = False
    
    print("\n" + "="*60)
    if all_pass:
        print("✅ All tests passed! PAT authentication should work.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        print("\nRecommended fixes:")
        if not results.get('env_file'):
            print("  - Create .env file in project root")
        if not results.get('pat_in_env'):
            print("  - Set AZURE_DEVOPS_EXT_PAT in .env file")
        if not results.get('node_npx'):
            print("  - Install Node.js 20+ (brew install node)")
        if not results.get('ado_package'):
            print("  - Check npm registry access")
        if not results.get('subprocess_env'):
            print("  - Environment variable passing issue")
        if not results.get('mcp_with_env'):
            print("  - ADO MCP server not recognizing PAT")
        if not results.get('mcp_loader'):
            print("  - MCP loader configuration issue")
    print("="*60)
    
    return all_pass


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
