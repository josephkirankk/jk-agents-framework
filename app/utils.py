from __future__ import annotations
import json, re
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
        m = re.search(r"(\{(?:[^{}]|(?R))*\})", s)
        if m:
            return m.group(1)
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
