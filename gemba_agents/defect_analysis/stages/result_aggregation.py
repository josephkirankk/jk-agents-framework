"""
Result aggregation stage for the defect analysis pipeline.

This stage consolidates vector search results, removes duplicates, and creates
a structured final output with consolidated root causes and corrective actions.
"""

import json
import logging
import os
import time
from typing import List, Set, Dict
from collections import Counter

from pipefunc import pipefunc

from ..models.data_models import (
    IntentData,
    VectorSearchResults,
    AggregatedResults,
    DefectAnalysisConfig,
    RootCause,
    CorrectiveAction
)

logger = logging.getLogger(__name__)

# Cache for ontology mappings to avoid repeated file reads
_ontology_cache = None


def _load_ontology_mappings() -> Dict[str, Dict[str, str]]:
    """
    Load root cause and corrective action mappings from the ontology file.

    Returns:
        Dictionary with 'root_causes' and 'corrective_actions' mappings
    """
    global _ontology_cache

    if _ontology_cache is not None:
        return _ontology_cache

    try:
        # Get the path to the ontology file relative to the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, "..", "..", "..")
        ontology_path = os.path.join(project_root, "config", "prompts", "ontology_merged_detailed_v8.json")

        with open(ontology_path, 'r', encoding='utf-8') as f:
            ontology_data = json.load(f)

        # Create mappings from code to text
        root_cause_mapping = {}
        for rc in ontology_data.get('root_causes', []):
            root_cause_mapping[rc['root_cause_code']] = rc['root_cause_text']

        corrective_action_mapping = {}
        for ca in ontology_data.get('corrective_actions', []):
            corrective_action_mapping[ca['action_code']] = ca['action_text']

        _ontology_cache = {
            'root_causes': root_cause_mapping,
            'corrective_actions': corrective_action_mapping
        }

        logger.info(f"Loaded ontology mappings: {len(root_cause_mapping)} root causes, {len(corrective_action_mapping)} corrective actions")
        return _ontology_cache

    except Exception as e:
        logger.error(f"Failed to load ontology mappings: {str(e)}")
        # Return empty mappings on failure
        _ontology_cache = {
            'root_causes': {},
            'corrective_actions': {}
        }
        return _ontology_cache


async def _aggregate_results_async(
    user_input: str,
    intent_data: IntentData,
    search_results: VectorSearchResults,
    config: DefectAnalysisConfig = DefectAnalysisConfig()
) -> AggregatedResults:
    """
    Aggregate and consolidate vector search results.
    
    This function takes the vector search results and consolidates them into
    a final structured output. It removes duplicates, consolidates root causes
    and corrective actions, and provides a comprehensive summary of the analysis.
    
    Args:
        user_input: Original user input
        intent_data: Extracted intent data
        search_results: Vector search results
        config: Configuration for the defect analysis pipeline
        
    Returns:
        AggregatedResults object containing consolidated results
        
    Example:
        >>> results = await aggregate_results(
        ...     user_input="Pump piston not working",
        ...     intent_data=intent_data,
        ...     search_results=search_results,
        ...     config=config
        ... )
        >>> print(f"Found {results.total_unique_results} unique defects")
        >>> print(f"Root causes: {results.root_causes}")
    """
    start_time = time.time()
    
    try:
        if config.enable_logging:
            logger.info(f"Starting result aggregation for {len(search_results.results)} results")
        
        # The search results are already deduplicated in the vector search stage
        unique_defects = search_results.results
        
        # Consolidate root causes from all results
        root_causes = _consolidate_root_causes(unique_defects)
        
        # Consolidate corrective actions from all results
        corrective_actions = _consolidate_corrective_actions(unique_defects)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Create aggregated results
        aggregated_results = AggregatedResults(
            original_input=user_input,
            intent_data=intent_data,
            total_unique_results=len(unique_defects),
            defects=unique_defects,
            root_causes=root_causes,
            corrective_actions=corrective_actions,
            processing_time_ms=processing_time
        )
        
        if config.enable_logging:
            logger.info(
                f"Result aggregation completed in {processing_time:.2f}ms. "
                f"Consolidated {len(root_causes)} root causes and "
                f"{len(corrective_actions)} corrective actions"
            )
        
        return aggregated_results
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        error_msg = f"Result aggregation failed after {processing_time:.2f}ms: {str(e)}"
        logger.error(error_msg)
        
        # Return minimal results on failure
        return AggregatedResults(
            original_input=user_input,
            intent_data=intent_data,
            total_unique_results=0,
            defects=[],
            root_causes=[],
            corrective_actions=[],
            processing_time_ms=processing_time
        )


