"""
Example usage of the TsDefects pipeline.

This script demonstrates how to use the integrated TsDefects pipeline
for defect analysis with TsSearch and agent enhancement.
"""

import asyncio
import json
import logging
from pathlib import Path

# Handle both direct execution and module execution
try:
    # Try relative imports first (when run as module)
    from .pipeline import TsDefectsPipeline, analyze_ts_defects_sync
    from .models.data_models import TsDefectsConfig
except ImportError:
    # Fall back to absolute imports (when run directly)
    import sys

    # Add the project root to Python path
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    sys.path.insert(0, str(project_root))

    from gemba_agents.tsdefects_pipeline.pipeline import (
        TsDefectsPipeline,
        analyze_ts_defects_sync
    )
    from gemba_agents.tsdefects_pipeline.models.data_models import (
        TsDefectsConfig
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



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


async def main():
    """Run all examples."""
    print("TsDefects Pipeline Examples")
    print("=" * 50)
    
    # Run examples

    
    await custom_config_example()
    print("\n" + "=" * 50)
    
    print("All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
