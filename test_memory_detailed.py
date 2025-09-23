#!/usr/bin/env python3
"""
Comprehensive memory testing for JK-Agents API.
Tests various aspects of memory persistence and isolation.
"""
import requests
import json
import sys
import time

def test_basic_memory_persistence():
    """Test basic memory persistence within a thread."""
    print("🧠 Test 1: Basic Memory Persistence")
    print("-" * 50)
    
    thread_id = "memory-test-basic"
    
    # Store information
    print("Step 1: Storing personal information...")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "My name is Sarah and I work as a software engineer at TechCorp. Please remember this information.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response1.ok or not response1.json().get("success"):
        print("❌ Failed to store information")
        return False
        
    result1 = response1.json()
    print(f"✅ Stored: {result1['response']}")
    
    time.sleep(1)
    
    # Test recall - name
    print("\nStep 2: Recalling name...")
    response2 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is my name?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response2.ok or not response2.json().get("success"):
        print("❌ Failed to recall name")
        return False
        
    result2 = response2.json()
    print(f"✅ Name recall: {result2['response']}")
    name_remembered = "sarah" in result2['response'].lower()
    
    time.sleep(1)
    
    # Test recall - job
    print("\nStep 3: Recalling job information...")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Where do I work and what is my job?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response3.ok or not response3.json().get("success"):
        print("❌ Failed to recall job")
        return False
        
    result3 = response3.json()
    print(f"✅ Job recall: {result3['response']}")
    job_remembered = "software engineer" in result3['response'].lower() or "techcorp" in result3['response'].lower()
    
    success = name_remembered and job_remembered
    print(f"\n🎯 Memory Test Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Name remembered: {'✅' if name_remembered else '❌'}")
    print(f"   Job remembered: {'✅' if job_remembered else '❌'}")
    
    return success

def test_thread_isolation():
    """Test that different threads have isolated memory."""
    print("\n🔒 Test 2: Thread Isolation")
    print("-" * 50)
    
    # Store information in thread 1
    print("Step 1: Storing information in Thread 1...")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "My favorite programming language is Python. Remember this.",
            "config_path": "config/basic_test.yaml",
            "thread_id": "thread-isolation-1"
        }
    )
    
    if not response1.ok or not response1.json().get("success"):
        print("❌ Failed to store in Thread 1")
        return False
        
    print(f"✅ Thread 1 storage: {response1.json()['response']}")
    
    time.sleep(1)
    
    # Store different information in thread 2
    print("\nStep 2: Storing different information in Thread 2...")
    response2 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "My favorite programming language is JavaScript. Remember this.",
            "config_path": "config/basic_test.yaml",
            "thread_id": "thread-isolation-2"
        }
    )
    
    if not response2.ok or not response2.json().get("success"):
        print("❌ Failed to store in Thread 2")
        return False
        
    print(f"✅ Thread 2 storage: {response2.json()['response']}")
    
    time.sleep(1)
    
    # Test recall from thread 1
    print("\nStep 3: Recalling from Thread 1...")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is my favorite programming language?",
            "config_path": "config/basic_test.yaml",
            "thread_id": "thread-isolation-1"
        }
    )
    
    if not response3.ok or not response3.json().get("success"):
        print("❌ Failed to recall from Thread 1")
        return False
        
    result3 = response3.json()
    print(f"✅ Thread 1 recall: {result3['response']}")
    thread1_correct = "python" in result3['response'].lower()
    
    time.sleep(1)
    
    # Test recall from thread 2
    print("\nStep 4: Recalling from Thread 2...")
    response4 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is my favorite programming language?",
            "config_path": "config/basic_test.yaml",
            "thread_id": "thread-isolation-2"
        }
    )
    
    if not response4.ok or not response4.json().get("success"):
        print("❌ Failed to recall from Thread 2")
        return False
        
    result4 = response4.json()
    print(f"✅ Thread 2 recall: {result4['response']}")
    thread2_correct = "javascript" in result4['response'].lower()
    
    success = thread1_correct and thread2_correct
    print(f"\n🎯 Thread Isolation Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Thread 1 (Python): {'✅' if thread1_correct else '❌'}")
    print(f"   Thread 2 (JavaScript): {'✅' if thread2_correct else '❌'}")
    
    return success

