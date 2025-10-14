#!/usr/bin/env python3
"""
Test script for LiteLLM multi-turn conversations.
Tests both text-only and multimodal interactions across multiple turns.
"""

import os
import sys
import asyncio
import json
import aiohttp
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️ dotenv not installed, skipping environment loading")

# API endpoint settings
API_URL = "http://localhost:8000"
MULTIMODAL_ENDPOINT = f"{API_URL}/multimodal"

# Test settings
TEST_TIMEOUT = 60  # seconds

async def test_turn(session, prompt, model, thread_id=None, image_path=None, turn_num=0):
    """Test a single conversation turn"""
    print(f"\n📝 TURN {turn_num}: Testing with prompt: '{prompt}'")
    
    # Create form data for the request
    data = aiohttp.FormData()
    data.add_field("model", model)
    data.add_field("prompt", prompt)
    data.add_field("temperature", "0.2")
    data.add_field("system_message", "You are a helpful assistant that maintains context across conversation turns.")
    
    if thread_id:
        data.add_field("thread_id", thread_id)
        print(f"🧵 Using thread_id for conversation continuity: {thread_id}")
    
    # Add image file if provided
    if image_path:
        print(f"🖼️ Attaching image: {image_path}")
        # Read image content first to avoid file closed issues
        with open(image_path, 'rb') as f:
            image_content = f.read()
        data.add_field('files', image_content, filename=os.path.basename(image_path), 
                     content_type='image/png')
    
    # Send request
    try:
        async with session.post(MULTIMODAL_ENDPOINT, data=data, timeout=TEST_TIMEOUT) as response:
            status = response.status
            if status != 200:
                print(f"❌ Request failed with status {status}")
                try:
                    result = await response.json()
                    print(f"Error: {result}")
                except:
                    print(f"Response: {await response.text()}")
                return None, None
            
            result = await response.json()
            
            # Print results
            print(f"✅ Request succeeded (Status: {status})")
            print(f"🧠 Model: {result.get('model')}")
            print(f"⏱️ Processing time: {result.get('processing_time')}s")
            print(f"📝 Response preview: {result.get('response')[:150]}...")
            
            # Return response and thread_id for next turn
            return result.get("response"), result.get("thread_id")
    except Exception as e:
        print(f"❌ Request exception: {str(e)}")
        return None, None

async def test_multi_turn_conversation():
    """Test a multi-turn conversation with both text and multimodal content"""
    print("🚀 Testing Multi-Turn Conversation with LiteLLM")
    print("=" * 60)
    
    # Define turns for the conversation
    turns = [
        {
            "prompt": "Please introduce yourself and remember my name is Alex.",
            "image_path": None
        },
        {
            "prompt": "What is my name? And can you list 3 colors?",
            "image_path": None
        },
        {
            "prompt": "Describe what you see in this image.",
            "image_path": "test_image.png"
        },
        {
            "prompt": "What colors did you mention earlier in our conversation, and what colors did you see in the image?",
            "image_path": None
        }
    ]
    
    # Choose model to use based on available API keys
    model = None
    if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
        model = "azure/gpt-4.1"
        print(f"Using Azure OpenAI model: {model}")
    elif os.getenv("GOOGLE_API_KEY"):
        model = "gemini/gemini-2.5-flash-lite"
        print(f"Using Google Gemini model: {model}")
    else:
        model = "openai/gpt-4o"  # Fallback
        print(f"Using OpenAI model: {model}")
    
    thread_id = None
    responses = []
    
    # Create HTTP session for tests
    async with aiohttp.ClientSession() as session:
        # Test API health
        try:
            async with session.get(f"{API_URL}/health") as response:
                if response.status != 200:
                    print(f"❌ API server is not running or unhealthy (status: {response.status})")
                    print(f"💡 Start the API server with: './run_litellm_api.sh' or 'python litellm_api.py'")
                    return False
                data = await response.json()
                print(f"✅ API is running (status: {response.status})")
                print(f"📋 API version: {data.get('version')}")
                print(f"📅 LiteLLM available: {data.get('litellm_available')}")
                print(f"🧠 Memory available: {data.get('memory_available')}")
        except Exception as e:
            print(f"❌ API not reachable: {str(e)}")
            print(f"💡 Make sure the API server is running at {API_URL}")
            return False
        
        # Run each turn in the conversation
        for i, turn in enumerate(turns):
            response, new_thread_id = await test_turn(
                session, 
                turn["prompt"], 
                model,
                thread_id=thread_id,
                image_path=turn["image_path"],
                turn_num=i+1
            )
            
            if response is None:
                print(f"❌ Turn {i+1} failed, stopping conversation")
                return False
            
            responses.append(response)
            thread_id = new_thread_id
            
            # Small delay between turns to avoid rate limiting
            await asyncio.sleep(1)
    
    # Analyze context preservation
    print("\n" + "=" * 60)
    print("🔍 CONTEXT PRESERVATION ANALYSIS:")
    print("=" * 60)
    
    # Check if name was remembered
    name_remembered = "Alex" in responses[1].lower()
    print(f"✅ Name remembered in turn 2: {name_remembered}")
    
    # Check if colors from turn 2 are referenced in turn 4
    if len(responses) >= 4:
        colors_referenced = any(color in responses[3].lower() for color 
                             in ["color", "red", "blue", "green", "yellow"])
        print(f"✅ Colors referenced in final turn: {colors_referenced}")
    
    # Check if image description is referenced in turn 4
    if len(responses) >= 4:
        image_referenced = any(term in responses[3].lower() for term 
                            in ["image", "picture", "photo", "triangle", "rectangle", "circle"])
        print(f"✅ Image description referenced in final turn: {image_referenced}")
    
    print("\n" + "=" * 60)
    print("📊 MULTI-TURN TEST SUMMARY:")
    print("=" * 60)
    
    success = len(responses) == len(turns)
    context_preserved = name_remembered and colors_referenced and image_referenced
    
    print(f"✅ Complete Conversation: {'Passed' if success else 'Failed'}")
    print(f"✅ Context Preservation: {'Passed' if context_preserved else 'Failed'}")
    
    overall = success and context_preserved
    print(f"\nOverall Result: {'✅ PASSED' if overall else '❌ FAILED'}")
    
    return overall

if __name__ == "__main__":
    asyncio.run(test_multi_turn_conversation())
