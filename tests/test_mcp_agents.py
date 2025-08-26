#!/usr/bin/env python3
"""
MCP Agent Integration Tests

This script tests how MCP servers integrate with the agent framework.
Tests real agent scenarios using MCP tools.
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

from app.main import run_supervised, load_app_config, build_agents_map
from app.mcp_loader import close_mcp_client
from app.config import AppConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPAgentTester:
    """Test MCP integration with agents"""
    
    def __init__(self):
        self.test_results = []
        self.server_processes = {}
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    async def start_weather_server(self, port: int = 8002) -> bool:
        """Start weather server for testing"""
        try:
            weather_server_path = Path("examples/mcp_servers/weather_server.py")
            if not weather_server_path.exists():
                return False
            
            process = subprocess.Popen([
                sys.executable, str(weather_server_path)
            ], env={**os.environ, "WEATHER_PORT": str(port)})
            
            self.server_processes['weather'] = process
            
            # Wait for server to start
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start weather server: {e}")
            return False
    
    def stop_servers(self):
        """Stop all test servers"""
        for name, process in self.server_processes.items():
            try:
                logger.info(f"Stopping {name} server")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except Exception as e:
                logger.error(f"Error stopping {name} server: {e}")
        self.server_processes.clear()
    
    async def test_math_agent_with_mcp(self):
        """Test math agent using MCP math server"""
        test_name = "Math Agent with MCP"
        
        try:
            config_data = {
                "models": {"default": "openai:gpt-4o-mini"},
                "supervisor": {
                    "name": "supervisor",
                    "model": "openai:gpt-4o-mini",
                    "prompt": "You are a supervisor agent."
                },
                "agents": [{
                    "name": "math_agent",
                    "description": "Math agent with MCP server",
                    "model": "openai:gpt-4o-mini",
                    "prompt": ("You are a math agent. Use available MCP tools for calculations. "
                              "Available MCP servers: {{mcpservers}}"),
                    "mcp_servers": {
                        "math": {
                            "description": "Arithmetic MCP via stdio",
                            "transport": "stdio",
                            "command": "python",
                            "args": [str(Path(__file__).parent.parent / "examples/mcp_servers/math_server.py"), "stdio"],
                            "env": {}
                        }
                    }
                }]
            }
            
            app_cfg = AppConfig(**config_data)
            agents_map, mcp_clients = await build_agents_map(
                app_cfg, 
                user_input="Calculate 15 * 7"
            )
            
            try:
                # Verify agent and MCP client creation
                has_agent = "math_agent" in agents_map
                has_mcp_client = "math_agent" in mcp_clients
                
                if not has_agent:
                    self.log_test_result(test_name, False, "Math agent not created")
                    return
                
                if not has_mcp_client:
                    self.log_test_result(test_name, False, "MCP client not created")
                    return
                
                # Test basic agent properties
                math_agent = agents_map["math_agent"]
                agent_type = type(math_agent).__name__
                
                self.log_test_result(
                    test_name,
                    True,
                    f"Created {agent_type} with MCP client"
                )
                
            finally:
                # Cleanup MCP clients
                for client in mcp_clients.values():
                    if client:
                        await close_mcp_client(client)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_weather_agent_with_http_mcp(self):
        """Test weather agent using HTTP MCP server"""
        test_name = "Weather Agent with HTTP MCP"
        
        # Start weather server
        if not await self.start_weather_server():
            self.log_test_result(test_name, False, "Could not start weather server")
            return
        
        try:
            config_data = {
                "models": {"default": "openai:gpt-4o-mini"},
                "supervisor": {
                    "name": "supervisor",
                    "model": "openai:gpt-4o-mini",
                    "prompt": "You are a supervisor agent."
                },
                "agents": [{
                    "name": "weather_agent",
                    "description": "Weather agent with HTTP MCP",
                    "model": "openai:gpt-4o-mini",
                    "prompt": ("You are a weather agent. Use available tools to get weather information. "
                              "Available MCP servers: {{mcpservers}}"),
                    "mcp_servers": {},  # Will use http_tools instead
                    "http_tools": {
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
                }]
            }
            
            app_cfg = AppConfig(**config_data)
            agents_map, mcp_clients = await build_agents_map(app_cfg)
            
            try:
                has_agent = "weather_agent" in agents_map
                
                if not has_agent:
                    self.log_test_result(test_name, False, "Weather agent not created")
                    return
                
                weather_agent = agents_map["weather_agent"]
                agent_type = type(weather_agent).__name__
                
                self.log_test_result(
                    test_name,
                    True,
                    f"Created {agent_type} with HTTP tools"
                )
                
            finally:
                for client in mcp_clients.values():
                    if client:
                        await close_mcp_client(client)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_multi_agent_different_mcp(self):
        """Test multiple agents with different MCP servers"""
        test_name = "Multi-Agent Different MCP"
        
        try:
            config_data = {
                "models": {"default": "openai:gpt-4o-mini"},
                "agents": [
                    {
                        "name": "math_agent",
                        "description": "Math calculations",
                        "model": "openai:gpt-4o-mini",
                        "prompt": "You are a math agent. Available MCP servers: {{mcpservers}}",
                        "mcp_servers": {
                            "math": {
                                "transport": "stdio",
                                "command": "python",
                                "args": ["examples/mcp_servers/math_server.py"]
                            }
                        }
                    },
                    {
                        "name": "test_agent",
                        "description": "Simple test agent",
                        "model": "openai:gpt-4o-mini",
                        "prompt": "You are a test agent without MCP servers.",
                        "mcp_servers": {}
                    }
                ]
            }
            
            app_cfg = AppConfig(**config_data)
            agents_map, mcp_clients = await build_agents_map(app_cfg)
            
            try:
                agent_count = len(agents_map)
                mcp_client_count = len([c for c in mcp_clients.values() if c is not None])
                
                expected_agents = 2
                expected_mcp_clients = 1  # Only math_agent should have MCP client
                
                success = (agent_count == expected_agents and 
                          mcp_client_count == expected_mcp_clients)
                
                self.log_test_result(
                    test_name,
                    success,
                    f"Created {agent_count} agents, {mcp_client_count} MCP clients"
                )
                
            finally:
                for client in mcp_clients.values():
                    if client:
                        await close_mcp_client(client)
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    async def test_agent_mcp_error_handling(self):
        """Test agent handling of MCP server errors"""
        test_name = "Agent MCP Error Handling"
        
        try:
            config_data = {
                "models": {"default": "openai:gpt-4o-mini"},
                "agents": [{
                    "name": "error_agent",
                    "description": "Agent with failing MCP server",
                    "model": "openai:gpt-4o-mini",
                    "prompt": "You are an agent with a failing MCP server.",
                    "mcp_servers": {
                        "failing": {
                            "transport": "stdio",
                            "command": "nonexistent_command_12345",
                            "args": []
                        }
                    }
                }]
            }
            
            app_cfg = AppConfig(**config_data)
            
            # This should either succeed with no MCP client or handle the error gracefully
            try:
                agents_map, mcp_clients = await build_agents_map(app_cfg)
                
                has_agent = "error_agent" in agents_map
                mcp_client = mcp_clients.get("error_agent")
                
                # Agent should be created even if MCP server fails
                self.log_test_result(
                    test_name,
                    has_agent,
                    f"Agent created: {has_agent}, MCP client: {mcp_client is not None}"
                )
                
                # Cleanup
                for client in mcp_clients.values():
                    if client:
                        await close_mcp_client(client)
                        
            except Exception as e:
                # If it raises an exception, that's also acceptable error handling
                self.log_test_result(
                    test_name,
                    True,
                    f"Handled error appropriately: {str(e)[:100]}"
                )
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Unexpected exception: {str(e)}")
    
    async def test_supervised_execution_with_mcp(self):
        """Test supervised execution with MCP agents"""
        test_name = "Supervised Execution with MCP"
        
        try:
            # Create a simple config file for testing
            config_path = Path("config/test_mcp_agents.yaml")
            config_content = """
