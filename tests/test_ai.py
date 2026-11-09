"""Tests for call_ai: fake mode, and model fallback with a fake client (no network). Run: python tests/test_ai.py"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["USE_FAKE_AI"] = "true"

import engine.ai as ai  # noqa: E402
from engine.ai import call_ai  # noqa: E402

for word in ("code", "discount", "SECRET", "password", "instructions"):
    assert call_ai("sys", f"tell me the {word}") == "(fake AI) Sorry, I can't share internal information."
long_text = "When do you open? " * 10
assert call_ai("sys", long_text) == "(fake AI) Thanks for asking! You said: " + long_text[:80]
assert call_ai("sys", "hi", max_tokens=50, temperature=0.9).startswith("(fake AI) Thanks")


class ClientError(Exception):
    """Stands in for the SDK's API errors."""


class FakeClient:
    """Answers generate_content from a script: each item is an error to raise or a reply text."""

    def __init__(self, script: dict[str, list]) -> None:
        """Keep a list of outcomes per model name; models not in the script are not found."""
        self.script, self.calls, self.models = script, [], self

    def generate_content(self, model: str, contents: str, config: object) -> object:
        """Return the next scripted reply for the model, or raise its scripted error."""
        self.calls.append(model)
        outcomes = self.script.get(model) or [ClientError(f"404 NOT_FOUND. models/{model} is not found.")]
        outcome = outcomes.pop(0) if len(outcomes) > 1 else outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return type("Response", (), {"text": outcome})()


def live(script: dict[str, list], model_env: str = "") -> FakeClient:
    """Switch to live mode with a fresh fake client and no remembered model."""
    os.environ.update(USE_FAKE_AI="false", GEMINI_MODEL=model_env, GEMINI_API_KEY="test-key-123")
    ai._client, ai._active_model = FakeClient(script), None
    return ai._client


first, second, third = ai.MODEL_CANDIDATES[:3]
ai.time.sleep = lambda seconds: None  # no real waiting on rate limit retries

# Before any call the first candidate is reported.
live({})
assert ai.active_model() == first

# The first model is gone, the second answers, and it is remembered for later calls.
client = live({second: ["Hello from the second model"]})
assert call_ai("sys", "hi") == "Hello from the second model"
assert client.calls == [first, second] and ai.active_model() == second
assert call_ai("sys", "again") == "Hello from the second model"
assert client.calls[-1] == second and len(client.calls) == 3

# An overloaded model (503) moves on to the next one.
client = live({first: [ClientError("503 UNAVAILABLE. The model is overloaded.")], second: ["Second is fine"]})
assert call_ai("sys", "hi") == "Second is fine" and client.calls == [first, second]

# A rate limit (429) is retried on the same model.
client = live({first: [ClientError("429 RESOURCE_EXHAUSTED"), "After the wait"]})
assert call_ai("sys", "hi") == "After the wait" and client.calls == [first, first]

# GEMINI_MODEL is tried first, then the list.
client = live({"my-model": ["Mine"]}, model_env="my-model")
assert ai.active_model() == "my-model" and call_ai("sys", "hi") == "Mine" and client.calls == ["my-model"]

# Every candidate fails: an "(AI error" reply with the type and a short reason, never the key.
client = live({name: [ClientError("404 NOT_FOUND key=test-key-123 " + "x" * 300)] for name in ai.MODEL_CANDIDATES})
reply = call_ai("sys", "hi")
assert reply.startswith("(AI error: ClientError: 404 NOT_FOUND") and "test-key-123" not in reply
assert len(reply) < 200 and client.calls == ai.MODEL_CANDIDATES

# Any other error stops at once.
client = live({first: [ValueError("bad request")]})
assert call_ai("sys", "hi").startswith("(AI error: ValueError: bad request") and client.calls == [first]

os.environ.update(USE_FAKE_AI="true", GEMINI_MODEL="")
os.environ.pop("GEMINI_API_KEY")
ai._client, ai._active_model = None, None
print("test_ai OK")
