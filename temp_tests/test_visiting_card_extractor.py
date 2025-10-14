"""
Test Suite for Visiting Card Extractor Configuration
====================================================

Validates the visiting card extraction system configuration and tools.
Run this before production deployment to ensure everything works correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import Mock, patch
import json


class TestVisitingCardTools(unittest.TestCase):
    """Test the visiting card helper tools."""
    
    def setUp(self):
        """Import tools dynamically."""
        from tools.visiting_card_tools import (
            normalize_phone,
            validate_email,
            parse_url,
            normalize_company_name,
            extract_contact_fields
        )
        self.normalize_phone = normalize_phone
        self.validate_email = validate_email
        self.parse_url = parse_url
        self.normalize_company_name = normalize_company_name
        self.extract_contact_fields = extract_contact_fields
    
    def test_phone_normalization_basic(self):
        """Test basic phone number normalization."""
        # Test with formatted US number
        result = self.normalize_phone.invoke("(555) 123-4567", country_hint="US")
        
        self.assertIsInstance(result, dict)
        self.assertIn("original", result)
        self.assertIn("valid", result)
        self.assertEqual(result["original"], "(555) 123-4567")
        
        # Should work even without phonenumbers library
        if result["e164"]:
            self.assertTrue(result["e164"].startswith("+"))
    
    def test_phone_normalization_international(self):
        """Test international phone number formats."""
        test_cases = [
            ("+1-555-123-4567", "US"),
            ("+91 98765 43210", "IN"),
            ("+44 20 7123 4567", "GB"),
        ]
        
        for phone, country in test_cases:
            result = self.normalize_phone.invoke(phone, country_hint=country)
            self.assertIsInstance(result, dict)
            self.assertIn("original", result)
    
    def test_email_validation_valid(self):
        """Test valid email addresses."""
        test_emails = [
            "john.smith@techcorp.com",
            "alice+test@example.co.uk",
            "contact@sub.domain.org",
        ]
        
        for email in test_emails:
            result = self.validate_email.invoke(email, check_mx=False)
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result["format_valid"], f"Email {email} should be valid")
            self.assertIn("domain", result)
            self.assertTrue(result["verified"])
    
    def test_email_validation_invalid(self):
        """Test invalid email addresses."""
        test_emails = [
            "not-an-email",
            "@no-local-part.com",
            "missing-domain@",
            "no-tld@domain",
        ]
        
        for email in test_emails:
            result = self.validate_email.invoke(email, check_mx=False)
            
            self.assertIsInstance(result, dict)
            self.assertFalse(result["format_valid"], f"Email {email} should be invalid")
    
    def test_url_parsing_valid(self):
        """Test URL parsing and normalization."""
        test_cases = [
            ("www.techcorp.com", "https://www.techcorp.com", "www.techcorp.com"),
            ("https://example.org", "https://example.org", "example.org"),
            ("techcorp.io", "https://techcorp.io", "techcorp.io"),
        ]
        
        for url, expected_normalized, expected_domain in test_cases:
            result = self.parse_url.invoke(url)
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result["valid"], f"URL {url} should be valid")
            self.assertEqual(result["normalized"], expected_normalized)
            self.assertEqual(result["domain"], expected_domain)
    
    def test_company_name_normalization(self):
        """Test company name normalization and legal suffix removal."""
        test_cases = [
            ("TechCorp Solutions, Inc.", "TechCorp Solutions", ["Inc."]),
            ("ABC Company LLC", "ABC", ["LLC", "Company"]),  # Company is also a legal suffix
            ("XYZ Ltd.", "XYZ", ["Ltd."]),
            ("Acme Corporation", "Acme", ["Corporation"]),
        ]
        
        for company, expected_normalized, expected_suffixes in test_cases:
            result = self.normalize_company_name.invoke(company)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["normalized"], expected_normalized)
            self.assertIsInstance(result["search_variants"], list)
            self.assertGreater(len(result["search_variants"]), 0)
    
    def test_contact_field_extraction(self):
        """Test extracting contact fields from OCR text."""
        sample_ocr = """
        John Smith
        Senior Software Engineer
        TechCorp Solutions, Inc.
        
        Phone: (555) 123-4567
        Email: john.smith@techcorp.com
        Web: www.techcorp.com
        
        123 Tech Street
        Silicon Valley, CA 94025
        """
        
        result = self.extract_contact_fields.invoke(sample_ocr)
        
        self.assertIsInstance(result, dict)
        self.assertIn("phones", result)
        self.assertIn("emails", result)
        self.assertIn("urls", result)
        
        # Should detect at least one of each
        self.assertGreater(len(result["emails"]), 0, "Should detect email")
        self.assertIn("john.smith@techcorp.com", result["emails"])


class TestConfigurationValidity(unittest.TestCase):
    """Test the YAML configuration file validity."""
    
    def setUp(self):
        """Load configuration file."""
        config_path = project_root / "config" / "visiting_card_extractor.yaml"
        
        if not config_path.exists():
            self.skipTest(f"Config file not found: {config_path}")
        
        import yaml
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def test_config_structure(self):
        """Test basic configuration structure."""
        required_keys = ["version", "name", "models", "supervisor", "agents", "timeouts"]
        
        for key in required_keys:
            self.assertIn(key, self.config, f"Config missing required key: {key}")
    
    def test_models_configuration(self):
        """Test models configuration."""
        models = self.config["models"]
        
        self.assertIn("default", models)
        self.assertIn("multimodal", models)
        self.assertIn("supervisor", models)
        
        # Check model format validity
        self.assertTrue(models["multimodal"].startswith("google:"), 
                       "Multimodal model should use Google Gemini")
    
    def test_agents_configuration(self):
        """Test agents are properly configured."""
        agents = self.config["agents"]
        
        self.assertIsInstance(agents, list)
        self.assertGreaterEqual(len(agents), 4, "Should have at least 4 agents")
        
        # Check required agents exist
        agent_names = [agent["name"] for agent in agents]
        required_agents = [
            "multimodal_ocr_agent",
            "contact_parser_agent",
            "company_research_agent",
            "aggregator_agent"
        ]
        
        for required in required_agents:
            self.assertIn(required, agent_names, f"Missing required agent: {required}")
    
    def test_agent_types_valid(self):
        """Test agent types are valid."""
        agents = self.config["agents"]
        valid_types = ["react", "normal"]
        
        for agent in agents:
            agent_type = agent.get("agent_type")
            self.assertIn(agent_type, valid_types, 
                         f"Invalid agent_type '{agent_type}' for {agent['name']}")
    
    def test_ocr_agent_configuration(self):
        """Test OCR agent uses multimodal model."""
        agents = self.config["agents"]
        ocr_agent = next((a for a in agents if a["name"] == "multimodal_ocr_agent"), None)
        
        self.assertIsNotNone(ocr_agent, "OCR agent not found")
        self.assertTrue(ocr_agent["model"].startswith("google:"),
                       "OCR agent should use Google Gemini for vision")
        self.assertEqual(ocr_agent["agent_type"], "react")
    
    def test_contact_parser_tools(self):
        """Test contact parser has python_tools configured."""
        agents = self.config["agents"]
        parser_agent = next((a for a in agents if a["name"] == "contact_parser_agent"), None)
        
        self.assertIsNotNone(parser_agent, "Parser agent not found")
        self.assertIn("python_tools", parser_agent, "Parser should have python_tools")
        
        # Check tool configuration
        python_tools = parser_agent["python_tools"]
        self.assertIsInstance(python_tools, dict)
        
        # Should have contact_normalization tools
        if "contact_normalization" in python_tools:
            tools_config = python_tools["contact_normalization"]
            self.assertEqual(tools_config["module_path"], "tools.visiting_card_tools")
            self.assertIn("normalize_phone", tools_config["tool_names"])
            self.assertIn("validate_email", tools_config["tool_names"])
    
    def test_research_agent_mcp_servers(self):
        """Test research agent has Brave Search MCP configured."""
        agents = self.config["agents"]
        research_agent = next((a for a in agents if a["name"] == "company_research_agent"), None)
        
        self.assertIsNotNone(research_agent, "Research agent not found")
        self.assertIn("mcp_servers", research_agent, "Research agent should have mcp_servers")
        
        # Check Brave Search configuration
        mcp_servers = research_agent["mcp_servers"]
        self.assertIn("brave_search", mcp_servers, "Should have brave_search MCP server")
        
        brave_config = mcp_servers["brave_search"]
        self.assertEqual(brave_config["transport"], "streamable_http")
        self.assertEqual(brave_config["url"], "http://localhost:8080/mcp")
    
    def test_timeouts_configured(self):
        """Test timeout values are reasonable."""
        timeouts = self.config["timeouts"]
        
        required_timeouts = ["ocr_processing", "data_normalization", 
                            "company_research", "data_aggregation"]
        
        for timeout_key in required_timeouts:
            self.assertIn(timeout_key, timeouts, f"Missing timeout: {timeout_key}")
            self.assertIsInstance(timeouts[timeout_key], int)
            self.assertGreater(timeouts[timeout_key], 0)
    
    def test_supervisor_prompt_completeness(self):
        """Test supervisor has comprehensive prompt."""
        supervisor = self.config["supervisor"]
        
        self.assertIn("prompt", supervisor)
        prompt = supervisor["prompt"]
        
        # Check for key prompt sections
        required_sections = [
            "{{business_context}}",
            "{{agents}}",
            "{{original_user_question}}",
            "SIMPLE EXTRACTION",
            "COMPREHENSIVE EXTRACTION",
        ]
        
        for section in required_sections:
            self.assertIn(section, prompt, f"Supervisor prompt missing: {section}")


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment configuration and prerequisites."""
    
    def test_env_variables_documented(self):
        """Test that required environment variables are documented in config."""
        config_path = project_root / "config" / "visiting_card_extractor.yaml"
        
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for environment variable documentation
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "BRAVE_API_KEY",
        ]
        
        for var in required_vars:
            self.assertIn(var, content, 
                         f"Config should document env var: {var}")
    
    def test_tools_module_importable(self):
        """Test that tools module can be imported."""
        try:
            from tools import visiting_card_tools
            self.assertTrue(hasattr(visiting_card_tools, 'normalize_phone'))
            self.assertTrue(hasattr(visiting_card_tools, 'validate_email'))
        except ImportError as e:
            self.fail(f"Failed to import visiting_card_tools: {e}")
    
    def test_optional_dependencies_info(self):
        """Test that optional dependencies are handled gracefully."""
        from tools import visiting_card_tools
        
        # Should have flags for optional dependencies
        self.assertTrue(hasattr(visiting_card_tools, 'HAS_PHONENUMBERS'))
        self.assertTrue(hasattr(visiting_card_tools, 'HAS_DNS'))
        
        # Tools should work even without optional deps
        result = visiting_card_tools.normalize_phone.invoke("+15551234567")
        self.assertIsInstance(result, dict)


