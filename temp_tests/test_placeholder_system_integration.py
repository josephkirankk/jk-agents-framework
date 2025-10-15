"""
Integration test for placeholder system.

This test verifies:
1. System placeholders (timestamp, date, etc.) work correctly
2. Business context placeholder replacement works
3. Agent prompts get placeholders replaced properly
4. Config-based placeholders work
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.template_utils import render_prompt_with_placeholders
from app.placeholder_system import PlaceholderContext, get_default_registry
from app.main import process_business_context_template


def test_system_placeholders():
    """Test that all system placeholders are working."""
    print("\n" + "=" * 70)
    print("TEST 1: System Placeholders")
    print("=" * 70)
    
    placeholders_to_test = [
        "timestamp",
        "datetime",
        "date",
        "time",
        "year",
        "month",
        "day",
        "platform",
    ]
    
    template = "\n".join([f"{placeholder}: {{{{{placeholder}}}}}" for placeholder in placeholders_to_test])
    
    try:
        result = render_prompt_with_placeholders(template)
        
        # Check that none of the placeholders remain unreplaced
        failed = []
        for placeholder in placeholders_to_test:
            if f"{{{{{placeholder}}}}}" in result:
                failed.append(placeholder)
        
        if failed:
            print(f"❌ FAILED: The following placeholders were not replaced: {', '.join(failed)}")
            print(f"\nResult:\n{result}")
            return False
        else:
            print("✅ PASSED: All system placeholders were replaced")
            print(f"\nSample output:")
            for line in result.split('\n')[:3]:
                print(f"  {line}")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_business_context_rendering():
    """Test that business context is rendered with placeholders."""
    print("\n" + "=" * 70)
    print("TEST 2: Business Context Rendering")
    print("=" * 70)
    
    business_context = """
SYSTEM IDENTITY: Test system
CURRENT DATETIME: {{timestamp}} (use this for date/time references)
TODAY'S DATE: {{date}}
PLATFORM: {{platform}}
"""
    
    try:
        result = process_business_context_template(business_context)
        
        if "{{timestamp}}" in result or "{{date}}" in result or "{{platform}}" in result:
            print("❌ FAILED: Some placeholders were not replaced in business_context")
            print(f"\nResult:\n{result}")
            return False
        else:
            print("✅ PASSED: Business context rendered with placeholders")
            print(f"\nRendered output:\n{result[:200]}...")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_prompt_rendering():
    """Test that agent prompts render placeholders correctly."""
    print("\n" + "=" * 70)
    print("TEST 3: Agent Prompt Rendering")
    print("=" * 70)
    
    prompt_template = """
You are agent: {{agent_name}}
Your description: {{agent_description}}
Business context: {{business_context}}
Current timestamp: {{timestamp}}
User question: {{original_user_question}}
"""
    
    try:
        result = render_prompt_with_placeholders(
            prompt_template,
            agent_name="test_agent",
            agent_description="A test agent for verification",
            business_context="Test business rules",
            original_user_question="What is the current time?",
        )
        
        # Check for unreplaced placeholders
        unreplaced = []
        for placeholder in ["agent_name", "agent_description", "business_context", 
                           "timestamp", "original_user_question"]:
            if f"{{{{{placeholder}}}}}" in result:
                unreplaced.append(placeholder)
        
        if unreplaced:
            print(f"❌ FAILED: Placeholders not replaced: {', '.join(unreplaced)}")
            print(f"\nResult:\n{result}")
            return False
        
        # Verify expected content is present
        if "test_agent" not in result or "Test business rules" not in result:
            print("❌ FAILED: Expected content not found in rendered prompt")
            print(f"\nResult:\n{result}")
            return False
        
        print("✅ PASSED: Agent prompt rendered correctly")
        print(f"\nSample output (first 200 chars):\n{result[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_placeholders():
    """Test that custom user-defined placeholders work."""
    print("\n" + "=" * 70)
    print("TEST 4: Custom Placeholders")
    print("=" * 70)
    
    context = PlaceholderContext()
    context.add_custom_placeholders({
        "custom_var": "test_value",
        "api_version": "v2.1",
    })
    
    template = """
Custom variable: {{custom_var}}
API Version: {{api_version}}
System timestamp: {{timestamp}}
"""
    
    try:
        result = render_prompt_with_placeholders(
            template,
            placeholder_context=context,
        )
        
        if "{{custom_var}}" in result or "{{api_version}}" in result or "{{timestamp}}" in result:
            print("❌ FAILED: Some placeholders were not replaced")
            print(f"\nResult:\n{result}")
            return False
        
        if "test_value" not in result or "v2.1" not in result:
            print("❌ FAILED: Custom placeholder values not found in result")
            print(f"\nResult:\n{result}")
            return False
        
        print("✅ PASSED: Custom placeholders work correctly")
        print(f"\nResult:\n{result}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_placeholder_documentation():
    """Test that placeholder documentation is available."""
    print("\n" + "=" * 70)
    print("TEST 5: Placeholder Documentation")
    print("=" * 70)
    
    try:
        registry = get_default_registry()
        available_placeholders = registry.get_available_placeholders()
        
        # Check for expected system placeholders
        expected_placeholders = ["timestamp", "date", "time", "platform", 
                                "agent_name", "business_context"]
        
        missing = [p for p in expected_placeholders if p not in available_placeholders]
        
        if missing:
            print(f"❌ FAILED: Expected placeholders not registered: {', '.join(missing)}")
            return False
        
        # Get documentation for a few placeholders
        docs = registry.get_documentation()
        
        if not docs:
            print("❌ FAILED: No documentation available")
            return False
        
        print(f"✅ PASSED: {len(available_placeholders)} placeholders registered")
        print(f"\nSample placeholders with documentation:")
        for placeholder in list(expected_placeholders)[:5]:
            doc = docs.get(placeholder, "No doc")
            print(f"  - {placeholder}: {doc[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timestamp_formats():
    """Test different timestamp format placeholders."""
    print("\n" + "=" * 70)
    print("TEST 6: Timestamp Format Variants")
    print("=" * 70)
    
    template = """
ISO timestamp: {{timestamp}}
ISO date: {{date_iso}}
US date: {{date_us}}
EU date: {{date_eu}}
Unix timestamp: {{timestamp_unix}}
"""
    
    try:
        result = render_prompt_with_placeholders(template)
        
        # Check format patterns
        import re
        
        checks = [
            (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', "ISO timestamp"),
            (r'\d{4}-\d{2}-\d{2}', "ISO date"),
            (r'\d{2}/\d{2}/\d{4}', "US or EU date"),
            (r'\d{10}', "Unix timestamp"),
        ]
        
        failed = []
        for pattern, name in checks:
            if not re.search(pattern, result):
                failed.append(name)
        
        if failed:
            print(f"❌ FAILED: Format checks failed for: {', '.join(failed)}")
            print(f"\nResult:\n{result}")
            return False
        
        print("✅ PASSED: All timestamp formats work correctly")
        print(f"\nResult:\n{result}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("PLACEHOLDER SYSTEM INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        ("System Placeholders", test_system_placeholders),
        ("Business Context Rendering", test_business_context_rendering),
        ("Agent Prompt Rendering", test_agent_prompt_rendering),
        ("Custom Placeholders", test_custom_placeholders),
        ("Placeholder Documentation", test_placeholder_documentation),
        ("Timestamp Formats", test_timestamp_formats),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
