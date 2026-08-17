#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import http.client
import json
import os
import argparse
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "verification.json"
FILES = (
    "manifest.json",
    "main.js",
    "styles.css",
    "bridge/poppy_ops_bridge.py",
    "config/bridge.json",
    "config/poppy-capability-graph.json",
)
MANIFEST = Path(r"C:\Users\david\Documents\Codex\2026-08-17\ho\work\poppy-ops-cockpit-delivery-manifest.json")
PREFLIGHT = Path(r"C:\Users\david\Documents\Codex\2026-08-17\ho\work\poppy-ops-cockpit-local-preflight.json")
PLUGIN_ROOT = Path(r"C:\Users\david\.codex\plugins\cache\personal\project-operations\0.1.0+codex.20260816213000")


def run(command: list[str], name: str) -> dict:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", timeout=120)
    result = {"name": name, "command": command, "exit_code": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
    if completed.returncode:
        raise RuntimeError(f"{name} failed\n{completed.stdout}\n{completed.stderr}")
    return result


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_health(port: int, timeout: float = 12) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            connection.request("GET", "/health")
            response = connection.getresponse()
            value = json.loads(response.read())
            connection.close()
            if response.status == 200:
                return value
        except (OSError, json.JSONDecodeError):
            time.sleep(0.1)
    raise RuntimeError("Bridge health endpoint did not become ready")


def bridge_smoke() -> dict:
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="poppy-verify-") as temp_name:
        temp = Path(temp_name)
        config = json.loads((ROOT / "config" / "bridge.json").read_text(encoding="utf-8"))
        config["port"] = port
        config["codex"]["launch_enabled"] = False
        config_path = temp / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        protected = []
        for vault in config["vaults"]:
            root = Path(vault["path"])
            protected.extend([root / "project-ops.json", *root.glob("wiki/**/current.md"), *root.glob("wiki/**/portfolio-summary.md"), *root.glob("dashboards/*")])
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in protected if path.is_file()}
        ledger = temp / "events.jsonl"
        database = temp / "events.sqlite3"
        replay = run([sys.executable, "bridge/poppy_ops_bridge.py", "replay", "--config", str(config_path), "--ledger", str(ledger), "--database", str(database), "--source", "fixtures/events.jsonl"], "fixture replay")
        process = subprocess.Popen(
            [sys.executable, "bridge/poppy_ops_bridge.py", "serve", "--config", str(config_path), "--ledger", str(ledger), "--database", str(database)],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        try:
            health = wait_health(port)
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/api/state")
            response = connection.getresponse()
            state = json.loads(response.read())
            connection.close()
            if response.status != 200 or len(state.get("vaults", [])) != 2 or not state.get("graph", {}).get("nodes"):
                raise RuntimeError("Bridge state response did not contain dual-vault and graph coverage")
            if len(state["graph"].get("nodes", [])) != 37 or len(state["graph"].get("edges", [])) != 81:
                raise RuntimeError("Bridge state did not preserve the full 37-node/81-edge topology")
            if any(run.get("cost", {}).get("basis") not in {"exact", "estimated", "shadow-price", "unavailable"} for run in state.get("runs", [])):
                raise RuntimeError("Run projection emitted an unsupported cost basis")
            unavailable_runs = [run for run in state.get("runs", []) if run.get("cost", {}).get("basis") == "unavailable"]
            if any(run.get("cost", {}).get("amount") is not None or run.get("cost", {}).get("currency") is not None for run in unavailable_runs):
                raise RuntimeError("Unavailable run cost retained a numeric subtotal or currency label")
            available_runs = [run for run in state.get("runs", []) if run.get("cost", {}).get("basis") != "unavailable"]
            if any(not isinstance(run.get("cost", {}).get("currency"), str) or len(run["cost"]["currency"]) != 3 for run in available_runs):
                raise RuntimeError("Available run cost lacks an explicit three-letter currency")
            if any(not finding.get("action") or not finding.get("references") for finding in state.get("findings", [])):
                raise RuntimeError("A deterministic finding lacks actionable lineage")
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            body = json.dumps({"scope": "configured-vaults", "mode": "read-only-index"})
            connection.request("POST", "/api/refresh", body=body, headers={"Content-Type": "application/json", "X-Poppy-Ops-Client": "obsidian-plugin"})
            refresh_response = connection.getresponse()
            refresh = json.loads(refresh_response.read())
            connection.close()
            if refresh_response.status != 200 or len(refresh.get("vaults", [])) != 2:
                raise RuntimeError("Read-only refresh smoke failed")
            after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in protected if path.is_file()}
            if before != after:
                raise RuntimeError("Canonical vault surface changed during read-only bridge smoke")
            return {
                "name": "localhost bridge smoke", "status": "pass", "port": port,
                "health": health, "vaults": [{"key": item["key"], "exists": item["exists"], "state": item["state"]} for item in state["vaults"]],
                "graph_nodes": len(state["graph"]["nodes"]), "graph_edges": len(state["graph"]["edges"]), "runs": len(state["runs"]), "unavailable_cost_runs": len(unavailable_runs), "findings_with_lineage": len(state["findings"]), "refresh_event": refresh["event"]["event_id"],
                "owned_process_pid": process.pid,
                "canonical_vault_hashes_unchanged": len(before),
            }
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if process.poll() is None:
                raise RuntimeError("Owned bridge process survived verification")


