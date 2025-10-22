#!/usr/bin/env python
"""
DeepAgent Integration Verification Script

Comprehensive verification of DeepAgent integration without requiring API calls.
This script verifies all components are properly integrated and working.
"""

import sys
import os
from pathlib import Path
import asyncio

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Print section header."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    """Print info message."""
    print(f"   {text}")


class VerificationSuite:
    """Comprehensive verification suite."""
    
    def __init__(self):
        self.results = []
    
    def test(self, name, func):
        """Run a test and record result."""
        try:
            result = func()
            if result:
                print_success(f"{name}")
                self.results.append((name, True, None))
            else:
                print_error(f"{name}")
                self.results.append((name, False, "Test returned False"))
        except Exception as e:
            print_error(f"{name}: {e}")
            self.results.append((name, False, str(e)))
    
    async def test_async(self, name, func):
        """Run an async test and record result."""
        try:
            result = await func()
            if result:
                print_success(f"{name}")
                self.results.append((name, True, None))
            else:
                print_error(f"{name}")
                self.results.append((name, False, "Test returned False"))
        except Exception as e:
            print_error(f"{name}: {e}")
            self.results.append((name, False, str(e)))
    
    def summary(self):
        """Print test summary."""
        print_header("VERIFICATION SUMMARY")
        
        passed = sum(1 for _, result, _ in self.results if result)
        failed = sum(1 for _, result, _ in self.results if not result)
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        
        if failed > 0:
            print(f"\n{RED}Failed Tests:{RESET}")
            for name, result, error in self.results:
                if not result:
                    print(f"  • {name}")
                    if error:
                        print(f"    Error: {error}")
        
        print(f"\n{BLUE}{'='*70}{RESET}")
        
        if failed == 0:
            print(f"{GREEN}🎉 ALL VERIFICATIONS PASSED!{RESET}")
        else:
            print(f"{RED}⚠️  Some verifications failed{RESET}")
        
        return failed == 0


# ============================================================================
# Test Functions
# ============================================================================

def test_deepagents_package():
    """Verify DeepAgents package is installed."""
    try:
        import deepagents
        print_info(f"DeepAgents package found")
        return True
    except ImportError:
        print_info("DeepAgents package NOT installed")
        return False


def test_config_imports():
    """Verify config models can be imported."""
    from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
    print_info("AgentConfig, DeepAgentConfig, SubAgentConfig imported")
    return True


def test_adapter_imports():
    """Verify adapter can be imported."""
    from app.deep_agent_adapter import DeepAgentAdapter, create_deep_agent_from_config
    print_info("DeepAgentAdapter and factory function imported")
    return True


def test_agent_builder_imports():
    """Verify agent builder recognizes DeepAgents."""
    from app.agent_builder import build_agent, HAS_DEEPAGENTS
    print_info(f"Agent builder imported (HAS_DEEPAGENTS={HAS_DEEPAGENTS})")
    return HAS_DEEPAGENTS


def test_agent_type_validation():
    """Verify 'deep' agent type is valid."""
    from app.config import AgentConfig
    config = AgentConfig(
        name="test",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="test"
    )
    print_info("'deep' agent type accepted")
    return config.agent_type == "deep"


def test_invalid_agent_type_rejected():
    """Verify invalid agent types are rejected."""
    from app.config import AgentConfig
    try:
        AgentConfig(
            name="test",
            agent_type="invalid",
            model="openai:gpt-4o-mini",
            prompt="test"
        )
        print_info("Invalid type was accepted (BAD)")
        return False
    except ValueError:
        print_info("Invalid agent type correctly rejected")
        return True


def test_deep_agent_config_creation():
    """Verify DeepAgentConfig can be created."""
    from app.config import DeepAgentConfig
    config = DeepAgentConfig(
        enabled=True,
        enable_filesystem=True,
        enable_todolist=True,
        enable_longterm_memory=False,
        subagents=[]
    )
    print_info(f"DeepAgentConfig created with filesystem={config.enable_filesystem}")
    return True


def test_subagent_config_creation():
    """Verify SubAgentConfig can be created."""
    from app.config import SubAgentConfig
    sub = SubAgentConfig(
        name="test_sub",
        description="Test subagent",
        system_prompt="Test prompt",
        model="openai:gpt-4o-mini",
        tools=["tool1", "tool2"]
    )
    print_info(f"SubAgentConfig created: {sub.name}")
    return sub.name == "test_sub"


def test_agent_config_with_deep_config():
    """Verify AgentConfig accepts deep_agent_config."""
    from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
    
    deep_config = DeepAgentConfig(
        enabled=True,
        subagents=[
            SubAgentConfig(
                name="sub1",
                description="Sub 1",
                system_prompt="Prompt"
            )
        ]
    )
    
    agent_config = AgentConfig(
        name="test",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="test",
        deep_agent_config=deep_config
    )
    
    print_info(f"AgentConfig with {len(agent_config.deep_agent_config.subagents)} subagents")
    return len(agent_config.deep_agent_config.subagents) == 1


async def test_react_agent_creation():
    """Verify ReAct agents still work."""
    from app.config import AgentConfig
    from app.agent_builder import build_agent
    from app.checkpointer_manager import get_global_checkpointer
    
    config = AgentConfig(
        name="test_react",
        agent_type="react",
        model="openai:gpt-4o-mini",
        prompt="Test prompt",
        mcp_servers={},
        http_tools={},
        python_tools={}
    )
    
    checkpointer = get_global_checkpointer()
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
        checkpointer=checkpointer
    )
    
    # Verify it's NOT a DeepAgentAdapter
    from app.deep_agent_adapter import DeepAgentAdapter
    is_react = not isinstance(agent, DeepAgentAdapter)
    
    print_info(f"ReAct agent created (not DeepAgent: {is_react})")
    
    # Cleanup
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except:
            pass
    
    return is_react


async def test_normal_agent_creation():
    """Verify Normal agents still work."""
    from app.config import AgentConfig
    from app.agent_builder import build_agent
    from app.checkpointer_manager import get_global_checkpointer
    
    config = AgentConfig(
        name="test_normal",
        agent_type="normal",
        model="openai:gpt-4o-mini",
        prompt="Test prompt",
        mcp_servers={},
        http_tools={},
        python_tools={}
    )
    
    checkpointer = get_global_checkpointer()
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
        checkpointer=checkpointer
    )
    
    # Verify it's NOT a DeepAgentAdapter
    from app.deep_agent_adapter import DeepAgentAdapter
    is_normal = not isinstance(agent, DeepAgentAdapter)
    
    print_info(f"Normal agent created (not DeepAgent: {is_normal})")
    
    # Cleanup
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except:
            pass
    
    return is_normal


async def test_deep_agent_creation():
    """Verify DeepAgent can be created."""
    from app.config import AgentConfig, DeepAgentConfig
    from app.agent_builder import build_agent
    from app.checkpointer_manager import get_global_checkpointer
    from app.deep_agent_adapter import DeepAgentAdapter
    
    config = AgentConfig(
        name="test_deep",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="Test prompt",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            subagents=[]
        ),
        mcp_servers={},
        http_tools={},
        python_tools={}
    )
    
    checkpointer = get_global_checkpointer()
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
        checkpointer=checkpointer
    )
    
    # Verify it IS a DeepAgentAdapter
    is_deep = isinstance(agent, DeepAgentAdapter)
    
    print_info(f"DeepAgent created (is DeepAgentAdapter: {is_deep})")
    
    # Cleanup
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except:
            pass
    
    return is_deep


async def test_deep_agent_with_subagents():
    """Verify DeepAgent with subagents can be created."""
    from app.config import AgentConfig, DeepAgentConfig, SubAgentConfig
    from app.agent_builder import build_agent
    from app.checkpointer_manager import get_global_checkpointer
    from app.deep_agent_adapter import DeepAgentAdapter
    
    subagents = [
        SubAgentConfig(
            name="sub1",
            description="Subagent 1",
            system_prompt="Test prompt 1"
        ),
        SubAgentConfig(
            name="sub2",
            description="Subagent 2",
            system_prompt="Test prompt 2"
        )
    ]
    
    config = AgentConfig(
        name="test_deep_with_subs",
        agent_type="deep",
        model="openai:gpt-4o-mini",
        prompt="Test orchestrator prompt",
        deep_agent_config=DeepAgentConfig(
            enabled=True,
            enable_filesystem=True,
            enable_todolist=True,
            subagents=subagents
        ),
        mcp_servers={},
        http_tools={},
        python_tools={}
    )
    
    checkpointer = get_global_checkpointer()
    agent, mcp_client = await build_agent(
        agent_cfg=config,
        default_model="openai:gpt-4o-mini",
        checkpointer=checkpointer
    )
    
    is_deep = isinstance(agent, DeepAgentAdapter)
    
    print_info(f"DeepAgent with {len(subagents)} subagents created")
    
    # Cleanup
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except:
            pass
    
    return is_deep


def test_requirements_file():
    """Verify deepagents is in requirements.txt."""
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print_info("requirements.txt not found")
        return False
    
    content = req_file.read_text()
    has_deepagents = "deepagents" in content
    
    print_info(f"deepagents in requirements.txt: {has_deepagents}")
    return has_deepagents


def test_example_files_exist():
    """Verify example files were created."""
    base = Path(__file__).parent
    
    files = [
        "examples/deep_agent_example.py",
        "examples/deep_agent_brave_search_example.py",
        "config/deep_agent_basic_example.yaml",
        "config/deep_agent_advanced_example.yaml",
        "temp_docs/DEEPAGENTS_INTEGRATION.md",
        "temp_docs/DEEPAGENTS_QUICK_REFERENCE.md",
        "temp_docs/DEEPAGENTS_README.md"
    ]
    
    missing = []
    for f in files:
        if not (base / f).exists():
            missing.append(f)
    
    if missing:
        print_info(f"Missing files: {', '.join(missing)}")
        return False
    
    print_info(f"All {len(files)} example/doc files exist")
    return True


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    """Run all verifications."""
    print_header("DeepAgent Integration Verification")
    print("This script verifies the DeepAgent integration is working correctly.\n")
    
    suite = VerificationSuite()
    
    # Phase 1: Package and Imports
    print_header("Phase 1: Package and Imports")
    suite.test("DeepAgents package installed", test_deepagents_package)
    suite.test("Config models import", test_config_imports)
    suite.test("Adapter imports", test_adapter_imports)
    suite.test("Agent builder recognizes DeepAgents", test_agent_builder_imports)
    
    # Phase 2: Configuration
    print_header("Phase 2: Configuration Validation")
    suite.test("'deep' agent type valid", test_agent_type_validation)
    suite.test("Invalid agent type rejected", test_invalid_agent_type_rejected)
    suite.test("DeepAgentConfig creation", test_deep_agent_config_creation)
    suite.test("SubAgentConfig creation", test_subagent_config_creation)
    suite.test("AgentConfig with deep_agent_config", test_agent_config_with_deep_config)
    
    # Phase 3: Agent Creation
    print_header("Phase 3: Agent Creation")
    await suite.test_async("ReAct agent creation (backward compat)", test_react_agent_creation)
    await suite.test_async("Normal agent creation (backward compat)", test_normal_agent_creation)
    await suite.test_async("DeepAgent creation", test_deep_agent_creation)
    await suite.test_async("DeepAgent with subagents creation", test_deep_agent_with_subagents)
    
    # Phase 4: Integration Completeness
    print_header("Phase 4: Integration Completeness")
    suite.test("deepagents in requirements.txt", test_requirements_file)
    suite.test("Example and documentation files exist", test_example_files_exist)
    
    # Summary
    success = suite.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
