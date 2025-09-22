#!/usr/bin/env python3
"""
VectorDB Wrapper CLI

Interactive command-line interface for testing VectorDB wrapper functionality.
Provides commands for health checks, searching, upserting, and batch operations.
"""

import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    # Try relative imports first (when run as module)
    from .client import VectorDBClient
    from .models import SearchRequest, UpsertRequest
    from .utils import setup_logging
    from .exceptions import VectorDBError, VectorDBConnectionError, VectorDBValidationError
except ImportError:
    # Fall back to absolute imports (when run directly)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from vectordb_wrapper.client import VectorDBClient
    from vectordb_wrapper.models import SearchRequest, UpsertRequest
    from vectordb_wrapper.utils import setup_logging
    from vectordb_wrapper.exceptions import VectorDBError, VectorDBConnectionError, VectorDBValidationError


class VectorDBCLI:
    """Interactive CLI for VectorDB wrapper."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the CLI with optional base URL."""
        self.base_url = base_url or os.getenv("VECTORDB_BASE_URL", "http://localhost:8010")
        self.client = VectorDBClient(base_url=self.base_url)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for the CLI."""
        setup_logging("INFO")
        
    async def start(self):
        """Start the interactive CLI."""
        print("🔍 VectorDB Wrapper CLI")
        print("=" * 50)
        print(f"Base URL: {self.base_url}")
        print("Type 'help' for available commands or 'quit' to exit.")
        print()
        
        try:
            while True:
                try:
                    command = input("vectordb> ").strip()
                    if not command:
                        continue
                        
                    if command.lower() in ['quit', 'exit', 'q']:
                        break
                    elif command.lower() in ['help', 'h', '?']:
                        self.show_help()
                    elif command.lower() in ['health', 'status']:
                        await self.health_check()
                    elif command.lower().startswith('search '):
                        await self.search_command(command[7:])
                    elif command.lower() == 'search':
                        await self.interactive_search()
                    elif command.lower().startswith('searchget '):
                        await self.search_get_command(command[10:])
                    elif command.lower() == 'searchget':
                        await self.interactive_search_get()
                    elif command.lower() == 'upsert':
                        await self.interactive_upsert()
                    elif command.lower() == 'batch':
                        await self.batch_upsert()
                    elif command.lower() == 'examples':
                        await self.run_examples()
                    elif command.lower() == 'config':
                        self.show_config()
                    elif command.lower().startswith('seturl '):
                        await self.set_url(command[7:])
                    else:
                        print(f"❌ Unknown command: {command}")
                        print("Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    print("\n⚠️  Operation cancelled.")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
        finally:
            if self.client:
                await self.client.close()
                
    def show_help(self):
        """Show available commands."""
        help_text = """
📋 Available Commands:

🔍 Search Commands:
  search <query>          - Search with inline query
  search                  - Interactive search with options
  searchget <query>       - Search using GET method with inline query  
  searchget               - Interactive GET search with options

📝 Data Commands:
  upsert                  - Interactive defect upsert
  batch                   - Batch upsert from JSON file

🔧 System Commands:
  health                  - Check API health status
  config                  - Show current configuration
  seturl <url>           - Change base URL
  examples               - Run example operations

ℹ️  General:
  help, h, ?             - Show this help
  quit, exit, q          - Exit CLI

