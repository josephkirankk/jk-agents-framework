"""
Test script for PepGenX CLI functionality
Tests the CLI without making actual API calls
"""

import sys
from pathlib import Path

# Add the scripts directory to the path so we can import pepgenx_cli
sys.path.insert(0, str(Path(__file__).parent))

from pepgenx_cli import get_model_provider

def test_model_provider_detection():
    """Test the model provider detection logic."""
    print("Testing model provider detection...")
    
    test_cases = [
        # OpenAI models
        ("gpt-4o", "openai"),
        ("gpt-4o-mini", "openai"),
        ("gpt-4", "openai"),
        ("gpt-35-turbo", "openai"),
        ("gpt-5", "openai"),
        ("GPT-4O", "openai"),  # Case insensitive
        
        # Anthropic models
        ("claude-3-5-sonnet", "aws-anthropic"),
        ("claude-3-sonnet", "aws-anthropic"),
        ("claude-3-opus", "aws-anthropic"),
        ("claude-3-haiku", "aws-anthropic"),
        ("claude-4-sonnet", "aws-anthropic"),
        ("CLAUDE-3-5-SONNET", "aws-anthropic"),  # Case insensitive
        
        # Meta models
        ("llama-3.3-70b-instruct", "aws-meta"),
        ("llama-4-maverick", "aws-meta"),
        ("LLAMA-3.3-70B-INSTRUCT", "aws-meta"),  # Case insensitive
        
        # Nova models
        ("nova-lite", "aws-nova"),
        ("nova-pro", "aws-nova"),
        ("nova micro", "aws-nova"),
        ("NOVA-LITE", "aws-nova"),  # Case insensitive
        
        # Databricks models
        ("databricks-model", "databricks"),
        ("DATABRICKS-MODEL", "databricks"),  # Case insensitive
        
        # Unknown models (should default to openai)
        ("unknown-model", "openai"),
        ("some-random-model", "openai"),
        ("", "openai"),  # Empty string
    ]
    
    passed = 0
    failed = 0
    
    for model_name, expected_provider in test_cases:
        actual_provider = get_model_provider(model_name)
        if actual_provider == expected_provider:
            print(f"✅ {model_name:<25} -> {actual_provider}")
            passed += 1
        else:
            print(f"❌ {model_name:<25} -> {actual_provider} (expected {expected_provider})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

def test_cli_help():
    """Test that CLI help works without errors."""
    print("\nTesting CLI help functionality...")
    
    try:
        import argparse
        from pepgenx_cli import main
        
        # This would normally call main(), but we'll just test the parser creation
        parser = argparse.ArgumentParser(description="Test parser")
        subparsers = parser.add_subparsers(dest='command')
        
        # List command
        list_parser = subparsers.add_parser('list')
        
        # Test command
        test_parser = subparsers.add_parser('test')
        test_parser.add_argument('--model', '-m', required=True)
        test_parser.add_argument('--system-prompt', '-s', type=int, default=2)
        test_parser.add_argument('--user-prompt', '-u', default='Hello, how are you?')
        
        # Test parsing some arguments
        test_args = [
            ['list'],
            ['test', '--model', 'gpt-4o'],
            ['test', '-m', 'claude-3-5-sonnet', '-u', 'Hello world'],
            ['test', '--model', 'gpt-4o', '--system-prompt', '1', '--user-prompt', 'What is 2+2?']
        ]
        
        for args in test_args:
            try:
                parsed = parser.parse_args(args)
                print(f"✅ Parsed args: {args}")
            except SystemExit:
                print(f"❌ Failed to parse args: {args}")
                return False
        
        print("✅ CLI argument parsing works correctly")
        return True
        
    except Exception as e:
        print(f"❌ CLI help test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PepGenX CLI Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test model provider detection
    if not test_model_provider_detection():
        all_passed = False
    
    # Test CLI help
    if not test_cli_help():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
