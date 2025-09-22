"""
Test script for TsSearch client functionality.

This script tests the TsSearch client against a real TsSearch API server
running on localhost:3000. It performs comprehensive testing of search
functionality with different search types and parameters.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vectordb_wrapper.ts_client import TsSearchClient
from vectordb_wrapper.ts_models import TsSearchRequest, SearchType, TsSearchFilters
from vectordb_wrapper.ts_exceptions import TsSearchException

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_health_check():
    """Test the health check functionality."""
    print("\n" + "="*60)
    print("🏥 TESTING HEALTH CHECK")
    print("="*60)
    
    try:
        async with TsSearchClient() as client:
            health = await client.health_check()
            print(f"✅ Health Status: {health['status']}")
            print(f"   Server URL: {health['server_url']}")
            if health['status'] == 'healthy':
                print(f"   Response Time: {health['response_time_ms']}ms")
            else:
                print(f"   Error: {health.get('error', 'Unknown')}")
            return health['status'] == 'healthy'
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_basic_hybrid_search():
    """Test basic hybrid search functionality."""
    print("\n" + "="*60)
    print("🔍 TESTING BASIC HYBRID SEARCH")
    print("="*60)
    
    try:
        async with TsSearchClient() as client:
            # Test with POST method
            request = TsSearchRequest(
                query="bearing temperature",
                search_type=SearchType.HYBRID,
                limit=5
            )
            
            response = await client.search_post(request)
            
            print(f"✅ POST Search Results:")
            print(f"   Query: '{response.data.query}'")
            print(f"   Search Type: {response.data.search_type}")
            print(f"   Total Found: {response.data.total_found}")
            print(f"   Processing Time: {response.data.processing_time_ms}ms")
            print(f"   Results Returned: {len(response.data.results)}")
            
            # Display top results
            for i, result in enumerate(response.data.results[:3], 1):
                print(f"\n   Result {i} (Score: {result.score:.4f}):")
                print(f"     Code: {result.defect_code}")
                print(f"     Text: {result.defect_text[:100]}...")
                print(f"     Machine: {result.machine}, Subsystem: {result.subsystem}")
            
            return len(response.data.results) > 0
            
    except Exception as e:
        print(f"❌ Basic hybrid search failed: {e}")
        return False


async def test_get_search():
    """Test GET method search functionality."""
    print("\n" + "="*60)
    print("🔍 TESTING GET METHOD SEARCH")
    print("="*60)
    
    try:
        async with TsSearchClient() as client:
            response = await client.search_get(
                query="bearing temperature",
                search_type=SearchType.HYBRID,
                limit=3
            )
            
            print(f"✅ GET Search Results:")
            print(f"   Query: '{response.data.query}'")
            print(f"   Search Type: {response.data.search_type}")
            print(f"   Total Found: {response.data.total_found}")
            print(f"   Processing Time: {response.data.processing_time_ms}ms")
            print(f"   Results Returned: {len(response.data.results)}")
            
            return len(response.data.results) > 0
            
    except Exception as e:
        print(f"❌ GET search failed: {e}")
        return False


async def test_filtered_search():
    """Test search with filters."""
    print("\n" + "="*60)
    print("🔍 TESTING FILTERED SEARCH")
    print("="*60)
    
    try:
        async with TsSearchClient() as client:
            # Test with filters
            filters = TsSearchFilters(
                machine="PLG",
                subsystem="GBX"
            )
            
            request = TsSearchRequest(
                query="bearing",
                search_type=SearchType.HYBRID,
                limit=5,
                filters=filters
            )
            
            response = await client.search_post(request)
            
            print(f"✅ Filtered Search Results:")
            print(f"   Query: '{response.data.query}'")
            print(f"   Filters Applied: {response.data.filters_applied}")
            print(f"   Total Found: {response.data.total_found}")
            print(f"   Processing Time: {response.data.processing_time_ms}ms")
            
            # Verify all results match filters
            all_match = True
            for result in response.data.results:
                if result.machine != "PLG" or result.subsystem != "GBX":
                    all_match = False
                    break
            
            print(f"   Filter Compliance: {'✅ All results match filters' if all_match else '❌ Some results don\'t match filters'}")
            
            return len(response.data.results) > 0 and all_match
            
    except Exception as e:
        print(f"❌ Filtered search failed: {e}")
        return False


async def test_different_search_types():
    """Test different search types (keyword, vector, hybrid)."""
    print("\n" + "="*60)
    print("🔍 TESTING DIFFERENT SEARCH TYPES")
    print("="*60)
    
    results = {}
    query = "bearing overheating"
    
    for search_type in [SearchType.KEYWORD, SearchType.VECTOR, SearchType.HYBRID]:
        try:
            async with TsSearchClient() as client:
                request = TsSearchRequest(
                    query=query,
                    search_type=search_type,
                    limit=3
                )
                
                response = await client.search_post(request)
                results[search_type.value] = {
                    'total_found': response.data.total_found,
                    'processing_time_ms': response.data.processing_time_ms,
                    'results_count': len(response.data.results)
                }
                
                print(f"✅ {search_type.value.upper()} Search:")
                print(f"   Total Found: {response.data.total_found}")
                print(f"   Processing Time: {response.data.processing_time_ms}ms")
                print(f"   Results Returned: {len(response.data.results)}")
                
        except Exception as e:
            print(f"❌ {search_type.value.upper()} search failed: {e}")
            results[search_type.value] = None
    
    # Summary
    print(f"\n📊 Search Type Comparison for query: '{query}'")
    for search_type, result in results.items():
        if result:
            print(f"   {search_type.upper()}: {result['total_found']} found, {result['processing_time_ms']}ms")
        else:
            print(f"   {search_type.upper()}: FAILED")
    
    return all(result is not None for result in results.values())


async def test_score_thresholds():
    """Test search with score thresholds."""
    print("\n" + "="*60)
    print("🔍 TESTING SCORE THRESHOLDS")
    print("="*60)
    
    try:
        async with TsSearchClient() as client:
            # Test with similarity score threshold
            request = TsSearchRequest(
                query="bearing temperature",
                search_type=SearchType.HYBRID,
                limit=10,
                min_similarity_score=0.3
            )
            
            response = await client.search_post(request)
            
            print(f"✅ Score Threshold Search:")
            print(f"   Query: '{response.data.query}'")
            print(f"   Min Similarity Score: 0.3")
            print(f"   Total Found: {response.data.total_found}")
            print(f"   Results Returned: {len(response.data.results)}")
            
            # Check if all results meet threshold
            min_score = min(result.score for result in response.data.results) if response.data.results else 1.0
            print(f"   Lowest Score: {min_score:.4f}")
            
            return len(response.data.results) > 0
            
    except Exception as e:
        print(f"❌ Score threshold search failed: {e}")
        return False


async def test_error_handling():
    """Test error handling with invalid requests."""
    print("\n" + "="*60)
    print("🔍 TESTING ERROR HANDLING")
    print("="*60)
    
    try:
        async with TsSearchClient() as client:
            # Test with empty query (should fail validation)
            try:
                request = TsSearchRequest(
                    query="",  # Empty query should fail
                    search_type=SearchType.HYBRID,
                    limit=5
                )
                await client.search_post(request)
                print("❌ Empty query should have failed validation")
                return False
            except Exception as e:
                print(f"✅ Empty query correctly rejected: {type(e).__name__}")
            
            # Test with invalid limit
            try:
                request = TsSearchRequest(
                    query="test",
                    search_type=SearchType.HYBRID,
                    limit=200  # Over limit should fail
                )
                await client.search_post(request)
                print("❌ Over-limit should have failed validation")
                return False
            except Exception as e:
                print(f"✅ Over-limit correctly rejected: {type(e).__name__}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


async def run_comprehensive_tests():
    """Run all tests and provide a summary."""
    print("🚀 STARTING COMPREHENSIVE TSSEARCH CLIENT TESTS")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing against server: {os.getenv('HYBRID_SEARCH_BASE_URL', 'http://localhost:3000')}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Basic Hybrid Search", test_basic_hybrid_search),
        ("GET Method Search", test_get_search),
        ("Filtered Search", test_filtered_search),
        ("Different Search Types", test_different_search_types),
        ("Score Thresholds", test_score_thresholds),
        ("Error Handling", test_error_handling),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! TsSearch client is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())
