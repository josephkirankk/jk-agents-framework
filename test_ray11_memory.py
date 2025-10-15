#!/usr/bin/env python3
"""
Test script to simulate the ray-11 memory issue with multiple API calls.
This will help verify that conversation memory is working correctly.
"""
import json
import requests
import time

def make_api_call(query, thread_id, call_number):
    """Make an API call and return the response."""
    print(f"\n{'='*60}")
    print(f"🔄 INTERACTION {call_number}: {query}")
    print(f"🧵 Thread ID: {thread_id}")
    print(f"{'='*60}")
    
    payload = {
        "input": query,
        "thread_id": thread_id
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:8001/query", 
            json=payload, 
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')
            
            print(f"✅ SUCCESS (took {elapsed:.1f}s)")
            print(f"📝 Response ({len(response_text)} chars):")
            print("-" * 40)
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            print("-" * 40)
            
            return {
                "success": True,
                "response": response_text,
                "elapsed": elapsed,
                "result": result
            }
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "elapsed": elapsed
            }
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ EXCEPTION after {elapsed:.1f}s: {e}")
        return {
            "success": False,
            "error": str(e),
            "elapsed": elapsed
        }

def analyze_context_awareness(responses):
    """Analyze if responses show context awareness from previous interactions."""
    print(f"\n{'='*60}")
    print(f"🧠 CONTEXT ANALYSIS")
    print(f"{'='*60}")
    
    if len(responses) < 2:
        print("❌ Need at least 2 responses to analyze context")
        return False
    
    context_indicators = []
    
    # Check if later responses reference earlier topics
    first_response = responses[0]['response'].lower()
    
    for i, response_data in enumerate(responses[1:], 2):
        response_text = response_data['response'].lower()
        
        print(f"\n🔍 Analyzing Response {i}:")
        
        # Look for references to previous topics
        context_found = False
        
        # Check for explicit references to machine learning (from first question)
        if 'machine learning' in first_response and 'machine learning' in response_text:
            print(f"   ✅ References 'machine learning' from first interaction")
            context_found = True
            context_indicators.append(f"Response {i}: References 'machine learning'")
        
        # Check for contextual continuity words
        continuity_words = ['as mentioned', 'as i said', 'previously', 'earlier', 'like i mentioned', 'as we discussed', 'building on', 'following up']
        found_continuity = [word for word in continuity_words if word in response_text]
        if found_continuity:
            print(f"   ✅ Uses continuity language: {found_continuity}")
            context_found = True
            context_indicators.append(f"Response {i}: Uses continuity language")
        
        # Check for specific examples that build on previous context
        if i == 2 and 'example' in response_text and any(term in response_text for term in ['algorithm', 'classification', 'prediction', 'model', 'data']):
            print(f"   ✅ Provides relevant examples in context")
            context_found = True
            context_indicators.append(f"Response {i}: Provides contextual examples")
        
        if not context_found:
            print(f"   ⚠️ No clear context indicators found")
    
    print(f"\n📊 CONTEXT SUMMARY:")
    if context_indicators:
        print(f"   ✅ {len(context_indicators)} context indicators found:")
        for indicator in context_indicators:
            print(f"      • {indicator}")
        print(f"   🎯 VERDICT: Memory system appears to be WORKING")
        return True
    else:
        print(f"   ❌ No context indicators found")
        print(f"   🎯 VERDICT: Memory system may NOT be working")
        return False

def test_ray11_scenario():
    """Test the ray-11 scenario with multiple interactions."""
    print(f"🔍 Testing Ray-11 Memory Scenario")
    print(f"Testing conversation memory with multiple related questions")
    print(f"Expected: Later responses should show context from earlier ones")
    
    # Use a unique thread ID for this test
    thread_id = f"ray-11-memory-test-{int(time.time())}"
    
    # Define the conversation sequence (similar to typical ray-11 interactions)
    conversation = [
        "What is machine learning?",
        "Can you give me a simple example?", 
        "How does that algorithm work in practice?",
        "What are the main challenges with this approach?"
    ]
    
    responses = []
    
    # Execute each interaction
    for i, query in enumerate(conversation, 1):
        result = make_api_call(query, thread_id, i)
        
        if result['success']:
            responses.append(result)
            
            # Add a short delay between calls
            if i < len(conversation):
                print(f"⏳ Waiting 2s before next interaction...")
                time.sleep(2)
        else:
            print(f"❌ CRITICAL: Interaction {i} failed, stopping test")
            return False
    
    # Analyze context awareness
    context_working = analyze_context_awareness(responses)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎯 FINAL RESULTS")
    print(f"{'='*60}")
    
    print(f"📊 Statistics:")
    print(f"   • Total interactions: {len(responses)}")
    print(f"   • Average response time: {sum(r['elapsed'] for r in responses) / len(responses):.1f}s")
    print(f"   • Thread ID: {thread_id}")
    
    if context_working:
        print(f"\n✅ SUCCESS: Ray-11 memory issue appears to be RESOLVED!")
        print(f"   • All interactions completed successfully")
        print(f"   • Context is maintained across interactions")
        print(f"   • Memory system is working correctly")
    else:
        print(f"\n❌ FAILURE: Ray-11 memory issue persists!")
        print(f"   • Interactions completed but no context awareness")
        print(f"   • Memory system may not be working properly")
        print(f"   • Further investigation needed")
    
    return context_working

if __name__ == "__main__":
    try:
        success = test_ray11_scenario()
        
        if success:
            print(f"\n🎉 Test completed successfully - Memory system is working!")
        else:
            print(f"\n⚠️ Test completed but issues detected - Memory system needs attention!")
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()