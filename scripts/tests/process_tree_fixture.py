#!/usr/bin/env python3
"""Disposable child/grandchild process fixture for supervisor tests."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def write_pid(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{os.getpid()}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("echo", "tree", "child", "sleeper", "rollback"))
    parser.add_argument("--pid-dir", type=Path)
    parser.add_argument("--pid-file", type=Path)
    parser.add_argument("--marker", type=Path)
    parser.add_argument("--exit-code", type=int, default=0)
    args = parser.parse_args()

    if args.mode == "echo":
        print("fixture-stdout", flush=True)
        print("fixture-stderr", file=sys.stderr, flush=True)
        return args.exit_code
    if args.mode == "rollback":
        if args.marker is None:
            raise SystemExit("--marker is required")
        args.marker.write_text("rollback-complete\n", encoding="utf-8")
        return args.exit_code
    if args.mode == "sleeper":
        if args.pid_file:
            write_pid(args.pid_file)
        time.sleep(60)
        return 0
    if args.pid_dir is None:
        raise SystemExit("--pid-dir is required")

    fixture = Path(__file__).resolve()
    if args.mode == "tree":
        write_pid(args.pid_dir / "root.pid")
        subprocess.Popen([sys.executable, str(fixture), "child", "--pid-dir", str(args.pid_dir)])
        print("tree-ready", flush=True)
        time.sleep(60)
        return 0
    if args.mode == "child":
        write_pid(args.pid_dir / "child.pid")
        subprocess.Popen(
            [
                sys.executable,
                str(fixture),
                "sleeper",
                "--pid-file",
                str(args.pid_dir / "grandchild.pid"),
            ]
        )
        time.sleep(60)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
