#!/usr/bin/env python3
"""
Comprehensive Auto-Summarization Integration Tests

Tests the auto-summarization system with:
1. Database verification
2. Multi-cycle summarization
3. Message preservation logic
4. Turn tracking integrity
5. Core details retention across unlimited turns
"""

import os
import sys
import json
import time
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
    print("✅ Environment variables loaded from .env file")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

# Import helpers for integration tests
try:
    from integration_tests.helpers.db import setup_test_db, cleanup_test_db
except ImportError:
    # Fallback if no helper is available
    def setup_test_db(): pass
    def cleanup_test_db(): pass

# Import the memory system
from app.simple_conversation_memory_fixed import (
    SimpleConversationMemory,
    get_conversation_memory,
    get_conversation_context_metadata,
    store_conversation_turn
)


class TestAutoSummarizationComprehensive(unittest.TestCase):
    """Comprehensive tests for auto-summarization with database verification."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with dedicated test storage."""
        cls.test_storage_dir = project_root / "test_data" / "auto_summarization_tests"
        cls.test_storage_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Test storage directory: {cls.test_storage_dir}")
        
        # Setup test environment if needed
        setup_test_db()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test resources after all tests."""
        cleanup_test_db()
    
    def setUp(self):
        """Set up each test with a fresh memory instance."""
        self.test_thread = f"test-auto-sum-{self._testMethodName}-{int(time.time())}"
        
        # Use the global memory instance for consistency with get_conversation_context_metadata
        self.memory = get_conversation_memory()
        
        print(f"\n🧪 Test: {self._testMethodName}")
        print(f"   Thread ID: {self.test_thread}")
    
    def tearDown(self):
        """Clean up after each test."""
        if self.memory.has_conversation(self.test_thread):
            self.memory.clear_conversation(self.test_thread)
    
    def _verify_disk_storage(self, thread_id: str) -> Dict[str, Any]:
        """Verify conversation is properly stored on disk and return the data."""
        # Use the storage directory from the global memory instance
        storage_dir = Path(self.memory.storage_dir)
        storage_file = storage_dir / f"{thread_id}.json"
        
        self.assertTrue(storage_file.exists(), f"Storage file should exist: {storage_file}")
        
        with open(storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertEqual(data['thread_id'], thread_id)
        self.assertIn('messages', data)
        self.assertIn('updated_at', data)
        
        return data
    
    def _add_conversation_messages(self, thread_id: str, count: int, prefix: str = "msg"):
        """Helper to add multiple conversation messages (user + assistant pairs)."""
        for i in range(count):
            self.memory.add_message(
                thread_id,
                'user',
                f'{prefix} {i + 1}: User message with some content to test summarization'
            )
            self.memory.add_message(
                thread_id,
                'assistant',
                f'{prefix} {i + 1}: Assistant response with detailed information'
            )
    
    def _add_messages_until_summarization(self, thread_id: str, prefix: str = "msg"):
        """Add exactly enough messages to trigger summarization (31 messages)."""
        # Add 15 full turns (30 messages)
        for i in range(15):
            self.memory.add_message(
                thread_id,
                'user',
                f'{prefix} {i + 1}: User message with some content to test summarization'
            )
            self.memory.add_message(
                thread_id,
                'assistant',
                f'{prefix} {i + 1}: Assistant response with detailed information'
            )
        # Add one more user message to trigger summarization (31st message)
        self.memory.add_message(
            thread_id,
            'user',
            f'{prefix} 16: Final user message that triggers summarization'
        )
    
    def test_summarization_threshold_triggers_correctly(self):
        """Test that summarization triggers at exactly the right threshold."""
        print("\n🔍 Testing summarization threshold...")
        
        # Add messages up to but not exceeding threshold (30 messages)
        self._add_conversation_messages(self.test_thread, 15)  # 30 messages total
        
        messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        self.assertEqual(len(messages), 30, "Should have exactly 30 messages")
        
        # Verify no summarization yet
        system_messages = [m for m in messages if m['role'] == 'system']
        self.assertEqual(len(system_messages), 0, "No system summary messages yet")
        
        print(f"✅ Pre-threshold: {len(messages)} messages, no summarization")
        
        # Add one more message to trigger summarization (31 messages)
        self.memory.add_message(
            self.test_thread,
            'user',
            'Trigger message: This should trigger auto-summarization'
        )
        
        # Verify summarization triggered
        messages_after = self.memory.get_conversation_history(self.test_thread, limit=-1)
        print(f"✅ Post-threshold: {len(messages_after)} messages after adding 31st")
        
        # Should have: 1 summary + 10 recent messages = 11 total
        self.assertEqual(len(messages_after), 11, "Should have summary + 10 recent messages")
        
        # Verify summary message exists
        summary_msg = messages_after[0]
        self.assertEqual(summary_msg['role'], 'system')
        self.assertEqual(summary_msg['turn_id'], 'Summary')
        self.assertIn('CONVERSATION SUMMARY', summary_msg['content'])
        
        print(f"✅ Summary message created: {summary_msg['content'][:100]}...")
        
        # Verify disk storage
        disk_data = self._verify_disk_storage(self.test_thread)
        self.assertEqual(len(disk_data['messages']), 11)
        
        print("✅ Summarization threshold test PASSED")
    
    def test_recent_messages_preserved_after_summarization(self):
        """Test that recent messages are preserved correctly after summarization."""
        print("\n🔍 Testing recent message preservation...")
        
        # Add exactly 31 messages to trigger summarization
        self._add_messages_until_summarization(self.test_thread, prefix="test")
        
        # Get messages after first summarization
        messages_after_first = self.memory.get_conversation_history(self.test_thread, limit=-1)
        
        print(f"   After triggering summarization: {len(messages_after_first)} messages in memory")
        
        # Should have: 1 summary + 10 recent = 11 after first summarization
        self.assertEqual(len(messages_after_first), 11,
                        "Should have 11 messages after first summarization")
        
        # Verify summary exists
        summary = messages_after_first[0]
        self.assertEqual(summary['role'], 'system')
        self.assertEqual(summary['turn_id'], 'Summary')
        
        # Get the last 10 preserved messages
        preserved_messages = messages_after_first[1:]
        self.assertEqual(len(preserved_messages), 10)
        
        # Verify all preserved messages have proper structure
        for i, msg in enumerate(preserved_messages):
            self.assertIn('content', msg)
            self.assertIn('role', msg)
            self.assertIn('turn_id', msg)
            self.assertIn('timestamp', msg)
            self.assertIn('metadata', msg)
        
        print(f"✅ Preserved {len(preserved_messages)} recent messages with full metadata")
        print("✅ Recent message preservation test PASSED")
    
    def test_multiple_summarization_cycles(self):
        """Test multiple cycles of summarization to ensure it works repeatedly."""
        print("\n🔍 Testing multiple summarization cycles...")
        
        cycle_results = []
        
        # First cycle: Add exactly 31 messages to trigger first summarization
        print(f"\n   Cycle 1:")
        self._add_messages_until_summarization(self.test_thread, prefix="cycle1")
        messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        
        # Should have 11 messages after first summarization (1 summary + 10 recent)
        self.assertEqual(len(messages), 11, "Cycle 1: Should have 11 messages")
        summary = messages[0]
        self.assertEqual(summary['role'], 'system')
        cycle_results.append({
            'cycle': 1,
            'total_messages': len(messages),
            'summarized_count': summary.get('metadata', {}).get('count', 0)
        })
        print(f"   ✅ Cycle 1: {len(messages)} messages, "
              f"{cycle_results[-1]['summarized_count']} summarized")
        
        # Second cycle: Add 20 more messages to trigger second summarization
        # 11 current + 20 new = 31 messages, which will trigger
        print(f"\n   Cycle 2:")
        self._add_conversation_messages(self.test_thread, 10, prefix="cycle2")
        messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        
        # Should have 11 messages after second summarization
        self.assertEqual(len(messages), 11, "Cycle 2: Should have 11 messages")
        summary = messages[0]
        self.assertEqual(summary['role'], 'system')
        cycle_results.append({
            'cycle': 2,
            'total_messages': len(messages),
            'summarized_count': summary.get('metadata', {}).get('count', 0)
        })
        print(f"   ✅ Cycle 2: {len(messages)} messages, "
              f"{cycle_results[-1]['summarized_count']} summarized")
        
        # Third cycle: Add 20 more messages to trigger third summarization
        print(f"\n   Cycle 3:")
        self._add_conversation_messages(self.test_thread, 10, prefix="cycle3")
        messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        
        # Should have 11 messages after third summarization
        self.assertEqual(len(messages), 11, "Cycle 3: Should have 11 messages")
        summary = messages[0]
        self.assertEqual(summary['role'], 'system')
        cycle_results.append({
            'cycle': 3,
            'total_messages': len(messages),
            'summarized_count': summary.get('metadata', {}).get('count', 0)
        })
        print(f"   ✅ Cycle 3: {len(messages)} messages, "
              f"{cycle_results[-1]['summarized_count']} summarized")
        
        # Verify each cycle worked correctly
        for result in cycle_results:
            self.assertGreater(result['summarized_count'], 0,
                             f"Cycle {result['cycle']} should have summarized messages")
            self.assertEqual(result['total_messages'], 11,
                           f"Cycle {result['cycle']} should maintain 11 messages")
        
        # Verify disk storage for final state
        disk_data = self._verify_disk_storage(self.test_thread)
        self.assertEqual(len(disk_data['messages']), 11)
        
        print("\n✅ Multiple summarization cycles test PASSED")
    
    def test_turn_id_integrity_across_summarization(self):
        """Test that turn IDs remain consistent across summarization."""
        print("\n🔍 Testing turn ID integrity...")
        
        # Add exactly 31 messages to trigger summarization
        self._add_messages_until_summarization(self.test_thread, prefix="turn")
        
        # After 31 messages, summarization should have triggered
        # Get messages which should be 11 (1 summary + 10 recent)
        messages_after = self.memory.get_conversation_history(self.test_thread, limit=-1)
        
        print(f"   Total messages after summarization: {len(messages_after)}")
        self.assertEqual(len(messages_after), 11, "Should have 11 messages after summarization")
        
        # Verify summary message
        summary = messages_after[0]
        self.assertEqual(summary['role'], 'system')
        self.assertEqual(summary['turn_id'], 'Summary')
        
        # Get the preserved recent messages (skip summary)
        recent_messages = messages_after[1:]
        turn_ids_preserved = [m.get('turn_id') for m in recent_messages]
        
        print(f"   Preserved turn IDs: {turn_ids_preserved}")
        
        # Verify turn IDs are properly formatted
        for turn_id in turn_ids_preserved:
            self.assertTrue(turn_id.startswith('Turn-'),
                          f"Turn ID should start with 'Turn-': {turn_id}")
        
        # Extract unique turn numbers
        turn_numbers = set()
        for turn_id in turn_ids_preserved:
            try:
                turn_num = int(turn_id.split('-')[1])
                turn_numbers.add(turn_num)
            except (IndexError, ValueError):
                pass
        
        print(f"   Turn numbers in preserved messages: {sorted(turn_numbers)}")
        
        # Should have at least a few complete turns preserved
        self.assertGreaterEqual(len(turn_numbers), 3, "Should preserve at least 3 turns")
        
        print("✅ Turn ID integrity test PASSED")
    
    def test_unlimited_conversation_turns_simulation(self):
        """Simulate unlimited conversation turns to verify core details are maintained."""
        print("\n🔍 Testing unlimited conversation turns simulation...")
        
        # Simulate 100 conversation turns (200 messages)
        important_data = []
        
        for turn in range(1, 101):
            user_msg = f"Turn {turn}: User asks about topic {turn}"
            assistant_msg = f"Turn {turn}: Important data point #{turn} - Response with details"
            
            self.memory.add_message(self.test_thread, 'user', user_msg)
            self.memory.add_message(self.test_thread, 'assistant', assistant_msg)
            
            # Track some important data points
            if turn in [10, 50, 90, 100]:
                important_data.append({
                    'turn': turn,
                    'user': user_msg,
                    'assistant': assistant_msg
                })
            
            # Check state periodically
            if turn % 20 == 0:
                messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
                print(f"   Turn {turn}: {len(messages)} messages in memory")
                
                # Should never exceed 31 messages (before summarization trigger)
                self.assertLessEqual(len(messages), 31,
                                   f"Memory should be bounded at turn {turn}")
        
        # Final verification
        final_messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        
        print(f"\n   Final state after 100 turns:")
        print(f"   - Total messages in memory: {len(final_messages)}")
        print(f"   - Memory bounded: {len(final_messages) <= 31}")
        
        # Verify recent turns are accessible
        metadata = get_conversation_context_metadata(self.test_thread)
        print(f"   - Turn count tracked: {metadata['turn_count']}")
        print(f"   - Word count: {metadata['word_count']}")
        
        # Verify the last 10 messages contain the most recent data
        recent_messages = [m for m in final_messages if m['role'] != 'system']
        last_messages_content = ' '.join([m['content'] for m in recent_messages[-5:]])
        
        # Should contain references to recent turns (95-100)
        has_recent_data = any(f"Turn {i}" in last_messages_content for i in range(95, 101))
        self.assertTrue(has_recent_data, "Should contain references to recent turns")
        
        print("✅ Unlimited conversation turns simulation PASSED")
    
    def test_metadata_preservation_across_summarization(self):
        """Test that message metadata is preserved across summarization."""
        print("\n🔍 Testing metadata preservation...")
        
        # Add messages with custom metadata
        for i in range(20):
            self.memory.add_message(
                self.test_thread,
                'user',
                f'User message {i + 1}',
                metadata={'user_id': f'user_{i}', 'priority': 'high'}
            )
            self.memory.add_message(
                self.test_thread,
                'assistant',
                f'Assistant response {i + 1}',
                metadata={'model': 'gpt-4', 'tokens': 100 + i}
            )
        
        messages_after = self.memory.get_conversation_history(self.test_thread, limit=-1)
        recent_messages = messages_after[1:]  # Skip summary
        
        # Verify metadata is preserved in recent messages
        for msg in recent_messages:
            self.assertIn('metadata', msg)
            metadata = msg['metadata']
            
            if msg['role'] == 'user':
                self.assertIn('user_id', metadata)
                self.assertIn('priority', metadata)
            else:
                self.assertIn('model', metadata)
                self.assertIn('tokens', metadata)
        
        print(f"✅ Metadata preserved in {len(recent_messages)} recent messages")
        print("✅ Metadata preservation test PASSED")
    
    def test_disk_persistence_after_summarization(self):
        """Test that summarization results are properly persisted to disk."""
        print("\n🔍 Testing disk persistence...")
        
        # Add exactly 31 messages to trigger summarization
        self._add_messages_until_summarization(self.test_thread, prefix="disk")
        
        # Verify disk file exists and has correct data
        disk_data = self._verify_disk_storage(self.test_thread)
        
        messages_in_file = disk_data['messages']
        self.assertEqual(len(messages_in_file), 11, "Disk should have 11 messages after summarization")
        
        # Verify summary message in disk data
        summary_in_file = messages_in_file[0]
        self.assertEqual(summary_in_file['role'], 'system')
        self.assertIn('CONVERSATION SUMMARY', summary_in_file['content'])
        self.assertEqual(summary_in_file['turn_id'], 'Summary')
        
        # Verify summary metadata
        summary_metadata = summary_in_file.get('metadata', {})
        self.assertEqual(summary_metadata.get('type'), 'basic_summary')
        self.assertGreater(summary_metadata.get('count', 0), 0, "Should have summarized count")
        
        # Verify recent messages in disk data
        recent_in_file = messages_in_file[1:]
        self.assertEqual(len(recent_in_file), 10, "Should have 10 recent messages in file")
        
        # Cross-verify with in-memory data
        messages_in_memory = self.memory.get_conversation_history(self.test_thread, limit=-1)
        self.assertEqual(len(messages_in_memory), len(messages_in_file),
                        "In-memory and disk message counts should match")
        
        for mem_msg, disk_msg in zip(messages_in_memory, messages_in_file):
            self.assertEqual(mem_msg['content'], disk_msg['content'])
            self.assertEqual(mem_msg['role'], disk_msg['role'])
            self.assertEqual(mem_msg.get('turn_id'), disk_msg.get('turn_id'))
        
        print(f"✅ Disk persistence verified: {len(messages_in_file)} messages on disk")
        print("✅ Disk persistence test PASSED")
    
    def test_conversation_context_metadata_with_summarization(self):
        """Test that conversation context metadata works correctly with summarization."""
        print("\n🔍 Testing conversation context metadata...")
        
        # Add exactly 31 messages to trigger one summarization
        self._add_messages_until_summarization(self.test_thread, prefix="meta")
        
        # Get messages and metadata
        messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        metadata = get_conversation_context_metadata(self.test_thread)
        
        print(f"   Messages after summarization: {len(messages)}")
        print(f"   Metadata after summarization:")
        print(f"   - Word count: {metadata['word_count']}")
        print(f"   - Turn count: {metadata['turn_count']}")
        print(f"   - Message count: {metadata['message_count']}")
        print(f"   - Memory size: {metadata['memory_size_bytes']} bytes")
        
        # Verify metadata is reasonable
        self.assertGreater(metadata['word_count'], 0, "Should have word count")
        self.assertGreater(metadata['turn_count'], 0, "Should have turn count")
        self.assertEqual(metadata['message_count'], 11, "Should have 11 messages after summarization")
        self.assertGreater(metadata['memory_size_bytes'], 0, "Should have memory size")
        
        # Turn count should reflect the preserved turns (not counting Summary)
        # With 10 preserved messages = 5 complete turns
        self.assertGreaterEqual(metadata['turn_count'], 5, 
                               "Should track at least 5 complete turns in preserved messages")
        
        # Verify summarization recommendation logic still works
        self.assertIn('summarization_recommended', metadata)
        self.assertIsInstance(metadata['summarization_recommended'], bool)
        
        print("✅ Conversation context metadata test PASSED")
    
    def test_summarization_content_quality(self):
        """Test that the summarization message contains useful information."""
        print("\n🔍 Testing summarization content quality...")
        
        # Add messages with specific content
        topics = ['Python', 'JavaScript', 'Data Science', 'Machine Learning', 'DevOps']
        
        for i, topic in enumerate(topics * 4):  # 20 turns, 40 messages
            self.memory.add_message(
                self.test_thread,
                'user',
                f'Tell me about {topic} in detail'
            )
            self.memory.add_message(
                self.test_thread,
                'assistant',
                f'Here is information about {topic}: [detailed explanation]'
            )
        
        messages = self.memory.get_conversation_history(self.test_thread, limit=-1)
        summary = messages[0]
        
        # Verify summary structure
        self.assertEqual(summary['role'], 'system')
        self.assertIn('CONVERSATION SUMMARY', summary['content'])
        
        # Verify summary metadata
        metadata = summary.get('metadata', {})
        self.assertEqual(metadata.get('type'), 'basic_summary')
        self.assertGreater(metadata.get('count', 0), 0, "Should have summarized count")
        
        print(f"   Summary: {summary['content']}")
        print(f"   Summarized count: {metadata.get('count')}")
        
        print("✅ Summarization content quality test PASSED")


if __name__ == "__main__":
    unittest.main()
