"""
Result processing stage for the TsDefects pipeline.

This stage performs simple processing and deduplication of TsSearch results.
Unlike the original defect_analysis pipeline, this does not perform complex
aggregation or ontology mapping - it simply ensures unique results and
maintains the TsDefectResult structure intact.
"""

import logging
import time
from typing import List

from pipefunc import pipefunc
from vectordb_wrapper.ts_models import TsDefectResult

from gemba_agents.defect_analysis.models.data_models import IntentData
from ..models.data_models import TsDefectsConfig, TsSearchResults

logger = logging.getLogger(__name__)


async def _process_ts_results_async(
    intent_data: IntentData,
    ts_search_results: TsSearchResults,
    config: TsDefectsConfig = TsDefectsConfig()
) -> List[TsDefectResult]:
    """
    Process and deduplicate TsSearch results.
    
    This function takes the TsSearch results and performs simple processing:
    - Ensures deduplication (already done in search stage, but double-check)
    - Maintains TsDefectResult structure intact
    - Sorts results by relevance score
    
    Args:
        intent_data: Extracted intent data (for context/logging)
        ts_search_results: TsSearch results from the previous stage
        config: Configuration for the TsDefects pipeline
        
    Returns:
        List of processed TsDefectResult objects
        
    Example:
        >>> results = await process_ts_results(
        ...     intent_data=intent_data,
        ...     ts_search_results=search_results,
        ...     config=config
        ... )
        >>> print(f"Processed {len(results)} unique defects")
    """
    start_time = time.time()
    
    try:
        if config.enable_logging:
            logger.info(f"Starting result processing for {len(ts_search_results.results)} TsSearch results")
        
        # The search results should already be deduplicated in the search stage,
        # but we'll double-check to ensure uniqueness based on TsDefectResult.id
        seen_ids = set()
        unique_results = []
        
        for result in ts_search_results.results:
            if result.id not in seen_ids:
                seen_ids.add(result.id)
                unique_results.append(result)
            elif config.enable_logging:
                logger.debug(f"Duplicate result found and skipped: {result.id}")
        
        # Sort by score (highest first) to ensure best results are first
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        if config.enable_logging:
            logger.info(
                f"Result processing completed in {processing_time:.2f}ms. "
                f"Processed {len(unique_results)} unique results "
                f"(removed {len(ts_search_results.results) - len(unique_results)} duplicates)"
            )
        
        return unique_results
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        error_msg = f"Result processing failed after {processing_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        # Return empty results on failure
        return []


def _validate_ts_defect_result(result: TsDefectResult) -> bool:
    """
    Validate a TsDefectResult object to ensure it has required fields.
    
    Args:
        result: TsDefectResult object to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Check for required fields
        if not result.id:
            logger.warning("TsDefectResult missing required 'id' field")
            return False
        
        if not result.defect_code:
            logger.warning(f"TsDefectResult {result.id} missing required 'defect_code' field")
            return False
        
        if not result.defect_text:
            logger.warning(f"TsDefectResult {result.id} missing required 'defect_text' field")
            return False
        
        # Check score is valid
        if not isinstance(result.score, (int, float)) or result.score < 0:
            logger.warning(f"TsDefectResult {result.id} has invalid score: {result.score}")
            return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Error validating TsDefectResult: {e}")
        return False


@pipefunc(output_name="processed_results", cache=True)
def process_ts_results(
    intent_data: IntentData,
    ts_search_results: TsSearchResults,
    config: TsDefectsConfig = TsDefectsConfig()
) -> List[TsDefectResult]:
    """
    Synchronous wrapper for result processing.

    This function wraps the async result processing logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        intent_data: Extracted intent data from the first stage
        ts_search_results: TsSearch results from the second stage
        config: Configuration for the TsDefects pipeline

    Returns:
        List of processed TsDefectResult objects
    """
    import asyncio

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    _process_ts_results_async(intent_data, ts_search_results, config)
                )
                return future.result()
        else:
            # We can use the existing loop
            return loop.run_until_complete(
                _process_ts_results_async(intent_data, ts_search_results, config)
            )
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(
            _process_ts_results_async(intent_data, ts_search_results, config)
        )
