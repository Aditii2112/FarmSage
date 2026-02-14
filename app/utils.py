from __future__ import annotations
import json
from typing import Any, Dict

def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Best-effort JSON parse. If the model returns extra text,
    try to extract first {...} block.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # Try to extract a JSON object region
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise
