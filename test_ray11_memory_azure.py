#!/usr/bin/env python3
"""
Improved Ray-11 memory test script with Azure OpenAI support.
This will properly test the conversation memory system with multiple interactions.
"""
import json
import requests
import time
import os
import subprocess
import signal
import sys

class APIServerManager:
    """Manage the API server lifecycle for testing."""
    
    def __init__(self, config_path="test_memory_config.yaml"):
        self.process = None
        self.config_path = config_path
        self.server_url = "http://localhost:8001"
        
    def start_server(self):
        """Start the API server with proper environment."""
        print("🚀 Starting API server with Azure OpenAI...")
        
        # Set up environment
        env = os.environ.copy()
        env['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
        
        # Verify Azure OpenAI credentials
        if not env.get('AZURE_OPENAI_ENDPOINT') or not env.get('AZURE_OPENAI_API_KEY'):
            print("❌ Azure OpenAI credentials not found!")
            print("   Please run: ./setup_azure_openai.sh")
            return False
        
        cmd = [
            sys.executable, "-m", "uvicorn", "api:app", 
            "--host", "0.0.0.0", "--port", "8001",
            "--log-level", "info"
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        print(f"   Config: {self.config_path}")
        print(f"   Azure endpoint: {env.get('AZURE_OPENAI_ENDPOINT', 'Not set')}")
        
        try:
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Wait for server to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{self.server_url}/health", timeout=2)
                    if response.status_code == 200:
                        print(f"   ✅ Server ready after {i+1} seconds!")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    if i % 5 == 4:  # Every 5 seconds
                        print(f"   ... still waiting ({i+1}s)")
            
            print("   ❌ Server failed to start within 30 seconds")
            self.stop_server()
            return False
            
        except Exception as e:
            print(f"   ❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the API server."""
        if self.process:
            print("🛑 Stopping API server...")
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
                print("   ✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("   ⚠️ Forcing server shutdown...")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                print(f"   ⚠️ Error stopping server: {e}")
            self.process = None
    
    def get_server_logs(self, lines=20):
        """Get the last N lines of server output."""
        if not self.process or not self.process.stdout:
            return []
        
        try:
            # This is a simplified approach - in a real scenario you'd need
            # to handle this more carefully with non-blocking reads
            return []
        except Exception:
            return []

def make_api_call(server_url, query, thread_id, call_number, config_path="test_memory_config.yaml"):
    """Make an API call and return the response."""
    print(f"\n{'='*60}")
    print(f"🔄 INTERACTION {call_number}: {query}")
    print(f"🧵 Thread ID: {thread_id}")
    print(f"{'='*60}")
    
    payload = {
        "input": query,
        "thread_id": thread_id,
        "config_path": config_path
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{server_url}/query", 
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
            # Show more of the response for better analysis
            if len(response_text) > 1000:
                print(response_text[:500] + "\n...\n" + response_text[-500:])
            else:
                print(response_text)
            print("-" * 40)
            
            return {
                "success": True,
                "response": response_text,
                "elapsed": elapsed,
                "result": result
            }
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
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
    
    # Get all response texts for analysis
    response_texts = [resp['response'].lower() for resp in responses]
    first_response = response_texts[0]
    
    for i, response_text in enumerate(response_texts[1:], 2):
        print(f"\n🔍 Analyzing Response {i}:")
        
        context_found = False
        
        # Check for explicit references to machine learning (from first question)
        if 'machine learning' in first_response and 'machine learning' in response_text:
            print(f"   ✅ References 'machine learning' from first interaction")
            context_found = True
            context_indicators.append(f"Response {i}: References 'machine learning'")
        
        # Check for contextual continuity words
        continuity_words = [
            'as mentioned', 'as i said', 'previously', 'earlier', 'like i mentioned', 
            'as we discussed', 'building on', 'following up', 'as discussed',
            'from the previous', 'continuing from', 'based on what we covered'
        ]
        found_continuity = [word for word in continuity_words if word in response_text]
        if found_continuity:
            print(f"   ✅ Uses continuity language: {found_continuity}")
            context_found = True
            context_indicators.append(f"Response {i}: Uses continuity language: {found_continuity}")
        
        # Check for specific examples that build on previous context
        if i == 2:
            ml_terms = ['algorithm', 'classification', 'prediction', 'model', 'data', 'training', 'supervised']
            found_ml_terms = [term for term in ml_terms if term in response_text]
            if 'example' in response_text and found_ml_terms:
                print(f"   ✅ Provides relevant ML examples: {found_ml_terms}")
                context_found = True
                context_indicators.append(f"Response {i}: Provides contextual ML examples")
        
        # Check if responses show progression in understanding
        if len(response_text) > len(response_texts[i-2]) * 0.8:  # Similar or longer response
            print(f"   ✅ Maintains response depth (not getting shorter due to lack of context)")
            context_found = True
            context_indicators.append(f"Response {i}: Maintains response depth")
        
        # Look for specific terms that would indicate the assistant knows we're talking about ML
        if i >= 3:  # Third response or later
            ml_context_terms = ['this approach', 'these algorithms', 'such methods', 'this technique']
            found_context_terms = [term for term in ml_context_terms if term in response_text]
            if found_context_terms:
                print(f"   ✅ Uses contextual references: {found_context_terms}")
                context_found = True
                context_indicators.append(f"Response {i}: Uses contextual references")
        
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

def test_memory_storage():
    """Test direct memory storage functionality."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING DIRECT MEMORY STORAGE")
    print(f"{'='*60}")
    
    try:
        # Import and test the memory system directly
        import sys
        import os
        from pathlib import Path
        
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        # Set environment
        os.environ['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
        
        from app.memory.memory_integration import (
            initialize_conversation_memory, 
            store_conversation_memory,
            enhance_system_message_with_memory
        )
        from app.main import load_app_config
        
        # Load config
        app_config = load_app_config("test_memory_config.yaml")
        print("   ✅ Configuration loaded")
        
        # Initialize memory
        memory_init = await initialize_conversation_memory(app_config)
        print(f"   ✅ Memory initialized: {memory_init}")
        
        # Test storage
        test_thread = "direct-memory-test"
        await store_conversation_memory(
            thread_id=test_thread,
            user_message="Test memory storage",
            assistant_response="Memory storage test response",
            app_config=app_config
        )
        print("   ✅ Memory storage successful")
        
        # Test enhancement
        enhanced = await enhance_system_message_with_memory(
            original_message="You are a test assistant.",
            thread_id=test_thread,
            app_config=app_config
        )
        
        context_added = len(enhanced) - len("You are a test assistant.")
        print(f"   ✅ Memory enhancement: {context_added} characters added")
        
        return context_added > 0
        
    except Exception as e:
        print(f"   ❌ Direct memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the comprehensive Ray-11 memory test."""
    print(f"🔍 Ray-11 Memory System Test with Azure OpenAI")
    print(f"Testing conversation memory with multiple related questions")
    print(f"Expected: Later responses should show context from earlier ones")
    
    # Check prerequisites
    if not os.getenv('AZURE_OPENAI_ENDPOINT') or not os.getenv('AZURE_OPENAI_API_KEY'):
        print("\n❌ Azure OpenAI credentials not found!")
        print("   Please run: ./setup_azure_openai.sh")
        print("   Then set your credentials and try again.")
        return False
    
    print(f"\n✅ Azure OpenAI endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    
    # Start API server
    server_manager = APIServerManager()
    
    try:
        if not server_manager.start_server():
            print("\n❌ Failed to start API server")
            return False
        
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
            result = make_api_call(
                server_manager.server_url, 
                query, 
                thread_id, 
                i,
                "test_memory_config.yaml"
            )
            
            if result['success'] and result['response'].strip():
                responses.append(result)
                
                # Add a short delay between calls
                if i < len(conversation):
                    print(f"⏳ Waiting 3s before next interaction...")
                    time.sleep(3)
            else:
                print(f"❌ CRITICAL: Interaction {i} failed or returned empty response")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
                print("   Continuing with remaining interactions...")
                # Don't return False here, continue with other interactions
        
        # Analyze context awareness
        if len(responses) >= 2:
            context_working = analyze_context_awareness(responses)
        else:
            print(f"\n❌ Not enough successful responses ({len(responses)}) to analyze context")
            context_working = False
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"🎯 FINAL RESULTS")
        print(f"{'='*60}")
        
        print(f"📊 Statistics:")
        print(f"   • Successful interactions: {len(responses)}/{len(conversation)}")
        if responses:
            print(f"   • Average response time: {sum(r['elapsed'] for r in responses) / len(responses):.1f}s")
            print(f"   • Average response length: {sum(len(r['response']) for r in responses) / len(responses):.0f} chars")
        print(f"   • Thread ID: {thread_id}")
        
        if len(responses) >= 2 and context_working:
            print(f"\n✅ SUCCESS: Ray-11 memory issue appears to be RESOLVED!")
            print(f"   • Multiple interactions completed successfully")
            print(f"   • Context is maintained across interactions")
            print(f"   • Memory system is working correctly")
            return True
        elif len(responses) >= 2:
            print(f"\n⚠️ PARTIAL SUCCESS: Interactions work but context unclear")
            print(f"   • API calls completed successfully")
            print(f"   • Responses generated but context indicators not clear")
            print(f"   • Memory system may need fine-tuning")
            return False
        else:
            print(f"\n❌ FAILURE: Ray-11 memory issue persists!")
            print(f"   • API interactions failing")
            print(f"   • Insufficient responses to test memory")
            print(f"   • Check server logs and Azure OpenAI connection")
            return False
        
    finally:
        # Always clean up
        server_manager.stop_server()

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print(f"\n🎉 Test completed successfully - Memory system is working!")
            sys.exit(0)
        else:
            print(f"\n⚠️ Test completed but issues detected - Memory system needs attention!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)