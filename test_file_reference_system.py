#!/usr/bin/env python3
"""
Test File Reference System

Validates that files are properly stored with reference IDs and can be retrieved by agents.
"""
import sys
import time
import requests
import json
from pathlib import Path

def test_file_storage():
    """Test file storage and retrieval system."""
    print("=" * 70)
    print("File Reference System Test")
    print("=" * 70)
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code != 200:
            print("❌ API server not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ API server not running. Start with: python api.py")
        return False
    
    print("✅ API server is running\n")
    
    # Test 1: Upload files and verify reference IDs
    print("Test 1: File Upload with Reference IDs")
    print("-" * 70)
    
    image_path1 = "/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"
    image_path2 = "/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"
    
    # Check if test files exist
    if not Path(image_path1).exists():
        print(f"⚠️  Test file not found: {image_path1}")
        print("   Skipping file upload test")
        return False
    
    if not Path(image_path2).exists():
        print(f"⚠️  Test file not found: {image_path2}")
        print("   Using only first image")
        files = [('file', open(image_path1, 'rb'))]
    else:
        files = [
            ('file', open(image_path1, 'rb')),
            ('file', open(image_path2, 'rb'))
        ]
    
    try:
        print(f"📤 Uploading {len(files)} file(s)...")
        
        response = requests.post(
            "http://localhost:8000/v1/query",
            data={
                'question': 'Extract complete data including company research',
                'config_name': 'visiting_card_extractor.yaml'
            },
            files=files,
            timeout=180
        )
        
        # Close file handles
        for _, f in files:
            f.close()
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
        
        result = response.json()
        
        # Check if files were processed
        if 'metadata' in result and 'file_info' in result['metadata']:
            file_info = result['metadata']['file_info']
            print(f"✅ Files processed: {len(file_info)}")
            
            for i, info in enumerate(file_info, 1):
                print(f"\nFile {i}:")
                print(f"  - Filename: {info.get('filename', 'N/A')}")
                print(f"  - Reference ID: {info.get('reference_id', 'N/A')}")
                print(f"  - Size: {info.get('size_bytes', 0)} bytes")
                print(f"  - MIME Type: {info.get('mime_type', 'N/A')}")
            
            # Check if OCR agent was able to access files
            if result.get('success'):
                response_text = result.get('response', '')
                
                if 'Please provide the image' in response_text or 'no company name' in response_text.lower():
                    print("\n⚠️  WARNING: OCR agent didn't access files!")
                    print("   Agent asked for images or reported no data")
                    print("   This indicates files were not retrieved via reference IDs")
                    return False
                else:
                    print("\n✅ OCR agent successfully accessed files!")
                    print(f"   Response preview: {response_text[:200]}...")
            else:
                print("\n❌ Extraction failed")
                print(f"   Error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("⚠️  No file_info in metadata")
            print(f"Metadata: {result.get('metadata', {})}")
            return False
        
        print("\n" + "=" * 70)
        print("✅ File Reference System Test PASSED")
        print("=" * 70)
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>180s)")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_storage_manager():
    """Test FileStorageManager directly."""
    print("\n" + "=" * 70)
    print("FileStorageManager Unit Test")
    print("=" * 70)
    
    try:
        from app.file_storage_manager import get_file_storage_manager
        
        manager = get_file_storage_manager()
        
        # Test 1: Store a file
        print("\nTest 1: Store file")
        test_content = b"Test file content for visiting card"
        ref_id = manager.store_file(
            filename="test_card.txt",
            content=test_content,
            mime_type="text/plain",
            thread_id="test_thread_123"
        )
        print(f"✅ Stored file with reference_id: {ref_id}")
        
        # Test 2: Retrieve file
        print("\nTest 2: Retrieve file")
        file_ref = manager.get_file(ref_id)
        if file_ref and file_ref.content == test_content:
            print(f"✅ Retrieved file successfully")
            print(f"   Filename: {file_ref.filename}")
            print(f"   Size: {file_ref.size_bytes} bytes")
        else:
            print("❌ File retrieval failed")
            return False
        
        # Test 3: List thread files
        print("\nTest 3: List thread files")
        files = manager.list_files("test_thread_123")
        if len(files) == 1 and files[0]['reference_id'] == ref_id:
            print(f"✅ Listed {len(files)} file(s) for thread")
        else:
            print(f"❌ Expected 1 file, got {len(files)}")
            return False
        
        # Test 4: Get stats
        print("\nTest 4: Storage stats")
        stats = manager.get_stats()
        print(f"   Total files: {stats['total_files']}")
        print(f"   Total size: {stats['total_size_mb']} MB")
        print(f"   Threads: {stats['total_threads']}")
        
        # Test 5: Delete file
        print("\nTest 5: Delete file")
        deleted = manager.delete_file(ref_id)
        if deleted:
            print(f"✅ Deleted file successfully")
        else:
            print("❌ File deletion failed")
            return False
        
        print("\n✅ All FileStorageManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ FileStorageManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔍 Testing File Reference System Implementation\n")
    
    # Run unit tests first
    unit_test_passed = test_file_storage_manager()
    
    if not unit_test_passed:
        print("\n❌ Unit tests failed. Fix FileStorageManager before testing API.")
        sys.exit(1)
    
    # Run integration test
    integration_test_passed = test_file_storage()
    
    if integration_test_passed:
        print("\n✅ All tests passed! File reference system is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed. Check the logs above for details.")
        sys.exit(1)
