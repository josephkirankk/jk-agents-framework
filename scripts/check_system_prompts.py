"""
Check PepGenX System Prompt Catalog
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Load config
    load_dotenv()
    
    # Load token
    try:
        with open('okta_token.json', 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        access_token = token_data['access_token']
    except Exception as e:
        print(f'No valid token found: {e}')
        return
    
    # Get system prompt catalog
    url = 'https://apim-na.qa.mypepsico.com/cgf/pepgenx/v2/llm/system-prompt-catalog'
    headers = {
        'project_id': os.getenv('PEPGENX_PROJECT_ID'),
        'team_id': os.getenv('PEPGENX_TEAM_ID'),
        'x-pepgenx-apikey': os.getenv('PEPGENX_API_KEY'),
        'Authorization': f'Bearer {access_token}'
    }
    
    print("Fetching system prompt catalog...")
    response = requests.get(url, headers=headers)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print("\nSystem Prompt Catalog:")
        print("=" * 80)
        
        # Check if it's a list or has a specific structure
        if isinstance(data, dict):
            if 'SYSTEM_PROMPT_CATALOG' in data:
                prompts = data['SYSTEM_PROMPT_CATALOG']
            elif 'system_prompts' in data:
                prompts = data['system_prompts']
            else:
                print("Full response structure:")
                print(json.dumps(data, indent=2))
                return
        else:
            prompts = data
        
        # Display prompts
        if isinstance(prompts, list):
            for i, prompt in enumerate(prompts):
                if isinstance(prompt, dict):
                    prompt_id = prompt.get('id', i+1)
                    title = prompt.get('title', prompt.get('name', 'No title'))
                    content = prompt.get('content', prompt.get('prompt', 'No content'))
                    
                    print(f"\nID: {prompt_id}")
                    print(f"Title: {title}")
                    print(f"Content: {content[:200]}{'...' if len(content) > 200 else ''}")
                    print("-" * 40)
                else:
                    print(f"ID: {i+1} - {prompt}")
        else:
            print("Unexpected format:")
            print(json.dumps(prompts, indent=2))
            
    else:
        print(f'Error: {response.text}')

if __name__ == "__main__":
    main()
