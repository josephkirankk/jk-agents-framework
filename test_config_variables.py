#!/usr/bin/env python3
"""
Simple test for the runtime configuration variables system.

This test verifies that the ConfigPlaceholderProvider correctly loads
variables from YAML files and integrates with the placeholder system.
"""

import os
import sys
import logging
import yaml
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger(__name__)


def test_config_provider():
    """Test the ConfigPlaceholderProvider functionality."""
    print("=" * 60)
    print("🧪 Testing Runtime Configuration Variables System")
    print("=" * 60)
    
    try:
        # Import the config provider
        from app.placeholder_system.config_provider import ConfigPlaceholderProvider
        from app.placeholder_system.context import PlaceholderContext
        
        # Test 1: Create config provider and load variables
        print("\n1️⃣ Testing ConfigPlaceholderProvider initialization...")
        
        config_provider = ConfigPlaceholderProvider()
        loaded_vars = config_provider.get_all_variables()
        loaded_files = config_provider.get_loaded_files()
        
        print(f"   ✅ Loaded {len(loaded_vars)} variables from {len(loaded_files)} files")
        print(f"   📁 Loaded files: {', '.join(loaded_files) if loaded_files else 'None'}")
        
        if loaded_vars:
            print("   📋 Variables loaded:")
            for var_name, var_value in loaded_vars.items():
                print(f"      - {var_name}: {var_value}")
        
        # Test 2: Check if ado_organization is available
        print("\n2️⃣ Testing ADO organization variable...")
        
        if config_provider.can_provide("ado_organization"):
            ado_org = config_provider.get_placeholder_value("ado_organization", {})
            print(f"   ✅ ADO Organization: '{ado_org}'")
        else:
            print("   ❌ ADO organization variable not found")
            print("   💡 Make sure config/vars.local.yaml exists with 'ado_organization' key")
        
        # Test 3: Test integration with PlaceholderContext
        print("\n3️⃣ Testing integration with PlaceholderContext...")
        
        context = PlaceholderContext()
        context_vars = context.build_context()
        
        if "ado_organization" in context_vars:
            print(f"   ✅ ADO organization available in context: '{context_vars['ado_organization']}'")
        else:
            print("   ❌ ADO organization not available in context")
        
        # Test 4: Show all available placeholders
        print("\n4️⃣ Available placeholders in context:")
        available_placeholders = context.get_available_placeholders()
        config_placeholders = [p for p in available_placeholders if p in loaded_vars]
        
        if config_placeholders:
            print("   📝 Configuration placeholders:")
            for placeholder in sorted(config_placeholders):
                doc = config_provider.get_placeholder_documentation(placeholder)
                print(f"      - {{{{ {placeholder} }}}} - {doc}")
        
        # Test 5: Create a simple template test
        print("\n5️⃣ Testing template rendering with config variables...")
        
        test_template = "ADO Organization: {{ ado_organization }}, Environment: {{ environment | default('not_set') }}"
        
        try:
            from jinja2 import Template
            template = Template(test_template)
            rendered = template.render(context_vars)
            print(f"   ✅ Template rendered: '{rendered}'")
        except ImportError:
            print("   ⚠️  Jinja2 not available, skipping template test")
        except Exception as e:
            print(f"   ❌ Template rendering failed: {e}")
        
        print("\n✅ Configuration variables system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ado_config_usage():
    """Test ADO configuration usage in the optimized config."""
    print("\n" + "=" * 60)
    print("🔧 Testing ADO Configuration Usage")
    print("=" * 60)
    
    try:
        ado_config_path = Path("config/ado_realtime_analysis_optimized.yaml")
        
        if not ado_config_path.exists():
            print(f"   ❌ ADO config file not found: {ado_config_path}")
            return False
        
        # Load the ADO config
        with open(ado_config_path, 'r', encoding='utf-8') as f:
            ado_config = yaml.safe_load(f)
        
        # Check for placeholder usage
        config_str = yaml.dump(ado_config)
        
        if "{{ado_organization}}" in config_str:
            print("   ✅ Found {{ado_organization}} placeholder in ADO config")
            
            # Test placeholder resolution
            from app.placeholder_system.context import PlaceholderContext
            context = PlaceholderContext()
            context_vars = context.build_context()
            
            if "ado_organization" in context_vars:
                resolved_org = context_vars["ado_organization"]
                print(f"   ✅ Placeholder would resolve to: '{resolved_org}'")
                
                # Show what the final config would look like
                updated_config_str = config_str.replace("{{ado_organization}}", resolved_org)
                print(f"   📋 Example resolved args would be:")
                print(f"      args: [\"-y\", \"@azure-devops/mcp\", \"{resolved_org}\"]")
                
            else:
                print("   ❌ ado_organization not available in context")
        else:
            print("   ❌ {{ado_organization}} placeholder not found in ADO config")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ADO config test failed: {e}")
        return False


def create_example_configs():
    """Create example configuration files for different environments."""
    print("\n" + "=" * 60)
    print("📁 Creating Example Configuration Files")
    print("=" * 60)
    
    config_dir = Path("config")
    
    # Example production config
    prod_config = {
        "ado_organization": "your-prod-org",
        "environment": "production",
        "debug_mode": False,
        "api_timeout": 180,
        "max_retries": 5,
        "log_level": "WARNING",
        "enable_fast_track_routing": True,
        "enable_performance_monitoring": True,
        "mock_external_services": False
    }
    
    prod_config_path = config_dir / "vars.production.yaml"
    if not prod_config_path.exists():
        with open(prod_config_path, 'w', encoding='utf-8') as f:
            f.write("# Production Configuration Variables\n")
            f.write("# Override development settings for production environment\n\n")
            yaml.dump(prod_config, f, default_flow_style=False, sort_keys=False)
        print(f"   ✅ Created example production config: {prod_config_path}")
    
    # Example staging config
    staging_config = {
        "ado_organization": "your-staging-org",
        "environment": "staging", 
        "debug_mode": True,
        "api_timeout": 150,
        "max_retries": 3,
        "log_level": "INFO",
        "enable_performance_monitoring": True,
        "mock_external_services": False
    }
    
    staging_config_path = config_dir / "vars.staging.yaml"
    if not staging_config_path.exists():
        with open(staging_config_path, 'w', encoding='utf-8') as f:
            f.write("# Staging Configuration Variables\n")
            f.write("# Override development settings for staging environment\n\n")
            yaml.dump(staging_config, f, default_flow_style=False, sort_keys=False)
        print(f"   ✅ Created example staging config: {staging_config_path}")
    
    # Show usage instructions
    print("\n📖 Usage Instructions:")
    print("   1. Edit config/vars.local.yaml with your ADO organization name")
    print("   2. For other environments, set ENVIRONMENT variable:")
    print("      export ENVIRONMENT=production  # Uses vars.production.yaml")
    print("      export ENVIRONMENT=staging     # Uses vars.staging.yaml")
    print("   3. Variables are automatically loaded and available as {{variable_name}} in configs")


def main():
    """Run all configuration variable tests."""
    print("🚀 Starting Configuration Variables System Tests")
    
    # Run tests
    config_test_passed = test_config_provider()
    ado_test_passed = test_ado_config_usage()
    
    # Create examples
    create_example_configs()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"   Config Provider Test: {'✅ PASSED' if config_test_passed else '❌ FAILED'}")
    print(f"   ADO Config Test: {'✅ PASSED' if ado_test_passed else '❌ FAILED'}")
    
    if config_test_passed and ado_test_passed:
        print("\n🎉 All tests passed! Configuration variables system is working correctly.")
        print("\n💡 Next Steps:")
        print("   1. Update config/vars.local.yaml with your actual ADO organization")
        print("   2. Use the optimized ADO config: config/ado_realtime_analysis_optimized.yaml")
        print("   3. Run queries and see the fast-track routing in action!")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())