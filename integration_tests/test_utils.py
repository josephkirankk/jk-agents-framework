"""
Shared utilities for integration tests - NO MOCKING
All tests interact with real systems (Azure OpenAI, ChromaDB, file system, etc.)
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage


def convert_app_config_to_dict(app_config) -> Dict[str, Any]:
    """
    Convert AppConfig to dict while preserving memory configuration.
    
    This is critical for proper checkpointer initialization with memory backends.
    The _raw_memory_config attribute must be preserved to avoid "Unsupported backend: none" errors.
    
    Args:
        app_config: AppConfig object from load_app_config()
        
    Returns:
        Dict with all config data including preserved memory backend configuration
    """
    # Convert to dict using Pydantic methods
    if hasattr(app_config, 'model_dump'):
        config_dict = app_config.model_dump()
    elif hasattr(app_config, 'dict'):
        config_dict = app_config.dict()
    else:
        config_dict = app_config.__dict__
    
    # CRITICAL: Preserve raw memory config if present
    # This ensures memory backend configuration is properly passed to checkpointer
    if hasattr(app_config, '_raw_memory_config'):
        config_dict['memory'] = app_config._raw_memory_config
    
    return config_dict


class TestResult:
    """Track test execution results"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.passed = False
        self.error = None
        self.details = {}
        self.sub_tests = []
    
    def finish(self, passed: bool, error: Optional[str] = None, **details):
        self.end_time = time.time()
        self.passed = passed
        self.error = error
        self.details = details
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def add_sub_test(self, name: str, passed: bool, **details):
        self.sub_tests.append({
            "name": name,
            "passed": passed,
            "details": details
        })
    
    def print_result(self):
        """Print formatted test result"""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        print(f"\n{'=' * 80}")
        print(f"{status}: {self.test_name}")
        print(f"Duration: {self.duration:.2f}s")
        
        if self.error:
            print(f"Error: {self.error}")
        
        if self.details:
            print("\nDetails:")
            for key, value in self.details.items():
                if isinstance(value, (dict, list)):
                    print(f"  {key}: {json.dumps(value, indent=4)}")
                else:
                    print(f"  {key}: {value}")
        
        if self.sub_tests:
            print("\nSub-tests:")
            for sub in self.sub_tests:
                status = "✅" if sub["passed"] else "❌"
                print(f"  {status} {sub['name']}")
                if sub["details"]:
                    for key, value in sub["details"].items():
                        print(f"      {key}: {value}")
        
        print("=" * 80)


class TestEnvironment:
    """Manage test environment and cleanup"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.test_dir = Path(__file__).parent.parent
        self.temp_files = []
        self.temp_dirs = []
        
    def get_config_path(self, config_name: str) -> Path:
        """Get path to config file"""
        return self.test_dir / "config" / config_name
    
    def create_temp_file(self, filename: str, content: str = "") -> Path:
        """Create temporary file for testing"""
        temp_file = self.test_dir / "integration_tests" / "temp" / filename
        temp_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file.write_text(content)
        self.temp_files.append(temp_file)
        return temp_file
    
    def cleanup(self):
        """Clean up temporary test files"""
        for file in self.temp_files:
            try:
                if file.exists():
                    file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {file}: {e}")
        
        for dir in self.temp_dirs:
            try:
                if dir.exists():
                    import shutil
                    shutil.rmtree(dir)
            except Exception as e:
                print(f"Warning: Failed to delete {dir}: {e}")


def check_azure_credentials() -> bool:
    """Check if Azure OpenAI credentials are configured"""
    required = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
        "AZURE_OPENAI_API_VERSION"
    ]
    
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"⚠️  Missing Azure OpenAI credentials: {', '.join(missing)}")
        return False
    
    return True


def check_google_credentials() -> bool:
    """Check if Google API credentials are configured"""
    return bool(os.getenv("GOOGLE_API_KEY"))


def check_anthropic_credentials() -> bool:
    """Check if Anthropic API credentials are configured"""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


async def invoke_agent(agent, query: str, thread_id: Optional[str] = None, 
                       config: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Invoke agent with query and return response
    
    Args:
        agent: Compiled LangGraph agent
        query: User query string
        thread_id: Optional thread ID for multi-turn conversations
        config: Optional configuration dict
        
    Returns:
        Dict with response and metadata
    """
    # Prepare input
    input_data = {"messages": [HumanMessage(content=query)]}
    
    # Prepare config
    if config is None:
        config = {}
    
    if thread_id:
        config["configurable"] = {"thread_id": thread_id}
    
    # Invoke agent
    start_time = time.time()
    result = await agent.ainvoke(input_data, config=config)
    end_time = time.time()
    
    # Extract response
    messages = result.get("messages", [])
    last_message = messages[-1] if messages else None
    response_text = last_message.content if last_message else ""
    
    return {
        "response": response_text,
        "messages": messages,
        "duration": end_time - start_time,
        "message_count": len(messages),
        "last_message": last_message
    }


def extract_tool_calls(messages: List) -> List[Dict]:
    """Extract tool calls from message history"""
    tool_calls = []
    
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "tool_name": tc.get("name", "unknown"),
                    "args": tc.get("args", {}),
                    "id": tc.get("id", "")
                })
    
    return tool_calls


def verify_chromadb_available() -> bool:
    """Check if ChromaDB is available and working"""
    try:
        import chromadb
        # Try to create a test client
        client = chromadb.Client()
        return True
    except Exception as e:
        print(f"⚠️  ChromaDB not available: {e}")
        return False


def print_test_header(title: str):
    """Print formatted test header"""
    print(f"\n\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_section(title: str):
    """Print section header"""
    print(f"\n{'-' * 80}")
    print(f"  {title}")
    print(f"{'-' * 80}")


class TestStats:
    """Track overall test statistics"""
    
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []
        self.start_time = time.time()
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total += 1
        if result.passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def skip_test(self, name: str, reason: str):
        self.total += 1
        self.skipped += 1
        print(f"\n⏭️  SKIPPED: {name}")
        print(f"   Reason: {reason}")
    
    @property
    def duration(self) -> float:
        return time.time() - self.start_time
    
    def print_summary(self):
        """Print final test summary"""
        print(f"\n\n{'=' * 80}")
        print("  INTEGRATION TEST SUMMARY")
        print(f"{'=' * 80}")
        print(f"\nTotal Tests: {self.total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏭️  Skipped: {self.skipped}")
        print(f"\nTotal Duration: {self.duration:.2f}s")
        print(f"Pass Rate: {(self.passed / max(self.total - self.skipped, 1)) * 100:.1f}%")
        
        if self.failed > 0:
            print(f"\n{'=' * 80}")
            print("  FAILED TESTS:")
            print(f"{'=' * 80}")
            for result in self.results:
                if not result.passed:
                    print(f"\n❌ {result.test_name}")
                    if result.error:
                        print(f"   Error: {result.error}")
        
        print(f"\n{'=' * 80}\n")
        
        return self.failed == 0


__all__ = [
    "TestResult",
    "TestEnvironment",
    "TestStats",
    "check_azure_credentials",
    "check_google_credentials",
    "check_anthropic_credentials",
    "invoke_agent",
    "extract_tool_calls",
    "verify_chromadb_available",
    "print_test_header",
    "print_section",
    "convert_app_config_to_dict"
]
