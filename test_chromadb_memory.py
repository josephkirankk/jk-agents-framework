#!/usr/bin/env python3
"""
Comprehensive ChromaDB Memory Testing for JK-Agents API.
Tests ChromaDB backend with multiple agents and multi-turn conversations.
"""
import requests
import json
import sys
import time
import uuid

def test_chromadb_initialization():
    """Test if ChromaDB memory system is properly initialized."""
    print("🚀 Test 1: ChromaDB Memory System Initialization")
    print("-" * 60)
    
    # Test a simple agent call to trigger memory initialization
    response = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Initialize ChromaDB memory test",
            "config_path": "config/basic_test.yaml",
            "thread_id": "chromadb-init-test"
        }
    )
    
    if response.ok and response.json().get("success"):
        result = response.json()
        print(f"✅ ChromaDB initialization successful")
        print(f"   Response: {result['response']}")
        print(f"   Thread ID: {result['thread_id']}")
        return True
    else:
        print(f"❌ ChromaDB initialization failed")
        if response.ok:
            print(f"   Error: {response.json().get('error', 'Unknown error')}")
        return False

def test_multi_turn_conversation():
    """Test multi-turn conversation with ChromaDB memory persistence."""
    print("\n💬 Test 2: Multi-Turn Conversation with ChromaDB")
    print("-" * 60)
    
    thread_id = f"chromadb-multi-turn-{uuid.uuid4().hex[:8]}"
    conversation_data = []
    
    # Turn 1: Initial context
    print("Turn 1: Setting initial context...")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "I'm a data scientist working on a project to predict customer churn using machine learning. My name is Alex Chen.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response1.ok or not response1.json().get("success"):
        print("❌ Turn 1 failed")
        return False
        
    result1 = response1.json()
    conversation_data.append(("Turn 1", result1['response']))
    print(f"✅ Turn 1: {result1['response']}")
    time.sleep(1)
    
    # Turn 2: Add more context
    print("\nTurn 2: Adding project details...")
    response2 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "The dataset has 50,000 customers with features like usage patterns, payment history, and support tickets. I'm using Python with scikit-learn.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response2.ok or not response2.json().get("success"):
        print("❌ Turn 2 failed")
        return False
        
    result2 = response2.json()
    conversation_data.append(("Turn 2", result2['response']))
    print(f"✅ Turn 2: {result2['response']}")
    time.sleep(1)
    
    # Turn 3: Memory recall test - name
    print("\nTurn 3: Testing name recall...")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What's my name again?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response3.ok or not response3.json().get("success"):
        print("❌ Turn 3 failed")
        return False
        
    result3 = response3.json()
    conversation_data.append(("Turn 3", result3['response']))
    name_recalled = "alex" in result3['response'].lower() and "chen" in result3['response'].lower()
    print(f"✅ Turn 3: {result3['response']}")
    print(f"   Name recalled: {'✅' if name_recalled else '❌'}")
    time.sleep(1)
    
    # Turn 4: Memory recall test - project details
    print("\nTurn 4: Testing project details recall...")
    response4 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "How many customers are in my dataset and what machine learning library am I using?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response4.ok or not response4.json().get("success"):
        print("❌ Turn 4 failed")
        return False
        
    result4 = response4.json()
    conversation_data.append(("Turn 4", result4['response']))
    dataset_recalled = "50,000" in result4['response'] or "50000" in result4['response']
    library_recalled = "scikit-learn" in result4['response'].lower() or "sklearn" in result4['response'].lower()
    print(f"✅ Turn 4: {result4['response']}")
    print(f"   Dataset size recalled: {'✅' if dataset_recalled else '❌'}")
    print(f"   Library recalled: {'✅' if library_recalled else '❌'}")
    time.sleep(1)
    
    # Turn 5: Complex context integration
    print("\nTurn 5: Testing complex context integration...")
    response5 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Based on what I've told you about my project, what would be a good next step for improving my churn prediction model?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response5.ok or not response5.json().get("success"):
        print("❌ Turn 5 failed")
        return False
        
    result5 = response5.json()
    conversation_data.append(("Turn 5", result5['response']))
    context_integration = any(keyword in result5['response'].lower() for keyword in 
                            ['feature', 'model', 'churn', 'customer', 'data', 'prediction'])
    print(f"✅ Turn 5: {result5['response']}")
    print(f"   Context integration: {'✅' if context_integration else '❌'}")
    
    # Summary
    success = name_recalled and dataset_recalled and library_recalled and context_integration
    print(f"\n🎯 Multi-Turn Conversation Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Total turns: {len(conversation_data)}")
    print(f"   Thread ID: {thread_id}")
    
    return success

