"""Kept so the CLAUDE.md rule "python test_engine.py must pass" still holds. Runs tests/run_all.py."""

import runpy
import sys
from pathlib import Path

sys.argv = ["run_all.py"]
runpy.run_path(str(Path(__file__).resolve().parent / "tests" / "run_all.py"), run_name="__main__")
