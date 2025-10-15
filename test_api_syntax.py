#!/usr/bin/env python3
"""
Quick test to validate API syntax and v1/query endpoint
"""
import sys
import subprocess
import time
import requests
import os
from pathlib import Path

def test_api_startup():
    """Test if the API can start without syntax errors."""
    print("Testing API syntax...")
    
    # Change to the project directory
    os.chdir("/Users/A80997271/Documents/projects/jk-agents-framework")
    
    try:
        # Start the API server in the background
        proc = subprocess.Popen(
            [sys.executable, "api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for startup
        time.sleep(10)
        
        # Check if it's still running (no syntax errors)
        if proc.poll() is None:
            print("✅ API server started successfully (no syntax errors)")
            
            # Test the endpoints
            try:
                # Test root endpoint
                response = requests.get("http://localhost:8000/", timeout=5)
                if response.status_code == 200:
                    print("✅ Root endpoint working")
                else:
                    print(f"⚠️ Root endpoint returned status {response.status_code}")
                    
                # Test v1/query endpoint with OPTIONS to see if it exists
                response = requests.options("http://localhost:8000/v1/query", timeout=5)
                if response.status_code in [200, 405]:  # 405 is fine, means endpoint exists
                    print("✅ v1/query endpoint exists")
                else:
                    print(f"❌ v1/query endpoint not found (status: {response.status_code})")
                    
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Could not test endpoints: {e}")
                
            # Terminate the server
            proc.terminate()
            proc.wait(timeout=5)
            return True
            
        else:
            # Server exited - check for errors
            stdout, stderr = proc.communicate()
            print(f"❌ API server failed to start:")
            if stderr:
                print(f"STDERR: {stderr}")
            if stdout:
                print(f"STDOUT: {stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False
    finally:
        # Ensure process is terminated
        try:
            proc.terminate()
        except:
            pass

if __name__ == "__main__":
    success = test_api_startup()
    if success:
        print("\n🎉 API is ready for testing!")
        print("\nYou can now use this curl command:")
        print("""
curl --location 'http://localhost:8000/v1/query' \\
--form 'question="Extract complete data including company research"' \\
--form 'config_name="visiting_card_extractor.yaml"' \\
--form 'file=@"/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21.jpeg"' \\
--form 'file=@"/Users/A80997271/Downloads/WhatsApp Image 2025-09-30 at 09.36.21 (1).jpeg"'
        """)
    else:
        print("\n❌ API needs fixing before testing")
        sys.exit(1)
