#!/usr/bin/env python3
"""Dependency-free localhost bridge for the Poppy Ops Cockpit.

The bridge reads configured project vaults, normalizes structured execution events,
stores an append-only ledger, and exposes a disposable SQLite projection. It never
writes project vaults and never talks directly to an external provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "bridge.json"
RUNTIME = ROOT / "runtime"
LEDGER = RUNTIME / "events.jsonl"
DATABASE = RUNTIME / "poppy-ops.sqlite3"
VALID_STATES = {"completed", "current", "waiting", "blocked", "pending", "failed", "gray"}
VALID_COST_BASIS = {"exact", "estimated", "shadow-price", "unavailable"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(json_dumps(value).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def parse_timestamp(value: Any) -> str:
    if isinstance(value, str) and value.strip():
        candidate = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            pass
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / (1000 if value > 10_000_000_000 else 1), timezone.utc).isoformat().replace("+00:00", "Z")
    return "1970-01-01T00:00:00Z"


def normalize_tokens(value: Any) -> dict[str, int]:
    source = value if isinstance(value, dict) else {}
    aliases = {
        "input": ("input", "input_tokens", "inputTokens"),
        "cached": ("cached", "cached_input_tokens", "cachedInputTokens"),
        "reasoning": ("reasoning", "reasoning_tokens", "reasoningTokens"),
        "output": ("output", "output_tokens", "outputTokens"),
    }
    result: dict[str, int] = {}
    for target, keys in aliases.items():
        raw = next((source[key] for key in keys if key in source), 0)
        try:
            result[target] = max(0, int(raw or 0))
        except (TypeError, ValueError):
            result[target] = 0
    return result


def normalize_cost(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    basis = str(source.get("basis") or "unavailable")
    if basis not in VALID_COST_BASIS:
        basis = "unavailable"
    raw_amount = source.get("amount")
    try:
        amount = None if raw_amount is None else round(float(raw_amount), 8)
    except (TypeError, ValueError):
        amount = None
        basis = "unavailable"
    return {"amount": amount, "currency": str(source.get("currency") or "USD"), "basis": basis}


def normalize_evidence(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue
        state = str(item.get("state") or "gray").lower()
        normalized.append(
            {
                "source": str(item.get("source") or "unknown"),
                "locator": item.get("locator"),
                "freshness": item.get("freshness") or "unknown",
                "authority": item.get("authority") or "unresolved",
                "contradiction": bool(item.get("contradiction", False)),
                "state": state if state in VALID_STATES else "gray",
            }
        )
    return normalized


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Event must be an object")
    status = str(raw.get("status") or "gray").lower()
    if status not in VALID_STATES:
        status = "gray"
    kind = str(raw.get("kind") or raw.get("method") or "unknown")
    event = {
        "schema_version": 1,
        "event_id": str(raw.get("event_id") or ""),
        "timestamp": parse_timestamp(raw.get("timestamp") or raw.get("emittedAtMs")),
        "run_id": str(raw.get("run_id") or raw.get("runId") or "unassigned"),
        "project": str(raw.get("project") or "portfolio"),
        "kind": kind,
        "status": status,
        "capability": raw.get("capability"),
        "skill": raw.get("skill"),
        "worker": raw.get("worker"),
        "tool": raw.get("tool"),
        "approval": raw.get("approval") or "not-required",
        "duration_ms": raw.get("duration_ms") if raw.get("duration_ms") is not None else raw.get("durationMs"),
        "tokens": normalize_tokens(raw.get("tokens") or raw.get("usage")),
        "cost": normalize_cost(raw.get("cost")),
        "evidence": normalize_evidence(raw.get("evidence")),
        "parent_id": raw.get("parent_id") or raw.get("parentId"),
        "message": str(raw.get("message") or kind),
        "metadata": raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {},
    }
    if event["duration_ms"] is not None:
        try:
            event["duration_ms"] = max(0, int(event["duration_ms"]))
        except (TypeError, ValueError):
            event["duration_ms"] = None
    if not event["event_id"]:
        identity = {key: value for key, value in event.items() if key != "event_id"}
        event["event_id"] = stable_id("evt", identity)
    return event


class EventStore:
    def __init__(self, ledger: Path = LEDGER, database: Path = DATABASE) -> None:
        self.ledger = Path(ledger)
        self.database = Path(database)
        self.lock = threading.RLock()
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.database, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    project TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    capability TEXT,
                    skill TEXT,
                    worker TEXT,
                    tool TEXT,
                    approval TEXT,
                    duration_ms INTEGER,
                    input_tokens INTEGER NOT NULL,
                    cached_tokens INTEGER NOT NULL,
                    reasoning_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_amount REAL,
                    cost_currency TEXT NOT NULL,
                    cost_basis TEXT NOT NULL,
                    parent_id TEXT,
                    message TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_run_time ON events(run_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_project_time ON events(project, timestamp);
                CREATE TABLE IF NOT EXISTS vault_snapshots (
                    vault_key TEXT PRIMARY KEY,
                    captured_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS owned_threads (
                    thread_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    interface TEXT NOT NULL,
                    controls_digest TEXT NOT NULL
                );
                """
            )

    def append(self, raw: dict[str, Any], *, persist: bool = True) -> tuple[dict[str, Any], bool]:
        material = dict(raw)
        material.setdefault("timestamp", utc_now())
        event = normalize_event(material)
        with self.lock:
            with self.connect() as connection:
                exists = connection.execute("SELECT 1 FROM events WHERE event_id = ?", (event["event_id"],)).fetchone()
                if exists:
                    return event, False
                if persist:
                    with self.ledger.open("a", encoding="utf-8", newline="\n") as handle:
                        handle.write(json_dumps(event) + "\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                self._insert(connection, event)
        return event, True

    @staticmethod
    def _insert(connection: sqlite3.Connection, event: dict[str, Any]) -> None:
        tokens = event["tokens"]
        cost = event["cost"]
        connection.execute(
            """INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event["event_id"], event["timestamp"], event["run_id"], event["project"], event["kind"],
                event["status"], event["capability"], event["skill"], event["worker"], event["tool"],
                event["approval"], event["duration_ms"], tokens["input"], tokens["cached"], tokens["reasoning"],
                tokens["output"], cost["amount"], cost["currency"], cost["basis"], event["parent_id"],
                event["message"], json_dumps(event["evidence"]), json_dumps(event["metadata"]), json_dumps(event),
            ),
        )

    def replay(self, source: Path | None = None, *, reset: bool = True) -> dict[str, int]:
        path = Path(source or self.ledger)
        accepted = malformed = duplicate = 0
        with self.lock:
            if reset:
                with self.connect() as connection:
                    connection.execute("DELETE FROM events")
            if not path.exists():
                return {"accepted": 0, "malformed": 0, "duplicate": 0}
            seen: set[str] = set()
            with path.open("r", encoding="utf-8") as handle, self.connect() as connection:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        event = normalize_event(json.loads(line))
                    except (json.JSONDecodeError, ValueError, TypeError):
                        malformed += 1
                        continue
                    if event["event_id"] in seen:
                        duplicate += 1
                        continue
                    seen.add(event["event_id"])
                    self._insert(connection, event)
                    accepted += 1
        return {"accepted": accepted, "malformed": malformed, "duplicate": duplicate}

    def events(self, limit: int = 300, run_id: str | None = None) -> list[dict[str, Any]]:
        limit = min(max(int(limit), 1), 2000)
        query = "SELECT raw_json FROM events"
        params: list[Any] = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY timestamp DESC, event_id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as connection:
            return [json.loads(row["raw_json"]) for row in connection.execute(query, params)]

    def runs(self, limit: int = 100) -> list[dict[str, Any]]:
        query = """
        SELECT run_id, project, MIN(timestamp) AS started_at, MAX(timestamp) AS updated_at,
               COUNT(*) AS event_count,
               SUM(COALESCE(duration_ms,0)) AS duration_ms,
               SUM(input_tokens) AS input_tokens, SUM(cached_tokens) AS cached_tokens,
               SUM(reasoning_tokens) AS reasoning_tokens, SUM(output_tokens) AS output_tokens,
               SUM(cost_amount) AS known_cost_amount,
               SUM(CASE WHEN cost_amount IS NULL OR cost_basis = 'unavailable' THEN 1 ELSE 0 END) AS unavailable_cost_count,
               SUM(CASE WHEN cost_basis = 'exact' THEN 1 ELSE 0 END) AS exact_cost_count,
               SUM(CASE WHEN cost_basis = 'estimated' THEN 1 ELSE 0 END) AS estimated_cost_count,
               SUM(CASE WHEN cost_basis = 'shadow-price' THEN 1 ELSE 0 END) AS shadow_cost_count,
               MAX(CASE status WHEN 'failed' THEN 7 WHEN 'blocked' THEN 6 WHEN 'current' THEN 5
                   WHEN 'waiting' THEN 4 WHEN 'gray' THEN 3 WHEN 'pending' THEN 2 ELSE 1 END) AS state_rank
        FROM events GROUP BY run_id, project ORDER BY updated_at DESC LIMIT ?
        """
        states = {7: "failed", 6: "blocked", 5: "current", 4: "waiting", 3: "gray", 2: "pending", 1: "completed"}
        with self.connect() as connection:
            result = []
            for row in connection.execute(query, (min(max(limit, 1), 500),)):
                item = dict(row)
                item["status"] = states.get(item.pop("state_rank"), "gray")
                item["tokens"] = {key: item.pop(f"{key}_tokens") for key in ("input", "cached", "reasoning", "output")}
                known_amount = item.pop("known_cost_amount")
                unavailable_count = item.pop("unavailable_cost_count")
                exact_count = item.pop("exact_cost_count")
                estimated_count = item.pop("estimated_cost_count")
                shadow_count = item.pop("shadow_cost_count")
                if unavailable_count or known_amount is None:
                    amount, basis = None, "unavailable"
                elif shadow_count:
                    amount, basis = round(known_amount, 8), "shadow-price"
                elif estimated_count:
                    amount, basis = round(known_amount, 8), "estimated"
                elif exact_count:
                    amount, basis = round(known_amount, 8), "exact"
                else:
                    amount, basis = None, "unavailable"
                item["cost"] = {"amount": amount, "currency": "USD", "basis": basis}
                result.append(item)
            return result

    def save_vault_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO vault_snapshots(vault_key,captured_at,payload_json) VALUES (?,?,?)",
                (snapshot["key"], snapshot["captured_at"], json_dumps(snapshot)),
            )

    def owned_thread_ids(self) -> list[str]:
        with self.connect() as connection:
            return [row["thread_id"] for row in connection.execute("SELECT thread_id FROM owned_threads ORDER BY created_at, thread_id")]

    def register_owned_thread(self, thread_id: str, controls: dict[str, Any]) -> None:
        digest = stable_id("controls", controls)
        with self.connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO owned_threads(thread_id,created_at,interface,controls_digest) VALUES (?,?,?,?)",
                (thread_id, utc_now(), "official-app-server-stdio-jsonrpc", digest),
            )


def file_state(path: Path, stale_days: int = 7) -> dict[str, Any]:
    if not path.exists():
        return {"state": "gray", "reason": "missing", "path": str(path), "modified_at": None, "age_days": None}
    modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    age_days = max(0.0, (datetime.now(timezone.utc) - modified).total_seconds() / 86400)
    return {
        "state": "gray" if age_days > stale_days else "completed",
        "reason": "stale" if age_days > stale_days else "available",
        "path": str(path),
        "modified_at": modified.isoformat().replace("+00:00", "Z"),
        "age_days": round(age_days, 2),
    }


def current_signal(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"state": "gray", "label": "Gray", "headline": "Current project assessment is unavailable", "review_after": None, "valid_as_of": None, "next_action_count": 0}
    try:
        text = path.read_text(encoding="utf-8")[:64_000]
    except OSError:
        return {"state": "gray", "label": "Gray", "headline": "Current project assessment could not be read", "review_after": None, "valid_as_of": None, "next_action_count": 0}
    signal = re.search(r"^>\s*\[!(?:warning|danger|success|info|note)\]\s*(Green|Yellow|Red|Gray)\b([^\r\n]*)", text, re.IGNORECASE | re.MULTILINE)
    label = signal.group(1).capitalize() if signal else "Gray"
    state = {"Green": "completed", "Yellow": "waiting", "Red": "failed", "Gray": "gray"}.get(label, "gray")
    tail = signal.group(2).strip() if signal else "— explicit traffic-light assessment unavailable"
    headline = f"{label} {tail}"
    review = re.search(r"^review_after:\s*([^\r\n]+)", text, re.MULTILINE)
    valid = re.search(r"^valid_as_of:\s*([^\r\n]+)", text, re.MULTILINE)
    next_section = re.search(r"^## Next actions\s*(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    action_count = len(re.findall(r"^\d+\.\s+", next_section.group(1), re.MULTILINE)) if next_section else 0
    return {"state": state, "label": label, "headline": headline, "review_after": review.group(1).strip() if review else None, "valid_as_of": valid.group(1).strip() if valid else None, "next_action_count": action_count}


class VaultIndexer:
    def __init__(self, config: dict[str, Any], store: EventStore) -> None:
        self.config = config
        self.store = store

    def refresh(self) -> list[dict[str, Any]]:
        snapshots = [self.inspect(entry) for entry in self.config.get("vaults", [])]
        for snapshot in snapshots:
            self.store.save_vault_snapshot(snapshot)
        return snapshots

    def inspect(self, entry: dict[str, Any]) -> dict[str, Any]:
        root = Path(str(entry.get("path", "")))
        snapshot: dict[str, Any] = {
            "key": str(entry.get("key") or root.name.lower() or "unknown"),
            "name": str(entry.get("name") or root.name or "Unknown vault"),
            "path": str(root),
            "captured_at": utc_now(),
            "exists": root.is_dir(),
            "state": "gray",
            "reason": "vault missing",
            "project": {},
            "sources": [],
            "authority": {},
            "records": {},
            "freshness": {},
            "contradictions": [],
        }
        if not root.is_dir():
            return snapshot
        profile_path = root / "project-ops.json"
        try:
            profile = read_json(profile_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            snapshot["reason"] = f"profile unavailable: {error.__class__.__name__}"
            return snapshot
        project = profile.get("project") if isinstance(profile.get("project"), dict) else {}
        sources = profile.get("sources") if isinstance(profile.get("sources"), dict) else {}
        authority = profile.get("authority") if isinstance(profile.get("authority"), dict) else {}
        tolerances = profile.get("tolerances") if isinstance(profile.get("tolerances"), dict) else {}
        stale_days = int(tolerances.get("volatile_source_max_age_days") or 7)
        current_candidates = list(root.glob("wiki/**/current.md"))
        portfolio_candidates = list(root.glob("wiki/**/portfolio-summary.md"))
        current = max(current_candidates, key=lambda item: item.stat().st_mtime) if current_candidates else root / "wiki" / snapshot["key"] / "current.md"
        portfolio = max(portfolio_candidates, key=lambda item: item.stat().st_mtime) if portfolio_candidates else root / "wiki" / snapshot["key"] / "portfolio-summary.md"
        current_state = file_state(current, stale_days)
        profile_state = file_state(profile_path, stale_days * 4)
        dashboard_files = list((root / "dashboards").glob("*")) if (root / "dashboards").is_dir() else []
        record_root = root / "wiki" / snapshot["key"] / "pm" / "records"
        operational_counts = {}
        if record_root.is_dir():
            for directory in sorted(path for path in record_root.iterdir() if path.is_dir()):
                operational_counts[directory.name] = len(list(directory.glob("*.md")))
        signal = current_signal(current)
        snapshot.update(
            {
                "state": "completed" if current_state["state"] == "completed" else "gray",
                "reason": "indexed" if current_state["state"] == "completed" else f"current record {current_state['reason']}",
                "project": {
                    "key": project.get("key") or snapshot["key"],
                    "name": project.get("name") or snapshot["name"],
                    "client": project.get("client"),
                    "stage": project.get("stage") or "unknown",
                    "next_milestone": project.get("next_milestone") or "No verified milestone",
                    "sensitivity": project.get("sensitivity") or "unknown",
                },
                "sources": [
                    {
                        "name": name,
                        "state": "gray",
                        "authority_for": [claim for claim, owner in authority.items() if owner == name or str(owner).startswith(f"{name}.")],
                        "mode": value.get("access") if isinstance(value, dict) else "configured-only",
                        "reason": "configured identity; live connector freshness unavailable",
                    }
                    for name, value in sorted(sources.items())
                ],
                "authority": authority,
                "records": {
                    "dashboard_count": len(dashboard_files),
                    "base_count": len([path for path in dashboard_files if path.suffix == ".base"]),
                    "current": str(current) if current.exists() else None,
                    "portfolio_summary": str(portfolio) if portfolio.exists() else None,
                    "operational_counts": operational_counts,
                },
                "freshness": {"profile": profile_state, "current": current_state, "portfolio": file_state(portfolio, stale_days * 4)},
                "health": signal,
                "contradictions": [
                    str(item) for item in (profile.get("onboarding", {}).get("known_risks", []) if isinstance(profile.get("onboarding"), dict) else [])
                ],
            }
        )
        return snapshot

    def fingerprint(self) -> str:
        material = []
        for entry in self.config.get("vaults", []):
            root = Path(str(entry.get("path", "")))
            candidates = [root / "project-ops.json"]
            candidates.extend(root.glob("wiki/**/current.md"))
            candidates.extend(root.glob("wiki/**/portfolio-summary.md"))
            candidates.extend((root / "dashboards").glob("*")) if (root / "dashboards").is_dir() else None
            for path in sorted(set(candidates), key=lambda item: str(item).lower()):
                try:
                    stat = path.stat()
                    material.append((str(path), stat.st_mtime_ns, stat.st_size))
                except OSError:
                    material.append((str(path), None, None))
        return stable_id("vault-fingerprint", material)


class VaultWatcher:
    def __init__(self, app: "Application", interval: float = 2.0) -> None:
        self.app = app
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True, name="poppy-vault-watcher")
        self.last_fingerprint = app.indexer.fingerprint()

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=self.interval + 2)

    def _run(self) -> None:
        while not self.stop_event.wait(self.interval):
            fingerprint = self.app.indexer.fingerprint()
            if fingerprint != self.last_fingerprint:
                self.last_fingerprint = fingerprint
                self.app.refresh()


class CapabilityGraph:
    def __init__(self, path: str | Path) -> None:
        candidate = Path(path)
        self.path = candidate if candidate.is_absolute() else ROOT / candidate

    def read(self) -> dict[str, Any]:
        try:
            graph = read_json(self.path)
            return {
                "state": "completed",
                "graph_id": graph.get("graph_id"),
                "schema_version": graph.get("schema_version"),
                "nodes": graph.get("nodes", []),
                "edges": graph.get("edges", []),
                "path": str(self.path),
                "digest": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            }
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return {"state": "gray", "reason": f"capability graph unavailable: {error.__class__.__name__}", "nodes": [], "edges": [], "path": str(self.path)}


def findings(events: Iterable[dict[str, Any]], vaults: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    events = list(events)
    result: list[dict[str, Any]] = []
    by_tool: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_capability: dict[str, list[tuple[dict[str, Any], int]]] = {}
    for event in events:
        if event.get("tool"):
            by_tool.setdefault((event.get("run_id", ""), event["tool"]), []).append(event)
        if event.get("capability") and isinstance(event.get("duration_ms"), int):
            by_capability.setdefault(event["capability"], []).append((event, event["duration_ms"]))
        if event.get("status") in {"failed", "blocked"}:
            refs = [{"type": "event", "id": event["event_id"], "run_id": event.get("run_id"), "project": event.get("project"), "label": event.get("message") or event.get("kind")}]
            result.append({"id": stable_id("finding", ["failure", event["event_id"]]), "severity": "high", "kind": "execution-failure", "message": event.get("message"), "event_ids": [event["event_id"]], "references": refs, "action": "Open the linked trace and resolve or explicitly accept the failed step."})
    for (run_id, tool), items in by_tool.items():
        if len(items) >= 3:
            refs = [{"type": "event", "id": item["event_id"], "run_id": item.get("run_id"), "project": item.get("project"), "label": item.get("message") or tool} for item in items]
            result.append({"id": stable_id("finding", ["repeat", run_id, tool]), "severity": "medium", "kind": "repeated-tool", "message": f"{tool} was called {len(items)} times in {run_id}; inspect query overlap.", "event_ids": [item["event_id"] for item in items], "references": refs, "action": "Compare the linked calls and consolidate overlapping logical requests."})
    for capability, samples in by_capability.items():
        if len(samples) >= 3:
            durations = [duration for _, duration in samples]
            ordered = sorted(durations)
            median = ordered[len(ordered) // 2]
            maximum = max(durations)
            if median and maximum > median * 1.6:
                slow_events = [event for event, duration in samples if duration == maximum]
                refs = [{"type": "event", "id": event["event_id"], "run_id": event.get("run_id"), "project": event.get("project"), "label": event.get("message") or capability} for event in slow_events]
                result.append({"id": stable_id("finding", ["slow", capability, maximum]), "severity": "medium", "kind": "duration-regression", "message": f"{capability} peaked at {maximum} ms versus a {median} ms recent median.", "event_ids": [event["event_id"] for event in slow_events], "references": refs, "action": "Inspect the slowest linked step and compare its evidence and tool activity with the median run."})
    for vault in vaults:
        if vault.get("state") == "gray":
            refs = [{"type": "source", "id": vault.get("key"), "project": vault.get("key"), "locator": vault.get("path"), "label": vault.get("name") or vault.get("key"), "state": "gray"}]
            result.append({"id": stable_id("finding", ["vault", vault.get("key"), vault.get("reason")]), "severity": "medium", "kind": "stale-or-missing-vault", "message": f"{vault.get('name')} is Gray: {vault.get('reason')}.", "event_ids": [], "references": refs, "action": "Open the linked vault source and restore or explicitly retire the missing evidence surface."})
        for contradiction in vault.get("contradictions", []):
            refs = [{"type": "source", "id": vault.get("key"), "project": vault.get("key"), "locator": vault.get("path"), "label": vault.get("name") or vault.get("key"), "state": vault.get("state") or "gray"}]
            result.append({"id": stable_id("finding", ["contradiction", vault.get("key"), contradiction]), "severity": "low", "kind": "preserved-contradiction", "message": contradiction, "event_ids": [], "references": refs, "action": "Review the linked source and preserve or resolve the contradiction with authoritative evidence."})
    return result[:100]


def validate_mcp_isolation(config: dict[str, Any], configured_names: Iterable[str]) -> dict[str, Any]:
    allowed_local = {str(item) for item in config.get("allowed_local_mcp_servers", [])}
    disabled_remote = {str(item) for item in config.get("disabled_remote_mcp_servers", [])}
    names = {str(item) for item in configured_names}
    unexpected = sorted(names - allowed_local - disabled_remote)
    launch_args = config.get("launch_args") if isinstance(config.get("launch_args"), list) else []
    missing_overrides = [name for name in sorted(disabled_remote) if not any(f"mcp_servers.{name}=" in str(arg) and "enabled=false" in str(arg) for arg in launch_args)]
    if unexpected:
        raise RuntimeError(f"Refusing Codex launch with unclassified MCP servers: {', '.join(unexpected)}")
    if missing_overrides:
        raise RuntimeError(f"Refusing Codex launch without disabled remote MCP overrides: {', '.join(missing_overrides)}")
    return {"allowed_local": sorted(allowed_local & names), "disabled_remote": sorted(disabled_remote & names), "unexpected": []}


def validate_thread_controls(response: dict[str, Any], expected_thread_id: str | None = None) -> dict[str, Any]:
    if "error" in response:
        raise RuntimeError(f"Codex thread request failed: {response['error']}")
    result = response.get("result") if isinstance(response.get("result"), dict) else {}
    thread = result.get("thread") if isinstance(result.get("thread"), dict) else {}
    thread_id = str(thread.get("id") or "")
    if not thread_id or (expected_thread_id and thread_id != expected_thread_id):
        raise RuntimeError("Codex returned a missing or mismatched dashboard thread identity")
    sandbox = result.get("sandbox") if isinstance(result.get("sandbox"), dict) else {}
    if result.get("approvalPolicy") != "never" or sandbox.get("type") != "readOnly":
        raise RuntimeError("Codex thread controls are Gray: read-only sandbox and never approval were not confirmed")
    if thread.get("threadSource") != "appServer":
        raise RuntimeError("Codex thread is not owned by the supported App Server surface")
    return {"thread_id": thread_id, "thread": thread, "approval_policy": "never", "sandbox": "readOnly"}


class CodexAppServerClient:
    """Bounded official App Server stdio client.

    It can initialize and create/resume read-only dashboard-owned threads. It does
    not submit a turn: the dock records a draft and leaves execution to a future
    approval-aware surface, preventing an unreviewed prompt from invoking tools.
    """

    def __init__(self, config: dict[str, Any], on_event, on_owned_thread=None) -> None:
        self.config = config
        self.on_event = on_event
        self.on_owned_thread = on_owned_thread
        self.process: subprocess.Popen[str] | None = None
        self.reader: threading.Thread | None = None
        self.stderr_reader: threading.Thread | None = None
        self.responses: dict[int, queue.Queue] = {}
        self.sequence = 0
        self.lock = threading.RLock()
        self.interface_state = "supported" if config.get("compatibility") == "supported" else "gray"
        self.connection_state = "disconnected"
        self.last_error: str | None = None
        self.user_agent: str | None = None
        self.thread_ids: list[str] = []

    def status(self) -> dict[str, Any]:
        executable = Path(str(self.config.get("executable", "")))
        return {
            "interface": self.config.get("interface"),
            "interface_state": self.interface_state,
            "connection_state": self.connection_state,
            "executable_available": executable.is_file(),
            "version": self.config.get("verified_version"),
            "user_agent": self.user_agent,
            "last_error": self.last_error,
            "thread_ids": self.thread_ids[-10:],
            "decision_receipt": self.config.get("decision_receipt"),
            "turn_submission": "disabled-by-authority-boundary",
            "external_mcp_policy": self.config.get("external_mcp_policy") or "gray",
        }

    def ensure_started(self) -> dict[str, Any]:
        with self.lock:
            if self.process and self.process.poll() is None and self.connection_state == "connected":
                return self.status()
            if not self.config.get("launch_enabled"):
                raise RuntimeError("Codex launch is disabled")
            executable = Path(str(self.config.get("executable", "")))
            if not executable.is_file():
                raise RuntimeError("Supported Codex executable is unavailable")
            mcp_check = subprocess.run(
                [str(executable), "mcp", "list"], cwd=ROOT, text=True, capture_output=True, encoding="utf-8", timeout=12,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
            )
            if mcp_check.returncode:
                raise RuntimeError("Could not verify configured MCP isolation through the official Codex CLI")
            configured_names = []
            for line in mcp_check.stdout.splitlines():
                match = re.match(r"^([A-Za-z0-9_.-]+)\s{2,}", line)
                if match and match.group(1) != "Name":
                    configured_names.append(match.group(1))
            isolation = validate_mcp_isolation(self.config, configured_names)
            startup = {"stdin": subprocess.PIPE, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8", "bufsize": 1, "cwd": str(ROOT)}
            if os.name == "nt":
                startup["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            launch_args = self.config.get("launch_args")
            if not isinstance(launch_args, list) or not all(isinstance(item, str) for item in launch_args):
                raise RuntimeError("Codex App Server launch arguments are missing or malformed")
            if "app-server" not in launch_args or "--stdio" not in launch_args:
                raise RuntimeError("Codex integration must use the declared App Server stdio surface")
            self.process = subprocess.Popen([str(executable), *launch_args], **startup)
            self.connection_state = "connecting"
            self.reader = threading.Thread(target=self._read_stdout, daemon=True, name="codex-appserver-stdout")
            self.stderr_reader = threading.Thread(target=self._read_stderr, daemon=True, name="codex-appserver-stderr")
            self.reader.start()
            self.stderr_reader.start()
            response = self.request("initialize", {"clientInfo": {"name": "poppy-ops-cockpit", "title": "Poppy Ops Cockpit", "version": "0.1.0"}, "capabilities": {"experimentalApi": False}}, timeout=12)
            if "error" in response:
                raise RuntimeError(f"Codex initialize failed: {response['error']}")
            self.user_agent = response.get("result", {}).get("userAgent")
            self.notify("initialized", {})
            self.connection_state = "connected"
            self.on_event({"kind": "codex.initialize", "status": "completed", "run_id": "codex-appserver", "project": "portfolio", "message": "Official Codex App Server initialized", "metadata": {"user_agent": self.user_agent, "interface": "stdio-jsonrpc", "mcp_isolation": isolation}})
            return self.status()

    def request(self, method: str, params: dict[str, Any], timeout: float = 15) -> dict[str, Any]:
        if not self.process or not self.process.stdin:
            raise RuntimeError("Codex App Server is not running")
        self.sequence += 1
        request_id = self.sequence
        result_queue: queue.Queue = queue.Queue(maxsize=1)
        self.responses[request_id] = result_queue
        self._write({"id": request_id, "method": method, "params": params})
        try:
            return result_queue.get(timeout=timeout)
        except queue.Empty as error:
            self.responses.pop(request_id, None)
            raise RuntimeError(f"Codex App Server timed out on {method}") from error

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._write({"method": method, "params": params})

    def _write(self, payload: dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            raise RuntimeError("Codex App Server stdin is unavailable")
        self.process.stdin.write(json_dumps(payload) + "\n")
        self.process.stdin.flush()

    def create_thread(self, draft: str = "") -> dict[str, Any]:
        self.ensure_started()
        response = self.request(
            "thread/start",
            {"cwd": str(ROOT), "approvalPolicy": "never", "sandbox": "read-only", "ephemeral": False, "threadSource": "appServer"},
            timeout=30,
        )
        validated = validate_thread_controls(response)
        thread_id = validated["thread_id"]
        if self.on_owned_thread:
            self.on_owned_thread(thread_id, {"approval_policy": validated["approval_policy"], "sandbox": validated["sandbox"], "thread_source": "appServer"})
        self.thread_ids.append(thread_id)
        self.on_event({"kind": "codex.thread.prepared", "status": "waiting", "run_id": thread_id or "codex-appserver", "project": "portfolio", "message": "Dashboard-owned read-only Codex task prepared; draft not submitted", "worker": "codex-appserver", "approval": "turn-not-authorized", "metadata": {"thread_id": thread_id, "draft": draft, "draft_submitted": False}})
        return {"thread_id": thread_id, "status": "waiting", "draft_submitted": False, "next_action": "Copy the draft and continue the task in an approval-aware Codex surface."}

    def resume_thread(self, thread_id: str, draft: str = "") -> dict[str, Any]:
        if thread_id not in self.thread_ids:
            raise RuntimeError("Refusing to resume a thread not created and owned by this dashboard adapter")
        self.ensure_started()
        response = self.request("thread/resume", {"threadId": thread_id}, timeout=30)
        validate_thread_controls(response, expected_thread_id=thread_id)
        self.on_event({"kind": "codex.thread.resumed", "status": "waiting", "run_id": thread_id, "project": "portfolio", "message": "Dashboard-owned Codex task resumed; draft not submitted", "worker": "codex-appserver", "approval": "turn-not-authorized", "metadata": {"thread_id": thread_id, "draft": draft, "draft_submitted": False}})
        return {"thread_id": thread_id, "status": "waiting", "draft_submitted": False, "next_action": "Copy the draft and continue in Codex."}

    def _read_stdout(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in payload and payload.get("id") in self.responses:
                self.responses.pop(payload["id"]).put(payload)
            elif payload.get("method"):
                self._handle_notification(payload)
        if self.connection_state != "stopped":
            self.connection_state = "disconnected"

    def _read_stderr(self) -> None:
        assert self.process and self.process.stderr
        for line in self.process.stderr:
            if "ERROR" in line.upper():
                self.last_error = line.strip()[:500]

    def _handle_notification(self, payload: dict[str, Any]) -> None:
        method = str(payload.get("method") or "codex.unknown")
        params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
        run_id = params.get("threadId")
        if not run_id and isinstance(params.get("thread"), dict):
            run_id = params["thread"].get("id")
        status = "current"
        lowered = method.lower()
        if "completed" in lowered or params.get("status") == "ready":
            status = "completed"
        elif "failed" in lowered or params.get("status") == "failed":
            status = "failed"
        elif "approval" in lowered:
            status = "waiting"
        safe_metadata: dict[str, Any] = {"method": method}
        for key in ("threadId", "turnId", "itemId", "status", "name", "durationMs", "model"):
            if key in params and isinstance(params[key], (str, int, float, bool, type(None))):
                safe_metadata[key] = params[key]
        if isinstance(params.get("thread"), dict):
            thread = params["thread"]
            safe_metadata["thread"] = {
                key: thread.get(key) for key in ("id", "ephemeral", "threadSource", "source", "status") if key in thread
            }
        usage = params.get("usage") or params.get("tokenUsage")
        event_tokens = normalize_tokens(usage)
        if method.lower().startswith("reasoning"):
            safe_metadata["content_redacted"] = "hidden-reasoning-boundary"
        self.on_event({"kind": method, "status": status, "run_id": run_id or "codex-appserver", "project": "portfolio", "message": method, "worker": "codex-appserver", "durationMs": params.get("durationMs"), "tokens": event_tokens, "emittedAtMs": payload.get("emittedAtMs"), "metadata": safe_metadata})

    def stop(self) -> None:
        with self.lock:
            if self.process and self.process.poll() is None:
                self.connection_state = "stopped"
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)


@dataclass
class Application:
    config: dict[str, Any]
    store: EventStore
    indexer: VaultIndexer
    graph: CapabilityGraph
    codex: CodexAppServerClient
    subscribers: set[queue.Queue]
    vaults: list[dict[str, Any]]

    @classmethod
    def create(cls, config_path: Path = DEFAULT_CONFIG, ledger: Path = LEDGER, database: Path = DATABASE) -> "Application":
        config = read_json(config_path)
        store = EventStore(ledger, database)
        subscribers: set[queue.Queue] = set()
        placeholder = cls(config, store, VaultIndexer(config, store), CapabilityGraph(config.get("capability_graph", "")), None, subscribers, [])  # type: ignore[arg-type]
        placeholder.codex = CodexAppServerClient(config.get("codex", {}), placeholder.record_event, store.register_owned_thread)
        placeholder.codex.thread_ids = store.owned_thread_ids()
        placeholder.vaults = placeholder.indexer.refresh()
        return placeholder

    def record_event(self, raw: dict[str, Any]) -> dict[str, Any]:
        event, created = self.store.append(raw)
        if created:
            for subscriber in tuple(self.subscribers):
                try:
                    subscriber.put_nowait(event)
                except queue.Full:
                    self.subscribers.discard(subscriber)
        return event

    def refresh(self) -> dict[str, Any]:
        self.vaults = self.indexer.refresh()
        event = self.record_event({"kind": "vault.refresh", "status": "completed" if all(v["exists"] for v in self.vaults) else "gray", "run_id": f"refresh-{datetime.now(timezone.utc).date().isoformat()}", "project": "portfolio", "message": "Local read-only vault index refreshed", "evidence": [{"source": v["name"], "locator": v["path"], "freshness": v["freshness"].get("current", {}).get("reason", "unknown"), "authority": "compiled-memory", "contradiction": bool(v["contradictions"]), "state": v["state"]} for v in self.vaults]})
        return {"captured_at": utc_now(), "vaults": self.vaults, "event": event}

    def state(self) -> dict[str, Any]:
        recent_events = self.store.events(500)
        return {
            "schema_version": 1,
            "captured_at": utc_now(),
            "service": {"state": "completed", "bind": self.config.get("bind"), "port": self.config.get("port"), "storage": {"ledger": str(self.store.ledger), "database": str(self.store.database)}},
            "codex": self.codex.status(),
            "vaults": self.vaults,
            "graph": self.graph.read(),
            "runs": self.store.runs(),
            "events": recent_events,
            "findings": findings(recent_events, self.vaults),
            "controls": {"vault_writes": "disabled", "external_writes": "disabled", "local_refresh": "read-only-index", "dock_turn_submission": "disabled"},
        }


class Handler(BaseHTTPRequestHandler):
    server_version = "PoppyOpsBridge/0.1"

    @property
    def app(self) -> Application:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[{utc_now()}] {self.address_string()} {fmt % args}\n")

    def _headers(self, status: int = 200, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.end_headers()

    def _json(self, value: Any, status: int = 200) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self._headers(status)
        self.wfile.write(payload)

    def _body(self, limit: int = 32_768) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid Content-Length") from error
        if length <= 0 or length > limit:
            raise ValueError("JSON body is required and must be bounded")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def _post_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        client = self.headers.get("X-Poppy-Ops-Client")
        return client == "obsidian-plugin" and (not origin or origin.startswith("app://obsidian"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self._json({"state": "completed", "service": "poppy-ops-bridge", "time": utc_now()})
        elif parsed.path == "/api/state":
            self._json(self.app.state())
        elif parsed.path == "/api/events":
            query = urllib.parse.parse_qs(parsed.query)
            self._json({"events": self.app.store.events(int(query.get("limit", ["300"])[0]), query.get("run_id", [None])[0])})
        elif parsed.path == "/events":
            self._sse()
        else:
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if not self._post_allowed():
            self._json({"error": "Obsidian client header required"}, HTTPStatus.FORBIDDEN)
            return
        try:
            body = self._body()
            if self.path == "/api/refresh":
                self._json(self.app.refresh())
            elif self.path == "/api/event":
                self._json({"event": self.app.record_event(body)}, HTTPStatus.CREATED)
            elif self.path == "/api/codex/connect":
                self._json({"codex": self.app.codex.ensure_started()})
            elif self.path == "/api/dock":
                draft = str(body.get("draft") or "")[:12_000]
                thread_id = str(body.get("thread_id") or "").strip()
                result = self.app.codex.resume_thread(thread_id, draft) if thread_id else self.app.codex.create_thread(draft)
                self._json(result, HTTPStatus.CREATED)
            else:
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as error:
            self._json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as error:
            self._json({"error": str(error), "state": "gray"}, HTTPStatus.SERVICE_UNAVAILABLE)

    def _sse(self) -> None:
        subscriber: queue.Queue = queue.Queue(maxsize=100)
        self.app.subscribers.add(subscriber)
        self._headers(200, "text/event-stream; charset=utf-8")
        try:
            self.wfile.write(b"event: ready\ndata: {\"state\":\"completed\"}\n\n")
            self.wfile.flush()
            deadline = time.monotonic() + 55
            while time.monotonic() < deadline:
                try:
                    event = subscriber.get(timeout=10)
                    self.wfile.write(f"event: poppy\ndata: {json_dumps(event)}\n\n".encode("utf-8"))
                except queue.Empty:
                    self.wfile.write(b": keepalive\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.app.subscribers.discard(subscriber)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, app: Application):
        super().__init__(address, Handler)
        self.app = app


def serve(config_path: Path, ledger: Path, database: Path) -> int:
    app = Application.create(config_path, ledger, database)
    bind = str(app.config.get("bind") or "127.0.0.1")
    if bind not in {"127.0.0.1", "localhost"}:
        raise SystemExit("Refusing non-loopback bind")
    port = int(app.config.get("port") or 7317)
    server = Server((bind, port), app)
    watcher = VaultWatcher(app)
    watcher.start()
    print(f"Poppy Ops Bridge listening on http://{bind}:{port}", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        watcher.stop()
        app.codex.stop()
        server.server_close()
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("serve", "refresh", "replay", "state"), nargs="?", default="serve")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    parser.add_argument("--database", type=Path, default=DATABASE)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args(argv)
    if args.command == "serve":
        return serve(args.config, args.ledger, args.database)
    app = Application.create(args.config, args.ledger, args.database)
    if args.command == "refresh":
        print(json.dumps(app.refresh(), ensure_ascii=False, indent=2))
    elif args.command == "replay":
        print(json.dumps(app.store.replay(args.source), indent=2))
    elif args.command == "state":
        print(json.dumps(app.state(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
