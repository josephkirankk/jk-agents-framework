#!/usr/bin/env python3
"""
Google Models Listing Program

This program lists all available Google models using multiple approaches:
1. Google Gen AI SDK (new unified SDK)
2. LangChain Google GenAI integration
3. Direct API calls

Based on the latest technical documentation from Google's Gen AI SDK.
"""

import os
import sys
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'google_models_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_and_install_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'google-genai': 'google.genai',  # New unified SDK
        'langchain-google-genai': 'langchain_google_genai',  # LangChain integration
        'requests': 'requests',
        'aiohttp': 'aiohttp'
    }

    missing_packages = []

    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        logger.warning(f"Missing packages: {missing_packages}")
        logger.info("Install missing packages with:")
        for package in missing_packages:
            logger.info(f"  pip install {package}")
        return False

    return True

class GoogleModelsLister:
    """Main class for listing Google models using different approaches"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with API key from environment or parameter"""
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("No API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
            sys.exit(1)
        
        logger.info("Initialized Google Models Lister")
    
    def list_models_with_new_sdk(self) -> List[Dict[str, Any]]:
        """List models using the new Google Gen AI SDK"""
        try:
            from google import genai
            from google.genai import types
            
            logger.info("Using Google Gen AI SDK (new unified SDK)")
            
            # Initialize client
            client = genai.Client(api_key=self.api_key)
            
            models = []
            
            # List all models with pagination
            logger.info("Fetching models...")
            for model in client.models.list():
                model_info = {
                    'name': getattr(model, 'name', 'Unknown'),
                    'display_name': getattr(model, 'display_name', 'N/A'),
                    'description': getattr(model, 'description', 'N/A'),
                    'version': getattr(model, 'version', 'N/A'),
                    'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
                    'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
                    'supported_actions': getattr(model, 'supported_actions', []),
                    'sdk': 'google-genai'
                }
                models.append(model_info)
            
            logger.info(f"Found {len(models)} models using Google Gen AI SDK")
            return models
            
        except ImportError as e:
            logger.error(f"Google Gen AI SDK not available: {e}")
            logger.info("Install with: pip install google-genai")
            return []
        except Exception as e:
            logger.error(f"Error listing models with Google Gen AI SDK: {e}")
            return []
    
    async def list_models_with_new_sdk_async(self) -> List[Dict[str, Any]]:
        """List models using the new Google Gen AI SDK (async)"""
        try:
            from google import genai
            
            logger.info("Using Google Gen AI SDK (async)")
            
            # Initialize client
            client = genai.Client(api_key=self.api_key)
            
            models = []
            
            # List models asynchronously
            async for model in await client.aio.models.list():
                model_info = {
                    'name': getattr(model, 'name', 'Unknown'),
                    'display_name': getattr(model, 'display_name', 'N/A'),
                    'description': getattr(model, 'description', 'N/A'),
                    'version': getattr(model, 'version', 'N/A'),
                    'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
                    'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
                    'supported_actions': getattr(model, 'supported_actions', []),
                    'sdk': 'google-genai-async'
                }
                models.append(model_info)
            
            logger.info(f"Found {len(models)} models using Google Gen AI SDK (async)")
            return models
            
        except ImportError as e:
            logger.error(f"Google Gen AI SDK not available: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing models with Google Gen AI SDK (async): {e}")
            return []
    
    def list_models_with_langchain(self) -> List[Dict[str, Any]]:
        """List models using LangChain Google GenAI integration"""
        try:
            import google.generativeai as genai
            
            logger.info("Using LangChain Google GenAI integration")
            
            # Configure the API key
            genai.configure(api_key=self.api_key)
            
            models = []
            
            # List models
            for model in genai.list_models():
                model_info = {
                    'name': model.name,
                    'display_name': getattr(model, 'display_name', model.name),
                    'description': getattr(model, 'description', 'N/A'),
                    'version': getattr(model, 'version', 'N/A'),
                    'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
                    'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
                    'supported_generation_methods': getattr(model, 'supported_generation_methods', []),
                    'sdk': 'langchain-google-genai'
                }
                models.append(model_info)
            
            logger.info(f"Found {len(models)} models using LangChain integration")
            return models
            
        except ImportError as e:
            logger.error(f"LangChain Google GenAI not available: {e}")
            logger.info("Install with: pip install langchain-google-genai")
            return []
        except Exception as e:
            logger.error(f"Error listing models with LangChain: {e}")
            return []
    
    async def list_models_with_direct_api(self) -> List[Dict[str, Any]]:
        """List models using direct API calls"""
        try:
            import aiohttp
            
            logger.info("Using direct API calls")
            
            url = "https://generativelanguage.googleapis.com/v1beta/models"
            params = {'key': self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        
                        for model in data.get('models', []):
                            model_info = {
                                'name': model.get('name', 'Unknown'),
                                'display_name': model.get('displayName', 'N/A'),
                                'description': model.get('description', 'N/A'),
                                'version': model.get('version', 'N/A'),
                                'input_token_limit': model.get('inputTokenLimit', 'N/A'),
                                'output_token_limit': model.get('outputTokenLimit', 'N/A'),
                                'supported_generation_methods': model.get('supportedGenerationMethods', []),
                                'sdk': 'direct-api'
                            }
                            models.append(model_info)
                        
                        logger.info(f"Found {len(models)} models using direct API")
                        return models
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        error_text = await response.text()
                        logger.error(f"Error response: {error_text}")
                        return []
                        
        except ImportError as e:
            logger.error(f"aiohttp not available: {e}")
            return []
        except Exception as e:
            logger.error(f"Error with direct API call: {e}")
            return []
    
    def print_models_table(self, models: List[Dict[str, Any]], title: str):
        """Print models in a formatted table"""
        if not models:
            logger.warning(f"No models found for {title}")
            return
        
        print(f"\n{'='*80}")
        print(f"{title.upper()}")
        print(f"{'='*80}")
        print(f"{'Model Name':<40} {'Version':<15} {'SDK':<20}")
        print(f"{'-'*80}")
        
        for model in models:
            name = model.get('name', 'Unknown')
            # Clean up model name for display
            display_name = name.replace('models/', '') if name.startswith('models/') else name
            version = str(model.get('version', 'N/A'))
            sdk = model.get('sdk', 'Unknown')
            
            print(f"{display_name:<40} {version:<15} {sdk:<20}")
        
        print(f"{'-'*80}")
        print(f"Total models: {len(models)}")
    
    def save_models_to_json(self, all_models: Dict[str, List[Dict[str, Any]]], filename: str):
        """Save all models to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_models, f, indent=2, ensure_ascii=False)
            logger.info(f"Models saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving models to JSON: {e}")
    
    async def run_all_methods(self):
        """Run all model listing methods and display results"""
        logger.info("Starting comprehensive Google models listing...")
        
        all_models = {}
        
        # Method 1: New Google Gen AI SDK (sync)
        models_new_sdk = self.list_models_with_new_sdk()
        if models_new_sdk:
            all_models['google_genai_sdk'] = models_new_sdk
            self.print_models_table(models_new_sdk, "Google Gen AI SDK (Synchronous)")
        
        # Method 2: New Google Gen AI SDK (async)
        models_new_sdk_async = await self.list_models_with_new_sdk_async()
        if models_new_sdk_async:
            all_models['google_genai_sdk_async'] = models_new_sdk_async
            self.print_models_table(models_new_sdk_async, "Google Gen AI SDK (Asynchronous)")
        
        # Method 3: LangChain integration
        models_langchain = self.list_models_with_langchain()
        if models_langchain:
            all_models['langchain_google_genai'] = models_langchain
            self.print_models_table(models_langchain, "LangChain Google GenAI")
        
        # Method 4: Direct API calls
        models_direct_api = await self.list_models_with_direct_api()
        if models_direct_api:
            all_models['direct_api'] = models_direct_api
            self.print_models_table(models_direct_api, "Direct API Calls")
        
        # Save all results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"google_models_{timestamp}.json"
        self.save_models_to_json(all_models, filename)
        
        # Summary
        total_unique_models = set()
        for method_models in all_models.values():
            for model in method_models:
                total_unique_models.add(model.get('name', 'Unknown'))
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"Total unique models found: {len(total_unique_models)}")
        print(f"Methods that returned results: {len(all_models)}")
        print(f"Results saved to: {filename}")
        print(f"Log file: google_models_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

async def main():
    """Main function"""
    print("Google Models Listing Program")
    print("=" * 50)
    
    # Check dependencies
    if not check_and_install_dependencies():
        logger.error("Please install missing dependencies and run again")
        return
    
    # Initialize lister
    lister = GoogleModelsLister()
    
    # Run all methods
    await lister.run_all_methods()

if __name__ == "__main__":
    asyncio.run(main())
