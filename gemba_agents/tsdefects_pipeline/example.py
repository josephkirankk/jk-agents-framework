"""
Example usage of the TsDefects pipeline.

This script demonstrates how to use the integrated TsDefects pipeline
for defect analysis with TsSearch and agent enhancement.
"""

import asyncio
import json
import logging
from pathlib import Path

from .pipeline import TsDefectsPipeline, analyze_ts_defects_sync
from .models.data_models import TsDefectsConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_example():
    """Basic example using the pipeline with default configuration."""
    print("=== Basic TsDefects Pipeline Example ===")
    
    # Create pipeline with default configuration
    pipeline = TsDefectsPipeline()
    
    # Test input
    user_input = "Oil ठंडा ही नहीं हो रहा है, चिल्लर जो है वो चिल्ल र सही से ऑयल को ठंडा नहीं कर रहा है। बहुत ज्या दा गर्म हो रहा है, धुआं निकल रहा है। ऐसे चलाएंगे तो फिर सब कुछ डूब जा एगा। जल्दी से रिपेयर करो।"
    
    print(f"Input: {user_input}")
    print("Running pipeline...")
    
    try:
        # Run the pipeline
        result = await pipeline.run(user_input)
        
        # Display results
        print(f"\nResults:")
        print(f"- Success: {result.success}")
        print(f"- Total results: {result.total_results}")
        print(f"- Processing time: {result.processing_time_ms:.2f}ms")
        
        if result.success and result.enhanced_defects:
            print(f"\nIntent Data:")
            print(f"- Component: {result.intent_data.component}")
            print(f"- Sub-component: {result.intent_data.sub_component}")
            print(f"- Issue: {result.intent_data.issue}")

            print(f"\nEnhanced Defects:")
            for i, defect in enumerate(result.enhanced_defects[:3], 1):  # Show top 3
                print(f"{i}. {defect.defect_code}")
                print(f"   Text: {defect.defect_text[:100]}...")
                print(f"   Score: {defect.score:.3f}")
                print(f"   Curator Action: {defect.curator_action}")
                print(f"   Rationale: {defect.rationale[:100]}...")
                print()

            print(f"\nRaw JSON Result:")
            enhanced_defects_json = [defect.model_dump() for defect in result.enhanced_defects]
            print(json.dumps(enhanced_defects_json, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"Pipeline failed: {e}")


async def custom_config_example():
    """Example using custom configuration."""
    print("=== Custom Configuration Example ===")
    
    # Create custom configuration
    config = TsDefectsConfig(
        intent_agent_name="jk_pilger_extract_intent_agent",
        processing_agent_name="jk_pilger_new_entries_only_defects_agent",
        search_limit=5,
        min_similarity_score=0.3,
        enable_logging=True,
        parallel_search=True
    )
    
    # Create pipeline with custom config
    pipeline = TsDefectsPipeline(config)
    
    # Test input
    user_input = "फीड स्क्रू, शाफ्ट तु टत आहे."
    
    print(f"Input: {user_input}")
    print("Running pipeline with custom config...")
    
    try:
        result = await pipeline.run(user_input)
        
        print(f"\nResults:")
        print(f"- Success: {result.success}")
        print(f"- Total results: {result.total_results}")
        print(f"- Processing time: {result.processing_time_ms:.2f}ms")
        
        if result.success and result.enhanced_defects:
            print(f"\nTop defect:")
            defect = result.enhanced_defects[0]
            print(f"- Code: {defect.defect_code}")
            print(f"- Text: {defect.defect_text}")
            print(f"- Machine: {defect.machine}")
            print(f"- Subsystem: {defect.subsystem}")
            print(f"- Component: {defect.component}")
            print(f"- Score: {defect.score:.3f}")
            print(f"- Curator Action: {defect.curator_action}")
            print(f"- Rationale: {defect.rationale}")

            print(f"\nRaw JSON Result:")
            enhanced_defects_json = [defect.model_dump() for defect in result.enhanced_defects]
            print(json.dumps(enhanced_defects_json, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"Pipeline failed: {e}")


def synchronous_example():
    """Example using synchronous execution."""
    print("=== Synchronous Execution Example ===")
    
    user_input = "Bearing overheating in the gearbox assembly"
    
    print(f"Input: {user_input}")
    print("Running pipeline synchronously...")
    
    try:
        # Use the convenience function for synchronous execution
        result = analyze_ts_defects_sync(user_input)
        
        print(f"\nResults:")
        print(f"- Success: {result.success}")
        print(f"- Total results: {result.total_results}")
        print(f"- Processing time: {result.processing_time_ms:.2f}ms")
        
        if result.success and result.enhanced_defects:
            print(f"\nFirst defect:")
            defect = result.enhanced_defects[0]
            print(f"- Code: {defect.defect_code}")
            print(f"- Curator Action: {defect.curator_action}")
        else:
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"Pipeline failed: {e}")


def pipeline_info_example():
    """Example showing pipeline information."""
    print("=== Pipeline Information Example ===")
    
    pipeline = TsDefectsPipeline()
    
    # Get pipeline information
    info = pipeline.get_pipeline_info()
    
    print("Pipeline Configuration:")
    print(json.dumps(info, indent=2, default=str))


async def batch_processing_example():
    """Example processing multiple inputs."""
    print("=== Batch Processing Example ===")
    
    pipeline = TsDefectsPipeline()
    
    test_inputs = [
        "Pump seal leakage causing fluid loss",
        "Motor bearing vibration detected",
        "Hydraulic pressure drop in main line",
        "Gear tooth wear in transmission"
    ]
    
    print(f"Processing {len(test_inputs)} inputs...")
    
    results = []
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n{i}. Processing: {user_input}")
        
        try:
            result = await pipeline.run(user_input)
            results.append(result)
            
            if result.success:
                print(f"   ✓ Found {result.total_results} defects in {result.processing_time_ms:.0f}ms")
            else:
                print(f"   ✗ Failed: {result.error_message}")
                
        except Exception as e:
            print(f"   ✗ Exception: {e}")
    
    # Summary
    successful = sum(1 for r in results if r.success)
    total_defects = sum(r.total_results for r in results if r.success)
    avg_time = sum(r.processing_time_ms for r in results if r.success) / max(successful, 1)
    
    print(f"\nBatch Summary:")
    print(f"- Successful: {successful}/{len(test_inputs)}")
    print(f"- Total defects found: {total_defects}")
    print(f"- Average processing time: {avg_time:.2f}ms")


async def main():
    """Run all examples."""
    print("TsDefects Pipeline Examples")
    print("=" * 50)
    
    # Run examples
    await basic_example()
    print("\n" + "=" * 50)
    
    await custom_config_example()
    print("\n" + "=" * 50)
    
    synchronous_example()
    print("\n" + "=" * 50)
    
    pipeline_info_example()
    print("\n" + "=" * 50)
    
    await batch_processing_example()
    print("\n" + "=" * 50)
    
    print("All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
