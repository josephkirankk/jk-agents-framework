#!/usr/bin/env python3
"""
Google Models Listing Program - Demo Version

This is a demo version that shows the program structure and expected output
without requiring a valid API key. It includes sample model data based on
the latest Google documentation.
"""

import json
from datetime import datetime
from typing import List, Dict, Any

def get_sample_models() -> Dict[str, List[Dict[str, Any]]]:
    """Return sample model data based on latest Google documentation"""
    
    # Based on latest Google Gen AI SDK documentation
    google_genai_models = [
        {
            'name': 'models/gemini-2.5-flash',
            'display_name': 'Gemini 2.5 Flash',
            'description': 'Fast and efficient model for general text and multimodal tasks',
            'version': '001',
            'input_token_limit': 1048576,
            'output_token_limit': 8192,
            'supported_actions': ['generateContent', 'embedContent', 'countTokens'],
            'sdk': 'google-genai'
        },
        {
            'name': 'models/gemini-2.5-pro',
            'display_name': 'Gemini 2.5 Pro',
            'description': 'Advanced model for coding and complex reasoning tasks',
            'version': '001',
            'input_token_limit': 2097152,
            'output_token_limit': 8192,
            'supported_actions': ['generateContent', 'embedContent', 'countTokens'],
            'sdk': 'google-genai'
        },
        {
            'name': 'models/gemini-2.0-flash',
            'display_name': 'Gemini 2.0 Flash',
            'description': 'Previous generation fast model',
            'version': '001',
            'input_token_limit': 1048576,
            'output_token_limit': 8192,
            'supported_actions': ['generateContent', 'embedContent'],
            'sdk': 'google-genai'
        },
        {
            'name': 'models/gemini-2.0-pro',
            'display_name': 'Gemini 2.0 Pro',
            'description': 'Previous generation advanced model',
            'version': '001',
            'input_token_limit': 2097152,
            'output_token_limit': 8192,
            'supported_actions': ['generateContent', 'embedContent'],
            'sdk': 'google-genai'
        },
        {
            'name': 'models/imagen-3.0-generate-002',
            'display_name': 'Imagen 3.0',
            'description': 'Advanced image generation model',
            'version': '002',
            'input_token_limit': 4096,
            'output_token_limit': 'N/A',
            'supported_actions': ['generateImages'],
            'sdk': 'google-genai'
        },
        {
            'name': 'models/veo-2.0-generate-001',
            'display_name': 'Veo 2.0',
            'description': 'Video generation model',
            'version': '001',
            'input_token_limit': 4096,
            'output_token_limit': 'N/A',
            'supported_actions': ['generateVideos'],
            'sdk': 'google-genai'
        }
    ]
    
    # LangChain models (similar but with different SDK identifier)
    langchain_models = [
        {**model, 'sdk': 'langchain-google-genai'} 
        for model in google_genai_models[:4]  # Only text models for LangChain
    ]
    
    # Direct API models (same data, different source)
    direct_api_models = [
        {**model, 'sdk': 'direct-api'} 
        for model in google_genai_models
    ]
    
    return {
        'google_genai_sdk': google_genai_models,
        'google_genai_sdk_async': google_genai_models,
        'langchain_google_genai': langchain_models,
        'direct_api': direct_api_models
    }

def print_models_table(models: List[Dict[str, Any]], title: str):
    """Print models in a formatted table"""
    if not models:
        print(f"No models found for {title}")
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

def print_detailed_model_info(models: List[Dict[str, Any]], title: str):
    """Print detailed model information"""
    if not models:
        return
    
    print(f"\n{'='*80}")
    print(f"DETAILED INFO: {title.upper()}")
    print(f"{'='*80}")
    
    for i, model in enumerate(models[:3], 1):  # Show first 3 models in detail
        print(f"\n{i}. {model.get('display_name', 'Unknown')}")
        print(f"   Name: {model.get('name', 'N/A')}")
        print(f"   Description: {model.get('description', 'N/A')}")
        print(f"   Version: {model.get('version', 'N/A')}")
        print(f"   Input Token Limit: {model.get('input_token_limit', 'N/A')}")
        print(f"   Output Token Limit: {model.get('output_token_limit', 'N/A')}")
        print(f"   Supported Actions: {', '.join(model.get('supported_actions', []))}")
        print(f"   SDK: {model.get('sdk', 'N/A')}")

def main():
    """Main demo function"""
    print("Google Models Listing Program - DEMO VERSION")
    print("=" * 60)
    print("This demo shows expected output with sample data from latest documentation")
    print("=" * 60)
    
    # Get sample models
    all_models = get_sample_models()
    
    # Display models for each method
    for method_name, models in all_models.items():
        method_title = method_name.replace('_', ' ').title()
        print_models_table(models, method_title)
    
    # Show detailed info for one method
    print_detailed_model_info(all_models['google_genai_sdk'], "Google Gen AI SDK")
    
    # Save sample data to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"google_models_demo_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_models, f, indent=2, ensure_ascii=False)
        print(f"\nSample data saved to: {filename}")
    except Exception as e:
        print(f"Error saving sample data: {e}")
    
    # Summary
    total_unique_models = set()
    for method_models in all_models.values():
        for model in method_models:
            total_unique_models.add(model.get('name', 'Unknown'))
    
    print(f"\n{'='*80}")
    print("DEMO SUMMARY")
    print(f"{'='*80}")
    print(f"Total unique models found: {len(total_unique_models)}")
    print(f"Methods that returned results: {len(all_models)}")
    print(f"Sample data saved to: {filename}")
    
    print(f"\n{'='*80}")
    print("RECOMMENDED MODELS (Latest Documentation)")
    print(f"{'='*80}")
    print("• General Text & Multimodal: gemini-2.5-flash")
    print("• Coding & Complex Reasoning: gemini-2.5-pro")
    print("• Image Generation: imagen-3.0-generate-002")
    print("• Video Generation: veo-2.0-generate-001")
    
    print(f"\n{'='*80}")
    print("DEPRECATED MODELS TO AVOID")
    print(f"{'='*80}")
    print("• gemini-1.5-flash (and variants)")
    print("• gemini-1.5-pro")
    print("• gemini-pro")
    
    print(f"\n{'='*80}")
    print("TO USE WITH REAL API KEY:")
    print(f"{'='*80}")
    print("1. Get API key from: https://aistudio.google.com/")
    print("2. Set environment variable: GOOGLE_API_KEY=your_key_here")
    print("3. Run: python list_google_models.py")

if __name__ == "__main__":
    main()
