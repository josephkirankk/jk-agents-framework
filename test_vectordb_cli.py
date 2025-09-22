#!/usr/bin/env python3
"""
Test script for VectorDB CLI

This script demonstrates how to use the VectorDB CLI programmatically
and provides examples of all available functionality.
"""

import asyncio
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vectordb_wrapper.cli import VectorDBCLI


async def test_cli_functionality():
    """Test CLI functionality programmatically."""
    print("🧪 Testing VectorDB CLI Functionality")
    print("=" * 50)
    
    # Initialize CLI
    cli = VectorDBCLI()
    
    try:
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        await cli.health_check()
        
        # Test 2: Configuration
        print("\n2. Testing Configuration Display...")
        cli.show_config()
        
        # Test 3: Search Command
        print("\n3. Testing Search Command...")
        await cli.search_command("motor bearing failure")
        
        # Test 4: GET Search Command  
        print("\n4. Testing GET Search Command...")
        await cli.search_get_command("hydraulic pump")
        
        # Test 5: Run Examples
        print("\n5. Testing Example Operations...")
        await cli.run_examples()
        
        print("\n✅ All CLI tests completed successfully!")
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
    finally:
        if cli.client:
            await cli.client.close()


def show_cli_usage():
    """Show CLI usage examples."""
    usage_text = """
🔍 VectorDB CLI Usage Examples

1. Start Interactive CLI:
   python -m vectordb_wrapper.cli

2. Start with Custom URL:
   python -m vectordb_wrapper.cli --url http://localhost:9000

3. Create Sample JSON for Testing:
   python -m vectordb_wrapper.cli --create-sample

4. Run CLI Directly:
   python vectordb_wrapper/cli.py

📋 Interactive Commands (once CLI is running):

Basic Commands:
  help                    - Show help
  health                  - Check API health
  config                  - Show configuration
  
Search Commands:
  search motor failure    - Quick search
  search                  - Interactive search with options
  searchget pump issue    - Quick GET search
  searchget               - Interactive GET search
  
Data Commands:
  upsert                  - Interactive defect creation
  batch                   - Batch upsert from JSON file
  
Utility Commands:
  examples                - Run example operations
  seturl http://new-url   - Change base URL
  quit                    - Exit CLI

💡 Tips:
- Use Tab completion where available
- Press Ctrl+C to cancel any operation
- All operations are logged to vectorlogs/ directory
- Set VECTORDB_BASE_URL environment variable for default URL
- Use the --create-sample flag to generate test data

🔧 Troubleshooting:
- If connection fails, check if VectorDB API is running
- Verify the base URL is correct
- Check firewall settings if using remote URL
- Review logs in vectorlogs/ directory for detailed error info
    """
    print(usage_text)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--usage":
        show_cli_usage()
    else:
        print("Running CLI functionality test...")
        asyncio.run(test_cli_functionality())
