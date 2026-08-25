"""Effect proposal and execution invariants owned by POP-V2-006."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .authority import authority_resolution_digest, canonical_digest, validate_authority_invariants


ENTRY_BY_CODE = {
    "POP2-INV-EFF-205": "invariant.effect.proposal-exactly-bound",
    "POP2-INV-EFF-206": "invariant.effect.change-invalidates-authority",
    "POP2-INV-EFF-207": "invariant.effect.high-risk-approval-distinct",
    "POP2-INV-EFF-208": "invariant.effect.attempt-is-not-verification",
    "POP2-INV-EFF-209": "invariant.effect.receipt-follows-authorized-attempt",
}
HIGH_RISK_CLASSES = {"destructive", "archive", "communication", "financial", "deployment", "production", "computer_control"}
EFFECT_BINDING_FIELDS = (
    "effect_id",
    "effect_class",
    "objective_digest",
    "plan_revision",
    "target",
    "preview_digest",
    "reversibility",
    "rollback",
    "verification",
    "authority_resolution_id",
    "authority_resolution_digest",
    "authority_ref",
    "authority_principal_kind",
    "high_risk_approval_ref",
)
EFFECT_AUTHORITY_SUBJECT_FIELDS = (
    "effect_id",
    "effect_class",
    "objective_digest",
    "plan_revision",
    "target",
    "preview_digest",
    "reversibility",
    "rollback",
    "verification",
)
EXECUTION_BINDING_FIELDS = (
    "effect_id",
    "effect_digest",
    "objective_digest",
    "plan_revision",
    "target",
    "preview_digest",
    "authority_resolution_id",
    "authority_resolution_digest",
    "authority_ref",
)


def _finding(code: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "owner_decision_id": "POP-V2-006",
        "manifest_entry_id": ENTRY_BY_CODE[code],
        "layer": "INVARIANT",
        "locator": "synthetic:effect-bundle",
        "json_pointer": pointer,
        "message": message,
    }


def effect_binding_digest(proposal: dict[str, Any]) -> str:
    """Return the canonical digest over every authority-sensitive proposal field."""
    basis = {field: proposal.get(field) for field in EFFECT_BINDING_FIELDS}
    return canonical_digest(basis)


def effect_authority_subject_digest(proposal: dict[str, Any]) -> str:
    """Bind the proposed mutation before resolution identity is attached.

    Separating this pre-authority subject digest from the final effect digest
    avoids a digest cycle: the resolution hashes this subject, while the final
    effect digest hashes the resulting resolution identity and authority.
    """
    return canonical_digest({field: proposal.get(field) for field in EFFECT_AUTHORITY_SUBJECT_FIELDS})


def receipt_digest(receipt: dict[str, Any]) -> str:
    """Hash the complete execution receipt, excluding only receipt_digest."""
    return canonical_digest({key: value for key, value in receipt.items() if key != "receipt_digest"})


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _anchored_record_index(
    records: Any, identity_field: str, anchored_digests: Any
) -> tuple[dict[str, list[dict[str, Any]]], bool]:
    """Index complete records and require an exact independent digest map."""
    values = [item for item in records if isinstance(item, dict)] if isinstance(records, list) else []
    by_identity: dict[str, list[dict[str, Any]]] = {}
    for item in values:
        identity = item.get(identity_field)
        if isinstance(identity, str) and identity:
            by_identity.setdefault(identity, []).append(item)
    invalid = (
        not isinstance(records, list)
        or len(values) != len(records)
        or len(by_identity) != len(values)
        or any(len(matches) != 1 for matches in by_identity.values())
        or not isinstance(anchored_digests, dict)
        or any(not isinstance(key, str) or not isinstance(value, str) for key, value in anchored_digests.items())
        or set(by_identity) != set(anchored_digests)
        or any(
            anchored_digests.get(identity) != canonical_digest(matches[0])
            for identity, matches in by_identity.items()
            if len(matches) == 1
        )
    )
    return by_identity, invalid


def validate_effect_invariants(
    bundle: dict[str, Any], trusted_anchors: dict[str, Any]
) -> list[dict[str, str]]:
    """Validate effects against separately supplied authority and history anchors."""
    findings: list[dict[str, str]] = []
    proposal = bundle.get("proposal", {})
    query = bundle.get("authority_query", {})
    resolution = bundle.get("authority_resolution", {})
    attempts = bundle.get("attempts", [])
    receipt = bundle.get("receipt", {})
    scope = query.get("scope", {}) if isinstance(query, dict) else {}
    subject_digest = effect_authority_subject_digest(proposal)
    authority_context = {
        "registry": bundle.get("authority_registry", {}),
        "sources": bundle.get("authority_sources", []),
        "candidates": bundle.get("authority_candidates", []),
        "query": query,
        "resolution": resolution,
    }
    authority_anchors = trusted_anchors.get("authority", {}) if isinstance(trusted_anchors, dict) else {}
    effect_anchors = trusted_anchors.get("effect", {}) if isinstance(trusted_anchors, dict) else {}
    anchored_attempts = effect_anchors.get("attempt_digests", {}) if isinstance(effect_anchors, dict) else {}
    attempts_by_id, attempt_anchor_invalid = _anchored_record_index(attempts, "attempt_id", anchored_attempts)
    attempt_values = [matches[0] for matches in attempts_by_id.values() if len(matches) == 1]
    anchored_receipts = effect_anchors.get("receipt_digests", {}) if isinstance(effect_anchors, dict) else {}
    receipt_records = [receipt] if isinstance(receipt, dict) else []
    receipts_by_id, receipt_anchor_invalid = _anchored_record_index(receipt_records, "receipt_id", anchored_receipts)
    receipt_anchor_invalid = receipt_anchor_invalid or len(receipts_by_id) != 1
    authority_context_valid = (
        isinstance(effect_anchors, dict)
        and effect_anchors.get("authority_anchor_digest") == canonical_digest(authority_anchors)
        and not validate_authority_invariants(authority_context, trusted_anchors)
    )
    query_time = _parse_timestamp(query.get("evaluated_at"))
    resolution_time = _parse_timestamp(resolution.get("resolved_at"))
    proposed_time = _parse_timestamp(proposal.get("proposed_at"))

    proposal_exact = (
        authority_context_valid
        and proposal.get("effect_digest") == effect_binding_digest(proposal)
        and scope.get("subject_kind") == "effect"
        and scope.get("subject_id") == proposal.get("effect_id")
        and scope.get("subject_digest") == subject_digest
        and scope.get("objective_digest") == proposal.get("objective_digest")
        and scope.get("plan_revision") == proposal.get("plan_revision")
        and query.get("requested_authority") == "effect_execution"
        and resolution.get("query_id") == query.get("query_id")
        and resolution.get("scope_digest") == scope.get("scope_digest")
        and resolution.get("evaluated_at") == query.get("evaluated_at")
        and resolution.get("candidate_set_digest") == query.get("candidate_set_digest")
        and resolution.get("resolution_id") == proposal.get("authority_resolution_id")
        and resolution.get("resolution_digest") == authority_resolution_digest(resolution)
        and resolution.get("resolution_digest") == proposal.get("authority_resolution_digest")
        and resolution.get("authority_ref") == proposal.get("authority_ref")
        and resolution.get("subject_id") == proposal.get("effect_id")
        and resolution.get("subject_digest") == subject_digest
        and resolution.get("objective_digest") == proposal.get("objective_digest")
        and resolution.get("plan_revision") == proposal.get("plan_revision")
        and resolution.get("outcome") == "authorized"
        and resolution.get("checks") == ["applicability", "authority", "specificity", "freshness", "safety", "conflict"]
        and isinstance(resolution.get("selected_candidate_ids"), list)
        and bool(resolution.get("selected_candidate_ids"))
        and query_time is not None
        and resolution_time is not None
        and proposed_time is not None
        and query_time <= resolution_time
        and proposed_time <= resolution_time
    )
    if not proposal_exact:
        findings.append(_finding("POP2-INV-EFF-205", "/proposal", "proposal must bind the exact target, preview, reversibility, rollback, verification, authority, objective, plan revision, and digest"))

    raw_history = bundle.get("proposal_history", [])
    history = [item for item in raw_history if isinstance(item, dict)] if isinstance(raw_history, list) else []
    tuples = [
        (item.get("authority_resolution_id"), item.get("authority_resolution_digest"), item.get("effect_digest"))
        for item in history
    ]
    current_tuple = (proposal.get("authority_resolution_id"), proposal.get("authority_resolution_digest"), proposal.get("effect_digest"))
    history_malformed = (
        not isinstance(raw_history, list)
        or len(history) != len(raw_history)
        or any(not all(isinstance(value, str) and value for value in item) for item in tuples)
        or len(tuples) != len(set(tuples))
        or tuples.count(current_tuple) != 1
    )
    by_resolution_id: dict[str, set[tuple[str, str]]] = {}
    by_resolution_identity: dict[tuple[str, str], set[str]] = {}
    for resolution_id, resolution_digest_value, effect_digest_value in tuples:
        if isinstance(resolution_id, str) and isinstance(resolution_digest_value, str) and isinstance(effect_digest_value, str):
            by_resolution_id.setdefault(resolution_id, set()).add((resolution_digest_value, effect_digest_value))
            by_resolution_identity.setdefault((resolution_id, resolution_digest_value), set()).add(effect_digest_value)
    computed_bindings = {
        resolution_id: {
            "authority_resolution_digest": next(iter(values))[0],
            "effect_digest": next(iter(values))[1],
        }
        for resolution_id, values in by_resolution_id.items()
        if len(values) == 1
    }
    history_anchor_invalid = (
        not isinstance(effect_anchors, dict)
        or effect_anchors.get("proposal_history_digest") != canonical_digest(raw_history)
        or effect_anchors.get("resolution_bindings") != computed_bindings
    )
    if history_malformed or history_anchor_invalid or any(len(values) > 1 for values in by_resolution_id.values()) or any(len(values) > 1 for values in by_resolution_identity.values()):
        findings.append(_finding("POP2-INV-EFF-206", "/proposal_history", "a changed authority-sensitive effect binding invalidates the prior authority resolution"))

    approval = proposal.get("high_risk_approval_ref")
    approval_records = bundle.get("high_risk_approvals", [])
    approval_values = [item for item in approval_records if isinstance(item, dict)] if isinstance(approval_records, list) else []
    approval_by_ref: dict[str, list[dict[str, Any]]] = {}
    for item in approval_values:
        if isinstance(item.get("approval_ref"), str):
            approval_by_ref.setdefault(item["approval_ref"], []).append(item)
    anchored_approvals = effect_anchors.get("approval_digests", {}) if isinstance(effect_anchors, dict) else {}
    approval_anchor_invalid = (
        not isinstance(approval_records, list)
        or len(approval_values) != len(approval_records)
        or any(len(values) != 1 for values in approval_by_ref.values())
        or not isinstance(anchored_approvals, dict)
        or set(approval_by_ref) != set(anchored_approvals)
        or any(
            anchored_approvals.get(reference) != canonical_digest(values[0])
            for reference, values in approval_by_ref.items()
            if len(values) == 1
        )
    )
    receipt_attempt_time = _parse_timestamp(receipt.get("attempted_at"))
    if proposal.get("effect_class") in HIGH_RISK_CLASSES:
        matches = approval_by_ref.get(approval, []) if isinstance(approval, str) else []
        approval_time = _parse_timestamp(matches[0].get("approved_at")) if len(matches) == 1 else None
        distinct_values = {
            proposal.get("effect_id"),
            receipt.get("receipt_id"),
            receipt.get("attempt_id"),
            proposal.get("authority_ref"),
            proposal.get("effect_digest"),
        }
        if (
            approval_anchor_invalid
            or not isinstance(approval, str)
            or not approval
            or approval in distinct_values
            or len(matches) != 1
            or matches[0].get("principal_kind") != "human"
            or not isinstance(matches[0].get("principal_ref"), str)
            or not matches[0].get("principal_ref")
            or matches[0].get("effect_digest") != proposal.get("effect_digest")
            or approval_time is None
            or proposed_time is None
            or resolution_time is None
            or receipt_attempt_time is None
            or approval_time < proposed_time
            or approval_time <= resolution_time
            or approval_time >= receipt_attempt_time
        ):
            findings.append(_finding("POP2-INV-EFF-207", "/proposal/high_risk_approval_ref", "a destructive or high-risk effect requires distinct human approval in addition to scoped effect authority"))
    elif approval_anchor_invalid:
        findings.append(_finding("POP2-INV-EFF-207", "/high_risk_approvals", "approval evidence must exactly match independently anchored complete records"))

    verified = receipt.get("verification_state") == "verified"
    verification_refs = receipt.get("verification_evidence_refs", [])
    attempted_marker = f"synthetic:attempt:{receipt.get('attempt_id')}"
    receipt_marker = f"synthetic:receipt:{receipt.get('receipt_id')}"
    evidence_records = bundle.get("verification_evidence", [])
    anchored_evidence = effect_anchors.get("verification_evidence_digests", {}) if isinstance(effect_anchors, dict) else {}
    evidence_by_ref, evidence_anchor_invalid = _anchored_record_index(
        evidence_records, "evidence_ref", anchored_evidence
    )
    attempt_time = _parse_timestamp(receipt.get("attempted_at"))
    verified_time = _parse_timestamp(receipt.get("verified_at"))
    expected_state = proposal.get("verification", {}).get("expected_state_digest") if isinstance(proposal.get("verification"), dict) else None
    resolved_evidence: list[dict[str, Any]] = []
    evidence_invalid = (
        receipt.get("attempt_outcome") != "succeeded"
        or not isinstance(verification_refs, list)
        or not verification_refs
        or len(verification_refs) != len(set(verification_refs))
        or attempted_marker in verification_refs
        or receipt_marker in verification_refs
        or attempt_time is None
        or verified_time is None
        or verified_time <= attempt_time
        or not isinstance(expected_state, str)
    )
    if isinstance(verification_refs, list):
        for reference in verification_refs:
            matches = evidence_by_ref.get(reference, []) if isinstance(reference, str) else []
            if len(matches) != 1:
                evidence_invalid = True
                continue
            evidence = matches[0]
            resolved_evidence.append(evidence)
            observed_time = _parse_timestamp(evidence.get("observed_at"))
            if (
                evidence.get("evidence_kind") != "read_back"
                or evidence.get("effect_id") != proposal.get("effect_id")
                or evidence.get("effect_digest") != proposal.get("effect_digest")
                or evidence.get("attempt_id") != receipt.get("attempt_id")
                or evidence.get("expected_state_digest") != expected_state
                or evidence.get("observed_state_digest") != expected_state
                or observed_time is None
                or attempt_time is None
                or observed_time <= attempt_time
                or verified_time is None
                or verified_time < observed_time
            ):
                evidence_invalid = True
    if not attempt_anchor_invalid and (evidence_anchor_invalid or (verified and evidence_invalid)):
        findings.append(_finding("POP2-INV-EFF-208", "/receipt/verification_state", "an attempted or successful execution is not verified without distinct read-back evidence"))

    attempt_ids = [item.get("attempt_id") for item in attempt_values]
    matches = [item for item in attempt_values if item.get("attempt_id") == receipt.get("attempt_id")]
    attempt = matches[0] if len(matches) == 1 else None
    receipt_anchor_identity_matches = (
        isinstance(anchored_receipts, dict)
        and isinstance(receipt.get("receipt_id"), str)
        and set(anchored_receipts) == {receipt.get("receipt_id")}
    )
    coordinated_evidence_identity_rewrite = (
        evidence_anchor_invalid
        and not evidence_invalid
        and not attempt_anchor_invalid
        and receipt_anchor_identity_matches
        and receipt.get("receipt_digest") == receipt_digest(receipt)
    )
    receipt_anchor_requires_finding = receipt_anchor_invalid and not coordinated_evidence_identity_rewrite
    receipt_valid = (
        isinstance(attempt, dict)
        and not attempt_anchor_invalid
        and not receipt_anchor_requires_finding
        and isinstance(attempts, list)
        and len(attempt_values) == len(attempts) == 1
        and len(attempt_ids) == len(set(attempt_ids))
        and resolution.get("outcome") == "authorized"
        and all(attempt.get(field) == proposal.get(field) for field in EXECUTION_BINDING_FIELDS)
        and attempt.get("outcome") == receipt.get("attempt_outcome")
        and attempt.get("attempted_at") == receipt.get("attempted_at")
        and receipt_attempt_time is not None
        and proposed_time is not None
        and resolution_time is not None
        and receipt_attempt_time > proposed_time
        and receipt_attempt_time > resolution_time
        and all(receipt.get(field) == proposal.get(field) for field in EXECUTION_BINDING_FIELDS)
        and receipt.get("receipt_digest") == receipt_digest(receipt)
        and "receipts" not in bundle
    )
    if not receipt_valid:
        findings.append(_finding("POP2-INV-EFF-209", "/receipt", "an execution receipt must follow and exactly bind one authorized attempt"))

    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))
