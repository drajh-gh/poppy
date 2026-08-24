#!/usr/bin/env python3
"""Run the deterministic Poppy v2 schema-foundation suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests/v2_schema", "-p", "test_*.py", "-v"],
        cwd=ROOT,
        text=True,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
