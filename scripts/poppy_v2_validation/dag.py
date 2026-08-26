"""Per-run execution DAG contracts owned exclusively by POP-V2-005."""

from __future__ import annotations

import copy
import re
from collections import defaultdict, deque
from datetime import datetime
from functools import lru_cache
from typing import Any

from .authority import canonical_digest
from .capability import capability_binding_digest
from .effect import effect_binding_digest


ENTRY_BY_CODE = {
    "POP2-INV-DAG-602": "invariant.dag.nodes-necessary-and-connected",
    "POP2-INV-DAG-612": "invariant.dag.acyclic",
    "POP2-INV-DAG-613": "invariant.dag.capability-binding-exact",
    "POP2-INV-DAG-614": "invariant.dag.edge-schema-match",
    "POP2-BEH-DAG-615": "invariant.dag.dependencies-before-ready",
    "POP2-BEH-DAG-616": "invariant.dag.attempt-sequence",
    "POP2-BEH-DAG-617": "invariant.dag.node-status-legal",
    "POP2-BEH-DAG-618": "invariant.dag.join-complete",
    "POP2-INV-DAG-619": "invariant.dag.effect-exactly-bound",
    "POP2-INV-DAG-620": "invariant.dag.registry-binding-immutable",
    "POP2-INV-DAG-621": "invariant.dag.receipt-eligible-and-minimized",
}
LEGAL_STATUS_TRANSITIONS = (
    "BLOCKED|CANCELLED", "BLOCKED|READY", "PLANNED|BLOCKED", "PLANNED|CANCELLED",
    "PLANNED|READY", "READY|CANCELLED", "READY|RUNNING", "RUNNING|CANCELLED",
    "RUNNING|FAILED", "RUNNING|LIMITED", "RUNNING|SUCCEEDED",
)
TERMINAL_STATUSES = frozenset({"SUCCEEDED", "LIMITED", "FAILED", "CANCELLED"})
RETENTION_FIELDS = (
    ("material_evidence", "material_evidence_refs", "evidence_refs"),
    ("decision", "decision_refs", "decision_refs"),
    ("verified_effect", "verified_effect_receipt_refs", "effect_receipt_refs"),
    ("safety_finding", "safety_finding_refs", "safety_finding_refs"),
    ("reusable_learning", "reusable_learning_refs", "reusable_learning_refs"),
)
ANCHOR_KEYS = {
    "run_id", "plan_revision", "objective_binding_record_digest", "revision_record_digest",
    "revision_structure_digest", "revision_history_digest", "node_record_digests",
    "node_structural_digests", "node_schema_digests", "node_capability_digests",
    "node_effect_digests", "edge_record_digests", "edge_topology_digests",
    "edge_contract_digests", "assignment_record_digests", "status_record_digests",
    "status_transition_digests", "attempt_record_digests", "outcome_record_digests",
    "outcome_execution_digests", "outcome_effect_digests", "outcome_retention_digests",
    "artifact_reference_record_digests", "artifact_binding_record_digests",
    "registry_identity", "capability_contracts", "schema_bindings", "effect_proposal_digests",
    "status_transition_rules", "retention_sources", "minimized_receipt_record_digest",
    "minimized_receipt_semantic_digest",
}
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
UUID_V7_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
ANCHOR_DIGEST_MAPS = (
    "node_record_digests", "node_structural_digests", "node_schema_digests",
    "node_capability_digests", "node_effect_digests", "edge_record_digests",
    "edge_topology_digests", "edge_contract_digests", "assignment_record_digests",
    "status_record_digests", "status_transition_digests", "attempt_record_digests",
    "outcome_record_digests", "outcome_execution_digests", "outcome_effect_digests",
    "outcome_retention_digests", "artifact_reference_record_digests",
    "artifact_binding_record_digests", "capability_contracts", "schema_bindings",
    "effect_proposal_digests",
)
RETENTION_SOURCE_FIELDS = tuple(field for _reason, field, _receipt in RETENTION_FIELDS)

REVISION_STRUCTURE_FIELDS = ("node_ids", "edge_ids", "entry_node_ids", "terminal_node_ids")
REVISION_HISTORY_FIELDS = (
    "$schema", "x-poppy-schema-version", "revision_id", "run_id", "plan_revision",
    "registry_id", "registry_version", "registry_digest", "compiled_at", "previous_revision_digest",
)
NODE_STRUCTURAL_FIELDS = (
    "$schema", "x-poppy-schema-version", "node_id", "selected_by_objective_clause_id",
    "necessity_reason", "activation_state", "join_kind",
)
NODE_SCHEMA_FIELDS = ("node_id", "input_schema_ids", "output_schema_ids")
NODE_CAPABILITY_FIELDS = ("node_id", "capability_binding")
NODE_EFFECT_FIELDS = ("node_id", "effect_binding")
EDGE_TOPOLOGY_FIELDS = ("edge_id", "from_node_id", "to_node_id", "required")
EDGE_CONTRACT_FIELDS = (
    "$schema", "x-poppy-schema-version", "edge_id", "artifact_name", "artifact_schema_id",
    "artifact_schema_version", "artifact_schema_digest",
)
STATUS_TRANSITION_FIELDS = (
    "$schema", "x-poppy-schema-version", "status_record_id", "run_id", "plan_revision",
    "node_id", "sequence", "status", "reason_codes",
)
OUTCOME_EXECUTION_FIELDS = (
    "$schema", "x-poppy-schema-version", "outcome_id", "run_id", "plan_revision", "node_id",
    "status", "attempt_id", "artifact_refs", "evidence_refs", "completed_at",
)
OUTCOME_EFFECT_FIELDS = ("outcome_id", "effect_id", "effect_digest")
OUTCOME_RETENTION_FIELDS = ("outcome_id", "material_evidence", "evidence_refs")
MINIMIZED_RECEIPT_SEMANTIC_FIELDS = (
    "$schema", "x-poppy-schema-version", "receipt_id", "run_id", "plan_revision",
    "objective_digest", "terminal_status", "retention_reasons", "evidence_refs",
    "effect_receipt_refs", "decision_refs", "safety_finding_refs", "reusable_learning_refs",
    "recorded_at",
)


