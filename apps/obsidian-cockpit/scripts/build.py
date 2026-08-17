#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "poppy-ops-cockpit"
FILES = (
    "manifest.json",
    "main.js",
    "styles.css",
    "bridge/poppy_ops_bridge.py",
    "config/bridge.json",
    "config/poppy-capability-graph.json",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    DIST.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in FILES:
        source = ROOT / name
        if not source.is_file():
            raise SystemExit(f"Missing build input: {source}")
        target = DIST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if source.read_bytes() != target.read_bytes():
            raise SystemExit(f"Build copy mismatch: {name}")
        hashes[name] = digest(target)
    actual = sorted(path.relative_to(DIST).as_posix() for path in DIST.rglob("*") if path.is_file())
    if actual != sorted(FILES):
        raise SystemExit(f"Unexpected package inventory: {actual}")
    result = {"status": "pass", "artifact": str(DIST), "files": hashes}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build()
