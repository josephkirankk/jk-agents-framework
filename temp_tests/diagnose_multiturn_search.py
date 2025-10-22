"""
Comprehensive diagnosis of multi-turn conversation and search issues.

This script will:
1. Test search tool functionality (google_search)
2. Test multi-turn conversation memory
3. Test ChromaDB backend initialization
4. Identify configuration issues
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import yaml
import asyncio
from typing import Dict, Any

print("\n" + "=" * 80)
print("  MULTI-TURN & SEARCH DIAGNOSTIC TOOL")
print("=" * 80)

# Test 1: Configuration Loading
print("\n" + "=" * 80)
print("TEST 1: Configuration Analysis")
print("=" * 80)

config_path = "config/deep_agent_advanced_serpapi.yaml"
print(f"\nAnalyzing config: {config_path}")

try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check memory configuration
    print("\n📋 Memory Configuration:")
    if 'memory' in config:
        mem_cfg = config['memory']
        print(f"  Backend: {mem_cfg.get('backend', 'NOT SET')}")
        if 'chromadb' in mem_cfg:
            chroma = mem_cfg['chromadb']
            print(f"  ChromaDB Path: {chroma.get('path', 'NOT SET')}")
            print(f"  ChromaDB Host: {chroma.get('host', 'NOT SET')}")
            print(f"  ChromaDB Port: {chroma.get('port', 'NOT SET')}")
            print(f"  Checkpoint Collection: {chroma.get('checkpoint_collection', 'NOT SET')}")
            print(f"  Context Collection: {chroma.get('context_collection', 'NOT SET')}")
    else:
        print("  ❌ ISSUE: No 'memory' section found in config")
    
    # Check conversation memory
    print("\n💬 Conversation Memory Configuration:")
    if 'conversation_memory' in config:
        conv_mem = config['conversation_memory']
        print(f"  Enabled: {conv_mem.get('enabled', False)}")
        print(f"  Database URL: '{conv_mem.get('database_url', '')}' (empty = in-memory)")
        print(f"  Max Conversations: {conv_mem.get('max_conversations', 'NOT SET')}")
        print(f"  Max Context Length: {conv_mem.get('max_context_length', 'NOT SET')}")
        
        # Issue check
        if conv_mem.get('enabled') and not conv_mem.get('database_url'):
            print("  ⚠️  WARNING: Conversation memory enabled but database_url is empty")
            print("               This will use in-memory storage (not persistent)")
    else:
        print("  ❌ ISSUE: No 'conversation_memory' section found")
    
    # Check MCP servers
    print("\n🔧 MCP Servers Configuration:")
    agents = config.get('agents', [])
    for agent in agents:
        if 'mcp_servers' in agent:
            print(f"\n  Agent: {agent.get('name')}")
            for server_name, server_config in agent['mcp_servers'].items():
                print(f"    - {server_name}:")
                print(f"        Command: {server_config.get('command')}")
                print(f"        Args: {server_config.get('args')}")
                
                # Check env vars
                if 'env' in server_config:
                    for key, value in server_config['env'].items():
                        if '${' in str(value):
                            # Extract var name
                            var_name = value.replace('${', '').replace('}', '')
                            actual_value = os.getenv(var_name, 'NOT_SET')
                            status = "✓" if actual_value and actual_value != 'NOT_SET' else "❌"
                            print(f"        {status} {key}: ${{{var_name}}} = {actual_value[:20] if actual_value != 'NOT_SET' else 'NOT_SET'}...")
    
    print("\n✅ Configuration loaded successfully")
    
except Exception as e:
    print(f"\n❌ FAILED to load configuration: {e}")
    import traceback
    traceback.print_exc()

# Test 2: SerperToolWrapper Check
print("\n" + "=" * 80)
print("TEST 2: SerperToolWrapper Functionality")
print("=" * 80)

try:
    from app.mcp_loader import SerperToolWrapper
    from unittest.mock import Mock
    
    print("\n✅ SerperToolWrapper imported successfully")
    
    # Test parameter injection
    mock_tool = Mock()
    mock_tool.name = "google_search"
    mock_tool.description = "Test"
    
    wrapper = SerperToolWrapper(inner=mock_tool)
    
    # Test 1: Minimal params
    test_params = {"query": "test"}
    result = wrapper._inject_defaults(test_params)
    
    if result.get("gl") == "us" and result.get("hl") == "en":
        print("✅ Parameter injection working: defaults added")
        print(f"     Input:  {{'query': 'test'}}")
        print(f"     Output: {result}")
    else:
        print("❌ Parameter injection FAILED")
        print(f"     Expected gl='us', hl='en'")
        print(f"     Got: {result}")
    
    # Test 2: Custom params
    test_params2 = {"query": "test", "gl": "in", "hl": "hi"}
    result2 = wrapper._inject_defaults(test_params2)
    
    if result2.get("gl") == "in" and result2.get("hl") == "hi":
        print("✅ Custom parameters preserved")
    else:
        print("❌ Custom parameters NOT preserved")
        print(f"     Got: {result2}")
        
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Memory Integration
print("\n" + "=" * 80)
print("TEST 3: Memory Integration")
print("=" * 80)

try:
    from app.memory_integration import (
        initialize_conversation_memory,
        is_conversation_memory_enabled,
        store_conversation_turn,
        get_conversation_context
    )
    from app.types import AppConfig
    from pathlib import Path
    
    print("\n✅ Memory integration module imported")
    
    # Load config as AppConfig - must use Path object
    from app.main import load_app_config
    
    app_cfg = load_app_config(Path(config_path))
    print(f"\n📋 AppConfig loaded for {config_path}")
    
    # Check if conversation memory is enabled
    is_enabled = is_conversation_memory_enabled(app_cfg)
    print(f"  Conversation memory enabled: {is_enabled}")
    
    # Initialize memory
    async def test_memory():
        init_result = await initialize_conversation_memory(app_cfg)
        print(f"  Memory initialization: {'✅ SUCCESS' if init_result else '❌ FAILED'}")
        
        # Test storing a turn
        test_thread = "test-thread-12345"
        store_result = await store_conversation_turn(
            test_thread,
            "Hello, this is a test",
            "Hello! I received your test message."
        )
        print(f"  Store conversation turn: {'✅ SUCCESS' if store_result else '❌ FAILED'}")
        
        # Test retrieving context
        context = get_conversation_context(test_thread)
        if context and "Hello" in context:
            print(f"  Retrieve context: ✅ SUCCESS")
            print(f"     Context preview: {context[:100]}...")
        else:
            print(f"  Retrieve context: ❌ FAILED or EMPTY")
            print(f"     Got: {context}")
    
    asyncio.run(test_memory())
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 4: ChromaDB Backend
print("\n" + "=" * 80)
print("TEST 4: ChromaDB Backend Check")
print("=" * 80)

try:
    from app.memory.chromadb_backend import ChromaDBBackend, ChromaDBConfig
    
    print("\n✅ ChromaDB backend imported")
    
    # Check if ChromaDB directory exists
    chroma_path = "./serp_memory"
    if os.path.exists(chroma_path):
        print(f"  ✅ ChromaDB path exists: {chroma_path}")
        # List contents
        contents = os.listdir(chroma_path)
        print(f"     Contents: {contents[:5] if len(contents) > 5 else contents}")
    else:
        print(f"  ⚠️  ChromaDB path does NOT exist: {chroma_path}")
        print(f"      Will be created on first use")
    
    # Try to initialize backend
    async def test_chromadb():
        try:
            # Create config object
            chroma_config = ChromaDBConfig(
                path=chroma_path,
                checkpoint_collection="test-checkpoints",
                context_collection="test-contexts"
            )
            
            backend = ChromaDBBackend(config=chroma_config)
            print("  ✅ ChromaDBBackend created")
            
            # Initialize backend
            await backend.initialize({"chromadb": {"path": chroma_path}})
            print("  ✅ ChromaDB backend initialized")
            
            # Test checkpoint store
            checkpoint_store = backend.checkpoint_store
            print("  ✅ Checkpoint store accessible")
            
            # Test storing a checkpoint
            test_checkpoint = b'{"test": "data"}'
            await checkpoint_store.store_checkpoint(
                user_id="test-user",
                thread_id="test-thread",
                checkpoint_data=test_checkpoint
            )
            print("  ✅ Test checkpoint stored")
            
            # Test retrieving checkpoint
            retrieved = await checkpoint_store.get_checkpoint(
                user_id="test-user",
                thread_id="test-thread"
            )
            if retrieved:
                print(f"  ✅ Checkpoint retrieval working")
            else:
                print("  ⚠️  Checkpoint retrieval returned None")
                
        except Exception as e:
            print(f"  ❌ ChromaDB test FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    asyncio.run(test_chromadb())
    
except Exception as e:
    print(f"❌ FAILED to test ChromaDB: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Search Tool Availability
print("\n" + "=" * 80)
print("TEST 5: Search Tool Availability")
print("=" * 80)

try:
    print("\nChecking if Serper API key is set...")
    serper_key = os.getenv("SERPER_API_KEY")
    
    if serper_key:
        print(f"  ✅ SERPER_API_KEY is set: {serper_key[:10]}...")
    else:
        print("  ❌ SERPER_API_KEY is NOT set")
        print("      The google_search tool will NOT work without this!")
    
    # Check if npx is available
    print("\nChecking if npx is available...")
    import subprocess
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"  ✅ npx is available: {result.stdout.strip()}")
        else:
            print(f"  ❌ npx command failed: {result.stderr}")
    except FileNotFoundError:
        print("  ❌ npx NOT found - Node.js/npm not installed or not in PATH")
    except subprocess.TimeoutExpired:
        print("  ⚠️  npx command timed out")
    except Exception as e:
        print(f"  ❌ Error checking npx: {e}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")

# Summary
print("\n" + "=" * 80)
print("  DIAGNOSTIC SUMMARY")
print("=" * 80)

print("\n🔍 Key Findings:")
print("\n1. Configuration Issues:")
print("   - Check if conversation_memory.database_url is empty")
print("   - Check if memory.backend is properly set to 'chromadb'")
print("\n2. Tool Issues:")
print("   - SerperToolWrapper must accept **kwargs (recently fixed)")
print("   - SERPER_API_KEY must be set in environment")
print("\n3. Memory Issues:")
print("   - In-memory storage is not persistent")
print("   - ChromaDB backend needs proper initialization")
print("\n4. Multi-turn Issues:")
print("   - Conversation context must be properly passed to agents")
print("   - Thread IDs must be consistent across turns")

print("\n📝 Next Steps:")
print("1. Review the test outputs above for any ❌ FAILED items")
print("2. Fix configuration issues identified")
print("3. Ensure SERPER_API_KEY is set")
print("4. Test actual query with multi-turn conversation")
print("=" * 80 + "\n")
