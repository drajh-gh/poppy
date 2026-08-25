"""Authority-resolution invariants owned by POP-V2-002."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any


ORDERED_CHECKS = ["applicability", "authority", "specificity", "freshness", "safety", "conflict"]
ENTRY_BY_CODE = {
    "POP2-INV-AUT-106": "invariant.authority.source-classification-registry-owned",
    "POP2-INV-AUT-107": "invariant.authority.no-precedence-number-or-last-wins",
    "POP2-INV-AUT-108": "invariant.authority.resolution-checks-ordered",
    "POP2-INV-AUT-109": "invariant.authority.resolution-exactly-bound",
    "POP2-INV-AUT-110": "invariant.authority.conflict-never-inferred-away",
    "POP2-INV-AUT-111": "invariant.authority.approval-is-not-boolean",
}
SPECIFICITY_ORDER = {"exact_scope": 0, "data_class_scope": 1, "broader_scope": 2}


def canonical_digest(value: Any) -> str:
    """Hash canonical UTF-8 JSON: sorted keys, compact separators, preserved Unicode."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def candidate_set_digest(candidates: list[dict[str, Any]]) -> str:
    """Hash complete candidate objects as a semantic set ordered by candidate_id.

    Candidate and source-reference identities are both unique because either
    duplicate would make the semantic set ambiguous.
    """
    if not isinstance(candidates, list) or any(not isinstance(item, dict) for item in candidates):
        raise ValueError("authority candidates must be a list of objects")
    candidate_ids = [item.get("candidate_id") for item in candidates]
    source_ref_ids = [item.get("source_ref_id") for item in candidates]
    if any(not isinstance(value, str) or not value for value in candidate_ids + source_ref_ids):
        raise ValueError("authority candidates require candidate_id and source_ref_id")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("duplicate candidate_id")
    if len(source_ref_ids) != len(set(source_ref_ids)):
        raise ValueError("duplicate source_ref_id")
    return canonical_digest(sorted(candidates, key=lambda item: item["candidate_id"]))


def authority_resolution_digest(resolution: dict[str, Any]) -> str:
    """Hash the complete resolution record, excluding only resolution_digest."""
    return canonical_digest({key: value for key, value in resolution.items() if key != "resolution_digest"})


def _finding(code: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "owner_decision_id": "POP-V2-002",
        "manifest_entry_id": ENTRY_BY_CODE[code],
        "layer": "INVARIANT",
        "locator": "synthetic:authority-bundle",
        "json_pointer": pointer,
        "message": message,
    }


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _forbidden_precedence_path(value: Any, pointer: str = "") -> str | None:
    forbidden = {"precedence", "precedence_number", "last_wins", "last_file_wins"}
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if str(key).casefold() in forbidden:
                return child_pointer
            found = _forbidden_precedence_path(child, child_pointer)
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _forbidden_precedence_path(child, f"{pointer}/{index}")
            if found is not None:
                return found
    return None


def _boolean_approval_path(value: Any, pointer: str = "") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if str(key).casefold() in {"approved", "approval", "is_approved"} and isinstance(child, bool):
                return child_pointer
            found = _boolean_approval_path(child, child_pointer)
            if found is not None:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _boolean_approval_path(child, f"{pointer}/{index}")
            if found is not None:
                return found
    return None


