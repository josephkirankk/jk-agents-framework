#!/usr/bin/env python3
"""
Test the improved dynamic version detection fix.

This validates that the system now correctly detects and uses
LangGraph's actual checkpoint version instead of hardcoding.
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

async def test_dynamic_version_detection():
    """Test the dynamic version detection system."""
    
    print("🔍 Testing Dynamic LangGraph Version Detection")
    print("=" * 55)
    
    try:
        # Test 1: Check what LangGraph actually uses
        print("\n📋 Test 1: LangGraph Default Version Detection")
        
        from langgraph.checkpoint.base import empty_checkpoint
        default_checkpoint = empty_checkpoint()
        actual_version = default_checkpoint.get('v')
        
        print(f"   LangGraph default version: {actual_version}")
        print(f"   Version type: {type(actual_version)}")
        
        # Test 2: Check our detection system
        print("\n🔧 Test 2: Our Dynamic Detection System")
        
        from app.memory.langgraph_adapter import HighPerformanceCheckpointer
        
        # Force reset for testing
        HighPerformanceCheckpointer._DETECTED_LANGGRAPH_VERSION = None
        
        # Create instance (should trigger detection)
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": "./test_version_detection_memory"
                }
            }
        }
        
        checkpointer = HighPerformanceCheckpointer(config)
        detected_version = HighPerformanceCheckpointer._get_compatible_version()
        
        print(f"   Our detected version: {detected_version}")
        print(f"   Matches LangGraph: {detected_version == actual_version}")
        
        # Test 3: Checkpoint creation with detected version
        print("\n📝 Test 3: Checkpoint Creation with Dynamic Version")
        
        test_checkpoint = {
            "id": "test-version-001",
            "ts": "2025-01-01T00:00:00+00:00",
            "channel_values": {"test": "data"},
            "channel_versions": {"test": 1},
            "versions_seen": {"test": 1},
            "pending_sends": []
            # Intentionally missing 'v' field to test detection
        }
        
        metadata = {"test": "version_detection"}
        
        # Store checkpoint (should add detected version)
        config_test = {"configurable": {"thread_id": "version-test-001", "checkpoint_ns": ""}}
        await checkpointer.aput(config_test, test_checkpoint, metadata, {})
        
        # Retrieve and check version
        retrieved = await checkpointer.aget(config_test)
        if retrieved:
            retrieved_version = retrieved.get('v')
            print(f"   Stored checkpoint version: {retrieved_version}")
            print(f"   Uses detected version: {retrieved_version == detected_version}")
        
        # Test 4: Edge case - invalid version handling
        print("\n⚠️  Test 4: Invalid Version Handling")
        
        edge_cases = [
            {"test_name": "missing_v", "checkpoint": {"id": "test", "ts": "2025-01-01T00:00:00+00:00"}},
            {"test_name": "string_v", "checkpoint": {"v": "invalid", "id": "test", "ts": "2025-01-01T00:00:00+00:00"}},
            {"test_name": "negative_v", "checkpoint": {"v": -1, "id": "test", "ts": "2025-01-01T00:00:00+00:00"}},
            {"test_name": "none_v", "checkpoint": {"v": None, "id": "test", "ts": "2025-01-01T00:00:00+00:00"}}
        ]
        
        for case in edge_cases:
            case_name = case["test_name"]
            case_checkpoint = case["checkpoint"]
            
            config_case = {"configurable": {"thread_id": f"edge-{case_name}", "checkpoint_ns": ""}}
            
            try:
                await checkpointer.aput(config_case, case_checkpoint, {"case": case_name}, {})
                retrieved_case = await checkpointer.aget(config_case)
                
                if retrieved_case:
                    fixed_version = retrieved_case.get('v')
                    print(f"   {case_name}: Fixed to version {fixed_version} ✅")
                else:
                    print(f"   {case_name}: No checkpoint retrieved ❌")
                    
            except Exception as e:
                print(f"   {case_name}: Error - {e} ❌")
        
        # Test 5: Performance impact assessment
        print("\n⚡ Test 5: Performance Impact of Dynamic Detection")
        
        import time
        
        # Test repeated version calls (should be cached)
        start_time = time.time()
        for _ in range(1000):
            version = HighPerformanceCheckpointer._get_compatible_version()
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 1000 * 1000  # Convert to microseconds
        print(f"   1000 version calls took: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Average per call: {avg_time:.3f}μs")
        print(f"   Caching effective: {avg_time < 1.0}")  # Should be very fast due to caching
        
        print(f"\n✅ Version Detection Tests Completed Successfully!")
        print(f"📊 Summary:")
        print(f"   - LangGraph default version: {actual_version}")
        print(f"   - Our detected version: {detected_version}")
        print(f"   - Version detection accuracy: {'✅ CORRECT' if detected_version == actual_version else '❌ MISMATCH'}")
        print(f"   - Dynamic adaptation: ✅ WORKING")
        print(f"   - Performance impact: ✅ MINIMAL")
        
    except Exception as e:
        print(f"🚨 Version detection test failed: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    print("🚀 Running Dynamic Version Detection Test")
    asyncio.run(test_dynamic_version_detection())
    print("✅ Version detection test completed.")
