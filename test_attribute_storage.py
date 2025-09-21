#!/usr/bin/env python3
"""
Test script to check if the issue is in attribute storage.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_attribute_storage():
    """Test Unicode handling in attribute storage."""
    
    # Test input with Hindi/Devanagari characters
    test_input = "rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"
    
    print("🧪 Testing Unicode Encoding in Attribute Storage")
    print("=" * 60)
    
    print(f"📝 Original input: {test_input}")
    print(f"📝 Input type: {type(test_input)}")
    print(f"📝 Input encoding: {test_input.encode('utf-8')}")
    print()
    
    # Create a simple object to test attribute storage
    class TestObject:
        pass
    
    test_obj = TestObject()
    
    # Test storing the Unicode string as an attribute
    print("🔄 Testing attribute storage...")
    
    try:
        # Store the Unicode string as an attribute
        setattr(test_obj, "_rendered_prompt", test_input)
        
        # Retrieve the attribute
        retrieved = getattr(test_obj, "_rendered_prompt", "(none)")
        
        print("✅ Attribute storage completed!")
        print(f"   Retrieved: {retrieved}")
        print(f"   Retrieved type: {type(retrieved)}")
        print(f"   Retrieved encoding: {retrieved.encode('utf-8')}")
        print()
        
        # Check if the Unicode string is preserved correctly
        if retrieved == test_input:
            print("✅ Unicode string preserved correctly in attribute storage!")
        else:
            print("❌ Unicode string corrupted in attribute storage!")
            print(f"   Expected: {test_input}")
            print(f"   Got:      {retrieved}")
            
            # Character-by-character comparison
            print("\n🔍 Character-by-character comparison:")
            for i, (expected, actual) in enumerate(zip(test_input, retrieved)):
                if expected != actual:
                    print(f"   Position {i}: expected '{expected}' (U+{ord(expected):04X}), got '{actual}' (U+{ord(actual):04X})")
        
        # Test with a template that includes the Unicode string
        template = f"""
Test template with Unicode:

USER INPUT:
{test_input}

End of template.
"""
        
        print("\n🔄 Testing template attribute storage...")
        
        # Store the template as an attribute
        setattr(test_obj, "_template", template)
        
        # Retrieve the template attribute
        retrieved_template = getattr(test_obj, "_template", "(none)")
        
        print("✅ Template attribute storage completed!")
        print(f"   Template length: {len(retrieved_template)} characters")
        
        # Check if the Unicode string is preserved in the template
        if test_input in retrieved_template:
            print("✅ Unicode string preserved correctly in template attribute!")
        else:
            print("❌ Unicode string corrupted in template attribute!")
            
            # Find the USER INPUT section
            lines = retrieved_template.split('\n')
            for i, line in enumerate(lines):
                if 'USER INPUT:' in line and i + 1 < len(lines):
                    actual_input = lines[i + 1]
                    print(f"   Expected: {test_input}")
                    print(f"   Got:      {actual_input}")
                    break
        
    except Exception as e:
        print(f"❌ Attribute storage test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_attribute_storage()
