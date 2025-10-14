#!/usr/bin/env python3
"""
Test the actual API server startup and memory initialization.

This will help us understand if the startup event runs properly.
"""
import asyncio
import json
import logging
import os
import requests
import subprocess
import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_api_server():
    """Start the API server as a subprocess."""
    print("🚀 Starting API server...")
    
    # Ensure DATABASE_URL is set
    env = os.environ.copy()
    if 'DATABASE_URL' not in env:
        env['DATABASE_URL'] = 'postgresql://jkagent_user:securepassword@localhost:5432/conversations'
        print(f"   Set DATABASE_URL: {env['DATABASE_URL']}")
    
    # Start the server using uvicorn
    cmd = [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
    
    print(f"   Command: {' '.join(cmd)}")
    print(f"   Working directory: {project_root}")
    
    process = subprocess.Popen(
        cmd,
        cwd=str(project_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    return process

def wait_for_server(host="localhost", port=8001, timeout=30):
    """Wait for the API server to be ready."""
    print(f"⏳ Waiting for server at {host}:{port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"   ✅ Server is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print(f"   ... still waiting ({int(time.time() - start_time)}s)")
    
    print(f"   ❌ Server not ready after {timeout}s")
    return False

def test_memory_through_api(host="localhost", port=8001):
    """Test memory functionality through the API."""
    print("\n🧠 Testing memory through API calls...")
    
    base_url = f"http://{host}:{port}"
    
    # Test 1: Make first API call
    print("\nTest 1: First API call")
    payload = {
        "input": "What is machine learning?",
        "thread_id": "api-test-ray-11"
    }
    
    try:
        response = requests.post(f"{base_url}/query", json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ First call successful")
            print(f"   Response preview: {str(result.get('response', ''))[:100]}...")
        else:
            print(f"   ❌ First call failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ First call error: {e}")
        return False
    
    # Test 2: Make second API call to same thread (should have context)
    print("\nTest 2: Second API call (should have context)")
    payload2 = {
        "input": "Can you give me a simple example?",
        "thread_id": "api-test-ray-11"
    }
    
    try:
        response2 = requests.post(f"{base_url}/query", json=payload2, timeout=60)
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   ✅ Second call successful")
            response_text = str(result2.get('response', ''))
            print(f"   Response preview: {response_text[:100]}...")
            
            # Check if response shows contextual understanding
            if any(keyword in response_text.lower() for keyword in ['machine learning', 'ml', 'example', 'such as']):
                print(f"   🎯 SUCCESS: Response shows contextual understanding!")
                return True
            else:
                print(f"   ⚠️ WARNING: Response may not show context from previous conversation")
                return False
        else:
            print(f"   ❌ Second call failed: {response2.status_code} - {response2.text}")
            return False
    except Exception as e:
        print(f"   ❌ Second call error: {e}")
        return False

def analyze_server_logs(process):
    """Analyze server startup logs for memory initialization."""
    print("\n📋 Analyzing server startup logs...")
    
    # Read some output from the process
    if process.stdout:
        try:
            # Read with a timeout
            import select
            ready, _, _ = select.select([process.stdout], [], [], 10)
            
            if ready:
                logs = process.stdout.read()
                print("   Server output:")
                for line in logs.strip().split('\n')[-20:]:  # Last 20 lines
                    if line.strip():
                        print(f"      {line}")
                        
                # Look for memory initialization messages
                if "Conversation memory initialized successfully" in logs:
                    print(f"   🎯 FOUND: Conversation memory initialization successful!")
                    return True
                elif "Failed to initialize conversation memory" in logs:
                    print(f"   ❌ FOUND: Memory initialization failed!")
                    return False
                elif "Could not load default configuration" in logs:
                    print(f"   ❌ FOUND: Configuration loading failed!")
                    return False
                else:
                    print(f"   ⚠️ No memory initialization messages found in logs")
                    return None
            else:
                print("   ⚠️ No output available from server process")
                return None
                
        except Exception as e:
            print(f"   ❌ Error reading server logs: {e}")
            return None
    else:
        print("   ❌ No stdout available from server process")
        return None

def main():
    """Run the complete API server memory test."""
    print("🔍 Testing API Server Memory Integration")
    print("=" * 50)
    
    # Start the API server
    server_process = start_api_server()
    
    try:
        # Wait for server to be ready
        if not wait_for_server():
            print("\n❌ FAILED: Server did not start properly")
            return False
        
        # Analyze startup logs
        logs_ok = analyze_server_logs(server_process)
        
        # Test memory through API
        memory_works = test_memory_through_api()
        
        print("\n" + "=" * 50)
        print("🎯 TEST RESULTS:")
        
        if logs_ok is True:
            print("   ✅ Server logs show memory initialization SUCCESS")
        elif logs_ok is False:
            print("   ❌ Server logs show memory initialization FAILED")
        else:
            print("   ⚠️ Server logs: Memory initialization status UNCLEAR")
        
        if memory_works:
            print("   ✅ API memory functionality is WORKING")
            print("\n🎉 CONCLUSION: Memory system is working in production!")
            print("   The ray-11 issue may be resolved, or was a temporary problem.")
        else:
            print("   ❌ API memory functionality is NOT WORKING")
            print("\n🔧 CONCLUSION: Memory system has issues in production.")
            print("   Possible causes:")
            print("   - Startup event not running")
            print("   - DATABASE_URL not set in production environment")
            print("   - Database connection issues")
            print("   - Process isolation problems")
        
        return memory_works
        
    finally:
        # Cleanup: terminate the server
        print(f"\n🧹 Cleaning up server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=10)
            print("   ✅ Server terminated gracefully")
        except subprocess.TimeoutExpired:
            print("   ⚠️ Server didn't terminate gracefully, killing...")
            server_process.kill()
            server_process.wait()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")
        sys.exit(1)