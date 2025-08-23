#!/usr/bin/env python3
"""
Internal Logging System Demo

This script demonstrates the internal LLM logging system capabilities,
including configuration, HTTP interception, and log analysis.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.internal_logger import (
    InternalLogger,
    InternalLogConfig,
    LogLevel,
    LLMProvider,
    get_internal_logger
)
from app.internal_logging_config import (
    get_config_manager,
    get_internal_logging_config,
    update_internal_logging_config
)
from app.internal_logging_integration import (
    initialize_internal_logging,
    get_logging_stats,
    agent_logging_context
)


def demo_basic_logging():
    """Demonstrate basic logging functionality."""
    print("=== Basic Logging Demo ===")
    
    # Configure logging for demo
    config = InternalLogConfig(
        enabled=True,
        log_level=LogLevel.DEBUG,
        log_directory="demo_logs",
        max_file_size_mb=1,  # Small size for demo
        max_files=3
    )
    
    logger = InternalLogger(config)
    
    # Simulate an LLM interaction
    with logger.log_llm_interaction(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        agent_name="demo_agent",
        user_input="What is the capital of France?"
    ) as ctx:
        # Log a request
        ctx.log_request(
            endpoint="https://api.openai.com/v1/chat/completions",
            method="POST",
            headers={
                "Authorization": "Bearer sk-demo-key",
                "Content-Type": "application/json"
            },
            payload={
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "What is the capital of France?"}
                ],
                "temperature": 0.7
            }
        )
        
        # Simulate some processing time
        import time
        time.sleep(0.1)
        
        # Log a response
        ctx.log_response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            payload={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "The capital of France is Paris."
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 8,
                    "total_tokens": 23
                }
            },
            token_usage={
                "prompt_tokens": 15,
                "completion_tokens": 8,
                "total_tokens": 23
            }
        )
    
    print(f"✓ Logged interaction to: {logger.get_current_log_file()}")
    
    # Show log stats
    stats = logger.get_log_stats()
    print(f"✓ Log files: {stats['total_log_files']}")
    print(f"✓ Total size: {stats['total_size_mb']} MB")
    
    return logger


def demo_configuration():
    """Demonstrate configuration management."""
    print("\n=== Configuration Demo ===")
    
    # Get configuration manager
    config_manager = get_config_manager()
    
    # Show current configuration
    config_info = config_manager.get_config_info()
    print("Current configuration:")
    for key, info in config_info.items():
        print(f"  {key}: {info['value']} (from {info['source']})")
    
    # Update configuration at runtime
    print("\nUpdating configuration...")
    config_manager.set_config_value("log_level", LogLevel.ERROR)
    config_manager.set_config_value("max_file_size_mb", 50)
    
    # Show updated configuration
    updated_config = config_manager.get_config()
    print(f"✓ Log level updated to: {updated_config.log_level.value}")
    print(f"✓ Max file size updated to: {updated_config.max_file_size_mb} MB")


def demo_sensitive_data_masking():
    """Demonstrate sensitive data masking."""
    print("\n=== Sensitive Data Masking Demo ===")
    
    config = InternalLogConfig(
        enabled=True,
        log_level=LogLevel.DEBUG,
        log_directory="demo_logs",
        mask_sensitive_data=True
    )
    
    logger = InternalLogger(config)
    
    # Test data with sensitive information
    test_data = {
        "api-key": "sk-very-secret-key-12345",
        "authorization": "Bearer secret-token",
        "user_data": "public information",
        "nested": {
            "password": "super-secret-password",
            "username": "john_doe"
        }
    }
    
    masked_data = logger._mask_sensitive_data(test_data)
    
    print("Original data:")
    print(json.dumps(test_data, indent=2))
    
    print("\nMasked data:")
    print(json.dumps(masked_data, indent=2))
    
    print("✓ Sensitive fields are masked while preserving structure")


def demo_agent_context():
    """Demonstrate agent context management."""
    print("\n=== Agent Context Demo ===")
    
    # Initialize the internal logging system
    initialize_internal_logging()
    
    # Use agent context
    with agent_logging_context("demo_agent", "Analyze this data"):
        print("✓ Agent context set for 'demo_agent'")
        
        # In a real scenario, LLM calls would be made here
        # and they would automatically be logged with the agent context
        print("✓ Any LLM calls within this context would be logged")
        print("  with agent_name='demo_agent' and user_input='Analyze this data'")
    
    print("✓ Agent context cleared")


def demo_log_analysis():
    """Demonstrate log file analysis."""
    print("\n=== Log Analysis Demo ===")
    
    # Find log files
    log_dir = Path("demo_logs")
    if not log_dir.exists():
        print("No demo logs found. Run other demos first.")
        return
    
    log_files = list(log_dir.glob("internal_logs_*.log"))
    if not log_files:
        print("No internal log files found.")
        return
    
    print(f"Found {len(log_files)} log files:")
    
    total_requests = 0
    total_tokens = 0
    providers = set()
    models = set()
    
    for log_file in log_files:
        print(f"  {log_file.name}")
        
        # Analyze log file
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    if entry.get("log_type") == "llm_request":
                        total_requests += 1
                        providers.add(entry.get("provider", "unknown"))
                        models.add(entry.get("model", "unknown"))
                    
                    elif entry.get("log_type") == "llm_response":
                        token_usage = entry.get("token_usage", {})
                        if token_usage:
                            total_tokens += token_usage.get("total_tokens", 0)
                
                except json.JSONDecodeError:
                    continue
    
    print(f"\nAnalysis results:")
    print(f"  Total requests: {total_requests}")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Providers: {', '.join(providers)}")
    print(f"  Models: {', '.join(models)}")


def demo_logging_stats():
    """Demonstrate logging statistics."""
    print("\n=== Logging Statistics Demo ===")
    
    try:
        stats = get_logging_stats()
        
        print("System statistics:")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Log level: {stats.get('config', {}).get('log_level', 'unknown')}")
        print(f"  Current log file: {stats.get('current_log_file', 'none')}")
        print(f"  Total log files: {stats.get('total_log_files', 0)}")
        print(f"  Total size: {stats.get('total_size_mb', 0)} MB")
        print(f"  Log directory: {stats.get('log_directory', 'unknown')}")
        
        config = stats.get('config', {})
        print(f"\nConfiguration:")
        print(f"  Max file size: {config.get('max_file_size_mb', 'unknown')} MB")
        print(f"  Max files: {config.get('max_files', 'unknown')}")
        print(f"  Compress old files: {config.get('compress_old_files', 'unknown')}")
        print(f"  Mask sensitive data: {config.get('mask_sensitive_data', 'unknown')}")
        
    except Exception as e:
        print(f"Error getting logging stats: {e}")


def cleanup_demo_logs():
    """Clean up demo log files."""
    print("\n=== Cleanup ===")
    
    log_dir = Path("demo_logs")
    if log_dir.exists():
        import shutil
        shutil.rmtree(log_dir)
        print("✓ Demo log files cleaned up")
    else:
        print("✓ No demo log files to clean up")


def main():
    """Run all demos."""
    print("Internal LLM Logging System Demo")
    print("=" * 40)
    
    try:
        # Run demos
        logger = demo_basic_logging()
        demo_configuration()
        demo_sensitive_data_masking()
        demo_agent_context()
        demo_log_analysis()
        demo_logging_stats()
        
        print("\n" + "=" * 40)
        print("✓ All demos completed successfully!")
        print(f"✓ Check the demo_logs directory for generated log files")
        
        # Ask if user wants to clean up
        response = input("\nClean up demo log files? (y/N): ").strip().lower()
        if response in ('y', 'yes'):
            cleanup_demo_logs()
        else:
            print("Demo log files preserved for inspection")
            
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
