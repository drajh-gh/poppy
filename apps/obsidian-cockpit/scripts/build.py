#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT.parents[1]
DIST = ROOT / "dist" / "poppy-ops-cockpit"
INPUTS = (
    (ROOT / "manifest.json", "manifest.json"),
    (ROOT / "main.js", "main.js"),
    (ROOT / "styles.css", "styles.css"),
    (ROOT / "bridge" / "poppy_ops_bridge.py", "bridge/poppy_ops_bridge.py"),
    (ROOT / "config" / "bridge.example.json", "config/bridge.json"),
    (PRODUCT_ROOT / "references" / "poppy-capability-graph.json", "config/poppy-capability-graph.json"),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    if DIST.is_dir():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for source, name in INPUTS:
        if not source.is_file():
            raise SystemExit(f"Missing build input: {source}")
        target = DIST / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if source.read_bytes() != target.read_bytes():
            raise SystemExit(f"Build copy mismatch: {name}")
        hashes[name] = digest(target)
    actual = sorted(path.relative_to(DIST).as_posix() for path in DIST.rglob("*") if path.is_file())
    expected = sorted(name for _source, name in INPUTS)
    if actual != expected:
        raise SystemExit(f"Unexpected package inventory: {actual}")
    result = {"status": "pass", "artifact": str(DIST), "files": hashes}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build()
