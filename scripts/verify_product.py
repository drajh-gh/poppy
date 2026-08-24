#!/usr/bin/env python3
"""Single deterministic verification entrypoint for the complete Poppy product."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = "85797ef39dfa641a87716d1c04d2613b67da7c22"
COCKPIT_SOURCE = "b7373b7ad3760243621bac2198f2b4c6ec4b9729"
REMOTE_SEED = "305efbd300a1c59ef0e84553b84638d0def22568"


def run(command: list[str], name: str) -> dict:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", timeout=300)
    result = {"name": name, "exit_code": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}
    if completed.returncode:
        raise RuntimeError(f"{name} failed\n{completed.stdout}\n{completed.stderr}")
    return result


def candidate_files() -> list[Path]:
    result = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], "candidate inventory")
    return [ROOT / line for line in result["stdout"].splitlines() if line]


def boundary_audit() -> dict:
    files = candidate_files()
    client_tokens = ("slo" + "ski", "ever" + "away", "orod" + "jarna")
    machine_tokens = ("c:\\users\\" + "david", "c:/users/" + "david", "c:\\va" + "ults", "c:/va" + "ults")
    violations: list[str] = []
    live_config_names = {"bridge.json", "bridge.local.json"}
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        lower_relative = relative.casefold()
        if any(part in lower_relative for part in ("/runtime/", "/evidence/", "/dist/")):
            violations.append(f"tracked generated/runtime path: {relative}")
        if path.name.casefold() in live_config_names:
            violations.append(f"tracked live config: {relative}")
        if path.suffix.casefold() in {".sqlite", ".sqlite3", ".db"}:
            violations.append(f"tracked database: {relative}")
        if not path.is_file() or path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".gif", ".ico"}:
            continue
        try:
            text = path.read_text(encoding="utf-8").casefold()
        except UnicodeDecodeError:
            continue
        for token in (*client_tokens, *machine_tokens):
            if token in text:
                violations.append(f"forbidden product identity/path in {relative}: {token}")
        if re.search(r"(?:api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}", text):
            violations.append(f"credential-shaped assignment in {relative}")
    graph_copies = [path.relative_to(ROOT).as_posix() for path in files if path.name == "poppy-capability-graph.json"]
    if graph_copies != ["references/poppy-capability-graph.json"]:
        violations.append(f"canonical graph source is not unique: {graph_copies}")
    if violations:
        raise RuntimeError("Product boundary audit failed:\n" + "\n".join(sorted(set(violations))))
    return {"name": "tracked product boundary audit", "status": "pass", "files_scanned": len(files), "canonical_graph": graph_copies[0]}


def ancestry_proof() -> dict:
    for revision in (CORE_SOURCE, COCKPIT_SOURCE, REMOTE_SEED):
        run(["git", "merge-base", "--is-ancestor", revision, "HEAD"], f"ancestry {revision}")
    return {"name": "three-history ancestry", "status": "pass", "head": run(["git", "rev-parse", "HEAD"], "candidate revision")["stdout"], "ancestors": [CORE_SOURCE, COCKPIT_SOURCE, REMOTE_SEED]}


def artifact_hashes() -> dict:
    artifact = ROOT / "apps" / "obsidian-cockpit" / "dist" / "poppy-ops-cockpit"
    files = sorted(path for path in artifact.rglob("*") if path.is_file())
    hashes = {path.relative_to(artifact).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    if len(hashes) != 6:
        raise RuntimeError(f"Expected six packaged cockpit files, found {sorted(hashes)}")
    return {"name": "cockpit artifact hashes", "status": "pass", "files": hashes}


def clean_proof() -> dict:
    status = run(["git", "status", "--porcelain"], "clean tree")
    if status["stdout"]:
        raise RuntimeError("Candidate tree is not clean:\n" + status["stdout"])
    return {"name": "clean candidate", "status": "pass"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-clean", action="store_true", help="Require a committed, clean candidate.")
    args = parser.parse_args(argv)
    checks: list[dict] = [
        run([sys.executable, "scripts/test_v2_schemas.py"], "Poppy v2 schema-foundation suite"),
        run([sys.executable, "scripts/test_project_operations.py"], "Project Operations deterministic suite"),
        run([sys.executable, "scripts/test_owned_process_supervisor.py"], "owned-process supervisor suite"),
        run([sys.executable, "-m", "compileall", "-q", "scripts", "apps/obsidian-cockpit/bridge", "apps/obsidian-cockpit/scripts", "apps/obsidian-cockpit/tests"], "Python compilation"),
        run([sys.executable, "apps/obsidian-cockpit/scripts/verify.py", "--check"], "Ops Cockpit deterministic suite"),
        boundary_audit(),
        ancestry_proof(),
        artifact_hashes(),
    ]
    if args.require_clean:
        checks.append(clean_proof())
    result = {
        "status": "pass",
        "product": "Poppy",
        "branch": run(["git", "branch", "--show-current"], "branch identity")["stdout"],
        "head": run(["git", "rev-parse", "HEAD"], "head identity")["stdout"],
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
