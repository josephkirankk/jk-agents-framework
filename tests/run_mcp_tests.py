#!/usr/bin/env python3
"""
MCP Test Runner

This script runs all MCP tests and provides a comprehensive report.
"""

import asyncio
import sys
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MCPTestRunner:
    """Comprehensive MCP test runner"""
    
    def __init__(self):
        self.test_scripts = [
            {
                'name': 'Basic MCP Tests',
                'script': 'test_mcp_basic.py',
                'description': 'Basic MCP server functionality tests'
            },
            {
                'name': 'Agent Integration Tests',
                'script': 'test_mcp_agents.py',
                'description': 'MCP integration with agent framework'
            },
            {
                'name': 'Performance Tests',
                'script': 'test_mcp_performance.py',
                'description': 'MCP server performance and reliability'
            }
        ]
        self.results = {}
    
    def print_header(self):
        """Print test runner header"""
        print("🧪 MCP COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print("Testing MCP server functionality with real servers (no mocks)")
        print("Covers: stdio, HTTP, SSE transports, agent integration, performance")
        print("=" * 80)
        print()
    
    def print_test_info(self, test_info: Dict[str, str]):
        """Print information about the test being run"""
        print(f"📋 Running: {test_info['name']}")
        print(f"   Script: {test_info['script']}")
        print(f"   Description: {test_info['description']}")
        print("-" * 60)
    
    async def run_test_script(self, script_path: Path) -> Dict[str, Any]:
        """Run a test script and capture results"""
        start_time = time.time()
        
        try:
            # Run the test script
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=script_path.parent.parent
            )
            
            stdout, stderr = await process.communicate()
            
            duration = time.time() - start_time
            
            return {
                'success': process.returncode == 0,
                'duration': duration,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'returncode': process.returncode
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'success': False,
                'duration': duration,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'exception': str(e)
            }
    
    def parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse test output to extract summary information"""
        lines = output.split('\n')
        
        summary = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0.0,
            'test_details': []
        }
        
        for line in lines:
            line = line.strip()
            
            # Look for test results
            if '✅ PASS' in line or '❌ FAIL' in line:
                summary['test_details'].append(line)
            
            # Look for summary information
            if 'Total Tests:' in line:
                try:
                    summary['total_tests'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Passed:' in line:
                try:
                    summary['passed_tests'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Failed:' in line:
                try:
                    summary['failed_tests'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Success Rate:' in line:
                try:
                    rate_str = line.split(':')[1].strip().replace('%', '')
                    summary['success_rate'] = float(rate_str)
                except:
                    pass
        
        return summary
    
    def print_test_result(self, test_name: str, result: Dict[str, Any]):
        """Print test result summary"""
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        duration = result['duration']
        
        print(f"{status} - {test_name} ({duration:.1f}s)")
        
        if result['success']:
            # Parse and show summary from output
            summary = self.parse_test_output(result['stdout'])
            if summary['total_tests'] > 0:
                print(f"   Tests: {summary['passed_tests']}/{summary['total_tests']} passed "
                      f"({summary['success_rate']:.1f}%)")
        else:
            print(f"   Return code: {result['returncode']}")
            if result.get('exception'):
                print(f"   Exception: {result['exception']}")
            elif result['stderr']:
                # Show first few lines of stderr
                stderr_lines = result['stderr'].split('\n')[:3]
                for line in stderr_lines:
                    if line.strip():
                        print(f"   Error: {line.strip()}")
        
        print()
    
    def check_prerequisites(self) -> List[str]:
        """Check test prerequisites"""
        issues = []
        
        # Check if example servers exist
        base_path = Path(__file__).parent.parent
        required_files = [
            "examples/mcp_servers/math_server.py",
            "examples/mcp_servers/weather_server.py"
        ]

        for file_path in required_files:
            full_path = base_path / file_path
            if not full_path.exists():
                issues.append(f"Missing example server: {file_path}")
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check if we can import required modules
        try:
            import aiohttp
        except ImportError:
            issues.append("aiohttp module not available")
        
        try:
            import requests
        except ImportError:
            issues.append("requests module not available")
        
        return issues
    
    async def run_all_tests(self):
        """Run all MCP tests"""
        self.print_header()
        
        # Check prerequisites
        issues = self.check_prerequisites()
        if issues:
            print("⚠️  Prerequisites Issues:")
            for issue in issues:
                print(f"   - {issue}")
            print("\nSome tests may fail due to missing prerequisites.\n")
        
        # Run each test script
        for test_info in self.test_scripts:
            self.print_test_info(test_info)
            
            script_path = Path(__file__).parent / test_info['script']
            
            if not script_path.exists():
                print(f"❌ SKIPPED - Script not found: {script_path}")
                self.results[test_info['name']] = {
                    'success': False,
                    'duration': 0,
                    'error': 'Script not found'
                }
                continue
            
            result = await self.run_test_script(script_path)
            self.results[test_info['name']] = result
            
            self.print_test_result(test_info['name'], result)
    
    def print_final_summary(self):
        """Print final test summary"""
        print("=" * 80)
        print("FINAL TEST SUMMARY")
        print("=" * 80)
        
        total_suites = len(self.results)
        passed_suites = sum(1 for r in self.results.values() if r['success'])
        total_duration = sum(r['duration'] for r in self.results.values())
        
        print(f"Test Suites: {passed_suites}/{total_suites} passed")
        print(f"Total Duration: {total_duration:.1f}s")
        print()
        
        # Show detailed results
        for test_name, result in self.results.items():
            status = "✅" if result['success'] else "❌"
            duration = result['duration']
            print(f"{status} {test_name}: {duration:.1f}s")
        
        print("=" * 80)
        
        if passed_suites == total_suites:
            print("🎉 ALL TEST SUITES PASSED!")
        else:
            print(f"⚠️  {total_suites - passed_suites} test suite(s) failed")
            print("\nFor detailed error information, check the output above.")
        
        print("=" * 80)
    
    def save_results(self):
        """Save test results to file"""
        try:
            import json
            
            results_file = Path("test_results.json")
            
            # Prepare results for JSON serialization
            json_results = {
                'timestamp': time.time(),
                'total_suites': len(self.results),
                'passed_suites': sum(1 for r in self.results.values() if r['success']),
                'total_duration': sum(r['duration'] for r in self.results.values()),
                'results': {}
            }
            
            for test_name, result in self.results.items():
                json_results['results'][test_name] = {
                    'success': result['success'],
                    'duration': result['duration'],
                    'returncode': result.get('returncode', 0),
                    'has_stdout': len(result.get('stdout', '')) > 0,
                    'has_stderr': len(result.get('stderr', '')) > 0
                }
            
            with open(results_file, 'w') as f:
                json.dump(json_results, f, indent=2)
            
            print(f"📄 Test results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


async def main():
    """Main test runner function"""
    runner = MCPTestRunner()
    
    try:
        await runner.run_all_tests()
        runner.print_final_summary()
        runner.save_results()
        
        # Exit with appropriate code
        failed_suites = sum(1 for r in runner.results.values() if not r['success'])
        sys.exit(0 if failed_suites == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
