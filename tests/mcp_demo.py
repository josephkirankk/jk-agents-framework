#!/usr/bin/env python3
"""
MCP Server Demo

Demonstrates working MCP servers with real calculations and weather data.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_loader import load_mcp_tools, close_mcp_client


async def demo_math_server():
    """Demonstrate math server capabilities"""
    print("🧮 Math Server Demo:")
    print("-" * 30)
    
    math_cfg = {
        'math': {
            'transport': 'stdio',
            'command': 'python',
            'args': [str(Path(__file__).parent.parent / 'examples/mcp_servers/math_server.py'), 'stdio']
        }
    }
    
    client, tools = await load_mcp_tools(math_cfg, tool_timeout=10)
    
    if not tools:
        print("❌ No math tools loaded")
        return
    
    try:
        # Test addition
        add_tool = next((t for t in tools if t.name == 'add'), None)
        if add_tool:
            result = await add_tool.arun({'a': 15, 'b': 27})
            print(f"  15 + 27 = {result}")
        
        # Test multiplication
        mult_tool = next((t for t in tools if t.name == 'multiply'), None)
        if mult_tool:
            result = await mult_tool.arun({'a': 8, 'b': 7})
            print(f"  8 × 7 = {result}")
        
        # Test expression calculation
        calc_tool = next((t for t in tools if t.name == 'calculate'), None)
        if calc_tool:
            result = await calc_tool.arun({'expression': '2 * 3 + 5'})
            print(f"  2 × 3 + 5 = {result}")
            
            result = await calc_tool.arun({'expression': '(10 + 5) / 3'})
            print(f"  (10 + 5) ÷ 3 = {result}")
        
        # Test division with error handling
        div_tool = next((t for t in tools if t.name == 'divide'), None)
        if div_tool:
            result = await div_tool.arun({'a': 20, 'b': 4})
            print(f"  20 ÷ 4 = {result}")
            
            try:
                result = await div_tool.arun({'a': 10, 'b': 0})
                print(f"  10 ÷ 0 = {result}")
            except Exception as e:
                print(f"  10 ÷ 0 = Error: {e}")
    
    finally:
        await close_mcp_client(client)


async def demo_weather_server():
    """Demonstrate weather server capabilities"""
    print("\n🌤️  Weather Server Demo:")
    print("-" * 30)
    
    weather_cfg = {
        'weather': {
            'transport': 'stdio',
            'command': 'python',
            'args': [str(Path(__file__).parent.parent / 'examples/mcp_servers/weather_server.py'), 'stdio']
        }
    }
    
    client, tools = await load_mcp_tools(weather_cfg, tool_timeout=10)
    
    if not tools:
        print("❌ No weather tools loaded")
        return
    
    try:
        # Test weather lookup
        weather_tool = next((t for t in tools if t.name == 'get_weather'), None)
        if weather_tool:
            cities = ['Mumbai', 'London', 'Tokyo']
            for city in cities:
                result = await weather_tool.arun({'city': city})
                if 'error' not in result:
                    print(f"  {city}: {result['temp']}°C, {result['condition']}")
                else:
                    print(f"  {city}: {result['error']}")
        
        # Test temperature only
        temp_tool = next((t for t in tools if t.name == 'get_temperature'), None)
        if temp_tool:
            result = await temp_tool.arun({'city': 'Delhi'})
            print(f"  Delhi temperature: {result}°C")
        
        # Test available cities
        cities_tool = next((t for t in tools if t.name == 'list_cities'), None)
        if cities_tool:
            result = await cities_tool.arun({})
            print(f"  Available cities: {', '.join(result[:4])}...")
        
        # Test unknown city
        if weather_tool:
            result = await weather_tool.arun({'city': 'UnknownCity'})
            print(f"  UnknownCity: {result.get('error', 'No data')}")
    
    finally:
        await close_mcp_client(client)


async def demo_python_runner():
    """Demonstrate Python runner capabilities"""
    print("\n🐍 Python Runner Demo:")
    print("-" * 30)
    
    # Check if Deno is available
    import subprocess
    try:
        result = subprocess.run(["deno", "--version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("  ⚠️  Skipped - Deno not available")
            return
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ⚠️  Skipped - Deno not found")
        return
    
    python_cfg = {
        'python_runner': {
            'transport': 'stdio',
            'command': 'deno',
            'args': [
                'run', '-N', '-R=node_modules', '-W=node_modules',
                '--node-modules-dir=auto', 
                'jsr:@pydantic/mcp-run-python', 
                'stdio'
            ]
        }
    }
    
    client, tools = await load_mcp_tools(python_cfg, tool_timeout=15)
    
    if not tools:
        print("  ❌ No Python runner tools loaded")
        return
    
    try:
        python_tool = next((t for t in tools if 'python' in t.name.lower()), None)
        if python_tool:
            # Test simple calculation
            result = await python_tool.arun({'code': 'print(2 + 3)'})
            print(f"  2 + 3 = {result}")
            
            # Test more complex code
            code = '''
import math
radius = 5
area = math.pi * radius ** 2
print(f"Circle area (r={radius}): {area:.2f}")
'''
            result = await python_tool.arun({'code': code})
            print(f"  Circle calculation: {result}")
    
    except Exception as e:
        print(f"  ⚠️  Python execution failed: {e}")
    finally:
        await close_mcp_client(client)


async def main():
    """Run MCP server demonstrations"""
    print("🚀 MCP Server Demonstration")
    print("=" * 50)
    print("Testing real MCP servers with actual calculations")
    print("=" * 50)
    
    await demo_math_server()
    await demo_weather_server()
    await demo_python_runner()
    
    print("\n" + "=" * 50)
    print("✅ All MCP server demonstrations completed!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        sys.exit(1)
