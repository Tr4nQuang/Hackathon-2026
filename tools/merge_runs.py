"""Admin tool: merge the Endless run files players sent into one CSV and print a short summary.

Usage:  python tools/merge_runs.py FOLDER_OR_FILES... [-o all_runs.csv]

Files that are not run files are skipped with a message. A section that appears in several files (the same player sent
a run twice) is kept once. Rows are sorted by time.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import export  # noqa: E402


def files_in(paths: list[str]) -> list[Path]:
    """Return the CSV files named, or found inside the folders named."""
    found: list[Path] = []
    for name in paths:
        path = Path(name)
        found += sorted(path.glob("*.csv")) if path.is_dir() else [path]
    return found


def typed(row: dict) -> dict:
    """Return a row read from a file with its numbers and booleans turned back into numbers and booleans."""
    ints = ("format", "section", "points", "security_pct", "helpfulness_pct", "overall_pct", "words", "rules_chars", "leaks",
            "customers_turned_away", "secret_points_kept", "secret_points_at_stake", "public_points_served", "public_points_asked", "run_score_after")
    out = {name: (int(row[name]) if name in ints else row[name]) for name in export.COLUMNS}
    for name in ("rules_redacted", "core_breached"):
        out[name] = row[name] == "True"
    return out


def merge(paths: list[str]) -> tuple[list[dict], list[str]]:
    """Return (merged rows, messages about skipped files)."""
    seen: set[tuple[str, int]] = set()
    rows: list[dict] = []
    notes: list[str] = []
    for path in files_in(paths):
        try:
            for row in map(typed, export.read_rows(path.read_text(encoding="utf-8"))):
                key = (row["run_id"], row["section"])
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
        except (OSError, ValueError, KeyError) as error:
            notes.append(f"skipped {path}: {error}")
    return sorted(rows, key=lambda row: (row["played_at"], row["run_id"], row["section"])), notes


def summary(rows: list[dict]) -> str:
    """Return a few lines about the merged rows."""
    runs = {row["run_id"] for row in rows}
    players = {row["session_id"] for row in rows}
    passed = sum(1 for row in rows if row["grade"] not in ("fail", "breach"))
    best = max((row["run_score_after"] for row in rows), default=0)
    return f"{len(rows)} sections in {len(runs)} runs from {len(players)} sessions; {passed} sections passed; best run score {best}."


def main() -> int:
    """Merge the files named on the command line and write the result."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="+", help="run files or folders of run files")
    parser.add_argument("-o", "--output", default="all_endless_runs.csv")
    args = parser.parse_args()
    rows, notes = merge(args.paths)
    print(*notes, sep="\n")
    if not rows:
        print("No rows found.")
        return 1
    Path(args.output).write_text(export.csv_text(rows), encoding="utf-8", newline="")
    print(f"{summary(rows)} Written to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
