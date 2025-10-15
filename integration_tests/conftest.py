"""
Pytest fixtures for integration tests - NO MOCKING
All tests interact with real systems: LLMs, ChromaDB, file system, etc.

Fixtures provide:
- Database setup/teardown
- Live LLM clients
- Environment configuration
- Shared test utilities
"""

import asyncio
import os
import sys
import time
import uuid
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from project root (parent of integration_tests directory)
from dotenv import load_dotenv
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Log if .env was loaded (helpful for debugging)
if env_path.exists():
    print(f"✓ Loaded .env from: {env_path}")
else:
    print(f"⚠ Warning: .env file not found at: {env_path}")

# Import core modules
from app.main import load_app_config
from app.checkpointer_manager import (
    get_global_checkpointer, clear_thread_memory, reset_all_memory,
    reset_checkpointer_singleton
)
from app.memory_integration import initialize_conversation_memory
from app.file_storage_manager import get_file_storage_manager
from app.mcp_loader import close_mcp_client

# Import test utilities
from test_utils import (
    TestEnvironment,
    check_azure_credentials,
    check_google_credentials,
    check_anthropic_credentials,
    verify_chromadb_available,
    convert_app_config_to_dict
)


# ============================================================================
# Session-scoped fixtures (setup once per test session)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function", autouse=True)
def reset_singletons():
    """
    Reset singleton instances between tests to ensure test isolation.
    This runs automatically before each test function.
    """
    # Reset before test
    try:
        reset_checkpointer_singleton()
    except Exception as e:
        print(f"Warning: Failed to reset singleton before test: {e}")
    
    yield
    
    # Reset after test
    try:
        reset_checkpointer_singleton()
    except Exception as e:
        print(f"Warning: Failed to reset singleton after test: {e}")


