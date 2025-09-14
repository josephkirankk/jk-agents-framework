#!/usr/bin/env python3
"""
JK-Agents with Custom OpenAI Endpoint Startup Script

This script starts both a custom OpenAI-compatible service and the JK-Agents API,
allowing seamless integration between the two systems.

Usage:
    python scripts/start_with_custom_endpoint.py [options]
    
Options:
    --service-port 8080        Port for custom OpenAI service
    --api-port 8001           Port for JK-Agents API
    --service-dir DIR         Directory containing the custom service
    --config CONFIG           Configuration file to use
"""

import argparse
import os
import subprocess
import sys
import time
import signal
from pathlib import Path
from typing import List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ServiceManager:
    """Manages multiple services with proper cleanup."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def start_service(self, name: str, command: List[str], 
                     cwd: Optional[Path] = None) -> subprocess.Popen:
        """Start a service and track it."""
        print(f"🚀 Starting {name}...")
        print(f"   Command: {' '.join(command)}")
        if cwd:
            print(f"   Working directory: {cwd}")
        
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(process)
            print(f"✅ {name} started with PID {process.pid}")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            raise
    
    def stop_all(self):
        """Stop all tracked services."""
        print("\n🛑 Stopping all services...")
        self.running = False
        
        for process in self.processes:
            if process.poll() is None:  # Process is still running
                print(f"   Stopping PID {process.pid}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"   Force killing PID {process.pid}...")
                    process.kill()
                except Exception as e:
                    print(f"   Error stopping PID {process.pid}: {e}")
        
        print("✅ All services stopped")
    
    def wait_for_service(self, url: str, timeout: int = 30) -> bool:
        """Wait for a service to become available."""
        import requests
        
        print(f"⏳ Waiting for service at {url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Service at {url} is ready")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(1)
        
        print(f"❌ Service at {url} not ready within {timeout} seconds")
        return False


def setup_environment(service_port: int):
    """Set up environment variables for custom OpenAI endpoint."""
    print("🔧 Setting up environment variables...")
    
    # Set custom OpenAI endpoint configuration
    base_url = f"http://127.0.0.1:{service_port}/v1"
    api_key = os.getenv("CUSTOM_OPENAI_API_KEY", "sk-test-key1")
    
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["OPENAI_API_KEY"] = api_key
    
    print(f"   OPENAI_BASE_URL = {base_url}")
    print(f"   OPENAI_API_KEY = {api_key}")


def check_service_directory(service_dir: Path) -> bool:
    """Check if custom service directory is properly configured."""
    if not service_dir.exists():
        print(f"❌ Service directory not found: {service_dir}")
        return False
    
    start_script = service_dir / "start.py"
    if not start_script.exists():
        print(f"❌ start.py not found in: {service_dir}")
        return False
    
    print(f"✅ Service directory found: {service_dir}")
    return True


def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(
        description="Start JK-Agents with custom OpenAI endpoint"
    )
    parser.add_argument("--service-port", type=int, default=8080, 
                       help="Port for custom OpenAI service (default: 8080)")
    parser.add_argument("--api-port", type=int, default=8001,
                       help="Port for JK-Agents API (default: 8001)")
    parser.add_argument("--service-dir", type=str, 
                       default="pepgenx_openai_wrapper",
                       help="Directory containing custom service")
    parser.add_argument("--config", type=str, 
                       default="config/openai_custom_endpoint.yaml",
                       help="Configuration file to use")
    
    args = parser.parse_args()
    
    print("🚀 JK-Agents with Custom OpenAI Endpoint")
    print("=" * 50)
    
    # Check prerequisites
    service_dir = project_root / args.service_dir
    if not check_service_directory(service_dir):
        sys.exit(1)
    
    # Setup environment
    setup_environment(args.service_port)
    
    # Create service manager
    manager = ServiceManager()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n📡 Received signal {signum}")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start custom OpenAI service
        service_process = manager.start_service(
            "Custom OpenAI Service",
            [sys.executable, "start.py"],
            cwd=service_dir
        )
        
        # Wait for service to be ready
        service_url = f"http://127.0.0.1:{args.service_port}"
        if not manager.wait_for_service(service_url):
            raise Exception("Custom OpenAI service failed to start")
        
        # Start JK-Agents API
        api_process = manager.start_service(
            "JK-Agents API",
            [
                sys.executable, "-m", "uvicorn", 
                "app.api:app", 
                "--host", "0.0.0.0", 
                "--port", str(args.api_port),
                "--reload"
            ],
            cwd=project_root
        )
        
        # Wait for API to be ready
        api_url = f"http://127.0.0.1:{args.api_port}"
        if not manager.wait_for_service(api_url):
            raise Exception("JK-Agents API failed to start")
        
        print("\n🎉 All services are running!")
        print("=" * 50)
        print(f"📡 Custom Service: {service_url}")
        print(f"📡 JK-Agents API:  {api_url}")
        print(f"📚 API Docs:       {api_url}/docs")
        print(f"📋 Configuration:  {args.config}")
        print("\n💡 Custom OpenAI endpoint is now available!")
        print("   JK-Agents will use the custom endpoint automatically")
        print("\n🛑 Press Ctrl+C to stop all services")
        
        # Keep running until interrupted
        while manager.running:
            time.sleep(1)
            
            # Check if any process has died
            for process in manager.processes:
                if process.poll() is not None:
                    print(f"❌ Process {process.pid} stopped unexpectedly")
                    manager.stop_all()
                    sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n📡 Received keyboard interrupt")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    finally:
        manager.stop_all()


if __name__ == "__main__":
    main()
