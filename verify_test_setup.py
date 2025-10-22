#!/usr/bin/env python3
"""
Integration Test Setup Verification
Checks all prerequisites before running integration tests
"""

import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version too old: {version.major}.{version.minor}.{version.micro}")
        print("   Required: Python 3.10+")
        return False


def check_dependencies():
    """Check required Python packages"""
    required = {
        'langchain': 'langchain',
        'langchain_openai': 'langchain-openai',
        'langchain_anthropic': 'langchain-anthropic',
        'langchain_google_genai': 'langchain-google-genai',
        'langgraph': 'langgraph',
        'chromadb': 'chromadb',
        'dotenv': 'python-dotenv',
        'fastapi': 'fastapi',
        'litellm': 'litellm',
    }
    
    print("\n📦 Checking Python packages...")
    all_ok = True
    
    for module_name, package_name in required.items():
        try:
            __import__(module_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Check for .env file"""
    env_path = Path(".env")
    if env_path.exists():
        print("\n✅ .env file found")
        return True
    else:
        print("\n❌ .env file not found")
        print("   Create from .env.example: cp .env.example .env")
        return False


def check_azure_credentials():
    """Check Azure OpenAI credentials"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n🔑 Checking Azure OpenAI credentials...")
    
    required = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_VERSION"
    ]
    
    all_ok = True
    for var in required:
        value = os.getenv(var)
        if value:
            # Mask API key
            if 'KEY' in var:
                display = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display = value[:50] + "..." if len(value) > 50 else value
            print(f"  ✅ {var} = {display}")
        else:
            print(f"  ❌ {var} - NOT SET")
            all_ok = False
    
    return all_ok


def check_optional_credentials():
    """Check optional provider credentials"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n🔑 Optional provider credentials:")
    
    optional = {
        "GOOGLE_API_KEY": "Google Gemini",
        "ANTHROPIC_API_KEY": "Anthropic Claude",
        "SERPER_API_KEY": "Serper Search",
    }
    
    for var, name in optional.items():
        value = os.getenv(var)
        if value:
            display = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  ✅ {name}: {display}")
        else:
            print(f"  ⏭️  {name}: Not set (optional)")


def check_system_commands():
    """Check required system commands"""
    import subprocess
    
    print("\n🔧 Checking system commands...")
    
    commands = {
        'deno': 'Deno runtime (for MCP Python server)',
        'uv': 'uv package manager (optional but recommended)',
    }
    
    for cmd, description in commands.items():
        try:
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"  ✅ {cmd}: {version}")
            else:
                print(f"  ❌ {cmd}: Command failed")
        except FileNotFoundError:
            print(f"  ⏭️  {cmd}: Not found ({description})")
        except Exception as e:
            print(f"  ⚠️  {cmd}: Error checking - {e}")


def check_file_permissions():
    """Check file system permissions"""
    print("\n📁 Checking file system permissions...")
    
    test_dirs = [
        Path("integration_tests/temp"),
        Path("data"),
        Path("test_data"),
    ]
    
    all_ok = True
    for test_dir in test_dirs:
        test_dir.mkdir(parents=True, exist_ok=True)
        test_file = test_dir / ".test_write"
        
        try:
            test_file.write_text("test")
            test_file.unlink()
            print(f"  ✅ {test_dir}: Writable")
        except Exception as e:
            print(f"  ❌ {test_dir}: Not writable - {e}")
            all_ok = False
    
    return all_ok


def check_test_configs():
    """Check if required test configs exist"""
    print("\n⚙️  Checking test configurations...")
    
    config_dir = Path("config")
    required_configs = [
        "python_exec_agent_working.yaml",
        "chromadb_memory_test.yaml",
        "test_data_parser_enterprise.yaml",
    ]
    
    all_ok = True
    for config in required_configs:
        config_path = config_dir / config
        if config_path.exists():
            print(f"  ✅ {config}")
        else:
            print(f"  ⏭️  {config} - Not found (will be created by tests)")
    
    return True


def test_azure_connection():
    """Test actual connection to Azure OpenAI"""
    print("\n🌐 Testing Azure OpenAI connection...")
    
    try:
        from dotenv import load_dotenv
        from langchain_openai import AzureChatOpenAI
        
        load_dotenv()
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if not all([endpoint, api_key, deployment, api_version]):
            print("  ⏭️  Skipping - credentials not set")
            return True
        
        llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            azure_deployment=deployment,
            api_version=api_version,
            temperature=0
        )
        
        # Test with a simple message
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content="Say 'test OK'")])
        
        print(f"  ✅ Connection successful!")
        print(f"  Response: {response.content[:50]}")
        return True
        
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False


def main():
    """Run all verification checks"""
    print("=" * 80)
    print("  INTEGRATION TEST SETUP VERIFICATION")
    print("=" * 80)
    
    results = []
    
    # Core checks
    results.append(("Python Version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Env File", check_env_file()))
    
    # Only check credentials if .env exists
    if results[-1][1]:
        results.append(("Azure Credentials", check_azure_credentials()))
        check_optional_credentials()
    
    # System checks
    check_system_commands()
    results.append(("File Permissions", check_file_permissions()))
    results.append(("Test Configs", check_test_configs()))
    
    # Connection test (optional)
    if all(r[1] for r in results):
        try:
            results.append(("Azure Connection", test_azure_connection()))
        except Exception as e:
            print(f"\n⚠️  Connection test skipped: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("  🎉 ALL CHECKS PASSED - Ready to run integration tests!")
        print("\n  Run tests with:")
        print("    ./run_integration_tests_full.sh")
        print("    or")
        print("    python integration_tests/run_all_tests.py")
    else:
        print("  ⚠️  SOME CHECKS FAILED - Please fix issues before running tests")
    print("=" * 80 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
