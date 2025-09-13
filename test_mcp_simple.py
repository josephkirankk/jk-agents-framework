#!/usr/bin/env python3
"""
Simple test to verify MCP library is working correctly.
"""

import asyncio
import sys
import traceback

sys.path.append('.')

async def test_mcp_basic():
    """Test basic MCP functionality."""
    print("=== Testing MCP Basic Functionality ===")
    
    try:
        # Test 1: Import MCP modules
        print("Test 1: Importing MCP modules...")
        from mcp.client.session import ClientSession
        from mcp.shared.session import JSONRPCResponse, JSONRPCError
        import anyio
        print("✓ MCP modules imported successfully")
        
        # Test 2: Test the problematic line
        print("Test 2: Testing anyio.create_memory_object_stream...")
        try:
            response_stream, response_stream_reader = anyio.create_memory_object_stream[JSONRPCResponse | JSONRPCError](1)
            print("✓ anyio.create_memory_object_stream works correctly")
        except Exception as e:
            print(f"✗ anyio.create_memory_object_stream failed: {e}")
            traceback.print_exc()
            
            # Try alternative syntax
            print("Trying alternative syntax...")
            try:
                response_stream, response_stream_reader = anyio.create_memory_object_stream(1)
                print("✓ anyio.create_memory_object_stream (without type annotation) works")
            except Exception as e2:
                print(f"✗ Alternative syntax also failed: {e2}")
                traceback.print_exc()
        
        # Test 3: Test MCP client creation
        print("Test 3: Testing MCP client creation...")
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        servers_config = {
            "restaurant_search": {
                "transport": "sse",
                "url": "http://localhost:8082/test/sse",
                "headers": {
                    "Authorization": "Bearer test-token"
                }
            }
        }
        
        try:
            mcp_client = MultiServerMCPClient(servers_config)
            print("✓ MCP client created successfully")
            
            # Test getting tools
            print("Test 4: Testing tool loading...")
            tools = await mcp_client.get_tools()
            print(f"✓ Tools loaded successfully: {len(tools)} tools")
            for tool in tools:
                print(f"  - {getattr(tool, 'name', 'unknown')}")
                
        except Exception as e:
            print(f"✗ MCP client creation/tool loading failed: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_basic())
