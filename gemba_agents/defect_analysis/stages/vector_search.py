"""
Vector search stage for the defect analysis pipeline.

This stage performs vector search using the extracted intent data to find
relevant defects, root causes, and corrective actions from the vector database.
"""

import asyncio
import logging
import time
from typing import List, Set

from pipefunc import pipefunc
from vectordb_wrapper import VectorDBClient, SearchRequest

from ..models.data_models import IntentData, VectorSearchResults, DefectResult, DefectAnalysisConfig

logger = logging.getLogger(__name__)


async def _search_vectors_async(
    intent_data: IntentData,
    config: DefectAnalysisConfig = DefectAnalysisConfig()
) -> VectorSearchResults:
    """
    Perform vector search using extracted intent data.
    
    This function constructs search queries from the intent data and performs
    vector searches to find relevant defects, root causes, and corrective actions.
    Multiple searches are performed using different combinations of the extracted
    components and issues, then results are combined and deduplicated.
    
    Args:
        intent_data: Extracted intent data from the previous stage
        config: Configuration for the defect analysis pipeline
        
    Returns:
        VectorSearchResults object containing all search results
        
    Raises:
        Exception: If vector search fails
        
    Example:
        >>> intent = IntentData(
        ...     interpreted_meaning="Pump piston not operating smoothly",
        ...     component="Pump",
        ...     sub_component="Pump piston",
        ...     related_component="Air compressor",
        ...     issue="Not operating smoothly"
        ... )
        >>> results = await search_vectors(intent, config)
        >>> print(f"Found {results.total_results} results")
    """
    start_time = time.time()
    
    try:
        if config.enable_logging:
            logger.info(f"Starting vector search for component: {intent_data.component}")
        
        # Construct search queries from intent data
        search_queries = _construct_search_queries(intent_data)
        
        if config.enable_logging:
            logger.info(f"Constructed {len(search_queries)} search queries: {search_queries}")
        
        # Perform vector searches
        all_results = []
        total_execution_time = 0.0
        
        async with VectorDBClient(base_url=config.vectordb_base_url) as client:
            if config.parallel_search:
                # Perform searches in parallel
                search_tasks = [
                    _perform_single_search(client, query, config)
                    for query in search_queries
                ]
                search_responses = await asyncio.gather(*search_tasks, return_exceptions=True)
                
                for i, response in enumerate(search_responses):
                    if isinstance(response, Exception):
                        logger.warning(f"Search failed for query '{search_queries[i]}': {response}")
                        continue
                    
                    all_results.extend(response.results)
                    total_execution_time += response.execution_time_ms
            else:
                # Perform searches sequentially
                for query in search_queries:
                    try:
                        response = await _perform_single_search(client, query, config)
                        all_results.extend(response.results)
                        total_execution_time += response.execution_time_ms
                    except Exception as e:
                        logger.warning(f"Search failed for query '{query}': {e}")
                        continue
        
        # Convert search results to DefectResult objects and deduplicate
        defect_results = _convert_and_deduplicate_results(all_results)
        
        # Create final results object
        vector_results = VectorSearchResults(
            query_terms=search_queries,
            total_results=len(defect_results),
            execution_time_ms=total_execution_time,
            results=defect_results
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        if config.enable_logging:
            logger.info(
                f"Vector search completed in {execution_time:.2f}ms. "
                f"Found {len(defect_results)} unique results from {len(all_results)} total results"
            )
        
        return vector_results
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = f"Vector search failed after {execution_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        # Return empty results on failure
        return VectorSearchResults(
            query_terms=[],
            total_results=0,
            execution_time_ms=execution_time,
            results=[]
        )


def _construct_search_queries(intent_data: IntentData) -> List[str]:
    """
    Construct search queries from intent data.
    
    Args:
        intent_data: Extracted intent data
        
    Returns:
        List of search query strings
    """
    queries = []
    
    # Primary query using the interpreted meaning
    if intent_data.interpreted_meaning and intent_data.interpreted_meaning != "Unknown":
        queries.append(intent_data.interpreted_meaning)
    
    # Component-based queries
    if intent_data.component and intent_data.component != "Unknown":
        if intent_data.issue and intent_data.issue != "Unknown":
            queries.append(f"{intent_data.component} {intent_data.issue}")
        
        if intent_data.sub_component and intent_data.sub_component != "Unknown":
            queries.append(f"{intent_data.component} {intent_data.sub_component}")
            
            if intent_data.issue and intent_data.issue != "Unknown":
                queries.append(f"{intent_data.component} {intent_data.sub_component} {intent_data.issue}")
    
    # Related component queries
    if intent_data.related_component and intent_data.related_component != "Unknown":
        queries.append(intent_data.related_component)
        
        if intent_data.issue and intent_data.issue != "Unknown":
            queries.append(f"{intent_data.related_component} {intent_data.issue}")
    
    # Issue-based query
    if intent_data.issue and intent_data.issue != "Unknown":
        queries.append(intent_data.issue)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for query in queries:
        if query not in seen:
            seen.add(query)
            unique_queries.append(query)
    
    return unique_queries


async def _perform_single_search(client: VectorDBClient, query: str, config: DefectAnalysisConfig):
    """
    Perform a single vector search.
    
    Args:
        client: VectorDB client
        query: Search query string
        config: Configuration object
        
    Returns:
        Search response from the vector database
    """
    request = SearchRequest(
        query=query,
        top_n=config.top_n,
        min_score=config.min_score
    )
    
    return await client.search(request)


def _convert_and_deduplicate_results(search_results: List) -> List[DefectResult]:
    """
    Convert search results to DefectResult objects and remove duplicates.
    
    Args:
        search_results: Raw search results from vector database
        
    Returns:
        List of unique DefectResult objects
    """
    seen_codes: Set[str] = set()
    defect_results = []
    
    for result in search_results:
        # Extract defect data from the result
        defect_data = result.defect if hasattr(result, 'defect') else result
        
        # Create DefectResult object
        defect_result = DefectResult(
            id=getattr(result, 'id', ''),
            score=getattr(result, 'score', 0.0),
            defect_code=getattr(defect_data, 'defect_code', ''),
            defect_text=getattr(defect_data, 'defect_text', ''),
            subsystem=getattr(defect_data, 'subsystem', ''),
            severity=getattr(defect_data, 'severity', ''),
            symptoms=getattr(defect_data, 'symptoms', []),
            detection_methods=getattr(defect_data, 'detection_methods', []),
            tags=getattr(defect_data, 'tags', []),
            likely_root_causes=getattr(defect_data, 'likely_root_causes', []),
            recommended_actions=getattr(defect_data, 'recommended_actions', [])
        )
        
        # Deduplicate based on defect_code
        if defect_result.defect_code and defect_result.defect_code not in seen_codes:
            seen_codes.add(defect_result.defect_code)
            defect_results.append(defect_result)
    
    # Sort by score (highest first)
    defect_results.sort(key=lambda x: x.score, reverse=True)

    return defect_results


@pipefunc(output_name="search_results", cache=True)
def search_vectors(
    intent_data: IntentData,
    config: DefectAnalysisConfig = DefectAnalysisConfig()
) -> VectorSearchResults:
    """
    Synchronous wrapper for vector search.

    This function wraps the async vector search logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        intent_data: Extracted intent data from the previous stage
        config: Configuration for the defect analysis pipeline

    Returns:
        VectorSearchResults containing search results and metadata
    """
    import asyncio

    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _search_vectors_async(intent_data, config))
                return future.result()
        else:
            # We can use the existing loop
            return loop.run_until_complete(_search_vectors_async(intent_data, config))
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(_search_vectors_async(intent_data, config))
