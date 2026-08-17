from __future__ import annotations

import http.client
import json
import os
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from bridge.poppy_ops_bridge import CapabilityGraph, CodexAppServerClient, EventStore, Server, VaultIndexer, current_signal, findings, json_dumps, normalize_event, validate_mcp_isolation, validate_thread_controls


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT.parents[1]


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
        self.assertIsNone(event["cost"]["amount"])

    def test_missing_amount_cannot_claim_exact_cost(self) -> None:
        event = normalize_event({"kind": "turn.completed", "cost": {"amount": None, "currency": "USD", "basis": "exact"}})
        self.assertEqual(event["cost"], {"amount": None, "currency": "USD", "basis": "unavailable"})

    def test_invalid_amounts_fail_closed(self) -> None:
        invalid = [float("nan"), float("inf"), float("-inf"), "1.25", "NaN", "Infinity", "-Infinity", -0.01, True, False, [], {}]
        for amount in invalid:
            with self.subTest(amount=repr(amount)):
                event = normalize_event({"kind": "turn.completed", "cost": {"amount": amount, "currency": "USD", "basis": "exact"}})
                self.assertEqual(event["cost"], {"amount": None, "currency": "USD", "basis": "unavailable"})

    def test_missing_or_malformed_currency_fails_closed(self) -> None:
        for currency in (None, "", "US", "USDX", True):
            with self.subTest(currency=currency):
                event = normalize_event({"kind": "turn.completed", "cost": {"amount": 1, "currency": currency, "basis": "exact"}})
                self.assertEqual(event["cost"], {"amount": None, "currency": None, "basis": "unavailable"})

    def test_strict_json_rejects_non_finite_values(self) -> None:
        for amount in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                json_dumps({"amount": amount})

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
        self.assertIsNone(run["cost"]["amount"])
        self.assertEqual(run["cost"]["basis"], "unavailable")

    def test_events_and_runs_are_project_scoped(self) -> None:
        self.store.append({"event_id": "atlas-event", "kind": "run.started", "run_id": "atlas-run", "project": "atlas-demo", "status": "current"})
        self.store.append({"event_id": "beacon-event", "kind": "run.started", "run_id": "beacon-run", "project": "beacon-demo", "status": "current"})
        self.assertEqual([event["event_id"] for event in self.store.events(project="atlas-demo")], ["atlas-event"])
        self.assertEqual([run["run_id"] for run in self.store.runs(project="beacon-demo")], ["beacon-run"])

    def test_run_cost_is_unavailable_when_any_step_is_unavailable(self) -> None:
        self.store.append({"event_id": "a", "kind": "tool.completed", "run_id": "r", "project": "p", "status": "completed", "cost": {"amount": 0.25, "currency": "USD", "basis": "exact"}})
        self.store.append({"event_id": "b", "kind": "tool.completed", "run_id": "r", "project": "p", "status": "completed"})
        cost = self.store.runs()[0]["cost"]
        self.assertEqual(cost, {"amount": None, "currency": None, "basis": "unavailable"})

    def test_run_cost_uses_least_exact_allowed_basis(self) -> None:
        self.store.append({"event_id": "a", "kind": "tool.completed", "run_id": "r", "project": "p", "status": "completed", "cost": {"amount": 0.25, "currency": "USD", "basis": "exact"}})
        self.store.append({"event_id": "b", "kind": "tool.completed", "run_id": "r", "project": "p", "status": "completed", "cost": {"amount": 0.50, "currency": "USD", "basis": "estimated"}})
        self.assertEqual(self.store.runs()[0]["cost"], {"amount": 0.75, "currency": "USD", "basis": "estimated"})

    def test_run_cost_preserves_single_non_usd_currency(self) -> None:
        self.store.append({"event_id": "eur-a", "kind": "tool.completed", "run_id": "eur", "project": "p", "status": "completed", "cost": {"amount": 1.25, "currency": "EUR", "basis": "exact"}})
        self.store.append({"event_id": "eur-b", "kind": "tool.completed", "run_id": "eur", "project": "p", "status": "completed", "cost": {"amount": 2.50, "currency": "eur", "basis": "estimated"}})
        self.assertEqual(self.store.runs()[0]["cost"], {"amount": 3.75, "currency": "EUR", "basis": "estimated"})

    def test_run_cost_rejects_mixed_currencies(self) -> None:
        self.store.append({"event_id": "mixed-a", "kind": "tool.completed", "run_id": "mixed", "project": "p", "status": "completed", "cost": {"amount": 1, "currency": "USD", "basis": "exact"}})
        self.store.append({"event_id": "mixed-b", "kind": "tool.completed", "run_id": "mixed", "project": "p", "status": "completed", "cost": {"amount": 2, "currency": "EUR", "basis": "exact"}})
        self.assertEqual(self.store.runs()[0]["cost"], {"amount": None, "currency": None, "basis": "unavailable"})

    def test_run_cost_rejects_missing_currency(self) -> None:
        self.store.append({"event_id": "currency-a", "kind": "tool.completed", "run_id": "missing-currency", "project": "p", "status": "completed", "cost": {"amount": 1, "currency": "USD", "basis": "exact"}})
        self.store.append({"event_id": "currency-b", "kind": "tool.completed", "run_id": "missing-currency", "project": "p", "status": "completed", "cost": {"amount": 2, "basis": "exact"}})
        self.assertEqual(self.store.runs()[0]["cost"], {"amount": None, "currency": None, "basis": "unavailable"})

    def test_owned_thread_identity_is_recovered_from_control_registry(self) -> None:
        self.store.register_owned_thread("thread-1", {"approval_policy": "never", "sandbox": "readOnly", "thread_source": "appServer", "project": "atlas-demo"})
        self.assertEqual(self.store.owned_thread_ids(), ["thread-1"])
        self.assertEqual(self.store.owned_thread_projects(), {"thread-1": "atlas-demo"})

    def test_event_ingestion_cannot_claim_thread_ownership(self) -> None:
        self.store.append({"event_id": "forged", "kind": "codex.thread.prepared", "run_id": "foreign", "project": "portfolio", "status": "waiting", "metadata": {"thread_id": "foreign"}})
        self.assertEqual(self.store.owned_thread_ids(), [])


