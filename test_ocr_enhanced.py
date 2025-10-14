"""
Enhanced test script for the improved /ocr/fast endpoint

Tests the new features:
- Compact OCR extraction (essential fields only)
- Final summarization step that combines results
- Structured JSON output for easy integration
"""

import requests
import json
from pathlib import Path
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
OCR_ENDPOINT = f"{API_BASE_URL}/ocr/fast"

def test_enhanced_ocr(image_paths: list):
    """
    Test the enhanced OCR endpoint with visiting cards.
    
    New features tested:
    1. Fast, compact OCR extraction
    2. Parallel processing of multiple images
    3. Final summarization into structured JSON
    4. Merged front/back cards
    """
    print(f"\n{'='*70}")
    print(f"🚀 Enhanced Visiting Card OCR Test")
    print(f"{'='*70}")
    print(f"Testing: Compact extraction + Structured summarization")
    print(f"Images: {len(image_paths)}")
    print(f"{'='*70}\n")
    
    # Prepare files
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
    
    print(f"\n🚀 Sending request to {OCR_ENDPOINT}...")
    print(f"⏱️  Processing {len(files)} images in parallel + final summarization...")
    
    try:
        start_time = datetime.now()
        
        # Make request
        response = requests.post(OCR_ENDPOINT, files=files)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n{'='*70}")
            print(f"✅ SUCCESS! Total time: {total_time:.2f}s")
            print(f"{'='*70}\n")
            
            # === MAIN FEATURE: STRUCTURED CARDS ===
            print(f"{'='*70}")
            print(f"📇 STRUCTURED CARDS (Main Output)")
            print(f"{'='*70}")
            
            structured_cards = result.get('structured_cards', [])
            
            if structured_cards:
                print(f"Found {len(structured_cards)} unique card(s):\n")
                
                for idx, card in enumerate(structured_cards, 1):
                    print(f"{'─'*70}")
                    print(f"Card #{idx}")
                    print(f"{'─'*70}")
                    print(f"👤 Name:    {card.get('name', 'N/A')}")
                    print(f"💼 Role:    {card.get('role', 'N/A')}")
                    print(f"🏢 Company: {card.get('company', 'N/A')}")
                    
                    phones = card.get('phone', [])
                    if phones and phones != [None]:
                        print(f"📞 Phone(s):")
                        for phone in phones:
                            if phone:
                                print(f"   • {phone}")
                    
                    emails = card.get('email', [])
                    if emails and emails != [None]:
                        print(f"📧 Email(s):")
                        for email in emails:
                            if email:
                                print(f"   • {email}")
                    
                    address = card.get('address')
                    if address and address != 'null':
                        print(f"🏠 Address: {address}")
                    
                    websites = card.get('website', [])
                    if websites and websites != [None]:
                        print(f"🌐 Website(s):")
                        for website in websites:
                            if website:
                                print(f"   • {website}")
                    
                    print()
            else:
                print("⚠️  No structured cards generated")
            
            # === PERFORMANCE METRICS ===
            print(f"{'='*70}")
            print(f"⚡ Performance Metrics")
            print(f"{'='*70}")
            print(f"Total Images:        {result['total_images']}")
            print(f"Successful:          {result['successful_count']}")
            print(f"Failed:              {result['failed_count']}")
            print(f"OCR Time:            {result['total_processing_time'] - result['summarization_time']:.2f}s")
            print(f"Summarization Time:  {result['summarization_time']:.2f}s")
            print(f"Total Time:          {result['total_processing_time']:.2f}s")
            print(f"Model Used:          {result['model_used']}")
            print(f"Timestamp:           {result['timestamp']}")
            
            # === INDIVIDUAL OCR RESULTS (Raw) ===
            print(f"\n{'='*70}")
            print(f"📄 Individual OCR Results (Per Image)")
            print(f"{'='*70}\n")
            
            for idx, ocr_result in enumerate(result['results'], 1):
                print(f"Image {idx}: {ocr_result['filename']}")
                print(f"  Status: {'✅ Success' if ocr_result['success'] else '❌ Failed'}")
                print(f"  Time: {ocr_result['processing_time']}s")
                
                if ocr_result['success']:
                    # Show compact extracted text
                    text = ocr_result['extracted_text']
                    lines = text.split('\n')
                    print(f"  Extracted (compact):")
                    for line in lines[:10]:  # Show first 10 lines
                        print(f"    {line}")
                    if len(lines) > 10:
                        print(f"    ... ({len(lines) - 10} more lines)")
                else:
                    print(f"  Error: {ocr_result['error']}")
                print()
            
            # Save full response
            output_file = Path("ocr_enhanced_results.json")
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"{'='*70}")
            print(f"💾 Full results saved to: {output_file}")
            print(f"{'='*70}\n")
            
            # Show JSON structure for integration
            print(f"{'='*70}")
            print(f"🔧 JSON Structure (for integration)")
            print(f"{'='*70}")
            print("Access structured cards:")
            print("  response['structured_cards'][0]['name']")
            print("  response['structured_cards'][0]['phone']")
            print("  response['structured_cards'][0]['email']")
            print("\nExample:")
            print(json.dumps(structured_cards[:1], indent=2))
            
            print(f"\n{'='*70}")
            print(f"✅ Test completed successfully!")
            print(f"{'='*70}\n")
            
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
    print("\n🔍 Enhanced Visiting Card OCR Test")
    print("=" * 70)
    
    # Check if server is running
    if test_health():
        print("\n📝 Testing with your images...")
        
        # Test with actual images
        test_images = [
            "/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 20.56.07.jpeg",
            "/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 20.56.08.jpeg"
        ]
        
        test_enhanced_ocr(test_images)
    else:
        print("\n❌ Cannot proceed without running API server")
