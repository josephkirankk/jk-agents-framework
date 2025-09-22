"""
Example usage of VectorDB wrapper.

This module provides example functions demonstrating how to use
the VectorDB wrapper for search and upsert operations.
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

try:
    # Try relative imports first (when run as module)
    from .client import VectorDBClient
    from .models import SearchRequest, UpsertRequest
    from .decorators import vectordb_wrapper, log_vectordb_operations
    from .utils import format_search_results, setup_logging
except ImportError:
    # Fall back to absolute imports (when run directly)
    # Add parent directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from vectordb_wrapper.client import VectorDBClient
    from vectordb_wrapper.models import SearchRequest, UpsertRequest
    from vectordb_wrapper.decorators import vectordb_wrapper, log_vectordb_operations
    from vectordb_wrapper.utils import format_search_results, setup_logging


# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)


async def basic_search_example():
    """Basic example of searching for defects."""
    async with VectorDBClient() as client:
        # Check health first
        health = await client.health_check()
        print(f"API Health: {health.status}")
        
        # Perform search
        request = SearchRequest(
            query="motor bearing failure",
            top_n=3,
            min_score=0.7
        )
        
        response = await client.search(request)
        print(f"Found {response.total_results} results in {response.execution_time_ms}ms")
        
        for result in response.results:
            print(f"- {result.defect.defect_code}: {result.defect.defect_text} (Score: {result.score:.1%})")


async def basic_upsert_example():
    """Basic example of upserting a defect."""
    async with VectorDBClient() as client:
        # Create upsert request
        request = UpsertRequest(
            defect_code="EX.PUMP.SEAL.LEAK.001",
            defect_text="Pump seal leakage causing fluid loss",
            subsystem="PMP",
            severity="High",
            symptoms=["visible fluid leakage", "reduced pressure"],
            detection_methods=["visual inspection", "pressure monitoring"],
            tags=["pump", "seal", "leakage"],
            likely_root_causes=["seal wear", "contamination"],
            recommended_actions=["replace seal", "check fluid"]
        )
        
        response = await client.upsert(request)
        print(f"Upsert result: {response.message}")
        print(f"Operation: {response.operation}")


@vectordb_wrapper(log_requests=True, log_responses=True)
async def decorated_search_example(client: VectorDBClient, query: str):
    """Example using the vectordb_wrapper decorator."""
    request = SearchRequest(query=query, top_n=5)
    response = await client.search(request)
    return response


@log_vectordb_operations(include_request_data=True)
async def logged_operation_example():
    """Example with detailed logging."""
    async with VectorDBClient() as client:
        # Search for hydraulic issues
        request = SearchRequest(
            query="hydraulic pump cavitation",
            top_n=3,
            min_score=0.6
        )
        
        response = await client.search(request)
        return response


async def batch_search_example():
    """Example of performing multiple searches."""
    queries = [
        "motor bearing failure",
        "hydraulic pump cavitation",
        "gear wear",
        "valve leakage",
        "sensor malfunction"
    ]
    
    async with VectorDBClient() as client:
        results = []
        
        for query in queries:
            print(f"Searching for: {query}")
            request = SearchRequest(query=query, top_n=2, min_score=0.7)
            response = await client.search(request)
            results.append({
                "query": query,
                "total_results": response.total_results,
                "execution_time_ms": response.execution_time_ms,
                "results": response.results
            })
        
        # Print summary
        print("\n=== Batch Search Summary ===")
        for result in results:
            print(f"Query: '{result['query']}' - {result['total_results']} results in {result['execution_time_ms']}ms")


async def comprehensive_example():
    """Comprehensive example showing various operations."""
    print("=== VectorDB Wrapper Comprehensive Example ===\n")
    
    async with VectorDBClient() as client:
        # 1. Health check
        print("1. Checking API health...")
        try:
            health = await client.health_check()
            print(f"   Status: {health.status}")
            print(f"   Message: {health.message}")
            print(f"   Pinecone Connected: {health.pinecone_connected}")
        except Exception as e:
            print(f"   Health check failed: {e}")
            return
        
        # 2. Upsert a new defect
        print("\n2. Upserting a new defect...")
        try:
            upsert_request = UpsertRequest(
                defect_code="TEST.MOTOR.OVERHEAT.001",
                defect_text="Motor overheating due to insufficient cooling",
                subsystem="MOT",
                severity="High",
                typical_frequency="Rare",
                symptoms=["excessive heat", "reduced performance", "unusual noise"],
                detection_methods=["temperature monitoring", "thermal imaging"],
                early_warning_signals=["slight temperature increase"],
                tags=["motor", "overheating", "cooling"],
                likely_root_causes=["blocked cooling vents", "fan failure", "overload"],
                recommended_actions=["check cooling system", "inspect fan", "reduce load"]
            )
            
            upsert_response = await client.upsert(upsert_request)
            print(f"   Result: {upsert_response.message}")
            print(f"   Operation: {upsert_response.operation}")
        except Exception as e:
            print(f"   Upsert failed: {e}")
        
        # 3. Search for the upserted defect
        print("\n3. Searching for motor overheating...")
        try:
            search_request = SearchRequest(
                query="motor overheating cooling",
                top_n=3,
                min_score=0.5
            )
            
            search_response = await client.search(search_request)
            print(f"   Found {search_response.total_results} results in {search_response.execution_time_ms}ms")
            
            for i, result in enumerate(search_response.results, 1):
                defect = result.defect
                print(f"   Result {i}:")
                print(f"     Code: {defect.defect_code}")
                print(f"     Text: {defect.defect_text}")
                print(f"     Score: {result.score:.1%}")
                print(f"     Severity: {defect.severity}")
                
        except Exception as e:
            print(f"   Search failed: {e}")
        
        # 4. Test GET search method
        print("\n4. Testing GET search method...")
        try:
            get_response = await client.search_get(
                query="bearing failure",
                top_n=2,
                min_score=0.7
            )
            print(f"   Found {get_response.total_results} results via GET method")
        except Exception as e:
            print(f"   GET search failed: {e}")


async def error_handling_example():
    """Example demonstrating error handling."""
    print("=== Error Handling Example ===\n")
    
    # Test with invalid base URL
    try:
        async with VectorDBClient(base_url="http://invalid-url:9999") as client:
            await client.health_check()
    except Exception as e:
        print(f"Expected connection error: {type(e).__name__}: {e}")
    
    # Test with invalid request data
    try:
        async with VectorDBClient() as client:
            # Invalid search request (empty query)
            request = SearchRequest(query="", top_n=5)
            await client.search(request)
    except Exception as e:
        print(f"Expected validation error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # Run examples
    print("Running VectorDB wrapper examples...\n")
    
    # Run basic examples
    asyncio.run(basic_search_example())
    print()
    asyncio.run(basic_upsert_example())
    print()
    
    # Run decorated example
    result = asyncio.run(decorated_search_example("Air compressor Not operating smoothly"))
    print(f"Decorated search found {result.total_results} results")
    print()
    
    # Run comprehensive example
    asyncio.run(comprehensive_example())
    print()
    
    # Run error handling example
    asyncio.run(error_handling_example())