def test_concurrent_threads():
    """Test ChromaDB with multiple concurrent threads."""
    print("\n🔀 Test 3: Concurrent Thread Management")
    print("-" * 60)
    
    threads = {}
    
    # Create multiple threads with different contexts
    thread_configs = [
        ("thread-doctor", "I'm Dr. Smith, a cardiologist specializing in heart surgery."),
        ("thread-teacher", "I'm Ms. Johnson, a high school math teacher who loves calculus."),
        ("thread-engineer", "I'm Mike, a software engineer working on distributed systems.")
    ]
    
    # Store information in each thread
    print("Step 1: Storing information in multiple threads...")
    for thread_id, context in thread_configs:
        response = requests.post(
            "http://localhost:8000/worker",
            json={
                "agent_name": "simple_test_agent",
                "input": context,
                "config_path": "config/basic_test.yaml",
                "thread_id": thread_id
            }
        )
        
        if response.ok and response.json().get("success"):
            threads[thread_id] = {
                "context": context,
                "response": response.json()['response']
            }
            print(f"✅ {thread_id}: {response.json()['response']}")
        else:
            print(f"❌ {thread_id}: Failed to store context")
            return False
        
        time.sleep(0.5)
    
    # Test recall from each thread
    print("\nStep 2: Testing recall from each thread...")
    recall_tests = [
        ("thread-doctor", "What's my profession and specialization?"),
        ("thread-teacher", "What subject do I teach and what topic do I love?"),
        ("thread-engineer", "What's my job and what type of systems do I work on?")
    ]
    
    recall_results = {}
    for thread_id, question in recall_tests:
        response = requests.post(
            "http://localhost:8000/worker",
            json={
                "agent_name": "simple_test_agent",
                "input": question,
                "config_path": "config/basic_test.yaml",
                "thread_id": thread_id
            }
        )
        
        if response.ok and response.json().get("success"):
            result = response.json()['response']
            recall_results[thread_id] = result
            print(f"✅ {thread_id}: {result}")
        else:
            print(f"❌ {thread_id}: Failed to recall")
            return False
        
        time.sleep(0.5)
    
    # Verify thread isolation
    print("\nStep 3: Verifying thread isolation...")
    isolation_checks = [
        ("thread-doctor", ["cardiologist", "heart", "surgery", "dr", "smith"]),
        ("thread-teacher", ["teacher", "math", "calculus", "johnson"]),
        ("thread-engineer", ["engineer", "software", "distributed", "mike"])
    ]
    
    isolation_success = True
    for thread_id, keywords in isolation_checks:
        if thread_id in recall_results:
            response_lower = recall_results[thread_id].lower()
            matches = sum(1 for keyword in keywords if keyword in response_lower)
            thread_isolated = matches > 0
            print(f"{'✅' if thread_isolated else '❌'} {thread_id}: {matches}/{len(keywords)} keywords found")
            if not thread_isolated:
                isolation_success = False
    
    success = len(threads) == 3 and len(recall_results) == 3 and isolation_success
    print(f"\n🎯 Concurrent Thread Management Result: {'✅ PASSED' if success else '❌ FAILED'}")
    
    return success

def test_memory_persistence_across_restarts():
    """Test if ChromaDB persists data across agent restarts."""
    print("\n💾 Test 4: Memory Persistence Across Restarts")
    print("-" * 60)
    
    thread_id = f"persistence-test-{uuid.uuid4().hex[:8]}"
    
    # Store important information
    print("Step 1: Storing persistent information...")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Remember this important information: My project codename is 'Phoenix' and the secret key is 'Delta-7-Alpha'. This data should persist.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response1.ok or not response1.json().get("success"):
        print("❌ Step 1 failed")
        return False
        
    result1 = response1.json()
    print(f"✅ Information stored: {result1['response']}")
    time.sleep(1)
    
    # Add more context
    print("\nStep 2: Adding more context...")
    response2 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "The Phoenix project has a budget of $2.5 million and involves 15 team members across 3 departments.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response2.ok or not response2.json().get("success"):
        print("❌ Step 2 failed")
        return False
        
    result2 = response2.json()
    print(f"✅ Additional context: {result2['response']}")
    time.sleep(2)  # Give ChromaDB time to persist
    
    # Test immediate recall
    print("\nStep 3: Testing immediate recall...")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is the codename of my project, its budget, and the secret key?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response3.ok or not response3.json().get("success"):
        print("❌ Step 3 failed")
        return False
        
    result3 = response3.json()
    print(f"✅ Immediate recall: {result3['response']}")
    
    # Check if all key information is recalled
    response_lower = result3['response'].lower()
    codename_recalled = "phoenix" in response_lower
    key_recalled = "delta-7-alpha" in response_lower or "delta" in response_lower
    budget_recalled = "2.5" in result3['response'] or "million" in response_lower
    
    print(f"   Codename recalled: {'✅' if codename_recalled else '❌'}")
    print(f"   Secret key recalled: {'✅' if key_recalled else '❌'}")
    print(f"   Budget recalled: {'✅' if budget_recalled else '❌'}")
    
    success = codename_recalled and key_recalled and budget_recalled
    print(f"\n🎯 Memory Persistence Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Thread ID for future testing: {thread_id}")
    
    return success

