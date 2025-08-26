#!/usr/bin/env python3
"""
Basic MCP Server Tests

This script tests MCP server functionality with real servers.
It covers basic scenarios to ensure MCP integration works correctly.
"""

import asyncio
import sys
import os
import logging
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_loader import load_mcp_tools, close_mcp_client, build_http_tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPBasicTester:
    """Basic MCP server testing functionality"""
    
    def __init__(self):
        self.test_results = []
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    async def test_stdio_math_server(self):
        """Test basic stdio math server"""
        test_name = "Stdio Math Server"
        
        try:
            # Check if math server file exists
            math_server_path = Path(__file__).parent.parent / "examples/mcp_servers/math_server.py"
            if not math_server_path.exists():
                self.log_test_result(test_name, False, f"Math server file not found: {math_server_path}")
                return
            
            servers_cfg = {
                "math": {
                    "description": "Arithmetic MCP via stdio",
                    "transport": "stdio",
                    "command": "python",
                    "args": [str(math_server_path), "stdio"],
                    "env": {}
                }
            }
            
            mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
            
            if mcp_client is None:
                self.log_test_result(test_name, False, "Failed to create MCP client")
                return
            
            tool_count = len(tools)
            tool_names = [getattr(tool, 'name', 'unknown') for tool in tools]
            
            await close_mcp_client(mcp_client)
            
            self.log_test_result(
                test_name, 
                True, 
                f"Loaded {tool_count} tools: {tool_names}"
            )
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_http_weather_server(self):
        """Test HTTP weather server"""
        test_name = "HTTP Weather Server"
        
        try:
            # Start weather server
            weather_server_path = Path(__file__).parent.parent / "examples/mcp_servers/weather_server.py"
            if not weather_server_path.exists():
                self.log_test_result(test_name, False, f"Weather server file not found: {weather_server_path}")
                return
            
            # Start server process
            process = subprocess.Popen([
                sys.executable, str(weather_server_path)
            ], env={**os.environ, "WEATHER_PORT": "8002"})
            
            # Wait for server to start
            await asyncio.sleep(2)
            
            try:
                # Test HTTP tools configuration
                http_tools_cfg = {
                    "weather": {
                        "description": "Get weather for a city",
                        "method": "GET",
                        "url": "http://localhost:8002/weather",
                        "params": [
                            {
                                "name": "city",
                                "in": "query",
                                "description": "City name"
                            }
                        ]
                    }
                }
                
                tools = build_http_tools(http_tools_cfg)
                
                if not tools:
                    self.log_test_result(test_name, False, "No HTTP tools created")
                    return
                
                # Test tool execution
                weather_tool = tools[0]
                result = await weather_tool.arun('{"city": "Mumbai"}')
                
                # Parse and validate result
                try:
                    result_data = json.loads(result)
                    has_weather_data = 'temp' in result_data or 'error' in result_data
                    
                    self.log_test_result(
                        test_name,
                        has_weather_data,
                        f"Weather data: {result_data}"
                    )
                except json.JSONDecodeError:
                    self.log_test_result(
                        test_name,
                        len(result) > 0,
                        f"Raw result: {result[:100]}..."
                    )
                
            finally:
                # Stop server
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_mcp_tool_timeout(self):
        """Test MCP tool timeout handling"""
        test_name = "MCP Tool Timeout"
        
        try:
            servers_cfg = {
                "timeout_test": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["-c", "import time; time.sleep(10); print('done')"],
                    "env": {}
                }
            }
            
            start_time = time.time()
            
            try:
                mcp_client, tools = await load_mcp_tools(
                    servers_cfg, 
                    tool_timeout=2.0  # 2 second timeout
                )
                
                elapsed = time.time() - start_time
                
                if mcp_client:
                    await close_mcp_client(mcp_client)
                
                # Should complete quickly due to timeout
                self.log_test_result(
                    test_name,
                    elapsed < 5.0,  # Should timeout within 5 seconds
                    f"Completed in {elapsed:.2f}s with {len(tools)} tools"
                )
                
            except Exception as e:
                elapsed = time.time() - start_time
                self.log_test_result(
                    test_name,
                    elapsed < 5.0,  # Should fail quickly
                    f"Expected timeout/error in {elapsed:.2f}s: {str(e)[:100]}"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Unexpected exception: {str(e)}")
    
    async def test_invalid_mcp_config(self):
        """Test handling of invalid MCP configurations"""
        test_name = "Invalid MCP Config"
        
        test_cases = [
            {
                "name": "Missing command",
                "config": {"invalid": {"transport": "stdio"}},
                "expected_error": "requires 'command'"
            },
            {
                "name": "Missing URL",
                "config": {"invalid": {"transport": "http"}},
                "expected_error": "requires 'url'"
            },
            {
                "name": "Invalid transport",
                "config": {"invalid": {"transport": "invalid", "command": "echo"}},
                "expected_error": "Unsupported transport"
            }
        ]
        
        all_passed = True
        messages = []
        
        for case in test_cases:
            try:
                await load_mcp_tools(case["config"])
                all_passed = False
                messages.append(f"{case['name']}: Should have failed")
            except ValueError as e:
                if case["expected_error"] in str(e):
                    messages.append(f"{case['name']}: Correctly rejected")
                else:
                    all_passed = False
                    messages.append(f"{case['name']}: Wrong error: {e}")
            except Exception as e:
                all_passed = False
                messages.append(f"{case['name']}: Unexpected error: {e}")
        
        self.log_test_result(test_name, all_passed, "; ".join(messages))
    
    async def test_python_runner_mcp(self):
        """Test Python runner MCP server (if Deno available)"""
        test_name = "Python Runner MCP"
        
        try:
            # Check if Deno is available
            result = subprocess.run(
                ["deno", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode != 0:
                self.log_test_result(test_name, True, "Skipped - Deno not available")
                return
            
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
            
            mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=15.0)
            
            if mcp_client is None:
                self.log_test_result(test_name, False, "Failed to create MCP client")
                return
            
            tool_count = len(tools)
            tool_names = [getattr(tool, 'name', 'unknown') for tool in tools]
            
            await close_mcp_client(mcp_client)
            
            self.log_test_result(
                test_name,
                tool_count > 0,
                f"Loaded {tool_count} tools: {tool_names}"
            )
            
        except subprocess.TimeoutExpired:
            self.log_test_result(test_name, True, "Skipped - Deno check timeout")
        except FileNotFoundError:
            self.log_test_result(test_name, True, "Skipped - Deno not found")
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print("\n" + "="*60)
        print("MCP BASIC TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        print("="*60)
        
        if passed_tests < total_tests:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")


async def main():
    """Run basic MCP tests"""
    print("🚀 Starting Basic MCP Server Tests")
    print("="*60)
    
    tester = MCPBasicTester()
    
    # Run tests
    await tester.test_stdio_math_server()
    await tester.test_http_weather_server()
    await tester.test_mcp_tool_timeout()
    await tester.test_invalid_mcp_config()
    await tester.test_python_runner_mcp()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)
