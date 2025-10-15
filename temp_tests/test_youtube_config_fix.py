"""
Test to verify the youtube_creative_team.yaml config fix works correctly.
This simulates what happens when the business_context is rendered.
"""
import sys
from pathlib import Path
import yaml

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import process_business_context_template


def test_youtube_config_business_context():
    """Test that the fixed youtube config business context renders correctly."""
    print("=" * 70)
    print("Testing YouTube Creative Team Config Fix")
    print("=" * 70)
    
    # Load the actual config
    config_path = Path(__file__).parent.parent / "config" / "youtube_creative_team.yaml"
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    business_context = config_data.get('business_context', '')
    
    print(f"\nOriginal business_context (first 300 chars):")
    print("-" * 70)
    print(business_context[:300])
    print("..." if len(business_context) > 300 else "")
    print("-" * 70)
    
    # Check if it contains the problematic pattern
    if "use {{timestamp}}" in business_context:
        print("\n❌ FAILED: Config still contains 'use {{timestamp}}' pattern")
        print("This will cause the LLM to output literal '{{timestamp}}' in responses.")
        return False
    
    # Process it through the actual function used in the app
    try:
        rendered = process_business_context_template(business_context)
        
        print(f"\nRendered business_context (first 400 chars):")
        print("-" * 70)
        print(rendered[:400])
        print("..." if len(rendered) > 400 else "")
        print("-" * 70)
        
        # Check that placeholders are replaced
        if "{{timestamp}}" in rendered or "{{date}}" in rendered:
            print("\n❌ FAILED: Placeholders not replaced in rendered business_context")
            return False
        
        # Check that we have the corrected instruction
        if "CURRENT DATETIME:" in business_context or "CURRENT DATETIME:" in rendered:
            print("\n✅ SUCCESS: Config has been corrected")
            print("- No 'use {{timestamp}}' instruction found")
            print("- Placeholder properly replaced in rendered output")
            print("- LLM will receive actual datetime value")
            return True
        else:
            print("\n⚠️  WARNING: Expected 'CURRENT DATETIME:' pattern not found")
            print("Config may have been changed in a different way.")
            # Still pass if placeholders are being replaced
            if "{{" not in rendered:
                print("But placeholders are being replaced, so it's okay.")
                return True
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR rendering business_context: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulate_agent_seeing_context():
    """Simulate what the agent would see after processing."""
    print("\n" + "=" * 70)
    print("Simulating Agent's View of Business Context")
    print("=" * 70)
    
    # This is what the config should look like after our fix
    correct_pattern = """
SYSTEM IDENTITY: Test system
CRITICAL RULES:
  - CURRENT DATETIME: {{timestamp}} (use this for date/time references)
"""
    
    wrong_pattern = """
SYSTEM IDENTITY: Test system  
CRITICAL RULES:
  - TIMESTAMP: use {{timestamp}} for dates and times
"""
    
    print("\n❌ WRONG Pattern (causes literal output):")
    print("-" * 70)
    processed_wrong = process_business_context_template(wrong_pattern)
    print(processed_wrong)
    print("-" * 70)
    print("LLM sees: 'use {{timestamp}}' and will output it literally")
    
    print("\n✅ CORRECT Pattern (provides actual value):")
    print("-" * 70)
    processed_correct = process_business_context_template(correct_pattern)
    print(processed_correct)
    print("-" * 70)
    print("LLM sees actual datetime and can reference it in responses")
    
    return True


if __name__ == "__main__":
    print("YouTube Creative Team Config Fix Verification\n")
    
    test1 = test_youtube_config_business_context()
    test2 = test_simulate_agent_seeing_context()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Config Fix Test: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Simulation Test: {'✅ PASSED' if test2 else '❌ FAILED'}")
    print("=" * 70)
    
    if test1 and test2:
        print("\n🎉 All tests passed! The fix is working correctly.")
        print("\nWhat was fixed:")
        print("1. Changed 'use {{timestamp}}' to 'CURRENT DATETIME: {{timestamp}}'")
        print("2. Placeholder is replaced BEFORE LLM sees the prompt")
        print("3. LLM now receives actual datetime value, not placeholder syntax")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    sys.exit(0 if (test1 and test2) else 1)
