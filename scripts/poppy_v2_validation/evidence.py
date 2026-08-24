"""Evidence/Gray invariants owned by POP-V2-007."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def _finding(code: str, entry_id: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "owner_decision_id": "POP-V2-007",
        "manifest_entry_id": entry_id,
        "layer": "INVARIANT",
        "locator": "synthetic:evidence-bundle",
        "json_pointer": pointer,
        "message": message,
    }


def _contains_score(value: Any) -> bool:
    if isinstance(value, dict):
        if any(str(key).casefold() in {"confidence", "confidence_score", "score", "weight", "probability"} for key in value):
            return True
        return any(_contains_score(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_score(child) for child in value)
    return False


def _has_required_cycle(required_edges: dict[str, set[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in required_edges.get(node, set())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in required_edges)


def validate_evidence_invariants(bundle: dict[str, Any]) -> list[dict[str, str]]:
    """Validate append-only revisions, contradictions, and required-dependency Gray propagation."""
    findings: list[dict[str, str]] = []
    claims = bundle.get("claims", [])
    revisions = bundle.get("revisions", [])
    observations = bundle.get("observations", [])
    contradictions = bundle.get("contradictions", [])
    dependencies = bundle.get("dependencies", [])

    if _contains_score(bundle):
        findings.append(_finding("POP2-INV-EVD-310", "invariant.evidence.no-confidence-averaging", "", "evidence state must not be derived from scores, weights, or probabilities"))

    claim_ids = {item.get("claim_id") for item in claims if isinstance(item, dict)}
    by_claim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for revision in revisions if isinstance(revisions, list) else []:
        if not isinstance(revision, dict):
            continue
        state = revision.get("state")
        if state not in {"supported", "contradicted", "gray"}:
            findings.append(_finding("POP2-INV-EVD-307", "invariant.evidence.state-is-three-valued", "/revisions", "claim state must be supported, contradicted, or gray"))
        claim_id = revision.get("claim_id")
        if isinstance(claim_id, str):
            by_claim[claim_id].append(revision)

    latest: dict[str, dict[str, Any]] = {}
    for claim_id, items in by_claim.items():
        ordered = sorted(items, key=lambda item: item.get("revision", 0))
        numbers = [item.get("revision") for item in ordered]
        digests = [item.get("content_digest") for item in ordered]
        if numbers != list(range(1, len(numbers) + 1)) or len(digests) != len(set(digests)):
            findings.append(_finding("POP2-INV-EVD-306", "invariant.evidence.claim-revisions-append-only", f"/revisions/{claim_id}", "claim revisions must be contiguous immutable revisions with unique content digests"))
        if ordered:
            latest[claim_id] = ordered[-1]

    observation_by_id = {
        item.get("observation_id"): item
        for item in observations if isinstance(item, dict) and isinstance(item.get("observation_id"), str)
    }
    observations_by_claim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observation_by_id.values():
        claim_id = observation.get("claim_id")
        if isinstance(claim_id, str):
            observations_by_claim[claim_id].append(observation)

    open_material: set[str] = set()
    for index, contradiction in enumerate(contradictions if isinstance(contradictions, list) else []):
        if not isinstance(contradiction, dict):
            continue
        left = contradiction.get("left_observation_id")
        right = contradiction.get("right_observation_id")
        if left == right or left not in observation_by_id or right not in observation_by_id:
            findings.append(_finding("POP2-INV-EVD-308", "invariant.evidence.contradiction-preserves-both-sides", f"/contradictions/{index}", "contradiction must preserve two distinct existing observations"))
        if contradiction.get("status") == "open" and contradiction.get("material") is True:
            claim_id = contradiction.get("claim_id")
            if isinstance(claim_id, str):
                open_material.add(claim_id)

    required_edges: dict[str, set[str]] = defaultdict(set)
    for dependency in dependencies if isinstance(dependencies, list) else []:
        if not isinstance(dependency, dict) or dependency.get("relationship") != "required":
            continue
        dependent = dependency.get("dependent_claim_id")
        required = dependency.get("dependency_claim_id")
        if isinstance(dependent, str) and isinstance(required, str):
            required_edges[dependent].add(required)
    if _has_required_cycle(required_edges):
        findings.append(_finding("POP2-INV-EVD-311", "invariant.evidence.dependency-cycle-invalid", "/dependencies", "required claim dependencies must be acyclic"))

    for claim_id in sorted(claim_ids | set(latest)):
        revision = latest.get(claim_id)
        if not revision:
            continue
        state = revision.get("state")
        expected_required = required_edges.get(claim_id, set())
        declared_required = set(revision.get("required_dependencies", [])) if isinstance(revision.get("required_dependencies"), list) else set()
        if declared_required != expected_required:
            findings.append(_finding("POP2-INV-EVD-305", "invariant.evidence.required-dependency-propagates-gray", f"/revisions/{claim_id}/required_dependencies", "claim revision must bind the exact required dependency claim IDs"))
        required_states = {required: latest.get(required, {}).get("state", "gray") for required in expected_required}
        non_supported = {required: value for required, value in required_states.items() if value != "supported"}
        expected_dependency_reasons = {
            (required, "required_dependency_contradicted" if value == "contradicted" else "required_dependency_gray")
            for required, value in non_supported.items()
        }
        dependency_reasons = {
            (item.get("dependency_claim_id"), item.get("reason_code"))
            for item in revision.get("dependency_reasons", [])
            if isinstance(item, dict)
        } if isinstance(revision.get("dependency_reasons"), list) else set()
        if dependency_reasons != expected_dependency_reasons:
            findings.append(_finding("POP2-INV-EVD-305", "invariant.evidence.required-dependency-propagates-gray", f"/revisions/{claim_id}/dependency_reasons", "dependency reason paths must exactly bind the non-supported required dependency claim IDs and reason codes"))
        if non_supported:
            reasons = set(revision.get("reason_codes", [])) if isinstance(revision.get("reason_codes"), list) else set()
            expected_reason_codes = {reason for _required, reason in expected_dependency_reasons}
            if state != "gray" or not expected_reason_codes.issubset(reasons):
                findings.append(_finding("POP2-INV-EVD-305", "invariant.evidence.required-dependency-propagates-gray", f"/revisions/{claim_id}", "a non-supported required dependency must make the dependent claim Gray with a reason path"))

        if state == "supported":
            usable_support = any(item.get("role") == "supports" and item.get("usable") is True for item in observations_by_claim.get(claim_id, []))
            if not usable_support or claim_id in open_material or non_supported:
                findings.append(_finding("POP2-INV-EVD-309", "invariant.evidence.supported-claim-gate", f"/revisions/{claim_id}", "supported requires usable own support, all required dependencies supported, and no open material contradiction"))

    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))
