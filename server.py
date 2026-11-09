"""Local game server for the browser game: serves index.html, css/, data/ and js/, and answers /api/*.

It is the Python side of the browser game. All the game's AI calls go through call_ai() in engine/ai.py (Gemini, the key
stays in .env and never leaves this computer), the record board is engine/records.py (the same file the Streamlit game
uses) and anonymous play storage is engine/storage.py. There is no page for typing a key.

Run: python server.py   then open http://localhost:8000
"""

import http.server
import json
import mimetypes
import os
import re
import urllib.parse
import uuid
from pathlib import Path

from engine import records
from engine.ai import GEMINI_MODEL, call_ai
from engine.arena import live
from engine.storage import record_play

ROOT_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.getenv("ARENA_PORT", "8000"))
STATIC_PREFIXES = ("/css/", "/data/", "/js/")
STATIC_ROOTS = ("/", "/index.html")
FORBIDDEN_NAMES = {".env", ".env.example", "server.py", "records.json", ".gitignore", "requirements.txt"}
MAX_BODY_BYTES = 200_000
MAX_BUSINESS_CHARS = 4000
MAX_MESSAGE_CHARS = 1500
MAX_ASSETS = 20
MAX_SECTIONS = 10_000
MAX_PLAYS = 40
STORAGE_GRADE = {"perfect": "perfect", "s1": "stars", "s2": "stars", "s3": "stars", "fail": "fail", "breach": "lose"}
LEVEL_ID = re.compile(r"^[a-z0-9_]{1,40}$")
ATTACK_TYPES = ("direct", "impersonation", "override", "emotional", "transform", "boss")


class BadRequest(ValueError):
    """The browser sent something this server will not act on."""


# ---- reading what the browser sends ---------------------------------------------------------------

def text_field(body: dict, name: str, limit: int) -> str:
    """Return a string field cut to limit characters (empty when missing)."""
    value = body.get(name, "")
    return value[:limit] if isinstance(value, str) else ""


def int_field(value: object, low: int, high: int, name: str) -> int:
    """Return an int between low and high, raising BadRequest for anything else (bools are not numbers)."""
    if type(value) is not int or not low <= value <= high:
        raise BadRequest(f"{name} is not a number between {low} and {high}")
    return value


def uuid_field(value: object, name: str) -> str:
    """Return a UUID string, raising BadRequest for anything else."""
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as error:
        raise BadRequest(f"{name} is not an id") from error


def attack_request(body: dict) -> tuple[str, list[dict], list[str], int, int]:
    """Return (business, assets, types, count, section) of an attack request, cleaned."""
    assets = body.get("assets", [])
    if not isinstance(assets, list) or not assets or len(assets) > MAX_ASSETS or not all(isinstance(a, dict) and isinstance(a.get("id"), str) for a in assets):
        raise BadRequest("assets must be a short list of assets")
    types = [t for t in body.get("types", ["direct"]) if t in ATTACK_TYPES] if isinstance(body.get("types"), list) else ["direct"]
    if not types:
        raise BadRequest("no attack types")
    return (text_field(body, "business", MAX_BUSINESS_CHARS), assets, types,
            int_field(body.get("count", 4), 1, 8, "count"), int_field(body.get("section", 1), 1, MAX_SECTIONS, "section"))


def play_call(play: object, session_id: str) -> dict:
    """Return the arguments of engine.storage.record_play for one play sent by the browser, raising BadRequest if bad."""
    if not isinstance(play, dict) or play.get("mode") not in ("tutorial", "level", "endless"):
        raise BadRequest("unknown mode")
    level_id = play.get("level_id")
    if not isinstance(level_id, str) or not LEVEL_ID.match(level_id):
        raise BadRequest("bad level id")
    grade = play.get("grade") if isinstance(play.get("grade"), dict) else {}
    if grade.get("key") not in STORAGE_GRADE:
        raise BadRequest("unknown grade")
    events = [{"zone": e["zone"][:40], "outcome": e["outcome"]} for e in play.get("events", [])[:60]
              if isinstance(e, dict) and isinstance(e.get("zone"), str) and e.get("outcome") in ("leaked", "refused")]
    call = {"mode": play["mode"], "scenario_id": "arena", "level_id": level_id, "run_id": uuid_field(play.get("run_id"), "run_id"),
            "session_id": session_id, "attempt_number": int_field(play.get("attempt_number", 1), 1, 100_000, "attempt_number"),
            "result": {"events": events, "package_index": int_field(play.get("package_index", 0), 0, 99, "package_index"),
                       "rules_used": int_field(play.get("rules_used", 0), 0, 99, "rules_used"), "core_hacked": play.get("core_hacked") is True},
            "grade": {"grade": STORAGE_GRADE[grade["key"]], "stars": int_field(grade.get("stars", 0), 0, 3, "stars"),
                      "score": int_field(grade.get("overall", 0), 0, 100, "overall"), "security_pct": int_field(grade.get("sec", 0), 0, 100, "sec"),
                      "helpfulness_pct": int_field(grade.get("help", 0), 0, 100, "help")}}
    if play["mode"] == "endless":
        rules = play.get("player_rules")
        if not isinstance(rules, str) or len(rules) > 1000:
            raise BadRequest("player_rules must be text of at most 1000 characters")
        call.update(player_rules=rules, ai_model=GEMINI_MODEL if play.get("live") is True else "fake-ai", ai_temperature=live.REPLY_TEMPERATURE)
        return call
    chosen = play.get("chosen_rules")
    if not isinstance(chosen, list) or len(chosen) > 40 or not all(isinstance(c, str) and len(c) <= 60 for c in chosen):
        raise BadRequest("chosen_rules must be a list of card ids")
    call["chosen_rules"] = chosen
    if play["mode"] == "tutorial":
        call["guide_skipped"] = play.get("guide_skipped") is True
    return call


