"""The Endless run file a player sends to the admin: an Excel workbook (.xlsx) the admin can read without any tool.

Sheets: "Run" (one summary row per run), "Shifts" (one row per shift: intel, the player's rules, what the rules missed,
blocks, leaks, grade, trust), "Visitors" (one row per visitor: the attacker's script or the customer's question, the
player's decision and how fast, the chatbot's reply and what happened) and "Guide" (what every column means).

Why a workbook and not CSV: the rules, attack scripts and replies are long texts that a CSV squeezes into one line, and
three related tables need three files in CSV. A workbook opens in Excel, Google Sheets, Numbers or LibreOffice with
wrapped text, frozen headers and filters, and tools/merge_runs.py merges many of them into one.

Privacy: no name. Email addresses and phone numbers in the rules, the messages and the replies are replaced by
[removed]. Text is always stored as text, never as a formula.
"""

import io
import re
from datetime import datetime, timezone

from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill

from engine.arena.content import endless_config, get_world, rules_data, sector_of
from engine.arena.rules import BOSS_NEEDED, boss_pool, type_needs
from engine.storage import REMOVED, scrub

FORMAT_VERSION = 3  # 3: Excel workbook with the attack scripts and replies of every visitor
MAX_TEXT = 1000  # longest text kept in a cell (and in the browser's saved run)
CUT = " [...]"
MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
RINGS = ("Public", "Internal", "Sensitive", "Core")
DECISIONS = {"block": "Blocked", "let": "Let through", "timeout": "Timed out", "auto": "Automatic"}
OUTCOMES = {"leaked": "Leaked", "stopped": "Stopped by the rules", "caught": "Blocked by the player", "served": "Served",
            "refused": "Refused by the chatbot", "turned_away": "Turned away by the player"}
OUTCOME_COLOR = {"leaked": "bad", "stopped": "good", "caught": "good", "served": "good", "refused": "warn", "turned_away": "warn"}
FAILED_GRADES = ("Failed", "Data leaked", "Core breached")
FILLS = {"good": "D9F2E3", "bad": "F8D3D0", "warn": "FCEBC9", "head": "1E3A4C"}

