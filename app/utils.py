from __future__ import annotations
import json
from typing import Optional
from pydantic import BaseModel, ValidationError

class SupervisorDecision(BaseModel):
    agent: str
    task: Optional[str] = None
    reason: Optional[str] = None

def extract_json_block(text: str) -> Optional[str]:
    if not text or not isinstance(text, str):
        return None
    s = text.strip()
    decoder = json.JSONDecoder()
    try:
        obj, idx = decoder.raw_decode(s)
        return s[:idx]
    except Exception:
        pass
    start = s.find("{")
    if start == -1:
        return None
    substring = s[start:]
    try:
        obj, idx = decoder.raw_decode(substring)
        return substring[:idx]
    except Exception:
        # Find balanced braces - simple approach for JSON objects
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(s):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    return s[start_idx:i+1]
    return None

def parse_supervisor_json(buf: str) -> Optional[SupervisorDecision]:
    try:
        block = extract_json_block(buf)
        if not block:
            return None
        data = json.loads(block)
        return SupervisorDecision(**data)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None
