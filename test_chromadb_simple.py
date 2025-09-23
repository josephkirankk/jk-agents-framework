#!/usr/bin/env python3
"""
Simple test for ChromaDB integration.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    
    try:
        import chromadb
        print("✅ chromadb imported successfully")
    except ImportError as e:
        print(f"❌ chromadb import failed: {e}")
        return False
    
    try:
        from langchain_chroma import Chroma
        print("✅ langchain_chroma imported successfully")
    except ImportError as e:
        print(f"❌ langchain_chroma import failed: {e}")
        return False
    
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("✅ HuggingFaceEmbeddings imported successfully")
    except ImportError as e:
        print(f"❌ HuggingFaceEmbeddings import failed: {e}")
        return False
    
    try:
        from app.memory.chromadb_checkpointer import ChromaDBCheckpointer
        print("✅ ChromaDBCheckpointer imported successfully")
    except ImportError as e:
        print(f"❌ ChromaDBCheckpointer import failed: {e}")
        return False
    
    try:
        from app.memory.simple_chromadb_memory import SimpleChromaDBMemory
        print("✅ SimpleChromaDBMemory imported successfully")
    except ImportError as e:
        print(f"❌ SimpleChromaDBMemory import failed: {e}")
        return False
    
    return True

def test_basic_chromadb():
    """Test basic ChromaDB functionality."""
    print("\nTesting basic ChromaDB functionality...")
    
    try:
        import chromadb
        from langchain_chroma import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        # Create a simple test
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Create vector store
        vectorstore = Chroma(
            collection_name="test_collection",
            embedding_function=embeddings,
            persist_directory="./test_chroma_db"
        )
        
        # Add some test data
        texts = ["Hello world", "This is a test", "ChromaDB is working"]
        vectorstore.add_texts(texts)
        
        # Search
        results = vectorstore.similarity_search("test", k=1)
        
        if results:
            print(f"✅ ChromaDB search successful: {results[0].page_content}")
            return True
        else:
            print("❌ ChromaDB search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_checkpointer():
    """Test ChromaDB checkpointer."""
    print("\nTesting ChromaDB checkpointer...")
    
    try:
        from app.memory.chromadb_checkpointer import ChromaDBCheckpointer
        
        # Create checkpointer
        checkpointer = ChromaDBCheckpointer("./test_checkpoints")
        
        # Test config
        config = {
            "configurable": {
                "thread_id": "test_thread"
            }
        }
        
        # Test checkpoint
        checkpoint = {"test": "data"}
        metadata = {"timestamp": "2024-01-01"}
        
        # Store and retrieve
        checkpointer.put(config, checkpoint, metadata, {})
        retrieved = checkpointer.get(config)
        
        if retrieved and retrieved.get("test") == "data":
            print("✅ ChromaDB checkpointer working correctly")
            return True
        else:
            print(f"❌ ChromaDB checkpointer failed: {retrieved}")
            return False
            
    except Exception as e:
        print(f"❌ ChromaDB checkpointer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Simple ChromaDB Integration Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic ChromaDB", test_basic_chromadb),
        ("Checkpointer Test", test_checkpointer)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed.")