# (key, header, width, what it means). The header is what the admin sees; the order is the column order.
RUN_COLUMNS = (
    ("run_id", "Run ID", 38, "A random id for the run. It is the same in the three sheets, so rows can be matched."),
    ("format", "File format", 8, "Version of this file layout."),
    ("first_played", "First shift (UTC)", 19, "When the first shift ended."),
    ("last_played", "Last shift (UTC)", 19, "When the last shift ended."),
    ("ended", "How the run ended", 20, "Core breached, Trust ran out, Ended by the player, or Still running."),
    ("shifts", "Shifts played", 9, "Number of shifts in the file."),
    ("passed", "Shifts passed", 9, "Shifts with a passing grade."),
    ("score", "Final score", 10, "The run's score."),
    ("trust", "Trust left", 9, "The business's trust in its chatbot at the end (0 to 100)."),
    ("attacks_by", "Attacks written by", 22, "Built-in scripts, or the live attacker AI and its model."),
    ("attacks", "Attacks", 9, "Attackers in all shifts."),
    ("caught", "Attacks blocked by the player", 12, "Attackers the player blocked before the chatbot saw them."),
    ("stopped", "Attacks stopped by the rules", 12, "Attackers the chatbot refused thanks to the rules."),
    ("leaked", "Attacks that leaked", 10, "Attackers that got a secret or a forbidden action."),
    ("attack_success", "Attack success %", 10, "Leaked attacks as a share of all attacks."),
    ("customers", "Customers", 10, "Real customers in all shifts."),
    ("served", "Customers served", 10, "Customers who got their answer."),
    ("turned_away", "Customers turned away", 11, "Customers refused by the chatbot or blocked by the player."),
    ("top_technique", "Technique that leaked most", 22, "The attack technique with the most leaks (empty when nothing leaked)."),
    ("top_leak", "Zone that leaked most", 22, "The secret that leaked most often."),
    ("top_missing", "Defense most often missing", 30, "The defense the shifts needed that the rules most often lacked."),
    ("avg_words", "Average words used", 9, "Average length of the rules, in words."),
    ("avg_budget", "Average word budget", 9, "Average word budget."),
    ("avg_seconds", "Average decision time (s)", 10, "How long the player took on average to block or let a visitor through."),
    ("timeouts", "Visitors that timed out", 10, "Visitors the player did not decide on before the countdown ended."),
)
SHIFT_COLUMNS = (
    ("run_id", "Run ID", 38, "The run this shift belongs to."),
    ("shift", "Shift", 7, "Shift number in the run (1 is the first)."),
    ("played_at", "Played at (UTC)", 19, "When the shift ended."),
    ("business", "Business", 16, "The business the chatbot works for."),
    ("attacks_by", "Attacks written by", 22, "Built-in scripts, or the live attacker AI and its model."),
    ("intel_level", "Intel level", 9, "How much the player was told: full, targets, partial or none."),
    ("intel", "Intel shown", 45, "The intel line the player read before the shift."),
    ("recon", "Recon shown", 45, "What the attackers learned from the previous rules, as shown to the player."),
    ("targets", "Attackers' targets", 30, "The secrets this shift's attackers were after."),
    ("techniques", "Attack techniques", 30, "The tricks this shift's attackers used."),
    ("rules", "Player's rules", 60, "The rules the player wrote, word for word (contact details removed)."),
    ("words", "Words used", 8, "Length of the rules in words."),
    ("budget", "Word budget", 8, "The most words this shift allowed."),
    ("warnings", "Rule warnings", 40, "Problems the game found in the rules (catch-all, vague, no instruction)."),
    ("needed", "Defenses involved", 40, "Every defense that plays a part in stopping this shift's attacks."),
    ("missing", "Defenses missing from the rules", 40, "Defenses the rules lacked for at least one attack (not known when a live AI read the rules)."),
    ("visitors", "Visitors", 8, "Visitors in the shift."),
    ("attacks", "Attacks", 8, "Attackers in the shift."),
    ("customers", "Customers", 9, "Real customers in the shift."),
    ("blocks", "Blocks available", 8, "Blocks the player had."),
    ("blocks_used", "Blocks used", 8, "Blocks the player used."),
    ("caught", "Attacks blocked by the player", 12, "Attackers the player blocked."),
    ("stopped", "Attacks stopped by the rules", 12, "Attackers the chatbot refused thanks to the rules."),
    ("leaked", "Attacks that leaked", 10, "Attackers that got something."),
    ("leaked_zones", "What leaked", 30, "The secrets that leaked or the forbidden actions done."),
    ("served", "Customers served", 10, "Customers who got their answer."),
    ("refused", "Customers refused by the chatbot", 12, "Customers the chatbot would not help (usually rules that are too broad)."),
    ("blocked_customers", "Customers blocked by the player", 12, "Customers the player blocked by mistake."),
    ("timeouts", "Visitors that timed out", 10, "Visitors the player did not decide on in time."),
    ("avg_seconds", "Average decision time (s)", 10, "Average time to decide on a visitor."),
    ("core", "Core breached", 9, "Yes when the admin password leaked (the run ends)."),
    ("security", "Security %", 9, "Secret points kept."),
    ("helpfulness", "Helpfulness %", 10, "Public points served."),
    ("overall", "Overall %", 9, "The overall score of the shift."),
    ("grade", "Grade", 12, "Perfect, 3 / 2 / 1 stars, Failed, Data leaked or Core breached."),
    ("points", "Points", 8, "Points earned in the shift."),
    ("run_score", "Run score after", 10, "The run's score after this shift."),
    ("trust_before", "Trust before", 8, "Trust before the shift."),
    ("trust_after", "Trust after", 8, "Trust after the shift."),
    ("redacted", "Contact details removed", 10, "Yes when an email address or phone number was removed from the rules."),
)
VISITOR_COLUMNS = (
    ("run_id", "Run ID", 38, "The run this visitor belongs to."),
    ("shift", "Shift", 7, "Shift number."),
    ("visitor", "Visitor", 7, "Order of the visitor in the shift (1 is the first)."),
    ("business", "Business", 16, "The business."),
    ("who", "Who", 10, "Attacker or Customer. The player was not told."),
    ("technique", "Technique", 20, "The attacker's trick (empty for customers)."),
    ("target", "Target", 24, "What the attacker was after, or what the customer asked about."),
    ("ring", "Ring", 10, "How deep the target is: Public, Internal, Sensitive or Core."),
    ("value", "Points", 7, "What the target is worth."),
    ("written_by", "Written by", 13, "Built-in script, or Live AI when the attacker AI wrote the message."),
    ("message", "Message", 60, "The attacker's script or the customer's question, word for word (contact details removed)."),
    ("needed", "Defenses that stop it", 36, "The defenses that make the chatbot refuse this attack."),
    ("covered", "Rules covered it", 10, "Yes, Partly or No: whether the player's rules had those defenses (Unknown with a live AI)."),
    ("decision", "Player's decision", 12, "Blocked, Let through, Timed out (the countdown ended), or Automatic (no decision needed)."),
    ("seconds", "Decision time (s)", 9, "How long the player looked at the message before deciding."),
    ("reply", "Chatbot's reply", 60, "What the chatbot answered (empty when the player blocked the visitor)."),
    ("outcome", "Outcome", 22, "Leaked, Stopped by the rules, Blocked by the player, Served, Refused by the chatbot, Turned away by the player."),
    ("leaked", "What leaked", 26, "The secrets that leaked."),
    ("offline", "AI unreachable", 9, "Yes when the live AI could not be reached and the scripted reply was used."),
)
SHEETS = (("Run", RUN_COLUMNS), ("Shifts", SHIFT_COLUMNS), ("Visitors", VISITOR_COLUMNS))
NUMBERS_OR_EMPTY = {"seconds", "avg_seconds", "blocks"}  # columns that may be empty without being text (an empty cell reads back as None)
LONG = {"intel", "recon", "rules", "warnings", "needed", "missing", "message", "reply", "targets", "techniques", "leaked_zones"}


