"""
Main defect analysis pipeline using pipefunc for orchestration.

This module provides the DefectAnalysisPipeline class that orchestrates
the three stages of defect analysis: intent extraction, vector search,
and result aggregation.
"""

import logging
import time
from typing import Optional

from pipefunc import Pipeline

from .models.data_models import DefectAnalysisConfig, AggregatedResults
from .stages.intent_extraction import extract_intent
from .stages.vector_search import search_vectors
from .stages.result_aggregation import aggregate_results

logger = logging.getLogger(__name__)


class DefectAnalysisPipeline:
    """
    Main defect analysis pipeline class.
    
    This class orchestrates the three stages of defect analysis using pipefunc:
    1. Intent Extraction: Extract structured intent from user input
    2. Vector Search: Search for relevant defects using intent data
    3. Result Aggregation: Consolidate and deduplicate results
    
    Example:
        >>> pipeline = DefectAnalysisPipeline()
        >>> result = await pipeline.run(
        ...     "The pump's loading/unloading piston is not operating smoothly"
        ... )
        >>> print(f"Found {result.total_unique_results} defects")
    """
    
    def __init__(self, config: Optional[DefectAnalysisConfig] = None):
        """
        Initialize the defect analysis pipeline.
        
        Args:
            config: Configuration for the pipeline. If None, uses default config.
        """
        self.config = config or DefectAnalysisConfig()
        
        # Create the pipefunc pipeline
        self.pipeline = Pipeline(
            [extract_intent, search_vectors, aggregate_results],
            profile=True,  # Enable profiling for performance monitoring
            cache_type="lru" if self.config.enable_caching else None,
            cache_kwargs={"max_size": 256} if self.config.enable_caching else None
        )
        
        if self.config.enable_logging:
            logger.info("DefectAnalysisPipeline initialized successfully")
    
    async def run(self, user_input: str) -> AggregatedResults:
        """
        Run the complete defect analysis pipeline.
        
        Args:
            user_input: Raw user input describing equipment issues
            
        Returns:
            AggregatedResults containing the complete analysis
            
        Raises:
            Exception: If pipeline execution fails
        """
        start_time = time.time()
        
        try:
            if self.config.enable_logging:
                logger.info(f"Starting defect analysis pipeline for: {user_input[:100]}...")
            
            # Run the pipeline
            runner = self.pipeline.map_async(
                inputs={
                    "user_input": user_input,
                    "config": self.config
                },
                storage="dict"  # Store results in memory
            )
            result = await runner.task
            
            # Extract the final result
            final_results = result["final_results"].output
            
            execution_time = (time.time() - start_time) * 1000
            
            if self.config.enable_logging:
                logger.info(
                    f"Pipeline completed in {execution_time:.2f}ms. "
                    f"Found {final_results.total_unique_results} unique defects"
                )
            
            return final_results
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Pipeline execution failed after {execution_time:.2f}ms: {str(e)}"
            logger.error(error_msg)
            raise
    
    def run_sync(self, user_input: str) -> AggregatedResults:
        """
        Run the pipeline synchronously.
        
        Args:
            user_input: Raw user input describing equipment issues
            
        Returns:
            AggregatedResults containing the complete analysis
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
            "stages": ["intent_extraction", "vector_search", "result_aggregation"],
            "config": self.config.model_dump(),
            "caching_enabled": self.config.enable_caching,
            "logging_enabled": self.config.enable_logging,
            "parallel_search": self.config.parallel_search
        }


# Convenience function for quick pipeline execution
async def analyze_defect(
    user_input: str,
    config: Optional[DefectAnalysisConfig] = None
) -> AggregatedResults:
    """
    Convenience function to run defect analysis with minimal setup.
    
    Args:
        user_input: Raw user input describing equipment issues
        config: Optional configuration. Uses defaults if not provided.
        
    Returns:
        AggregatedResults containing the complete analysis
        
    Example:
        >>> result = await analyze_defect(
        ...     "The pump's loading/unloading piston is not operating smoothly"
        ... )
        >>> print(result.intent_data.component)  # "Pump"
    """
    pipeline = DefectAnalysisPipeline(config)
    return await pipeline.run(user_input)


def analyze_defect_sync(
    user_input: str,
    config: Optional[DefectAnalysisConfig] = None
) -> AggregatedResults:
    """
    Synchronous convenience function to run defect analysis.
    
    Args:
        user_input: Raw user input describing equipment issues
        config: Optional configuration. Uses defaults if not provided.
        
    Returns:
        AggregatedResults containing the complete analysis
        
    Example:
        >>> result = analyze_defect_sync(
        ...     "The pump's loading/unloading piston is not operating smoothly"
        ... )
        >>> print(result.intent_data.component)  # "Pump"
    """
    pipeline = DefectAnalysisPipeline(config)
    return pipeline.run_sync(user_input)
