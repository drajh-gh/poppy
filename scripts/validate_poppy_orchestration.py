#!/usr/bin/env python3
"""Validate Poppy's static capability DAG and normalized plan/closure packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
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
CURRENT_TURN_GRANT_ALIASES = ("poppy", "project operations partner")
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


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_string(item) for item in value)


def _name_continuation(character: str) -> bool:
    category = unicodedata.category(character)
    return category[0] in {"L", "M", "N"} or category in {"Pc", "Cf"} or character == "-"


def _has_explicit_alias(text: str, alias: str) -> bool:
    start = 0
    while True:
        index = text.find(alias, start)
        if index < 0:
            return False
        before = text[index - 1] if index else ""
        after_index = index + len(alias)
        after = text[after_index] if after_index < len(text) else ""
        if (not before or not _name_continuation(before)) and (
            not after or not _name_continuation(after)
        ):
            return True
        start = index + 1


def _turn_is_exact_authorization_grant(mention: str, actions: list[Any]) -> bool:
    normalized_actions = [_canonical_text(action) for action in actions if _is_string(action)]
    if len(normalized_actions) != 1 or len(actions) != 1:
        return False
    action = normalized_actions[0]
    accepted = {
        f"{alias}{separator} i authorize this exact action: {action}"
        for alias in CURRENT_TURN_GRANT_ALIASES
        for separator in (",", ":")
    }
    return mention in accepted


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


STRUCTURE_EXCEPTIONS = (AttributeError, IndexError, KeyError, TypeError, ValueError)


def _validate_graph_impl(graph: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if not _is_integer(graph.get("schema_version")) or graph.get("schema_version") != 1:
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
    if not _is_integer(limits.get("max_depth")) or limits.get("max_depth") != 1:
        errors.append("delegation_limits.max_depth must be 1")
    if not _is_integer(limits.get("max_active_workers")) or limits.get("max_active_workers") != 2:
        errors.append("delegation_limits.max_active_workers must be 2")
    if not _is_integer(limits.get("max_created_workers")) or limits.get("max_created_workers") != 5:
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


def validate_graph(graph: dict[str, Any], root: Path = ROOT) -> list[str]:
    if not isinstance(graph, dict):
        return ["capability graph must be an object"]
    try:
        return _validate_graph_impl(graph, root)
    except STRUCTURE_EXCEPTIONS:
        return ["capability graph contains invalid nested field types"]


def _validate_trigger(packet: dict[str, Any], errors: list[str]) -> None:
    trigger = _object(packet.get("trigger"), "trigger", errors)
    mention = trigger.get("mention")
    mention_folded = mention.casefold() if _is_string(mention) else ""
    explicit_name = _has_explicit_alias(mention_folded, "poppy")
    explicit_alias = _has_explicit_alias(mention_folded, "project operations partner")
    if not explicit_name and not explicit_alias:
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
    packet: dict[str, Any], interaction: str, selected: list[str], risk_floor: str | None,
    disposition: str | None, errors: list[str]
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
    allowed_normalized = {
        _canonical_text(item) for item in authority.get("allowed_actions", []) if _is_string(item)
    }
    forbidden_normalized = {
        _canonical_text(item) for item in authority.get("forbidden_actions", []) if _is_string(item)
    }
    approval_normalized = {
        _canonical_text(item) for item in authority.get("approval_required", []) if _is_string(item)
    }
    if allowed_normalized & forbidden_normalized:
        errors.append("authority allowed_actions and forbidden_actions must not overlap")
    if allowed_normalized & approval_normalized:
        errors.append("authority allowed_actions and approval_required must not overlap")
    if forbidden_normalized & approval_normalized:
        errors.append("authority forbidden_actions and approval_required must not overlap")
    maximum_risk = authority.get("maximum_risk")
    if maximum_risk not in RISKS:
        errors.append("authority.maximum_risk must be R0, R1, R2, or R3")
    elif risk_floor in RISKS and RISK_ORDER[maximum_risk] < RISK_ORDER[risk_floor]:
        errors.append("authority.maximum_risk is below the preflight risk floor")
    if not _is_string(authority.get("receipt_id")):
        errors.append("authority.receipt_id must bind the authority source")
    source = authority.get("source")
    if source not in {"current-user-turn", "approved-manifest", "named-approver-receipt"}:
        errors.append("authority.source is invalid")
    source_digest = authority.get("source_digest")
    if not isinstance(source_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", source_digest):
        errors.append("authority.source_digest must be a lowercase SHA-256 digest")
    if source == "current-user-turn":
        trigger = packet.get("trigger", {})
        if authority.get("receipt_id") != trigger.get("turn_id"):
            errors.append("current-turn authority receipt_id must match trigger.turn_id")
        if source_digest != trigger.get("turn_digest"):
            errors.append("current-turn authority source_digest must match trigger.turn_digest")
        if status == "authorized":
            mention = trigger.get("mention", "")
            normalized_mention = _canonical_text(mention) if _is_string(mention) else ""
            if not _turn_is_exact_authorization_grant(
                normalized_mention, authority.get("allowed_actions", [])
            ):
                errors.append(
                    "current-turn mutation authority requires one standalone exact authorization grant"
                )
    if risk_floor == "R3" and source == "approved-manifest":
        errors.append("R3 authority cannot come from an approved manifest; it requires separate exact approval")
    previews = authority.get("effect_previews")
    if not isinstance(previews, list):
        errors.append("authority.effect_previews must be a list")
        previews = []
    preview_ids: set[str] = set()
    for index, item in enumerate(previews):
        preview = _object(item, f"authority.effect_previews[{index}]", errors)
        for field in ("effect_id", "target", "action", "rollback", "handler"):
            if not _is_string(preview.get(field)):
                errors.append(f"authority.effect_previews[{index}].{field} must be non-empty")
        effect_id = preview.get("effect_id")
        if _is_string(effect_id):
            if effect_id in preview_ids:
                errors.append(f"authority.effect_previews[{index}].effect_id must be unique")
            preview_ids.add(effect_id)
        action_bucket = "approval_required" if status == "approval-required" else "allowed_actions"
        bucket_actions = {
            _canonical_text(action)
            for action in authority.get(action_bucket, [])
            if _is_string(action)
        }
        preview_action = preview.get("action")
        if not _is_string(preview_action) or _canonical_text(preview_action) not in bucket_actions:
            errors.append(
                f"authority.effect_previews[{index}].action is outside {action_bucket}"
            )
    if interaction == "mutating":
        stopping = disposition in {"ask-user", "escalate-approval"}
        if status in {"read-only", "denied"} and not stopping:
            errors.append("mutating plans require authorized or approval-required authority")
        if status == "authorized" and "authorized-execution" not in selected:
            errors.append("mutating plans must select authorized-execution")
        if status == "authorized" and not authority.get("allowed_actions"):
            errors.append("authorized mutating plans require bounded allowed_actions")
        if status == "approval-required" and not ({"human-approval", "needs-user-decision"} & set(selected)):
            errors.append("approval-required plans must select a root approval or user-decision node")
        if status == "approval-required" and "authorized-execution" in selected:
            errors.append("approval-required plans must stop before authorized execution and re-plan after approval")
        if not previews:
            errors.append("mutating plans require exact effect previews")
    elif previews:
        errors.append("read-only plans cannot carry mutation effect previews")
    if interaction != "mutating" and "authorized-execution" in selected:
        errors.append("non-mutating plans cannot select authorized-execution")
    if status == "denied" and "authorized-execution" in selected:
        errors.append("denied authority cannot select authorized-execution")


def _validate_delegation(
    packet: dict[str, Any], graph: dict[str, Any], selected: list[str], selected_edges: list[tuple[str, str]],
    nodes: dict[str, dict[str, Any]], errors: list[str]
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
    max_depth = delegation.get("max_depth")
    max_active = delegation.get("max_active_workers")
    if workers and (
        not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 1
    ):
        errors.append("delegation with workers requires max_depth of at least 1")
    if workers and (
        not isinstance(max_active, int) or isinstance(max_active, bool) or max_active < 1
    ):
        errors.append("delegation with workers requires a positive max_active_workers budget")
    max_created = delegation.get("max_created_workers")
    safe_max_created = max_created if _is_integer(max_created) else -1
    if len(workers) > safe_max_created:
        errors.append("delegation workers exceed max_created_workers")
    worker_ids: set[str] = set()
    active_workers = 0
    root_task_id = packet.get("root_task_id")
    edge_artifacts = {
        (edge.get("from"), edge.get("to")): edge.get("artifact")
        for edge in graph.get("edges", [])
        if isinstance(edge, dict)
    }
    for index, item in enumerate(workers):
        path = f"delegation.workers[{index}]"
        worker = _object(item, path, errors)
        worker_id = worker.get("id")
        node_id = worker.get("node")
        if not _is_string(worker_id) or worker_id in worker_ids:
            errors.append(f"{path}.id must be unique and non-empty")
        else:
            worker_ids.add(worker_id)
            if worker_id == root_task_id:
                errors.append(f"{path}.id must differ from the root task ID")
        if worker.get("root_task_id") != root_task_id or worker.get("parent_task_id") != root_task_id:
            errors.append(f"{path} must be a depth-one child of the recorded root task")
        if not _is_integer(worker.get("depth")) or worker.get("depth") != 1:
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
        output_contract = worker.get("output_contract")
        if not _is_string(output_contract) or output_contract not in node.get("outputs", []):
            errors.append(f"{path}.output_contract must match one declared node output artifact")
        minimized_inputs = worker.get("minimized_inputs")
        if not _string_list(minimized_inputs):
            errors.append(f"{path}.minimized_inputs must be a non-empty string list")
        else:
            required_inputs = {
                edge_artifacts.get((source, target))
                for source, target in selected_edges
                if target == node_id and _is_string(edge_artifacts.get((source, target)))
            }
            if set(minimized_inputs) != required_inputs or len(minimized_inputs) != len(required_inputs):
                errors.append(f"{path}.minimized_inputs must exactly match selected incoming artifacts")
        if not _string_list(worker.get("stop_conditions")):
            errors.append(f"{path}.stop_conditions must be a non-empty string list")
        if worker.get("effort") not in {"low", "medium", "high", "xhigh"}:
            errors.append(f"{path}.effort is invalid")
        if not _is_string(worker.get("effort_rationale")):
            errors.append(f"{path}.effort_rationale must be non-empty")
        allowance = worker.get("remaining_task_allowance")
        if not _is_integer(allowance) or allowance != 0:
            errors.append(f"{path}.remaining_task_allowance must be 0 because recursive delegation is forbidden")
    safe_max_active = max_active if _is_integer(max_active) else -1
    if active_workers > safe_max_active:
        errors.append("delegation active workers exceed max_active_workers")


def _validate_plan_impl(packet: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _is_integer(packet.get("schema_version")) or packet.get("schema_version") != 1:
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
    project_id = packet.get("project_id")
    normalized_project = project_id.strip().casefold() if isinstance(project_id, str) else ""
    exact_project = (
        isinstance(project_id, str)
        and project_id == project_id.strip()
        and bool(ID_RE.fullmatch(project_id))
        and normalized_project not in {"not-required", "unresolved", "unknown"}
    )
    raw_disposition = packet.get("preflight", {}).get("disposition")
    truthful_unresolved_stop = (
        raw_disposition in {"ask-user", "escalate-approval"} and project_id == "unresolved"
    )
    if interaction in {"substantive-read", "mutating"} and not exact_project and not truthful_unresolved_stop:
        errors.append("substantive plans require one exact resolved project_id")
    acceptance = packet.get("acceptance")
    if not _string_list(acceptance):
        errors.append("acceptance must be a non-empty string list")

    selected, selected_edges, nodes = _validate_selected_graph(packet, graph, errors)
    selected_set = set(selected)
    confidence, disposition = _validate_preflight(packet, errors)
    stopping = disposition in {"ask-user", "escalate-approval"}
    risk_floor = packet.get("preflight", {}).get("risk")
    _validate_authority(packet, interaction, selected, risk_floor, disposition, errors)
    selected_handlers = {
        nodes[node_id].get("handler")
        for node_id in selected
        if node_id in nodes and nodes[node_id].get("kind") == "capability"
    }
    graph_capability_handlers = {
        node.get("handler")
        for node in nodes.values()
        if node.get("kind") == "capability"
    }
    for index, preview in enumerate(packet.get("authority", {}).get("effect_previews", [])):
        if (
            isinstance(preview, dict)
            and preview.get("handler") not in selected_handlers
            and not (stopping and preview.get("handler") in graph_capability_handlers)
        ):
            errors.append(
                f"authority.effect_previews[{index}].handler must identify a selected capability handler"
            )
    _validate_delegation(packet, graph, selected, selected_edges, nodes, errors)
    available_workers = [
        worker
        for worker in packet.get("delegation", {}).get("workers", [])
        if isinstance(worker, dict) and worker.get("status") in {"planned", "active", "complete"}
    ]
    for assessment_node in sorted(
        node_id for node_id in selected_set if nodes.get(node_id, {}).get("execution") == "fresh-worker"
    ):
        assessors = [
            worker
            for worker in available_workers
            if worker.get("node") == assessment_node
            and worker.get("skill") == nodes[assessment_node].get("handler")
            and worker.get("authority") == "read-only"
        ]
        if len(assessors) != 1:
            errors.append(
                f"selected fresh-worker node {assessment_node} requires exactly one separately planned worker"
            )
    if risk_floor in {"R2", "R3"}:
        evaluator_workers = [
            worker
            for worker in packet.get("delegation", {}).get("workers", [])
            if isinstance(worker, dict)
            and worker.get("node") == "postflight-evaluate"
            and worker.get("skill") == "project-ops-evaluate"
            and worker.get("authority") == "read-only"
            and worker.get("status") in {"planned", "active"}
        ]
        if len(evaluator_workers) != 1:
            errors.append("R2 and R3 plans require exactly one planned fresh postflight evaluator worker")

    always_required = {"trigger", "triage", "terminal"}
    if not stopping:
        always_required.update({"readiness-screen", "postflight-evaluate"})
    missing = sorted(always_required - selected_set)
    if missing:
        errors.append(f"plan is missing required control nodes: {', '.join(missing)}")
    if interaction == "simple" and not stopping:
        if "direct-answer" not in selected_set:
            errors.append("simple plans must select direct-answer")
        forbidden = selected_set & {"memory-orient", "preflight-evaluate", "dispatch", "memory-close"}
        if forbidden:
            errors.append("simple plans cannot force substantive lifecycle nodes")
        if disposition != "answer-directly":
            errors.append("simple plans require answer-directly disposition")
    if interaction in {"substantive-read", "mutating"} and not stopping:
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
        if interaction == "mutating" and disposition != "execute-graph":
            errors.append("authorized mutation requires execute-graph disposition")
        if "delivery" in selected_set:
            if interaction != "mutating":
                errors.append("delivery execution requires mutating interaction_class")
            delivery_stages = {"functional-qa", "final-assurance"}
            if not delivery_stages.issubset(selected_set):
                errors.append("delivery execution requires Functional QA and Final Assurance nodes")
            for edge in (
                ("delivery", "functional-qa"),
                ("functional-qa", "final-assurance"),
                ("final-assurance", "join"),
            ):
                if edge not in selected_edges:
                    errors.append(f"delivery execution requires stage edge {edge[0]}->{edge[1]}")
            if ("delivery", "join") in selected_edges:
                errors.append("delivery execution cannot select the stopped-before-review delivery->join bypass")
            stage_workers = {
                node_id: next(
                    (worker for worker in available_workers if worker.get("node") == node_id),
                    {},
                )
                for node_id in delivery_stages
            }
            if sum(worker.get("status") == "active" for worker in stage_workers.values()) > 1:
                errors.append("Functional QA and Final Assurance cannot be active simultaneously")
            final_status = stage_workers.get("final-assurance", {}).get("status")
            functional_status = stage_workers.get("functional-qa", {}).get("status")
            if final_status in {"active", "complete"} and functional_status != "complete":
                errors.append("Final Assurance cannot start before Functional QA completes")
    if stopping:
        if "needs-user-decision" not in selected_set and "human-approval" not in selected_set:
            errors.append("ask-user or escalate-approval must select a root decision node")
        if "authorized-execution" in selected_set:
            errors.append("a stopped plan cannot select authorized execution")
    if interaction == "mutating" and confidence in {"low", "insufficient"} and not stopping:
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
    if interaction == "simple" and not stopping and (
        memory.get("orientation") != "not-required" or memory.get("closure") != "not-required"
    ):
        errors.append("simple plans must keep memory orientation and closure not-required")
    if interaction in {"substantive-read", "mutating"} and not stopping and memory.get("closure") != "required":
        errors.append("substantive plans require a memory-close disposition")
    if stopping and memory.get("closure") not in {"not-required", "required"}:
        errors.append("stopped plans require an explicit memory disposition")
    if scope_mode in {"read-only", "review-only", "diagnosis-only"} and memory.get("durable_write") != "not-planned":
        errors.append("explicit non-write scope must suppress every durable memory write and receipt")
    return errors


def validate_plan(packet: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    if not isinstance(packet, dict):
        return ["plan packet must be an object"]
    try:
        return _validate_plan_impl(packet, graph)
    except STRUCTURE_EXCEPTIONS:
        return ["plan packet contains invalid nested field types"]


def _validate_closure_impl(
    packet: dict[str, Any], graph: dict[str, Any], plan: dict[str, Any] | None = None
) -> list[str]:
    errors: list[str] = []
    if plan is None:
        errors.append("closure validation requires the exact bound plan")
    if not _is_integer(packet.get("schema_version")) or packet.get("schema_version") != 1:
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
            "trigger": plan.get("trigger"),
            "selected_nodes": plan.get("selected_nodes"),
            "selected_edges": plan.get("selected_edges"),
        }
        for field, expected in bindings.items():
            if packet.get(field) != expected:
                errors.append(f"closure {field} does not match the bound plan")
        if packet.get("authority_receipt_id") != plan.get("authority", {}).get("receipt_id"):
            errors.append("closure authority receipt does not match the bound plan")
        if packet.get("risk") != plan.get("preflight", {}).get("risk"):
            errors.append("closure risk does not match the bound plan risk floor")
    _validate_trigger(packet, errors)
    interaction = packet.get("interaction_class")
    if interaction not in INTERACTION_CLASSES:
        errors.append("interaction_class is invalid")
        interaction = "simple"
    selected, _, selected_node_definitions = _validate_selected_graph(packet, graph, errors)

    results = _list(packet.get("node_results"), "node_results", errors)
    result_nodes: set[str] = set()
    result_status_by_node: dict[str, str] = {}
    result_evidence_by_node: dict[str, set[str]] = {}
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
            if _is_string(node_id):
                result_status_by_node[node_id] = status
        if not _is_string(result.get("summary")):
            errors.append(f"{path}.summary must be non-empty")
        if not isinstance(result.get("evidence_refs"), list) or not all(
            _is_string(value) for value in result.get("evidence_refs", [])
        ):
            errors.append(f"{path}.evidence_refs must be a string list")
        elif _is_string(node_id):
            result_evidence_by_node[node_id] = set(result.get("evidence_refs", []))
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
        elif status in {"pass", "limited"} and not result.get("evidence_refs"):
            errors.append(f"{path}.evidence_refs must contain direct evidence for passing acceptance")
    if not acceptance:
        errors.append("acceptance_results must be non-empty")
    if plan is not None:
        planned_acceptance = plan.get("acceptance", [])
        recorded_acceptance = [
            item.get("item") for item in acceptance if isinstance(item, dict)
        ]
        if recorded_acceptance != planned_acceptance:
            errors.append("acceptance_results must exactly cover the bound plan acceptance contract")

    effects = _list(packet.get("external_effects"), "external_effects", errors)
    unverified_effect = False
    recorded_effects: list[tuple[str, str, str, str]] = []
    recorded_effect_ids: set[str] = set()
    for index, item in enumerate(effects):
        path = f"external_effects[{index}]"
        effect = _object(item, path, errors)
        for field in ("effect_id", "target", "action", "handler", "authority_receipt_id"):
            if not _is_string(effect.get(field)):
                errors.append(f"{path}.{field} must be non-empty")
        effect_id = effect.get("effect_id")
        if _is_string(effect_id):
            if effect_id in recorded_effect_ids:
                errors.append(f"{path}.effect_id must be unique")
            recorded_effect_ids.add(effect_id)
        recorded_effects.append(
            (effect.get("effect_id"), effect.get("target"), effect.get("action"), effect.get("handler"))
        )
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

    approval_decision = packet.get("approval_decision", "not-required")
    if approval_decision not in {"not-required", "approved", "denied", "deferred"}:
        errors.append("approval_decision is invalid")
    if plan is not None:
        planned_effects = [
            (item.get("effect_id"), item.get("target"), item.get("action"), item.get("handler"))
            for item in plan.get("authority", {}).get("effect_previews", [])
            if isinstance(item, dict)
        ]
        plan_authority = plan.get("authority", {}).get("status")
        if plan_authority == "approval-required":
            if approval_decision == "not-required":
                errors.append("approval-required closures must record the root approval decision")
            if recorded_effects:
                errors.append("approval-required plans cannot produce effects; create a new authorized plan")
        else:
            if approval_decision != "not-required":
                errors.append("approval_decision must be not-required when the bound plan is already authorized")
            if recorded_effects != planned_effects:
                errors.append("external effects must exactly match the bound plan effect previews")
        if recorded_effects:
            if result_status_by_node.get("authorized-execution") != "pass":
                errors.append("recorded effects require a passing authorized-execution node result")

    worker_closures = _list(packet.get("worker_closures"), "worker_closures", errors)
    closure_workers: set[str] = set()
    worker_outcomes: dict[str, str] = {}
    worker_evidence_by_id: dict[str, set[str]] = {}
    worker_cards_by_id: dict[str, dict[str, Any]] = {}
    worker_needed_parent_decision = False
    parent_resolution_receipts: list[str] = []
    for index, item in enumerate(worker_closures):
        path = f"worker_closures[{index}]"
        card = _object(item, path, errors)
        worker_id = card.get("worker_id")
        if not _is_string(worker_id) or worker_id in closure_workers:
            errors.append(f"{path}.worker_id must be unique and non-empty")
        else:
            closure_workers.add(worker_id)
            worker_cards_by_id[worker_id] = card
            if worker_id == packet.get("root_task_id"):
                errors.append(f"{path}.worker_id must differ from the root task ID")
        if card.get("root_task_id") != packet.get("root_task_id") or card.get("parent_task_id") != packet.get("root_task_id"):
            errors.append(f"{path} must bind to the root task")
        outcome = card.get("outcome")
        if outcome not in {"complete", "limited", "NEEDS_PARENT_DECISION", "failed"}:
            errors.append(f"{path}.outcome is invalid")
        if outcome == "NEEDS_PARENT_DECISION":
            worker_needed_parent_decision = True
            if not _is_string(card.get("parent_resolution_receipt")):
                errors.append(f"{path}.parent_resolution_receipt is required after NEEDS_PARENT_DECISION")
            else:
                parent_resolution_receipts.append(card["parent_resolution_receipt"])
        if _is_string(worker_id) and _is_string(outcome):
            worker_outcomes[worker_id] = outcome
        if not _string_list(card.get("evidence_refs")):
            errors.append(f"{path}.evidence_refs must be a non-empty string list")
        elif _is_string(worker_id):
            worker_evidence_by_id[worker_id] = set(card["evidence_refs"])
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
            if isinstance(item, dict) and _is_string(item.get("id"))
        }
        if closure_workers != planned_workers:
            errors.append("worker_closures must exactly cover the bound plan workers")
        planned_worker_nodes = {
            item.get("id"): item.get("node")
            for item in plan.get("delegation", {}).get("workers", [])
            if isinstance(item, dict) and _is_string(item.get("id"))
        }
        for worker_id, node_id in planned_worker_nodes.items():
            node_kind = selected_node_definitions.get(node_id, {}).get("kind")
            if node_kind not in {"assessment", "evaluation"}:
                continue
            worker_verdict = worker_cards_by_id.get(worker_id, {}).get("verdict")
            allowed_verdicts = (
                {"PASS_HANDOFF", "BLOCK_REMEDIATE", "ESCALATE_APPROVAL"}
                if node_kind == "assessment"
                else GENERAL_VERDICTS
            )
            if worker_verdict not in allowed_verdicts:
                errors.append(
                    f"worker closure {worker_id} must record a valid structured {node_kind} verdict"
                )
        for node_id in selected:
            if selected_node_definitions.get(node_id, {}).get("execution") != "fresh-worker":
                continue
            node_workers = [
                worker_id for worker_id, worker_node in planned_worker_nodes.items() if worker_node == node_id
            ]
            if len(node_workers) != 1:
                continue
            worker_id = node_workers[0]
            if result_status_by_node.get(node_id) in {"pass", "limited"}:
                if worker_outcomes.get(worker_id) != "complete":
                    errors.append(f"passing fresh-worker node {node_id} requires a complete worker closure")
                if not (
                    result_evidence_by_node.get(node_id, set())
                    & worker_evidence_by_id.get(worker_id, set())
                ):
                    errors.append(f"passing fresh-worker node {node_id} must cite its worker evidence")
                if worker_cards_by_id.get(worker_id, {}).get("verdict") != "PASS_HANDOFF":
                    errors.append(f"passing assessment node {node_id} requires PASS_HANDOFF")
    if worker_needed_parent_decision and not ({"needs-user-decision", "human-approval"} & set(selected)):
        errors.append("worker NEEDS_PARENT_DECISION requires a selected root decision node")
    for receipt in parent_resolution_receipts:
        bound = any(
            result_status_by_node.get(node_id) == "pass"
            and receipt in result_evidence_by_node.get(node_id, set())
            for node_id in ("needs-user-decision", "human-approval")
        )
        if not bound:
            errors.append("worker parent_resolution_receipt must bind to passing root-decision evidence")
    if plan is not None:
        for worker_id, node_id in planned_worker_nodes.items():
            if selected_node_definitions.get(node_id, {}).get("execution") == "fresh-worker":
                continue
            if result_status_by_node.get(node_id) not in {"pass", "limited"}:
                continue
            card = worker_cards_by_id.get(worker_id, {})
            outcome = worker_outcomes.get(worker_id)
            resolution_receipt = card.get("parent_resolution_receipt")
            resolved_parent_decision = outcome == "NEEDS_PARENT_DECISION" and any(
                result_status_by_node.get(decision_node) == "pass"
                and resolution_receipt in result_evidence_by_node.get(decision_node, set())
                for decision_node in ("needs-user-decision", "human-approval")
            )
            if outcome != "complete" and not resolved_parent_decision:
                errors.append(f"passing delegated node {node_id} requires a resolved worker closure")
            if not (
                result_evidence_by_node.get(node_id, set())
                & worker_evidence_by_id.get(worker_id, set())
            ):
                errors.append(f"passing delegated node {node_id} must cite its worker evidence")

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
    evaluator = postflight.get("evaluator")
    evaluator_id = postflight.get("evaluator_task_id")
    evaluator_key = evaluator_id if _is_string(evaluator_id) else ""
    independent = postflight.get("independent")
    if evaluator == "root":
        if evaluator_id != packet.get("root_task_id"):
            errors.append("root evaluator_task_id must match the root task")
        if independent is not False:
            errors.append("the root evaluator cannot claim independent evaluation")
    if evaluator == "fresh-worker":
        if evaluator_id == packet.get("root_task_id"):
            errors.append("the root task cannot claim independent evaluation")
        if independent is not True:
            errors.append("fresh-worker evaluation must be marked independent")
        planned_evaluators = {
            worker.get("id")
            for worker in plan.get("delegation", {}).get("workers", [])
            if isinstance(worker, dict)
            and _is_string(worker.get("id"))
            and worker.get("node") == "postflight-evaluate"
            and worker.get("skill") == "project-ops-evaluate"
            and worker.get("authority") == "read-only"
            and worker.get("status") in {"planned", "active"}
        } if plan is not None else set()
        if (
            evaluator_key not in planned_evaluators
            or evaluator_key not in closure_workers
            or worker_outcomes.get(evaluator_key) != "complete"
        ):
            errors.append("independent evaluator identity must match its planned worker and closure card")
        evidence_basis = postflight.get("evidence_basis")
        evidence_basis_set = {
            item for item in evidence_basis if _is_string(item)
        } if isinstance(evidence_basis, list) else set()
        if not (evidence_basis_set & worker_evidence_by_id.get(evaluator_key, set())):
            errors.append("fresh-worker postflight must cite the independent evaluator evidence")
        if worker_cards_by_id.get(evaluator_key, {}).get("verdict") != verdict:
            errors.append("fresh-worker evaluator verdict must match the overall postflight verdict")
    if risk in {"R2", "R3"} and (independent is not True or evaluator != "fresh-worker"):
        errors.append("R2 and R3 closures require a fresh independent evaluator")

    if verdict == "PASS" and any(status != "pass" for status in acceptance_statuses):
        errors.append("PASS requires every acceptance item to pass")
    if verdict == "PASS" and (any(status != "pass" for status in node_statuses) or unverified_effect):
        errors.append("PASS requires every selected node to pass and every effect to be verified")
    if verdict == "PASS" and any(outcome in {"limited", "failed"} for outcome in worker_outcomes.values()):
        errors.append("PASS cannot include limited or failed worker outcomes")
    if verdict == "PASS_WITH_LIMITATIONS":
        if any(status in {"fail", "unverified"} for status in acceptance_statuses):
            errors.append("PASS_WITH_LIMITATIONS cannot include failed or unverified acceptance")
        if any(status in {"failed", "skipped"} for status in node_statuses) or unverified_effect:
            errors.append("PASS_WITH_LIMITATIONS cannot include failed/skipped nodes or unverified effects")
        if any(outcome == "failed" for outcome in worker_outcomes.values()):
            errors.append("PASS_WITH_LIMITATIONS cannot include failed worker outcomes")
    if verdict in {"PASS", "PASS_WITH_LIMITATIONS"} and postflight.get("confidence") == "insufficient":
        errors.append("a passing verdict cannot have insufficient final confidence")

    if plan is not None and "delivery" in plan.get("selected_nodes", []):
        functional_status = result_status_by_node.get("functional-qa")
        assurance_status = result_status_by_node.get("final-assurance")
        if functional_status != "pass" and assurance_status != "skipped":
            errors.append("Final Assurance must be skipped when Functional QA does not pass")
        if result_status_by_node.get("authorized-execution") == "pass" and (
            functional_status != "pass" or assurance_status != "pass"
        ):
            errors.append("delivery authorized execution requires passing Functional QA and Final Assurance")
        if recorded_effects and (functional_status != "pass" or assurance_status != "pass"):
            errors.append("delivery effects require passing Functional QA and Final Assurance")

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


def validate_closure(
    packet: dict[str, Any], graph: dict[str, Any], plan: dict[str, Any] | None = None
) -> list[str]:
    if not isinstance(packet, dict):
        return ["closure packet must be an object"]
    try:
        return _validate_closure_impl(packet, graph, plan)
    except STRUCTURE_EXCEPTIONS:
        return ["closure packet contains invalid nested field types"]


def validate_packet(
    packet: dict[str, Any], graph: dict[str, Any] | None = None, plan: dict[str, Any] | None = None
) -> list[str]:
    if not isinstance(packet, dict):
        return ["packet must be an object"]
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