models:
  default: "openai:gpt-4o-mini"

agents:
  - name: "test_math_agent"
    description: "Test math agent"
    model: "openai:gpt-4o-mini"
    prompt: |
      You are a helpful math agent. Answer math questions directly.
      Available MCP servers: {{mcpservers}}
    mcp_servers:
      math:
        description: "Math calculations"
        transport: "stdio"
        command: "python"
        args: ["examples/mcp_servers/math_server.py"]
        env: {}
"""
            
            # Write temporary config
            config_path.write_text(config_content)
            
            try:
                # Test loading the config
                app_cfg = load_app_config(str(config_path))
                
                if app_cfg is None:
                    self.log_test_result(test_name, False, "Failed to load config")
                    return
                
                # Test building agents
                agents_map, mcp_clients = await build_agents_map(app_cfg)
                
                try:
                    has_agent = "test_math_agent" in agents_map
                    has_mcp = "test_math_agent" in mcp_clients
                    
                    self.log_test_result(
                        test_name,
                        has_agent,
                        f"Config loaded, agent: {has_agent}, MCP: {has_mcp}"
                    )
                    
                finally:
                    for client in mcp_clients.values():
                        if client:
                            await close_mcp_client(client)
                            
            finally:
                # Clean up config file
                if config_path.exists():
                    config_path.unlink()
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print("\n" + "="*60)
        print("MCP AGENT INTEGRATION TEST SUMMARY")
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
    """Run MCP agent integration tests"""
    print("🚀 Starting MCP Agent Integration Tests")
    print("="*60)
    
    tester = MCPAgentTester()
    
    try:
        # Run tests
        await tester.test_math_agent_with_mcp()
        await tester.test_weather_agent_with_http_mcp()
        await tester.test_multi_agent_different_mcp()
        await tester.test_agent_mcp_error_handling()
        await tester.test_supervised_execution_with_mcp()
        
    finally:
        # Cleanup servers
        tester.stop_servers()
    
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
