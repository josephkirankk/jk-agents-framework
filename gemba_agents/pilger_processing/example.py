"""
Example usage of the Pilger Processing Pipeline.

This script demonstrates how to use the PilgerProcessingPipeline to process
DefectAnalysisPipeline results through the jk_pilger_new_entries_agent.
"""

import asyncio
import logging
from typing import Optional

from gemba_agents.defect_analysis import DefectAnalysisPipeline, DefectAnalysisConfig
from .pipeline import PilgerProcessingPipeline, process_defect_analysis
from .models.data_models import PilgerProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_example():
    """
    Basic example showing sequential processing through both pipelines.
    """
    print("\n" + "=" * 60)
    print("BASIC PILGER PROCESSING EXAMPLE")
    print("=" * 60)
    
    user_input = "The pump's loading/unloading piston is not operating smoothly"
    
    try:
        # Stage 1: Defect Analysis
        print(f"\n🔍 Stage 1: Running DefectAnalysisPipeline...")
        defect_pipeline = DefectAnalysisPipeline()
        defect_results = await defect_pipeline.run(user_input)
        
        print(f"✅ Defect analysis completed:")
        print(f"   - Original input: {defect_results.original_input}")
        print(f"   - Component: {defect_results.intent_data.component}")
        print(f"   - Issue: {defect_results.intent_data.issue}")
        print(f"   - Unique results: {defect_results.total_unique_results}")
        print(f"   - Processing time: {defect_results.processing_time_ms:.2f}ms")
        
        # Stage 2: Pilger Processing
        print(f"\n🔧 Stage 2: Running PilgerProcessingPipeline...")
        pilger_pipeline = PilgerProcessingPipeline()
        pilger_results = await pilger_pipeline.run(defect_results)
        
        print(f"✅ Pilger processing completed:")
        print(f"   - Success: {pilger_results.success}")
        print(f"   - Insights: {len(pilger_results.processed_insights)}")
        print(f"   - Actions: {len(pilger_results.recommended_actions)}")
        print(f"   - Confidence: {pilger_results.confidence_score}")
        print(f"   - Processing time: {pilger_results.processing_time_ms:.2f}ms")
        print(f"   - Agent time: {pilger_results.agent_execution_time_ms:.2f}ms")
        
        if pilger_results.processed_insights:
            print(f"\n💡 Additional Insights:")
            for i, insight in enumerate(pilger_results.processed_insights, 1):
                print(f"   {i}. {insight}")
        
        if pilger_results.recommended_actions:
            print(f"\n🛠️ Additional Actions:")
            for i, action in enumerate(pilger_results.recommended_actions, 1):
                print(f"   {i}. {action}")
        
        return pilger_results
        
    except Exception as e:
        print(f"❌ Error in basic example: {e}")
        logger.error(f"Basic example failed: {e}")
        return None


async def convenience_function_example():
    """
    Example using convenience functions for streamlined processing.
    """
    print("\n" + "=" * 60)
    print("CONVENIENCE FUNCTION EXAMPLE")
    print("=" * 60)
    
    user_input = "Motor bearing overheating"
    
    try:
        # Import convenience functions
        from gemba_agents.defect_analysis import analyze_defect
        
        print(f"\n🚀 Processing with convenience functions...")
        print(f"Input: {user_input}")
        
        # Stage 1: Defect analysis
        defect_results = await analyze_defect(user_input)
        print(f"✅ Defect analysis: {defect_results.total_unique_results} results")
        
        # Stage 2: Pilger processing
        pilger_results = await process_defect_analysis(defect_results)
        print(f"✅ Pilger processing: {len(pilger_results.processed_insights)} insights")
        
        return pilger_results
        
    except Exception as e:
        print(f"❌ Error in convenience function example: {e}")
        logger.error(f"Convenience function example failed: {e}")
        return None


async def custom_configuration_example():
    """
    Example with custom configuration settings.
    """
    print("\n" + "=" * 60)
    print("CUSTOM CONFIGURATION EXAMPLE")
    print("=" * 60)
    
    user_input = "Hydraulic pump cavitation"
    
    try:
        # Custom configurations
        defect_config = DefectAnalysisConfig(
            top_n=5,
            min_score=0.7,
            enable_logging=True
        )
        
        pilger_config = PilgerProcessingConfig(
            format_for_agent="text",  # Use text format instead of JSON
            timeout_seconds=180,      # Extended timeout
            enable_caching=False      # Disable caching for this example
        )
        
        print(f"\n⚙️ Using custom configurations...")
        print(f"   - Defect analysis: top_n={defect_config.top_n}, min_score={defect_config.min_score}")
        print(f"   - Pilger processing: format={pilger_config.format_for_agent}, timeout={pilger_config.timeout_seconds}s")
        
        # Stage 1: Defect analysis with custom config
        defect_pipeline = DefectAnalysisPipeline(defect_config)
        defect_results = await defect_pipeline.run(user_input)
        
        print(f"✅ Defect analysis: {defect_results.total_unique_results} results")
        
        # Stage 2: Pilger processing with custom config
        pilger_pipeline = PilgerProcessingPipeline(pilger_config)
        pilger_results = await pilger_pipeline.run(defect_results)
        
        print(f"✅ Pilger processing: Success={pilger_results.success}")
        
        return pilger_results
        
    except Exception as e:
        print(f"❌ Error in custom configuration example: {e}")
        logger.error(f"Custom configuration example failed: {e}")
        return None


