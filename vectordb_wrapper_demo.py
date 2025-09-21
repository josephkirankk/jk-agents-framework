"""
Simple demo of VectorDB wrapper functionality.

This script demonstrates the basic usage of the VectorDB wrapper
for search and upsert operations.
"""

import asyncio
import os
from vectordb_wrapper import VectorDBClient, SearchRequest, UpsertRequest


async def demo():
    """Demonstrate VectorDB wrapper functionality."""
    print("🔍 VectorDB Wrapper Demo")
    print("=" * 40)
    
    # Set base URL (you can also set VECTORDB_BASE_URL environment variable)
    base_url = os.getenv("VECTORDB_BASE_URL", "http://localhost:8010")
    print(f"Using VectorDB API at: {base_url}")
    print()
    
    async with VectorDBClient(base_url=base_url) as client:
        # 1. Health Check
        print("1. 🏥 Health Check")
        try:
            health = await client.health_check()
            print(f"   Status: {health.status}")
            print(f"   Pinecone Connected: {health.pinecone_connected}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return
        print()
        
        # 2. Search Example
        print("2. 🔍 Search Example")
        try:
            search_request = SearchRequest(
                query="motor bearing failure",
                top_n=3,
                min_score=0.7
            )
            
            response = await client.search(search_request)
            print(f"   Query: '{response.query}'")
            print(f"   Found {response.total_results} results in {response.execution_time_ms}ms")
            
            for i, result in enumerate(response.results, 1):
                defect = result.defect
                print(f"   Result {i} (Score: {result.score:.1%}):")
                print(f"     Code: {defect.defect_code}")
                print(f"     Text: {defect.defect_text}")
                print(f"     Subsystem: {defect.subsystem}")
                print(f"     Severity: {defect.severity}")
                if defect.symptoms:
                    print(f"     Symptoms: {', '.join(defect.symptoms[:3])}")
                print()
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
        
        # 3. Upsert Example
        print("3. 📝 Upsert Example")
        try:
            upsert_request = UpsertRequest(
                defect_code="DEMO.HYDRAULIC.LEAK.001",
                defect_text="Hydraulic system leak causing pressure loss",
                subsystem="HYD",
                severity="Medium",
                symptoms=["visible fluid leak", "pressure drop", "pump noise"],
                detection_methods=["visual inspection", "pressure monitoring"],
                tags=["hydraulic", "leak", "pressure"],
                likely_root_causes=["seal failure", "hose damage", "fitting loose"],
                recommended_actions=["inspect seals", "check hoses", "tighten fittings"]
            )
            
            response = await client.upsert(upsert_request)
            print(f"   Success: {response.success}")
            print(f"   Message: {response.message}")
            print(f"   Operation: {response.operation}")
            print(f"   Defect Code: {response.defect_code}")
            
        except Exception as e:
            print(f"   ❌ Upsert failed: {e}")
        print()
        
        # 4. Search for the upserted defect
        print("4. 🔍 Search for Upserted Defect")
        try:
            response = await client.search_get(
                query="hydraulic leak pressure",
                top_n=2,
                min_score=0.5
            )
            
            print(f"   Found {response.total_results} results")
            for result in response.results:
                if "DEMO.HYDRAULIC" in result.defect.defect_code:
                    print(f"   ✅ Found our demo defect: {result.defect.defect_code}")
                    print(f"      Score: {result.score:.1%}")
                    break
            else:
                print("   ℹ️  Demo defect not found in top results")
                
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
    
    print()
    print("✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo())