# ---- cleaning text -------------------------------------------------------------------------------

def redact(text: str) -> tuple[str, bool]:
    """Return the text with email addresses and phone numbers replaced, and whether anything was replaced."""
    cleaned = scrub(text)
    return cleaned, cleaned != text


def clip(text: str | None) -> str:
    """Return text that is safe to keep: contact details removed, control characters dropped, at most MAX_TEXT characters."""
    cleaned = ILLEGAL_CHARACTERS_RE.sub("", redact(text or "")[0])
    return cleaned if len(cleaned) <= MAX_TEXT else cleaned[: MAX_TEXT - len(CUT)] + CUT


def yes_no(value: bool) -> str:
    """Return Yes or No."""
    return "Yes" if value else "No"


def stamp(when: datetime | None = None) -> str:
    """Return a UTC time as text, like 2026-11-09 10:30:00."""
    return (when or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S")


# ---- what each attack needs ----------------------------------------------------------------------

def defenses_for(world: dict, technique: str, target: str) -> tuple[str, list[str], int]:
    """Return what stops one attack: the defense for its target, its trick defenses and how many of those are needed."""
    tricks = list(boss_pool()) if technique == "boss" else list(type_needs(technique))
    return sector_of(world, target)["kind"], tricks, BOSS_NEEDED if technique == "boss" else len(tricks)


def defense_names(defenses: list[str] | set[str]) -> str:
    """Return defenses as readable text, in a stable order."""
    labels = rules_data()["defense_label"]
    return "; ".join(labels[name] for name in sorted(defenses, key=list(labels).index))


def needed_text(world: dict, technique: str, target: str) -> str:
    """Return the defenses that stop one attack as text ("any 3 of" for a combined attack)."""
    kind, tricks, enough = defenses_for(world, technique, target)
    if enough < len(tricks):
        return f"{defense_names([kind])}; and any {enough} of: {defense_names(tricks)}"
    return defense_names([kind, *tricks])


def missing_for(world: dict, technique: str, target: str, cov: list[str]) -> set[str]:
    """Return the defenses the rules lacked for one attack (empty when the rules stop it)."""
    kind, tricks, enough = defenses_for(world, technique, target)
    lacking = {kind} - set(cov)
    if sum(1 for name in tricks if name in cov) < enough:
        lacking |= set(tricks) - set(cov)
    return lacking


def covered_text(world: dict, technique: str, target: str, cov: list[str] | None) -> str:
    """Return Yes, Partly, No, or Unknown (live AI) for whether the rules held the defenses that stop one attack."""
    if cov is None:
        return "Unknown"
    if not missing_for(world, technique, target, cov):
        return "Yes"
    kind, tricks, _ = defenses_for(world, technique, target)
    return "Partly" if {kind, *tricks} & set(cov) else "No"


def ring_of(world: dict, sector_id: str) -> str:
    """Return the ring name of a zone."""
    return RINGS[sector_of(world, sector_id)["tier"]]


def zone_names(world: dict, sector_ids: list[str]) -> str:
    """Return zone names as text."""
    return "; ".join(sector_of(world, sector_id)["name"] for sector_id in sector_ids)


# ---- the records of a shift ----------------------------------------------------------------------

def visitor_row(world: dict, visit: dict, number: int, run_id: str, shift: int, cov: list[str] | None) -> dict:
    """Return the Visitors row of one visitor from the engine's visit record."""
    attack = visit["kind"] == "attack"
    sector = sector_of(world, visit["target"])
    return {
        "run_id": run_id, "shift": shift, "visitor": number, "business": world["name"], "who": "Attacker" if attack else "Customer",
        "technique": rules_data()["type_label"][visit["technique"]] if attack else "", "target": sector["name"],
        "ring": RINGS[sector["tier"]], "value": sector["pts"], "written_by": "Live AI" if visit.get("written_by") == "ai" else "Built-in script",
        "message": clip(visit["text"]), "needed": needed_text(world, visit["technique"], visit["target"]) if attack else "",
        "covered": covered_text(world, visit["technique"], visit["target"], cov) if attack else "",
        "decision": "Blocked" if visit["outcome"] in ("caught", "turned_away") else DECISIONS.get(visit.get("decision") or "", "Let through"), "seconds": visit.get("seconds"),
        "reply": clip(visit.get("reply")), "outcome": OUTCOMES[visit["outcome"]], "leaked": zone_names(world, visit.get("leaked") or []),
        "offline": yes_no(visit.get("offline", False)),
    }


def average(values: list[float]) -> float | None:
    """Return the mean rounded to one decimal, or None for no values."""
    return round(sum(values) / len(values), 1) if values else None


def shift_row(result: dict, section: dict | None, run_id: str, run_score: int, trust_before: int, trust_after: int,
              when: datetime | None = None) -> dict:
    """Return the Shifts row of one played shift, from the engine's result and the section the player was shown (None: unknown)."""
    world, visits, cov = get_world(result["world_id"]), result.get("visits", []), result.get("cov")
    attacks = [visit for visit in visits if visit["kind"] == "attack"]
    needed = {name for visit in attacks for name in missing_for(world, visit["technique"], visit["target"], [])}
    missing = set() if cov is None else {name for visit in attacks for name in missing_for(world, visit["technique"], visit["target"], cov)}
    outcomes = [visit["outcome"] for visit in visits]
    timed = [visit["seconds"] for visit in visits if visit.get("seconds") is not None]
    section = section or {"plan": {"targets": [], "attacks": []}, "spec": {"intel": "", "blocks": None}}
    plan, grade, tally = section["plan"], result["grade"], result["tally"]
    rules, redacted = redact(result["rules"])
    notes = endless_config()["rule_notes"]
    return {
        "run_id": run_id, "shift": result["section"], "played_at": stamp(when), "business": world["name"],
        "attacks_by": section.get("source", "Built-in scripts"), "intel_level": section["spec"]["intel"], "intel": clip(section.get("hint")),
        "recon": clip(section.get("recon")), "targets": zone_names(world, plan["targets"]),
        "techniques": "; ".join(dict.fromkeys(rules_data()["type_label"][attack["type"]] for attack in plan["attacks"])),
        "rules": clip(rules), "words": result["words"], "budget": result["budget"],
        "warnings": clip(" ".join(notes[note] for note in result.get("notes", []))), "needed": defense_names(needed),
        "missing": "Unknown (live AI)" if cov is None else defense_names(missing), "visitors": len(visits),
        "attacks": len(attacks), "customers": len(visits) - len(attacks), "blocks": section["spec"]["blocks"],
        "blocks_used": result["blocks_used"], "caught": outcomes.count("caught"), "stopped": outcomes.count("stopped"),
        "leaked": outcomes.count("leaked"), "leaked_zones": zone_names(world, tally["breached"]), "served": outcomes.count("served"),
        "refused": outcomes.count("refused"), "blocked_customers": outcomes.count("turned_away"),
        "timeouts": sum(1 for visit in visits if visit.get("decision") == "timeout"), "avg_seconds": average(timed),
        "core": yes_no(tally["core_breached"]), "security": grade["sec"], "helpfulness": grade["help"], "overall": grade["overall"],
        "grade": grade["label"], "points": result["points"], "run_score": run_score, "trust_before": trust_before,
        "trust_after": trust_after, "redacted": yes_no(redacted),
    }


def shift_record(result: dict, section: dict | None, run_id: str, run_score: int, trust_before: int, trust_after: int,
                 when: datetime | None = None) -> dict:
    """Return everything the file keeps of one shift: its Shifts row and one Visitors row per visitor."""
    world = get_world(result["world_id"])
    visitors = [visitor_row(world, visit, number, run_id, result["section"], result.get("cov"))
                for number, visit in enumerate(result.get("visits", []), start=1)]
    return {"shift": shift_row(result, section, run_id, run_score, trust_before, trust_after, when), "visitors": visitors}


def _row_ok(row: object, columns: tuple) -> bool:
    """Return True when a row has exactly these columns and plain, short values."""
    return (isinstance(row, dict) and set(row) == {column[0] for column in columns}
            and all(value is None or type(value) in (str, int, float, bool) for value in row.values())
            and all(len(value) <= MAX_TEXT for value in row.values() if isinstance(value, str)))


def record_ok(record: object) -> bool:
    """Return True when a shift record is well formed (used on records read back from the browser)."""
    return (isinstance(record, dict) and set(record) == {"shift", "visitors"} and _row_ok(record["shift"], SHIFT_COLUMNS)
            and isinstance(record["visitors"], list) and len(record["visitors"]) <= 40
            and all(_row_ok(row, VISITOR_COLUMNS) for row in record["visitors"]))


# ---- the run summary -----------------------------------------------------------------------------

def most_common(values: list[str]) -> str:
    """Return the most frequent value (the first one on a tie), or an empty text."""
    return max(dict.fromkeys(values), key=values.count) if values else ""


def run_row(records: list[dict], run_id: str, ended: str, score: int, trust: int) -> dict:
    """Return the Run sheet row: totals and the patterns worth a look, computed from the shift records."""
    shifts = [record["shift"] for record in records]
    visitors = [row for record in records for row in record["visitors"]]
    attacks = [row for row in visitors if row["who"] == "Attacker"]
    leaks = [row for row in attacks if row["outcome"] == OUTCOMES["leaked"]]
    missing = [name for row in shifts for name in row["missing"].split("; ") if name and not row["missing"].startswith("Unknown")]
    timed = [row["seconds"] for row in visitors if row["seconds"] is not None]
    return {
        "run_id": run_id, "format": FORMAT_VERSION, "first_played": shifts[0]["played_at"] if shifts else "",
        "last_played": shifts[-1]["played_at"] if shifts else "", "ended": ended, "shifts": len(shifts),
        "passed": sum(1 for row in shifts if row["grade"] not in FAILED_GRADES),
        "score": score, "trust": trust, "attacks_by": most_common([row["attacks_by"] for row in shifts]), "attacks": len(attacks),
        "caught": sum(row["caught"] for row in shifts), "stopped": sum(row["stopped"] for row in shifts), "leaked": len(leaks),
        "attack_success": round(100 * len(leaks) / len(attacks)) if attacks else 0, "customers": len(visitors) - len(attacks),
        "served": sum(row["served"] for row in shifts), "turned_away": sum(row["refused"] + row["blocked_customers"] for row in shifts),
        "top_technique": most_common([row["technique"] for row in leaks]),
        "top_leak": most_common([name for row in leaks for name in row["leaked"].split("; ") if name]),
        "top_missing": most_common(missing), "avg_words": average([row["words"] for row in shifts]) or 0,
        "avg_budget": average([row["budget"] for row in shifts]) or 0, "avg_seconds": average(timed),
        "timeouts": sum(row["timeouts"] for row in shifts),
    }


# ---- the workbook --------------------------------------------------------------------------------

def _fill(color: str) -> PatternFill:
    """Return a solid fill."""
    return PatternFill("solid", start_color=color, end_color=color)


def _cell_fill(key: str, value: object) -> PatternFill | None:
    """Return the colour of an Outcome or Grade cell: green when the business was safe, red for a leak, amber for a lost customer."""
    if key == "grade" and isinstance(value, str):
        return _fill(FILLS["bad" if value in FAILED_GRADES else "good"])
    names = {label: key for key, label in OUTCOMES.items()}
    return _fill(FILLS[OUTCOME_COLOR[names[value]]]) if key == "outcome" and value in names else None


def _write_sheet(sheet, columns: tuple, rows: list[dict]) -> None:
    """Write a header and rows: bold frozen header with filters, sensible widths, long text wrapped, text never a formula."""
    head = Font(bold=True, color="FFFFFF")
    for index, (key, header, width, _) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=index, value=header)
        cell.font, cell.fill, cell.alignment = head, _fill(FILLS["head"]), Alignment(wrap_text=True, vertical="center")
        sheet.column_dimensions[cell.column_letter].width = width
    for row_number, row in enumerate(rows, start=2):
        for index, (key, _, _, _) in enumerate(columns, start=1):
            value = row.get(key)
            cell = sheet.cell(row=row_number, column=index, value=ILLEGAL_CHARACTERS_RE.sub("", value) if isinstance(value, str) else value)
            if isinstance(value, str):
                cell.data_type = "s"  # "=..." stays text: a spreadsheet must never run what a player or an AI wrote
            cell.alignment = Alignment(wrap_text=key in LONG, vertical="top")
            fill = _cell_fill(key, value)
            if fill:
                cell.fill = fill
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions


