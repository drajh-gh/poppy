#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT.parents[1]
DEFAULT_DIST = ROOT / "dist" / "poppy-ops-cockpit"
DEFAULT_CONFIG = ROOT / "config" / "bridge.example.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(*, config_source: Path = DEFAULT_CONFIG, output: Path = DEFAULT_DIST) -> dict:
    inputs = (
        (ROOT / "manifest.json", "manifest.json"),
        (ROOT / "main.js", "main.js"),
        (ROOT / "styles.css", "styles.css"),
        (ROOT / "bridge" / "poppy_ops_bridge.py", "bridge/poppy_ops_bridge.py"),
        (config_source.resolve(), "config/bridge.json"),
        (PRODUCT_ROOT / "references" / "poppy-capability-graph.json", "config/poppy-capability-graph.json"),
    )
    output = output.resolve()
    runtime_root = (PRODUCT_ROOT / "runtime").resolve()
    if output != DEFAULT_DIST.resolve() and runtime_root not in output.parents:
        raise SystemExit(f"Refusing package output outside ignored product runtime: {output}")
    if output.is_dir():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for source, name in inputs:
        if not source.is_file():
            raise SystemExit(f"Missing build input: {source}")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if source.read_bytes() != target.read_bytes():
            raise SystemExit(f"Build copy mismatch: {name}")
        hashes[name] = digest(target)
    actual = sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file())
    expected = sorted(name for _source, name in inputs)
    if actual != expected:
        raise SystemExit(f"Unexpected package inventory: {actual}")
    result = {"status": "pass", "artifact": str(output), "config_source": str(config_source.resolve()), "files": hashes}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build an exact six-file Poppy Ops Cockpit package.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Bridge configuration to package.")
    parser.add_argument("--output", type=Path, default=DEFAULT_DIST, help="Package output directory.")
    args = parser.parse_args()
    build(config_source=args.config, output=args.output)