class TestIntegrationReadiness(unittest.TestCase):
    """Test that the system is ready for integration."""
    
    def test_config_file_exists(self):
        """Test that configuration file exists."""
        config_path = project_root / "config" / "visiting_card_extractor.yaml"
        self.assertTrue(config_path.exists(), "Config file should exist")
    
    def test_tools_file_exists(self):
        """Test that tools file exists."""
        tools_path = project_root / "tools" / "visiting_card_tools.py"
        self.assertTrue(tools_path.exists(), "Tools file should exist")
    
    def test_documentation_exists(self):
        """Test that documentation exists."""
        docs_path = project_root / "docs" / "VISITING_CARD_EXTRACTOR_GUIDE.md"
        self.assertTrue(docs_path.exists(), "Documentation should exist")
    
    def test_brave_research_config_matches_working_example(self):
        """Test that Brave MCP config matches the working brave-research.yaml."""
        import yaml
        
        # Load working config
        working_config_path = project_root / "config" / "brave-research.yaml"
        if not working_config_path.exists():
            self.skipTest("brave-research.yaml not found for comparison")
        
        with open(working_config_path, 'r') as f:
            working_config = yaml.safe_load(f)
        
        # Load our config
        our_config_path = project_root / "config" / "visiting_card_extractor.yaml"
        with open(our_config_path, 'r') as f:
            our_config = yaml.safe_load(f)
        
        # Find research agents in both configs
        working_agents = working_config.get("agents", [])
        our_agents = our_config.get("agents", [])
        
        working_research = next((a for a in working_agents if "brave_search" in a.get("mcp_servers", {})), None)
        our_research = next((a for a in our_agents if a["name"] == "company_research_agent"), None)
        
        if working_research and our_research:
            # Compare Brave MCP configuration structure
            working_brave = working_research["mcp_servers"]["brave_search"]
            our_brave = our_research["mcp_servers"]["brave_search"]
            
            self.assertEqual(our_brave["transport"], working_brave["transport"],
                           "Brave MCP transport should match working config")
            self.assertEqual(our_brave["url"], working_brave["url"],
                           "Brave MCP URL should match working config")


def run_tests():
    """Run all tests and print results."""
    print("=" * 70)
    print("VISITING CARD EXTRACTOR - TEST SUITE")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVisitingCardTools))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationValidity))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentSetup))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationReadiness))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Configuration is ready for production!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review errors above and fix issues")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