def test_memory_scalability():
    """Test ChromaDB scalability with many messages in a thread."""
    print("\n📈 Test 5: Memory Scalability")
    print("-" * 60)
    
    thread_id = f"scalability-test-{uuid.uuid4().hex[:8]}"
    
    # Create a long conversation with many messages
    print("Step 1: Creating extended conversation...")
    topics = [
        "artificial intelligence and machine learning trends",
        "climate change and renewable energy solutions", 
        "space exploration and Mars colonization",
        "quantum computing and its applications",
        "biotechnology and genetic engineering",
        "cryptocurrency and blockchain technology",
        "virtual reality and augmented reality",
        "autonomous vehicles and transportation",
        "cybersecurity and data privacy",
        "social media and digital communication"
    ]
    
    conversation_summary = []
    for i, topic in enumerate(topics, 1):
        print(f"   Message {i}: {topic[:30]}...")
        response = requests.post(
            "http://localhost:8000/worker",
            json={
                "agent_name": "simple_test_agent",
                "input": f"Let's discuss {topic}. This is message {i} in our extended conversation.",
                "config_path": "config/basic_test.yaml",
                "thread_id": thread_id
            }
        )
        
        if response.ok and response.json().get("success"):
            result = response.json()['response']
            conversation_summary.append(f"Topic {i}: {topic}")
            print(f"   ✅ Response length: {len(result)} characters")
        else:
            print(f"   ❌ Message {i} failed")
            return False
        
        time.sleep(0.3)  # Brief pause between messages
    
    # Test recall of early conversation topics
    print(f"\nStep 2: Testing recall across {len(topics)} messages...")
    response_recall = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What were the first three topics we discussed in our conversation?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response_recall.ok or not response_recall.json().get("success"):
        print("❌ Recall test failed")
        return False
        
    recall_result = response_recall.json()['response']
    print(f"✅ Recall response: {recall_result}")
    
    # Check if early topics are recalled
    early_topics = ["artificial intelligence", "climate change", "space exploration"]
    topics_recalled = sum(1 for topic in early_topics 
                         if any(word in recall_result.lower() for word in topic.split()))
    
    print(f"   Early topics recalled: {topics_recalled}/{len(early_topics)}")
    
    success = topics_recalled >= 2  # At least 2 out of 3 early topics
    print(f"\n🎯 Memory Scalability Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Total messages processed: {len(topics) + 1}")
    print(f"   Thread ID: {thread_id}")
    
    return success

def main():
    """Run all ChromaDB memory tests."""
    print("🧠 ChromaDB Memory System Testing Suite")
    print("=" * 70)
    
    # Check if server is running
    try:
        health = requests.get("http://localhost:8000/health")
        if not health.ok:
            print("❌ API server is not responding")
            return 1
    except:
        print("❌ Cannot connect to API server on localhost:8000")
        return 1
    
    print("✅ API server is running")
    print()
    
    # Run all ChromaDB tests
    tests = [
        ("ChromaDB Initialization", test_chromadb_initialization),
        ("Multi-Turn Conversation", test_multi_turn_conversation),
        ("Concurrent Thread Management", test_concurrent_threads),
        ("Memory Persistence", test_memory_persistence_across_restarts),
        ("Memory Scalability", test_memory_scalability),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
        
        print("\n" + "=" * 70)
    
    # Summary
    print("\n📊 CHROMADB MEMORY TEST SUMMARY")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall ChromaDB Test Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All ChromaDB memory tests passed! ChromaDB system is working perfectly.")
        return 0
    else:
        print("⚠️ Some ChromaDB tests failed. Check the memory system configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())