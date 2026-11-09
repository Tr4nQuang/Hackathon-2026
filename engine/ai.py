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

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
MAX_RETRIES = 3
RETRY_WAITS = (2, 4)
EMPTY_REPLY = "(AI error: EmptyResponse. Please try again.)"

_client = None


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


def call_ai(system_prompt: str, user_message: str, max_tokens: int = 200, temperature: float = 0.2) -> str:
    """Send one message to the model and return its text reply, retrying on rate limits."""
    if _is_fake():
        return _fake_reply(system_prompt, user_message)
    try:
        from google.genai import types

        client = _get_client()
    except Exception as error:  # noqa: BLE001 missing SDK or key must not crash the game
        return f"(AI error: {type(error).__name__}. Please try again.)"
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", GEMINI_MODEL),
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            text = (response.text or "").strip()
            return text or EMPTY_REPLY
        except Exception as error:  # noqa: BLE001 keep the game alive on API errors
            if _is_rate_limit(error) and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_WAITS[attempt])
                continue
            return f"(AI error: {type(error).__name__}. Please try again.)"
    return EMPTY_REPLY
