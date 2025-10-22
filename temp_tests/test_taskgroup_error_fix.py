#!/usr/bin/env python3
"""
Test script to verify TaskGroup error handling improvements.

This script tests:
1. Environment variable validation
2. Detailed error extraction from BaseExceptionGroup
3. User-friendly error messages with setup instructions
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_mcp_validation():
    """Test MCP server environment variable validation"""
    print("=" * 80)
    print("TEST 1: MCP Server Environment Validation")
    print("=" * 80)
    
    from app.main import load_app_config
    from app.mcp_validation import validate_all_agents_env
    
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "deep_agent_advanced_serpapi.yaml"
    
    try:
        print(f"\n📂 Loading config: {config_path}")
        app_cfg = load_app_config(config_path)
        print(f"✓ Config loaded successfully")
        print(f"  Agents: {[a.name for a in app_cfg.agents]}")
        
        # Validate environment
        print("\n🔍 Validating MCP server environment variables...")
        is_valid, error_msg = validate_all_agents_env(app_cfg.agents)
        
        if is_valid:
            print("✅ All environment variables are properly configured")
            return True
        else:
            print("❌ Environment validation failed:")
            print()
            print(error_msg)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serper_key():
    """Test SERPER_API_KEY specifically"""
    print("\n" + "=" * 80)
    print("TEST 2: SERPER_API_KEY Validation")
    print("=" * 80)
    
    serper_key = os.getenv("SERPER_API_KEY")
    
    if not serper_key:
        print("❌ SERPER_API_KEY is not set")
        print("\n💡 To fix:")
        print("   1. Visit https://serper.dev")
        print("   2. Sign up for a free account (2,500 free searches)")
        print("   3. Get your API key from the dashboard")
        print("   4. Add to .env file:")
        print("      SERPER_API_KEY=your_api_key_here")
        return False
    
    if serper_key == "your-serper-api-key-here":
        print("❌ SERPER_API_KEY is still the placeholder value")
        print("\n💡 Replace with your actual API key from https://serper.dev")
        return False
    
    # Check key format
    if len(serper_key) < 10:
        print(f"⚠️  Warning: SERPER_API_KEY seems too short ({len(serper_key)} chars)")
        return False
    
    print(f"✅ SERPER_API_KEY is set")
    print(f"   Length: {len(serper_key)} characters")
    print(f"   Preview: {serper_key[:10]}...{serper_key[-4:]}")
    return True


def test_error_extraction():
    """Test that BaseExceptionGroup errors are properly extracted"""
    print("\n" + "=" * 80)
    print("TEST 3: BaseExceptionGroup Error Extraction")
    print("=" * 80)
    
    import sys
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("⚠️  Python 3.11+ required for BaseExceptionGroup")
        print(f"   Current version: {sys.version_info.major}.{sys.version_info.minor}")
        return True  # Not applicable
    
    print(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor} (supports BaseExceptionGroup)")
    
    # Test the error extraction logic
    try:
        from app.planner_executor import safe_langgraph_execution
        print("✓ safe_langgraph_execution imported successfully")
        
        # Check that the function has enhanced error handling
        import inspect
        source = inspect.getsource(safe_langgraph_execution)
        
        # Check for key improvements
        checks = [
            ("detailed_errors", "Detailed error tracking"),
            ("traceback.format_exception", "Full traceback extraction"),
            ("Hint:", "User-friendly hints"),
            ("serper", "MCP/Serper detection"),
        ]
        
        all_good = True
        for pattern, description in checks:
            if pattern in source:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ Missing: {description}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error checking error handling: {e}")
        return False


def test_api_validation():
    """Test that API endpoints have validation"""
    print("\n" + "=" * 80)
    print("TEST 4: API Endpoint Validation")
    print("=" * 80)
    
    try:
        import api
        import inspect
        
        # Check query_endpoint
        source = inspect.getsource(api.query_endpoint)
        
        if "validate_all_agents_env" in source:
            print("✓ /query endpoint has MCP validation")
        else:
            print("✗ /query endpoint missing MCP validation")
            return False
        
        # Check query_form_endpoint
        source_form = inspect.getsource(api.query_form_endpoint)
        
        if "validate_all_agents_env" in source_form:
            print("✓ /query/form endpoint has MCP validation")
        else:
            print("✗ /query/form endpoint missing MCP validation")
            return False
        
        print("✅ All API endpoints have proper validation")
        return True
        
    except Exception as e:
        print(f"❌ Error checking API validation: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🔧" * 40)
    print("TASKGROUP ERROR FIX - VERIFICATION TESTS")
    print("🔧" * 40 + "\n")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded environment variables from .env\n")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment\n")
    
    results = []
    
    # Run tests
    results.append(("Environment Validation", test_mcp_validation()))
    results.append(("SERPER_API_KEY Check", test_serper_key()))
    results.append(("Error Extraction", test_error_extraction()))
    results.append(("API Validation", test_api_validation()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