async def error_handling_example():
    """
    Example demonstrating error handling.
    """
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLE")
    print("=" * 60)
    
    try:
        # Create config with invalid agent name to test error handling
        config = PilgerProcessingConfig(
            agent_name="non_existent_agent",
            config_path="config/jk-gemba.yaml"
        )
        
        # Create mock defect analysis data for testing
        from gemba_agents.defect_analysis.models.data_models import IntentData, AggregatedResults
        
        intent_data = IntentData(
            interpreted_meaning="Test error handling",
            component="Test Component",
            sub_component="Test Sub-component",
            related_component="Unknown",
            issue="Test Issue"
        )
        
        mock_defect_results = AggregatedResults(
            original_input="Test input for error handling",
            intent_data=intent_data,
            total_unique_results=0,
            defects=[],
            root_causes=[],
            corrective_actions=[],
            processing_time_ms=100.0
        )
        
        pipeline = PilgerProcessingPipeline(config)
        
        print(f"\n🧪 Testing error handling with invalid agent...")
        result = await pipeline.run(mock_defect_results)
        
        if not result.success:
            print(f"✅ Expected error handled gracefully:")
            print(f"   - Success: {result.success}")
            print(f"   - Error: {result.error_message}")
            print(f"   - Original data preserved: {result.original_defect_analysis is not None}")
        else:
            print(f"⚠️ Unexpected success: {result}")
        
        return result
        
    except Exception as e:
        print(f"✅ Exception caught and handled: {str(e)}")
        logger.info(f"Expected error in error handling example: {e}")
        return None


def synchronous_example():
    """
    Example of synchronous processing.
    """
    print("\n" + "=" * 60)
    print("SYNCHRONOUS PROCESSING EXAMPLE")
    print("=" * 60)
    
    user_input = "Gear tooth broken"
    
    try:
        from gemba_agents.defect_analysis import analyze_defect_sync
        from .pipeline import process_defect_analysis_sync
        
        print(f"\n🔄 Running synchronous processing...")
        print(f"Input: {user_input}")
        
        # Synchronous processing
        defect_results = analyze_defect_sync(user_input)
        print(f"✅ Defect analysis (sync): {defect_results.total_unique_results} results")
        
        pilger_results = process_defect_analysis_sync(defect_results)
        print(f"✅ Pilger processing (sync): Success={pilger_results.success}")
        
        return pilger_results
        
    except Exception as e:
        print(f"❌ Error in synchronous example: {e}")
        logger.error(f"Synchronous example failed: {e}")
        return None


async def pipeline_info_example():
    """
    Example showing pipeline information and profiling.
    """
    print("\n" + "=" * 60)
    print("PIPELINE INFORMATION EXAMPLE")
    print("=" * 60)
    
    try:
        # Create pipelines
        defect_pipeline = DefectAnalysisPipeline()
        pilger_pipeline = PilgerProcessingPipeline()
        
        # Get pipeline information
        defect_info = defect_pipeline.get_pipeline_info()
        pilger_info = pilger_pipeline.get_pipeline_info()
        
        print(f"\n📊 DefectAnalysisPipeline Info:")
        print(f"   - Stages: {defect_info['stages']}")
        print(f"   - Caching: {defect_info['caching_enabled']}")
        print(f"   - Logging: {defect_info['logging_enabled']}")
        
        print(f"\n📊 PilgerProcessingPipeline Info:")
        print(f"   - Stages: {pilger_info['stages']}")
        print(f"   - Agent: {pilger_info['agent_name']}")
        print(f"   - Caching: {pilger_info['caching_enabled']}")
        print(f"   - Timeout: {pilger_info['timeout_seconds']}s")
        
        # Run a quick processing to generate profiling data
        user_input = "Test input for profiling"
        defect_results = await defect_pipeline.run(user_input)
        pilger_results = await pilger_pipeline.run(defect_results)
        
        print(f"\n⏱️ Performance Metrics:")
        print(f"   - Defect analysis: {defect_results.processing_time_ms:.2f}ms")
        print(f"   - Pilger processing: {pilger_results.processing_time_ms:.2f}ms")
        print(f"   - Agent execution: {pilger_results.agent_execution_time_ms:.2f}ms")
        
        # Print profiling stats (if available)
        print(f"\n📈 Profiling Statistics:")
        try:
            defect_pipeline.print_profiling_stats()
            pilger_pipeline.print_profiling_stats()
        except Exception as e:
            print(f"   Profiling stats not available: {e}")
        
        return pilger_results
        
    except Exception as e:
        print(f"❌ Error in pipeline info example: {e}")
        logger.error(f"Pipeline info example failed: {e}")
        return None


async def main():
    """
    Main function to run all examples.
    """
    print("🚀 Pilger Processing Pipeline Examples")
    print("=" * 60)
    
    examples = [
        ("Basic Example", basic_example),
        ("Convenience Functions", convenience_function_example),
        ("Custom Configuration", custom_configuration_example),
        ("Error Handling", error_handling_example),
        ("Pipeline Information", pipeline_info_example),
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n🔄 Running {name}...")
            result = await example_func()
            results[name] = result
            print(f"✅ {name} completed")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            results[name] = None
    
    # Run synchronous example separately
    try:
        print(f"\n🔄 Running Synchronous Example...")
        sync_result = synchronous_example()
        results["Synchronous Example"] = sync_result
        print(f"✅ Synchronous Example completed")
    except Exception as e:
        print(f"❌ Synchronous Example failed: {e}")
        results["Synchronous Example"] = None
    
    # Summary
    print(f"\n" + "=" * 60)
    print("EXAMPLES SUMMARY")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✅ Success" if result is not None else "❌ Failed"
        print(f"{status}: {name}")
    
    successful_count = sum(1 for result in results.values() if result is not None)
    total_count = len(results)
    
    print(f"\n📊 Overall: {successful_count}/{total_count} examples completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
