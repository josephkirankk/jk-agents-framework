# PepGenX System Prompt Recommendations

Based on testing with "What is 2+2?", here are the best system prompts for different use cases.

## 🎯 For Direct Answers

### **Best Choice: System Prompt 0 (No System Prompt)**
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 0 --user-prompt "What is 2+2?"
```
**Response**: `2 + 2 = **4**`
- ✅ Most direct and concise
- ✅ No extra formatting or analysis
- ✅ Perfect for straightforward questions

### **Alternative: System Prompt 6 (Tool-Aware Assistant)**
```bash
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 6 --user-prompt "What is 2+2?"
```
**Response**: `The answer is simple: 2 + 2 = 4.`
- ✅ Very direct with minimal extra text
- ✅ Good for general Q&A

## 📊 Complete System Prompt Comparison

| System Prompt | Response | Directness | Best For |
|---------------|----------|------------|----------|
| **0** (None) 🎯 | `2 + 2 = **4**` | ⭐⭐⭐⭐⭐ | **Direct answers, math, facts** |
| **1** (Content Safety) | Safety analysis + answer | ⭐⭐ | Content moderation |
| **2** (Adobe Firefly) ⭐ | Image description | ❌ | Image generation |
| **3** (ESG Assistant) | Redirects to ESG topics | ❌ | PepsiCo ESG only |
| **4** (Prompt Generator) | Creates system prompt | ❌ | Meta-prompting |
| **5** (Prompt Enhancer) | Rephrases question | ❌ | Prompt improvement |
| **6** (Tool-Aware) | `The answer is simple: 2 + 2 = 4.` | ⭐⭐⭐⭐ | General Q&A |
| **7** (Adaptation Expert) | Adapts prompt format | ❌ | Cross-model adaptation |

## 💡 Usage Recommendations

### **For Math and Logic Questions**
```bash
# Best: No system prompt
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 0 --user-prompt "Calculate 15 * 23"

# Or use reasoning models (always direct)
python scripts/pepgenx_cli.py test --model o1-mini --user-prompt "Solve: If x + 5 = 12, what is x?"
```

### **For General Questions**
```bash
# Direct answers
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 0 --user-prompt "What is the capital of France?"

# Slightly more conversational
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 6 --user-prompt "What is the capital of France?"
```

### **For Creative Tasks**
```bash
# Image generation prompts
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 2 --user-prompt "A sunset over mountains"

# Writing enhancement
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 5 --user-prompt "Write a story about a robot"
```

### **For Business/Corporate Use**
```bash
# Content safety check
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 1 --user-prompt "Review this marketing copy"

# ESG-related questions
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 3 --user-prompt "What are our sustainability goals?"
```

## 🚀 Quick Reference Commands

```bash
# Show all system prompts
python scripts/pepgenx_cli.py prompts

# Direct answer mode (recommended for most questions)
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 0 --user-prompt "Your question here"

# Reasoning model (best for complex math/logic)
python scripts/pepgenx_cli.py test --model o1-mini --user-prompt "Your complex question here"

# General Q&A mode
python scripts/pepgenx_cli.py test --model gpt-4o --system-prompt 6 --user-prompt "Your question here"
```

## 🎯 Key Takeaways

1. **System Prompt 0** (No System Prompt) gives the most direct answers
2. **System Prompt 6** (Tool-Aware Assistant) is good for general Q&A
3. **Reasoning models** (o1-mini, o3, etc.) are best for complex math and logic
4. **System Prompt 2** (Adobe Firefly) is the default but optimized for image generation
5. Most other system prompts are specialized for specific tasks and may not give direct answers

## 🔧 CLI Updates

The CLI now supports:
- `--system-prompt 0` for no system prompt (direct response mode)
- Automatic reasoning model detection and endpoint routing
- Clear indicators for model types and system prompt usage

**Updated help text shows**: `use 0 for no system prompt` in the system-prompt argument description.
