#!/usr/bin/env python3
"""
Debug ChromaDB 'v' KeyError investigation script.

This script reproduces the exact error conditions to understand where
the 'v' KeyError is occurring in multi-turn conversations.
"""

import asyncio
import json
import logging
import traceback
from typing import Dict, Any

# Set up logging to capture all debug information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_v_error.log')
    ]
)

log = logging.getLogger(__name__)

async def investigate_chromadb_v_error():
    """Investigate the ChromaDB 'v' KeyError issue step by step."""
    
    print("🔍 Starting ChromaDB 'v' KeyError Investigation")
    print("=" * 60)
    
    try:
        # Import the memory system components
        from app.memory.langgraph_adapter import HighPerformanceCheckpointer
        from app.memory.manager import ResourceLimits
        
        # Create checkpointer with debug configuration
        config = {
            "memory": {
                "backend": "chromadb",
                "chromadb": {
                    "path": "./debug_chromadb_memory",
                    "max_connections": 5,
                    "batch_size": 10,
                    "enable_batch_processing": False,  # Disable for clearer debugging
                    "l1_cache_size": 100
                }
            }
        }
        
        checkpointer = HighPerformanceCheckpointer(config)
        
        print("✅ Created checkpointer instance")
        
        # Initialize the checkpointer
        await checkpointer._ensure_initialized()
        print("✅ Initialized checkpointer")
        
        # Test 1: Store first checkpoint (this should work)
        print("\n📝 Test 1: Store first checkpoint")
        thread_id = "debug-thread-001"
        config1 = {"configurable": {"thread_id": thread_id}}
        
        # Create a realistic checkpoint structure
        test_checkpoint = {
            "v": 4,
            "id": "checkpoint-001",
            "ts": "2025-01-01T00:00:00+00:00",
            "channel_values": {
                "messages": [
                    {"role": "user", "content": "First message"},
                    {"role": "assistant", "content": "First response"}
                ]
            },
            "channel_versions": {"messages": 1},
            "versions_seen": {"messages": 1},
            "pending_sends": []
        }
        
        test_metadata = {
            "thread_id": thread_id,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "step": 1
        }
        
        test_new_versions = {"messages": 1}
        
        # Store first checkpoint
        result_config = await checkpointer.aput(config1, test_checkpoint, test_metadata, test_new_versions)
        print(f"✅ Stored first checkpoint: {result_config}")
        
        # Test 2: Retrieve first checkpoint (this should work)
        print("\n📖 Test 2: Retrieve first checkpoint")
        retrieved_checkpoint = await checkpointer.aget(config1)
        
        if retrieved_checkpoint:
            print(f"✅ Retrieved first checkpoint successfully")
            print(f"   Type: {type(retrieved_checkpoint)}")
            print(f"   Keys: {list(retrieved_checkpoint.keys()) if isinstance(retrieved_checkpoint, dict) else 'N/A'}")
            print(f"   Version field 'v': {retrieved_checkpoint.get('v') if isinstance(retrieved_checkpoint, dict) else 'N/A'}")
        else:
            print("❌ Failed to retrieve first checkpoint")
            return
        
        # Test 3: Store second checkpoint (multi-turn scenario)
        print("\n📝 Test 3: Store second checkpoint (multi-turn)")
        
        # Create updated checkpoint for second turn
        test_checkpoint_2 = {
            "v": 4,
            "id": "checkpoint-002",
            "ts": "2025-01-01T00:01:00+00:00",
            "channel_values": {
                "messages": [
                    {"role": "user", "content": "First message"},
                    {"role": "assistant", "content": "First response"},
                    {"role": "user", "content": "Second message"},
                    {"role": "assistant", "content": "Second response"}
                ]
            },
            "channel_versions": {"messages": 2},
            "versions_seen": {"messages": 2},
            "pending_sends": []
        }
        
        test_metadata_2 = {
            "thread_id": thread_id,
            "timestamp": "2025-01-01T00:01:00+00:00",
            "step": 2
        }
        
        test_new_versions_2 = {"messages": 2}
        
        # Store second checkpoint
        result_config_2 = await checkpointer.aput(config1, test_checkpoint_2, test_metadata_2, test_new_versions_2)
        print(f"✅ Stored second checkpoint: {result_config_2}")
        
        # Test 4: Retrieve second checkpoint (this is where the error likely occurs)
        print("\n📖 Test 4: Retrieve second checkpoint (potential error point)")
        
        try:
            retrieved_checkpoint_2 = await checkpointer.aget(config1)
            
            if retrieved_checkpoint_2:
                print(f"✅ Retrieved second checkpoint successfully")
                print(f"   Type: {type(retrieved_checkpoint_2)}")
                print(f"   Keys: {list(retrieved_checkpoint_2.keys()) if isinstance(retrieved_checkpoint_2, dict) else 'N/A'}")
                print(f"   Version field 'v': {retrieved_checkpoint_2.get('v') if isinstance(retrieved_checkpoint_2, dict) else 'N/A'}")
            else:
                print("❌ Retrieved None for second checkpoint")
                
        except KeyError as e:
            print(f"🚨 CAUGHT KeyError: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            
            # Analyze the error
            await analyze_keyerror(e, checkpointer, thread_id)
            
        except Exception as e:
            print(f"🚨 CAUGHT Other Exception: {type(e).__name__}: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
        
        # Test 5: Direct ChromaDB inspection
        print("\n🔬 Test 5: Direct ChromaDB inspection")
        await inspect_chromadb_data(checkpointer, thread_id)
        
    except Exception as e:
        print(f"🚨 CRITICAL ERROR in investigation: {type(e).__name__}: {e}")
        print("Full traceback:")
        print(traceback.format_exc())

async def analyze_keyerror(error: KeyError, checkpointer, thread_id: str):
    """Analyze the KeyError to understand its root cause."""
    
    print("\n🔍 Analyzing KeyError:")
    print(f"   Error message: {error}")
    print(f"   Error args: {error.args}")
    
    # Check if it's the 'v' key specifically
    if str(error).strip("'\"") == "v":
        print("   ✅ Confirmed: This is the 'v' KeyError we're investigating")
        
        # Try to access the raw data from ChromaDB
        try:
            if checkpointer._manager and checkpointer._manager._backend:
                raw_data = await checkpointer._manager._backend.checkpoint_store.retrieve_checkpoint(
                    checkpointer._user_id, thread_id
                )
                
                if raw_data:
                    print(f"   Raw data retrieved: {len(raw_data)} bytes")
                    print(f"   Raw data type: {type(raw_data)}")
                    
                    # Try to decode and parse the raw data
                    try:
                        if isinstance(raw_data, bytes):
                            decoded = raw_data.decode('utf-8')
                            print(f"   Decoded length: {len(decoded)}")
                            
                            parsed = json.loads(decoded)
                            print(f"   Parsed data type: {type(parsed)}")
                            print(f"   Parsed keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'N/A'}")
                            
                            if isinstance(parsed, dict) and "checkpoint" in parsed:
                                checkpoint_data = parsed["checkpoint"]
                                print(f"   Checkpoint data type: {type(checkpoint_data)}")
                                print(f"   Checkpoint keys: {list(checkpoint_data.keys()) if isinstance(checkpoint_data, dict) else 'N/A'}")
                                print(f"   Has 'v' field: {'v' in checkpoint_data if isinstance(checkpoint_data, dict) else 'N/A'}")
                                
                                if isinstance(checkpoint_data, dict) and 'v' in checkpoint_data:
                                    print(f"   'v' field value: {checkpoint_data['v']} (type: {type(checkpoint_data['v'])})")
                                else:
                                    print("   ❌ Missing 'v' field in checkpoint data!")
                                    print(f"   Checkpoint content: {checkpoint_data}")
                    
                    except json.JSONDecodeError as je:
                        print(f"   ❌ JSON decode error: {je}")
                        print(f"   Raw decoded string (first 200 chars): {decoded[:200] if isinstance(decoded, str) else 'N/A'}")
                    
                    except Exception as pe:
                        print(f"   ❌ Parse error: {pe}")
                
                else:
                    print("   ❌ No raw data found in ChromaDB")
        
        except Exception as e:
            print(f"   ❌ Error accessing raw data: {e}")
    
    else:
        print(f"   ❌ Different KeyError: {error}")

async def inspect_chromadb_data(checkpointer, thread_id: str):
    """Directly inspect ChromaDB collections and data."""
    
    try:
        if not checkpointer._manager or not checkpointer._manager._backend:
            print("   ❌ No backend available for inspection")
            return
        
        backend = checkpointer._manager._backend
        
        # Get collection info
        print(f"   Thread ID: {thread_id}")
        print(f"   User ID: {checkpointer._user_id}")
        
        # Try to list all checkpoints for this thread
        checkpoints = await backend.checkpoint_store.list_checkpoints(
            checkpointer._user_id, thread_id
        )
        
        print(f"   Found {len(checkpoints)} checkpoints:")
        for i, cp in enumerate(checkpoints):
            print(f"     {i+1}. ID: {cp.get('id', 'N/A')}")
            print(f"        Thread: {cp.get('thread_id', 'N/A')}")
            print(f"        Timestamp: {cp.get('timestamp', 'N/A')}")
            print(f"        Size: {cp.get('size', 'N/A')} bytes")
        
        # Try direct ChromaDB access
        print("\n   Direct ChromaDB collection access:")
        if hasattr(backend, '_pool') and backend._pool:
            async with backend._pool.acquire() as client:
                collection_name = backend.checkpoint_store._get_collection_name(checkpointer._user_id)
                print(f"   Collection name: {collection_name}")
                
                try:
                    collection = client.get_collection(collection_name)
                    
                    # Get all documents for this thread
                    results = collection.get(
                        where={"thread_id": thread_id},
                        include=["metadatas", "documents", "ids"]
                    )
                    
                    print(f"   Direct query results:")
                    print(f"     IDs: {len(results.get('ids', []))}")
                    print(f"     Documents: {len(results.get('documents', []))}")
                    print(f"     Metadatas: {len(results.get('metadatas', []))}")
                    
                    # Examine each document
                    documents = results.get("documents", [])
                    metadatas = results.get("metadatas", [])
                    ids = results.get("ids", [])
                    
                    for i, (doc_id, doc, meta) in enumerate(zip(ids, documents, metadatas)):
                        print(f"\n     Document {i+1}:")
                        print(f"       ID: {doc_id}")
                        print(f"       Metadata: {meta}")
                        print(f"       Document length: {len(doc) if doc else 0}")
                        
                        if doc:
                            try:
                                parsed_doc = json.loads(doc)
                                print(f"       Document keys: {list(parsed_doc.keys()) if isinstance(parsed_doc, dict) else 'N/A'}")
                                
                                if isinstance(parsed_doc, dict) and "checkpoint" in parsed_doc:
                                    checkpoint = parsed_doc["checkpoint"]
                                    print(f"       Checkpoint keys: {list(checkpoint.keys()) if isinstance(checkpoint, dict) else 'N/A'}")
                                    print(f"       Has 'v': {'v' in checkpoint if isinstance(checkpoint, dict) else 'N/A'}")
                                    if isinstance(checkpoint, dict) and 'v' in checkpoint:
                                        print(f"       'v' value: {checkpoint['v']} (type: {type(checkpoint['v'])})")
                            
                            except Exception as e:
                                print(f"       Document parse error: {e}")
                                print(f"       Document content (first 100 chars): {doc[:100]}")
                
                except Exception as e:
                    print(f"   Collection access error: {e}")
        
    except Exception as e:
        print(f"   ChromaDB inspection error: {e}")
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    print("🚀 Running ChromaDB 'v' KeyError Investigation")
    asyncio.run(investigate_chromadb_v_error())
    print("\n✅ Investigation completed. Check debug_v_error.log for detailed logs.")
