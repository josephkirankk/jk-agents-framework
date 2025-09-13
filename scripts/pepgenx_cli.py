"""
PepGenX CLI Tool

A command-line interface for testing PepGenX API endpoints.
Supports listing available models and testing them with custom prompts.

Usage:
    python scripts/pepgenx_cli.py list
    python scripts/pepgenx_cli.py test --model gpt-4o --user-prompt "What is 2+2?"
    python scripts/pepgenx_cli.py test --model claude-3-5-sonnet --system-prompt 1

Configuration:
    - .env file for API endpoints and credentials
    - okta_token.json for the current access token
"""

import argparse
import json
import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv


def load_okta_token(token_file_path):
    """Load the access token from the OKTA token JSON file."""
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


def get_model_provider(model_name):
    """Determine the provider for a given model name."""
    model_name = model_name.lower()
    
    if any(x in model_name for x in ['gpt-', 'gpt4', 'gpt5']):
        return 'openai'
    elif any(x in model_name for x in ['claude-', 'claude3', 'claude4']):
        return 'aws-anthropic'
    elif any(x in model_name for x in ['llama-', 'llama3', 'llama4']):
        return 'aws-meta'
    elif any(x in model_name for x in ['nova-', 'nova']):
        return 'aws-nova'
    elif 'databricks' in model_name:
        return 'databricks'
    else:
        # Default to openai for unknown models
        return 'openai'


def load_config():
    """Load configuration from environment variables and token file."""
    load_dotenv()
    
    # Get configuration from environment variables
    api_base = os.getenv('PEPGENX_API_BASE', 'https://apim-na.qa.mypepsico.com/cgf/pepgenx')
    project_id = os.getenv('PEPGENX_PROJECT_ID')
    team_id = os.getenv('PEPGENX_TEAM_ID')
    api_key = os.getenv('PEPGENX_API_KEY')
    user_id = os.getenv('PEPGENX_USER_ID', 'cli-user')
    token_file = os.getenv('OKTA_TOKEN_FILE', 'okta_token.json')
    
    # Validate required environment variables
    required_vars = {
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
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        token_file_path = project_root / token_file
        
        access_token = load_okta_token(token_file_path)
        
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"Error loading OKTA token: {e}")
        sys.exit(1)
    
    return {
        'api_base': api_base.rstrip('/'),
        'project_id': project_id,
        'team_id': team_id,
        'api_key': api_key,
        'user_id': user_id,
        'access_token': access_token
    }


def build_headers(config, include_user_id=False):
    """Build common headers for API requests."""
    headers = {
        "Content-Type": "application/json",
        "project_id": config['project_id'],
        "team_id": config['team_id'],
        "x-pepgenx-apikey": config['api_key'],
        "Authorization": f"Bearer {config['access_token']}"
    }
    
    if include_user_id:
        headers["user_id"] = config['user_id']
    
    return headers


def list_models(config):
    """List all available models."""
    url = f"{config['api_base']}/v2/llm/list-models"
    headers = build_headers(config)

    try:
        print(f"Fetching models from: {url}")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])

            print(f"\n✅ Found {len(models)} models:")
            print("-" * 85)
            print(f"{'Model Name':<35} {'Provider':<15} {'Restricted':<10}")
            print("-" * 85)

            for i, model in enumerate(models):
                # Handle different possible response formats
                if isinstance(model, dict):
                    # Use the correct field names from the API response
                    name = model.get('model') or model.get('name') or model.get('model_name') or f'Model-{i+1}'
                    provider = model.get('provider') or model.get('model_provider') or 'Unknown'
                    model_type = model.get('type', '')
                    restricted = '✓' if model.get('restricted_access', False) or model.get('restricted', False) else ''

                    # Add type indicator for reasoning models
                    if model_type == 'reasoning':
                        name = f"{name} (reasoning)"

                elif isinstance(model, str):
                    name = model
                    provider = 'Unknown'
                    restricted = ''
                else:
                    name = str(model)
                    provider = 'Unknown'
                    restricted = ''

                print(f"{name:<35} {provider:<15} {restricted:<10}")

            print("-" * 85)

        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")


def is_reasoning_model(model_name):
    """Check if a model is a reasoning model."""
    reasoning_models = ['o1', 'o1-mini', 'o3', 'o3-mini', 'o4-mini', 'claude-4-opus']
    return any(model_name.startswith(rm) for rm in reasoning_models)


