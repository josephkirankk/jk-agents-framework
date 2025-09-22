#!/bin/bash
# VectorDB CLI Launcher for Unix/Linux/macOS
# This script provides easy access to the VectorDB CLI with various options

echo
echo "========================================"
echo "   VectorDB Wrapper CLI Launcher"
echo "========================================"
echo

# Check if virtual environment exists and activate it
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo
fi

# Function to show help
show_help() {
    echo "Usage: ./start_vectordb_cli.sh [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --sample       Create sample JSON file for testing"
    echo "  --test         Run CLI functionality test"
    echo "  --usage        Show detailed CLI usage examples"
    echo "  --url URL      Start CLI with custom base URL"
    echo
    echo "Examples:"
    echo "  ./start_vectordb_cli.sh"
    echo "  ./start_vectordb_cli.sh --url http://localhost:9000"
    echo "  ./start_vectordb_cli.sh --sample"
    echo "  ./start_vectordb_cli.sh --test"
    echo
}

# Check command line arguments
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    --sample)
        echo "Creating sample JSON file..."
        python -m vectordb_wrapper.cli --create-sample
        echo
        echo "Sample file created! You can now use it with the 'batch' command in CLI."
        exit 0
        ;;
    --test)
        echo "Running CLI functionality test..."
        python test_vectordb_cli.py
        exit 0
        ;;
    --usage)
        echo "Showing detailed CLI usage..."
        python test_vectordb_cli.py --usage
        exit 0
        ;;
    *)
        # Default: Start interactive CLI
        echo "Starting VectorDB CLI..."
        echo "Type 'help' for available commands or 'quit' to exit."
        echo
        python -m vectordb_wrapper.cli "$@"
        ;;
esac

echo
