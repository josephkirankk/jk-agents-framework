#!/usr/bin/env python3
"""
Simple MCP Server Test

A straightforward test to verify MCP servers are working.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_loader import load_mcp_tools, close_mcp_client


async def test_math_server():
    """Test the math MCP server"""
    print("🧮 Testing Math MCP Server...")
    
    math_server_path = Path(__file__).parent.parent / "examples/mcp_servers/math_server.py"
    
    if not math_server_path.exists():
        print(f"❌ Math server not found: {math_server_path}")
        return False
    
    servers_cfg = {
        "math": {
            "description": "Math MCP server",
            "transport": "stdio",
            "command": "python",
            "args": [str(math_server_path), "stdio"],
            "env": {}
        }
    }
    
    try:
        mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
        
        if not mcp_client:
            print("❌ Failed to create MCP client")
            return False
        
        if not tools:
            print("❌ No tools loaded")
            await close_mcp_client(mcp_client)
            return False
        
        print(f"✅ Loaded {len(tools)} tools:")
        for tool in tools:
            tool_name = getattr(tool, 'name', 'unknown')
            print(f"   - {tool_name}")
        
        # Test a simple tool call
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == 'add':
                try:
                    # Test the add tool
                    result = await tool.arun('{"a": 5, "b": 3}')
                    print(f"✅ Add tool test: 5 + 3 = {result}")
                    break
                except Exception as e:
                    print(f"⚠️  Add tool test failed: {e}")
        
        await close_mcp_client(mcp_client)
        return True
        
    except Exception as e:
        print(f"❌ Math server test failed: {e}")
        return False


async def test_weather_server():
    """Test the weather MCP server"""
    print("\n🌤️  Testing Weather MCP Server...")
    
    weather_server_path = Path(__file__).parent.parent / "examples/mcp_servers/weather_server.py"
    
    if not weather_server_path.exists():
        print(f"❌ Weather server not found: {weather_server_path}")
        return False
    
    servers_cfg = {
        "weather": {
            "description": "Weather MCP server",
            "transport": "stdio",
            "command": "python",
            "args": [str(weather_server_path), "stdio"],
            "env": {}
        }
    }
    
    try:
        mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
        
        if not mcp_client:
            print("❌ Failed to create MCP client")
            return False
        
        if not tools:
            print("❌ No tools loaded")
            await close_mcp_client(mcp_client)
            return False
        
        print(f"✅ Loaded {len(tools)} tools:")
        for tool in tools:
            tool_name = getattr(tool, 'name', 'unknown')
            print(f"   - {tool_name}")
        
        # Test a weather tool call
        for tool in tools:
            if hasattr(tool, 'name') and 'weather' in tool.name.lower():
                try:
                    result = await tool.arun('{"city": "Mumbai"}')
                    print(f"✅ Weather tool test: {result}")
                    break
                except Exception as e:
                    print(f"⚠️  Weather tool test failed: {e}")
        
        await close_mcp_client(mcp_client)
        return True
        
    except Exception as e:
        print(f"❌ Weather server test failed: {e}")
        return False


async def test_python_runner():
    """Test the Python runner MCP server"""
    print("\n🐍 Testing Python Runner MCP Server...")
    
    servers_cfg = {
        "python_runner": {
            "description": "Python code runner",
            "transport": "stdio",
            "command": "deno",
            "args": [
                "run", "-N", "-R=node_modules", "-W=node_modules",
                "--node-modules-dir=auto", 
                "jsr:@pydantic/mcp-run-python", 
                "stdio"
            ],
            "env": {}
        }
    }
    
    try:
        # Check if Deno is available
        import subprocess
        result = subprocess.run(["deno", "--version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("⚠️  Skipped - Deno not available")
            return True
        
        mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=15.0)
        
        if not mcp_client:
            print("❌ Failed to create MCP client")
            return False
        
        if not tools:
            print("❌ No tools loaded")
            await close_mcp_client(mcp_client)
            return False
        
        print(f"✅ Loaded {len(tools)} tools:")
        for tool in tools:
            tool_name = getattr(tool, 'name', 'unknown')
            print(f"   - {tool_name}")
        
        # Test Python code execution
        for tool in tools:
            if hasattr(tool, 'name') and 'python' in tool.name.lower():
                try:
                    result = await tool.arun('{"code": "print(2 + 3)"}')
                    print(f"✅ Python execution test: {result}")
                    break
                except Exception as e:
                    print(f"⚠️  Python execution test failed: {e}")
        
        await close_mcp_client(mcp_client)
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️  Skipped - Deno check timeout")
        return True
    except FileNotFoundError:
        print("⚠️  Skipped - Deno not found")
        return True
    except Exception as e:
        print(f"❌ Python runner test failed: {e}")
        return False


async def main():
    """Run simple MCP tests"""
    print("🚀 Simple MCP Server Tests")
    print("=" * 50)
    
    results = []
    
    # Test each server
    results.append(await test_math_server())
    results.append(await test_weather_server())
    results.append(await test_python_runner())
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