def _finding(code: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code, "owner_decision_id": "POP-V2-005", "manifest_entry_id": ENTRY_BY_CODE[code],
        "layer": "BEHAVIOR" if code.startswith("POP2-BEH-") else "INVARIANT",
        "locator": "synthetic:dag-bundle", "json_pointer": pointer, "message": message,
    }


def _digest_without(value: Any, field: str) -> str | None:
    if not isinstance(value, dict):
        return None
    candidate = copy.deepcopy(value)
    candidate.pop(field, None)
    return canonical_digest(candidate)


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and DIGEST_PATTERN.fullmatch(value) is not None


def _is_digest_map(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and all(isinstance(key, str) and key and _is_digest(digest) for key, digest in value.items())
    )


def _valid_dag_trust_anchor(anchor: Any) -> bool:
    """Validate the complete independent anchor before any nested value is used."""
    if not isinstance(anchor, dict) or set(anchor) != ANCHOR_KEYS:
        return False
    run_id = anchor.get("run_id")
    if not isinstance(run_id, str) or UUID_V7_PATTERN.fullmatch(run_id) is None:
        return False
    if not isinstance(anchor.get("plan_revision"), int) or isinstance(anchor["plan_revision"], bool) or anchor["plan_revision"] < 1:
        return False
    scalar_digests = (
        "objective_binding_record_digest", "revision_record_digest", "revision_structure_digest",
        "revision_history_digest", "minimized_receipt_record_digest",
        "minimized_receipt_semantic_digest",
    )
    if any(not _is_digest(anchor.get(name)) for name in scalar_digests):
        return False
    if any(not _is_digest_map(anchor.get(name)) for name in ANCHOR_DIGEST_MAPS):
        return False
    node_keys = set(anchor["node_record_digests"])
    edge_keys = set(anchor["edge_record_digests"])
    outcome_keys = set(anchor["outcome_record_digests"])
    if not node_keys:
        return False
    if any(set(anchor[name]) != node_keys for name in (
        "node_structural_digests", "node_schema_digests", "node_capability_digests",
        "node_effect_digests",
    )):
        return False
    if any(set(anchor[name]) != edge_keys for name in ("edge_topology_digests", "edge_contract_digests")):
        return False
    if any(set(anchor[name]) != outcome_keys for name in (
        "outcome_execution_digests", "outcome_effect_digests", "outcome_retention_digests",
    )):
        return False
    if any(not anchor[name] for name in (
        "assignment_record_digests", "status_record_digests", "status_transition_digests",
        "attempt_record_digests", "outcome_record_digests", "capability_contracts",
    )):
        return False
    registry = anchor.get("registry_identity")
    if (
        not isinstance(registry, dict)
        or set(registry) != {"registry_id", "registry_version", "registry_digest"}
        or not all(isinstance(registry.get(name), str) and registry[name] for name in ("registry_id", "registry_version"))
        or not _is_digest(registry.get("registry_digest"))
    ):
        return False
    if anchor.get("status_transition_rules") != list(LEGAL_STATUS_TRANSITIONS):
        return False
    sources = anchor.get("retention_sources")
    if not isinstance(sources, dict) or set(sources) != set(RETENTION_SOURCE_FIELDS):
        return False
    for field in RETENTION_SOURCE_FIELDS:
        refs = sources.get(field)
        if (
            not isinstance(refs, list)
            or any(not isinstance(ref, str) or not ref for ref in refs)
            or refs != sorted(set(refs))
        ):
            return False
    return True


@lru_cache(maxsize=1)
def _effect_schema_store() -> Any:
    # Import lazily to reuse the repository's authoritative schema evaluator
    # without creating a package-import cycle during validator initialization.
    from validate_v2_schemas import SchemaStore
    return SchemaStore()


def _authoritative_effect_proposal_valid(proposal: Any) -> bool:
    if not isinstance(proposal, dict):
        return False
    try:
        return not _effect_schema_store().validate(proposal, "poppy://schema/effect/proposal/v1")
    except (OSError, ValueError, TypeError):
        return False


def dag_revision_digest(revision: dict[str, Any]) -> str:
    value = _digest_without(revision, "revision_digest")
    if value is None:
        raise ValueError("DAG revision must be an object")
    return value


def dag_record_digest(record: dict[str, Any], digest_field: str) -> str:
    value = _digest_without(record, digest_field)
    if value is None:
        raise ValueError("DAG record must be an object")
    return value