def fixture_install() -> dict:
    source = ROOT / "dist" / "poppy-ops-cockpit"
    root = ROOT / "runtime" / "fixture-install"
    destinations = [root / "Sloski" / ".obsidian" / "plugins" / "poppy-ops-cockpit", root / "EverAway" / ".obsidian" / "plugins" / "poppy-ops-cockpit"]
    source_hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in FILES}
    results = []
    for destination in destinations:
        destination.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for name in FILES:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / name, target)
            hashes[name] = hashlib.sha256((destination / name).read_bytes()).hexdigest()
        inventory = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file())
        if inventory != sorted(FILES):
            raise RuntimeError(f"Fixture installation inventory mismatch: {destination}: {inventory}")
        if hashes != source_hashes:
            raise RuntimeError(f"Fixture installation hash mismatch: {destination}")
        results.append({"path": str(destination), "files": hashes})
    return {"name": "fixture installation read-back", "status": "pass", "source": str(source), "installations": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify and optionally freeze Poppy Ops Cockpit evidence.")
    parser.add_argument("--check", action="store_true", help="Run every gate without rewriting the frozen evidence file.")
    args = parser.parse_args(argv)
    checks = []
    checks.append(run([sys.executable, str(PLUGIN_ROOT / "scripts" / "validate_delivery_manifest.py"), str(MANIFEST), "--required-extension", "obsidian-runtime-smoke", "--required-extension", "codex-stream-compatibility"], "delivery manifest validation"))
    checks.append(run([sys.executable, str(PLUGIN_ROOT / "scripts" / "validate_local_execution_preflight.py"), "--json", str(PREFLIGHT)], "local execution preflight validation"))
    checks.append(run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], "unit tests"))
    checks.append(run([sys.executable, "scripts/build.py"], "package build"))
    checks.append(run(["node", "--check", "main.js"], "plugin syntax"))
    checks.append(run(["node", "tests/obsidian_smoke.js"], "obsidian runtime smoke"))
    checks.append(bridge_smoke())
    checks.append(fixture_install())
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("id") != "poppy-ops-cockpit" or manifest.get("isDesktopOnly") is not True:
        raise RuntimeError("Plugin manifest identity mismatch")
    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    for requirement in ("prefers-reduced-motion", ":focus-visible", "--poppy-cyan", ".poppy-execution-rail", ".poppy-topology-edge", ".poppy-finding-ref"):
        if requirement not in css:
            raise RuntimeError(f"Stylesheet requirement missing: {requirement}")
    evidence = {
        "schema_version": 1,
        "status": "pass",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "candidate": "working-tree-pre-freeze",
        "checks": checks,
        "codex_gate": json.loads((ROOT / "evidence" / "codex-appserver-probe.json").read_text(encoding="utf-8")),
        "real_vault_installation": "pending-post-assurance",
        "external_writes": [],
    }
    if not args.check:
        EVIDENCE.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "evidence": str(EVIDENCE) if not args.check else "unchanged (--check)", "checks": [item["name"] for item in checks]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
