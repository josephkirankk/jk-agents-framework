"""
Test to verify that placeholder replacement works correctly.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.template_utils import render_prompt_with_placeholders
from app.placeholder_system import PlaceholderContext


def test_timestamp_placeholder():
    """Test that {{timestamp}} placeholder gets replaced."""
    template = """
Business context with placeholder: {{timestamp}}
And another placeholder: {{date}}
"""
    
    print("=" * 60)
    print("Testing placeholder replacement...")
    print("=" * 60)
    print(f"Template:\n{template}")
    print("=" * 60)
    
    try:
        result = render_prompt_with_placeholders(template)
        print(f"Result:\n{result}")
        print("=" * 60)
        
        if "{{timestamp}}" in result:
            print("❌ FAILED: {{timestamp}} was not replaced!")
            return False
        elif "{{date}}" in result:
            print("❌ FAILED: {{date}} was not replaced!")
            return False
        else:
            print("✅ SUCCESS: All placeholders were replaced!")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_business_context_from_config():
    """Test rendering business context similar to the actual config."""
    business_context = """SYSTEM IDENTITY: You are an internal content production system for a YouTube channel.
BRAND VOICE: Friendly, authoritative, concise, storytelling-first.
CRITICAL RULES:
  - PRIORITIZE: existing conversation context and memory for series continuity
  - VERIFY: when making factual claims cite sources or mark as "needs verification"
  - NO FICTION: do not invent quotes, statistics, or sources
  - SEO FIRST: ideation must consider keywords, search intent, and thumbnails
  - TIMESTAMP: use {{timestamp}} for dates and times (UTC datetime)
"""
    
    print("\n" + "=" * 60)
    print("Testing business_context rendering...")
    print("=" * 60)
    print(f"Business context template:\n{business_context}")
    print("=" * 60)
    
    try:
        result = render_prompt_with_placeholders(business_context)
        print(f"Rendered result:\n{result}")
        print("=" * 60)
        
        if "{{timestamp}}" in result:
            print("❌ FAILED: {{timestamp}} was not replaced in business_context!")
            return False
        else:
            print("✅ SUCCESS: {{timestamp}} was replaced in business_context!")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running placeholder replacement tests...\n")
    
    test1 = test_timestamp_placeholder()
    test2 = test_business_context_from_config()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (timestamp placeholder): {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (business context): {'✅ PASSED' if test2 else '❌ FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if (test1 and test2) else 1)
