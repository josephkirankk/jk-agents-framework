"""
TsSearch Client Example

This script demonstrates how to use the TsSearchClient for searching defects
using the Typesense API with hybrid, keyword, and vector search capabilities.
"""

import asyncio
import logging
import os
from datetime import datetime

from vectordb_wrapper import (
    TsSearchClient,
    TsSearchRequest,
    TsSearchFilters,
    SearchType,
    TsSearchException
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_search_example():
    """Basic example of searching for defects using hybrid search."""
    print("\n" + "="*60)
    print("🔍 BASIC HYBRID SEARCH EXAMPLE")
    print("="*60)
    
    async with TsSearchClient() as client:
        # Check health first
        health = await client.health_check()
        print(f"API Health: {health['status']}")
        
        # Perform basic hybrid search
        request = TsSearchRequest(
            query="bearing temperature problems",
            search_type=SearchType.HYBRID,
            limit=5
        )
        
        response = await client.search(request)
        print(f"Found {response.data.total_found} results in {response.data.processing_time_ms}ms")
        
        for i, result in enumerate(response.data.results, 1):
            print(f"\nResult {i} (Score: {result.score:.4f}):")
            print(f"  Code: {result.defect_code}")
            print(f"  Text: {result.defect_text}")
            print(f"  Machine: {result.machine}, Subsystem: {result.subsystem}")
            print(f"  Component: {result.component}, Type: {result.defect_type}")


async def filtered_search_example():
    """Example of searching with filters."""
    print("\n" + "="*60)
    print("🔍 FILTERED SEARCH EXAMPLE")
    print("="*60)
    
    async with TsSearchClient() as client:
        # Search with filters
        filters = TsSearchFilters(
            machine="PLG",
            subsystem="GBX",
            component="BEARING"
        )
        
        request = TsSearchRequest(
            query="overheating",
            search_type=SearchType.HYBRID,
            limit=3,
            filters=filters
        )
        
        response = await client.search(request)
        print(f"Filtered search found {response.data.total_found} results")
        print(f"Filters applied: {response.data.filters_applied}")
        
        for result in response.data.results:
            print(f"  - {result.defect_code}: {result.defect_text[:80]}...")


async def get_method_example():
    """Example using GET method for simple searches."""
    print("\n" + "="*60)
    print("🔍 GET METHOD SEARCH EXAMPLE")
    print("="*60)
    
    async with TsSearchClient() as client:
        # Simple GET search
        response = await client.search_get(
            query="gear wear",
            search_type=SearchType.KEYWORD,
            limit=3,
            machine="PLG"
        )
        
        print(f"GET search found {response.data.total_found} results")
        
        for result in response.data.results:
            print(f"  - {result.defect_code}: {result.defect_text[:80]}...")


async def compare_search_types_example():
    """Example comparing different search types."""
    print("\n" + "="*60)
    print("🔍 SEARCH TYPE COMPARISON EXAMPLE")
    print("="*60)
    
    query = "bearing noise vibration"
    
    async with TsSearchClient() as client:
        for search_type in [SearchType.KEYWORD, SearchType.VECTOR, SearchType.HYBRID]:
            request = TsSearchRequest(
                query=query,
                search_type=search_type,
                limit=3
            )
            
            response = await client.search(request)
            
            print(f"\n{search_type.value.upper()} Search:")
            print(f"  Found: {response.data.total_found} results")
            print(f"  Time: {response.data.processing_time_ms}ms")
            
            for result in response.data.results[:2]:  # Show top 2
                print(f"    - {result.defect_code} (Score: {result.score:.4f})")


async def score_threshold_example():
    """Example using score thresholds."""
    print("\n" + "="*60)
    print("🔍 SCORE THRESHOLD EXAMPLE")
    print("="*60)
    
    async with TsSearchClient() as client:
        # Search with similarity score threshold
        request = TsSearchRequest(
            query="hydraulic pump problems",
            search_type=SearchType.HYBRID,
            limit=10,
            min_similarity_score=0.2
        )
        
        response = await client.search(request)
        
        print(f"Search with min similarity score 0.2:")
        print(f"  Found: {response.data.total_found} results")
        
        if response.data.results:
            scores = [r.score for r in response.data.results]
            print(f"  Score range: {min(scores):.4f} - {max(scores):.4f}")
            
            for result in response.data.results[:3]:
                print(f"    - {result.defect_code} (Score: {result.score:.4f})")


async def error_handling_example():
    """Example of error handling."""
    print("\n" + "="*60)
    print("🔍 ERROR HANDLING EXAMPLE")
    print("="*60)
    
    async with TsSearchClient() as client:
        try:
            # This should work fine
            request = TsSearchRequest(
                query="valid search",
                search_type=SearchType.HYBRID,
                limit=5
            )
            response = await client.search(request)
            print(f"✅ Valid search succeeded: {response.data.total_found} results")
            
        except TsSearchException as e:
            print(f"❌ Search failed: {e}")
        
        try:
            # Test with invalid parameters (this will be caught by Pydantic)
            request = TsSearchRequest(
                query="test",
                search_type=SearchType.HYBRID,
                limit=200  # Over the limit
            )
            response = await client.search(request)
            
        except Exception as e:
            print(f"✅ Invalid parameters correctly rejected: {type(e).__name__}")


async def main():
    """Run all examples."""
    print("🚀 TSSEARCH CLIENT EXAMPLES")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server URL: {os.getenv('HYBRID_SEARCH_BASE_URL', 'http://localhost:3000')}")
    
    examples = [
        basic_search_example,
        filtered_search_example,
        get_method_example,
        compare_search_types_example,
        score_threshold_example,
        error_handling_example
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example {example.__name__} failed: {e}")
    
    print("\n" + "="*80)
    print("✅ All examples completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
