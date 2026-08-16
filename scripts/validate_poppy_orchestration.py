#!/usr/bin/env python3
"""Validate Poppy's static capability DAG and normalized plan/closure packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GRAPH = ROOT / "references" / "poppy-capability-graph.json"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKET_TYPES = {"capability-graph", "plan", "closure"}
INTERACTION_CLASSES = {"simple", "bounded-advisory", "substantive-read", "mutating"}
CONFIDENCE_LEVELS = {"high", "medium", "low", "insufficient"}
DISPOSITIONS = {
    "answer-directly",
    "orient-then-answer",
    "discover-then-plan",
    "execute-graph",
    "ask-user",
    "escalate-approval",
}
RISKS = {"R0", "R1", "R2", "R3"}
RISK_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}
GENERAL_VERDICTS = {"PASS", "PASS_WITH_LIMITATIONS", "BLOCK_REMEDIATE", "ESCALATE"}
SPECIAL_HANDLERS = {"selected-capability-handler"}
REQUIRED_GRAPH_NODES = {
    "trigger",
    "triage",
    "project-resolve",
    "readiness-screen",
    "direct-answer",
    "memory-orient",
    "preflight-evaluate",
    "needs-user-decision",
    "dispatch",
    "intake-reconcile",
    "raid-control",
    "join",
    "reconcile",
    "human-approval",
    "authorized-execution",
    "postflight-evaluate",
    "memory-close",
    "terminal",
}
SUBSTANTIVE_LIFECYCLE = {
    "trigger",
    "triage",
    "project-resolve",
    "readiness-screen",
    "memory-orient",
    "preflight-evaluate",
    "dispatch",
    "join",
    "reconcile",
    "postflight-evaluate",
    "memory-close",
    "terminal",
}


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_is_string(item) for item in value)


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    return value


def _graph_index(graph: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], set[tuple[str, str]]]:
    nodes = {
        item["id"]: item
        for item in graph.get("nodes", [])
        if isinstance(item, dict) and _is_string(item.get("id"))
    }
    edges = {
        (item["from"], item["to"])
        for item in graph.get("edges", [])
        if isinstance(item, dict) and _is_string(item.get("from")) and _is_string(item.get("to"))
    }
    return nodes, edges


def validate_graph(graph: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if graph.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if graph.get("packet_type") != "capability-graph":
        errors.append("packet_type must be capability-graph")
    if not _is_string(graph.get("graph_id")):
        errors.append("graph_id must be a non-empty string")

    trigger = _object(graph.get("trigger"), "trigger", errors)
    if trigger.get("canonical_name") != "Poppy":
        errors.append("trigger.canonical_name must be Poppy")
    if trigger.get("match") != "case-insensitive-explicit-mention":
        errors.append("trigger.match must require a case-insensitive explicit mention")
    if not _string_list(trigger.get("aliases")):
        errors.append("trigger.aliases must be a non-empty string list")

    if set(graph.get("interaction_classes", [])) != INTERACTION_CLASSES:
        errors.append("interaction_classes must contain the four Poppy interaction classes")
    if set(graph.get("confidence_levels", [])) != CONFIDENCE_LEVELS:
        errors.append("confidence_levels must contain high, medium, low, and insufficient")

    limits = _object(graph.get("delegation_limits"), "delegation_limits", errors)
    if limits.get("max_depth") != 1:
        errors.append("delegation_limits.max_depth must be 1")
    if limits.get("max_active_workers") != 2:
        errors.append("delegation_limits.max_active_workers must be 2")
    if limits.get("max_created_workers") != 5:
        errors.append("delegation_limits.max_created_workers must be 5")

    nodes_raw = _list(graph.get("nodes"), "nodes", errors)
    nodes: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(nodes_raw):
        path = f"nodes[{index}]"
        node = _object(item, path, errors)
        node_id = node.get("id")
        if not _is_string(node_id) or not ID_RE.fullmatch(node_id):
            errors.append(f"{path}.id must be lowercase hyphen-case")
            continue
        if node_id in nodes:
            errors.append(f"{path}.id duplicates node {node_id}")
            continue
        nodes[node_id] = node
        if node.get("kind") not in {"control", "evaluation", "memory", "capability", "assessment", "authority"}:
            errors.append(f"{path}.kind is invalid")
        handler = node.get("handler")
        if not _is_string(handler):
            errors.append(f"{path}.handler must be a non-empty string")
        elif handler not in SPECIAL_HANDLERS and not (root / "skills" / handler / "SKILL.md").is_file():
            errors.append(f"{path}.handler does not resolve to a bundled skill: {handler}")
        if node.get("execution") not in {
            "root-only",
            "root-or-worker",
            "fresh-worker",
            "root-or-fresh-worker",
        }:
            errors.append(f"{path}.execution is invalid")
        if not _string_list(node.get("outputs")):
            errors.append(f"{path}.outputs must be a non-empty string list")
        if not _string_list(node.get("inputs")):
            errors.append(f"{path}.inputs must be a non-empty string list")

    missing = sorted(REQUIRED_GRAPH_NODES - set(nodes))
    if missing:
        errors.append(f"graph is missing required nodes: {', '.join(missing)}")

    edges_raw = _list(graph.get("edges"), "edges", errors)
    edge_pairs: set[tuple[str, str]] = set()
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    indegree: dict[str, int] = {node_id: 0 for node_id in nodes}
    for index, item in enumerate(edges_raw):
        path = f"edges[{index}]"
        edge = _object(item, path, errors)
        source, target = edge.get("from"), edge.get("to")
        if source not in nodes:
            errors.append(f"{path}.from references unknown node {source}")
        if target not in nodes:
            errors.append(f"{path}.to references unknown node {target}")
        if source == target:
            errors.append(f"{path} cannot be a self-edge")
        pair = (source, target)
        if pair in edge_pairs:
            errors.append(f"{path} duplicates edge {source}->{target}")
        edge_pairs.add(pair)
        if not _is_string(edge.get("artifact")):
            errors.append(f"{path}.artifact must be a non-empty string")
        if not _is_string(edge.get("condition")):
            errors.append(f"{path}.condition must be a non-empty string")
        if source in nodes and target in nodes and source != target:
            if edge.get("artifact") not in nodes[source].get("outputs", []):
                errors.append(f"{path}.artifact is not produced by {source}")
            if edge.get("artifact") not in nodes[target].get("inputs", []):
                errors.append(f"{path}.artifact is not accepted by {target}")
            adjacency[source].append(target)
            indegree[target] += 1

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    visited = 0
    while queue:
        source = queue.popleft()
        visited += 1
        for target in adjacency[source]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if visited != len(nodes):
        errors.append("capability graph must be acyclic")

    reachable = {"trigger"} if "trigger" in nodes else set()
    queue = deque(reachable)
    while queue:
        source = queue.popleft()
        for target in adjacency.get(source, []):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    unreachable = sorted(set(nodes) - reachable)
    if unreachable:
        errors.append(f"graph nodes are unreachable from trigger: {', '.join(unreachable)}")

    reverse: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for source, targets in adjacency.items():
        for target in targets:
            reverse[target].append(source)
    terminal_reachable = {"terminal"} if "terminal" in nodes else set()
    queue = deque(terminal_reachable)
    while queue:
        target = queue.popleft()
        for source in reverse.get(target, []):
            if source not in terminal_reachable:
                terminal_reachable.add(source)
                queue.append(source)
    no_terminal = sorted(set(nodes) - terminal_reachable)
    if no_terminal:
        errors.append(f"graph nodes lack a terminal path: {', '.join(no_terminal)}")

    paths = _object(graph.get("required_paths"), "required_paths", errors)
    for name in ("simple", "substantive", "closure"):
        path_nodes = paths.get(name)
        if not _string_list(path_nodes):
            errors.append(f"required_paths.{name} must be a non-empty string list")
            continue
        for source, target in zip(path_nodes, path_nodes[1:]):
            if (source, target) not in edge_pairs:
                errors.append(f"required_paths.{name} uses missing edge {source}->{target}")

    invariants = graph.get("invariants")
    if not _string_list(invariants) or len(invariants) < 8:
        errors.append("invariants must contain at least eight non-empty contracts")
    return errors


def _validate_trigger(packet: dict[str, Any], errors: list[str]) -> None:
    trigger = _object(packet.get("trigger"), "trigger", errors)
    mention = trigger.get("mention")
    if not _is_string(mention) or not any(
        alias in mention.casefold() for alias in ("poppy", "project operations partner")
    ):
        errors.append("trigger.mention must explicitly contain Poppy or Project Operations Partner")
    if trigger.get("matched") is not True:
        errors.append("trigger.matched must be true")
    if trigger.get("provenance") != "current-user-turn":
        errors.append("trigger.provenance must be current-user-turn")
    if not _is_string(trigger.get("turn_id")):
        errors.append("trigger.turn_id must identify the trusted current user turn")
    digest = trigger.get("turn_digest")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append("trigger.turn_digest must be a lowercase SHA-256 digest")
    elif _is_string(mention) and digest != hashlib.sha256(mention.encode("utf-8")).hexdigest():
        errors.append("trigger.turn_digest must bind the trusted current user turn text")


def _validate_selected_graph(
    packet: dict[str, Any], graph: dict[str, Any], errors: list[str]
) -> tuple[list[str], set[tuple[str, str]], dict[str, dict[str, Any]]]:
    nodes, allowed_edges = _graph_index(graph)
    selected = packet.get("selected_nodes")
    if not _string_list(selected):
        errors.append("selected_nodes must be a non-empty string list")
        selected = []
    if len(selected) != len(set(selected)):
        errors.append("selected_nodes must be unique")
    unknown = sorted(set(selected) - set(nodes))
    if unknown:
        errors.append(f"selected_nodes contains unknown nodes: {', '.join(unknown)}")
    positions = {node_id: index for index, node_id in enumerate(selected)}

    selected_edges_raw = _list(packet.get("selected_edges"), "selected_edges", errors)
    selected_edges: set[tuple[str, str]] = set()
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in selected}
    for index, item in enumerate(selected_edges_raw):
        path = f"selected_edges[{index}]"
        edge = _object(item, path, errors)
        pair = (edge.get("from"), edge.get("to"))
        if pair in selected_edges:
            errors.append(f"{path} duplicates selected edge {pair[0]}->{pair[1]}")
        selected_edges.add(pair)
        if pair not in allowed_edges:
            errors.append(f"{path} is not permitted by the capability graph: {pair[0]}->{pair[1]}")
        if pair[0] not in positions or pair[1] not in positions:
            errors.append(f"{path} endpoints must both be selected")
        elif positions[pair[0]] >= positions[pair[1]]:
            errors.append(f"{path} violates selected node dependency order")
        else:
            adjacency[pair[0]].append(pair[1])

    if selected and selected[0] != "trigger":
        errors.append("selected_nodes must begin with trigger")
    if selected and selected[-1] != "terminal":
        errors.append("selected_nodes must end with terminal")
    reachable = {"trigger"} if "trigger" in selected else set()
    queue = deque(reachable)
    while queue:
        source = queue.popleft()
        for target in adjacency.get(source, []):
            if target not in reachable:
                reachable.add(target)
                queue.append(target)
    disconnected = sorted(set(selected) - reachable)
    if disconnected:
        errors.append(f"selected subgraph contains nodes unreachable from trigger: {', '.join(disconnected)}")

    reverse: dict[str, list[str]] = {node_id: [] for node_id in selected}
    for source, targets in adjacency.items():
        for target in targets:
            reverse[target].append(source)
    terminal_reachable = {"terminal"} if "terminal" in selected else set()
    queue = deque(terminal_reachable)
    while queue:
        target = queue.popleft()
        for source in reverse.get(target, []):
            if source not in terminal_reachable:
                terminal_reachable.add(source)
                queue.append(source)
    unterminated = sorted(set(selected) - terminal_reachable)
    if unterminated:
        errors.append(f"selected subgraph contains nodes without a terminal path: {', '.join(unterminated)}")
    return selected, selected_edges, nodes


def _validate_preflight(packet: dict[str, Any], errors: list[str]) -> tuple[str | None, str | None]:
    preflight = _object(packet.get("preflight"), "preflight", errors)
    confidence = preflight.get("confidence")
    disposition = preflight.get("disposition")
    if confidence not in CONFIDENCE_LEVELS:
        errors.append("preflight.confidence is invalid")
    if disposition not in DISPOSITIONS:
        errors.append("preflight.disposition is invalid")
    if preflight.get("risk") not in RISKS:
        errors.append("preflight.risk must be R0, R1, R2, or R3")
    if not _string_list(preflight.get("evidence_basis")):
        errors.append("preflight.evidence_basis must be a non-empty string list")
    for field in ("assumptions", "missing_evidence", "contradictions"):
        if not isinstance(preflight.get(field), list) or not all(
            _is_string(item) for item in preflight.get(field, [])
        ):
            errors.append(f"preflight.{field} must be a string list")
    if confidence in {"low", "insufficient"} and disposition == "execute-graph":
        errors.append("low or insufficient confidence cannot dispatch execution")
    return confidence, disposition


def _validate_authority(
    packet: dict[str, Any], interaction: str, selected: list[str], risk_floor: str | None, errors: list[str]
) -> None:
    authority = _object(packet.get("authority"), "authority", errors)
    status = authority.get("status")
    if status not in {"read-only", "authorized", "approval-required", "denied"}:
        errors.append("authority.status is invalid")
    for field in ("allowed_actions", "approval_required", "forbidden_actions"):
        if not isinstance(authority.get(field), list) or not all(
            _is_string(item) for item in authority.get(field, [])
        ):
            errors.append(f"authority.{field} must be a string list")
    maximum_risk = authority.get("maximum_risk")
    if maximum_risk not in RISKS:
        errors.append("authority.maximum_risk must be R0, R1, R2, or R3")
    elif risk_floor in RISKS and RISK_ORDER[maximum_risk] < RISK_ORDER[risk_floor]:
        errors.append("authority.maximum_risk is below the preflight risk floor")
    if not _is_string(authority.get("receipt_id")):
        errors.append("authority.receipt_id must bind the authority source")
    previews = authority.get("effect_previews")
    if not isinstance(previews, list):
        errors.append("authority.effect_previews must be a list")
        previews = []
    for index, item in enumerate(previews):
        preview = _object(item, f"authority.effect_previews[{index}]", errors)
        for field in ("target", "action", "rollback", "handler"):
            if not _is_string(preview.get(field)):
                errors.append(f"authority.effect_previews[{index}].{field} must be non-empty")
    if interaction == "mutating":
        if status in {"read-only", "denied"}:
            errors.append("mutating plans require authorized or approval-required authority")
        if "authorized-execution" not in selected:
            errors.append("mutating plans must select authorized-execution")
        if status == "authorized" and not authority.get("allowed_actions"):
            errors.append("authorized mutating plans require bounded allowed_actions")
        if status == "approval-required" and "human-approval" not in selected:
            errors.append("approval-required plans must select human-approval")
        if not previews:
            errors.append("mutating plans require exact effect previews")
    elif previews:
        errors.append("read-only plans cannot carry mutation effect previews")
    if status == "denied" and "authorized-execution" in selected:
        errors.append("denied authority cannot select authorized-execution")


def _validate_delegation(
    packet: dict[str, Any], graph: dict[str, Any], selected: list[str], nodes: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    delegation = _object(packet.get("delegation"), "delegation", errors)
    limits = graph.get("delegation_limits", {})
    mode = delegation.get("mode")
    if mode not in {"none", "bounded"}:
        errors.append("delegation.mode must be none or bounded")
    for field, maximum in (
        ("max_depth", limits.get("max_depth")),
        ("max_active_workers", limits.get("max_active_workers")),
        ("max_created_workers", limits.get("max_created_workers")),
    ):
        value = delegation.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > maximum:
            errors.append(f"delegation.{field} exceeds the capability-graph limit")
    workers = _list(delegation.get("workers"), "delegation.workers", errors)
    if mode == "none" and workers:
        errors.append("delegation workers must be empty when mode is none")
    if len(workers) > delegation.get("max_created_workers", 0):
        errors.append("delegation workers exceed max_created_workers")
    worker_ids: set[str] = set()
    active_workers = 0
    root_task_id = packet.get("root_task_id")
    for index, item in enumerate(workers):
        path = f"delegation.workers[{index}]"
        worker = _object(item, path, errors)
        worker_id = worker.get("id")
        node_id = worker.get("node")
        if not _is_string(worker_id) or worker_id in worker_ids:
            errors.append(f"{path}.id must be unique and non-empty")
        else:
            worker_ids.add(worker_id)
        if worker.get("root_task_id") != root_task_id or worker.get("parent_task_id") != root_task_id:
            errors.append(f"{path} must be a depth-one child of the recorded root task")
        if worker.get("depth") != 1:
            errors.append(f"{path}.depth must be 1")
        if worker.get("can_delegate") is not False:
            errors.append(f"{path}.can_delegate must be false")
        if worker.get("shared_memory_write") is not False:
            errors.append(f"{path}.shared_memory_write must be false")
        if worker.get("decision_protocol") != "NEEDS_PARENT_DECISION":
            errors.append(f"{path}.decision_protocol must be NEEDS_PARENT_DECISION")
        if worker.get("status") not in {"planned", "active", "complete", "stopped"}:
            errors.append(f"{path}.status is invalid")
        active_workers += worker.get("status") == "active"
        if node_id not in selected:
            errors.append(f"{path}.node must be selected")
            continue
        node = nodes.get(node_id, {})
        if node.get("execution") == "root-only":
            errors.append(f"{path}.node is root-only")
        if worker.get("skill") != node.get("handler"):
            errors.append(f"{path}.skill must match the selected node handler")
        if worker.get("authority") != "read-only":
            errors.append(f"{path}.authority must be read-only; capability-owned delivery controls isolated writers")
        if not _is_string(worker.get("output_contract")):
            errors.append(f"{path}.output_contract must be non-empty")
        if not _string_list(worker.get("minimized_inputs")):
            errors.append(f"{path}.minimized_inputs must be a non-empty string list")
        if not _string_list(worker.get("stop_conditions")):
            errors.append(f"{path}.stop_conditions must be a non-empty string list")
        if worker.get("effort") not in {"low", "medium", "high", "xhigh"}:
            errors.append(f"{path}.effort is invalid")
        if not _is_string(worker.get("effort_rationale")):
            errors.append(f"{path}.effort_rationale must be non-empty")
        allowance = worker.get("remaining_task_allowance")
        if not isinstance(allowance, int) or isinstance(allowance, bool) or allowance < 0:
            errors.append(f"{path}.remaining_task_allowance must be a non-negative integer")
    if active_workers > delegation.get("max_active_workers", 0):
        errors.append("delegation active workers exceed max_active_workers")


def validate_plan(packet: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if packet.get("packet_type") != "plan":
        errors.append("packet_type must be plan")
    for field in ("run_id", "root_task_id", "objective", "project_id", "graph_id", "graph_digest"):
        if not _is_string(packet.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if packet.get("graph_id") != graph.get("graph_id"):
        errors.append("graph_id does not match the capability graph")
    if packet.get("graph_digest") != canonical_digest(graph):
        errors.append("graph_digest does not match the exact capability graph")
    _validate_trigger(packet, errors)
    interaction = packet.get("interaction_class")
    if interaction not in INTERACTION_CLASSES:
        errors.append("interaction_class is invalid")
        interaction = "simple"
    acceptance = packet.get("acceptance")
    if not _string_list(acceptance):
        errors.append("acceptance must be a non-empty string list")

    selected, selected_edges, nodes = _validate_selected_graph(packet, graph, errors)
    selected_set = set(selected)
    confidence, disposition = _validate_preflight(packet, errors)
    risk_floor = packet.get("preflight", {}).get("risk")
    _validate_authority(packet, interaction, selected, risk_floor, errors)
    selected_handlers = {
        nodes[node_id].get("handler")
        for node_id in selected
        if node_id in nodes and nodes[node_id].get("kind") == "capability"
    }
    for index, preview in enumerate(packet.get("authority", {}).get("effect_previews", [])):
        if isinstance(preview, dict) and preview.get("handler") not in selected_handlers:
            errors.append(
                f"authority.effect_previews[{index}].handler must identify a selected capability handler"
            )
    _validate_delegation(packet, graph, selected, nodes, errors)

    always_required = {"trigger", "triage", "readiness-screen", "postflight-evaluate", "terminal"}
    missing = sorted(always_required - selected_set)
    if missing:
        errors.append(f"plan is missing required control nodes: {', '.join(missing)}")
    if interaction == "simple":
        if "direct-answer" not in selected_set:
            errors.append("simple plans must select direct-answer")
        forbidden = selected_set & {"memory-orient", "preflight-evaluate", "dispatch", "memory-close"}
        if forbidden:
            errors.append("simple plans cannot force substantive lifecycle nodes")
        if disposition != "answer-directly":
            errors.append("simple plans require answer-directly disposition")
    if interaction in {"substantive-read", "mutating"}:
        missing = sorted(SUBSTANTIVE_LIFECYCLE - selected_set)
        if missing:
            errors.append(f"substantive plans are missing lifecycle nodes: {', '.join(missing)}")
        capability_count = sum(
            1
            for node_id in selected
            if nodes.get(node_id, {}).get("kind") in {"capability", "assessment"}
            and node_id != "direct-answer"
        )
        if capability_count == 0:
            errors.append("substantive plans must select at least one capability node")
        capability_nodes = {
            node_id
            for node_id in selected
            if nodes.get(node_id, {}).get("kind") in {"capability", "assessment"}
            and node_id != "direct-answer"
        }
        for node_id in sorted(capability_nodes):
            downstream_capability = any(
                source == node_id and target in capability_nodes for source, target in selected_edges
            )
            if not downstream_capability and (node_id, "join") not in selected_edges:
                errors.append(f"leaf capability {node_id} must feed the join barrier")
        if ("join", "reconcile") not in selected_edges:
            errors.append("substantive plans require join->reconcile")
        if disposition not in {"orient-then-answer", "discover-then-plan", "execute-graph"}:
            errors.append("substantive execution has an incompatible preflight disposition")
    if interaction == "mutating" and confidence in {"low", "insufficient"}:
        errors.append("mutating plans require medium or high preflight confidence")

    scope_mode = packet.get("scope_mode")
    if scope_mode not in {"read-only", "review-only", "diagnosis-only", "write-authorized"}:
        errors.append("scope_mode is invalid")
    if interaction == "mutating" and scope_mode != "write-authorized":
        errors.append("mutating plans require write-authorized scope_mode")
    if interaction != "mutating" and scope_mode == "write-authorized":
        errors.append("non-mutating plans cannot claim write-authorized scope_mode")

    memory = _object(packet.get("memory"), "memory", errors)
    if memory.get("orientation") not in {"not-required", "complete", "gray"}:
        errors.append("memory.orientation is invalid")
    if memory.get("closure") not in {"not-required", "required"}:
        errors.append("memory.closure is invalid")
    if memory.get("durable_write") not in {"not-planned", "conditional", "planned"}:
        errors.append("memory.durable_write is invalid")
    if interaction == "simple" and (
        memory.get("orientation") != "not-required" or memory.get("closure") != "not-required"
    ):
        errors.append("simple plans must keep memory orientation and closure not-required")
    if interaction in {"substantive-read", "mutating"} and memory.get("closure") != "required":
        errors.append("substantive plans require a memory-close disposition")
    if scope_mode in {"read-only", "review-only", "diagnosis-only"} and memory.get("durable_write") != "not-planned":
        errors.append("explicit non-write scope must suppress every durable memory write and receipt")
    return errors


def validate_closure(
    packet: dict[str, Any], graph: dict[str, Any], plan: dict[str, Any] | None = None
) -> list[str]:
    errors: list[str] = []
    if packet.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if packet.get("packet_type") != "closure":
        errors.append("packet_type must be closure")
    for field in (
        "run_id",
        "plan_run_id",
        "root_task_id",
        "objective",
        "project_id",
        "graph_id",
        "graph_digest",
        "plan_digest",
        "authority_receipt_id",
    ):
        if not _is_string(packet.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if packet.get("graph_id") != graph.get("graph_id"):
        errors.append("graph_id does not match the capability graph")
    if packet.get("graph_digest") != canonical_digest(graph):
        errors.append("graph_digest does not match the exact capability graph")
    if plan is not None:
        if validate_plan(plan, graph):
            errors.append("bound plan is invalid")
        if packet.get("plan_digest") != canonical_digest(plan):
            errors.append("plan_digest does not match the exact bound plan")
        bindings = {
            "plan_run_id": plan.get("run_id"),
            "root_task_id": plan.get("root_task_id"),
            "objective": plan.get("objective"),
            "project_id": plan.get("project_id"),
            "interaction_class": plan.get("interaction_class"),
            "scope_mode": plan.get("scope_mode"),
            "selected_nodes": plan.get("selected_nodes"),
            "selected_edges": plan.get("selected_edges"),
        }
        for field, expected in bindings.items():
            if packet.get(field) != expected:
                errors.append(f"closure {field} does not match the bound plan")
        if packet.get("authority_receipt_id") != plan.get("authority", {}).get("receipt_id"):
            errors.append("closure authority receipt does not match the bound plan")
    _validate_trigger(packet, errors)
    interaction = packet.get("interaction_class")
    if interaction not in INTERACTION_CLASSES:
        errors.append("interaction_class is invalid")
        interaction = "simple"
    selected, _, _ = _validate_selected_graph(packet, graph, errors)

    results = _list(packet.get("node_results"), "node_results", errors)
    result_nodes: set[str] = set()
    node_statuses: list[str] = []
    for index, item in enumerate(results):
        path = f"node_results[{index}]"
        result = _object(item, path, errors)
        node_id = result.get("node")
        if node_id not in selected or node_id in result_nodes:
            errors.append(f"{path}.node must identify one unique selected node")
        else:
            result_nodes.add(node_id)
        status = result.get("status")
        if status not in {"pass", "limited", "skipped", "failed"}:
            errors.append(f"{path}.status is invalid")
        else:
            node_statuses.append(status)
        if not _is_string(result.get("summary")):
            errors.append(f"{path}.summary must be non-empty")
        if not isinstance(result.get("evidence_refs"), list) or not all(
            _is_string(value) for value in result.get("evidence_refs", [])
        ):
            errors.append(f"{path}.evidence_refs must be a string list")
        if status == "skipped" and not _is_string(result.get("skip_reason")):
            errors.append(f"{path}.skip_reason is required when skipped")
    missing_results = sorted(set(selected) - result_nodes)
    if missing_results:
        errors.append(f"node_results are missing selected nodes: {', '.join(missing_results)}")

    acceptance = _list(packet.get("acceptance_results"), "acceptance_results", errors)
    acceptance_statuses: list[str] = []
    for index, item in enumerate(acceptance):
        path = f"acceptance_results[{index}]"
        result = _object(item, path, errors)
        if not _is_string(result.get("item")):
            errors.append(f"{path}.item must be non-empty")
        status = result.get("status")
        if status not in {"pass", "limited", "fail", "unverified"}:
            errors.append(f"{path}.status is invalid")
        else:
            acceptance_statuses.append(status)
        if not isinstance(result.get("evidence_refs"), list) or not all(
            _is_string(value) for value in result.get("evidence_refs", [])
        ):
            errors.append(f"{path}.evidence_refs must be a string list")
    if not acceptance:
        errors.append("acceptance_results must be non-empty")

    effects = _list(packet.get("external_effects"), "external_effects", errors)
    unverified_effect = False
    recorded_effects: set[tuple[str, str, str]] = set()
    for index, item in enumerate(effects):
        path = f"external_effects[{index}]"
        effect = _object(item, path, errors)
        for field in ("target", "action", "handler", "authority_receipt_id"):
            if not _is_string(effect.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        recorded_effects.add((effect.get("target"), effect.get("action"), effect.get("handler")))
        if effect.get("authority_receipt_id") != packet.get("authority_receipt_id"):
            errors.append(f"{path}.authority_receipt_id must match the closure authority receipt")
        if not isinstance(effect.get("verified"), bool):
            errors.append(f"{path}.verified must be boolean")
        unverified_effect = unverified_effect or effect.get("verified") is not True
        if not isinstance(effect.get("evidence_refs"), list) or not all(
            _is_string(value) for value in effect.get("evidence_refs", [])
        ):
            errors.append(f"{path}.evidence_refs must be a string list")
        if effect.get("verified") is True and not effect.get("evidence_refs"):
            errors.append(f"{path}.evidence_refs must include read-back evidence")

    if plan is not None:
        planned_effects = {
            (item.get("target"), item.get("action"), item.get("handler"))
            for item in plan.get("authority", {}).get("effect_previews", [])
            if isinstance(item, dict)
        }
        if recorded_effects != planned_effects:
            errors.append("external effects must exactly match the bound plan effect previews")

    worker_closures = _list(packet.get("worker_closures"), "worker_closures", errors)
    closure_workers: set[str] = set()
    for index, item in enumerate(worker_closures):
        path = f"worker_closures[{index}]"
        card = _object(item, path, errors)
        worker_id = card.get("worker_id")
        if not _is_string(worker_id) or worker_id in closure_workers:
            errors.append(f"{path}.worker_id must be unique and non-empty")
        else:
            closure_workers.add(worker_id)
        if card.get("root_task_id") != packet.get("root_task_id") or card.get("parent_task_id") != packet.get("root_task_id"):
            errors.append(f"{path} must bind to the root task")
        if card.get("outcome") not in {"complete", "limited", "NEEDS_PARENT_DECISION", "failed"}:
            errors.append(f"{path}.outcome is invalid")
        if not _string_list(card.get("evidence_refs")):
            errors.append(f"{path}.evidence_refs must be a non-empty string list")
        repository = _object(card.get("repository_state"), f"{path}.repository_state", errors)
        if repository.get("status") not in {"clean", "recoverable", "not-applicable"}:
            errors.append(f"{path}.repository_state.status is invalid")
        if repository.get("status") == "recoverable" and not all(
            _is_string(repository.get(field)) for field in ("commit", "branch")
        ):
            errors.append(f"{path}.repository_state requires commit and branch when recoverable")
        for field in ("residual_risk", "next_action"):
            if not _is_string(card.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
    if plan is not None:
        planned_workers = {
            item.get("id")
            for item in plan.get("delegation", {}).get("workers", [])
            if isinstance(item, dict)
        }
        if closure_workers != planned_workers:
            errors.append("worker_closures must exactly cover the bound plan workers")

    postflight = _object(packet.get("postflight"), "postflight", errors)
    verdict = postflight.get("verdict")
    if verdict not in GENERAL_VERDICTS:
        errors.append("postflight.verdict is invalid")
    if postflight.get("confidence") not in CONFIDENCE_LEVELS:
        errors.append("postflight.confidence is invalid")
    if not _string_list(postflight.get("evidence_basis")):
        errors.append("postflight.evidence_basis must be a non-empty string list")
    if not isinstance(postflight.get("residual_risks"), list) or not all(
        _is_string(value) for value in postflight.get("residual_risks", [])
    ):
        errors.append("postflight.residual_risks must be a string list")
    if postflight.get("evaluator") not in {"root", "fresh-worker"}:
        errors.append("postflight.evaluator must be root or fresh-worker")
    if not _is_string(postflight.get("evaluator_task_id")):
        errors.append("postflight.evaluator_task_id must be non-empty")
    if not isinstance(postflight.get("independent"), bool):
        errors.append("postflight.independent must be boolean")
    risk = packet.get("risk")
    if risk not in RISKS:
        errors.append("risk must be R0, R1, R2, or R3")
    if risk in {"R2", "R3"}:
        if postflight.get("independent") is not True or postflight.get("evaluator") != "fresh-worker":
            errors.append("R2 and R3 closures require a fresh independent evaluator")
        if postflight.get("evaluator_task_id") == packet.get("root_task_id"):
            errors.append("the root task cannot claim independent evaluation")

    if verdict == "PASS" and any(status != "pass" for status in acceptance_statuses):
        errors.append("PASS requires every acceptance item to pass")
    if verdict == "PASS" and (any(status != "pass" for status in node_statuses) or unverified_effect):
        errors.append("PASS requires every selected node to pass and every effect to be verified")
    if verdict == "PASS_WITH_LIMITATIONS":
        if any(status in {"fail", "unverified"} for status in acceptance_statuses):
            errors.append("PASS_WITH_LIMITATIONS cannot include failed or unverified acceptance")
        if any(status in {"failed", "skipped"} for status in node_statuses) or unverified_effect:
            errors.append("PASS_WITH_LIMITATIONS cannot include failed/skipped nodes or unverified effects")
    if verdict in {"PASS", "PASS_WITH_LIMITATIONS"} and postflight.get("confidence") == "insufficient":
        errors.append("a passing verdict cannot have insufficient final confidence")

    memory = _object(packet.get("memory"), "memory", errors)
    closure = memory.get("closure")
    if closure not in {"not-required", "no-change", "updated", "proposed-only", "failed"}:
        errors.append("memory.closure is invalid")
    if interaction in {"substantive-read", "mutating"} and closure == "not-required":
        errors.append("substantive closures require a memory disposition")
    if interaction == "simple" and closure not in {"not-required", "no-change"}:
        errors.append("simple closures cannot create a durable memory update by default")
    if packet.get("scope_mode") in {"read-only", "review-only", "diagnosis-only"} and closure not in {
        "not-required",
        "no-change",
    }:
        errors.append("explicit non-write scope cannot update memory or create a receipt")
    return errors


def validate_packet(
    packet: dict[str, Any], graph: dict[str, Any] | None = None, plan: dict[str, Any] | None = None
) -> list[str]:
    packet_type = packet.get("packet_type")
    if packet_type not in PACKET_TYPES:
        return ["packet_type must be capability-graph, plan, or closure"]
    if packet_type == "capability-graph":
        return validate_graph(packet)
    if graph is None:
        graph = json.loads(DEFAULT_GRAPH.read_text(encoding="utf-8"))
    graph_errors = validate_graph(graph)
    if graph_errors:
        return [f"capability graph invalid: {error}" for error in graph_errors]
    if packet_type == "plan":
        return validate_plan(packet, graph)
    return validate_closure(packet, graph, plan)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
        graph = None
        plan = None
        if packet.get("packet_type") != "capability-graph":
            graph = json.loads(args.graph.read_text(encoding="utf-8"))
        if args.plan is not None:
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 1
    errors = validate_packet(packet, graph, plan)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