💡 Tips:
  - Use Ctrl+C to cancel any operation
  - All operations are logged to vectorlogs/ directory
  - Set VECTORDB_BASE_URL environment variable for default URL
        """
        print(help_text)
        
    async def health_check(self):
        """Perform health check."""
        print("🏥 Checking API health...")
        try:
            health = await self.client.health_check()
            print(f"✅ Status: {health.status}")
            print(f"📝 Message: {health.message}")
            print(f"🔗 Pinecone Connected: {'✅' if health.pinecone_connected else '❌'}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            
    async def search_command(self, query: str):
        """Execute search with inline query."""
        if not query.strip():
            print("❌ Please provide a search query.")
            return

        print(f"🔍 Searching for: '{query}'")
        try:
            request = SearchRequest(query=query)
            response = await self.client.search(request)
            self.display_search_results(response)
        except Exception as e:
            print(f"❌ Search failed: {e}")

    async def interactive_search(self):
        """Interactive search with options."""
        print("🔍 Interactive Search")
        print("-" * 20)

        try:
            query = input("Enter search query: ").strip()
            if not query:
                print("❌ Query cannot be empty.")
                return

            top_n = input("Number of results (default: 5): ").strip()
            top_n = int(top_n) if top_n else 5

            min_score = input("Minimum score 0.0-1.0 (default: 0.1): ").strip()
            min_score = float(min_score) if min_score else 0.1

            print(f"\n🔍 Searching for: '{query}' (top_n={top_n}, min_score={min_score})")

            request = SearchRequest(query=query, top_n=top_n, min_score=min_score)
            response = await self.client.search(request)
            self.display_search_results(response)

        except ValueError as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ Search failed: {e}")

    async def search_get_command(self, query: str):
        """Execute GET search with inline query."""
        if not query.strip():
            print("❌ Please provide a search query.")
            return

        print(f"🔍 GET Searching for: '{query}'")
        try:
            response = await self.client.search_get(query=query)
            self.display_search_results(response)
        except Exception as e:
            print(f"❌ GET search failed: {e}")

    async def interactive_search_get(self):
        """Interactive GET search with options."""
        print("🔍 Interactive GET Search")
        print("-" * 25)

        try:
            query = input("Enter search query: ").strip()
            if not query:
                print("❌ Query cannot be empty.")
                return

            top_n = input("Number of results (default: 5): ").strip()
            top_n = int(top_n) if top_n else 5

            min_score = input("Minimum score 0.0-1.0 (default: 0.1): ").strip()
            min_score = float(min_score) if min_score else 0.1

            print(f"\n🔍 GET Searching for: '{query}' (top_n={top_n}, min_score={min_score})")

            response = await self.client.search_get(query=query, top_n=top_n, min_score=min_score)
            self.display_search_results(response)

        except ValueError as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ GET search failed: {e}")

    def display_search_results(self, response):
        """Display search results in a formatted way."""
        print(f"\n📊 Search Results:")
        print(f"   Query: {response.query}")
        print(f"   Total Results: {response.total_results}")
        print(f"   Execution Time: {response.execution_time_ms:.1f}ms")
        print()

        if not response.results:
            print("   No results found.")
            return

        for i, result in enumerate(response.results, 1):
            defect = result.defect
            print(f"   Result {i}:")
            print(f"     🏷️  Code: {defect.defect_code}")
            print(f"     📝 Text: {defect.defect_text}")
            print(f"     🎯 Score: {result.score:.1%}")
            print(f"     🔧 Subsystem: {defect.subsystem}")
            print(f"     ⚠️  Severity: {defect.severity}")
            if defect.symptoms:
                print(f"     🔍 Symptoms: {', '.join(defect.symptoms[:3])}{'...' if len(defect.symptoms) > 3 else ''}")
            print()

    async def interactive_upsert(self):
        """Interactive defect upsert."""
        print("📝 Interactive Defect Upsert")
        print("-" * 30)

        try:
            # Required fields
            defect_code = input("Defect Code (required): ").strip()
            if not defect_code:
                print("❌ Defect code is required.")
                return

            defect_text = input("Defect Description (required): ").strip()
            if not defect_text:
                print("❌ Defect description is required.")
                return

            subsystem = input("Subsystem (required): ").strip()
            if not subsystem:
                print("❌ Subsystem is required.")
                return

            # Optional fields
            severity = input("Severity (default: Medium): ").strip() or "Medium"
            frequency = input("Typical Frequency (default: Unknown): ").strip() or "Unknown"

            # List fields
            print("\nEnter lists (comma-separated, or press Enter to skip):")
            symptoms_input = input("Symptoms: ").strip()
            symptoms = [s.strip() for s in symptoms_input.split(',')] if symptoms_input else []

            detection_input = input("Detection Methods: ").strip()
            detection_methods = [s.strip() for s in detection_input.split(',')] if detection_input else []

            warning_input = input("Early Warning Signals: ").strip()
            early_warnings = [s.strip() for s in warning_input.split(',')] if warning_input else []

            tags_input = input("Tags: ").strip()
            tags = [s.strip() for s in tags_input.split(',')] if tags_input else []

            causes_input = input("Likely Root Causes: ").strip()
            root_causes = [s.strip() for s in causes_input.split(',')] if causes_input else []

            actions_input = input("Recommended Actions: ").strip()
            actions = [s.strip() for s in actions_input.split(',')] if actions_input else []

            # Create and execute upsert request
            print(f"\n📝 Upserting defect: {defect_code}")

            request = UpsertRequest(
                defect_code=defect_code,
                defect_text=defect_text,
                subsystem=subsystem,
                severity=severity,
                typical_frequency=frequency,
                symptoms=symptoms,
                detection_methods=detection_methods,
                early_warning_signals=early_warnings,
                tags=tags,
                likely_root_causes=root_causes,
                recommended_actions=actions
            )

            response = await self.client.upsert(request)

            print(f"✅ Success: {response.message}")
            print(f"🔧 Operation: {response.operation}")
            print(f"🏷️  Defect Code: {response.defect_code}")

        except Exception as e:
            print(f"❌ Upsert failed: {e}")

    async def batch_upsert(self):
        """Batch upsert from JSON file."""
        print("📦 Batch Upsert from JSON")
        print("-" * 25)

        try:
            file_path = input("Enter JSON file path: ").strip()
            if not file_path:
                print("❌ File path is required.")
                return

            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return

            print(f"📂 Reading file: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                json_content = f.read()

            print("🚀 Starting batch upsert...")
            result = await self.client.upsert_json_defects(json_content)

            print(f"\n📊 Batch Upsert Results:")
            print(f"   Total Defects: {result['total_defects']}")
            print(f"   ✅ Successful: {result['successful_upserts']}")
            print(f"   ❌ Failed: {result['failed_upserts']}")

            if result['successful_upserts'] > 0:
                success_rate = (result['successful_upserts'] / result['total_defects']) * 100
                print(f"   📈 Success Rate: {success_rate:.1f}%")

            if result['errors']:
                print(f"\n❌ Errors:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"   - Defect {error['defect_index']}: {error['error']}")
                if len(result['errors']) > 5:
                    print(f"   ... and {len(result['errors']) - 5} more errors")

        except Exception as e:
            print(f"❌ Batch upsert failed: {e}")

    async def run_examples(self):
        """Run example operations."""
        print("🚀 Running Example Operations")
        print("-" * 30)

        try:
            # Example search
            print("1. Example Search...")
            request = SearchRequest(query="motor bearing failure", top_n=3, min_score=0.7)
            response = await self.client.search(request)
            print(f"   Found {response.total_results} results in {response.execution_time_ms:.1f}ms")

            # Example upsert
            print("\n2. Example Upsert...")
            upsert_request = UpsertRequest(
                defect_code="CLI.TEST.EXAMPLE.001",
                defect_text="CLI test defect for demonstration",
                subsystem="CLI",
                severity="Low",
                symptoms=["test symptom"],
                tags=["cli", "test", "example"]
            )
            upsert_response = await self.client.upsert(upsert_request)
            print(f"   {upsert_response.message} ({upsert_response.operation})")

            # Example GET search
            print("\n3. Example GET Search...")
            get_response = await self.client.search_get("CLI test", top_n=2)
            print(f"   Found {get_response.total_results} results via GET method")

            print("\n✅ Examples completed successfully!")

        except Exception as e:
            print(f"❌ Examples failed: {e}")

    def show_config(self):
        """Show current configuration."""
        print("⚙️  Current Configuration")
        print("-" * 25)
        print(f"Base URL: {self.base_url}")
        print(f"Client Timeout: {self.client.timeout}s" if self.client else "Client: Not initialized")
        print(f"Max Retries: {self.client.max_retries}" if self.client else "")
        print(f"Environment VECTORDB_BASE_URL: {os.getenv('VECTORDB_BASE_URL', 'Not set')}")

    async def set_url(self, new_url: str):
        """Change the base URL."""
        if not new_url.strip():
            print("❌ URL cannot be empty.")
            return

        print(f"🔄 Changing base URL from {self.base_url} to {new_url}")

        # Close existing client
        if self.client:
            await self.client.close()

        # Update URL and create new client
        self.base_url = new_url
        self.client = VectorDBClient(base_url=self.base_url)

        print("✅ Base URL updated successfully!")

        # Test connection
        try:
            await self.health_check()
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to new URL: {e}")


def create_sample_json():
    """Create a sample JSON file for batch testing."""
    sample_data = {
        "defects": [
            {
                "defect_code": "CLI.SAMPLE.001",
                "defect_text": "Sample defect for CLI testing",
                "subsystem": "CLI",
                "severity": "Low",
                "symptoms": ["sample symptom 1", "sample symptom 2"],
                "detection_methods": ["visual inspection"],
                "tags": ["cli", "sample", "test"],
                "likely_root_causes": ["testing"],
                "recommended_actions": ["verify functionality"]
            },
            {
                "defect_code": "CLI.SAMPLE.002",
                "defect_text": "Another sample defect for batch testing",
                "subsystem": "CLI",
                "severity": "Medium",
                "symptoms": ["batch symptom"],
                "tags": ["cli", "batch", "test"]
            }
        ]
    }

    filename = "sample_defects.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)

    print(f"📄 Created sample JSON file: {filename}")
    return filename


async def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="VectorDB Wrapper CLI")
    parser.add_argument("--url", help="Base URL for VectorDB API")
    parser.add_argument("--create-sample", action="store_true",
                       help="Create sample JSON file for batch testing")

    args = parser.parse_args()

    if args.create_sample:
        create_sample_json()
        return

    cli = VectorDBCLI(base_url=args.url)
    await cli.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ CLI Error: {e}")
        sys.exit(1)