def finalize_dag_fixture(bundle: dict[str, Any]) -> dict[str, Any]:
    """Finalize only checked-in synthetic fixture templates; validation never repairs records."""
    value = copy.deepcopy(bundle)
    objective = value["objective_binding"]
    objective["binding_digest"] = dag_record_digest(objective, "binding_digest")
    for node in value["nodes"]:
        binding = node["capability_binding"]
        binding["binding_digest"] = capability_binding_digest(binding)
    effect_values = value["effect_proposals"]
    for effect in effect_values:
        effect["effect_digest"] = effect_binding_digest(effect)
    effect_ids = [item.get("effect_id") for item in effect_values]
    effects = {
        item["effect_id"]: item for item in effect_values
        if len(effect_ids) == len(set(effect_ids)) and isinstance(item.get("effect_id"), str)
    }
    for node in value["nodes"]:
        binding = node.get("effect_binding")
        if isinstance(binding, dict) and binding.get("effect_id") in effects:
            binding["effect_digest"] = effects[binding["effect_id"]]["effect_digest"]
    for outcome in value["outcomes"]:
        if outcome.get("effect_id") in effects:
            outcome["effect_digest"] = effects[outcome["effect_id"]]["effect_digest"]
    for collection, field in (
        (value["nodes"], "node_digest"), (value["edges"], "edge_digest"),
        (value["assignments"], "assignment_digest"), (value["attempts"], "attempt_digest"),
        (value["outcomes"], "outcome_digest"), (value["artifact_references"], "reference_digest"),
        (value["artifact_bindings"], "binding_digest"),
    ):
        for record in collection:
            record[field] = dag_record_digest(record, field)
    previous_by_node: dict[str, str | None] = {}
    for status in value["statuses"]:
        status["previous_status_digest"] = previous_by_node.get(status["node_id"])
        status["status_digest"] = dag_record_digest(status, "status_digest")
        previous_by_node[status["node_id"]] = status["status_digest"]
    revision = value["revision"]
    revision["objective_binding_digest"] = objective["binding_digest"]
    revision["revision_digest"] = dag_revision_digest(revision)
    receipt = value.get("minimized_receipt")
    if isinstance(receipt, dict):
        receipt["dag_revision_digest"] = revision["revision_digest"]
        terminal_ids = set(revision["terminal_node_ids"])
        terminal_outcomes = [item for item in value["outcomes"] if item["node_id"] in terminal_ids]
        if len(terminal_outcomes) == 1:
            receipt["outcome_digest"] = terminal_outcomes[0]["outcome_digest"]
        receipt["receipt_digest"] = dag_record_digest(receipt, "receipt_digest")
    return value


def build_dag_trust_anchor(bundle: dict[str, Any]) -> dict[str, Any]:
    """Build a fixture-authoring anchor; callers persist it independently of runtime records."""
    b = finalize_dag_fixture(bundle)
    def records(name: str, key: str) -> dict[str, str]:
        identities = [item.get(key) for item in b[name]]
        if any(not isinstance(identity, str) or not identity for identity in identities) or len(identities) != len(set(identities)):
            raise ValueError(f"DAG fixture {name} identities must be unique non-empty strings")
        return {str(item[key]): canonical_digest(item) for item in b[name]}
    def projections(name: str, key: str, fields: tuple[str, ...]) -> dict[str, str]:
        return {str(item[key]): canonical_digest({field: item.get(field) for field in fields}) for item in b[name]}
    revision, objective = b["revision"], b["objective_binding"]
    material = sorted({ref for item in b["outcomes"] if item.get("material_evidence") is True for ref in item.get("evidence_refs", [])})
    sources = b.get("retention_sources", {})
    retention_sources = {"material_evidence_refs": material, **{field: sorted(sources.get(field, [])) for _reason, field, _receipt in RETENTION_FIELDS[1:]}}
    return {
        "run_id": revision["run_id"], "plan_revision": revision["plan_revision"],
        "objective_binding_record_digest": canonical_digest(objective),
        "revision_record_digest": canonical_digest(revision),
        "revision_structure_digest": canonical_digest({f: revision.get(f) for f in REVISION_STRUCTURE_FIELDS}),
        "revision_history_digest": canonical_digest({f: revision.get(f) for f in REVISION_HISTORY_FIELDS}),
        "node_record_digests": records("nodes", "node_id"),
        "node_structural_digests": projections("nodes", "node_id", NODE_STRUCTURAL_FIELDS),
        "node_schema_digests": projections("nodes", "node_id", NODE_SCHEMA_FIELDS),
        "node_capability_digests": projections("nodes", "node_id", NODE_CAPABILITY_FIELDS),
        "node_effect_digests": projections("nodes", "node_id", NODE_EFFECT_FIELDS),
        "edge_record_digests": records("edges", "edge_id"),
        "edge_topology_digests": projections("edges", "edge_id", EDGE_TOPOLOGY_FIELDS),
        "edge_contract_digests": projections("edges", "edge_id", EDGE_CONTRACT_FIELDS),
        "assignment_record_digests": records("assignments", "assignment_id"),
        "status_record_digests": records("statuses", "status_record_id"),
        "status_transition_digests": projections("statuses", "status_record_id", STATUS_TRANSITION_FIELDS),
        "attempt_record_digests": records("attempts", "attempt_id"),
        "outcome_record_digests": records("outcomes", "outcome_id"),
        "outcome_execution_digests": projections("outcomes", "outcome_id", OUTCOME_EXECUTION_FIELDS),
        "outcome_effect_digests": projections("outcomes", "outcome_id", OUTCOME_EFFECT_FIELDS),
        "outcome_retention_digests": projections("outcomes", "outcome_id", OUTCOME_RETENTION_FIELDS),
        "artifact_reference_record_digests": records("artifact_references", "artifact_id"),
        "artifact_binding_record_digests": records("artifact_bindings", "binding_id"),
        "registry_identity": {k: revision[k] for k in ("registry_id", "registry_version", "registry_digest")},
        "capability_contracts": {"capability.synthetic.summarize@1.0.0": "sha256:76fbd30a28addb9a224d97f8e4486164c08498a0e4cb77d1e7942a38f8b73111"},
        "schema_bindings": {"poppy://schema/synthetic/result/v1@1.0.0": "sha256:3333333333333333333333333333333333333333333333333333333333333333"},
        "effect_proposal_digests": {item["effect_id"]: canonical_digest(item) for item in b["effect_proposals"]},
        "status_transition_rules": list(LEGAL_STATUS_TRANSITIONS), "retention_sources": retention_sources,
        "minimized_receipt_record_digest": canonical_digest(b.get("minimized_receipt")),
        "minimized_receipt_semantic_digest": canonical_digest({
            field: b.get("minimized_receipt", {}).get(field)
            for field in MINIMIZED_RECEIPT_SEMANTIC_FIELDS
        }),
    }


