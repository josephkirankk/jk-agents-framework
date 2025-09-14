"""
PepGenX API Test Script

This script demonstrates how to call the PepGenX API using configuration from environment variables
and dynamically loading the authorization token from the OKTA token file.

Configuration is loaded from:
- .env file for API endpoints and credentials
- okta_token.json for the current access token

Usage:
    python scripts/antropic_test.py
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

def main():
    """
    Main function to execute the PepGenX API call.
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
    
    # Prepare the API request payload
    payload = {
        "generation_model": "gpt-4o",
        "custom_prompt": "what is 10 + 21738723=?",
        "system_prompt": 2
    }
    
    # Prepare headers with configuration from environment and token file
    headers = {
        "cookie": "visid_incap_3083631=xQmXg9ugSTSeQWNV5aJKG3%2F5lWYAAAAAQUIPAAAAAACIihIo4RZCLe8D1XZ69fBj; nlbi_3083631=u4IiKroFyUeUrouepeISQwAAAADzyP2Xf1xAYVAam3ClYNUE; incap_ses_739_3083631=53GlFWkR3G3jUnHd5HRBCkTXHWgAAAAAcM%2FcF27orkeUYYNnqXMmZA%3D%3D; incap_ses_737_3083631=xc%2FHegrYO041pV%2BT51k6CsSKGGgAAAAA%2FftCeaRUgR7PGCQA01OM%2FQ%3D%3D; visid_incap_3138930=jQCFt0HuRKqs20VWpnLhXG1voGcAAAAAQUIPAAAAAADcWv%2FADh8aKjCLcK8gPUCm; nlbi_3138930=4PtqRDVy9EIHmHupZ1hi0QAAAABBA1VwZpBP8VEhRlQj3kI5; incap_ses_737_3138930=dJQYXTRIqm0XSMeU51k6CnEmGmgAAAAWP0uXTJzdwivM6E1SLA0Jw%3D%3D; incap_ses_48_3138930=Bf7uYcntvxQsfJF%2BHoiqAB77GmgAAAAAbv0u8kGRUHsl%2FLRVFXz7ag%3D%3D; incap_ses_33_3138930=hdCYSNHICnIi%2FHZwoj11ACs3EmgAAAAA7OWzUjPM6%2FtolptCJn7jKA%3D%3D",
        "project_id": project_id,
        "team_id": team_id,
        "x-pepgenx-apikey": api_key,
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        print(f"Making API request to: {api_url}")
        print(f"Using project_id: {project_id}")
        print(f"Using team_id: {team_id}")
        print("Payload:", json.dumps(payload, indent=2))
        
        # Make the API request
        response = requests.post(api_url, json=payload, headers=headers)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        # Try to parse JSON response if possible
        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            print("Response is not valid JSON")
            
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