def validate_authority_invariants(
    bundle: dict[str, Any], trusted_anchors: dict[str, Any]
) -> list[dict[str, str]]:
    """Validate authority against separately supplied, immutable trust anchors.

    Canonical digests inside ``bundle`` prove internal consistency only. The
    independent ``trusted_anchors.authority`` record binds the complete registry,
    source, and candidate records accepted by the evaluator.
    """
    findings: list[dict[str, str]] = []
    registry = bundle.get("registry", {})
    sources = bundle.get("sources", [])
    query = bundle.get("query", {})
    candidates = bundle.get("candidates", [])
    resolution = bundle.get("resolution", {})

    registry_kinds: dict[str, dict[str, Any]] = {}
    duplicate_kind = False
    for item in registry.get("source_kinds", []) if isinstance(registry, dict) else []:
        if not isinstance(item, dict) or not isinstance(item.get("source_kind_id"), str):
            continue
        kind_id = item["source_kind_id"]
        duplicate_kind = duplicate_kind or kind_id in registry_kinds
        registry_kinds[kind_id] = item
    classification_fields = ("data_class", "owner_kind", "authority_semantics")
    classification_invalid = duplicate_kind
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, dict):
            classification_invalid = True
            continue
        registered = registry_kinds.get(source.get("source_kind_id"))
        if (
            registered is None
            or source.get("registry_digest") != registry.get("registry_digest")
            or any(source.get(field) != registered.get(field) for field in classification_fields)
        ):
            classification_invalid = True
    if classification_invalid:
        findings.append(_finding("POP2-INV-AUT-106", "/sources", "source classification must be owned by and exactly match one registry entry"))

    precedence_path = _forbidden_precedence_path(bundle)
    if precedence_path is not None:
        findings.append(_finding("POP2-INV-AUT-107", precedence_path, "authority resolution must not use a precedence number or last-wins rule"))

    if resolution.get("checks") != ORDERED_CHECKS:
        findings.append(_finding("POP2-INV-AUT-108", "/resolution/checks", "checks must run in applicability, authority, specificity, freshness, safety, conflict order"))

    scope = query.get("scope", {}) if isinstance(query, dict) else {}
    candidate_values = [item for item in candidates if isinstance(item, dict)] if isinstance(candidates, list) else []
    source_values = [item for item in sources if isinstance(item, dict)] if isinstance(sources, list) else []
    sources_by_ref: dict[str, list[dict[str, Any]]] = {}
    for source in source_values:
        source_ref_id = source.get("source_ref_id")
        if isinstance(source_ref_id, str):
            sources_by_ref.setdefault(source_ref_id, []).append(source)
    try:
        actual_candidate_digest = candidate_set_digest(candidates)
        candidate_identity_invalid = False
    except ValueError:
        actual_candidate_digest = None
        candidate_identity_invalid = True
    authority_anchors = trusted_anchors.get("authority", {}) if isinstance(trusted_anchors, dict) else {}
    anchored_registry = authority_anchors.get("registry_digest") if isinstance(authority_anchors, dict) else None
    anchored_sources = authority_anchors.get("source_digests", {}) if isinstance(authority_anchors, dict) else {}
    anchored_candidates = authority_anchors.get("candidate_digests", {}) if isinstance(authority_anchors, dict) else {}
    source_ids = [item.get("source_ref_id") for item in source_values]
    candidate_record_ids = [item.get("candidate_id") for item in candidate_values]
    anchor_invalid = (
        not isinstance(anchored_registry, str)
        or anchored_registry != canonical_digest(registry)
        or not isinstance(anchored_sources, dict)
        or not isinstance(anchored_candidates, dict)
        or any(not isinstance(key, str) or not isinstance(value, str) for key, value in anchored_sources.items())
        or any(not isinstance(key, str) or not isinstance(value, str) for key, value in anchored_candidates.items())
        or len(source_ids) != len(set(source_ids))
        or len(candidate_record_ids) != len(set(candidate_record_ids))
        or set(source_ids) != set(anchored_sources)
        or set(candidate_record_ids) != set(anchored_candidates)
        or any(anchored_sources.get(item.get("source_ref_id")) != canonical_digest(item) for item in source_values)
        or any(anchored_candidates.get(item.get("candidate_id")) != canonical_digest(item) for item in candidate_values)
    )
    exact_fields = {
        "query_id": query.get("query_id"),
        "scope_digest": scope.get("scope_digest"),
        "subject_id": scope.get("subject_id"),
        "subject_digest": scope.get("subject_digest"),
        "objective_digest": scope.get("objective_digest"),
        "plan_revision": scope.get("plan_revision"),
        "evaluated_at": query.get("evaluated_at"),
        "candidate_set_digest": query.get("candidate_set_digest"),
    }
    exact_invalid = any(resolution.get(field) != expected for field, expected in exact_fields.items())
    query_refs = query.get("candidate_source_refs", [])
    current_refs = [item.get("source_ref_id") for item in candidate_values]
    exact_invalid = exact_invalid or candidate_identity_invalid
    exact_invalid = exact_invalid or anchor_invalid
    exact_invalid = exact_invalid or not isinstance(query_refs, list) or len(query_refs) != len(set(query_refs)) or set(query_refs) != set(current_refs)
    exact_invalid = exact_invalid or query.get("candidate_set_digest") != actual_candidate_digest or resolution.get("candidate_set_digest") != actual_candidate_digest
    exact_invalid = exact_invalid or resolution.get("resolution_digest") != authority_resolution_digest(resolution)
    authority_kind_by_semantics = {"grant": "grant", "constrain": "constrain", "reference_only": "evidence", "none": "none"}
    if len(source_values) != len(sources) or any(len(matches) != 1 for matches in sources_by_ref.values()):
        exact_invalid = True
    for candidate in candidate_values:
        if any(candidate.get(field) != scope.get(field) for field in ("scope_digest", "subject_id", "subject_digest", "data_class", "plan_revision")):
            exact_invalid = True
        matching_sources = sources_by_ref.get(candidate.get("source_ref_id"), [])
        if len(matching_sources) != 1:
            exact_invalid = True
            continue
        source = matching_sources[0]
        evaluated_at = _parse_timestamp(query.get("evaluated_at"))
        observed_at = _parse_timestamp(source.get("observed_at"))
        fresh_until_value = source.get("fresh_until")
        fresh_until = _parse_timestamp(fresh_until_value) if fresh_until_value is not None else None
        if (
            candidate.get("data_class") != source.get("data_class")
            or candidate.get("authority_kind") != authority_kind_by_semantics.get(source.get("authority_semantics"))
            or source.get("scope_digest") != scope.get("scope_digest")
            or candidate.get("scope_digest") != source.get("scope_digest")
            or evaluated_at is None
            or observed_at is None
            or observed_at > evaluated_at
            or (fresh_until_value is not None and fresh_until is None)
            or (
                candidate.get("freshness") == "current"
                and (
                    (fresh_until is not None and fresh_until <= evaluated_at)
                    or source.get("superseded_by") is not None
                )
            )
        ):
            exact_invalid = True
    candidate_by_id = {item.get("candidate_id"): item for item in candidate_values}
    candidate_ids = set(candidate_by_id)
    selected_ids = resolution.get("selected_candidate_ids", [])
    conflict_ids = resolution.get("conflict_candidate_ids", [])
    if (
        not isinstance(selected_ids, list)
        or len(selected_ids) != len(set(selected_ids))
        or not set(selected_ids).issubset(candidate_ids)
        or not isinstance(conflict_ids, list)
        or len(conflict_ids) != len(set(conflict_ids))
        or not set(conflict_ids).issubset(candidate_ids)
    ):
        exact_invalid = True

    viable = [
        item for item in candidate_values
        if item.get("applicability") == "applicable"
        and item.get("authority_kind") == "grant"
        and item.get("freshness") == "current"
        and item.get("safety") == "allows"
    ]
    best_peers: list[dict[str, Any]] = []
    if viable:
        best = min(SPECIFICITY_ORDER.get(str(item.get("specificity")), 99) for item in viable)
        best_peers = [item for item in viable if SPECIFICITY_ORDER.get(str(item.get("specificity")), 99) == best]
        positions = {item.get("position_digest") for item in best_peers}
        if len(best_peers) > 1 and len(positions) > 1:
            expected_conflicts = {item.get("candidate_id") for item in best_peers}
            if resolution.get("outcome") != "unresolved_conflict" or set(resolution.get("conflict_candidate_ids", [])) != expected_conflicts:
                findings.append(_finding("POP2-INV-AUT-110", "/resolution/outcome", "an unresolved material authority conflict must remain visible and fail closed"))

    if resolution.get("outcome") == "authorized":
        best_ids = {item.get("candidate_id") for item in best_peers}
        selected = [candidate_by_id.get(item) for item in selected_ids] if isinstance(selected_ids, list) else []
        if (
            not selected
            or any(item is None for item in selected)
            or not set(selected_ids).issubset(best_ids)
            or any(
                item.get("applicability") != "applicable"
                or item.get("authority_kind") != "grant"
                or item.get("freshness") != "current"
                or item.get("safety") != "allows"
                or not isinstance(item.get("authority_ref"), str)
                or item.get("authority_ref") != resolution.get("authority_ref")
                for item in selected if isinstance(item, dict)
            )
        ):
            exact_invalid = True
        blocking_constraints = [
            item for item in candidate_values
            if item.get("applicability") == "applicable"
            and item.get("authority_kind") == "constrain"
            and item.get("freshness") == "current"
            and item.get("safety") in {"denies", "narrows"}
        ]
        if blocking_constraints:
            exact_invalid = True

    query_time = _parse_timestamp(query.get("evaluated_at"))
    resolution_time = _parse_timestamp(resolution.get("resolved_at"))
    if query_time is None or resolution_time is None or query_time > resolution_time:
        exact_invalid = True

    if exact_invalid:
        findings.append(_finding("POP2-INV-AUT-109", "/resolution", "resolution must bind independent registry/source/candidate anchors, freshness, chronology, and viable selected authority"))

    approval_path = _boolean_approval_path(bundle)
    worker_grant = any(item.get("principal_kind") == "internal_worker" and item.get("authority_kind") == "grant" for item in candidate_values)
    imported_task_grant = any(
        item.get("principal_kind") == "user_owned_task"
        and item.get("authority_kind") == "grant"
        and item.get("task_scope_ref") != query.get("current_task_ref")
        for item in candidate_values
    )
    selected = [item for item in candidate_values if item.get("candidate_id") in set(selected_ids if isinstance(selected_ids, list) else [])]
    typed_authorized_invalid = resolution.get("outcome") == "authorized" and (
        not isinstance(resolution.get("authority_ref"), str)
        or not resolution.get("authority_ref")
        or not selected
        or any(item.get("authority_kind") != "grant" for item in selected)
    )
    if approval_path is not None or worker_grant or imported_task_grant or typed_authorized_invalid:
        pointer = approval_path or "/candidates"
        findings.append(_finding("POP2-INV-AUT-111", pointer, "approval is a typed scoped outcome; workers and imported task evidence do not become human authority"))

    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))