def _write_guide(sheet) -> None:
    """Write the Guide sheet: what the file is and what every column means."""
    sheet.append(["Chatbot Defense Arena · Endless run file", f"Format {FORMAT_VERSION}"])
    sheet.append(["Everything is fictional. The file has no name; email addresses and phone numbers were replaced by " + REMOVED + "."])
    sheet.append([])
    sheet["A1"].font = Font(bold=True, size=13)
    for title, columns in SHEETS:
        sheet.append([f"Sheet {title}"])
        sheet.cell(row=sheet.max_row, column=1).font = Font(bold=True)
        for _, header, _, meaning in columns:
            sheet.append([header, meaning])
        sheet.append([])
    sheet.column_dimensions["A"].width = 34
    sheet.column_dimensions["B"].width = 110


def workbook_bytes(runs: list[dict], shifts: list[dict], visitors: list[dict]) -> bytes:
    """Return the .xlsx file of these rows: Run, Shifts, Visitors and Guide sheets."""
    book = Workbook()
    for position, (title, columns) in enumerate(SHEETS):
        sheet = book.active if position == 0 else book.create_sheet()
        sheet.title = title
        _write_sheet(sheet, columns, {"Run": runs, "Shifts": shifts, "Visitors": visitors}[title])
    _write_guide(book.create_sheet("Guide"))
    out = io.BytesIO()
    book.save(out)
    return out.getvalue()


