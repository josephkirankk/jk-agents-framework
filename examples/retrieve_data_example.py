#!/usr/bin/env python3
"""
Example script for retrieving data from the Large Data Retrieval API

This script demonstrates how to:
1. Retrieve data by reference ID
2. List all available datasets
3. Save data to files
4. Filter and process retrieved data
"""

import requests
import json
import sys
from typing import Dict, Any, List, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_DATA_ENDPOINT = f"{API_BASE_URL}/api/data"


def check_api_health() -> bool:
    """Check if the API server is running and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Server is healthy")
            print(f"   Version: {health_data.get('version')}")
            print(f"   LiteLLM Available: {health_data.get('litellm_available')}")
            return True
        else:
            print(f"❌ API Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API server at {API_BASE_URL}")
        print(f"   Make sure the server is running: python litellm_api.py")
        return False
    except Exception as e:
        print(f"❌ Error checking API health: {e}")
        return False


def retrieve_data_by_reference(reference_id: str, thread_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve data by reference ID.
    
    Args:
        reference_id: Reference ID (format: ref_[a-f0-9]{12})
        thread_id: Optional thread ID for filtering
    
    Returns:
        Dictionary with status, reference_id, data, and metadata, or None if error
    """
    try:
        url = f"{API_DATA_ENDPOINT}/{reference_id}"
        params = {}
        if thread_id:
            params['thread_id'] = thread_id
        
        print(f"\n📥 Retrieving data for reference ID: {reference_id}")
        if thread_id:
            print(f"   Thread ID filter: {thread_id}")
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data retrieved successfully")
            print(f"   Status: {data['status']}")
            print(f"   Reference ID: {data['reference_id']}")
            
            # Print metadata
            metadata = data['metadata']
            print(f"\n📊 Metadata:")
            print(f"   Tool Name: {metadata.get('tool_name')}")
            print(f"   Content Type: {metadata.get('content_type')}")
            print(f"   Size: {metadata.get('size_bytes'):,} bytes ({metadata.get('size_bytes') / 1024 / 1024:.2f} MB)")
            print(f"   Compressed: {metadata.get('compressed')}")
            print(f"   Created At: {metadata.get('created_at')}")
            print(f"   Access Count: {metadata.get('access_count')}")
            
            if 'record_count' in metadata:
                print(f"   Record Count: {metadata.get('record_count')}")
            
            # Print data summary
            dataset = data['data']
            if isinstance(dataset, list):
                print(f"\n📋 Data Summary:")
                print(f"   Type: list")
                print(f"   Length: {len(dataset)} records")
                if len(dataset) > 0:
                    print(f"   First record: {json.dumps(dataset[0], indent=6)}")
            elif isinstance(dataset, dict):
                print(f"\n📋 Data Summary:")
                print(f"   Type: dict")
                print(f"   Keys: {list(dataset.keys())[:10]}")
            
            return data
        
        elif response.status_code == 400:
            error = response.json()
            print(f"❌ Bad Request: {error.get('detail')}")
            return None
        
        elif response.status_code == 404:
            error = response.json()
            print(f"❌ Not Found: {error.get('detail')}")
            return None
        
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"   {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error retrieving data: {e}")
        return None


def list_all_datasets(limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
    """
    List all stored datasets.
    
    Args:
        limit: Maximum number of datasets to return
        offset: Offset for pagination
    
    Returns:
        Dictionary with status, total_count, and datasets list, or None if error
    """
    try:
        print(f"\n📋 Listing datasets (limit={limit}, offset={offset})")
        
        params = {'limit': limit, 'offset': offset}
        response = requests.get(API_DATA_ENDPOINT, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Datasets retrieved successfully")
            print(f"   Total Count: {data['total_count']}")
            print(f"   Returned: {len(data['datasets'])} datasets")
            
            # Print dataset summaries
            print(f"\n📊 Datasets:")
            for i, dataset in enumerate(data['datasets'], 1):
                print(f"\n   {i}. Reference ID: {dataset['reference_id']}")
                print(f"      Tool Name: {dataset['tool_name']}")
                print(f"      Size: {dataset['size_bytes']:,} bytes ({dataset['size_bytes'] / 1024 / 1024:.2f} MB)")
                print(f"      Created: {dataset['created_at']}")
                print(f"      Access Count: {dataset['access_count']}")
                
                metadata = dataset.get('metadata', {})
                if 'record_count' in metadata:
                    print(f"      Record Count: {metadata['record_count']}")
            
            return data
        
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"   {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error listing datasets: {e}")
        return None


def save_data_to_file(data: Dict[str, Any], filename: str, data_only: bool = False):
    """
    Save retrieved data to a JSON file.
    
    Args:
        data: Data dictionary from API
        filename: Output filename
        data_only: If True, save only the data field; if False, save complete response
    """
    try:
        print(f"\n💾 Saving data to file: {filename}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            if data_only:
                json.dump(data['data'], f, indent=2, ensure_ascii=False)
                print(f"✅ Data saved successfully (data only)")
            else:
                json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Data saved successfully (complete response)")
        
        # Print file size
        import os
        file_size = os.path.getsize(filename)
        print(f"   File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    except Exception as e:
        print(f"❌ Error saving data to file: {e}")


def main():
    """Main function demonstrating API usage."""
    print("="*80)
    print("LARGE DATA RETRIEVAL API - EXAMPLE CLIENT")
    print("="*80)
    
    # Check API health
    if not check_api_health():
        print("\n⚠️  Please start the API server first:")
        print("   cd /path/to/jk-agents-core")
        print("   source .venv/bin/activate")
        print("   python litellm_api.py")
        sys.exit(1)
    
    # Example 1: List all datasets
    print("\n" + "="*80)
    print("EXAMPLE 1: List All Datasets")
    print("="*80)
    datasets_response = list_all_datasets(limit=5)
    
    if datasets_response and datasets_response['datasets']:
        # Get the first reference ID for the next example
        first_ref_id = datasets_response['datasets'][0]['reference_id']
        
        # Example 2: Retrieve data by reference ID
        print("\n" + "="*80)
        print("EXAMPLE 2: Retrieve Data by Reference ID")
        print("="*80)
        data_response = retrieve_data_by_reference(first_ref_id)
        
        if data_response:
            # Example 3: Save data to file
            print("\n" + "="*80)
            print("EXAMPLE 3: Save Data to File")
            print("="*80)
            
            # Save complete response
            save_data_to_file(data_response, "complete_response.json", data_only=False)
            
            # Save data only
            save_data_to_file(data_response, "data_only.json", data_only=True)
    
    # Example 4: Test error handling
    print("\n" + "="*80)
    print("EXAMPLE 4: Error Handling")
    print("="*80)
    
    # Invalid reference ID format
    print("\n--- Test 1: Invalid Reference ID Format ---")
    retrieve_data_by_reference("invalid_ref")
    
    # Non-existent reference ID
    print("\n--- Test 2: Non-existent Reference ID ---")
    retrieve_data_by_reference("ref_000000000000")
    
    print("\n" + "="*80)
    print("EXAMPLES COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