def _consolidate_root_causes(defects: List) -> List[RootCause]:
    """
    Consolidate root causes from all defect results into structured format.

    Args:
        defects: List of DefectResult objects

    Returns:
        List of consolidated RootCause objects with code and text, sorted by frequency
    """
    all_causes = []

    for defect in defects:
        if hasattr(defect, 'likely_root_causes') and defect.likely_root_causes:
            all_causes.extend(defect.likely_root_causes)

    if not all_causes:
        return []

    # Count frequency and remove duplicates
    cause_counts = Counter(all_causes)

    # Load ontology mappings
    ontology_mappings = _load_ontology_mappings()
    root_cause_mapping = ontology_mappings['root_causes']

    # Convert codes to structured objects
    consolidated_causes = []
    for cause_code, count in cause_counts.most_common():
        # Get the descriptive text from ontology, fallback to code if not found
        cause_text = root_cause_mapping.get(cause_code, f"Unknown root cause: {cause_code}")

        root_cause = RootCause(
            root_cause_code=cause_code,
            root_cause_text=cause_text
        )
        consolidated_causes.append(root_cause)

    return consolidated_causes


def _consolidate_corrective_actions(defects: List) -> List[CorrectiveAction]:
    """
    Consolidate corrective actions from all defect results into structured format.

    Args:
        defects: List of DefectResult objects

    Returns:
        List of consolidated CorrectiveAction objects with code and text, sorted by frequency
    """
    all_actions = []

    for defect in defects:
        if hasattr(defect, 'recommended_actions') and defect.recommended_actions:
            all_actions.extend(defect.recommended_actions)

    if not all_actions:
        return []

    # Count frequency and remove duplicates
    action_counts = Counter(all_actions)

    # Load ontology mappings
    ontology_mappings = _load_ontology_mappings()
    corrective_action_mapping = ontology_mappings['corrective_actions']

    # Convert codes to structured objects
    consolidated_actions = []
    for action_code, count in action_counts.most_common():
        # Get the descriptive text from ontology, fallback to code if not found
        action_text = corrective_action_mapping.get(action_code, f"Unknown corrective action: {action_code}")

        corrective_action = CorrectiveAction(
            action_code=action_code,
            action_text=action_text
        )
        consolidated_actions.append(corrective_action)

    return consolidated_actions


def _remove_similar_items(items: List[str], similarity_threshold: float = 0.8) -> List[str]:
    """
    Remove similar items from a list based on string similarity.
    
    This is a simple implementation that could be enhanced with more
    sophisticated similarity algorithms if needed.
    
    Args:
        items: List of strings to deduplicate
        similarity_threshold: Threshold for considering items similar
        
    Returns:
        List of unique items with similar ones removed
    """
    if not items:
        return []
    
    unique_items = []
    
    for item in items:
        is_similar = False
        
        for existing_item in unique_items:
            # Simple similarity check based on common words
            item_words = set(item.lower().split())
            existing_words = set(existing_item.lower().split())
            
            if item_words and existing_words:
                intersection = len(item_words.intersection(existing_words))
                union = len(item_words.union(existing_words))
                similarity = intersection / union if union > 0 else 0
                
                if similarity >= similarity_threshold:
                    is_similar = True
                    break
        
        if not is_similar:
            unique_items.append(item)

    return unique_items


@pipefunc(output_name="final_results", cache=True)
def aggregate_results(
    user_input: str,
    intent_data: IntentData,
    search_results: VectorSearchResults,
    config: DefectAnalysisConfig = DefectAnalysisConfig()
) -> AggregatedResults:
    """
    Synchronous wrapper for result aggregation.

    This function wraps the async result aggregation logic to make it compatible
    with pipefunc's synchronous execution model.

    Args:
        user_input: Original user input
        intent_data: Extracted intent data from the first stage
        search_results: Vector search results from the second stage
        config: Configuration for the defect analysis pipeline

    Returns:
        AggregatedResults containing the final consolidated analysis
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
                    _aggregate_results_async(user_input, intent_data, search_results, config)
                )
                return future.result()
        else:
            # We can use the existing loop
            return loop.run_until_complete(
                _aggregate_results_async(user_input, intent_data, search_results, config)
            )
    except RuntimeError:
        # No event loop exists, create a new one
        return asyncio.run(
            _aggregate_results_async(user_input, intent_data, search_results, config)
        )
