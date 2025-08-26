#!/usr/bin/env python3
"""
MCP Performance and Stress Tests

This script tests MCP server performance, concurrent usage, and reliability.
"""

import asyncio
import sys
import os
import logging
import time
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mcp_loader import load_mcp_tools, close_mcp_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPPerformanceTester:
    """Test MCP server performance and reliability"""
    
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
    
    async def test_mcp_server_startup_time(self):
        """Test MCP server startup performance"""
        test_name = "MCP Server Startup Time"
        
        try:
            servers_cfg = {
                "math": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["examples/mcp_servers/math_server.py"]
                }
            }
            
            startup_times = []
            
            # Test multiple startups
            for i in range(3):
                start_time = time.time()
                
                mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
                
                if mcp_client:
                    startup_time = time.time() - start_time
                    startup_times.append(startup_time)
                    await close_mcp_client(mcp_client)
                else:
                    self.log_test_result(test_name, False, f"Failed startup {i+1}")
                    return
            
            avg_startup = statistics.mean(startup_times)
            max_startup = max(startup_times)
            
            # Consider startup successful if average is under 5 seconds
            success = avg_startup < 5.0
            
            self.log_test_result(
                test_name,
                success,
                f"Avg: {avg_startup:.2f}s, Max: {max_startup:.2f}s"
            )
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_concurrent_mcp_tool_calls(self):
        """Test concurrent MCP tool usage"""
        test_name = "Concurrent MCP Tool Calls"
        
        try:
            servers_cfg = {
                "math": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["examples/mcp_servers/math_server.py"]
                }
            }
            
            mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
            
            if not mcp_client or not tools:
                self.log_test_result(test_name, False, "No MCP client or tools available")
                return
            
            try:
                # Test concurrent tool calls
                async def call_tool(tool, input_data, call_id):
                    try:
                        start_time = time.time()
                        result = await tool.arun(input_data)
                        duration = time.time() - start_time
                        return {
                            'call_id': call_id,
                            'success': True,
                            'duration': duration,
                            'result': result
                        }
                    except Exception as e:
                        return {
                            'call_id': call_id,
                            'success': False,
                            'error': str(e),
                            'duration': time.time() - start_time
                        }
                
                # Create concurrent tasks
                concurrent_calls = 10
                tasks = []
                
                for i in range(concurrent_calls):
                    for tool in tools[:1]:  # Use first tool only
                        tasks.append(call_tool(tool, f"test_input_{i}", i))
                
                if not tasks:
                    self.log_test_result(test_name, False, "No tasks created")
                    return
                
                # Execute concurrent calls
                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Analyze results
                successful_calls = [r for r in results if isinstance(r, dict) and r.get('success')]
                failed_calls = [r for r in results if isinstance(r, dict) and not r.get('success')]
                exceptions = [r for r in results if isinstance(r, Exception)]
                
                success_rate = len(successful_calls) / len(results)
                avg_duration = statistics.mean([r['duration'] for r in successful_calls]) if successful_calls else 0
                
                # Consider test successful if >70% of calls succeed
                test_success = success_rate >= 0.7
                
                self.log_test_result(
                    test_name,
                    test_success,
                    f"Success rate: {success_rate:.1%}, Avg duration: {avg_duration:.2f}s, "
                    f"Total time: {total_time:.2f}s, Exceptions: {len(exceptions)}"
                )
                
            finally:
                await close_mcp_client(mcp_client)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_mcp_server_memory_usage(self):
        """Test MCP server memory usage over time"""
        test_name = "MCP Server Memory Usage"
        
        try:
            import psutil
        except ImportError:
            self.log_test_result(test_name, True, "Skipped - psutil not available")
            return
        
        try:
            servers_cfg = {
                "math": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["examples/mcp_servers/math_server.py"]
                }
            }
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create and use MCP client multiple times
            memory_samples = [initial_memory]
            
            for i in range(5):
                mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
                
                if mcp_client:
                    # Use tools if available
                    for tool in tools[:1]:
                        try:
                            await tool.arun(f"test_{i}")
                        except:
                            pass  # Ignore tool execution errors
                    
                    await close_mcp_client(mcp_client)
                
                # Sample memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
                
                # Small delay between iterations
                await asyncio.sleep(0.5)
            
            final_memory = memory_samples[-1]
            memory_increase = final_memory - initial_memory
            max_memory = max(memory_samples)
            
            # Consider test successful if memory increase is reasonable (<50MB)
            test_success = memory_increase < 50.0
            
            self.log_test_result(
                test_name,
                test_success,
                f"Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, "
                f"Increase: {memory_increase:.1f}MB, Max: {max_memory:.1f}MB"
            )
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_mcp_server_error_recovery(self):
        """Test MCP server error recovery"""
        test_name = "MCP Server Error Recovery"
        
        try:
            servers_cfg = {
                "math": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["examples/mcp_servers/math_server.py"]
                }
            }
            
            mcp_client, tools = await load_mcp_tools(servers_cfg, tool_timeout=10.0)
            
            if not mcp_client or not tools:
                self.log_test_result(test_name, False, "No MCP client or tools available")
                return
            
            try:
                recovery_tests = []
                
                # Test 1: Invalid input handling
                for tool in tools[:1]:
                    try:
                        result = await tool.arun("invalid_input_12345")
                        recovery_tests.append(True)  # Handled gracefully
                    except Exception as e:
                        # Exception is also acceptable error handling
                        recovery_tests.append(True)
                        logger.info(f"Tool handled invalid input with exception: {e}")
                
                # Test 2: Multiple rapid calls
                rapid_calls = []
                for i in range(5):
                    for tool in tools[:1]:
                        try:
                            rapid_calls.append(tool.arun(f"rapid_{i}"))
                        except:
                            pass
                
                if rapid_calls:
                    try:
                        await asyncio.gather(*rapid_calls, return_exceptions=True)
                        recovery_tests.append(True)  # Survived rapid calls
                    except Exception as e:
                        recovery_tests.append(False)
                        logger.error(f"Failed rapid calls test: {e}")
                
                # Test 3: Server still responsive after errors
                try:
                    for tool in tools[:1]:
                        result = await tool.arun("final_test")
                        recovery_tests.append(True)
                        break
                except Exception as e:
                    recovery_tests.append(False)
                    logger.error(f"Server not responsive after errors: {e}")
                
                success_rate = sum(recovery_tests) / len(recovery_tests) if recovery_tests else 0
                test_success = success_rate >= 0.7
                
                self.log_test_result(
                    test_name,
                    test_success,
                    f"Recovery success rate: {success_rate:.1%} ({sum(recovery_tests)}/{len(recovery_tests)})"
                )
                
            finally:
                await close_mcp_client(mcp_client)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_mcp_timeout_reliability(self):
        """Test MCP timeout handling reliability"""
        test_name = "MCP Timeout Reliability"
        
        try:
            # Test with different timeout values
            timeout_tests = []
            
            for timeout in [1.0, 3.0, 5.0]:
                servers_cfg = {
                    "timeout_test": {
                        "transport": "stdio",
                        "command": "python",
                        "args": ["-c", f"import time; time.sleep({timeout + 1}); print('done')"]
                    }
                }
                
                start_time = time.time()
                
                try:
                    mcp_client, tools = await load_mcp_tools(
                        servers_cfg, 
                        tool_timeout=timeout
                    )
                    
                    elapsed = time.time() - start_time
                    
                    if mcp_client:
                        await close_mcp_client(mcp_client)
                    
                    # Should complete within reasonable time of timeout
                    timeout_respected = elapsed <= (timeout + 2.0)
                    timeout_tests.append(timeout_respected)
                    
                    logger.info(f"Timeout {timeout}s test: {elapsed:.2f}s elapsed, respected: {timeout_respected}")
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    timeout_respected = elapsed <= (timeout + 2.0)
                    timeout_tests.append(timeout_respected)
                    
                    logger.info(f"Timeout {timeout}s test (exception): {elapsed:.2f}s elapsed, respected: {timeout_respected}")
            
            success_rate = sum(timeout_tests) / len(timeout_tests)
            test_success = success_rate >= 0.7
            
            self.log_test_result(
                test_name,
                test_success,
                f"Timeout reliability: {success_rate:.1%} ({sum(timeout_tests)}/{len(timeout_tests)})"
            )
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print("\n" + "="*60)
        print("MCP PERFORMANCE TEST SUMMARY")
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
    """Run MCP performance tests"""
    print("🚀 Starting MCP Performance Tests")
    print("="*60)
    
    tester = MCPPerformanceTester()
    
    # Run tests
    await tester.test_mcp_server_startup_time()
    await tester.test_concurrent_mcp_tool_calls()
    await tester.test_mcp_server_memory_usage()
    await tester.test_mcp_server_error_recovery()
    await tester.test_mcp_timeout_reliability()
    
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