def _values(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _record_map(values: list[dict[str, Any]], key: str) -> tuple[bool, dict[str, str]]:
    ids = [item.get(key) for item in values]
    unique = all(isinstance(item, str) and item for item in ids) and len(ids) == len(set(ids))
    return unique, {str(item[key]): canonical_digest(item) for item in values if isinstance(item.get(key), str)}


def _projection_map(values: list[dict[str, Any]], key: str, fields: tuple[str, ...]) -> dict[str, str]:
    return {str(item[key]): canonical_digest({f: item.get(f) for f in fields}) for item in values if isinstance(item.get(key), str)}


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def _status_groups(statuses: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in statuses:
        if isinstance(item.get("node_id"), str):
            grouped[item["node_id"]].append(item)
    for values in grouped.values():
        values.sort(key=lambda item: item.get("sequence", -1))
    return grouped


def _first_time(groups: dict[str, list[dict[str, Any]]], node_id: str, status: str) -> datetime | None:
    return next((_timestamp(item.get("recorded_at")) for item in groups.get(node_id, []) if item.get("status") == status), None)


def _reach(starts: set[str], graph: dict[str, set[str]]) -> set[str]:
    seen, queue = set(starts), deque(starts)
    while queue:
        for target in graph.get(queue.popleft(), set()):
            if target not in seen:
                seen.add(target); queue.append(target)
    return seen


def validate_dag_invariants(bundle: dict[str, Any], trusted_anchors: dict[str, Any]) -> list[dict[str, str]]:
    anchor = trusted_anchors.get("dag", {}) if isinstance(trusted_anchors, dict) else {}
    if not _valid_dag_trust_anchor(anchor):
        return [_finding(code, "/", "the complete independent DAG trust anchor is required") for code in ENTRY_BY_CODE]
    violations: set[str] = set()
    revision = bundle.get("revision", {}) if isinstance(bundle, dict) else {}
    objective = bundle.get("objective_binding", {}) if isinstance(bundle, dict) else {}
    names = {
        "nodes": "node_id", "edges": "edge_id", "assignments": "assignment_id",
        "statuses": "status_record_id", "attempts": "attempt_id", "outcomes": "outcome_id",
        "artifact_references": "artifact_id", "artifact_bindings": "binding_id",
    }
    values = {name: _values(bundle.get(name)) for name in names}
    maps: dict[str, dict[str, str]] = {}
    unique: dict[str, bool] = {}
    for name, key in names.items():
        unique[name], maps[name] = _record_map(values[name], key)
    nodes, edges = values["nodes"], values["edges"]
    node_by_id = {item["node_id"]: item for item in nodes if isinstance(item.get("node_id"), str)}
    edge_by_id = {item["edge_id"]: item for item in edges if isinstance(item.get("edge_id"), str)}
    artifacts = {item["artifact_id"]: item for item in values["artifact_references"] if isinstance(item.get("artifact_id"), str)}
    assignments = {item["assignment_id"]: item for item in values["assignments"] if isinstance(item.get("assignment_id"), str)}
    run_id, plan_revision = revision.get("run_id"), revision.get("plan_revision")
    node_identity_exact = unique["nodes"] and set(maps["nodes"]) == set(anchor["node_record_digests"])
    artifact_identity_exact = (
        unique["artifact_references"] and unique["artifact_bindings"]
        and set(maps["artifact_references"]) == set(anchor["artifact_reference_record_digests"])
        and set(maps["artifact_bindings"]) == set(anchor["artifact_binding_record_digests"])
    )

    # Complete canonical record anchors are authoritative. Projections route a
    # changed immutable field to its accepted owner without weakening coverage.
    objective_changed = canonical_digest(objective) != anchor["objective_binding_record_digest"]
    revision_structure = canonical_digest({f: revision.get(f) for f in REVISION_STRUCTURE_FIELDS})
    revision_history = canonical_digest({f: revision.get(f) for f in REVISION_HISTORY_FIELDS})
    if objective_changed:
        violations.add("POP2-INV-DAG-602")
    if revision_structure != anchor["revision_structure_digest"]:
        violations.add("POP2-INV-DAG-602")
    if revision_history != anchor["revision_history_digest"]:
        violations.add("POP2-INV-DAG-620")
    if canonical_digest(revision) != anchor["revision_record_digest"] and not objective_changed and revision_structure == anchor["revision_structure_digest"] and revision_history == anchor["revision_history_digest"]:
        violations.add("POP2-INV-DAG-620")

    node_structural = _projection_map(nodes, "node_id", NODE_STRUCTURAL_FIELDS)
    node_schema = _projection_map(nodes, "node_id", NODE_SCHEMA_FIELDS)
    node_capability = _projection_map(nodes, "node_id", NODE_CAPABILITY_FIELDS)
    node_effect = _projection_map(nodes, "node_id", NODE_EFFECT_FIELDS)
    if not node_identity_exact or node_structural != anchor["node_structural_digests"]:
        violations.add("POP2-INV-DAG-602")
    elif maps["nodes"] != anchor["node_record_digests"]:
        if node_capability != anchor["node_capability_digests"]: violations.add("POP2-INV-DAG-613")
        if node_schema != anchor["node_schema_digests"]: violations.add("POP2-INV-DAG-614")
        if node_effect != anchor["node_effect_digests"]: violations.add("POP2-INV-DAG-619")
        if node_capability == anchor["node_capability_digests"] and node_schema == anchor["node_schema_digests"] and node_effect == anchor["node_effect_digests"]:
            violations.add("POP2-INV-DAG-602")

    # A structural node-set defect owns the whole integrated rewrite. This is
    # the fail-closed necessary-node boundary and prevents diagnostic smearing.
    if node_identity_exact:
        edge_topology = _projection_map(edges, "edge_id", EDGE_TOPOLOGY_FIELDS)
        edge_contract = _projection_map(edges, "edge_id", EDGE_CONTRACT_FIELDS)
        topology_exact = unique["edges"] and edge_topology == anchor["edge_topology_digests"]
        if not topology_exact: violations.add("POP2-INV-DAG-612")
        if topology_exact and (maps["edges"] != anchor["edge_record_digests"] or edge_contract != anchor["edge_contract_digests"]):
            violations.add("POP2-INV-DAG-614")
        if maps["assignments"] != anchor["assignment_record_digests"] or not unique["assignments"]:
            violations.add("POP2-BEH-DAG-616")
        if maps["attempts"] != anchor["attempt_record_digests"] or not unique["attempts"]:
            violations.add("POP2-BEH-DAG-616")
        outcome_execution = _projection_map(values["outcomes"], "outcome_id", OUTCOME_EXECUTION_FIELDS)
        outcome_effect = _projection_map(values["outcomes"], "outcome_id", OUTCOME_EFFECT_FIELDS)
        outcome_retention = _projection_map(values["outcomes"], "outcome_id", OUTCOME_RETENTION_FIELDS)
        if not unique["outcomes"] or outcome_execution != anchor["outcome_execution_digests"]:
            violations.add("POP2-BEH-DAG-616")
        outcome_identity_exact = unique["outcomes"] and set(maps["outcomes"]) == set(anchor["outcome_record_digests"])
        if outcome_identity_exact and outcome_effect != anchor["outcome_effect_digests"]: violations.add("POP2-INV-DAG-619")
        if outcome_identity_exact and outcome_retention != anchor["outcome_retention_digests"]: violations.add("POP2-INV-DAG-621")
        if outcome_identity_exact and maps["outcomes"] != anchor["outcome_record_digests"] and outcome_execution == anchor["outcome_execution_digests"] and outcome_effect == anchor["outcome_effect_digests"] and outcome_retention == anchor["outcome_retention_digests"]:
            violations.add("POP2-BEH-DAG-616")
        if topology_exact and (not unique["artifact_references"] or not unique["artifact_bindings"] or maps["artifact_references"] != anchor["artifact_reference_record_digests"] or maps["artifact_bindings"] != anchor["artifact_binding_record_digests"]):
            violations.add("POP2-INV-DAG-614")
    else:
        topology_exact = False

    # Smallest necessary connected plan and exact revision identity sets.
    node_ids = set(node_by_id)
    entry_ids = set(revision.get("entry_node_ids", [])) if isinstance(revision.get("entry_node_ids"), list) else set()
    terminal_ids = set(revision.get("terminal_node_ids", [])) if isinstance(revision.get("terminal_node_ids"), list) else set()
    forward: dict[str, set[str]] = defaultdict(set); reverse: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        source, target = edge.get("from_node_id"), edge.get("to_node_id")
        if source in node_ids and target in node_ids and source != target:
            forward[source].add(target); reverse[target].add(source)
    clauses = set(objective.get("clause_ids", [])) if isinstance(objective.get("clause_ids"), list) else set()
    if (
        not node_ids or set(revision.get("node_ids", [])) != node_ids
        or not entry_ids or not terminal_ids or not entry_ids.issubset(node_ids) or not terminal_ids.issubset(node_ids)
        or _reach(entry_ids, forward) != node_ids or _reach(terminal_ids, reverse) != node_ids
        or any(item.get("activation_state") != "active" or item.get("selected_by_objective_clause_id") not in clauses or not item.get("necessity_reason") or item.get("node_digest") != _digest_without(item, "node_digest") for item in nodes)
        or {item.get("selected_by_objective_clause_id") for item in nodes} != clauses
        or objective.get("binding_digest") != _digest_without(objective, "binding_digest")
    ):
        violations.add("POP2-INV-DAG-602")
    revision_edge_ids = set(revision.get("edge_ids", [])) if isinstance(revision.get("edge_ids"), list) else set()
    if revision_edge_ids != set(edge_by_id):
        violations.add(
            "POP2-INV-DAG-612"
            if revision_edge_ids == set(anchor["edge_record_digests"])
            else "POP2-INV-DAG-602"
        )

    # Acyclicity.
    indegree = {node: 0 for node in node_ids}
    for source in forward:
        for target in forward[source]: indegree[target] += 1
    queue = deque(sorted(node for node, count in indegree.items() if count == 0)); visited = 0
    while queue:
        source = queue.popleft(); visited += 1
        for target in sorted(forward.get(source, set())):
            indegree[target] -= 1
            if indegree[target] == 0: queue.append(target)
    if node_identity_exact and visited != len(node_ids): violations.add("POP2-INV-DAG-612")

    # Exact capability and registry bindings.
    registry = anchor["registry_identity"]; contracts = anchor["capability_contracts"]
    for node in nodes if node_identity_exact else []:
        binding = node.get("capability_binding", {})
        key = f"{binding.get('contract_id')}@{binding.get('contract_version')}"
        if (
            binding.get("run_id") != run_id or binding.get("registry_id") != registry.get("registry_id")
            or binding.get("registry_version") != registry.get("registry_version") or binding.get("registry_digest") != registry.get("registry_digest")
            or binding.get("contract_digest") != contracts.get(key) or binding.get("binding_digest") != capability_binding_digest(binding)
            or "latest" in str(binding.get("contract_version", "")).casefold()
        ): violations.add("POP2-INV-DAG-613")

    status_groups = _status_groups(values["statuses"])
    outcome_by_node = {item["node_id"]: item for item in values["outcomes"] if isinstance(item.get("node_id"), str)}
    bindings_by_edge: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for binding in values["artifact_bindings"]:
        if isinstance(binding.get("edge_id"), str): bindings_by_edge[binding["edge_id"]].append(binding)

    # Exact typed artifact production and consumption.
    if node_identity_exact and topology_exact and artifact_identity_exact:
        schemas = anchor["schema_bindings"]
        for edge in edges:
            expected = (edge.get("artifact_schema_id"), edge.get("artifact_schema_version"), edge.get("artifact_schema_digest"))
            key = f"{expected[0]}@{expected[1]}"; producer = node_by_id.get(str(edge.get("from_node_id"))); consumer = node_by_id.get(str(edge.get("to_node_id")))
            bs = bindings_by_edge.get(str(edge.get("edge_id")), [])
            if schemas.get(key) != expected[2] or not producer or expected[0] not in producer.get("output_schema_ids", []) or not consumer or expected[0] not in consumer.get("input_schema_ids", []) or len(bs) != 1:
                violations.add("POP2-INV-DAG-614"); continue
            binding = bs[0]; artifact = artifacts.get(str(binding.get("artifact_id")))
            if not artifact or artifact.get("producing_node_id") != edge.get("from_node_id") or (artifact.get("schema_id"), artifact.get("schema_version"), artifact.get("schema_digest")) != expected or binding.get("consumer_node_id") != edge.get("to_node_id") or (binding.get("expected_schema_id"), binding.get("expected_schema_version"), binding.get("expected_schema_digest")) != expected:
                violations.add("POP2-INV-DAG-614")

    # Dependency readiness and all-join completion are schedule owners.
    readiness_invalid = False; join_invalid = False
    if node_identity_exact and topology_exact and artifact_identity_exact:
        for node_id in node_ids:
            if node_by_id[node_id].get("join_kind") == "all": continue
            ready = _first_time(status_groups, node_id, "READY")
            if ready is None: continue
            for edge in [item for item in edges if item.get("to_node_id") == node_id and item.get("required") is True]:
                outcome = outcome_by_node.get(str(edge.get("from_node_id"))); bs = bindings_by_edge.get(str(edge.get("edge_id")), [])
                completed = _timestamp(outcome.get("completed_at")) if outcome else None; available = _timestamp(bs[0].get("available_at")) if len(bs) == 1 else None
                if not outcome or outcome.get("status") != "succeeded" or completed is None or available is None or completed >= ready or available >= ready: readiness_invalid = True
        for node in nodes:
            if node.get("join_kind") != "all": continue
            node_id = str(node.get("node_id")); incoming = [item for item in edges if item.get("to_node_id") == node_id and item.get("required") is True]
            ready = _first_time(status_groups, node_id, "READY"); running = _first_time(status_groups, node_id, "RUNNING"); outcome_time = _timestamp(outcome_by_node.get(node_id, {}).get("completed_at"))
            if len(incoming) < 2 or ready is None or running is None or outcome_time is None: join_invalid = True; continue
            for edge in incoming:
                outcome = outcome_by_node.get(str(edge.get("from_node_id"))); bs = bindings_by_edge.get(str(edge.get("edge_id")), [])
                completed = _timestamp(outcome.get("completed_at")) if outcome else None; available = _timestamp(bs[0].get("available_at")) if len(bs) == 1 else None
                if not outcome or outcome.get("status") != "succeeded" or completed is None or available is None or completed >= ready or available >= ready or ready >= running or running >= outcome_time: join_invalid = True
    if readiness_invalid: violations.add("POP2-BEH-DAG-615")
    if join_invalid: violations.add("POP2-BEH-DAG-618")

    # Attempts, outcomes, assignments, produced artifacts, and chronology.
    attempts_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list); outcomes_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list); assignments_by_node: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in values["attempts"]: attempts_by_node[str(item.get("node_id"))].append(item)
    for item in values["outcomes"]: outcomes_by_node[str(item.get("node_id"))].append(item)
    for item in values["assignments"]: assignments_by_node[str(item.get("node_id"))].append(item)
    if node_identity_exact:
        if set(attempts_by_node) != node_ids or set(outcomes_by_node) != node_ids or set(assignments_by_node) != node_ids: violations.add("POP2-BEH-DAG-616")
        for node_id in node_ids:
            attempts = sorted(attempts_by_node.get(node_id, []), key=lambda item: item.get("attempt_number", -1)); node_outcomes = outcomes_by_node.get(node_id, []); node_assignments = assignments_by_node.get(node_id, [])
            if len(node_outcomes) != 1 or len(node_assignments) != 1 or not attempts: violations.add("POP2-BEH-DAG-616"); continue
            previous: datetime | None = None
            for index, attempt in enumerate(attempts, 1):
                start, completed = _timestamp(attempt.get("started_at")), _timestamp(attempt.get("completed_at")); running = _first_time(status_groups, node_id, "RUNNING"); assignment = assignments.get(str(attempt.get("assignment_id")))
                if attempt.get("attempt_number") != index or not assignment or assignment.get("node_id") != node_id or start is None or completed is None or running is None or start <= running or completed <= start or (previous is not None and start <= previous) or attempt.get("attempt_digest") != _digest_without(attempt, "attempt_digest"): violations.add("POP2-BEH-DAG-616")
                previous = completed
            if any(item.get("state") == "succeeded" for item in attempts[:-1]):
                violations.add("POP2-BEH-DAG-616")
            attempt, outcome = attempts[-1], node_outcomes[0]; terminal = [item for item in status_groups.get(node_id, []) if item.get("status") in TERMINAL_STATUSES]
            if len(terminal) != 1 or outcome.get("attempt_id") != attempt.get("attempt_id") or outcome.get("status") != attempt.get("state") or outcome.get("artifact_refs") != attempt.get("produced_artifact_refs") or outcome.get("evidence_refs") != attempt.get("evidence_refs") or terminal[0].get("status") != str(outcome.get("status", "")).upper() or _timestamp(outcome.get("completed_at")) is None or previous is None or _timestamp(outcome.get("completed_at")) <= previous or _timestamp(terminal[0].get("recorded_at")) <= _timestamp(outcome.get("completed_at")): violations.add("POP2-BEH-DAG-616")
            for ref in attempt.get("produced_artifact_refs", []):
                artifact = artifacts.get(str(ref)); anchored_binding_ids = set(anchor["artifact_binding_record_digests"]); bindings = [item for item in values["artifact_bindings"] if item.get("artifact_id") == ref and item.get("binding_id") in anchored_binding_ids]
                if not artifact or artifact.get("producing_node_id") != node_id or (not bindings and node_id not in terminal_ids): violations.add("POP2-BEH-DAG-616")
                for binding in bindings:
                    edge = edge_by_id.get(str(binding.get("edge_id")))
                    if not edge or edge.get("from_node_id") != node_id or edge.get("to_node_id") != binding.get("consumer_node_id"): violations.add("POP2-BEH-DAG-616")

    # Closed status policy, chain, chronology, and complete canonical history.
    status_invalid = bundle.get("status_transition_rules") != list(LEGAL_STATUS_TRANSITIONS) or anchor["status_transition_rules"] != list(LEGAL_STATUS_TRANSITIONS) or not unique["statuses"]
    for node_id in node_ids if node_identity_exact else []:
        previous_digest = None; previous_name = None; previous_time = None; terminal_seen = False
        for index, status in enumerate(status_groups.get(node_id, []), 1):
            current_time, current_name = _timestamp(status.get("recorded_at")), status.get("status")
            if status.get("sequence") != index or status.get("previous_status_digest") != previous_digest or status.get("status_digest") != _digest_without(status, "status_digest") or current_time is None or (previous_time is not None and current_time <= previous_time) or terminal_seen: status_invalid = True
            if previous_name is None and current_name != "PLANNED": status_invalid = True
            if previous_name is not None and f"{previous_name}|{current_name}" not in LEGAL_STATUS_TRANSITIONS: status_invalid = True
            terminal_seen = current_name in TERMINAL_STATUSES; previous_name = str(current_name); previous_time = current_time; previous_digest = status.get("status_digest")
        if not terminal_seen: status_invalid = True
    transition_map = _projection_map(values["statuses"], "status_record_id", STATUS_TRANSITION_FIELDS)
    complete_status_changed = maps["statuses"] != anchor["status_record_digests"]
    if transition_map != anchor["status_transition_digests"]: status_invalid = True
    if complete_status_changed and transition_map == anchor["status_transition_digests"] and not readiness_invalid and not join_invalid: status_invalid = True
    if status_invalid and node_identity_exact: violations.add("POP2-BEH-DAG-617")

    # Effect records, node bindings, and outcomes share an exact independent proposal.
    raw_effects = bundle.get("effect_proposals")
    effects = _values(raw_effects)
    effect_unique, effect_map = _record_map(effects, "effect_id")
    effect_by_id = {
        str(item["effect_id"]): item for item in effects
        if effect_unique and isinstance(item.get("effect_id"), str)
    }
    if node_identity_exact:
        if (
            not isinstance(raw_effects, list)
            or len(effects) != len(raw_effects)
            or not effect_unique
            or any(not _authoritative_effect_proposal_valid(item) for item in effects)
            or effect_map != anchor["effect_proposal_digests"]
        ):
            violations.add("POP2-INV-DAG-619")
        bound: list[str] = []
        for node in nodes:
            binding = node.get("effect_binding"); outcome = outcome_by_node.get(str(node.get("node_id")))
            if binding is None:
                if outcome and (outcome.get("effect_id") is not None or outcome.get("effect_digest") is not None): violations.add("POP2-INV-DAG-619")
                continue
            effect = effect_by_id.get(str(binding.get("effect_id"))) if isinstance(binding, dict) else None
            if not effect or binding.get("effect_digest") != effect.get("effect_digest") or effect.get("effect_digest") != effect_binding_digest(effect) or effect.get("objective_digest") != objective.get("objective_digest") or effect.get("plan_revision") != plan_revision or not outcome or outcome.get("effect_id") != effect.get("effect_id") or outcome.get("effect_digest") != effect.get("effect_digest"): violations.add("POP2-INV-DAG-619")
            else: bound.append(effect["effect_id"])
        if len(bound) != len(set(bound)) or set(bound) != set(effect_by_id): violations.add("POP2-INV-DAG-619")

    # Revision/registry identity owns only its complete canonical surface.
    registry_actual = {k: revision.get(k) for k in ("registry_id", "registry_version", "registry_digest")}
    if run_id != anchor["run_id"] or plan_revision != anchor["plan_revision"] or registry_actual != anchor["registry_identity"] or revision.get("revision_digest") != dag_revision_digest(revision) or revision.get("objective_binding_digest") != objective.get("binding_digest"):
        if not objective_changed and node_identity_exact: violations.add("POP2-INV-DAG-620")

    # Five independent retention triggers and one exact minimized receipt.
    material = sorted({ref for item in values["outcomes"] if item.get("material_evidence") is True for ref in item.get("evidence_refs", []) if isinstance(ref, str)})
    declared = bundle.get("retention_sources", {}); actual_sources = {"material_evidence_refs": material}
    receipt_invalid = not isinstance(declared, dict)
    for _reason, field, _receipt in RETENTION_FIELDS[1:]:
        refs = declared.get(field, []) if isinstance(declared, dict) else []
        if not isinstance(refs, list) or len(refs) != len(set(refs)) or any(not isinstance(ref, str) for ref in refs): receipt_invalid = True; refs = []
        actual_sources[field] = sorted(refs)
    if actual_sources != anchor["retention_sources"]: receipt_invalid = True
    reasons = [reason for reason, field, _receipt in RETENTION_FIELDS if actual_sources[field]]; receipt = bundle.get("minimized_receipt")
    if reasons:
        allowed = {"$schema","x-poppy-schema-version","receipt_id","run_id","plan_revision","dag_revision_digest","objective_digest","terminal_status","retention_reasons","evidence_refs","effect_receipt_refs","decision_refs","safety_finding_refs","reusable_learning_refs","outcome_digest","recorded_at","receipt_digest"}
        terminal_outcome = next((item for item in values["outcomes"] if item.get("node_id") in terminal_ids), None)
        if not isinstance(receipt, dict) or set(receipt) != allowed or receipt.get("retention_reasons") != reasons or any(receipt.get(receipt_field) != actual_sources[source_field] for _reason, source_field, receipt_field in RETENTION_FIELDS) or not terminal_outcome or receipt.get("outcome_digest") != terminal_outcome.get("outcome_digest") or receipt.get("terminal_status") != terminal_outcome.get("status") or receipt.get("dag_revision_digest") != revision.get("revision_digest") or receipt.get("objective_digest") != objective.get("objective_digest") or receipt.get("receipt_digest") != _digest_without(receipt, "receipt_digest"):
            receipt_invalid = True
        elif canonical_digest(receipt) != anchor["minimized_receipt_record_digest"]:
            semantic_digest = canonical_digest({field: receipt.get(field) for field in MINIMIZED_RECEIPT_SEMANTIC_FIELDS})
            if semantic_digest != anchor["minimized_receipt_semantic_digest"]:
                receipt_invalid = True
    elif receipt is not None: receipt_invalid = True
    if receipt_invalid and node_identity_exact: violations.add("POP2-INV-DAG-621")

    messages = {
        "POP2-INV-DAG-602": ("/nodes", "the independently anchored objective and complete revision must contain only necessary connected nodes"),
        "POP2-INV-DAG-612": ("/edges", "the complete independently anchored topology must be exact and acyclic"),
        "POP2-INV-DAG-613": ("/nodes/capability_binding", "capability bindings must match the exact independent registry and contract"),
        "POP2-INV-DAG-614": ("/artifact_bindings", "complete edge and artifact records must implement exact typed production and consumption"),
        "POP2-BEH-DAG-615": ("/statuses", "READY requires all predecessor outcomes and typed bindings"),
        "POP2-BEH-DAG-616": ("/attempts", "complete assignments, attempts, outcomes, and produced artifacts must agree"),
        "POP2-BEH-DAG-617": ("/statuses", "complete status records must follow the closed policy and immutable chain"),
        "POP2-BEH-DAG-618": ("/nodes", "an all-join cannot run before every required branch completes"),
        "POP2-INV-DAG-619": ("/effect_proposals", "effects must bind one exact independent proposal"),
        "POP2-INV-DAG-620": ("/revision", "complete revision and registry identity must remain immutable"),
        "POP2-INV-DAG-621": ("/minimized_receipt", "only exact materially eligible minimized receipts may persist"),
    }
    return [_finding(code, *messages[code]) for code in sorted(violations)]
