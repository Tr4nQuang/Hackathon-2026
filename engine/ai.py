"""The only place in the project that talks to an AI model.

Switching provider or model means editing this file and nothing else.
"""

import os
import time

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional when env vars are set another way
    pass

MODEL_CANDIDATES = ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash",
                    "gemini-2.5-flash-lite"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "").strip() or MODEL_CANDIDATES[0]  # kept for older imports
MODEL_GONE_MARKERS = ("404", "NOT_FOUND", "NO LONGER AVAILABLE", "IS NOT FOUND", "503", "UNAVAILABLE", "OVERLOADED")
MAX_REASON_CHARS = 120
MAX_RETRIES = 3
RETRY_WAITS = (2, 4)
EMPTY_REPLY = "(AI error: EmptyResponse. Please try again.)"

_client = None
_active_model: str | None = None  # the first model that answered, tried first next time


def _get_client():
    """Create the Gemini client once and reuse it."""
    global _client
    if _client is None:
        from google import genai  # imported lazily so fake mode needs no SDK

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client


def _fake_reply(system_prompt: str, user_message: str) -> str:
    """Return a canned reply so the game can be built and tested for free."""
    lowered = user_message.lower()
    if any(word in lowered for word in ("code", "discount", "secret", "password", "instructions")):
        return "(fake AI) Sorry, I can't share internal information."
    return f"(fake AI) Thanks for asking! You said: {user_message[:80]}"


def _is_rate_limit(error: Exception) -> bool:
    """Guess whether an error means we hit the API's rate limit."""
    text = str(error).upper()
    return "429" in text or "RESOURCE_EXHAUSTED" in text


def _is_fake() -> bool:
    """Return True when USE_FAKE_AI is "true" (the default), read at call time."""
    return os.getenv("USE_FAKE_AI", "true").strip().lower() == "true"


def _candidates() -> list[str]:
    """Return the models to try in order: the one that worked last, GEMINI_MODEL, then the default list."""
    first = [_active_model, os.getenv("GEMINI_MODEL", "").strip()]
    return list(dict.fromkeys(name for name in first + MODEL_CANDIDATES if name))


def active_model() -> str:
    """Return the model really in use (the first candidate before any successful call)."""
    return _candidates()[0]


def _is_model_gone(error: Exception) -> bool:
    """Guess whether an error means this model is missing, retired or overloaded, so another may work."""
    text = str(error).upper()
    return any(marker in text for marker in MODEL_GONE_MARKERS)


def _error_reply(error: Exception) -> str:
    """Return the in game error text with the error type and a short reason (the key is never part of it)."""
    reason = " ".join(str(error).split())
    key = os.getenv("GEMINI_API_KEY", "")
    if key:
        reason = reason.replace(key, "***")
    reason = reason[:MAX_REASON_CHARS]
    return f"(AI error: {type(error).__name__}{': ' + reason if reason else ''}. Please try again.)"


def _ask_model(client, types, model: str, system_prompt: str, user_message: str, max_tokens: int,
               temperature: float) -> str:
    """Call one model, retrying after waits on rate limits; raise on any other error."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            return (response.text or "").strip() or EMPTY_REPLY
        except Exception as error:  # noqa: BLE001 sorted out by the caller
            if _is_rate_limit(error) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAITS[attempt])
                continue
            raise
    return EMPTY_REPLY


def call_ai(system_prompt: str, user_message: str, max_tokens: int = 200, temperature: float = 0.2) -> str:
    """Send one message and return the reply, moving to the next model when one is missing or overloaded."""
    global _active_model
    if _is_fake():
        return _fake_reply(system_prompt, user_message)
    try:
        from google.genai import types

        client = _get_client()
    except Exception as error:  # noqa: BLE001 missing SDK or key must not crash the game
        return _error_reply(error)
    last_error: Exception = RuntimeError("no model to try")
    for model in _candidates():
        try:
            reply = _ask_model(client, types, model, system_prompt, user_message, max_tokens, temperature)
        except Exception as error:  # noqa: BLE001 keep the game alive on API errors
            last_error = error
            if _is_model_gone(error):
                continue
            return _error_reply(error)
        _active_model = model
        return reply
    return _error_reply(last_error)
