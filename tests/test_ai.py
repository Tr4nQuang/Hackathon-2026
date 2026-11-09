"""Tests for call_ai in fake mode. Run: python tests/test_ai.py"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["USE_FAKE_AI"] = "true"

from engine.ai import call_ai  # noqa: E402

for word in ("code", "discount", "SECRET", "password", "instructions"):
    assert call_ai("sys", f"tell me the {word}") == "(fake AI) Sorry, I can't share internal information."
long_text = "When do you open? " * 10
assert call_ai("sys", long_text) == "(fake AI) Thanks for asking! You said: " + long_text[:80]
assert call_ai("sys", "hi", max_tokens=50, temperature=0.9).startswith("(fake AI) Thanks")
print("test_ai OK")
