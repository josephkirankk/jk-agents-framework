"""
Main Pilger processing pipeline using pipefunc for orchestration.

This module provides the PilgerProcessingPipeline class that processes
DefectAnalysisPipeline results through the jk_pilger_new_entries_agent
for additional insights and actions.
"""

import logging
import time
from typing import Optional

from pipefunc import Pipeline

from gemba_agents.defect_analysis.models.data_models import AggregatedResults
from .models.data_models import PilgerProcessingConfig, PilgerProcessingResult
from .stages.agent_processing import process_with_pilger_agent

logger = logging.getLogger(__name__)


class PilgerProcessingPipeline:
    """
    Main Pilger processing pipeline class.
    
    This class processes DefectAnalysisPipeline results through the jk_pilger_new_entries_agent
    to provide additional insights and recommended actions. It's designed to work as a
    sequential step after the DefectAnalysisPipeline.
    
    Example:
        >>> from gemba_agents.defect_analysis import DefectAnalysisPipeline
        >>> from gemba_agents.pilger_processing import PilgerProcessingPipeline
        >>> 
        >>> # First stage: Defect analysis
        >>> defect_pipeline = DefectAnalysisPipeline()
        >>> defect_results = await defect_pipeline.run("The pump piston is not operating smoothly")
        >>> 
        >>> # Second stage: Pilger processing
        >>> pilger_pipeline = PilgerProcessingPipeline()
        >>> final_results = await pilger_pipeline.run(defect_results)
        >>> print(f"Additional insights: {len(final_results.processed_insights)}")
    """
    
    def __init__(self, config: Optional[PilgerProcessingConfig] = None):
        """
        Initialize the Pilger processing pipeline.
        
        Args:
            config: Configuration for the pipeline. If None, uses default config.
        """
        self.config = config or PilgerProcessingConfig()
        
        # Create the pipefunc pipeline with single stage
        self.pipeline = Pipeline(
            [process_with_pilger_agent],
            profile=True,  # Enable profiling for performance monitoring
            cache_type="lru" if self.config.enable_caching else None,
            cache_kwargs={"max_size": 128} if self.config.enable_caching else None
        )
        
        if self.config.enable_logging:
            logger.info("PilgerProcessingPipeline initialized successfully")
    
    async def run(self, defect_analysis: AggregatedResults) -> PilgerProcessingResult:
        """
        Run the complete Pilger processing pipeline.
        
        Args:
            defect_analysis: Results from DefectAnalysisPipeline
            
        Returns:
            PilgerProcessingResult containing the complete processing results
            
        Raises:
            Exception: If pipeline execution fails
        """
        start_time = time.time()
        
        try:
            if self.config.enable_logging:
                logger.info(f"Starting Pilger processing pipeline for defect analysis with {defect_analysis.total_unique_results} results")
            
            # Since we only have one async function in the pipeline and pipefunc
            # has issues with async functions in multiprocessing, we'll call it directly
            processing_result = await process_with_pilger_agent(
                defect_analysis=defect_analysis,
                config=self.config
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Create the final result object
            final_result = PilgerProcessingResult(**processing_result)
            
            if self.config.enable_logging:
                logger.info(
                    f"Pipeline completed in {execution_time:.2f}ms. "
                    f"Generated {len(final_result.processed_insights)} insights and "
                    f"{len(final_result.recommended_actions)} actions"
                )
            
            return final_result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Pipeline execution failed after {execution_time:.2f}ms: {str(e)}"
            logger.error(error_msg)

            # Return error result instead of raising
            return PilgerProcessingResult(
                success=False,
                pilger_agent_response={},
                processed_insights=[],
                recommended_actions=[],
                confidence_score=None,
                processing_time_ms=execution_time,
                agent_execution_time_ms=0.0,
                error_message=str(e)
            )
    
    def run_sync(self, defect_analysis: AggregatedResults) -> PilgerProcessingResult:
        """
        Run the pipeline synchronously.
        
        Args:
            defect_analysis: Results from DefectAnalysisPipeline
            
        Returns:
            PilgerProcessingResult containing the complete processing results
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
            return loop.run_until_complete(self.run(defect_analysis))
        except RuntimeError:
            # Create a new event loop for synchronous execution
            return asyncio.run(self.run(defect_analysis))
    
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
            "stages": ["agent_processing"],
            "config": self.config.model_dump(),
            "agent_name": self.config.agent_name,
            "caching_enabled": self.config.enable_caching,
            "logging_enabled": self.config.enable_logging,
            "timeout_seconds": self.config.timeout_seconds
        }


# Convenience function for quick pipeline execution
async def process_defect_analysis(
    defect_analysis: AggregatedResults,
    config: Optional[PilgerProcessingConfig] = None
) -> PilgerProcessingResult:
    """
    Convenience function to process defect analysis results with minimal setup.
    
    Args:
        defect_analysis: Results from DefectAnalysisPipeline
        config: Optional configuration. Uses defaults if not provided.
        
    Returns:
        PilgerProcessingResult containing the complete processing results
        
    Example:
        >>> from gemba_agents.defect_analysis import analyze_defect
        >>> from gemba_agents.pilger_processing import process_defect_analysis
        >>> 
        >>> defect_results = await analyze_defect("The pump piston is not operating smoothly")
        >>> pilger_results = await process_defect_analysis(defect_results)
        >>> print(f"Insights: {pilger_results.processed_insights}")
    """
    pipeline = PilgerProcessingPipeline(config)
    return await pipeline.run(defect_analysis)


def process_defect_analysis_sync(
    defect_analysis: AggregatedResults,
    config: Optional[PilgerProcessingConfig] = None
) -> PilgerProcessingResult:
    """
    Synchronous convenience function to process defect analysis results.
    
    Args:
        defect_analysis: Results from DefectAnalysisPipeline
        config: Optional configuration. Uses defaults if not provided.
        
    Returns:
        PilgerProcessingResult containing the complete processing results
        
    Example:
        >>> from gemba_agents.defect_analysis import analyze_defect_sync
        >>> from gemba_agents.pilger_processing import process_defect_analysis_sync
        >>> 
        >>> defect_results = analyze_defect_sync("The pump piston is not operating smoothly")
        >>> pilger_results = process_defect_analysis_sync(defect_results)
        >>> print(f"Actions: {pilger_results.recommended_actions}")
    """
    pipeline = PilgerProcessingPipeline(config)
    return pipeline.run_sync(defect_analysis)
