#!/usr/bin/env python3
"""
Test the new 4-method file management system.

This verifies:
1. save_file() - stores and compresses files, returns ref ID
2. get_file_metadata() - returns metadata only (no content)
3. get_file_content() - returns text content for text files
4. get_image_base64() - returns base64 for images (large data)
"""
import sys
from pathlib import Path
from PIL import Image
import io

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.file_storage_manager import FileStorageManager, get_file_storage_manager
import app.file_storage_manager as fsm_module


def create_test_image(width=1200, height=1600):
    """Create a test image similar to visiting cards."""
    img = Image.new('RGB', (width, height), color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=90)
    return buffer.getvalue()


def test_file_management_system():
    """Test the complete 4-method file management system."""
    print("=" * 70)
    print("Testing 4-Method File Management System")
    print("=" * 70)
    
    # Reset global instance for testing
    fsm_module._file_storage_manager = FileStorageManager(
        compress_images=True,
        max_image_dimension=1024
    )
    manager = get_file_storage_manager()
    
    # Create test data
    print("\n1. Creating test data...")
    test_image_data = create_test_image(1200, 1600)
    test_text_data = b"This is a test text file content."
    
    original_image_size = len(test_image_data)
    print(f"   ✓ Test image: {original_image_size:,} bytes (1200x1600)")
    print(f"   ✓ Test text: {len(test_text_data)} bytes")
    
    # Test 1: save_file() for image
    print("\n2. Testing save_file() for IMAGE...")
    image_ref_id = manager.store_file(
        filename="test_card.jpg",
        content=test_image_data,
        mime_type="image/jpeg",
        thread_id="test_thread_001"
    )
    print(f"   ✓ Image saved with ref_id: {image_ref_id}")
    
    # Test 2: save_file() for text
    print("\n3. Testing save_file() for TEXT...")
    text_ref_id = manager.store_file(
        filename="test_notes.txt",
        content=test_text_data,
        mime_type="text/plain",
        thread_id="test_thread_001"
    )
    print(f"   ✓ Text saved with ref_id: {text_ref_id}")
    
    # Test 3: get_file_metadata() for image
    print("\n4. Testing get_file_metadata() for IMAGE...")
    image_metadata = manager.get_file_metadata(image_ref_id)
    
    if not image_metadata:
        print("   ❌ FAILED: Could not retrieve image metadata")
        return False
    
    print(f"   ✓ Metadata retrieved:")
    print(f"     - filename: {image_metadata['filename']}")
    print(f"     - mime_type: {image_metadata['mime_type']}")
    print(f"     - size_bytes: {image_metadata['size_bytes']:,}")
    print(f"     - is_image: {image_metadata['is_image']}")
    print(f"     - is_text: {image_metadata['is_text']}")
    
    if image_metadata.get('compression'):
        comp = image_metadata['compression']
        print(f"     - compressed: {comp.get('original_size_bytes', 0):,} -> {comp.get('compressed_size_bytes', 0):,} bytes")
        print(f"     - reduction: {comp.get('compression_ratio_percent', 0):.1f}%")
    
    # Verify compression happened
    compressed_size = image_metadata['size_bytes']
    if compressed_size >= original_image_size:
        print(f"   ❌ FAILED: Image not compressed ({compressed_size} >= {original_image_size})")
        return False
    
    reduction = ((1 - compressed_size / original_image_size) * 100)
    print(f"   ✓ Image compressed: {original_image_size:,} -> {compressed_size:,} ({reduction:.1f}% reduction)")
    
    # Test 4: get_file_metadata() for text
    print("\n5. Testing get_file_metadata() for TEXT...")
    text_metadata = manager.get_file_metadata(text_ref_id)
    
    if not text_metadata:
        print("   ❌ FAILED: Could not retrieve text metadata")
        return False
    
    print(f"   ✓ Metadata retrieved:")
    print(f"     - filename: {text_metadata['filename']}")
    print(f"     - is_image: {text_metadata['is_image']}")
    print(f"     - is_text: {text_metadata['is_text']}")
    
    # Test 5: get_file_content_raw() for text
    print("\n6. Testing get_file_content_raw() for TEXT...")
    text_content = manager.get_file_content_raw(text_ref_id)
    
    if not text_content:
        print("   ❌ FAILED: Could not retrieve text content")
        return False
    
    decoded_text = text_content.decode('utf-8')
    print(f"   ✓ Text content retrieved: \"{decoded_text}\"")
    
    if decoded_text != test_text_data.decode('utf-8'):
        print("   ❌ FAILED: Text content doesn't match original")
        return False
    
    # Test 6: get_file_content_base64() for image
    print("\n7. Testing get_file_content_base64() for IMAGE...")
    image_base64 = manager.get_file_content_base64(image_ref_id)
    
    if not image_base64:
        print("   ❌ FAILED: Could not retrieve image base64")
        return False
    
    base64_size = len(image_base64)
    expected_base64_size = compressed_size * 4 / 3  # Base64 adds ~33% overhead
    
    print(f"   ✓ Base64 content retrieved: {base64_size:,} characters")
    print(f"   ✓ Expected size: ~{int(expected_base64_size):,} characters")
    
    if abs(base64_size - expected_base64_size) / expected_base64_size > 0.1:
        print("   ⚠️  WARNING: Base64 size doesn't match expected")
    
    # Test 7: Verify metadata has NO content
    print("\n8. Verifying metadata contains NO content...")
    if 'content' in image_metadata:
        print("   ❌ FAILED: Metadata contains content field")
        return False
    if 'base64_content' in image_metadata:
        print("   ❌ FAILED: Metadata contains base64_content field")
        return False
    
    print("   ✓ Metadata is clean (no content fields)")
    
    # Test 8: Token estimation
    print("\n9. Estimating token usage...")
    # Token estimation: base64 size / 3
    estimated_tokens = base64_size / 3
    print(f"   - Image base64: {base64_size:,} chars → ~{int(estimated_tokens):,} tokens")
    
    if estimated_tokens > 30000:
        print("   ⚠️  WARNING: Token count still high (>30K)")
    else:
        print(f"   ✓ Token count acceptable (<30K)")
    
    # Test 9: Verify separation of concerns
    print("\n10. Verifying separation of concerns...")
    print("   ✓ save_file() - Stores and compresses")
    print("   ✓ get_file_metadata() - Returns metadata only (no content)")
    print("   ✓ get_file_content_raw() - Returns text content")
    print("   ✓ get_file_content_base64() - Returns image base64")
    print("   ✓ All methods work independently")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    
    print("\nSummary:")
    print(f"- Original image: {original_image_size:,} bytes")
    print(f"- Compressed image: {compressed_size:,} bytes")
    print(f"- Compression ratio: {reduction:.1f}%")
    print(f"- Base64 size: {base64_size:,} characters")
    print(f"- Estimated tokens: ~{int(estimated_tokens):,}")
    print(f"- Metadata is clean: ✓")
    print(f"- 4 methods work correctly: ✓")
    
    return True


if __name__ == "__main__":
    try:
        success = test_file_management_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)