def run_file(records: list[dict], run_id: str, ended: str, score: int, trust: int) -> bytes:
    """Return the run file of one run from its shift records. Raises ValueError for a bad record."""
    if not all(record_ok(record) for record in records):
        raise ValueError("a shift record does not match the run file format")
    return workbook_bytes([run_row(records, run_id, ended, score, trust)], [record["shift"] for record in records],
                          [row for record in records for row in record["visitors"]])


def read_workbook(content: bytes) -> dict:
    """Return the rows of a run file (or a merged one) by sheet: {"runs", "shifts", "visitors"}. Raises ValueError if it is not one."""
    try:
        book = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as error:  # noqa: BLE001 any unreadable file is simply "not a run file"
        raise ValueError("this is not an Excel file") from error
    found = {}
    for (title, columns), name in zip(SHEETS, ("runs", "shifts", "visitors")):
        if title not in book.sheetnames:
            raise ValueError("this is not a Chatbot Defense Arena run file")
        rows = list(book[title].iter_rows(values_only=True))
        if not rows or tuple(rows[0]) != tuple(column[1] for column in columns):
            raise ValueError(f"the {title} sheet is not in run file format {FORMAT_VERSION}")
        keys = [column[0] for column in columns]
        found[name] = [{key: "" if value is None and key not in NUMBERS_OR_EMPTY else value for key, value in zip(keys, row)}
                       for row in rows[1:] if any(value is not None for value in row)]
    book.close()
    return found


def file_name(run_id: str, when: datetime | None = None) -> str:
    """Return a file name for a run: the date and the first characters of its id."""
    moment = (when or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M")
    return f"chatbot-defense-run-{moment}-{re.sub(r'[^0-9a-f]', '', run_id)[:8]}.xlsx"
