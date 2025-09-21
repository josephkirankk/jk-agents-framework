"""
Example usage of the defect analysis pipeline.

This module demonstrates how to use the DefectAnalysisPipeline for analyzing
equipment defects and issues.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
import json

from gemba_agents.defect_analysis.pipeline import DefectAnalysisPipeline, analyze_defect_sync
from gemba_agents.defect_analysis.models.data_models import DefectAnalysisConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def basic_example():
    """
    Basic example of using the defect analysis pipeline.
    """
    print("=" * 60)
    print("BASIC DEFECT ANALYSIS EXAMPLE")
    print("=" * 60)
    
    # Create pipeline with default configuration
    pipeline = DefectAnalysisPipeline()
    
    # Example user inputs
    test_inputs = [
        "The pump's loading/unloading piston is not operating smoothly",
        "Motor bearing is overheating and making noise",
        "Hydraulic system has a leak near the pump",
        "Gear tooth on the rack strip is broken",
        "पंप लोडिंग अनलोडिंग करने वाला पिस्टन बराबर से चल नहीं रहा है"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n{i}. Analyzing: {user_input}")
        print("-" * 50)
        
        try:
            # Run the pipeline
            result = await pipeline.run(user_input)
            
            # Display results
            print(f"✅ Analysis completed in {result.processing_time_ms:.2f}ms")
            print(f"📝 Interpreted meaning: {result.intent_data.interpreted_meaning}")
            print(f"🔧 Component: {result.intent_data.component}")
            print(f"⚙️  Sub-component: {result.intent_data.sub_component}")
            print(f"🔗 Related component: {result.intent_data.related_component}")
            print(f"⚠️  Issue: {result.intent_data.issue}")
            print(f"📊 Found {result.total_unique_results} unique defects")
            
            if result.root_causes:
                print(f"🔍 Top root causes: {', '.join(result.root_causes[:3])}")
            
            if result.corrective_actions:
                print(f"🛠️  Top actions: {', '.join(result.corrective_actions[:3])}")
                
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
    
    # Print profiling statistics
    print("\n" + "=" * 60)
    print("PIPELINE PROFILING STATISTICS")
    print("=" * 60)
    pipeline.print_profiling_stats()


async def custom_config_example():
    """
    Example using custom configuration.
    """
    print("\n" + "=" * 60)
    print("CUSTOM CONFIGURATION EXAMPLE")
    print("=" * 60)
    
    # Create custom configuration
    config = DefectAnalysisConfig(
        top_n=15,  # Get more results
        min_score=0.5,  # Lower threshold
        parallel_search=True,  # Enable parallel search
        enable_logging=True,
        enable_caching=True
    )
    
    # Create pipeline with custom config
    pipeline = DefectAnalysisPipeline(config)
    
    # Test input
    user_input = "The gearbox bearing is making unusual noise and getting hot"
    
    print(f"Analyzing with custom config: {user_input}")
    print(f"Configuration: top_n={config.top_n}, min_score={config.min_score}")
    
    try:
        result = await pipeline.run(user_input)
        
        print(f"✅ Found {result.total_unique_results} defects")
        print(f"⏱️  Processing time: {result.processing_time_ms:.2f}ms")
        
        # Show detailed results
        if result.defects:
            print("\n📋 Top 3 matching defects:")
            for i, defect in enumerate(result.defects[:3], 1):
                print(f"  {i}. {defect.defect_code}: {defect.defect_text}")
                print(f"     Score: {defect.score:.1%}, Severity: {defect.severity}")
                
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")


def synchronous_example():
    """
    Example of using the pipeline synchronously.
    """
    print("\n" + "=" * 60)
    print("SYNCHRONOUS USAGE EXAMPLE")
    print("=" * 60)
    
    user_input = "Hydraulic pump cavitation detected"
    
    print(f"Running synchronous analysis: {user_input}")
    
    try:
        # Use the convenience function
        result = analyze_defect_sync(user_input)
        
        print(f"✅ Synchronous analysis completed")
        print(f"🔧 Component: {result.intent_data.component}")
        print(f"⚠️  Issue: {result.intent_data.issue}")
        print(f"📊 Results: {result.total_unique_results} defects found")
        
    except Exception as e:
        print(f"❌ Synchronous analysis failed: {str(e)}")


async def pipeline_visualization_example():
    """
    Example of visualizing the pipeline structure.
    """
    print("\n" + "=" * 60)
    print("PIPELINE VISUALIZATION EXAMPLE")
    print("=" * 60)
    
    pipeline = DefectAnalysisPipeline()
    
    print("Pipeline information:")
    info = pipeline.get_pipeline_info()
    print(json.dumps(info, indent=2))
    
    print("\nPipeline stages:")
    for stage in info["stages"]:
        print(f"  - {stage}")
    
    # Note: Actual visualization would require matplotlib
    print("\nTo visualize the pipeline graph, call: pipeline.visualize()")


async def error_handling_example():
    """
    Example demonstrating error handling.
    """
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLE")
    print("=" * 60)
    
    # Create config with invalid agent name to test error handling
    config = DefectAnalysisConfig(
        agent_name="non_existent_agent",
        config_path="config/jk-gemba.yaml"
    )
    
    pipeline = DefectAnalysisPipeline(config)
    
    try:
        result = await pipeline.run("Test input for error handling")
        print(f"Unexpected success: {result}")
    except Exception as e:
        print(f"✅ Expected error caught: {str(e)}")
        print("The pipeline handles errors gracefully")


async def main():
    """
    Run all examples.
    """
    print("DEFECT ANALYSIS PIPELINE EXAMPLES")
    print("=" * 60)
    
    try:
        await basic_example()
        await custom_config_example()
        synchronous_example()
        await pipeline_visualization_example()
        await error_handling_example()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {str(e)}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
