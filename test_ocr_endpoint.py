"""
Test script for the /ocr/fast endpoint

This script tests the fast OCR API endpoint with sample images.
"""

import requests
import json
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
OCR_ENDPOINT = f"{API_BASE_URL}/ocr/fast"

def test_ocr_endpoint_with_images(image_paths: list, model: str = "gemini/gemini-flash-latest"):
    """
    Test the OCR endpoint with a list of image files.
    
    Args:
        image_paths: List of paths to image files
        model: LiteLLM model to use (default: gemini/gemini-flash-latest)
    """
    print(f"\n{'='*60}")
    print(f"Testing Fast OCR Endpoint")
    print(f"{'='*60}")
    print(f"Model: {model}")
    print(f"Images: {len(image_paths)}")
    print(f"Endpoint: {OCR_ENDPOINT}")
    print(f"{'='*60}\n")
    
    # Prepare files for upload
    files = []
    for img_path in image_paths:
        path = Path(img_path)
        if not path.exists():
            print(f"⚠️  Warning: Image not found: {img_path}")
            continue
        
        print(f"📄 Adding: {path.name}")
        files.append(
            ('files', (path.name, open(path, 'rb'), 'image/jpeg'))
        )
    
    if not files:
        print("❌ No valid images found to process")
        return
    
    # Prepare form data
    data = {
        'model': model,
        'temperature': 0.1,
        'structured_output': True
    }
    
    print(f"\n🚀 Sending request to {OCR_ENDPOINT}...")
    
    try:
        # Make request
        response = requests.post(
            OCR_ENDPOINT,
            files=files,
            data=data
        )
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\n{'='*60}")
            print(f"Response Summary")
            print(f"{'='*60}")
            print(f"Total Images: {result['total_images']}")
            print(f"Successful: {result['successful_count']}")
            print(f"Failed: {result['failed_count']}")
            print(f"Total Processing Time: {result['total_processing_time']}s")
            print(f"Model Used: {result['model_used']}")
            print(f"Timestamp: {result['timestamp']}")
            
            print(f"\n{'='*60}")
            print(f"Individual Results")
            print(f"{'='*60}")
            
            for idx, ocr_result in enumerate(result['results'], 1):
                print(f"\n📄 Image {idx}: {ocr_result['filename']}")
                print(f"   Success: {ocr_result['success']}")
                print(f"   Processing Time: {ocr_result['processing_time']}s")
                
                if ocr_result['success']:
                    print(f"   Extracted Text Preview:")
                    text = ocr_result['extracted_text']
                    preview = text[:200] + "..." if len(text) > 200 else text
                    for line in preview.split('\n'):
                        print(f"      {line}")
                else:
                    print(f"   Error: {ocr_result['error']}")
            
            print(f"\n{'='*60}")
            print(f"✅ Test completed successfully!")
            print(f"{'='*60}\n")
            
            # Save full response to file
            output_file = Path("ocr_test_results.json")
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"💾 Full results saved to: {output_file}")
            
        else:
            print(f"\n❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to API server at {API_BASE_URL}")
        print("Make sure the server is running with: python -m uvicorn api:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def test_with_sample_images():
    """
    Test with sample images (you need to provide your own image paths).
    """
    # Example image paths - UPDATE THESE WITH YOUR ACTUAL IMAGE PATHS
    sample_images = [
        # Add your test image paths here
        # "path/to/image1.jpg",
        # "path/to/image2.png",
    ]
    
    if not sample_images:
        print("\n⚠️  No sample images configured!")
        print("\nTo test the OCR endpoint, please:")
        print("1. Edit this script and add image paths to the 'sample_images' list")
        print("2. Or call test_ocr_endpoint_with_images() with your own image paths")
        print("\nExample:")
        print("  test_ocr_endpoint_with_images(['image1.jpg', 'image2.png'])")
        return
    
    test_ocr_endpoint_with_images(sample_images)


def test_health():
    """Test if the API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print(f"✅ API server is running at {API_BASE_URL}")
            return True
        else:
            print(f"⚠️  API server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to API server at {API_BASE_URL}")
        print("Please start the server with: python -m uvicorn api:app --reload")
        return False


if __name__ == "__main__":
    print("\n🔍 Fast OCR Endpoint Test Script")
    print("=" * 60)
    
    # First check if server is running
    if test_health():
        print("\n📝 Ready to test OCR endpoint")
        print("\nUsage:")
        print("  1. Add image paths to the script")
        print("  2. Or use: test_ocr_endpoint_with_images(['path1.jpg', 'path2.png'])")
        print("\n" + "=" * 60)
        
        # Run test if sample images are configured
        test_with_sample_images()
    else:
        print("\n❌ Cannot proceed without running API server")
