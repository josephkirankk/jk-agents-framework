"""
TsSearch vector search stage for the TsDefects pipeline.

This stage performs vector search using the extracted intent data to find
relevant defects using TsSearchClient. It replaces the VectorDB-based search
with TsSearch (Typesense) operations.
"""

import asyncio
import logging
import time
from typing import List

from pipefunc import pipefunc
from vectordb_wrapper import TsSearchClient, TsSearchRequest, SearchType

from gemba_agents.defect_analysis.models.data_models import IntentData
from ..models.data_models import TsDefectsConfig, TsSearchResults

logger = logging.getLogger(__name__)


async def _search_ts_vectors_async(
    intent_data: IntentData,
    config: TsDefectsConfig = TsDefectsConfig()
) -> TsSearchResults:
    """
    Perform vector search using TsSearchClient with extracted intent data.
    
    This function constructs search queries from the intent data and performs
    TsSearch operations to find relevant defects. Multiple searches are performed 
    using different combinations of the extracted components and issues, then 
    results are combined and deduplicated.
    
    Args:
        intent_data: Extracted intent data from the previous stage
        config: Configuration for the TsDefects pipeline
        
    Returns:
        TsSearchResults object containing all search results
        
    Raises:
        Exception: If TsSearch fails
        
    Example:
        >>> intent = IntentData(
        ...     interpreted_meaning="Pump piston not operating smoothly",
        ...     component="Pump",
        ...     sub_component="Pump piston",
        ...     related_component="Air compressor",
        ...     issue="Not operating smoothly"
        ... )
        >>> results = await search_ts_vectors(intent, config)
        >>> print(f"Found {results.total_results} results")
    """
    start_time = time.time()
    
    try:
        if config.enable_logging:
            logger.info(f"Starting TsSearch for component: {intent_data.component}")
        
        # Construct search queries from intent data
        search_queries = _construct_search_queries(intent_data)
        
        if config.enable_logging:
            logger.info(f"Constructed {len(search_queries)} search queries: {search_queries}")
        
        # Perform TsSearch operations
        all_results = []
        total_execution_time = 0.0
        
        async with TsSearchClient(base_url=config.ts_search_base_url) as client:
            if config.parallel_search:
                # Perform searches in parallel
                search_tasks = [
                    _perform_single_ts_search(client, query, config)
                    for query in search_queries
                ]
                search_responses = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for i, response in enumerate(search_responses):
                    if isinstance(response, Exception):
                        logger.warning(f"TsSearch failed for query '{search_queries[i]}': {response}")
                        continue
                    
                    all_results.extend(response.data.results)
                    total_execution_time += response.data.processing_time_ms
            else:
                # Perform searches sequentially
                for query in search_queries:
                    try:
                        response = await _perform_single_ts_search(client, query, config)
                        all_results.extend(response.data.results)
                        total_execution_time += response.data.processing_time_ms
                    except Exception as e:
                        logger.warning(f"TsSearch failed for query '{query}': {e}")
                        continue
        
        # Deduplicate results based on TsDefectResult.id
        unique_results = _deduplicate_ts_results(all_results)
        
        # Create final results object
        ts_results = TsSearchResults(
            query_terms=search_queries,
            total_results=len(unique_results),
            execution_time_ms=total_execution_time,
            results=unique_results
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        if config.enable_logging:
            logger.info(
                f"TsSearch completed in {execution_time:.2f}ms. "
                f"Found {len(unique_results)} unique results from {len(all_results)} total results"
            )
        
        return ts_results
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"TsSearch failed after {execution_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        # Return empty results on failure
        return TsSearchResults(
            query_terms=[],
            total_results=0,
            execution_time_ms=execution_time,
            results=[]
        )


def _construct_search_queries(intent_data: IntentData) -> List[str]:
    """
    Construct search queries from intent data.

    Creates a maximum of 2 queries based on the following logic:
    1. If component, sub_component, and issue are not null,
       add "<component> <sub-component> <issue>"
    2. If related_component is not null, add "<related_component> <issue>"

    Args:
        intent_data: Extracted intent data

    Returns:
        List of search query strings (max 2 queries)
    """
    queries = []

    # Query 1: Component + Sub-component + Issue (skip null fields)
    query_parts = []
    if intent_data.component and intent_data.component != "null":
        query_parts.append(intent_data.component)
    if intent_data.sub_component and intent_data.sub_component != "null":
        query_parts.append(intent_data.sub_component)
    if intent_data.issue and intent_data.issue != "null":
        query_parts.append(intent_data.issue)

    if query_parts:
        queries.append(" ".join(query_parts))

    # Query 2: Related component + Issue (if related_component is not null)
    if (intent_data.related_component and
            intent_data.related_component != "null" and
            intent_data.issue and intent_data.issue != "null"):
        queries.append(f"{intent_data.related_component} {intent_data.issue}")

    return queries


async def _perform_single_ts_search(client: TsSearchClient, query: str, config: TsDefectsConfig):
    """
    Perform a single TsSearch operation.
    
    Args:
        client: TsSearchClient instance
        query: Search query string
        config: Configuration object
        
    Returns:
        TsSearchResponse from the search operation
    """
    request = TsSearchRequest(
        query=query,
        search_type=SearchType.HYBRID,
        limit=config.search_limit,
        collection=config.collection,
        min_similarity_score=config.min_similarity_score
    )
    
    return await client.search(request)


def _deduplicate_ts_results(search_results: List) -> List:
    """
    Deduplicate TsSearch results based on TsDefectResult.id.
    
    Args:
        search_results: List of TsDefectResult objects from TsSearch
        
    Returns:
        List of unique TsDefectResult objects sorted by score
    """
    seen_ids = set()
    unique_results = []
    
    for result in search_results:
        # Use TsDefectResult.id for deduplication
        if result.id and result.id not in seen_ids:
            seen_ids.add(result.id)
            unique_results.append(result)
    
    # Sort by score (highest first)
    unique_results.sort(key=lambda x: x.score, reverse=True)

    return unique_results


@pipefunc(output_name="ts_search_results", cache=True)
def search_ts_vectors(
    intent_data: IntentData,
    config: TsDefectsConfig = TsDefectsConfig()
) -> TsSearchResults:
    """
    Synchronous wrapper for TsSearch vector search.

    This function wraps the async TsSearch logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        intent_data: Extracted intent data from the previous stage
        config: Configuration for the TsDefects pipeline

    Returns:
        TsSearchResults containing search results and metadata
    """
    import asyncio

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _search_ts_vectors_async(intent_data, config))
                return future.result()
        else:
            # We can use the existing loop
            return loop.run_until_complete(_search_ts_vectors_async(intent_data, config))
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(_search_ts_vectors_async(intent_data, config))
