#!/usr/bin/env python3
"""
Test Data Parser Enterprise - Large Data MCP Server Integration Verification

This script verifies that the test_data_parser_enterprise.yaml configuration
has been correctly integrated with the Large Data MCP Server.
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any

class TestDataParserIntegrationVerifier:
    """Verify Large Data MCP Server integration in test_data_parser_enterprise.yaml"""
    
    def __init__(self):
        self.config_path = Path("config/test_data_parser_enterprise.yaml")
        self.config = None
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
    
    def load_config(self) -> bool:
        """Load and parse the YAML configuration"""
        print("\n" + "="*80)
        print("CONFIGURATION LOADING")
        print("="*80 + "\n")
        
        try:
            if not self.config_path.exists():
                self.log_check(
                    "Configuration file exists",
                    False,
                    f"File not found: {self.config_path}"
                )
                return False
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            self.log_check(
                "Configuration file loaded",
                True,
                f"Loaded from: {self.config_path}"
            )
            return True
            
        except yaml.YAMLError as e:
            self.log_check(
                "YAML syntax validation",
                False,
                f"YAML error: {str(e)}"
            )
            return False
        except Exception as e:
            self.log_check(
                "Configuration loading",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def verify_large_data_handling_config(self) -> bool:
        """Verify large_data_handling configuration exists"""
        print("\n" + "="*80)
        print("LARGE DATA HANDLING CONFIGURATION")
        print("="*80 + "\n")
        
        if "large_data_handling" not in self.config:
            self.log_check(
                "large_data_handling section exists",
                False,
                "Missing large_data_handling configuration"
            )
            return False
        
        ldh = self.config["large_data_handling"]
        
        # Check enabled
        enabled = ldh.get("enabled", False)
        self.log_check(
            "large_data_handling enabled",
            enabled,
            f"enabled: {enabled}"
        )
        
        # Check large_data section
        has_large_data = "large_data" in ldh
        self.log_check(
            "large_data section exists",
            has_large_data,
            f"sqlite_path: {ldh.get('large_data', {}).get('sqlite_path', 'N/A')}"
        )
        
        # Check compression
        compression = ldh.get("large_data", {}).get("compression", False)
        self.log_check(
            "Compression enabled",
            compression,
            f"compression: {compression}"
        )
        
        return enabled and has_large_data
    
    def verify_data_generator_agent(self) -> bool:
        """Verify data_generator agent has Large Data MCP Server"""
        print("\n" + "="*80)
        print("DATA GENERATOR AGENT VERIFICATION")
        print("="*80 + "\n")
        
        if "agents" not in self.config:
            self.log_check(
                "Agents section exists",
                False,
                "Missing agents configuration"
            )
            return False
        
        # Find data_generator agent
        data_generator = None
        for agent in self.config["agents"]:
            if agent.get("name") == "data_generator":
                data_generator = agent
                break
        
        if not data_generator:
            self.log_check(
                "data_generator agent exists",
                False,
                "data_generator agent not found"
            )
            return False
        
        self.log_check(
            "data_generator agent exists",
            True,
            f"Description: {data_generator.get('description', 'N/A')}"
        )
        
        # Check MCP servers
        mcp_servers = data_generator.get("mcp_servers", {})
        
        # Check python_runner
        has_python = "python_runner" in mcp_servers
        self.log_check(
            "python_runner MCP server configured",
            has_python,
            "For data generation"
        )
        
        # Check large_data_storage
        has_large_data = "large_data_storage" in mcp_servers
        self.log_check(
            "large_data_storage MCP server configured",
            has_large_data,
            "For efficient storage"
        )
        
        if has_large_data:
            lds = mcp_servers["large_data_storage"]
            
            # Verify transport
            transport = lds.get("transport")
            self.log_check(
                "large_data_storage uses stdio transport",
                transport == "stdio",
                f"transport: {transport}"
            )
            
            # Verify command
            command = lds.get("command")
            self.log_check(
                "large_data_storage uses python command",
                command == "python",
                f"command: {command}"
            )
            
            # Verify args
            args = lds.get("args", [])
            expected_args = ["-m", "app.mcp_large_data_server"]
            args_correct = args == expected_args
            self.log_check(
                "large_data_storage args correct",
                args_correct,
                f"args: {args}"
            )
        
        return has_python and has_large_data
    
    def verify_agent_prompt(self) -> bool:
        """Verify data_generator agent prompt includes Large Data instructions"""
        print("\n" + "="*80)
        print("AGENT PROMPT VERIFICATION")
        print("="*80 + "\n")
        
        # Find data_generator agent
        data_generator = None
        for agent in self.config["agents"]:
            if agent.get("name") == "data_generator":
                data_generator = agent
                break
        
        if not data_generator:
            return False
        
        prompt = data_generator.get("prompt", "")
        
        # Check for key sections
        checks = [
            ("LARGE DATA OPTIMIZATION", "LARGE DATA OPTIMIZATION section"),
            ("WORKFLOW", "WORKFLOW section"),
            ("store_large_dataset", "store_large_dataset tool mentioned"),
            ("reference_id", "reference_id mentioned"),
            ("preview", "preview mentioned"),
            ("> 100", "threshold (> 100 records) mentioned"),
        ]
        
        for keyword, description in checks:
            has_keyword = keyword in prompt
            self.log_check(
                f"Prompt includes {description}",
                has_keyword,
                f"Keyword: '{keyword}'"
            )
        
        return all(keyword in prompt for keyword, _ in checks)
    
    def verify_parser_agent_unchanged(self) -> bool:
        """Verify requirement_parser agent was not modified"""
        print("\n" + "="*80)
        print("REQUIREMENT PARSER AGENT VERIFICATION")
        print("="*80 + "\n")
        
        # Find requirement_parser agent
        parser = None
        for agent in self.config["agents"]:
            if agent.get("name") == "requirement_parser":
                parser = agent
                break
        
        if not parser:
            self.log_check(
                "requirement_parser agent exists",
                False,
                "requirement_parser agent not found"
            )
            return False
        
        self.log_check(
            "requirement_parser agent exists",
            True,
            "Agent preserved"
        )
        
        # Check it only has python_runner (not large_data_storage)
        mcp_servers = parser.get("mcp_servers", {})
        has_python = "python_runner" in mcp_servers
        has_large_data = "large_data_storage" in mcp_servers
        
        self.log_check(
            "requirement_parser has python_runner",
            has_python,
            "For parsing logic"
        )
        
        self.log_check(
            "requirement_parser does NOT have large_data_storage",
            not has_large_data,
            "Parser doesn't need large data storage"
        )
        
        return has_python and not has_large_data
    
    def verify_supervisor_unchanged(self) -> bool:
        """Verify supervisor configuration was not modified"""
        print("\n" + "="*80)
        print("SUPERVISOR VERIFICATION")
        print("="*80 + "\n")
        
        if "supervisor" not in self.config:
            self.log_check(
                "Supervisor section exists",
                False,
                "Missing supervisor configuration"
            )
            return False
        
        supervisor = self.config["supervisor"]
        
        # Check name
        name = supervisor.get("name")
        self.log_check(
            "Supervisor name preserved",
            name == "supervisor",
            f"name: {name}"
        )
        
        # Check prompt includes 2-step plan
        prompt = supervisor.get("prompt", "")
        has_2step = "s1=parse params, s2=generate data" in prompt
        self.log_check(
            "Supervisor 2-step plan preserved",
            has_2step,
            "s1=parse, s2=generate"
        )
        
        return name == "supervisor" and has_2step
    
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
        
        return failed_checks == 0
    
    def run_verification(self) -> bool:
        """Run all verification checks"""
        print("\n" + "🔍 "*20)
        print("   TEST DATA PARSER ENTERPRISE - INTEGRATION VERIFICATION")
        print("🔍 "*20 + "\n")
        
        # Load config
        if not self.load_config():
            return False
        
        # Run all checks
        self.verify_large_data_handling_config()
        self.verify_data_generator_agent()
        self.verify_agent_prompt()
        self.verify_parser_agent_unchanged()
        self.verify_supervisor_unchanged()
        
        # Generate report
        all_ok = self.generate_report()
        
        if all_ok:
            print("🎉 "*20)
            print("   ALL VERIFICATIONS PASSED!")
            print("   The Test Data Parser Enterprise configuration is correctly")
            print("   integrated with the Large Data MCP Server.")
            print("🎉 "*20 + "\n")
        else:
            print("⚠️  "*20)
            print("   SOME VERIFICATIONS FAILED")
            print("   Please review the errors above and fix them.")
            print("⚠️  "*20 + "\n")
        
        return all_ok


def main():
    """Main verification execution"""
    verifier = TestDataParserIntegrationVerifier()
    success = verifier.run_verification()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

