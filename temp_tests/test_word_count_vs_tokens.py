#!/usr/bin/env python3
"""
Test to demonstrate the difference between conversation word count 
and current turn token usage.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.simple_conversation_memory_fixed import (
    get_conversation_memory,
    get_conversation_context_metadata
)


def test_word_count_vs_token_count():
    """
    Demonstrate that conversation word count (for summarization) 
    is different from current turn token count.
    """
    print("\n" + "="*70)
    print("WORD COUNT VS TOKEN COUNT - DEMONSTRATION")
    print("="*70)
    
    memory = get_conversation_memory()
    thread_id = "test-token-demo"
    
    # Simulate the user's conversation
    print("\n[Creating Conversation Similar to User's Log]")
    
    # Turn 1: Short exchange
    memory.add_message(thread_id, "user", "whats my name")
    memory.add_message(thread_id, "assistant", 
        "Your name is currently unknown in this session context. "
        "If you'd like me to address you by name, please provide it.")
    
    # Turn 2: Short exchange
    memory.add_message(thread_id, "user", "my namer is joseph")
    memory.add_message(thread_id, "assistant",
        "Thank you, Joseph! I've noted your name and will address you as Joseph "
        "in our future brainstorming sessions. If you have any specific AI use case "
        "ideas or questions, feel free to let me know—I'm here to help!")
    
    # Turn 3: User asks for research (short request)
    memory.add_message(thread_id, "user", "research on hyderabad news today")
    
    # Turn 3: System responds with LONG research (simulating web research output)
    long_research_response = """Certainly, Joseph! Here's a concise, prioritized summary of today's Hyderabad news (October 15, 2025) for quick review:

---

**Top Headlines – Hyderabad (Oct 15, 2025)**

1. **Traffic Enforcement Intensifies**
   - Hyderabad Traffic Police launched a city-wide crackdown on mobile phone use while driving
   - Over 80,000 cases booked this year; recent two-day drive resulted in 2,345 violations
   - Goal: Improve road safety and reduce accidents caused by distracted driving
   - Fines: ₹1,000 per violation, over ₹7.72 crore collected in 2025
   - Source: Telangana Today, The Hindu

2. **Water Supply Upgrade**
   - HMWSSB continues infrastructure upgrades
   - Pipeline expansions, smart water management systems
   - Improved water quality, availability, and drought resilience
   - Source: HMWSSB Official Site

3. **Real Estate Boom**
   - Luxury housing market sparks sustainability debate
   - Strong commercial and residential growth despite global uncertainty
   - Major IT companies (Foxconn, Cognizant, Kia) investing heavily
   - Source: Hindustan Times, Deccan Chronicle, Moneycontrol

4. **Tech Sector Expansion**
   - Hyderabad remains IT and electronics manufacturing hub
   - Government incentives supporting $500 billion electronics ecosystem by 2030
   - Source: Evertiq, Moneycontrol

5. **Cultural Events**
   - Diwali and Dhantrayodashi (Dhanteras) preparations underway
   - Scheduled for October 18-19, 2025
   - Boost to local tourism, hospitality, and traditional arts
   - Source: Telangana Tourism

---

Each headline is backed by credible sources from recent news coverage."""
    
    memory.add_message(thread_id, "assistant", long_research_response)
    
    # Get metadata
    metadata = get_conversation_context_metadata(thread_id)
    
    print(f"\n✅ Conversation Created: {metadata['message_count']} messages, {metadata['turn_count']} turns")
    
    # Calculate actual word count
    import re
    all_content = " ".join(msg['content'] for msg in memory.get_conversation_history(thread_id, limit=-1))
    actual_words = len(re.findall(r'\b\w+\b', all_content))
    
    print(f"\n📊 CONVERSATION METRICS:")
    print(f"   Word count (from metadata): {metadata['word_count']}")
    print(f"   Word count (manual calc): {actual_words}")
    print(f"   Turn count: {metadata['turn_count']}")
    print(f"   Message count: {metadata['message_count']}")
    print(f"   Summarization recommended: {metadata['summarization_recommended']}")
    
    # Estimate tokens for different components
    # Rough estimate: 1 word ≈ 1.3 tokens (English text)
    estimated_history_tokens = actual_words * 1.3
    
    print(f"\n💡 TOKEN ESTIMATE BREAKDOWN:")
    print(f"   Conversation history: ~{int(estimated_history_tokens)} tokens")
    print(f"   ")
    print(f"   If this was sent to an agent with:")
    print(f"   - Agent system prompt: ~2,500 tokens")
    print(f"   - Business context: ~500 tokens")
    print(f"   - Conversation history: ~{int(estimated_history_tokens)} tokens")
    print(f"   - Current request: ~50 tokens")
    print(f"   = Total input: ~{int(3050 + estimated_history_tokens)} tokens")
    print(f"   ")
    print(f"   If agent does web research:")
    print(f"   - Web search results: ~5,000-10,000 tokens")
    print(f"   - Agent response: ~1,500 tokens")
    print(f"   ")
    print(f"   If response passed to next agent (synthesizer):")
    print(f"   - Previous agent response: ~6,500-11,500 tokens")
    print(f"   - Synthesizer prompt: ~2,500 tokens")
    print(f"   - Business context: ~500 tokens")
    print(f"   - Conversation history: ~{int(estimated_history_tokens)} tokens")
    print(f"   = Synthesizer input: ~{int(9500 + estimated_history_tokens)} - ~{int(14500 + estimated_history_tokens)} tokens")
    print(f"   ")
    print(f"   TOTAL for both agents: ~13,000-18,000 tokens")
    print(f"   With multiple web searches: Can reach 20,000-25,000 tokens ✅")
    
    print(f"\n🎯 KEY INSIGHT:")
    print(f"   - Conversation history: {actual_words} words ({metadata['summarization_recommended']=})")
    print(f"   - Current turn tokens: 20,000+ (from web research + agent work)")
    print(f"   - These are DIFFERENT metrics!")
    print(f"   - Summarization triggers on HISTORY word count, not current turn tokens")
    
    print(f"\n✅ VERDICT:")
    if metadata['word_count'] < 2000:
        print(f"   Summarization correctly NOT triggered:")
        print(f"   {metadata['word_count']} words < 2000 threshold ✅")
    else:
        print(f"   Summarization should trigger:")
        print(f"   {metadata['word_count']} words > 2000 threshold")
    
    print(f"\n" + "="*70)
    
    # Cleanup
    if thread_id in memory.conversations:
        del memory.conversations[thread_id]


if __name__ == "__main__":
    test_word_count_vs_token_count()