def test_model(config, model_name, system_prompt, user_prompt):
    """Test a specific model with given prompts."""
    provider = get_model_provider(model_name)

    # Use different endpoint for reasoning models
    if is_reasoning_model(model_name):
        endpoint = "generate-reasoning-response"
    else:
        endpoint = "generate-response"

    url = f"{config['api_base']}/v2/llm/{provider}/{endpoint}"
    headers = build_headers(config)
    
    # Build payload based on model type
    if is_reasoning_model(model_name):
        # Reasoning models use different payload structure
        payload = {
            "generation_model": model_name,
            "custom_prompt": user_prompt,
            "max_completion_tokens": 1000  # Default for reasoning models
        }

        # Add reasoning_effort for supported models (not o3-mini or o1-mini)
        if not (model_name.startswith('o3-mini') or model_name.startswith('o1-mini')):
            payload["reasoning_effort"] = "medium"

        # Note: Reasoning models don't support system prompts
        # Skip system prompt for reasoning models
    else:
        # Regular models use standard payload
        payload = {
            "generation_model": model_name,
            "custom_prompt": user_prompt
        }

        # Add system prompt if provided (skip if system_prompt is 0)
        if system_prompt is not None and system_prompt != 0:
            if isinstance(system_prompt, int):
                payload["system_prompt"] = system_prompt
            else:
                payload["system_prompt"] = system_prompt
    
    try:
        model_type = "reasoning" if is_reasoning_model(model_name) else "standard"
        print(f"Testing model: {model_name} ({model_type})")
        print(f"Provider: {provider}")
        print(f"Endpoint: {endpoint}")
        print(f"URL: {url}")

        if is_reasoning_model(model_name):
            print(f"System prompt: N/A (reasoning models don't support system prompts)")
        elif system_prompt == 0:
            print(f"System prompt: None (direct response mode)")
        else:
            print(f"System prompt: {system_prompt}")

        print(f"User prompt: {user_prompt}")
        print("-" * 60)
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Handle different response formats
                if 'response' in data:
                    # Standard response format
                    print(f"✅ Response: {data['response']}")
                elif 'choices' in data:
                    # Raw response format
                    if data['choices'] and 'message' in data['choices'][0]:
                        content = data['choices'][0]['message'].get('content', 'No content')
                        print(f"✅ Response: {content}")
                    else:
                        print(f"✅ Raw Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"✅ Full Response: {json.dumps(data, indent=2)}")
                    
            except json.JSONDecodeError:
                print(f"✅ Response (non-JSON): {response.text}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")


def show_system_prompts():
    """Show available system prompts and their descriptions."""
    prompts = {
        0: "No System Prompt - Direct response mode (BEST FOR DIRECT ANSWERS)",
        1: "Content Safety Analyzer - Analyzes prompts against 16 content guidelines",
        2: "Adobe Firefly Image Optimizer - Refines prompts for image generation (DEFAULT)",
        3: "PepsiCo ESG Assistant - Expert for Environmental/Social/Governance queries",
        4: "System Prompt Generator - Creates detailed system prompts for LLMs",
        5: "Prompt Enhancer - Improves clarity, tone, and effectiveness",
        6: "Tool-Aware Assistant - AI assistant with external tool access",
        7: "Prompt Adaptation Expert - Adapts prompts between different AI models"
    }

    print("Available System Prompts:")
    print("=" * 85)
    for prompt_id, description in prompts.items():
        if prompt_id == 0:
            marker = " 🎯"
        elif prompt_id == 2:
            marker = " ⭐"
        else:
            marker = ""
        print(f"{prompt_id}: {description}{marker}")
    print("=" * 85)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PepGenX CLI Tool - List and test LLM models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/pepgenx_cli.py list
  python scripts/pepgenx_cli.py prompts
  python scripts/pepgenx_cli.py test --model gpt-4o
  python scripts/pepgenx_cli.py test --model claude-3-5-sonnet --user-prompt "Explain AI"
  python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 1 --user-prompt "What is 2+2?"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List all available models')

    # Prompts command
    prompts_parser = subparsers.add_parser('prompts', help='Show available system prompts')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test a specific model')
    test_parser.add_argument('--model', '-m', required=True, help='Model name to test')
    test_parser.add_argument('--system-prompt', '-s', type=int, default=2,
                           help='System prompt ID (default: 2 - Adobe Firefly Image Optimizer, use 0 for no system prompt)')
    test_parser.add_argument('--user-prompt', '-u', default='Hello, how are you?',
                           help='User prompt text (default: "Hello, how are you?")')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration
    config = load_config()
    
    # Execute command
    if args.command == 'list':
        list_models(config)
    elif args.command == 'prompts':
        show_system_prompts()
    elif args.command == 'test':
        test_model(config, args.model, args.system_prompt, args.user_prompt)


if __name__ == "__main__":
    main()
