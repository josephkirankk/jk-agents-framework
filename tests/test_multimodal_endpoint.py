#!/usr/bin/env python3
"""
Test Multimodal API Endpoint
Tests the /multimodal endpoint in the API server
"""

import os
import sys
import asyncio
import aiohttp
import tempfile
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment variable loading")

API_URL = "http://localhost:8000"
TEST_TIMEOUT = 60  # seconds

async def create_test_image():
    """Create a test image for multimodal processing"""
    # Create a 400x300 image with white background
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some geometric shapes
    draw.rectangle([50, 50, 150, 100], fill='blue', outline='black', width=2)
    draw.ellipse([160, 35, 240, 115], fill='red', outline='black', width=2)  # Circle
    draw.polygon([(300, 50), (350, 100), (250, 100)], fill='green', outline='black', width=2)
    
    # Add text
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    
    draw.text((50, 150), "Test Image Analysis", fill='black', font=font)
    draw.text((50, 180), "Blue Rectangle", fill='blue', font=font)
    draw.text((50, 210), "Red Circle", fill='red', font=font)
    draw.text((50, 240), "Green Triangle", fill='green', font=font)
    
    # Save to temporary file
    temp_dir = Path(tempfile.mkdtemp())
    image_path = temp_dir / "test_multimodal_image.png"
    img.save(image_path)
    
    return str(image_path), temp_dir

async def test_multimodal_text_only(session):
    """Test the multimodal endpoint with text-only content"""
    print("\n📝 Testing /multimodal endpoint - Text Only")
    
    # Define model to use (prioritize models based on available keys)
    if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
        model = "azure/gpt-4.1"
        print(f"Using Azure OpenAI model: {model}")
    elif os.getenv("GOOGLE_API_KEY"):
        model = "gemini/gemini-2.5-flash-lite"
        print(f"Using Google Gemini model: {model}")
    else:
        model = "openai/gpt-4o"  # Fallback
        print(f"Using OpenAI model: {model}")
    
    data = aiohttp.FormData()
    data.add_field("model", model)
    data.add_field("prompt", "Calculate the square root of 144 step by step.")
    data.add_field("temperature", "0.2")
    data.add_field("system_message", "You are a helpful math assistant.")
    
    try:
        async with session.post(f"{API_URL}/multimodal", data=data, timeout=TEST_TIMEOUT) as response:
            status = response.status
            result = await response.json()
            
            if status == 200:
                print(f"✅ Text-only request succeeded (Status: {status})")
                print(f"🧠 Model: {result.get('model')}")
                print(f"⏱️ Processing time: {result.get('processing_time')}s")
                print(f"📏 Response preview: {result.get('response')[:200]}...")
                thread_id = result.get("thread_id")
                return True, thread_id
            else:
                print(f"❌ Text-only request failed (Status: {status})")
                print(f"📋 Error: {result}")
                return False, None
                
    except Exception as e:
        print(f"❌ Text-only request exception: {str(e)}")
        return False, None

async def test_multimodal_image(session, thread_id=None):
    """Test the multimodal endpoint with an image"""
    print("\n🖼️ Testing /multimodal endpoint - With Image")
    
    # Create test image
    try:
        image_path, temp_dir = await create_test_image()
    except Exception as e:
        print(f"❌ Failed to create test image: {str(e)}")
        return False
    
    # Define model to use (prioritize models based on available keys)
    if os.getenv("GOOGLE_API_KEY"):
        model = "gemini/gemini-2.5-flash-lite"  # Good for vision tasks
        print(f"Using Google Gemini model: {model}")
    elif os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
        model = "azure/gpt-4.1"  # May support vision
        print(f"Using Azure OpenAI model: {model}")
    else:
        model = "openai/gpt-4o"  # Fallback
        print(f"Using OpenAI model: {model}")
    
    data = aiohttp.FormData()
    data.add_field("model", model)
    data.add_field("prompt", "Analyze this image and describe the shapes and colors you see.")
    data.add_field("temperature", "0.2")
    data.add_field("system_message", "You are a helpful vision assistant.")
    
    if thread_id:
        data.add_field("thread_id", thread_id)
        print(f"🧵 Using thread_id for conversation continuity: {thread_id}")
    
    # Add the image file
    with open(image_path, 'rb') as f:
        data.add_field('files', f, filename='test_image.png', content_type='image/png')
    
    try:
        async with session.post(f"{API_URL}/multimodal", data=data, timeout=TEST_TIMEOUT) as response:
            status = response.status
            result = await response.json()
            
            if status == 200:
                print(f"✅ Image request succeeded (Status: {status})")
                print(f"🧠 Model: {result.get('model')}")
                print(f"⏱️ Processing time: {result.get('processing_time')}s")
                print(f"🖼️ Files processed: {result.get('files_processed')}")
                print(f"📏 Response preview: {result.get('response')[:200]}...")
                success = True
            else:
                print(f"❌ Image request failed (Status: {status})")
                print(f"📋 Error: {result}")
                success = False
    except Exception as e:
        print(f"❌ Image request exception: {str(e)}")
        success = False
    
    # Clean up
    try:
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up temp files: {e}")
    
    return success

async def test_multimodal_conversation(session):
    """Test multimodal conversation continuity across turns"""
    print("\n🔄 Testing Multimodal Conversation Continuity")
    
    # First turn: text-only request
    success, thread_id = await test_multimodal_text_only(session)
    if not success or not thread_id:
        print("❌ Failed to establish first conversation turn")
        return False
    
    # Second turn: image request with the same thread ID
    success = await test_multimodal_image(session, thread_id)
    if not success:
        print("❌ Failed to continue conversation with image")
        return False
    
    print("✅ Successfully tested conversation continuity across text and image turns")
    return True

async def test_api_health(session):
    """Test if the API is running and healthy"""
    try:
        async with session.get(f"{API_URL}/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ API is running (status: {response.status})")
                print(f"📋 API version: {data.get('version')}")
                print(f"📅 Server time: {data.get('server_time')}")
                return True
            else:
                print(f"❌ API health check failed (status: {response.status})")
                return False
    except Exception as e:
        print(f"❌ API not reachable: {str(e)}")
        print(f"💡 Make sure the API server is running at {API_URL}")
        return False

async def main():
    """Main test execution function"""
    print("🚀 Testing Multimodal API Endpoint")
    print("="*60)
    
    # Check for required environment variables
    print("\n🔐 API Key Environment Variables:")
    key_vars = [
        "OPENAI_API_KEY",
        "AZURE_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY"
    ]
    
    for var in key_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: ✅ Set (value hidden)")
        else:
            print(f"  {var}: ❌ Not set")
    
    # Create HTTP session for tests
    async with aiohttp.ClientSession() as session:
        # First check if API is running
        api_running = await test_api_health(session)
        if not api_running:
            print("❌ API server is not running - tests cannot proceed")
            return False
        
        # Run tests
        success_text = await test_multimodal_text_only(session)
        success_image = await test_multimodal_image(session)
        success_conversation = await test_multimodal_conversation(session)
        
        # Summary
        print("\n"+"="*60)
        print("📊 MULTIMODAL API TEST SUMMARY:")
        print("="*60)
        print(f"✅ API Health Check: {'Passed' if api_running else 'Failed'}")
        print(f"✅ Text-Only Request: {'Passed' if success_text[0] else 'Failed'}")
        print(f"✅ Image Request: {'Passed' if success_image else 'Failed'}")
        print(f"✅ Conversation Continuity: {'Passed' if success_conversation else 'Failed'}")
        
        overall = api_running and success_text[0] and success_image and success_conversation
        print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")
        
        return overall

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
