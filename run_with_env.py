#!/usr/bin/env python3
"""
Environment Configuration Helper Script

This script allows you to run any command with a specific environment configuration.
It automatically sets the ENVIRONMENT variable to load the appropriate vars.[env].yaml file.

Usage:
    python run_with_env.py production python your_script.py [args]
    python run_with_env.py staging python tests/test_agent_continuity.py
    python run_with_env.py development python -m app.main

Examples:
    python run_with_env.py production python api.py
    python run_with_env.py staging python -m app.main "analyze my work items"
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse


def verify_environment_config(env_name):
    """Verify that the environment config file exists."""
    config_file = Path("config") / f"vars.{env_name}.yaml"
    if not config_file.exists():
        print(f"⚠️  Warning: Config file {config_file} does not exist.")
        print(f"   This may cause the environment '{env_name}' to not load properly.")
        return False
    return True


def list_available_environments():
    """List all available environment configurations."""
    config_dir = Path("config")
    environments = []
    
    if not config_dir.exists():
        print("❌ Error: config directory not found")
        return environments
    
    for file in config_dir.glob("vars.*.yaml"):
        if file.name.startswith("vars.") and file.name.endswith(".yaml"):
            env_name = file.name[5:-5]  # Extract environment name from vars.[env].yaml
            if env_name != "local":  # Skip vars.local.yaml
                environments.append(env_name)
    
    return environments


def run_with_environment(environment, command):
    """Run a command with the specified environment."""
    # Copy the current environment variables
    env = os.environ.copy()
    
    # Set the ENVIRONMENT variable
    env["ENVIRONMENT"] = environment
    
    # Print execution information
    print(f"🚀 Running command with {environment} environment")
    print(f"   Loading config from: config/vars.{environment}.yaml")
    print(f"   Command: {' '.join(command)}")
    print("="*60)
    
    # Execute the command with the modified environment
    return subprocess.run(command, env=env)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run a command with specific environment configuration")
    parser.add_argument("environment", help="Environment to use (production, staging, development)")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    parser.add_argument("--list", action="store_true", help="List available environments")
    
    args = parser.parse_args()
    
    # List available environments if requested
    if args.list:
        environments = list_available_environments()
        if environments:
            print("📂 Available environments:")
            for env in environments:
                print(f"   - {env}")
        else:
            print("❌ No environment configuration files found")
        return 0
    
    # Make sure an environment was specified
    if not args.environment:
        parser.print_help()
        print("\n❌ Error: No environment specified")
        return 1
    
    # Make sure a command was specified
    if not args.command:
        parser.print_help()
        print("\n❌ Error: No command specified")
        return 1
    
    # Verify the environment configuration
    verify_environment_config(args.environment)
    
    # Run the command with the specified environment
    result = run_with_environment(args.environment, args.command)
    
    # Return the exit code from the command
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
