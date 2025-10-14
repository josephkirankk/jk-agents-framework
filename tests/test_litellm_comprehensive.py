#!/usr/bin/env python3
"""
Comprehensive test for LiteLLM multimodal integration with multi-turn conversations.
Tests text-only and multimodal interactions with detailed conversation analysis.
"""

import os
import sys
import asyncio
import json
import aiohttp
import re
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

async def send_request(session, model, prompt, thread_id=None, image_path=None):
    """Send a request to the multimodal endpoint"""
    # Create form data for the request
    data = aiohttp.FormData()
    data.add_field("model", model)
    data.add_field("prompt", prompt)
    data.add_field("temperature", "0.2")
    data.add_field("system_message", "You are a helpful assistant for testing multi-turn conversations.")
    
    if thread_id:
        data.add_field("thread_id", thread_id)
    
    # Add image file if provided
    if image_path:
        # Read image content first to avoid file closed issues
        with open(image_path, 'rb') as f:
            image_content = f.read()
        data.add_field('files', image_content, filename=os.path.basename(image_path), 
                     content_type='image/png')
    
    # Send request
    async with session.post(MULTIMODAL_ENDPOINT, data=data, timeout=TEST_TIMEOUT) as response:
        if response.status != 200:
            try:
                error = await response.json()
                return None, None, f"HTTP {response.status}: {error.get('detail', 'Unknown error')}"
            except:
                return None, None, f"HTTP {response.status}: {await response.text()}"
        
        result = await response.json()
        return result.get("response"), result.get("thread_id"), None

async def check_api_health(session):
    """Check if the API is running"""
    try:
        async with session.get(f"{API_URL}/health") as response:
            if response.status != 200:
                return False, f"API unhealthy: HTTP {response.status}"
            data = await response.json()
            return True, data
    except Exception as e:
        return False, f"API unreachable: {str(e)}"

def analyze_context_preservation(responses, turns, name="Alex", colors=["red", "blue", "green"]):
    """Analyze how well context is preserved across conversation turns"""
    results = {}
    
    # Check for name in turn 2
    if len(responses) >= 2:
        results["name_remembered"] = name.lower() in responses[1].lower()
        
    # Check for colors mentioned in turn 2 referenced in turn 4
    if len(responses) >= 4:
        # Find colors mentioned in turn 2
        colors_turn2 = set()
        for color in colors:
            if color in responses[1].lower():
                colors_turn2.add(color)
                
        # Check if turn 4 references colors from turn 2
        colors_referenced = False
        for color in colors_turn2:
            if color in responses[3].lower():
                colors_referenced = True
                break
        results["colors_referenced"] = colors_referenced
        
    # Check if image description from turn 3 is referenced in turn 4
    if len(responses) >= 4:
        # Image-related terms to check for
        image_terms = ["blue rectangle", "red circle", "green triangle", 
                      "geometric shapes", "test image"]
        
        # Check if any image terms from turn 3 are in turn 4
        image_referenced = False
        for term in image_terms:
            if term.lower() in responses[2].lower() and term.lower() in responses[3].lower():
                image_referenced = True
                break
        results["image_referenced"] = image_referenced
        
    # Check for explicit turn references
    turn_references = []
    for i, response in enumerate(responses):
        turn_refs = re.findall(r'\[Turn-(\d+)\]', response)
        if turn_refs:
            turn_references.append((i+1, [int(t) for t in turn_refs]))
    results["turn_references"] = turn_references
    
    return results

