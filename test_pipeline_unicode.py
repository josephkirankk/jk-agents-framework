#!/usr/bin/env python3
"""
Test script to check Unicode handling between pipelines.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from gemba_agents.defect_analysis import DefectAnalysisPipeline, DefectAnalysisConfig
from gemba_agents.pilger_processing import PilgerProcessingPipeline, PilgerProcessingConfig

async def test_pipeline_unicode():
    """Test Unicode handling between defect analysis and Pilger processing pipelines."""
    
    # Test input with Hindi/Devanagari characters
    test_input = "rack पट्टी के बोल्ट लूज हो गए हैं, उसको टाइट करना पड़ेगा।"
    
    print("🧪 Testing Unicode Encoding Between Pipelines")
    print("=" * 60)
    
    print(f"📝 Original input: {test_input}")
    print(f"📝 Input type: {type(test_input)}")
    print(f"📝 Input encoding: {test_input.encode('utf-8')}")
    print()
    
    try:
        # Stage 1: Defect Analysis Pipeline
        print("🔄 Stage 1: Running defect analysis pipeline...")
        
        defect_config = DefectAnalysisConfig(
            top_n=3,
            min_score=0.7,
            enable_logging=False,  # Disable logging to avoid noise
            enable_caching=False,
            parallel_search=False
        )
        
        defect_pipeline = DefectAnalysisPipeline(defect_config)
        defect_result = await defect_pipeline.run(test_input)
        
        print("✅ Defect analysis completed!")
        print(f"   Original input: {defect_result.original_input}")
        print(f"   Original input type: {type(defect_result.original_input)}")
        print(f"   Original input encoding: {defect_result.original_input.encode('utf-8')}")
        
        # Check if the original input is preserved correctly
        if defect_result.original_input == test_input:
            print("✅ Original input preserved correctly in defect analysis!")
        else:
            print("❌ Original input corrupted in defect analysis!")
            print(f"   Expected: {test_input}")
            print(f"   Got:      {defect_result.original_input}")
            return
        
        print()
        
        # Stage 2: Pilger Processing Pipeline
        print("🔄 Stage 2: Running Pilger processing pipeline...")
        
        pilger_config = PilgerProcessingConfig(
            agent_name="jk_pilger_new_entries_agent",
            timeout_seconds=60,
            format_for_agent="structured",
            enable_logging=False  # Disable logging to avoid noise
        )
        
        # Check the input to Pilger processing
        print(f"📝 Input to Pilger processing:")
        print(f"   defect_result.original_input: {defect_result.original_input}")
        print(f"   Type: {type(defect_result.original_input)}")
        print(f"   Encoding: {defect_result.original_input.encode('utf-8')}")
        print()
        
        # Add debugging to the Pilger processing stage
        print("🔍 Debugging Pilger processing input...")
        
        # Manually check what would be passed to the agent
        user_input_text = defect_result.original_input
        print(f"   user_input_text: {user_input_text}")
        print(f"   user_input_text type: {type(user_input_text)}")
        print(f"   user_input_text encoding: {user_input_text.encode('utf-8')}")
        
        # Check if the user_input_text is still correct
        if user_input_text == test_input:
            print("✅ user_input_text is still correct!")
        else:
            print("❌ user_input_text is corrupted!")
            print(f"   Expected: {test_input}")
            print(f"   Got:      {user_input_text}")
            
            # Character-by-character comparison
            print("\n🔍 Character-by-character comparison:")
            for i, (expected, actual) in enumerate(zip(test_input, user_input_text)):
                if expected != actual:
                    print(f"   Position {i}: expected '{expected}' (U+{ord(expected):04X}), got '{actual}' (U+{ord(actual):04X})")
        
        print()
        print("🔄 Running Pilger processing pipeline...")
        
        pilger_pipeline = PilgerProcessingPipeline(pilger_config)
        pilger_result = await pilger_pipeline.run(defect_result)
        
        print("✅ Pilger processing completed!")
        print(f"   Success: {pilger_result.success}")
        print(f"   Processing time: {pilger_result.processing_time_ms:.2f}ms")
        
        if pilger_result.error_message:
            print(f"   Error: {pilger_result.error_message}")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline_unicode())