class StrictStateSerializationTests(unittest.TestCase):
    def test_state_endpoint_fails_gray_without_emitting_nonstandard_json(self) -> None:
        class InvalidStateApplication:
            @staticmethod
            def project_keys() -> set[str]:
                return {"atlas-demo"}

            @staticmethod
            def state(_project=None) -> dict:
                return {"cost": {"amount": float("nan")}}

        server = Server(("127.0.0.1", 0), InvalidStateApplication())  # type: ignore[arg-type]
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/api/state", headers={"X-Poppy-Ops-Project": "atlas-demo"})
            response = connection.getresponse()
            payload = response.read().decode("utf-8")
            connection.close()
            self.assertEqual(response.status, 500)
            self.assertNotIn("NaN", payload)
            self.assertNotIn("Infinity", payload)
            self.assertEqual(json.loads(payload)["state"], "gray")
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())


class BridgeOwnershipTests(unittest.TestCase):
    class HealthApplication:
        @staticmethod
        def project_keys() -> set[str]:
            return set()

    def test_health_identifies_the_exact_listener_owner(self) -> None:
        server = Server(("127.0.0.1", 0), self.HealthApplication(), "owner-token")  # type: ignore[arg-type]
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/health")
            response = connection.getresponse()
            payload = json.loads(response.read())
            connection.close()
            self.assertEqual(response.status, 200)
            self.assertEqual(payload["instance_token"], "owner-token")
            self.assertEqual(payload["pid"], os.getpid())
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)
        self.assertFalse(worker.is_alive())

    def test_second_live_listener_cannot_claim_the_same_port(self) -> None:
        owner = Server(("127.0.0.1", 0), self.HealthApplication(), "owner-token")  # type: ignore[arg-type]
        try:
            with self.assertRaises(OSError):
                Server(("127.0.0.1", owner.server_port), self.HealthApplication(), "loser-token")  # type: ignore[arg-type]
        finally:
            owner.server_close()