@pytest.fixture(scope="session")
def test_root_dir():
    """Root directory of the project."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def config_dir(test_root_dir):
    """Configuration directory."""
    return test_root_dir / "config"


@pytest.fixture(scope="session")
def data_dir(test_root_dir):
    """Data directory for test databases."""
    data_dir = test_root_dir / "integration_tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture(scope="session")
def temp_dir():
    """Temporary directory for test files (cleaned up after session)."""
    temp_path = Path(tempfile.mkdtemp(prefix="jk_agents_test_"))
    yield temp_path
    # Cleanup after all tests
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="session")
def env_config():
    """
    Environment configuration from .env file.
    Returns dict with provider credentials.
    """
    ado_pat = os.getenv("AZURE_DEVOPS_EXT_PAT")
    return {
        "azure_openai": {
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
            "available": check_azure_credentials()
        },
        "google": {
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "available": check_google_credentials()
        },
        "anthropic": {
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "available": check_anthropic_credentials()
        },
        "azure_devops": {
            "pat_token": ado_pat,
            "available": bool(ado_pat)
        },
        "chromadb": {
            "available": verify_chromadb_available()
        }
    }


@pytest.fixture(scope="session")
def llm_config(env_config):
    """
    LLM configuration for tests.
    Uses Azure OpenAI as primary provider with fallbacks.
    """
    if env_config["azure_openai"]["available"]:
        return {
            "provider": "azure_openai",
            "model": f"azure_openai:{env_config['azure_openai']['deployment']}",
            "temperature": 0,
            "top_p": 1.0,
            "max_tokens": 2000
        }
    elif env_config["google"]["available"]:
        return {
            "provider": "google",
            "model": "google:gemini-1.5-flash",
            "temperature": 0,
            "top_p": 1.0,
            "max_tokens": 2000
        }
    elif env_config["anthropic"]["available"]:
        return {
            "provider": "anthropic",
            "model": "anthropic:claude-3-haiku-20240307",
            "temperature": 0,
            "top_p": 1.0,
            "max_tokens": 2000
        }
    else:
        pytest.skip("No LLM provider credentials configured")


# ============================================================================
# Function-scoped fixtures (setup/teardown per test)
# ============================================================================

@pytest.fixture
def test_thread_id():
    """Generate unique thread ID for each test."""
    return f"test_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def test_env(test_root_dir, temp_dir):
    """
    Test environment with cleanup.
    Provides helper methods for creating test files.
    """
    env = TestEnvironment(f"test_{uuid.uuid4().hex[:8]}")
    yield env
    # Cleanup after test
    env.cleanup()


@pytest.fixture
async def chromadb_memory(test_thread_id, data_dir, test_config):
    """
    ChromaDB memory backend initialized for test.
    Automatically cleans up test thread after test completes.
    """
    if not verify_chromadb_available():
        pytest.skip("ChromaDB not available")
    
    # Initialize conversation memory for test (using test config)
    await initialize_conversation_memory(test_config)
    
    yield test_thread_id
    
    # Cleanup: Clear test thread memory
    try:
        clear_thread_memory(test_thread_id)
    except Exception as e:
        print(f"Warning: Failed to clear test thread memory: {e}")


@pytest.fixture
async def clean_memory():
    """
    Clean all memory before test.
    Use this fixture for tests that need a fresh memory state.
    """
    try:
        reset_all_memory()
        reset_checkpointer_singleton()
    except Exception as e:
        print(f"Warning: Failed to reset memory: {e}")
    yield
    # Cleanup after test too
    try:
        reset_checkpointer_singleton()
    except Exception as e:
        print(f"Warning: Failed to reset checkpointer after test: {e}")


@pytest.fixture
def test_config(config_dir, llm_config):
    """
    Load a working test configuration.
    Returns loaded AppConfig object.
    """
    # Use simple config without MCP servers for basic tests
    config_path = config_dir / "simple_test_no_mcp.yaml"
    if not config_path.exists():
        # Fallback to python_exec_agent_working
        config_path = config_dir / "python_exec_agent_working.yaml"
        if not config_path.exists():
            # Final fallback
            config_path = config_dir / "agents.yaml"
    
    return load_app_config(config_path)


@pytest.fixture
async def test_agent(test_config, test_thread_id):
    """
    Build a test agent with real LLM.
    Returns compiled agent ready for invocation.
    """
    from app.agent_builder import build_agent
    
    # Get first agent config
    agent_cfg = test_config.agents[0]
    default_model = test_config.models.get("default", "azure_openai:gpt-4.1")
    
    # Convert AppConfig to dict and preserve memory config (critical for checkpointer)
    app_config_dict = convert_app_config_to_dict(test_config)
    
    # Build agent with app_config for proper checkpointer initialization
    agent, mcp_client = await build_agent(
        agent_cfg=agent_cfg,
        default_model=default_model,
        config_path=str(test_config.config_path) if hasattr(test_config, "config_path") else "",
        app_config=app_config_dict
    )
    
    yield agent
    
    # Cleanup MCP client
    if mcp_client:
        try:
            await close_mcp_client(mcp_client)
        except Exception as e:
            print(f"Warning: Failed to close MCP client: {e}")


@pytest.fixture
def file_storage():
    """
    File storage manager for handling uploaded files.
    """
    return get_file_storage_manager()


@pytest.fixture
def performance_tracker():
    """
    Track performance metrics during test.
    Returns dict with timing information.
    """
    metrics = {
        "start_time": time.time(),
        "operations": []
    }
    
    def track_operation(name: str, duration: float):
        metrics["operations"].append({
            "name": name,
            "duration": duration,
            "timestamp": time.time()
        })
    
    metrics["track"] = track_operation
    
    yield metrics
    
    metrics["total_duration"] = time.time() - metrics["start_time"]


# ============================================================================
# Utility fixtures
# ============================================================================

@pytest.fixture
def retry_config():
    """
    Retry configuration for transient LLM failures.
    """
    return {
        "max_retries": 3,
        "initial_delay": 1.0,
        "backoff_factor": 2.0,
        "max_delay": 10.0
    }


@pytest.fixture
async def cleanup_files(temp_dir):
    """
    Cleanup files created during test.
    Use this as a context manager or fixture.
    """
    files_to_cleanup = []
    
    def register_file(filepath: Path):
        files_to_cleanup.append(filepath)
    
    yield register_file
    
    # Cleanup registered files
    for filepath in files_to_cleanup:
        if filepath.exists():
            try:
                filepath.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {filepath}: {e}")


# ============================================================================
# Skip markers for conditional tests
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "azure: mark test as requiring Azure OpenAI credentials"
    )
    config.addinivalue_line(
        "markers", "google: mark test as requiring Google Gemini credentials"
    )
    config.addinivalue_line(
        "markers", "anthropic: mark test as requiring Anthropic credentials"
    )
    config.addinivalue_line(
        "markers", "chromadb: mark test as requiring ChromaDB"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (>30 seconds)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically skip tests based on markers and available credentials."""
    env_config = {
        "azure": check_azure_credentials(),
        "google": check_google_credentials(),
        "anthropic": check_anthropic_credentials(),
        "chromadb": verify_chromadb_available()
    }
    
    for item in items:
        # Check for provider markers
        for provider in ["azure", "google", "anthropic", "chromadb"]:
            if provider in item.keywords and not env_config[provider]:
                item.add_marker(
                    pytest.mark.skip(reason=f"{provider.title()} credentials not configured")
                )
