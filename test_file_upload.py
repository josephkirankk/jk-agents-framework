#!/usr/bin/env python3
"""
Test file upload functionality with Azure OpenAI
"""

import requests
import json
from pathlib import Path

def test_file_upload():
    api_base = "http://localhost:8000"
    
    # Test data file
    test_file = Path("test_data.txt")
    
    if not test_file.exists():
        print(f"❌ Test file {test_file} not found")
        return False
    
    print(f"🔍 Testing file upload with Azure OpenAI...")
    print(f"📁 File: {test_file} ({test_file.stat().st_size} bytes)")
    
    # Prepare form data
    data = {
        "agent_name": "azure_text_agent",
        "input": "Analyze this uploaded data file. Calculate average scores for each subject and identify the top performer in each subject. Provide a detailed analysis.",
        "config_path": "config/azure_openai_test.yaml",
        "thread_id": "test-file-upload-azure-1"
    }
    
    # Upload the file
    with open(test_file, 'rb') as f:
        files = {"files": (test_file.name, f, "text/plain")}
        
        try:
            print("📤 Uploading file and processing...")
            response = requests.post(
                f"{api_base}/worker/upload",
                data=data,
                files=files,
                timeout=60
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ File upload successful!")
                print(f"🎯 Success: {result.get('success', False)}")
                print(f"📝 Response preview: {str(result.get('response', ''))[:200]}...")
                
                if result.get('success'):
                    print("\n" + "="*50)
                    print("FULL RESPONSE:")
                    print("="*50)
                    print(result.get('response', ''))
                    print("="*50)
                    return True
                else:
                    print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ HTTP Error {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"Raw response: {response.text[:500]}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Request timed out after 60 seconds")
            return False
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return False

if __name__ == "__main__":
    success = test_file_upload()
    exit(0 if success else 1)
