#!/usr/bin/env python3
"""
Test script to verify large_data_handling is properly configured
"""

import sys
from pathlib import Path
import yaml

def check_config():
    """Check if configuration is correct"""
    config_path = Path("./config/test_data_parser_enterprise.yaml")
    
    if not config_path.exists():
        print("❌ Config file not found")
        return False
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Check large_data_handling section
    if "large_data_handling" not in config:
        print("❌ large_data_handling section missing")
        return False
    
    ldh = config["large_data_handling"]
    
    # Check enabled
    if not ldh.get("enabled"):
        print("❌ large_data_handling.enabled is False or missing")
        return False
    
    print(f"✅ large_data_handling.enabled = {ldh.get('enabled')}")
    
    # Check token_threshold
    threshold = ldh.get("token_threshold", "NOT SET")
    print(f"✅ large_data_handling.token_threshold = {threshold}")
    
    # Check large_data section
    if "large_data" not in ldh:
        print("⚠️  large_data subsection missing (will use defaults)")
    else:
        print(f"✅ large_data.sqlite_path = {ldh['large_data'].get('sqlite_path', 'default')}")
        print(f"✅ large_data.compression = {ldh['large_data'].get('compression', True)}")
    
    # Check summarization
    if "summarization" in ldh:
        print(f"✅ summarization.max_summary_tokens = {ldh['summarization'].get('max_summary_tokens', 150)}")
    
    return True

def check_enhanced_tool_node():
    """Check if EnhancedToolNode can be imported"""
    try:
        from app.memory.enhanced_tool_node import EnhancedToolNode
        print("✅ EnhancedToolNode can be imported")
        return True
    except ImportError as e:
        print(f"❌ Cannot import EnhancedToolNode: {e}")
        return False

def check_smart_tool_wrapper():
    """Check if SmartToolWrapper can be imported"""
    try:
        from app.memory.smart_tool_wrapper import SmartToolWrapper
        print("✅ SmartToolWrapper can be imported")
        return True
    except ImportError as e:
        print(f"❌ Cannot import SmartToolWrapper: {e}")
        return False

def check_large_data_storage():
    """Check if LargeDataStorage can be imported"""
    try:
        from app.memory.large_data_storage import LargeDataStorage
        print("✅ LargeDataStorage can be imported")
        return True
    except ImportError as e:
        print(f"❌ Cannot import LargeDataStorage: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("  LARGE DATA HANDLING FIX VERIFICATION")
    print("="*80 + "\n")
    
    print("1. Checking configuration...")
    config_ok = check_config()
    print()
    
    print("2. Checking module imports...")
    enhanced_ok = check_enhanced_tool_node()
    wrapper_ok = check_smart_tool_wrapper()
    storage_ok = check_large_data_storage()
    print()
    
    print("="*80)
    if config_ok and enhanced_ok and wrapper_ok and storage_ok:
        print("✅ ALL CHECKS PASSED")
        print("\nLarge data handling should now work correctly.")
        print("\nTo test:")
        print("  1. Start server: uvicorn api:app --reload")
        print("  2. Run test: ./test_system.sh")
        print("  3. Check logs for: 'Enhanced tool node initialized with large data handling'")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above.")
        print("="*80 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
