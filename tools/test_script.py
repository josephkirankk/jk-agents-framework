#!/usr/bin/env python
"""Simple test script to verify Python execution"""

import sys
import os

def main():
    print("Python version:", sys.version)
    print("Current directory:", os.getcwd())
    print("Script is running successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
