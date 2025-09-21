"""
Setup script for the Defect Analysis Pipeline.

This script provides installation and setup utilities for the defect analysis pipeline.
"""

import os
import sys
import subprocess
from pathlib import Path


def install_requirements():
    """Install required packages."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ Requirements file not found!")
        return False
    
    try:
        print("📦 Installing requirements...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def check_dependencies():
    """Check if all dependencies are available."""
    required_modules = [
        "pipefunc",
        "pydantic", 
        "aiohttp",
        "vectordb_wrapper"
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - Available")
        except ImportError:
            print(f"❌ {module} - Missing")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {', '.join(missing_modules)}")
        return False
    
    print("\n✅ All dependencies are available!")
    return True


def check_configuration():
    """Check if required configuration files exist."""
    config_files = [
        "config/jk-gemba.yaml",
        "vectordb_wrapper/__init__.py"
    ]
    
    missing_files = []
    
    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            print(f"✅ {config_file} - Found")
        else:
            print(f"❌ {config_file} - Missing")
            missing_files.append(config_file)
    
    if missing_files:
        print(f"\n⚠️  Missing configuration files: {', '.join(missing_files)}")
        print("Please ensure the jk-agents project is properly set up.")
        return False
    
    print("\n✅ All configuration files are available!")
    return True


def run_tests():
    """Run the test suite."""
    test_file = Path(__file__).parent / "test_pipeline.py"
    
    if not test_file.exists():
        print("❌ Test file not found!")
        return False
    
    try:
        print("🧪 Running tests...")
        subprocess.check_call([
            sys.executable, "-m", "pytest", str(test_file), "-v"
        ])
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False


def run_example():
    """Run the example script."""
    example_file = Path(__file__).parent / "example.py"
    
    if not example_file.exists():
        print("❌ Example file not found!")
        return False
    
    try:
        print("🚀 Running example...")
        subprocess.check_call([sys.executable, str(example_file)])
        print("✅ Example completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Example failed: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("DEFECT ANALYSIS PIPELINE SETUP")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Setup steps
    steps = [
        ("Installing requirements", install_requirements),
        ("Checking dependencies", check_dependencies),
        ("Checking configuration", check_configuration),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        print("-" * 40)
        
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    # Optional steps
    print("\nOptional steps:")
    print("1. Run tests: python setup.py test")
    print("2. Run example: python setup.py example")
    print("3. View documentation: docs/DEFECT_ANALYSIS_PIPELINE.md")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            run_tests()
        elif command == "example":
            run_example()
        elif command == "deps":
            check_dependencies()
        elif command == "config":
            check_configuration()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, example, deps, config")
    else:
        main()
