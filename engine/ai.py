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

USE_FAKE_AI = os.getenv("USE_FAKE_AI", "true").strip().lower() == "true"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
MAX_RETRIES = 3

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
    return "429" in text or "RESOURCE_EXHAUSTED" in text or "RATE" in text


def call_ai(system_prompt: str, user_message: str, max_tokens: int = 200) -> str:
    """Send one message to the model and return its text reply.

    Retries with a growing wait when the free tier rate limit is hit,
    so a demo does not crash halfway through a round.
    """
    if USE_FAKE_AI:
        return _fake_reply(system_prompt, user_message)

    from google.genai import types

    client = _get_client()
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                ),
            )
            return response.text or ""
        except Exception as error:  # noqa: BLE001 keep the game alive on API errors
            if _is_rate_limit(error) and attempt < MAX_RETRIES - 1:
                time.sleep(2 * (attempt + 1))
                continue
            return f"(AI error: {type(error).__name__}. Please try again.)"
    return "(AI error: too many requests. Please wait a moment.)"
