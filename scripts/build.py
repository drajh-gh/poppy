#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "poppy-ops-cockpit"
FILES = ("manifest.json", "main.js", "styles.css")


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
        shutil.copy2(source, target)
        if source.read_bytes() != target.read_bytes():
            raise SystemExit(f"Build copy mismatch: {name}")
        hashes[name] = digest(target)
    result = {"status": "pass", "artifact": str(DIST), "files": hashes}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build()

