from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bridge.poppy_ops_bridge import CapabilityGraph, EventStore, VaultIndexer, current_signal, findings, normalize_event


ROOT = Path(__file__).resolve().parents[1]


class EventNormalizationTests(unittest.TestCase):
    def test_missing_evidence_and_cost_degrade_explicitly(self) -> None:
        event = normalize_event({"kind": "tool.finished", "status": "green", "run_id": "r1"})
        self.assertEqual(event["status"], "gray")
        self.assertEqual(event["cost"]["basis"], "unavailable")
        self.assertEqual(event["tokens"], {"input": 0, "cached": 0, "reasoning": 0, "output": 0})
        self.assertTrue(event["event_id"].startswith("evt-"))

    def test_cost_basis_is_bounded(self) -> None:
        event = normalize_event({"kind": "turn.completed", "cost": {"amount": "1.25", "basis": "invoice"}})
        self.assertEqual(event["cost"]["basis"], "unavailable")
        self.assertEqual(event["cost"]["amount"], 1.25)

    def test_contradiction_is_preserved(self) -> None:
        event = normalize_event({"kind": "evidence.read", "evidence": [{"source": "budget", "contradiction": True, "state": "completed"}]})
        self.assertTrue(event["evidence"][0]["contradiction"])


class EventStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.store = EventStore(root / "events.jsonl", root / "events.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_append_is_idempotent_and_ledger_is_append_only(self) -> None:
        raw = {"event_id": "evt-test", "kind": "run.started", "run_id": "r1", "project": "p", "status": "current"}
        _, first = self.store.append(raw)
        _, second = self.store.append(raw)
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(len(self.store.ledger.read_text(encoding="utf-8").splitlines()), 1)
        self.assertEqual(len(self.store.events()), 1)

    def test_replay_is_deterministic_and_skips_malformed(self) -> None:
        source = Path(self.temp.name) / "source.jsonl"
        source.write_text(
            "\n".join(
                [
                    json.dumps({"event_id": "a", "kind": "run.started", "run_id": "r", "project": "p", "status": "completed"}),
                    "{malformed",
                    json.dumps({"event_id": "a", "kind": "run.started", "run_id": "r", "project": "p", "status": "completed"}),
                    json.dumps({"event_id": "b", "kind": "tool.completed", "run_id": "r", "project": "p", "status": "completed", "duration_ms": 20}),
                ]
            ) + "\n",
            encoding="utf-8",
        )
        first = self.store.replay(source)
        first_rows = self.store.events()
        second = self.store.replay(source)
        self.assertEqual(first, {"accepted": 2, "malformed": 1, "duplicate": 1})
        self.assertEqual(first, second)
        self.assertEqual(first_rows, self.store.events())

    def test_run_projection_aggregates_tokens_and_status(self) -> None:
        self.store.append({"event_id": "a", "kind": "run.started", "run_id": "r", "project": "p", "status": "completed", "tokens": {"input": 3}})
        self.store.append({"event_id": "b", "kind": "tool.started", "run_id": "r", "project": "p", "status": "blocked", "tokens": {"output": 4}, "duration_ms": 5})
        run = self.store.runs()[0]
        self.assertEqual(run["status"], "blocked")
        self.assertEqual(run["tokens"]["input"], 3)
        self.assertEqual(run["tokens"]["output"], 4)
        self.assertEqual(run["duration_ms"], 5)


class VaultIndexerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = EventStore(self.root / "events.jsonl", self.root / "events.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_missing_vault_is_gray(self) -> None:
        config = {"vaults": [{"key": "missing", "name": "Missing", "path": str(self.root / "none")}]}
        vault = VaultIndexer(config, self.store).refresh()[0]
        self.assertEqual(vault["state"], "gray")
        self.assertFalse(vault["exists"])

    def test_profile_is_read_without_canonical_write(self) -> None:
        vault = self.root / "vault"
        (vault / "wiki" / "demo").mkdir(parents=True)
        (vault / "dashboards").mkdir()
        profile = {
            "project": {"key": "demo", "name": "Demo", "stage": "active", "next_milestone": "Gate", "sensitivity": "confidential"},
            "sources": {"github": {"access": "read-only"}},
            "authority": {"implementation": "github"},
            "tolerances": {"volatile_source_max_age_days": 7},
            "onboarding": {"known_risks": ["Fact A conflicts with fact B"]},
        }
        profile_path = vault / "project-ops.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")
        current = vault / "wiki" / "demo" / "current.md"
        current.write_text("# Current", encoding="utf-8")
        before = {path: path.read_bytes() for path in (profile_path, current)}
        config = {"vaults": [{"key": "demo", "name": "Demo", "path": str(vault)}]}
        snapshot = VaultIndexer(config, self.store).refresh()[0]
        after = {path: path.read_bytes() for path in (profile_path, current)}
        self.assertEqual(before, after)
        self.assertEqual(snapshot["state"], "completed")
        self.assertEqual(snapshot["sources"][0]["authority_for"], ["implementation"])
        self.assertEqual(snapshot["contradictions"], ["Fact A conflicts with fact B"])

    def test_current_signal_preserves_traffic_light_and_review(self) -> None:
        current = self.root / "current.md"
        current.write_text("---\nvalid_as_of: 2026-08-17\nreview_after: 2026-08-18\n---\n> [!danger] Red — release proof missing\n\n## Next actions\n\n1. Capture proof.\n2. Reconcile.\n", encoding="utf-8")
        signal = current_signal(current)
        self.assertEqual(signal["state"], "failed")
        self.assertEqual(signal["headline"], "Red — release proof missing")
        self.assertEqual(signal["next_action_count"], 2)
        self.assertEqual(signal["review_after"], "2026-08-18")


class GraphAndFindingTests(unittest.TestCase):
    def test_pinned_graph_is_available(self) -> None:
        graph = CapabilityGraph(ROOT / "config" / "poppy-capability-graph.json").read()
        self.assertEqual(graph["state"], "completed")
        self.assertGreater(len(graph["nodes"]), 25)
        self.assertEqual(len(graph["digest"]), 64)

    def test_findings_are_deterministic_and_link_events(self) -> None:
        events = [
            normalize_event({"event_id": f"e{i}", "kind": "tool.completed", "run_id": "r", "project": "p", "status": "completed", "tool": "vault-index"})
            for i in range(3)
        ]
        first = findings(events, [])
        second = findings(events, [])
        self.assertEqual(first, second)
        repeated = next(item for item in first if item["kind"] == "repeated-tool")
        self.assertEqual(repeated["event_ids"], ["e0", "e1", "e2"])


if __name__ == "__main__":
    unittest.main()
