#!/usr/bin/env python3
"""
Test script to isolate the Unicode encoding issue in the defect analysis pipeline.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from gemba_agents.defect_analysis import DefectAnalysisPipeline, DefectAnalysisConfig

async def test_encoding():
    """Test Unicode handling in the defect analysis pipeline."""
    
    # Test input with Hindi/Devanagari characters
    test_input = "rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"
    
    print("🧪 Testing Unicode Encoding in Defect Analysis Pipeline")
    print("=" * 70)
    
    print(f"📝 Original input: {test_input}")
    print(f"📝 Input type: {type(test_input)}")
    print(f"📝 Input encoding: {test_input.encode('utf-8')}")
    print(f"📝 Input length: {len(test_input)} characters")
    print()
    
    try:
        # Create pipeline with minimal configuration
        config = DefectAnalysisConfig(
            top_n=3,
            min_score=0.2,
            enable_logging=True,
            enable_caching=False,
            parallel_search=False
        )
        
        pipeline = DefectAnalysisPipeline(config)
        
        print("🔄 Running defect analysis pipeline...")
        result = await pipeline.run(test_input)
        
        print("✅ Pipeline completed successfully!")
        print()
        print(f"📊 Results:")
        print(f"   - Original input: {result.original_input}")
        print(f"   - Original input type: {type(result.original_input)}")
        print(f"   - Original input encoding: {result.original_input.encode('utf-8')}")
        print(f"   - Interpreted meaning: {result.intent_data.interpreted_meaning}")
        print(f"   - Component: {result.intent_data.component}")
        print(f"   - Issue: {result.intent_data.issue}")
        print(f"   - Total results: {result.total_unique_results}")
        
        # Check if the original input is preserved correctly
        if result.original_input == test_input:
            print("✅ Original input preserved correctly!")
        else:
            print("❌ Original input corrupted!")
            print(f"   Expected: {test_input}")
            print(f"   Got:      {result.original_input}")
            
            # Check character by character
            print("\n🔍 Character-by-character comparison:")
            for i, (expected, actual) in enumerate(zip(test_input, result.original_input)):
                if expected != actual:
                    print(f"   Position {i}: expected '{expected}' (U+{ord(expected):04X}), got '{actual}' (U+{ord(actual):04X})")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_encoding())