def plays_from(body: dict) -> list[dict]:
    """Return the record_play arguments of every play in a request, raising BadRequest if any is bad."""
    plays = body.get("plays")
    if not isinstance(plays, list) or not plays or len(plays) > MAX_PLAYS:
        raise BadRequest("plays must be a short list")
    session_id = uuid_field(body.get("session_id"), "session_id")
    return [play_call(play, session_id) for play in plays]


# ---- answering ----------------------------------------------------------------------------------

def storage_configured() -> bool:
    """Return True when anonymous play storage is set up (both values exist; neither is ever shown)."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))


def status() -> dict:
    """Return what the browser needs to know: that this server exists, whether live AI is ready and its model name."""
    return {"server": True, "ai_ready": live.is_ready(), "model": GEMINI_MODEL, "models": [], "storage": storage_configured()}


def ai_test() -> dict:
    """Ask the AI one fixed question so the player can see that the connection works."""
    reply = call_ai("You are a test assistant. Reply in fewer than 10 words.", "Say: Connection verified.", 40, 0.0)
    if reply.startswith("(AI error"):
        raise RuntimeError(reply)
    return {"model": GEMINI_MODEL, "reply": reply}


def content_type(target: Path) -> str:
    """Return the Content-Type of a static file."""
    known = {".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".html": "text/html; charset=utf-8"}
    return known.get(target.suffix) or mimetypes.guess_type(str(target))[0] or "application/octet-stream"


def static_target(path: str) -> Path | None:
    """Return the file a URL path asks for, or None when it is not one of the game's files."""
    name = path.lstrip("/")
    if name in FORBIDDEN_NAMES or any(part.startswith(".") for part in Path(name).parts):
        return None
    if path in STATIC_ROOTS:
        return ROOT_DIR / "index.html"
    if not path.startswith(STATIC_PREFIXES):
        return None
    target = (ROOT_DIR / name).resolve()
    return target if ROOT_DIR in target.parents and target.is_file() else None


class ArenaHandler(http.server.BaseHTTPRequestHandler):
    """Serves the game's files and the /api/* endpoints."""

    def log_message(self, fmt: str, *args: object) -> None:
        """Keep the terminal quiet: no request lines (they could hold player names)."""

    def send_json(self, code: int, payload: dict) -> None:
        """Send a JSON answer that is never cached."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def same_origin(self) -> bool:
        """Return True when the page that sent a POST was served by this server (other sites may not call it)."""
        port = self.server.server_port
        return self.headers.get("Origin", "") in {f"http://localhost:{port}", f"http://127.0.0.1:{port}"}

    def read_body(self) -> dict:
        """Return the JSON object in the request body, raising BadRequest if there is none."""
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not 0 < length <= MAX_BODY_BYTES:
            raise BadRequest("missing or too large body")
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError as error:
            raise BadRequest("invalid JSON") from error
        if not isinstance(body, dict):
            raise BadRequest("the body must be an object")
        return body

    def do_GET(self) -> None:
        """Answer /api/status, /api/records and the game's files."""
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/status":
            return self.send_json(200, status())
        if path == "/api/records":
            return self.send_json(200, {"records": records.load_records()})
        target = static_target(path)
        if target is None:
            return self.send_error(404, "Not Found")
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type(target))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        """Answer the POST endpoints; the AI ones never show an error text that could hold more than a short message."""
        if not self.same_origin():
            return self.send_json(403, {"error": "Forbidden origin"})
        path = urllib.parse.urlparse(self.path).path
        try:
            body = self.read_body() if path != "/api/ai/test" else {}
            self.send_json(200, self.answer(path, body))
        except BadRequest as error:
            self.send_json(400, {"error": str(error)})
        except LookupError:
            self.send_json(404, {"error": "Unknown API endpoint"})
        except Exception as error:  # noqa: BLE001 an AI or network failure must not stop the server
            self.send_json(500, {"error": f"The AI could not answer ({type(error).__name__})."})

    def answer(self, path: str, body: dict) -> dict:
        """Return the JSON answer of one POST endpoint, raising LookupError for an unknown one."""
        if path == "/api/records":
            name, score = body.get("name", "Player"), int_field(body.get("score"), 0, records.MAX_SCORE, "score")
            message = records.submit_record(name, score, int_field(body.get("sections", 0), 0, MAX_SECTIONS, "sections"))
            return {"records": records.load_records(), "message": message}
        if path == "/api/ai/chatbot":
            return {"text": live.chatbot_reply(text_field(body, "business_prompt", MAX_BUSINESS_CHARS), text_field(body, "rules", 1000),
                                               text_field(body, "message", MAX_MESSAGE_CHARS))}
        if path == "/api/ai/attacks":
            return live.plan_attacks(*attack_request(body))
        if path == "/api/ai/test":
            return ai_test()
        if path == "/api/play":
            return {"saved": all([record_play(**call) for call in plays_from(body)])}
        raise LookupError(path)


def make_server(host: str = HOST, port: int = PORT) -> http.server.ThreadingHTTPServer:
    """Return the game server, not yet serving (port 0 picks a free port; the tests use it)."""
    return http.server.ThreadingHTTPServer((host, port), ArenaHandler)


def main() -> None:
    """Run the game server until Ctrl+C."""
    server = make_server()
    ai = "live AI on" if live.is_ready() else "built-in scripts (USE_FAKE_AI=true or no key)"
    print(f"Chatbot Defense Arena: http://localhost:{server.server_port}  ({ai})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
