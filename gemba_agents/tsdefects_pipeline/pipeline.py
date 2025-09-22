"""
Main TsDefects pipeline using pipefunc for orchestration.

This module provides the TsDefectsPipeline class that integrates both defect analysis
and agent processing functionality using TsSearch (Typesense) for vector operations.

The pipeline performs 4 stages:
1. Intent extraction from user input
2. Vector search using TsSearchClient
3. Result processing and deduplication
4. Agent enhancement with curator actions and rationale
"""

import logging
import time
from typing import Optional

from pipefunc import Pipeline

from .models.data_models import TsDefectsConfig, TsDefectsResult
from .stages.intent_extraction import extract_intent
from .stages.ts_vector_search import search_ts_vectors
from .stages.result_processing import process_ts_results
from .stages.agent_enhancement import enhance_with_agent

logger = logging.getLogger(__name__)


class TsDefectsPipeline:
    """
    Main TsDefects pipeline class.
    
    This class orchestrates the four stages of integrated defect analysis using pipefunc:
    1. Intent Extraction: Extract structured intent from user input
    2. TS Vector Search: Search for relevant defects using TsSearchClient
    3. Result Processing: Simple deduplication and validation
    4. Agent Enhancement: Add curator_action and rationale to each defect
    
    Example:
        >>> pipeline = TsDefectsPipeline()
        >>> result = await pipeline.run(
        ...     "The pump's loading/unloading piston is not operating smoothly"
        ... )
        >>> print(f"Found {result.total_results} enhanced defects")
        >>> for defect in result.enhanced_defects:
        ...     print(f"- {defect.defect_code}: {defect.curator_action}")
    """
    
    def __init__(self, config: Optional[TsDefectsConfig] = None):
        """
        Initialize the TsDefects pipeline.
        
        Args:
            config: Configuration for the pipeline. If None, uses default config.
        """
        self.config = config or TsDefectsConfig()
        
        # Create the pipefunc pipeline with all 4 stages
        self.pipeline = Pipeline(
            [extract_intent, search_ts_vectors, process_ts_results, enhance_with_agent],
            profile=True,  # Enable profiling for performance monitoring
            cache_type="lru" if self.config.enable_caching else None,
            cache_kwargs={"max_size": 256} if self.config.enable_caching else None
        )
        
        if self.config.enable_logging:
            logger.info("TsDefectsPipeline initialized successfully")
    
    async def run(self, user_input: str) -> TsDefectsResult:
        """
        Run the complete TsDefects pipeline.
        
        Args:
            user_input: Raw user input describing equipment issues
            
        Returns:
            TsDefectsResult containing the complete analysis with enhanced defects
            
        Raises:
            Exception: If pipeline execution fails
        """
        start_time = time.time()
        
        try:
            if self.config.enable_logging:
                logger.info(f"Starting TsDefects pipeline for: {user_input[:100]}...")
            
            # Run the pipeline
            runner = self.pipeline.map_async(
                inputs={
                    "user_input": user_input,
                    "config": self.config
                },
                storage="dict"  # Store results in memory
            )
            result = await runner.task
            
            # Extract results from each stage
            intent_data = result["intent_data"].output
            enhanced_defects = result["enhanced_results"].output
            
            execution_time = (time.time() - start_time) * 1000
            
            # Create final result object
            final_result = TsDefectsResult(
                original_input=user_input,
                intent_data=intent_data,
                total_results=len(enhanced_defects),
                enhanced_defects=enhanced_defects,
                processing_time_ms=execution_time,
                success=True,
                error_message=None
            )
            
            if self.config.enable_logging:
                logger.info(
                    f"Pipeline completed in {execution_time:.2f}ms. "
                    f"Found {final_result.total_results} enhanced defects"
                )
            
            return final_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Pipeline execution failed after {execution_time:.2f}ms: {str(e)}"
            logger.error(error_msg)
            
            # Return error result instead of raising
            # Create a default IntentData for error cases
            from gemba_agents.defect_analysis.models.data_models import IntentData
            default_intent = IntentData(
                interpreted_meaning=f"Pipeline failed: {str(e)}",
                component="Unknown",
                sub_component="Unknown",
                related_component="Unknown",
                issue="Unknown"
            )

            return TsDefectsResult(
                original_input=user_input,
                intent_data=default_intent,
                total_results=0,
                enhanced_defects=[],
                processing_time_ms=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def run_sync(self, user_input: str) -> TsDefectsResult:
        """
        Run the pipeline synchronously.
        
        Args:
            user_input: Raw user input describing equipment issues
            
        Returns:
            TsDefectsResult containing the complete analysis with enhanced defects
        """
        import asyncio
        
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run()
                raise RuntimeError(
                    "Cannot run sync version from within an async context. "
                    "Use the async run() method instead."
                )
            return loop.run_until_complete(self.run(user_input))
        except RuntimeError:
            # Create a new event loop for synchronous execution
            return asyncio.run(self.run(user_input))
    
    def visualize(self, **kwargs):
        """
        Visualize the pipeline structure.
        
        Args:
            **kwargs: Additional arguments passed to pipeline.visualize()
        """
        return self.pipeline.visualize(**kwargs)
    
    def print_profiling_stats(self):
        """
        Print profiling statistics for the pipeline.
        """
        return self.pipeline.print_profiling_stats()
    
    def get_pipeline_info(self) -> dict:
        """
        Get information about the pipeline configuration.
        
        Returns:
            Dictionary containing pipeline information
        """
        return {
            "stages": ["intent_extraction", "ts_vector_search", "result_processing", "agent_enhancement"],
            "config": self.config.model_dump(),
            "intent_agent": self.config.intent_agent_name,
            "processing_agent": self.config.processing_agent_name,
            "ts_search_base_url": self.config.ts_search_base_url,
            "caching_enabled": self.config.enable_caching,
            "logging_enabled": self.config.enable_logging,
            "parallel_search": self.config.parallel_search
        }


# Convenience function for quick pipeline execution
async def analyze_ts_defects(
    user_input: str,
    config: Optional[TsDefectsConfig] = None
) -> TsDefectsResult:
    """
    Convenience function to run TsDefects analysis with minimal setup.
    
    Args:
        user_input: Raw user input describing equipment issues
        config: Optional configuration. Uses defaults if not provided.
        
    Returns:
        TsDefectsResult containing the complete analysis with enhanced defects
        
    Example:
        >>> result = await analyze_ts_defects(
        ...     "The pump's loading/unloading piston is not operating smoothly"
        ... )
        >>> print(f"Found {result.total_results} defects")
        >>> for defect in result.enhanced_defects:
        ...     print(f"- {defect.defect_code}: {defect.curator_action}")
    """
    pipeline = TsDefectsPipeline(config)
    return await pipeline.run(user_input)


def analyze_ts_defects_sync(
    user_input: str,
    config: Optional[TsDefectsConfig] = None
) -> TsDefectsResult:
    """
    Synchronous convenience function to run TsDefects analysis.
    
    Args:
        user_input: Raw user input describing equipment issues
        config: Optional configuration. Uses defaults if not provided.
        
    Returns:
        TsDefectsResult containing the complete analysis with enhanced defects
        
    Example:
        >>> result = analyze_ts_defects_sync(
        ...     "The pump's loading/unloading piston is not operating smoothly"
        ... )
        >>> print(f"Found {result.total_results} defects")
        >>> for defect in result.enhanced_defects:
        ...     print(f"- {defect.defect_code}: {defect.curator_action}")
    """
    pipeline = TsDefectsPipeline(config)
    return pipeline.run_sync(user_input)
