#!/usr/bin/env python3
"""
Large Data MCP Server - Final Verification Script

This script performs a comprehensive verification of the entire implementation:
1. Checks all files are present
2. Verifies MCP server can be imported
3. Validates configuration files
4. Runs integration tests
5. Generates verification report
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class LargeDataMCPVerification:
    """Comprehensive verification of Large Data MCP implementation"""
    
    def __init__(self):
        self.results = []
        self.errors = []
    
    def log_check(self, name: str, passed: bool, details: str = ""):
        """Log a verification check"""
        status = "✅" if passed else "❌"
        self.results.append({
            "check": name,
            "passed": passed,
            "details": details
        })
        print(f"{status} {name}")
        if details:
            print(f"   {details}")
        if not passed:
            self.errors.append(name)
    
    def verify_files_exist(self) -> bool:
        """Verify all required files exist"""
        print("\n" + "="*80)
        print("FILE VERIFICATION")
        print("="*80 + "\n")
        
        required_files = {
            "MCP Server": "app/mcp_large_data_server.py",
            "Configuration": "config/large_data_mcp_demo.yaml",
            "Integration Tests": "test_large_data_mcp_integration.py",
            "Technical Docs": "docs/LARGE_DATA_MCP_SERVER.md",
            "Quick Start": "docs/LARGE_DATA_MCP_QUICKSTART.md",
            "Demo Script": "examples/large_data_mcp_demo.py",
            "Implementation Summary": "LARGE_DATA_MCP_IMPLEMENTATION.md",
        }
        
        all_exist = True
        for name, path in required_files.items():
            file_path = Path(path)
            exists = file_path.exists()
            size = file_path.stat().st_size if exists else 0
            
            self.log_check(
                f"{name} exists",
                exists,
                f"Path: {path}, Size: {size:,} bytes" if exists else f"Missing: {path}"
            )
            
            if not exists:
                all_exist = False
        
        return all_exist
    
    def verify_imports(self) -> bool:
        """Verify all modules can be imported"""
        print("\n" + "="*80)
        print("IMPORT VERIFICATION")
        print("="*80 + "\n")
        
        all_imported = True
        
        # Test MCP server import
        try:
            from app import mcp_large_data_server
            self.log_check(
                "MCP Server module imports",
                True,
                "app.mcp_large_data_server loaded successfully"
            )
        except Exception as e:
            self.log_check(
                "MCP Server module imports",
                False,
                f"Import error: {str(e)}"
            )
            all_imported = False
        
        # Test storage import
        try:
            from app.memory.large_data_storage import LargeDataStorage
            self.log_check(
                "LargeDataStorage imports",
                True,
                "app.memory.large_data_storage.LargeDataStorage loaded"
            )
        except Exception as e:
            self.log_check(
                "LargeDataStorage imports",
                False,
                f"Import error: {str(e)}"
            )
            all_imported = False
        
        # Test MCP library
        try:
            import mcp
            self.log_check(
                "MCP library available",
                True,
                f"mcp version: {getattr(mcp, '__version__', 'unknown')}"
            )
        except Exception as e:
            self.log_check(
                "MCP library available",
                False,
                f"Import error: {str(e)}"
            )
            all_imported = False
        
        return all_imported
    
    def verify_mcp_server_components(self) -> bool:
        """Verify MCP server has all required components"""
        print("\n" + "="*80)
        print("MCP SERVER COMPONENTS")
        print("="*80 + "\n")
        
        try:
            from app import mcp_large_data_server
            
            required_components = [
                ("server", "MCP Server instance"),
                ("initialize_storage", "Storage initialization function"),
                ("store_large_dataset", "Store dataset tool"),
                ("retrieve_large_dataset", "Retrieve dataset tool"),
                ("get_dataset_preview", "Preview tool"),
                ("list_stored_datasets", "List tool"),
                ("get_storage_statistics", "Statistics tool"),
                ("cleanup_expired_datasets", "Cleanup tool"),
            ]
            
            all_present = True
            for component, description in required_components:
                has_component = hasattr(mcp_large_data_server, component)
                self.log_check(
                    f"{description}",
                    has_component,
                    f"Component: {component}"
                )
                if not has_component:
                    all_present = False
            
            return all_present
            
        except Exception as e:
            self.log_check(
                "MCP Server components check",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def verify_configuration(self) -> bool:
        """Verify configuration file is valid"""
        print("\n" + "="*80)
        print("CONFIGURATION VERIFICATION")
        print("="*80 + "\n")
        
        try:
            import yaml
            
            config_path = Path("config/large_data_mcp_demo.yaml")
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check required sections
            required_sections = [
                "business_context",
                "models",
                "memory",
                "supervisor",
                "agents"
            ]
            
            all_valid = True
            for section in required_sections:
                has_section = section in config
                self.log_check(
                    f"Config has '{section}' section",
                    has_section,
                    f"Present: {has_section}"
                )
                if not has_section:
                    all_valid = False
            
            # Check agents have MCP servers configured
            if "agents" in config:
                agents_with_mcp = 0
                for agent in config["agents"]:
                    if "mcp_servers" in agent and "large_data_storage" in agent["mcp_servers"]:
                        agents_with_mcp += 1
                
                self.log_check(
                    "Agents configured with Large Data MCP",
                    agents_with_mcp > 0,
                    f"{agents_with_mcp} agents configured"
                )
            
            return all_valid
            
        except Exception as e:
            self.log_check(
                "Configuration validation",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def verify_integration_tests(self) -> bool:
        """Run integration tests"""
        print("\n" + "="*80)
        print("INTEGRATION TESTS")
        print("="*80 + "\n")
        
        try:
            # Import and run tests
            from test_large_data_mcp_integration import LargeDataMCPIntegrationTest
            
            test_suite = LargeDataMCPIntegrationTest()
            success = test_suite.run_all_tests()
            
            # Check results
            passed = sum(1 for r in test_suite.test_results if r["passed"])
            total = len(test_suite.test_results)
            
            self.log_check(
                "Integration tests",
                success,
                f"Passed: {passed}/{total} tests"
            )
            
            return success
            
        except Exception as e:
            self.log_check(
                "Integration tests",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*80)
        print("VERIFICATION REPORT")
        print("="*80 + "\n")
        
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r["passed"])
        failed_checks = total_checks - passed_checks
        
        print(f"Total Checks: {total_checks}")
        print(f"Passed: {passed_checks} ✅")
        print(f"Failed: {failed_checks} ❌")
        print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%\n")
        
        if failed_checks > 0:
            print("Failed Checks:")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()
        
        # Save report
        report = {
            "summary": {
                "total": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "success_rate": (passed_checks/total_checks)*100
            },
            "checks": self.results,
            "errors": self.errors
        }
        
        report_file = "large_data_mcp_verification_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"Detailed report saved to: {report_file}\n")
        
        return failed_checks == 0
    
    def run_verification(self) -> bool:
        """Run all verification checks"""
        print("\n" + "🔍 "*20)
        print("   LARGE DATA MCP SERVER - FINAL VERIFICATION")
        print("🔍 "*20 + "\n")
        
        # Run all checks
        files_ok = self.verify_files_exist()
        imports_ok = self.verify_imports()
        components_ok = self.verify_mcp_server_components()
        config_ok = self.verify_configuration()
        tests_ok = self.verify_integration_tests()
        
        # Generate report
        all_ok = self.generate_report()
        
        if all_ok:
            print("🎉 "*20)
            print("   ALL VERIFICATIONS PASSED!")
            print("   The Large Data MCP Server is ready for production use.")
            print("🎉 "*20 + "\n")
        else:
            print("⚠️  "*20)
            print("   SOME VERIFICATIONS FAILED")
            print("   Please review the errors above and fix them.")
            print("⚠️  "*20 + "\n")
        
        return all_ok


def main():
    """Main verification execution"""
    verifier = LargeDataMCPVerification()
    success = verifier.run_verification()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

