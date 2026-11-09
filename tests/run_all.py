"""Run every tests/test_*.py file in its own process. Run: python tests/run_all.py"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run each test file, print a summary and return 1 if any failed."""
    env = {**os.environ, "USE_FAKE_AI": "true"}
    failed = []
    for path in sorted(Path(__file__).resolve().parent.glob("test_*.py")):
        code = subprocess.run([sys.executable, str(path)], env=env).returncode
        print(f"{'PASS' if code == 0 else 'FAIL'} {path.name}")
        if code:
            failed.append(path.name)
    print(f"{len(failed)} failed" if failed else "all tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
