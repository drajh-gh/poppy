#!/usr/bin/env python3
"""Deterministic, project-neutral verification for the Obsidian cockpit."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT.parents[1]
FILES = (
    "manifest.json",
    "main.js",
    "styles.css",
    "bridge/poppy_ops_bridge.py",
    "config/bridge.json",
    "config/poppy-capability-graph.json",
)


def run(command: list[str], name: str) -> dict:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", timeout=180)
    result = {"name": name, "exit_code": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
    if completed.returncode:
        raise RuntimeError(f"{name} failed\n{completed.stdout}\n{completed.stderr}")
    return result


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def request_json(port: int, method: str, route: str, *, project: str | None = None, body: dict | None = None) -> tuple[int, dict]:
    headers = {"X-Poppy-Ops-Client": "obsidian-plugin"}
    payload = None
    if project is not None:
        headers["X-Poppy-Ops-Project"] = project
    if body is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(body)
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, route, body=payload, headers=headers)
    response = connection.getresponse()
    value = json.loads(response.read())
    status = response.status
    connection.close()
    return status, value


def request_sse_ready(port: int, project: str) -> str:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request("GET", f"/events?project={project}", headers={"X-Poppy-Ops-Client": "obsidian-plugin"})
    response = connection.getresponse()
    line = response.readline().decode("utf-8").strip()
    connection.close()
    if response.status != 200 or line != "event: ready":
        raise RuntimeError(f"SSE did not connect for {project}: status={response.status}, line={line!r}")
    return line


def write_fixture_vault(root: Path, key: str, name: str, *, contradiction: bool = False) -> list[Path]:
    vault = root / key
    current = vault / "wiki" / key / "current.md"
    current.parent.mkdir(parents=True)
    profile = {
        "project": {"key": key, "name": name, "stage": "active", "next_milestone": "Synthetic gate", "sensitivity": "synthetic"},
        "sources": {"repository": {"access": "read-only"}},
        "authority": {"implementation": "repository"},
        "tolerances": {"volatile_source_max_age_days": 7},
        "onboarding": {"known_risks": ["Synthetic contradiction"] if contradiction else []},
    }
    profile_path = vault / "project-ops.json"
    profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    current.write_text("---\nvalid_as_of: 2026-01-02\nreview_after: 2099-01-01\n---\n> [!success] Green — synthetic fixture current\n\n## Next actions\n\n1. Verify the fixture.\n", encoding="utf-8")
    return [profile_path, current]


def bridge_smoke() -> dict:
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="poppy-cockpit-verify-") as temp_name:
        temp = Path(temp_name)
        protected = [
            *write_fixture_vault(temp / "vaults", "atlas-demo", "Atlas Demo"),
            *write_fixture_vault(temp / "vaults", "beacon-demo", "Beacon Demo", contradiction=True),
        ]
        before = {str(path): digest(path) for path in protected}
        config = json.loads((ROOT / "config" / "bridge.example.json").read_text(encoding="utf-8"))
        config.update({
            "port": port,
            "runtime": {"ledger": str(temp / "events.jsonl"), "database": str(temp / "events.sqlite3")},
            "vaults": [
                {"key": "atlas-demo", "name": "Atlas Demo", "path": str(temp / "vaults" / "atlas-demo")},
                {"key": "beacon-demo", "name": "Beacon Demo", "path": str(temp / "vaults" / "beacon-demo")},
            ],
            "capability_graph": str(PRODUCT_ROOT / "references" / "poppy-capability-graph.json"),
        })
        config["codex"]["launch_enabled"] = False
        config_path = temp / "bridge.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        replay = run([
            sys.executable, "bridge/poppy_ops_bridge.py", "replay", "--config", str(config_path),
            "--ledger", str(temp / "events.jsonl"), "--database", str(temp / "events.sqlite3"),
            "--source", "fixtures/events.jsonl",
        ], "synthetic event replay")
        processes: list[tuple[str, subprocess.Popen]] = []

        def start_pair(cycle: int) -> list[tuple[str, subprocess.Popen]]:
            pair = []
            for project in ("atlas-demo", "beacon-demo"):
                token = f"verify-{cycle}-{project}"
                process = subprocess.Popen(
                    [
                        sys.executable, "bridge/poppy_ops_bridge.py", "serve", "--config", str(config_path),
                        "--ledger", str(temp / "events.jsonl"), "--database", str(temp / "events.sqlite3"),
                        "--instance-token", token,
                    ],
                    cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
                )
                pair.append((token, process))
                processes.append((token, process))
            return pair

        def converge(pair: list[tuple[str, subprocess.Popen]]) -> tuple[subprocess.Popen, dict]:
            health = wait_health(port)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and sum(process.poll() is None for _token, process in pair) != 1:
                time.sleep(0.05)
            alive = [(token, process) for token, process in pair if process.poll() is None]
            if len(alive) != 1:
                raise RuntimeError(f"Dual-vault startup left {len(alive)} bridge processes instead of one")
            token, owner = alive[0]
            if health.get("instance_token") != token or health.get("pid") != owner.pid:
                raise RuntimeError(f"Health ownership mismatch: health={health}, owner={token}/{owner.pid}")
            losers = [process for _token, process in pair if process is not owner]
            if any(process.poll() != 73 for process in losers):
                raise RuntimeError(f"Losing bridge child did not exit with the ownership code: {[process.poll() for process in losers]}")
            return owner, health

        pair = start_pair(1)
        try:
            owner, health = converge(pair)
            rejected_scopes = {}
            for label, project in (("missing", None), ("empty", ""), ("unknown", "unknown-demo")):
                rejected_status, rejected = request_json(port, "GET", "/api/state", project=project)
                if rejected_status < 400 or rejected.get("state") != "gray" or {"vaults", "runs", "events"} & rejected.keys():
                    raise RuntimeError(f"{label} project scope did not fail closed: {rejected_status} {rejected}")
                rejected_scopes[label] = rejected_status
            scopes = {}
            for project in ("atlas-demo", "beacon-demo"):
                scoped_status, scoped = request_json(port, "GET", "/api/state", project=project)
                if scoped_status != 200 or scoped.get("scope", {}).get("project") != project:
                    raise RuntimeError(f"Project scope was not preserved for {project}")
                if [vault.get("key") for vault in scoped.get("vaults", [])] != [project]:
                    raise RuntimeError(f"Project state leaked another vault into {project}")
                if any(item.get("project") != project for item in [*scoped.get("runs", []), *scoped.get("events", [])]):
                    raise RuntimeError(f"Project telemetry leaked into {project}")
                if len(scoped.get("graph", {}).get("nodes", [])) != 37 or len(scoped.get("graph", {}).get("edges", [])) != 81:
                    raise RuntimeError("Canonical capability graph topology changed")
                scopes[project] = {"runs": len(scoped.get("runs", [])), "events": len(scoped.get("events", []))}
            poll_sse_checks = 0
            for _interval in range(2):
                for project in ("atlas-demo", "beacon-demo"):
                    scoped_status, scoped = request_json(port, "GET", "/api/state", project=project)
                    if scoped_status != 200 or scoped.get("scope", {}).get("project") != project:
                        raise RuntimeError(f"Repeated poll lost project scope for {project}")
                    request_sse_ready(port, project)
                    poll_sse_checks += 1
                time.sleep(0.2)
            refresh_status, refresh = request_json(port, "POST", "/api/refresh", project="atlas-demo", body={"scope": "configured-vaults", "mode": "read-only-index"})
            if refresh_status != 200 or [vault.get("key") for vault in refresh.get("vaults", [])] != ["atlas-demo"] or refresh.get("event", {}).get("project") != "atlas-demo":
                raise RuntimeError(f"Scoped read-only refresh failed: status={refresh_status}, response={refresh}")
            after = {str(path): digest(path) for path in protected}
            if before != after:
                raise RuntimeError("Synthetic vault fixtures changed during read-only bridge smoke")
            owner.terminate()
            owner.wait(timeout=5)
            reloaded_owner, reloaded_health = converge(start_pair(2))
            for project in ("atlas-demo", "beacon-demo"):
                scoped_status, scoped = request_json(port, "GET", "/api/state", project=project)
                if scoped_status != 200 or scoped.get("scope", {}).get("project") != project:
                    raise RuntimeError(f"Reloaded bridge lost project scope for {project}")
                request_sse_ready(port, project)
                poll_sse_checks += 1
            reloaded_owner.terminate()
            reloaded_owner.wait(timeout=5)
            if any(process.poll() is None for _token, process in processes):
                raise RuntimeError("Owned bridge process survived dual-vault lifecycle smoke")
            return {
                "name": "synthetic localhost integration",
                "status": "pass",
                "health": health,
                "reload_health": reloaded_health,
                "rejected_scopes": rejected_scopes,
                "project_scopes": scopes,
                "poll_sse_checks": poll_sse_checks,
                "reload_cycles": 2,
                "owned_process_ledger": [
                    {"token": token, "pid": process.pid, "exit_code": process.returncode}
                    for token, process in processes
                ],
                "owned_process_survivors": 0,
                "replay": replay["stdout"],
                "protected_hashes_unchanged": len(before),
            }
        finally:
            for _token, process in processes:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
            if any(process.poll() is None for _token, process in processes):
                raise RuntimeError("Owned bridge process survived verification cleanup")


def package_readback() -> dict:
    source = ROOT / "dist" / "poppy-ops-cockpit"
    source_hashes = {name: digest(source / name) for name in FILES}
    with tempfile.TemporaryDirectory(prefix="poppy-cockpit-install-") as temp_name:
        results = []
        for project in ("atlas-demo", "beacon-demo"):
            destination = Path(temp_name) / project / ".obsidian" / "plugins" / "poppy-ops-cockpit"
            for name in FILES:
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source / name, target)
            inventory = sorted(path.relative_to(destination).as_posix() for path in destination.rglob("*") if path.is_file())
            hashes = {name: digest(destination / name) for name in FILES}
            if inventory != sorted(FILES) or hashes != source_hashes:
                raise RuntimeError(f"Synthetic installation mismatch for {project}")
            results.append({"project": project, "hashes": hashes})
    return {"name": "synthetic package installation read-back", "status": "pass", "source_hashes": source_hashes, "installations": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compatibility flag; verification never rewrites source evidence.")
    parser.parse_args(argv)
    checks = [
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"], "cockpit unit tests"),
        run([sys.executable, "scripts/build.py"], "cockpit package build"),
        run(["node", "--check", "main.js"], "plugin syntax"),
        run(["node", "tests/obsidian_smoke.js"], "Obsidian runtime smoke"),
        run(["node", "tests/bridge_lifecycle_smoke.js"], "dual-vault bridge lifecycle regression"),
        bridge_smoke(),
        package_readback(),
    ]
    if (PRODUCT_ROOT / "references" / "poppy-capability-graph.json").read_bytes() != (ROOT / "dist" / "poppy-ops-cockpit" / "config" / "poppy-capability-graph.json").read_bytes():
        raise RuntimeError("Packaged capability graph differs from the canonical root graph")
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("id") != "poppy-ops-cockpit" or manifest.get("isDesktopOnly") is not True:
        raise RuntimeError("Plugin manifest identity mismatch")
    print(json.dumps({"status": "pass", "checks": [item["name"] for item in checks], "graph_source": "references/poppy-capability-graph.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
