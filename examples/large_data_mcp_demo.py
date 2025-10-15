#!/usr/bin/env python3
"""
Large Data MCP Server - Practical Demo

This script demonstrates how to use the Large Data MCP Server
to efficiently handle large datasets without flooding the LLM context.

Features demonstrated:
1. Generating large datasets
2. Storing datasets efficiently
3. Retrieving previews vs full data
4. Token savings comparison
5. Storage management
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.memory.large_data_storage import LargeDataStorage


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def demo_basic_storage():
    """Demo 1: Basic storage and retrieval"""
    print_section("DEMO 1: Basic Storage and Retrieval")
    
    # Initialize storage
    storage = LargeDataStorage({
        "sqlite_path": "./examples/demo_data/large_data_storage.db",
        "file_path": "./examples/demo_data/large_files/",
        "compression": True,
        "max_sqlite_size_mb": 50
    })
    
    # Generate sample dataset
    print("📊 Generating sample dataset (1000 customer records)...")
    customers = [
        {
            "id": i,
            "name": f"Customer {i}",
            "email": f"customer{i}@example.com",
            "city": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"][i % 5],
            "orders": [
                {"order_id": j, "amount": j * 100.5, "product": f"Product {j}"}
                for j in range(5)
            ]
        }
        for i in range(1000)
    ]
    
    # Store the dataset
    print("💾 Storing dataset in database...")
    storage_info = storage.store_large_data(
        reference_id="demo_customers_001",
        tool_name="demo_script",
        data=customers,
        metadata={
            "description": "Sample customer dataset with orders",
            "record_count": len(customers)
        }
    )
    
    print(f"✅ Dataset stored successfully!")
    print(f"   Reference ID: demo_customers_001")
    print(f"   Size: {storage_info.size_mb:.2f} MB")
    print(f"   Storage Type: {storage_info.storage_type}")
    print(f"   Compressed: {storage_info.compressed}")
    
    # Retrieve the dataset
    print("\n📥 Retrieving dataset...")
    retrieved_data = storage.retrieve_large_data("demo_customers_001")
    
    print(f"✅ Dataset retrieved successfully!")
    print(f"   Records: {len(retrieved_data)}")
    print(f"   First record: {json.dumps(retrieved_data[0], indent=2)}")
    
    return storage


def demo_token_savings(storage: LargeDataStorage):
    """Demo 2: Token savings comparison"""
    print_section("DEMO 2: Token Savings Comparison")
    
    # Retrieve the dataset
    full_data = storage.retrieve_large_data("demo_customers_001")
    
    # Calculate full data size
    full_json = json.dumps(full_data)
    full_size = len(full_json)
    full_tokens = full_size // 4  # Rough estimate: 1 token ≈ 4 characters
    
    # Create preview (what the MCP server returns)
    preview_response = {
        "status": "success",
        "reference_id": "demo_customers_001",
        "description": "Sample customer dataset with orders",
        "preview": full_data[:5],  # First 5 records
        "total_count": len(full_data),
        "size_mb": 0.5,
        "message": "Dataset stored successfully!"
    }
    
    preview_json = json.dumps(preview_response)
    preview_size = len(preview_json)
    preview_tokens = preview_size // 4
    
    # Calculate savings
    token_savings = full_tokens - preview_tokens
    savings_percent = (token_savings / full_tokens) * 100
    
    print("📊 Token Usage Comparison:")
    print(f"\n   Full Dataset:")
    print(f"   - Size: {full_size:,} characters")
    print(f"   - Estimated Tokens: {full_tokens:,}")
    print(f"   - Cost Impact: HIGH 💰💰💰")
    
    print(f"\n   Preview + Reference:")
    print(f"   - Size: {preview_size:,} characters")
    print(f"   - Estimated Tokens: {preview_tokens:,}")
    print(f"   - Cost Impact: LOW 💰")
    
    print(f"\n   💡 Savings:")
    print(f"   - Token Reduction: {token_savings:,} tokens")
    print(f"   - Percentage Saved: {savings_percent:.1f}%")
    print(f"   - Cost Reduction: ~{savings_percent:.1f}%")
    
    print(f"\n   🎯 Result: Using the Large Data MCP Server saves {savings_percent:.1f}% of tokens!")


def demo_storage_management(storage: LargeDataStorage):
    """Demo 3: Storage management and statistics"""
    print_section("DEMO 3: Storage Management")
    
    # Store a few more datasets for demonstration
    print("📊 Creating additional datasets for demo...")
    
    # Small dataset
    small_data = [{"id": i, "value": i * 10} for i in range(50)]
    storage.store_large_data(
        reference_id="demo_small_001",
        tool_name="demo_script",
        data=small_data,
        metadata={"description": "Small test dataset"}
    )
    
    # Large dataset
    large_data = [
        {
            "id": i,
            "data": "x" * 1000,  # Make it larger
            "nested": {"field1": i, "field2": i * 2}
        }
        for i in range(5000)
    ]
    storage.store_large_data(
        reference_id="demo_large_001",
        tool_name="demo_script",
        data=large_data,
        metadata={"description": "Large test dataset"}
    )
    
    # Get storage statistics
    print("\n📈 Storage Statistics:")
    stats = storage.get_storage_stats()
    
    print(f"\n   Total Datasets: {stats['total_references']}")
    print(f"   Total Size: {stats['total_size_mb']:.2f} MB")
    
    if stats['storage_breakdown']:
        print(f"\n   Storage Breakdown:")
        for key, info in stats['storage_breakdown'].items():
            print(f"   - {key}:")
            print(f"     • Count: {info['count']}")
            print(f"     • Total: {info['total_mb']:.2f} MB")
            print(f"     • Average: {info['avg_mb']:.2f} MB")
    
    # List all datasets
    print("\n📋 Stored Datasets:")
    references = storage.list_references(limit=10)
    
    for i, ref in enumerate(references, 1):
        print(f"\n   {i}. {ref['reference_id']}")
        print(f"      - Tool: {ref['tool_name']}")
        print(f"      - Size: {ref['size_mb']:.2f} MB ({ref['size_category']})")
        print(f"      - Storage: {ref['storage_type']}")
        print(f"      - Created: {ref['created_at']}")


def demo_preview_vs_full(storage: LargeDataStorage):
    """Demo 4: Preview vs Full Retrieval"""
    print_section("DEMO 4: Preview vs Full Retrieval")
    
    print("🔍 Scenario: Analyzing a dataset")
    print("\n   Step 1: Get preview to understand structure")
    
    # Simulate getting metadata (what get_dataset_preview would return)
    cursor = storage.conn.execute("""
        SELECT tool_name, size_bytes, size_category, storage_type, 
               content_type, compressed, metadata, created_at, access_count
        FROM large_tool_data 
        WHERE reference_id = ?
    """, ("demo_customers_001",))
    
    row = cursor.fetchone()
    if row:
        tool_name, size_bytes, size_category, storage_type, content_type, compressed, metadata_json, created_at, access_count = row
        metadata = json.loads(metadata_json)
        
        print(f"\n   Preview Information:")
        print(f"   - Description: {metadata.get('description', 'N/A')}")
        print(f"   - Size: {size_bytes / (1024 * 1024):.2f} MB")
        print(f"   - Records: {metadata.get('record_count', 'N/A')}")
        print(f"   - Storage: {storage_type}")
        print(f"   - Compressed: {compressed}")
        print(f"   - Access Count: {access_count}")
    
    # Get sample data
    full_data = storage.retrieve_large_data("demo_customers_001")
    preview = full_data[:3]
    
    print(f"\n   Sample Records (3 of {len(full_data)}):")
    for i, record in enumerate(preview, 1):
        print(f"\n   Record {i}:")
        print(f"   {json.dumps(record, indent=6)}")
    
    print(f"\n   💡 Decision: Based on preview, we can see the structure.")
    print(f"      If we need full analysis, we can retrieve the complete dataset.")
    print(f"      Otherwise, we work with the preview to save tokens!")


def demo_cleanup(storage: LargeDataStorage):
    """Demo 5: Cleanup and maintenance"""
    print_section("DEMO 5: Cleanup and Maintenance")
    
    print("🧹 Running cleanup of expired datasets...")
    cleanup_result = storage.cleanup_expired_data()
    
    print(f"\n   Cleanup Results:")
    print(f"   - Records Cleaned: {cleanup_result['cleaned_records']}")
    print(f"   - Files Cleaned: {cleanup_result['cleaned_files']}")
    
    if cleanup_result['cleaned_records'] == 0:
        print(f"\n   ℹ️  No expired datasets found (all datasets are recent)")
        print(f"      Datasets expire after 48 hours by default")
    
    print(f"\n   💡 Best Practice: Run cleanup regularly to free storage space")


def main():
    """Run all demos"""
    print("\n" + "🚀 "*20)
    print("   LARGE DATA MCP SERVER - PRACTICAL DEMONSTRATION")
    print("🚀 "*20)
    
    # Create demo data directory
    Path("./examples/demo_data").mkdir(parents=True, exist_ok=True)
    Path("./examples/demo_data/large_files").mkdir(parents=True, exist_ok=True)
    
    try:
        # Run demos
        storage = demo_basic_storage()
        demo_token_savings(storage)
        demo_storage_management(storage)
        demo_preview_vs_full(storage)
        demo_cleanup(storage)
        
        # Final summary
        print_section("SUMMARY")
        print("✅ All demos completed successfully!")
        print("\n   Key Takeaways:")
        print("   1. Large datasets are stored efficiently in database")
        print("   2. Token savings of 99%+ for large datasets")
        print("   3. Data persists across sessions")
        print("   4. Preview-first approach saves tokens")
        print("   5. Easy storage management and cleanup")
        
        print("\n   Next Steps:")
        print("   - Try the demo configuration: config/large_data_mcp_demo.yaml")
        print("   - Read the documentation: docs/LARGE_DATA_MCP_SERVER.md")
        print("   - Run integration tests: test_large_data_mcp_integration.py")
        
        print("\n" + "🎉 "*20)
        print("   Thank you for trying the Large Data MCP Server!")
        print("🎉 "*20 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

