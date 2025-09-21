#!/usr/bin/env python3
"""
Test script to isolate the Unicode encoding issue in template rendering.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from app.placeholder_system import PlaceholderContext
from app.template_utils import render_prompt_with_placeholders

def test_template_rendering():
    """Test Unicode handling in template rendering."""
    
    # Test input with Hindi/Devanagari characters
    test_input = "rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"
    
    print("🧪 Testing Unicode Encoding in Template Rendering")
    print("=" * 60)
    
    print(f"📝 Original input: {test_input}")
    print(f"📝 Input type: {type(test_input)}")
    print(f"📝 Input encoding: {test_input.encode('utf-8')}")
    print()
    
    # Simple template with user_input placeholder
    template = """
Test template with placeholder:

USER INPUT:
{{user_input}}

End of template.
"""
    
    print("🔄 Testing template rendering...")
    
    try:
        # Create placeholder context
        context = PlaceholderContext()
        
        # Add custom placeholder
        custom_placeholders = {
            "user_input": test_input
        }
        context.add_custom_placeholders(custom_placeholders)
        
        # Render template
        rendered = render_prompt_with_placeholders(
            template,
            placeholder_context=context
        )
        
        print("✅ Template rendered successfully!")
        print()
        print("📄 Rendered template:")
        print("-" * 40)
        print(rendered)
        print("-" * 40)
        print()
        
        # Check if the user input is preserved correctly
        if test_input in rendered:
            print("✅ User input preserved correctly in rendered template!")
        else:
            print("❌ User input corrupted in rendered template!")
            
            # Find the USER INPUT section
            lines = rendered.split('\n')
            for i, line in enumerate(lines):
                if 'USER INPUT:' in line and i + 1 < len(lines):
                    actual_input = lines[i + 1]
                    print(f"   Expected: {test_input}")
                    print(f"   Got:      {actual_input}")
                    
                    # Check character by character
                    print("\n🔍 Character-by-character comparison:")
                    for j, (expected, actual) in enumerate(zip(test_input, actual_input)):
                        if expected != actual:
                            print(f"   Position {j}: expected '{expected}' (U+{ord(expected):04X}), got '{actual}' (U+{ord(actual):04X})")
                    break
        
        # Test encoding of the rendered template
        print(f"\n📝 Rendered template encoding: {rendered.encode('utf-8')[:100]}...")
        
    except Exception as e:
        print(f"❌ Template rendering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_template_rendering()
