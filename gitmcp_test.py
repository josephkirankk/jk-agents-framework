#!/usr/bin/env python3
"""
Corrected GitMCP Python Client
Working implementation based on the actual GitMCP protocol discovered.
"""

import asyncio
import aiohttp
import json
import re
import sys
from typing import Dict, List, Optional, Any
import urllib.parse


class GitMCPClient:
    """Working GitMCP client using the correct session-based protocol"""
    
    def __init__(self, owner: str, repo: str, use_generic: bool = False):
        """Initialize GitMCP client"""
        self.owner = owner
        self.repo = repo
        
        if use_generic:
            self.base_url = "https://gitmcp.io/docs"
        else:
            self.base_url = f"https://gitmcp.io/{owner}/{repo}"
        
        self.session = None
        self.session_id = None
        self.message_endpoint = None
        self.message_id = 0
    
    def _next_id(self) -> int:
        """Get next message ID"""
        self.message_id += 1
        return self.message_id
    
    async def connect(self):
        """Connect to GitMCP and establish session"""
        self.session = aiohttp.ClientSession()
        
        # Connect with proper headers that GitMCP expects
        headers = {
            'Accept': 'application/json, text/event-stream',
            'Cache-Control': 'no-cache',
        }
        
        print(f"Connecting to: {self.base_url}")
        
        async with self.session.get(self.base_url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Failed to connect: {response.status}")
            
            print("✓ Connected, reading session endpoint...")
            
            # Read SSE events to get the message endpoint
            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                
                if line_str.startswith('data: '):
                    endpoint_path = line_str[6:]  # Remove 'data: ' prefix
                    
                    # Extract session ID from the endpoint
                    match = re.search(r'sessionId=([a-f0-9]+)', endpoint_path)
                    if match:
                        self.session_id = match.group(1)
                        # Build full message endpoint URL
                        self.message_endpoint = f"{self.base_url}{endpoint_path}"
                        print(f"✓ Session ID: {self.session_id}")
                        print(f"✓ Message endpoint: {self.message_endpoint}")
                        break
            
            if not self.session_id:
                raise Exception("Failed to extract session ID")
    
    async def send_message(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send MCP message using the session endpoint"""
        if not self.message_endpoint:
            raise Exception("Not connected. Call connect() first.")
        
        message = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }
        
        # Use the headers GitMCP expects
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
        }
        
        try:
            async with self.session.post(
                self.message_endpoint,
                json=message,
                headers=headers,
                timeout=30
            ) as response:
                
                print(f"→ {method} (Status: {response.status})")
                
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize MCP session"""
        return await self.send_message("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "python-gitmcp-client",
                "version": "1.0.0"
            }
        })
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return await self.send_message("tools/list", {})
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool"""
        return await self.send_message("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
    
    async def list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        return await self.send_message("resources/list", {})
    
    async def get_documentation(self) -> str:
        """Get repository documentation"""
        result = await self.call_tool("fetch_documentation")
        
        if 'result' in result:
            content = result['result'].get('content', [])
            if content and isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                return '\n'.join(text_parts)
        
        return f"Error or no content: {result}"
    
    async def search_documentation(self, query: str) -> List[str]:
        """Search documentation"""
        result = await self.call_tool("search_documentation", {"query": query})
        
        results = []
        if 'result' in result:
            content = result['result'].get('content', [])
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text = block.get('text', '')
                    try:
                        # Try to parse as JSON if it looks structured
                        data = json.loads(text)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    results.append(item.get('content', str(item)))
                    except:
                        results.append(text)
        
        return results
    
    async def search_code(self, query: str, language: str = None) -> List[Dict[str, Any]]:
        """Search code in repository"""
        args = {"query": query}
        if language:
            args["language"] = language
        
        result = await self.call_tool("search_code", args)
        
        code_results = []
        if 'result' in result:
            content = result['result'].get('content', [])
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text = block.get('text', '')
                    try:
                        data = json.loads(text)
                        if isinstance(data, dict) and 'items' in data:
                            code_results.extend(data['items'])
                    except:
                        code_results.append({"content": text})
        
        return code_results
    
    async def close(self):
        """Close the connection"""
        if self.session:
            await self.session.close()


async def run_complete_demo():
    """Run a complete demo of GitMCP functionality"""
    print("=== Complete GitMCP Demo ===\n")
    
    client = GitMCPClient("tiangolo", "fastapi")
    
    try:
        # Step 1: Connect
        await client.connect()
        
        # Step 2: Initialize
        print("\n🔧 Initializing MCP session...")
        init_result = await client.initialize()
        
        if 'error' in init_result:
            print(f"❌ Initialization failed: {init_result['error']}")
            return
        
        print("✅ MCP session initialized successfully!")
        if 'result' in init_result:
            capabilities = init_result['result'].get('capabilities', {})
            print(f"Server capabilities: {list(capabilities.keys())}")
        
        # Step 3: List tools
        print("\n🛠️ Listing available tools...")
        tools_result = await client.list_tools()
        
        if 'error' in tools_result:
            print(f"❌ Failed to list tools: {tools_result['error']}")
            return
        
        if 'result' in tools_result and 'tools' in tools_result['result']:
            tools = tools_result['result']['tools']
            print(f"✅ Found {len(tools)} tools:")
            
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool['name']}")
                if 'description' in tool:
                    print(f"     📝 {tool['description']}")
            
            # Step 4: Try to get documentation
            print("\n📚 Fetching repository documentation...")
            docs = await client.get_documentation()
            print(f"Documentation preview:\n{docs[:500]}...")
            
            # Step 5: Search documentation
            print("\n🔍 Searching for 'async' in documentation...")
            search_results = await client.search_documentation("async")
            print(f"Found {len(search_results)} results:")
            for i, result in enumerate(search_results[:2], 1):
                print(f"  {i}. {result[:150]}...")
            
            # Step 6: Search code
            print("\n💻 Searching for 'FastAPI' in code...")
            code_results = await client.search_code("FastAPI", "python")
            print(f"Found {len(code_results)} code results:")
            for i, result in enumerate(code_results[:3], 1):
                name = result.get('name', 'Unknown')
                path = result.get('path', 'Unknown')
                print(f"  {i}. {name} ({path})")
        
        else:
            print("❌ No tools found in response")
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        await run_complete_demo()
    else:
        print("Usage: python script.py demo")
        print("\nThis will test the complete GitMCP functionality:")
        print("1. Connect via SSE")
        print("2. Initialize MCP session") 
        print("3. List available tools")
        print("4. Fetch documentation")
        print("5. Search documentation and code")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo cancelled")
    except Exception as e:
        print(f"Demo failed: {e}")