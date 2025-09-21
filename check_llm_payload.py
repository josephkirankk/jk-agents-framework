#!/usr/bin/env python3
"""
Check LLM payload for Unicode characters.
"""

import json
import os

def check_llm_payload():
    """Check the LLM payload for Unicode characters."""
    
    # Find the latest LLM payload file
    agentlog_dir = "agentlog"
    payload_files = [f for f in os.listdir(agentlog_dir) if f.startswith("llm_payload_jk_pilger_new_entries_agent")]
    
    if not payload_files:
        print("No LLM payload files found")
        return
    
    # Get the latest file
    latest_file = sorted(payload_files)[-1]
    filepath = os.path.join(agentlog_dir, latest_file)
    
    print(f"📄 Checking LLM payload file: {latest_file}")
    print("=" * 60)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("🔍 Searching for user input in request messages...")
        
        request_messages = data.get('request', {}).get('messages', [])
        for i, msg in enumerate(request_messages):
            content = msg.get('content', '')
            if 'rack' in content.lower():
                print(f"\n📝 Message {i} ({msg.get('role', 'unknown')}):")
                print(f"   Content preview: {content[:200]}...")
                
                # Look for the USER INPUT section
                if 'USER INPUT:' in content:
                    lines = content.split('\n')
                    for j, line in enumerate(lines):
                        if 'USER INPUT:' in line and j + 1 < len(lines):
                            user_input_line = lines[j + 1]
                            print(f"\n🎯 Found USER INPUT line:")
                            print(f"   Content: {repr(user_input_line)}")
                            print(f"   Display: {user_input_line}")
                            
                            # Check for Unicode characters
                            if any(ord(c) > 127 for c in user_input_line):
                                print("   ✅ Contains Unicode characters")
                            else:
                                print("   ❌ No Unicode characters found")
                            break
        
        print("\n🔍 Searching for user input in response...")
        
        response_content = data.get('response', {}).get('content', '')
        if 'rack' in response_content.lower():
            print(f"📝 Response content preview: {response_content[:200]}...")
        
    except Exception as e:
        print(f"❌ Error reading LLM payload: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_llm_payload()
