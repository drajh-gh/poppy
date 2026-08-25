"""Kernel lifecycle invariants owned by POP-V2-003."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .authority import canonical_digest


STATES = (
    "RECEIVED", "TRIAGED", "CONTEXT_RESOLVED", "ORIENTED", "PLANNED",
    "AWAITING_AUTHORITY", "EXECUTING", "JOINING", "EVALUATING", "PERSISTING",
    "SUCCEEDED", "LIMITED", "BLOCKED", "CANCELLED", "FAILED",
)
CONDITIONAL_STATES = ("ORIENTED", "AWAITING_AUTHORITY", "PERSISTING")
TERMINAL_STATE_SEQUENCE = ("SUCCEEDED", "LIMITED", "BLOCKED", "CANCELLED", "FAILED")
TERMINAL_STATES = set(TERMINAL_STATE_SEQUENCE)
ANCHOR_KEYS = {
    "run_id", "plan_revision", "states", "conditional_states", "terminal_states",
    "transition_rule_keys", "required_guards_by_rule", "transition_ids", "event_ids",
    "transition_record_digests", "revision_ids", "revision_record_digests",
    "outcome_id", "outcome_record_digest", "authority_binding", "authority_binding_digest",
    "evaluation_binding", "evaluation_binding_digest", "attempted_effects_digest",
    "persistence", "persistence_digest", "durable_delta_digest",
}
ENTRY_BY_CODE = {
    "POP2-BEH-KRN-406": "invariant.kernel.legal-transition-only",
    "POP2-BEH-KRN-407": "invariant.kernel.terminal-singular-immutable",
    "POP2-BEH-KRN-408": "invariant.kernel.required-guards-pass",
    "POP2-INV-KRN-409": "invariant.kernel.transition-digest-chain",
    "POP2-BEH-KRN-410": "invariant.kernel.plan-revision-invalidates-old-bindings",
    "POP2-BEH-KRN-411": "invariant.kernel.authority-denial-is-no-effect-terminal",
    "POP2-BEH-KRN-412": "invariant.kernel.persistence-gated",
}


def transition_record_digest(record: dict[str, Any]) -> str:
    """Hash the complete immutable transition record except its own digest."""
    return canonical_digest({key: value for key, value in record.items() if key != "transition_digest"})


def outcome_record_digest(record: dict[str, Any]) -> str:
    """Hash the complete immutable outcome record except its own digest."""
    return canonical_digest({key: value for key, value in record.items() if key != "outcome_digest"})


def _finding(code: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "owner_decision_id": "POP-V2-003",
        "manifest_entry_id": ENTRY_BY_CODE[code],
        "layer": "INVARIANT",
        "locator": "synthetic:kernel-bundle",
        "json_pointer": pointer,
        "message": message,
    }


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _rule_key(source: Any, event: Any, destination: Any) -> str:
    return f"{source}|{event}|{destination}"


def _same_without_plan_revision(actual: Any, expected: Any) -> bool:
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        return actual is None and expected is None
    return (
        {key: value for key, value in actual.items() if key != "plan_revision"}
        == {key: value for key, value in expected.items() if key != "plan_revision"}
    )


def _unique_strings(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value) and len(value) == len(set(value))


def validate_kernel_invariants(
    bundle: dict[str, Any], trusted_anchors: dict[str, Any]
) -> list[dict[str, str]]:
    """Validate a provider-neutral run lifecycle against independent trust anchors."""
    findings: list[dict[str, str]] = []
    anchor = trusted_anchors.get("kernel", {}) if isinstance(trusted_anchors, dict) else {}
    anchor_complete = isinstance(anchor, dict) and set(anchor) == ANCHOR_KEYS

    transitions = bundle.get("transitions", [])
    allowed = bundle.get("allowed_transitions", [])
    revisions = bundle.get("plan_revisions", [])
    outcome = bundle.get("outcome", {})
    authority = bundle.get("authority_binding")
    evaluation = bundle.get("evaluation_binding")
    persistence = bundle.get("persistence", {})
    attempted_effects = bundle.get("attempted_effects", [])
    transition_values = [item for item in transitions if isinstance(item, dict)] if isinstance(transitions, list) else []
    allowed_values = [item for item in allowed if isinstance(item, dict)] if isinstance(allowed, list) else []
    revision_values = [item for item in revisions if isinstance(item, dict)] if isinstance(revisions, list) else []

    rule_keys = [
        _rule_key(item.get("source_state"), item.get("event_type"), item.get("destination_state"))
        for item in allowed_values
    ]
    anchored_rule_keys = anchor.get("transition_rule_keys") if anchor_complete else None
    illegal = not anchor_complete or not isinstance(allowed, list) or len(allowed_values) != len(allowed)
    illegal = illegal or not isinstance(bundle.get("states"), list) or not isinstance(bundle.get("conditional_states"), list) or not isinstance(bundle.get("terminal_states"), list)
    illegal = illegal or (
        list(bundle.get("states", [])) != list(STATES)
        or list(bundle.get("conditional_states", [])) != list(CONDITIONAL_STATES)
        or list(bundle.get("terminal_states", [])) != list(TERMINAL_STATE_SEQUENCE)
        or (anchor.get("states") != list(STATES) if anchor_complete else True)
    )
    illegal = illegal or (
        not anchor_complete
        or anchor.get("conditional_states") != list(CONDITIONAL_STATES)
        or anchor.get("terminal_states") != list(TERMINAL_STATE_SEQUENCE)
        or len(rule_keys) != len(set(rule_keys))
        or not isinstance(anchored_rule_keys, list)
        or sorted(rule_keys) != sorted(anchored_rule_keys)
    )
    allowed_key_set = set(rule_keys)
    for item in transition_values:
        event = item.get("event", {})
        key = _rule_key(
            item.get("source_state"),
            event.get("event_type") if isinstance(event, dict) else None,
            item.get("destination_state"),
        )
        if key not in allowed_key_set:
            illegal = True
    if illegal:
        findings.append(_finding(
            "POP2-BEH-KRN-406", "/allowed_transitions",
            "accepted states and each typed transition rule must match the independent kernel policy anchor exactly",
        ))

    terminal_indexes = [
        index for index, item in enumerate(transition_values)
        if item.get("destination_state") in TERMINAL_STATES
    ]
    final_transition_time = _timestamp(transition_values[-1].get("transitioned_at")) if transition_values else None
    terminal_time = _timestamp(outcome.get("terminal_at")) if isinstance(outcome, dict) else None
    computed_outcome_digest = outcome_record_digest(outcome) if isinstance(outcome, dict) else None
    terminal_invalid = (
        not anchor_complete
        or len(terminal_indexes) != 1
        or not transition_values
        or terminal_indexes[-1] != len(transition_values) - 1
        or any(item.get("source_state") in TERMINAL_STATES for item in transition_values)
        or not isinstance(outcome, dict)
        or outcome.get("terminal_state") != transition_values[-1].get("destination_state")
        or outcome.get("run_id") != bundle.get("run_id")
        or outcome.get("outcome_id") != anchor.get("outcome_id")
        or outcome.get("outcome_digest") != computed_outcome_digest
        or computed_outcome_digest != anchor.get("outcome_record_digest")
        or final_transition_time is None
        or terminal_time is None
        or terminal_time <= final_transition_time
    )
    if terminal_invalid:
        findings.append(_finding(
            "POP2-BEH-KRN-407", "/outcome",
            "one anchored immutable outcome must follow the final singular terminal transition and match its canonical digest",
        ))

    required_by_rule: dict[str, list[Any]] = {}
    duplicate_rule_guard = False
    for key, item in zip(rule_keys, allowed_values):
        required = item.get("required_guard_codes", [])
        if not _unique_strings(required):
            duplicate_rule_guard = True
            required = []
        required_by_rule[key] = required
    anchored_rule_set_matches = (
        anchor_complete
        and len(rule_keys) == len(set(rule_keys))
        and isinstance(anchor.get("transition_rule_keys"), list)
        and sorted(rule_keys) == sorted(anchor["transition_rule_keys"])
    )
    guard_invalid = (
        not anchor_complete
        or duplicate_rule_guard
        or (anchored_rule_set_matches and required_by_rule != anchor.get("required_guards_by_rule"))
    )
    for item in transition_values:
        event = item.get("event", {})
        key = _rule_key(item.get("source_state"), event.get("event_type") if isinstance(event, dict) else None, item.get("destination_state"))
        results = item.get("guard_results", [])
        result_values = [value for value in results if isinstance(value, dict)] if isinstance(results, list) else []
        guard_codes = [value.get("guard_code") for value in result_values]
        if (
            not isinstance(results, list)
            or len(result_values) != len(results)
            or not _unique_strings(guard_codes)
            or any(
                next((value.get("outcome") for value in result_values if value.get("guard_code") == code), None) != "passed"
                for code in required_by_rule.get(key, [])
            )
        ):
            guard_invalid = True
    if guard_invalid:
        findings.append(_finding(
            "POP2-BEH-KRN-408", "/transitions",
            "anchored required guard sets must be unique, present, and passed without duplicate guard codes",
        ))

    transition_ids = [item.get("transition_id") for item in transition_values]
    event_ids = [
        item.get("event", {}).get("event_id") if isinstance(item.get("event"), dict) else None
        for item in transition_values
    ]
    transition_digests = {
        str(item.get("transition_id")): transition_record_digest(item)
        for item in transition_values
        if isinstance(item.get("transition_id"), str)
    }
    chain_invalid = not anchor_complete or not isinstance(transitions, list) or len(transition_values) != len(transitions)
    chain_invalid = chain_invalid or (
        not _unique_strings(transition_ids)
        or not _unique_strings(event_ids)
        or (transition_ids != anchor.get("transition_ids") if anchor_complete else True)
    )
    chain_invalid = chain_invalid or (
        not anchor_complete
        or event_ids != anchor.get("event_ids")
        or transition_digests != anchor.get("transition_record_digests")
    )
    previous_digest: str | None = None
    previous_destination: Any = None
    previous_time: datetime | None = None
    for index, item in enumerate(transition_values):
        current_time = _timestamp(item.get("transitioned_at"))
        event = item.get("event", {})
        event_time = _timestamp(event.get("occurred_at")) if isinstance(event, dict) else None
        guard_times = [
            _timestamp(value.get("evaluated_at"))
            for value in item.get("guard_results", [])
            if isinstance(value, dict)
        ] if isinstance(item.get("guard_results"), list) else []
        if (
            item.get("sequence") != index + 1
            or item.get("run_id") != bundle.get("run_id")
            or item.get("previous_transition_digest") != previous_digest
            or item.get("transition_digest") != transition_record_digest(item)
            or (index > 0 and item.get("source_state") != previous_destination)
            or current_time is None
            or event_time is None
            or event_time >= current_time
            or (previous_time is not None and event_time <= previous_time)
            or any(value is None or value <= event_time or value >= current_time for value in guard_times)
            or (previous_time is not None and current_time <= previous_time)
        ):
            chain_invalid = True
        previous_digest = item.get("transition_digest") if isinstance(item.get("transition_digest"), str) else None
        previous_destination = item.get("destination_state")
        previous_time = current_time
    if not transition_values:
        chain_invalid = True
    if chain_invalid:
        findings.append(_finding(
            "POP2-INV-KRN-409", "/transitions",
            "anchored transition/event identities, strict chronology, state continuity, and canonical digest chain must bind exactly",
        ))

    revision_ids = [item.get("revision_id") for item in revision_values]
    revision_digests = {
        str(item.get("revision_id")): canonical_digest(item)
        for item in revision_values
        if isinstance(item.get("revision_id"), str)
    }
    revision_invalid = not anchor_complete or not isinstance(revisions, list) or len(revision_values) != len(revisions)
    revision_invalid = revision_invalid or (
        not _unique_strings(revision_ids)
        or (revision_ids != anchor.get("revision_ids") if anchor_complete else True)
    )
    revision_invalid = revision_invalid or (
        not anchor_complete
        or revision_digests != anchor.get("revision_record_digests")
        or bundle.get("run_id") != anchor.get("run_id")
        or bundle.get("plan_revision") != anchor.get("plan_revision")
    )
    expected_revision = 1
    previous_revision_time: datetime | None = None
    first_event_time = None
    if transition_values and isinstance(transition_values[0].get("event"), dict):
        first_event_time = _timestamp(transition_values[0]["event"].get("occurred_at"))
    for record in revision_values:
        record_time = _timestamp(record.get("recorded_at"))
        if (
            record.get("run_id") != bundle.get("run_id")
            or record.get("prior_revision") != expected_revision
            or record.get("plan_revision") != expected_revision + 1
            or record.get("authority_binding_valid") is not False
            or record.get("evaluation_binding_valid") is not False
            or record.get("previous_digest") == record.get("current_digest")
            or record_time is None
            or (previous_revision_time is not None and record_time <= previous_revision_time)
            or (first_event_time is not None and record_time >= first_event_time)
        ):
            revision_invalid = True
        expected_revision += 1
        previous_revision_time = record_time
    current_revision = bundle.get("plan_revision")
    if current_revision != expected_revision:
        revision_invalid = True
    for binding in (authority, evaluation):
        if binding is not None and (not isinstance(binding, dict) or binding.get("plan_revision") != current_revision):
            revision_invalid = True
    if any(item.get("plan_revision") != current_revision for item in transition_values):
        revision_invalid = True
    if isinstance(outcome, dict) and outcome.get("plan_revision") != current_revision:
        revision_invalid = True
    if revision_invalid:
        findings.append(_finding(
            "POP2-BEH-KRN-410", "/plan_revisions",
            "anchored material revision history must be immutable, chronological, incrementing, and invalidate old bindings",
        ))

    anchored_authority = anchor.get("authority_binding") if anchor_complete else None
    authority_anchor_valid = (
        anchor_complete
        and anchor.get("authority_binding_digest") == canonical_digest(anchored_authority)
        and _same_without_plan_revision(authority, anchored_authority)
    )
    authority_outcome = authority.get("outcome") if isinstance(authority, dict) else None
    outcome_authority = outcome.get("authority_outcome") if isinstance(outcome, dict) else None
    authority_invalid = not authority_anchor_valid or not isinstance(attempted_effects, list)
    authority_invalid = authority_invalid or (
        anchor.get("attempted_effects_digest") != canonical_digest(attempted_effects)
        if anchor_complete else True
    )
    if authority is None:
        authority_invalid = authority_invalid or outcome_authority != "not_required"
    else:
        authority_invalid = authority_invalid or (
            not isinstance(authority, dict)
            or authority.get("valid") is not True
            or authority_outcome != outcome_authority
        )
    if authority_outcome in {"denied", "missing"}:
        authority_invalid = authority_invalid or (
            not isinstance(outcome, dict)
            or outcome.get("terminal_state") not in TERMINAL_STATES
            or outcome.get("attempted_effect_count") != 0
            or outcome.get("durable_delta") is not False
            or bool(attempted_effects)
            or not isinstance(persistence, dict)
            or persistence.get("entered") is not False
            or persistence.get("persisted") is not False
        )
    if isinstance(outcome, dict) and isinstance(attempted_effects, list):
        authority_invalid = authority_invalid or outcome.get("attempted_effect_count") != len(attempted_effects)
    if authority_invalid:
        findings.append(_finding(
            "POP2-BEH-KRN-411", "/authority_binding",
            "the anchored authority outcome must agree exactly with the outcome, and denial or absence must terminate without effect",
        ))

    anchored_evaluation = anchor.get("evaluation_binding") if anchor_complete else None
    evaluation_anchor_valid = (
        anchor_complete
        and anchor.get("evaluation_binding_digest") == canonical_digest(anchored_evaluation)
        and _same_without_plan_revision(evaluation, anchored_evaluation)
    )
    persistence_anchor_valid = (
        anchor_complete
        and anchor.get("persistence_digest") == canonical_digest(anchor.get("persistence"))
        and persistence == anchor.get("persistence")
    )
    entered_persistence = any(
        item.get("destination_state") == "PERSISTING" or item.get("source_state") == "PERSISTING"
        for item in transition_values
    )
    persistence_invalid = (
        not evaluation_anchor_valid
        or not persistence_anchor_valid
        or not isinstance(persistence, dict)
        or persistence.get("entered") is not entered_persistence
    )
    if entered_persistence and isinstance(persistence, dict):
        durable_digest = persistence.get("durable_delta_digest")
        anchored_durable_digest = anchor.get("durable_delta_digest") if anchor_complete else None
        anchored_persistence_key = _rule_key("EVALUATING", "DURABLE_DELTA_AUTHORIZED", "PERSISTING")
        actual_persistence_flow = any(
            item.get("source_state") == "EVALUATING"
            and isinstance(item.get("event"), dict)
            and item["event"].get("event_type") == "DURABLE_DELTA_AUTHORIZED"
            and item.get("destination_state") == "PERSISTING"
            for item in transition_values
        )
        anchored_rule_values = anchor.get("transition_rule_keys", []) if anchor_complete else []
        persistence_invalid = persistence_invalid or (
            not isinstance(durable_digest, str)
            or not isinstance(anchored_durable_digest, str)
            or durable_digest != anchored_durable_digest
            or not _unique_strings(anchored_rule_values)
            or anchored_persistence_key not in set(anchored_rule_values)
        )
        persistence_invalid = persistence_invalid or (
            not actual_persistence_flow
            or not authority_anchor_valid
            or not isinstance(authority, dict)
            or authority.get("valid") is not True
            or authority.get("outcome") != "authorized"
            or authority.get("plan_revision") != current_revision
            or not evaluation_anchor_valid
            or not isinstance(evaluation, dict)
            or evaluation.get("valid") is not True
            or evaluation.get("state") != "supported"
            or evaluation.get("authorized_durable_delta") is not True
            or evaluation.get("plan_revision") != current_revision
            or not isinstance(outcome, dict)
        )
        outcome_value = outcome if isinstance(outcome, dict) else {}
        if persistence.get("persisted") is True:
            persistence_invalid = persistence_invalid or outcome_value.get("durable_delta") is not True
        else:
            persistence_invalid = persistence_invalid or (
                persistence.get("persisted") is not False
                or outcome_value.get("durable_delta") is not False
                or outcome_value.get("terminal_state") == "SUCCEEDED"
            )
    elif isinstance(persistence, dict):
        persistence_invalid = persistence_invalid or (
            persistence.get("persisted") is not False
            or persistence.get("durable_delta_digest") is not None
            or (anchor.get("durable_delta_digest") is not None if anchor_complete else True)
        )
    if persistence_invalid:
        findings.append(_finding(
            "POP2-BEH-KRN-412", "/persistence",
            "persistence requires anchored current authority, supported evaluation, exact durable delta, and legal evaluation-to-persistence flow",
        ))

    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))