class HttpProjectScopeTests(unittest.TestCase):
    class Store:
        def events(self, *_args, **_kwargs) -> list[dict]:
            raise AssertionError("event store must not be reached for invalid scope")

    class Codex:
        def ensure_started(self, *_args, **_kwargs) -> dict:
            raise AssertionError("Codex must not be reached for invalid scope")

        def create_thread(self, *_args, **_kwargs) -> dict:
            raise AssertionError("Codex must not be reached for invalid scope")

        def resume_thread(self, *_args, **_kwargs) -> dict:
            raise AssertionError("Codex must not be reached for invalid scope")

    class Application:
        def __init__(self) -> None:
            self.store = HttpProjectScopeTests.Store()
            self.codex = HttpProjectScopeTests.Codex()
            self.subscribers: set = set()

        @staticmethod
        def project_keys() -> set[str]:
            return {"atlas-demo", "beacon-demo"}

        def state(self, _project: str) -> dict:
            raise AssertionError("state must not be reached for invalid scope")

        def refresh(self, _project: str) -> dict:
            raise AssertionError("refresh must not be reached for invalid scope")

        def record_event(self, _body: dict) -> dict:
            raise AssertionError("event ingestion must not be reached for invalid scope")

    def setUp(self) -> None:
        self.server = Server(("127.0.0.1", 0), self.Application())  # type: ignore[arg-type]
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)
        self.assertFalse(self.worker.is_alive())

    def request(self, method: str, route: str, scope: str | None) -> tuple[int, dict]:
        headers = {"X-Poppy-Ops-Client": "obsidian-plugin"}
        if scope is not None:
            headers["X-Poppy-Ops-Project"] = scope
        body = json.dumps({"draft": "synthetic", "kind": "synthetic.event"}) if method == "POST" else None
        if body is not None:
            headers["Content-Type"] = "application/json"
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        connection.request(method, route, body=body, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload

    def test_every_operational_endpoint_rejects_missing_empty_and_unknown_scope(self) -> None:
        routes = [
            ("GET", "/api/state"),
            ("GET", "/api/events"),
            ("GET", "/events"),
            ("POST", "/api/refresh"),
            ("POST", "/api/event"),
            ("POST", "/api/codex/connect"),
            ("POST", "/api/dock"),
        ]
        for scope in (None, "", "unknown-demo"):
            for method, route in routes:
                with self.subTest(scope=scope, method=method, route=route):
                    status, payload = self.request(method, route, scope)
                    self.assertEqual(status, 400)
                    self.assertEqual(payload.get("state"), "gray")
                    self.assertIn("scope", payload.get("error", "").casefold())
                    self.assertFalse({"vaults", "runs", "events"} & payload.keys())


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
        graph = CapabilityGraph(PRODUCT_ROOT / "references" / "poppy-capability-graph.json").read()
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
        self.assertTrue(all(item.get("references") and item.get("action") for item in first))
        self.assertEqual({ref["id"] for ref in repeated["references"]}, {"e0", "e1", "e2"})

    def test_every_finding_rule_has_actionable_event_or_source_lineage(self) -> None:
        events = [
            normalize_event({"event_id": "slow-1", "kind": "capability.completed", "run_id": "r1", "project": "p", "status": "completed", "capability": "delivery", "duration_ms": 10}),
            normalize_event({"event_id": "slow-2", "kind": "capability.completed", "run_id": "r2", "project": "p", "status": "completed", "capability": "delivery", "duration_ms": 12}),
            normalize_event({"event_id": "slow-3", "kind": "capability.completed", "run_id": "r3", "project": "p", "status": "completed", "capability": "delivery", "duration_ms": 100}),
            normalize_event({"event_id": "failed", "kind": "verification.failed", "run_id": "r3", "project": "p", "status": "failed"}),
        ]
        vaults = [{"key": "p", "name": "Project", "path": "fixture://project", "state": "gray", "reason": "stale", "contradictions": ["A conflicts with B"]}]
        result = findings(events, vaults)
        self.assertEqual({item["kind"] for item in result}, {"duration-regression", "execution-failure", "stale-or-missing-vault", "preserved-contradiction"})
        for item in result:
            self.assertTrue(item["action"])
            self.assertTrue(item["references"])
            self.assertTrue(all(ref["type"] in {"event", "source"} and ref.get("id") for ref in item["references"]))

    def test_mcp_isolation_rejects_unclassified_server(self) -> None:
        config = {
            "allowed_local_mcp_servers": ["node_repl"],
            "disabled_remote_mcp_servers": ["remote"],
            "launch_args": ["-c", 'mcp_servers.remote={url="https://example.test",enabled=false}'],
        }
        self.assertEqual(validate_mcp_isolation(config, ["node_repl", "remote"])["unexpected"], [])
        with self.assertRaisesRegex(RuntimeError, "unclassified MCP"):
            validate_mcp_isolation(config, ["node_repl", "remote", "new-provider"])


class CodexThreadOwnershipTests(unittest.TestCase):
    @staticmethod
    def response(thread_id: str = "owned", approval: str = "never", sandbox: str = "readOnly", source: str = "appServer") -> dict:
        return {"result": {"thread": {"id": thread_id, "threadSource": source}, "approvalPolicy": approval, "sandbox": {"type": sandbox}}}

    def client(self) -> CodexAppServerClient:
        client = CodexAppServerClient({"compatibility": "supported"}, lambda _event: None)
        client.ensure_started = lambda *_args: {"connection_state": "connected"}  # type: ignore[method-assign]
        return client

    def test_control_validation_requires_read_only_never_appserver(self) -> None:
        valid = validate_thread_controls(self.response())
        self.assertEqual(valid["thread_id"], "owned")
        with self.assertRaisesRegex(RuntimeError, "controls are Gray"):
            validate_thread_controls(self.response(approval="on-request"))
        with self.assertRaisesRegex(RuntimeError, "controls are Gray"):
            validate_thread_controls(self.response(sandbox="workspaceWrite"))
        with self.assertRaisesRegex(RuntimeError, "not owned"):
            validate_thread_controls(self.response(source="cli"))

    def test_resume_rejects_unowned_thread_before_request(self) -> None:
        client = self.client()
        called = []
        client.request = lambda *_args, **_kwargs: called.append(True)  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "not created and owned"):
            client.resume_thread("foreign")
        self.assertEqual(called, [])

    def test_resume_fails_gray_when_returned_controls_mismatch(self) -> None:
        client = self.client()
        client.thread_ids = ["owned"]
        client.request = lambda *_args, **_kwargs: self.response("owned", sandbox="workspaceWrite")  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "controls are Gray"):
            client.resume_thread("owned")

    def test_resume_accepts_only_confirmed_owned_controls(self) -> None:
        events = []
        client = CodexAppServerClient({"compatibility": "supported"}, events.append)
        client.thread_ids = ["owned"]
        client.ensure_started = lambda *_args: {"connection_state": "connected"}  # type: ignore[method-assign]
        client.request = lambda *_args, **_kwargs: self.response("owned")  # type: ignore[method-assign]
        result = client.resume_thread("owned", "draft", "beacon-demo")
        self.assertEqual(result["thread_id"], "owned")
        self.assertFalse(result["draft_submitted"])
        self.assertEqual(events[0]["approval"], "turn-not-authorized")
        self.assertEqual(events[0]["project"], "beacon-demo")

    def test_create_registers_ownership_only_after_control_validation(self) -> None:
        owned = []
        client = CodexAppServerClient({"compatibility": "supported"}, lambda _event: None, lambda thread_id, controls: owned.append((thread_id, controls)))
        client.ensure_started = lambda *_args: {"connection_state": "connected"}  # type: ignore[method-assign]
        client.request = lambda *_args, **_kwargs: self.response("new")  # type: ignore[method-assign]
        client.create_thread("draft", "atlas-demo")
        self.assertEqual(owned[0][0], "new")
        self.assertEqual(owned[0][1]["sandbox"], "readOnly")
        self.assertEqual(owned[0][1]["project"], "atlas-demo")

        rejected = []
        client = CodexAppServerClient({"compatibility": "supported"}, lambda _event: None, lambda thread_id, controls: rejected.append((thread_id, controls)))
        client.ensure_started = lambda *_args: {"connection_state": "connected"}  # type: ignore[method-assign]
        client.request = lambda *_args, **_kwargs: self.response("bad", approval="on-request")  # type: ignore[method-assign]
        with self.assertRaisesRegex(RuntimeError, "controls are Gray"):
            client.create_thread("draft")
        self.assertEqual(rejected, [])


if __name__ == "__main__":
    unittest.main()