async def test_comprehensive():
    """Comprehensive test of text and multimodal interactions with conversation analysis"""
    print("🚀 COMPREHENSIVE LITELLM MULTI-TURN TEST")
    print("=" * 60)
    
    # Define conversation turns with different interaction types
    turns = [
        {
            "type": "text",
            "prompt": "Hello! My name is Alex. Please remember that and introduce yourself.",
            "description": "Basic text introduction with name to remember"
        },
        {
            "type": "text",
            "prompt": "What's my name? And what are your favorite primary colors?",
            "description": "Memory test and new information request"
        },
        {
            "type": "multimodal",
            "prompt": "What shapes and colors do you see in this image?",
            "image": "test_image.png",
            "description": "Image analysis with shapes and colors"
        },
        {
            "type": "text",
            "prompt": "Compare the colors you mentioned as your favorites with the colors in the image.",
            "description": "Multi-turn memory test across text and image"
        }
    ]
    
    # Choose model to test with
    model = None
    if os.getenv("AZURE_API_KEY") and os.getenv("AZURE_API_BASE"):
        model = "azure/gpt-4.1"
        print(f"🧠 Using Azure OpenAI model: {model}")
    elif os.getenv("GOOGLE_API_KEY"):
        model = "gemini/gemini-2.5-flash-lite"
        print(f"🧠 Using Google Gemini model: {model}")
    else:
        model = "openai/gpt-4o"
        print(f"🧠 Using OpenAI model: {model}")
    
    # Create session and test
    async with aiohttp.ClientSession() as session:
        # Check API health
        healthy, status = await check_api_health(session)
        if not healthy:
            print(f"❌ API server issue: {status}")
            print(f"💡 Start the API server with: './run_litellm_api.sh'")
            return False
        
        print(f"✅ API server healthy: {status}")
        
        # Run the conversation
        thread_id = None
        responses = []
        errors = []
        
        for i, turn in enumerate(turns):
            turn_num = i + 1
            turn_type = turn["type"]
            prompt = turn["prompt"]
            image_path = turn.get("image") if turn_type == "multimodal" else None
            
            print(f"\n📝 TURN {turn_num}: {turn_type.upper()} - {turn['description']}")
            print(f"💬 Prompt: \"{prompt}\"")
            
            if thread_id:
                print(f"🧵 Thread ID: {thread_id}")
            
            if image_path:
                print(f"🖼️ Image: {image_path}")
            
            # Send the request
            response, new_thread_id, error = await send_request(
                session, model, prompt, thread_id, image_path
            )
            
            if error:
                print(f"❌ Error: {error}")
                errors.append(error)
                break
            
            # Display response
            print(f"✅ Response received, {len(response)} chars")
            print(f"📄 Preview: {response[:150]}..." if len(response) > 150 else f"📄 Response: {response}")
            
            # Update for next turn
            responses.append(response)
            thread_id = new_thread_id
            
            # Small delay between turns
            if i < len(turns) - 1:
                await asyncio.sleep(1)
    
    # Analyze results
    print("\n" + "=" * 60)
    print("🔍 CONVERSATION ANALYSIS")
    print("=" * 60)
    
    if len(responses) < len(turns):
        print(f"❌ Incomplete conversation: {len(responses)}/{len(turns)} turns completed")
        for error in errors:
            print(f"  - Error: {error}")
        return False
    
    # Perform detailed analysis
    analysis = analyze_context_preservation(responses, turns)
    
    # Report results
    for key, value in analysis.items():
        if key == "turn_references":
            print(f"📌 Turn references:")
            for turn_num, refs in value:
                print(f"  - Turn {turn_num} references turns {refs}")
        else:
            status = "✅ PASS" if value else "❌ FAIL"
            print(f"{status} {key.replace('_', ' ').title()}")
    
    # Determine overall success
    success = (
        len(responses) == len(turns) and
        analysis.get("name_remembered", False) and
        analysis.get("colors_referenced", False) and 
        analysis.get("image_referenced", False)
    )
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    print(f"✅ Complete conversation: {len(responses)}/{len(turns)} turns")
    print(f"✅ Memory preservation: {'✅ GOOD' if success else '❌ NEEDS IMPROVEMENT'}")
    print(f"✅ Turn references: {'✅ PRESENT' if analysis.get('turn_references') else '❌ MISSING'}")
    
    print(f"\nOverall Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    asyncio.run(test_comprehensive())
