"""Admin tool: merge the Endless run files players sent into one Excel workbook and print what stands out.

Usage:  python tools/merge_runs.py FOLDER_OR_FILES... [-o all_runs.xlsx]

Files that are not run files (or come from an older version of the game, such as the earlier CSV files) are skipped
with a message. A run, shift or visitor that appears in several files (the same player sent a run twice) is kept once:
for a run, the copy with the most shifts wins. Rows are sorted by time.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import export  # noqa: E402


def files_in(paths: list[str]) -> list[Path]:
    """Return the files named, or the .xlsx files found inside the folders named."""
    found: list[Path] = []
    for name in paths:
        path = Path(name)
        found += sorted(path.glob("*.xlsx")) if path.is_dir() else [path]
    return found


def merge(paths: list[str]) -> tuple[dict, list[str]]:
    """Return (merged rows by sheet, messages about skipped files)."""
    runs: dict[str, dict] = {}
    shifts: dict[tuple, dict] = {}
    visitors: dict[tuple, dict] = {}
    notes: list[str] = []
    for path in files_in(paths):
        try:
            found = export.read_workbook(path.read_bytes())
        except (OSError, ValueError) as error:
            notes.append(f"skipped {path}: {error}")
            continue
        for row in found["runs"]:
            if row["run_id"] not in runs or (row["shifts"] or 0) > (runs[row["run_id"]]["shifts"] or 0):
                runs[row["run_id"]] = row
        shifts.update({(row["run_id"], row["shift"]): row for row in found["shifts"]})
        visitors.update({(row["run_id"], row["shift"], row["visitor"]): row for row in found["visitors"]})
    merged = {"runs": sorted(runs.values(), key=lambda row: (str(row["first_played"]), row["run_id"])),
              "shifts": sorted(shifts.values(), key=lambda row: (str(row["played_at"]), row["run_id"], row["shift"])),
              "visitors": sorted(visitors.values(), key=lambda row: (row["run_id"], row["shift"], row["visitor"]))}
    return merged, notes


def top(values: list, count: int = 3) -> str:
    """Return the most common values with their counts, like "Impersonation (12), Combined attack (7)"."""
    return ", ".join(f"{value} ({times})" for value, times in Counter(v for v in values if v).most_common(count)) or "none"


def summary(merged: dict) -> str:
    """Return a few lines about the merged files: the size, how attacks went and what players most often missed."""
    runs, shifts, visitors = merged["runs"], merged["shifts"], merged["visitors"]
    attacks = [row for row in visitors if row["who"] == "Attacker"]
    leaks = [row for row in attacks if row["outcome"] == export.OUTCOMES["leaked"]]
    missing = [name for row in shifts for name in str(row["missing"] or "").split("; ") if not str(row["missing"]).startswith("Unknown")]
    best = max((row["score"] or 0 for row in runs), default=0)
    lines = [f"{len(runs)} runs, {len(shifts)} shifts, {len(visitors)} visitors; best run score {best}.",
             f"Attacks: {len(attacks)}, {len(leaks)} leaked ({round(100 * len(leaks) / len(attacks)) if attacks else 0}%).",
             f"Techniques that leaked most: {top([row['technique'] for row in leaks])}.",
             f"Defenses most often missing from the rules: {top(missing)}."]
    return "\n".join(lines)


def main() -> int:
    """Merge the files named on the command line and write the result."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("paths", nargs="+", help="run files or folders of run files")
    parser.add_argument("-o", "--output", default="all_endless_runs.xlsx")
    args = parser.parse_args()
    merged, notes = merge(args.paths)
    print(*notes, sep="\n")
    if not merged["shifts"]:
        print("No shifts found.")
        return 1
    Path(args.output).write_bytes(export.workbook_bytes(merged["runs"], merged["shifts"], merged["visitors"]))
    print(f"{summary(merged)}\nWritten to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
