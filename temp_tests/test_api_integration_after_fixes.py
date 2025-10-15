#!/usr/bin/env python3
"""
Quick integration test to verify API still works after concurrency fixes.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_api_imports():
    """Test that API imports successfully."""
    print("\n🔍 Test: API imports...")
    try:
        import api
        print("✅ PASS: API module imported successfully")
        return True
    except Exception as e:
        print(f"❌ FAIL: Could not import API: {e}")
        return False


def test_fastapi_app_creation():
    """Test that FastAPI app is created."""
    print("\n🔍 Test: FastAPI app creation...")
    try:
        from api import app
        if app is None:
            print("❌ FAIL: FastAPI app is None")
            return False
        print(f"✅ PASS: FastAPI app created: {app.title}")
        return True
    except Exception as e:
        print(f"❌ FAIL: Could not create FastAPI app: {e}")
        return False


def test_performance_tracking_context():
    """Test that performance tracking context manager works."""
    print("\n🔍 Test: Performance tracking context...")
    try:
        import asyncio
        from api import track_performance
        
        async def test_tracking():
            async with track_performance("test_operation", "test_thread"):
                # Simulate some work
                await asyncio.sleep(0.001)
        
        asyncio.run(test_tracking())
        print("✅ PASS: Performance tracking works")
        return True
    except Exception as e:
        print(f"❌ FAIL: Performance tracking failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics_structure():
    """Test that metrics structure is correct."""
    print("\n🔍 Test: Metrics structure...")
    try:
        from api import _performance_metrics, _metrics_lock
        
        with _metrics_lock:
            required_keys = ["total_requests", "successful_requests", "failed_requests", 
                           "thread_contexts", "response_times", "memory_operations"]
            
            for key in required_keys:
                if key not in _performance_metrics:
                    print(f"❌ FAIL: Missing key in metrics: {key}")
                    return False
        
        print("✅ PASS: Metrics structure is correct")
        return True
    except Exception as e:
        print(f"❌ FAIL: Metrics structure check failed: {e}")
        return False


def test_cache_structure():
    """Test that cache structure is correct."""
    print("\n🔍 Test: Cache structure...")
    try:
        from api import _preloaded_cache, _cache_lock
        
        with _cache_lock:
            # Cache should be a dict
            if not isinstance(_preloaded_cache, dict):
                print(f"❌ FAIL: Cache is not a dict: {type(_preloaded_cache)}")
                return False
        
        print("✅ PASS: Cache structure is correct")
        return True
    except Exception as e:
        print(f"❌ FAIL: Cache structure check failed: {e}")
        return False


def test_file_storage_functionality():
    """Test basic file storage functionality."""
    print("\n🔍 Test: File storage functionality...")
    try:
        from app.file_storage_manager import get_file_storage_manager
        
        storage = get_file_storage_manager()
        
        # Store a test file
        ref_id = storage.store_file(
            filename="test.txt",
            content=b"test content",
            mime_type="text/plain",
            thread_id="test_thread"
        )
        
        # Retrieve it
        metadata = storage.get_file_metadata(ref_id)
        
        if metadata is None:
            print("❌ FAIL: Could not retrieve file metadata")
            return False
        
        if metadata["filename"] != "test.txt":
            print(f"❌ FAIL: Wrong filename: {metadata['filename']}")
            return False
        
        # Clean up
        storage.delete_file(ref_id)
        
        print(f"✅ PASS: File storage works (ref_id: {ref_id})")
        return True
    except Exception as e:
        print(f"❌ FAIL: File storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_integration_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("🔧 API INTEGRATION TESTS (After Concurrency Fixes)")
    print("=" * 70)
    
    tests = [
        ("API Imports", test_api_imports),
        ("FastAPI App Creation", test_fastapi_app_creation),
        ("Performance Tracking", test_performance_tracking_context),
        ("Metrics Structure", test_metrics_structure),
        ("Cache Structure", test_cache_structure),
        ("File Storage Functionality", test_file_storage_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ FAIL: {test_name} - Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("=" * 70)
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ API FUNCTIONALITY VERIFIED - All systems operational!")
        return True
    else:
        print(f"❌ {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
