#!/usr/bin/env python3
"""
Utility script to verify API keys are properly loaded from .env file.
This script checks for the presence of various API keys needed by the jk-agents-framework.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, List

# ANSI color codes for better readability
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def mask_key(key: str) -> str:
    """Mask an API key for display, showing only first 4 and last 4 characters."""
    if not key or len(key) < 10:
        return "[Invalid key format]"
    
    return f"{key[:4]}...{key[-4:]}"

def check_env_keys() -> Dict[str, Dict[str, str]]:
    """Check for environment variables related to API keys."""
    # Try to load from .env file first
    try:
        from dotenv import load_dotenv
        # Look for .env file in the project root (one level up from tests directory)
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'
        
        if env_path.exists():
            print(f"{GREEN}✓ Found .env file at: {env_path}{RESET}")
            load_dotenv(env_path)
            print(f"{GREEN}✓ Loaded environment variables from .env file{RESET}")
        else:
            print(f"{YELLOW}! No .env file found at {env_path}{RESET}")
            print(f"{YELLOW}! Will check for environment variables set directly{RESET}")
    except ImportError:
        print(f"{YELLOW}! python-dotenv not installed, using existing environment variables{RESET}")

    # Define providers and their associated keys
    providers = {
        "Azure OpenAI": {
            "keys": [
                "AZURE_OPENAI_API_KEY", 
                "AZURE_API_KEY"
            ],
            "additional": [
                "AZURE_OPENAI_ENDPOINT", 
                "AZURE_API_BASE",
                "AZURE_OPENAI_API_VERSION", 
                "AZURE_API_VERSION"
            ]
        },
        "OpenAI": {
            "keys": ["OPENAI_API_KEY"],
            "additional": ["OPENAI_BASE_URL"]
        },
        "Google Gemini": {
            "keys": [
                "GOOGLE_API_KEY", 
                "GEMINI_API_KEY"
            ],
            "additional": []
        },
        "Anthropic": {
            "keys": ["ANTHROPIC_API_KEY"],
            "additional": []
        }
    }
    
    # Check all providers and collect results
    results = {}
    
    for provider, config in providers.items():
        key_found = False
        key_value = None
        additional_vars = {}
        
        # Check main API keys
        for key_name in config["keys"]:
            key_value = os.getenv(key_name)
            if key_value:
                key_found = True
                break
        
        # Check additional configuration
        for additional_key in config["additional"]:
            additional_value = os.getenv(additional_key)
            if additional_value:
                additional_vars[additional_key] = additional_value
        
        results[provider] = {
            "key_found": key_found,
            "key_value": key_value,
            "additional_vars": additional_vars
        }
    
    return results

def display_results(results: Dict[str, Dict[str, str]]) -> None:
    """Display the results of API key checks."""
    print(f"\n{BLUE}=== API Key Availability ==={RESET}")
    
    any_provider_available = False
    
    for provider, data in results.items():
        key_found = data["key_found"]
        key_value = data["key_value"]
        additional_vars = data["additional_vars"]
        
        if key_found:
            any_provider_available = True
            print(f"{GREEN}✓ {provider}: API key found{RESET}")
            print(f"  Key: {mask_key(key_value)}")
            
            if additional_vars:
                print(f"  Additional configuration:")
                for key, value in additional_vars.items():
                    print(f"    {key}: {value}")
        else:
            print(f"{YELLOW}✗ {provider}: No API key found{RESET}")
    
    print(f"\n{BLUE}=== Summary ==={RESET}")
    if any_provider_available:
        print(f"{GREEN}✓ At least one model provider is configured and available{RESET}")
    else:
        print(f"{RED}✗ No model providers are configured. Please add API keys to your .env file{RESET}")

def fix_compatibility_vars() -> None:
    """Fix compatibility variables between different providers."""
    # Fix for LangChain AzureChatOpenAI compatibility
    if os.getenv('AZURE_OPENAI_API_VERSION') and not os.getenv('OPENAI_API_VERSION'):
        os.environ['OPENAI_API_VERSION'] = os.getenv('AZURE_OPENAI_API_VERSION')
        print(f"{GREEN}✓ Set OPENAI_API_VERSION from AZURE_OPENAI_API_VERSION for compatibility{RESET}")
    
    # Set GOOGLE_API_KEY from GEMINI_API_KEY if needed
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        print(f"{GREEN}✓ Set GOOGLE_API_KEY from GEMINI_API_KEY for compatibility{RESET}")

def check_model_functionality(results: Dict[str, Dict[str, str]]) -> None:
    """Verify if the loaded API keys actually work by testing a model."""
    # Only run this check if the user confirms
    response = input(f"\nWould you like to test the API keys by making a test request? (y/n): ")
    if response.lower() != 'y':
        print(f"{YELLOW}Skipping API test{RESET}")
        return
    
    try:
        # Get a provider that has an API key
        available_providers = [
            provider for provider, data in results.items() 
            if data["key_found"]
        ]
        
        if not available_providers:
            print(f"{RED}No available providers to test{RESET}")
            return
        
        provider = available_providers[0]
        print(f"\n{BLUE}Testing {provider} API...{RESET}")
        
        # Import the necessary modules
        try:
            from app.enhanced_litellm_wrapper import test_litellm_model
            import asyncio
            
            # Determine which model to test
            model_id = None
            if provider == "Azure OpenAI":
                model_id = "azure/gpt-4.1"
            elif provider == "OpenAI":
                model_id = "openai/gpt-4o-mini"
            elif provider == "Google Gemini":
                model_id = "gemini/gemini-2.5-flash-lite"
            elif provider == "Anthropic":
                model_id = "anthropic/claude-3-haiku"
            
            if not model_id:
                print(f"{RED}No model ID available for {provider}{RESET}")
                return
            
            print(f"Testing model: {model_id}")
            
            # Run the test
            async def run_test():
                result = await test_litellm_model(model_id, "Hello, this is a test message.")
                return result
            
            result = asyncio.run(run_test())
            
            # Display result
            if result.get("success", False):
                print(f"{GREEN}✓ API test successful!{RESET}")
                print(f"Response: {result['response'][:100]}...")
            else:
                print(f"{RED}✗ API test failed: {result.get('error', 'Unknown error')}{RESET}")
        
        except ImportError as e:
            print(f"{RED}Failed to import required modules: {e}{RESET}")
        except Exception as e:
            print(f"{RED}Error during API test: {e}{RESET}")
            import traceback
            print(traceback.format_exc())
    
    except Exception as e:
        print(f"{RED}Error during API test setup: {e}{RESET}")

if __name__ == "__main__":
    print(f"{BLUE}=== .env API Key Loader ==={RESET}")
    
    # Fix compatibility variables
    fix_compatibility_vars()
    
    # Check for API keys
    results = check_env_keys()
    
    # Display results
    display_results(results)
    
    # Test API key functionality if available
    check_model_functionality(results)