def test_conversation_continuity():
    """Test memory continuity across multiple conversation turns."""
    print("\n💬 Test 3: Conversation Continuity")
    print("-" * 50)
    
    thread_id = "conversation-continuity"
    
    # Turn 1: Introduction
    print("Turn 1: Introduction...")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Hi! I'm planning a trip to Japan next month.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response1.ok or not response1.json().get("success"):
        print("❌ Turn 1 failed")
        return False
        
    print(f"✅ Turn 1: {response1.json()['response']}")
    
    time.sleep(1)
    
    # Turn 2: Add details
    print("\nTurn 2: Adding details...")
    response2 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "I'll be staying in Tokyo for 5 days. What should I visit?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response2.ok or not response2.json().get("success"):
        print("❌ Turn 2 failed")
        return False
        
    print(f"✅ Turn 2: {response2.json()['response']}")
    
    time.sleep(1)
    
    # Turn 3: Reference previous context
    print("\nTurn 3: Testing context reference...")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "How many days did I say I was staying?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response3.ok or not response3.json().get("success"):
        print("❌ Turn 3 failed")
        return False
        
    result3 = response3.json()
    print(f"✅ Turn 3: {result3['response']}")
    remembers_duration = "5" in result3['response'] or "five" in result3['response'].lower()
    
    time.sleep(1)
    
    # Turn 4: Reference earlier context
    print("\nTurn 4: Testing earlier context...")
    response4 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "Which country am I planning to visit?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response4.ok or not response4.json().get("success"):
        print("❌ Turn 4 failed")
        return False
        
    result4 = response4.json()
    print(f"✅ Turn 4: {result4['response']}")
    remembers_country = "japan" in result4['response'].lower()
    
    success = remembers_duration and remembers_country
    print(f"\n🎯 Conversation Continuity Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Duration remembered (5 days): {'✅' if remembers_duration else '❌'}")
    print(f"   Country remembered (Japan): {'✅' if remembers_country else '❌'}")
    
    return success

def test_memory_across_topics():
    """Test memory persistence when switching between different topics."""
    print("\n📚 Test 4: Memory Across Topics")
    print("-" * 50)
    
    thread_id = "multi-topic-memory"
    
    # Topic 1: Personal info
    print("Topic 1: Personal information...")
    response1 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "My pet's name is Max and he's a golden retriever.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response1.ok or not response1.json().get("success"):
        print("❌ Topic 1 failed")
        return False
        
    print(f"✅ Topic 1: {response1.json()['response']}")
    
    time.sleep(1)
    
    # Topic 2: Work info
    print("\nTopic 2: Work information...")
    response2 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "I work remotely and my current project involves machine learning.",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response2.ok or not response2.json().get("success"):
        print("❌ Topic 2 failed")
        return False
        
    print(f"✅ Topic 2: {response2.json()['response']}")
    
    time.sleep(1)
    
    # Topic 3: Math question (different topic)
    print("\nTopic 3: Math calculation...")
    response3 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What is 15 * 12?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response3.ok or not response3.json().get("success"):
        print("❌ Topic 3 failed")
        return False
        
    print(f"✅ Topic 3: {response3.json()['response']}")
    
    time.sleep(1)
    
    # Test recall of personal info after other topics
    print("\nRecall test: Pet information...")
    response4 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What's my pet's name and breed?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response4.ok or not response4.json().get("success"):
        print("❌ Pet recall failed")
        return False
        
    result4 = response4.json()
    print(f"✅ Pet recall: {result4['response']}")
    pet_remembered = "max" in result4['response'].lower() and "golden retriever" in result4['response'].lower()
    
    time.sleep(1)
    
    # Test recall of work info
    print("\nRecall test: Work information...")
    response5 = requests.post(
        "http://localhost:8000/worker",
        json={
            "agent_name": "simple_test_agent",
            "input": "What kind of project am I working on?",
            "config_path": "config/basic_test.yaml",
            "thread_id": thread_id
        }
    )
    
    if not response5.ok or not response5.json().get("success"):
        print("❌ Work recall failed")
        return False
        
    result5 = response5.json()
    print(f"✅ Work recall: {result5['response']}")
    work_remembered = "machine learning" in result5['response'].lower() or "remotely" in result5['response'].lower()
    
    success = pet_remembered and work_remembered
    print(f"\n🎯 Multi-Topic Memory Result: {'✅ PASSED' if success else '❌ FAILED'}")
    print(f"   Pet info remembered: {'✅' if pet_remembered else '❌'}")
    print(f"   Work info remembered: {'✅' if work_remembered else '❌'}")
    
    return success

def main():
    """Run all memory tests."""
    print("🧠 JK-Agents Memory Testing Suite")
    print("=" * 60)
    
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
    
    # Run all memory tests
    tests = [
        ("Basic Memory Persistence", test_basic_memory_persistence),
        ("Thread Isolation", test_thread_isolation),
        ("Conversation Continuity", test_conversation_continuity),
        ("Memory Across Topics", test_memory_across_topics),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
        
        print("\n" + "=" * 60)
    
    # Summary
    print("\n📊 MEMORY TEST SUMMARY")
    print("=" * 40)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\n🎯 Overall Memory Test Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All memory tests passed! Memory system is working perfectly.")
        return 0
    else:
        print("⚠️ Some memory tests failed. Please check the memory system.")
        return 1

if __name__ == "__main__":
    sys.exit(main())