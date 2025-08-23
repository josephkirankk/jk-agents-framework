#!/usr/bin/env python3
"""
Example client for the JK-Agents FastAPI interface.

This script demonstrates how to interact with the multi-agent system via HTTP API.
"""
import requests
import json
import time
from typing import Dict, Any, Optional


class JKAgentsClient:
    """Client for interacting with the JK-Agents API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client with the API base URL."""
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health status of the API server."""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}
    
    def query(
        self,
        question: str,
        config_path: Optional[str] = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Send a query to the multi-agent system (supervised execution).

        Args:
            question: The user's question or prompt
            config_path: Optional path to configuration file
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing the response from the API
        """
        payload = {"input": question}
        if config_path:
            payload["config_path"] = config_path

        try:
            response = requests.post(
                f"{self.base_url}/query",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "response": "",
                "error": str(e)
            }

    def worker(
        self,
        agent_name: str,
        question: str,
        config_path: Optional[str] = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Execute a specific agent directly (single agent execution).

        Args:
            agent_name: Name of the agent to execute
            question: The user's question or prompt
            config_path: Optional path to configuration file
            timeout: Request timeout in seconds

        Returns:
            Dictionary containing the response from the API
        """
        payload = {
            "agent_name": agent_name,
            "input": question
        }
        if config_path:
            payload["config_path"] = config_path

        try:
            response = requests.post(
                f"{self.base_url}/worker",
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {
                "success": False,
                "response": "",
                "agent_name": agent_name,
                "error": str(e)
            }


def demo_basic_usage():
    """Demonstrate basic API usage."""
    print("=== JK-Agents API Client Demo ===\n")
    
    client = JKAgentsClient()
    
    # Health check
    print("1. Health Check")
    health = client.health_check()
    if "error" in health:
        print(f"❌ Health check failed: {health['error']}")
        return
    else:
        print(f"✅ API is {health['status']} (version {health['version']})")
    
    print("\n" + "="*50 + "\n")
    
    # Example queries (supervised execution)
    queries = [
        {
            "question": "what is the temperature in mumbai and add it with the temperature in delhi",
            "config": "config/brave_math_weather_hybrid.yaml",
            "description": "Complex multi-step query (supervised)"
        }
    ]

    # Example worker calls (direct execution)
    worker_calls = [
        {
            "agent_name": "weather_agent",
            "question": "what is the temperature in mumbai",
            "config": "config/brave_math_weather_hybrid.yaml",
            "description": "Weather agent (direct)"
        },
        {
            "agent_name": "math_agent",
            "question": "calculate 15 + 27",
            "config": "config/brave_math_weather_hybrid.yaml",
            "description": "Math agent (direct)"
        }
    ]
    
    # Test supervised queries
    for i, query_info in enumerate(queries, 2):
        print(f"{i}. {query_info['description']}")
        print(f"Question: {query_info['question']}")

        start_time = time.time()
        result = client.query(
            query_info["question"],
            query_info["config"]
        )
        end_time = time.time()

        if result["success"]:
            print(f"✅ Success ({end_time - start_time:.1f}s)")
            print(f"Answer: {result['response']}")
            if result.get("metadata"):
                metadata = result["metadata"]
                print(f"Steps: {metadata.get('total_steps', 'unknown')}")
                print(f"Model: {metadata.get('model_used', 'unknown')}")
        else:
            print(f"❌ Failed ({end_time - start_time:.1f}s)")
            print(f"Error: {result['error']}")

        print("\n" + "="*50 + "\n")

    # Test direct worker calls
    for i, worker_info in enumerate(worker_calls, len(queries) + 2):
        print(f"{i}. {worker_info['description']}")
        print(f"Agent: {worker_info['agent_name']}")
        print(f"Question: {worker_info['question']}")

        start_time = time.time()
        result = client.worker(
            worker_info["agent_name"],
            worker_info["question"],
            worker_info["config"]
        )
        end_time = time.time()

        if result["success"]:
            print(f"✅ Success ({end_time - start_time:.1f}s)")
            print(f"Response: {result['response']}")
            if result.get("metadata"):
                metadata = result["metadata"]
                print(f"Model: {metadata.get('model_used', 'unknown')}")
        else:
            print(f"❌ Failed ({end_time - start_time:.1f}s)")
            print(f"Error: {result['error']}")

        print("\n" + "="*50 + "\n")


def demo_interactive_mode():
    """Interactive mode for testing queries."""
    print("=== Interactive Mode ===")
    print("Enter your questions (type 'quit' to exit)")
    print("Format: question [| config_path]")
    print("Example: what is the weather in delhi | config/brave_math_weather_hybrid.yaml")
    print()
    
    client = JKAgentsClient()
    
    while True:
        try:
            user_input = input("Query: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            # Parse input for optional config path
            parts = user_input.split(' | ')
            question = parts[0].strip()
            config_path = parts[1].strip() if len(parts) > 1 else None
            
            print(f"Processing: {question}")
            if config_path:
                print(f"Using config: {config_path}")
            
            start_time = time.time()
            result = client.query(question, config_path)
            end_time = time.time()
            
            print(f"\nResult ({end_time - start_time:.1f}s):")
            if result["success"]:
                print(f"✅ {result['response']}")
            else:
                print(f"❌ Error: {result['error']}")
            print()
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function to run the demo."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        demo_interactive_mode()
    else:
        demo_basic_usage()
        
        print("💡 Tip: Run with --interactive for interactive mode")
        print("   python examples/api_client_example.py --interactive")


if __name__ == "__main__":
    main()
