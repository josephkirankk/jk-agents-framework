"""
PepGenX API Example Script

This example demonstrates different ways to use the PepGenX API with various prompts and models.
It shows how to:
1. Load configuration from environment variables
2. Dynamically load OKTA tokens
3. Make different types of API calls
4. Handle responses and errors

Usage:
    python scripts/pepgenx_example.py
"""

import json
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

def load_okta_token(token_file_path):
    """
    Load the access token from the OKTA token JSON file.
    
    Args:
        token_file_path (str): Path to the OKTA token JSON file
        
    Returns:
        str: The access token
        
    Raises:
        FileNotFoundError: If the token file doesn't exist
        KeyError: If the token file doesn't contain 'access_token'
        json.JSONDecodeError: If the token file is not valid JSON
    """
    try:
        with open(token_file_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
        
        if 'access_token' not in token_data:
            raise KeyError("'access_token' not found in token file")
            
        return token_data['access_token']
    
    except FileNotFoundError:
        raise FileNotFoundError(f"OKTA token file not found: {token_file_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in token file: {e}")

def make_pepgenx_request(api_url, payload, headers):
    """
    Make a request to the PepGenX API.
    
    Args:
        api_url (str): The API endpoint URL
        payload (dict): The request payload
        headers (dict): The request headers
        
    Returns:
        dict: The API response
    """
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": response.text}
        else:
            print(f"Error Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def main():
    """
    Main function demonstrating various PepGenX API calls.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment variables
    api_url = os.getenv('PEPGENX_API_URL')
    project_id = os.getenv('PEPGENX_PROJECT_ID')
    team_id = os.getenv('PEPGENX_TEAM_ID')
    api_key = os.getenv('PEPGENX_API_KEY')
    token_file = os.getenv('OKTA_TOKEN_FILE', 'okta_token.json')
    
    # Validate required environment variables
    required_vars = {
        'PEPGENX_API_URL': api_url,
        'PEPGENX_PROJECT_ID': project_id,
        'PEPGENX_TEAM_ID': team_id,
        'PEPGENX_API_KEY': api_key
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all PepGenX variables are set.")
        sys.exit(1)
    
    # Load the access token from OKTA token file
    try:
        # Construct the full path to the token file (relative to project root)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        token_file_path = project_root / token_file
        
        access_token = load_okta_token(token_file_path)
        print(f"Successfully loaded access token from: {token_file_path}")
        
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"Error loading OKTA token: {e}")
        sys.exit(1)
    
    # Prepare base headers
    base_headers = {
        "cookie": "visid_incap_3083631=xQmXg9ugSTSeQWNV5aJKG3%2F5lWYAAAAAQUIPAAAAAACIihIo4RZCLe8D1XZ69fBj; nlbi_3083631=u4IiKroFyUeUrouepeISQwAAAADzyP2Xf1xAYVAam3ClYNUE; incap_ses_739_3083631=53GlFWkR3G3jUnHd5HRBCkTXHWgAAAAAcM%2FcF27orkeUYYNnqXMmZA%3D%3D; incap_ses_737_3083631=xc%2FHegrYO041pV%2BT51k6CsSKGGgAAAAA%2FftCeaRUgR7PGCQA01OM%2FQ%3D%3D; visid_incap_3138930=jQCFt0HuRKqs20VWpnLhXG1voGcAAAAAQUIPAAAAAADcWv%2FADh8aKjCLcK8gPUCm; nlbi_3138930=4PtqRDVy9EIHmHupZ1hi0QAAAABBA1VwZpBP8VEhRlQj3kI5; incap_ses_737_3138930=dJQYXTRIqm0XSMeU51k6CnEmGmgAAAAWP0uXTJzdwivM6E1SLA0Jw%3D%3D; incap_ses_48_3138930=Bf7uYcntvxQsfJF%2BHoiqAB77GmgAAAAAbv0u8kGRUHsl%2FLRVFXz7ag%3D%3D; incap_ses_33_3138930=hdCYSNHICnIi%2FHZwoj11ACs3EmgAAAAA7OWzUjPM6%2FtolptCJn7jKA%3D%3D",
        "project_id": project_id,
        "team_id": team_id,
        "x-pepgenx-apikey": api_key,
        "Authorization": f"Bearer {access_token}"
    }
    
    # Example 1: Simple creative prompt
    print("\n" + "="*60)
    print("EXAMPLE 1: Creative Writing")
    print("="*60)
    
    payload1 = {
        "generation_model": "claude-3-7-sonnet",
        "custom_prompt": "Write a short story about a robot learning to paint",
        "system_prompt": 1
    }
    
    print(f"Prompt: {payload1['custom_prompt']}")
    response1 = make_pepgenx_request(api_url, payload1, base_headers)
    if response1:
        print(f"Response: {json.dumps(response1, indent=2)}")
    
    # Example 2: Business analysis prompt
    print("\n" + "="*60)
    print("EXAMPLE 2: Business Analysis")
    print("="*60)
    
    payload2 = {
        "generation_model": "claude-3-7-sonnet",
        "custom_prompt": "Analyze the key trends in the beverage industry for 2024",
        "system_prompt": 1
    }
    
    print(f"Prompt: {payload2['custom_prompt']}")
    response2 = make_pepgenx_request(api_url, payload2, base_headers)
    if response2:
        print(f"Response: {json.dumps(response2, indent=2)}")
    
    # Example 3: Technical explanation
    print("\n" + "="*60)
    print("EXAMPLE 3: Technical Explanation")
    print("="*60)
    
    payload3 = {
        "generation_model": "claude-3-7-sonnet",
        "custom_prompt": "Explain how machine learning can be used in supply chain optimization",
        "system_prompt": 1
    }
    
    print(f"Prompt: {payload3['custom_prompt']}")
    response3 = make_pepgenx_request(api_url, payload3, base_headers)
    if response3:
        print(f"Response: {json.dumps(response3, indent=2)}")
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)

if __name__ == "__main__":
    main()
