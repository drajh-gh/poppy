#!/usr/bin/env python3
"""Validate a generic Project Operations delivery dispatch manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


RISK_ORDER = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}
PLUGIN_MAX_AUTOMATIC_REMEDIATIONS = 2
REVIEW_STAGES = ("functional_qa", "final_assurance")
EXTENSION_CLASSIFICATIONS = {"required", "not-applicable"}
REQUIRED = {
    "schema_version",
    "project",
    "run_id",
    "work_item",
    "objective",
    "acceptance_contract",
    "non_goals",
    "dependencies",
    "base_revision",
    "risk_floor",
    "maximum_authority",
    "allowed_actions",
    "forbidden_actions",
    "required_gates",
    "stop_conditions",
    "approved_by",
    "approved_at",
}
R3_ACTION = re.compile(r"(?:merge|deploy|production|send\s+(?:email|slack)|invoice|credential|delete)", re.I)


def _is_remediation_limit(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= PLUGIN_MAX_AUTOMATIC_REMEDIATIONS


def _validate_execution_policy(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["execution_policy must be an object"]

    errors: list[str] = []
    if "max_automatic_remediations" in value and not _is_remediation_limit(value["max_automatic_remediations"]):
        errors.append(
            "execution_policy.max_automatic_remediations must be an integer from 0 to 2"
        )
    if "review_stages" in value and value["review_stages"] != list(REVIEW_STAGES):
        errors.append(
            "execution_policy.review_stages must contain distinct ordered stages: "
            "functional_qa, final_assurance"
        )
    return errors


def effective_automatic_remediation_limit(
    manifest: dict[str, Any], adapter_limit: int | None = None
) -> int:
    """Resolve the strictest valid plugin, adapter, and manifest remediation ceiling."""
    limits = [PLUGIN_MAX_AUTOMATIC_REMEDIATIONS]
    if adapter_limit is not None:
        if not _is_remediation_limit(adapter_limit):
            raise ValueError("adapter max_automatic_remediations must be an integer from 0 to 2")
        limits.append(adapter_limit)

    execution_policy = manifest.get("execution_policy")
    if execution_policy is not None:
        policy_errors = _validate_execution_policy(execution_policy)
        if policy_errors:
            raise ValueError("; ".join(policy_errors))
        manifest_limit = execution_policy.get("max_automatic_remediations")
        if manifest_limit is not None:
            limits.append(manifest_limit)
    return min(limits)


def effective_review_stages(manifest: dict[str, Any]) -> tuple[str, str]:
    """Return the fixed ordered review roles for a valid schema-v1 manifest."""
    execution_policy = manifest.get("execution_policy")
    if execution_policy is None:
        return REVIEW_STAGES
    policy_errors = _validate_execution_policy(execution_policy)
    if policy_errors:
        raise ValueError("; ".join(policy_errors))
    stages = execution_policy.get("review_stages")
    return REVIEW_STAGES if stages is None else tuple(stages)


def _validate_extension_gates(value: Any, required_extensions: set[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        return ["extension_gates must be a non-empty list"]

    errors: list[str] = []
    seen: set[str] = set()
    for index, gate in enumerate(value):
        label = f"extension_gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{label} must be an object")
            continue
        gate_id = gate.get("id")
        if not isinstance(gate_id, str) or not re.fullmatch(
            r"[a-z0-9]+(?:-[a-z0-9]+)*", gate_id
        ):
            errors.append(f"{label}.id must be a lowercase hyphenated key")
        elif gate_id in seen:
            errors.append(f"duplicate extension gate: {gate_id}")
        else:
            seen.add(gate_id)
        if gate.get("classification") not in EXTENSION_CLASSIFICATIONS:
            errors.append(
                f"{label}.classification must be required or not-applicable"
            )
        rationale = gate.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"{label}.rationale must be a non-empty string")
        evidence = gate.get("evidence")
        if (
            not isinstance(evidence, list)
            or not evidence
            or any(not isinstance(item, str) or not item.strip() for item in evidence)
        ):
            errors.append(f"{label}.evidence must be a non-empty list of strings")

    for gate_id in sorted(required_extensions - seen):
        errors.append(f"missing adapter-nominated extension gate: {gate_id}")
    return errors


def validate_manifest(
    value: dict[str, Any], required_extensions: set[str] | None = None
) -> list[str]:
    required_extensions = required_extensions or set()
    errors: list[str] = []
    for field in sorted(REQUIRED - set(value)):
        errors.append(f"missing field: {field}")
    if errors:
        return errors
    if value.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if "execution_policy" in value:
        errors.extend(_validate_execution_policy(value["execution_policy"]))
    if "extension_gates" in value:
        errors.extend(
            _validate_extension_gates(value["extension_gates"], required_extensions)
        )
    elif required_extensions:
        for gate_id in sorted(required_extensions):
            errors.append(f"missing adapter-nominated extension gate: {gate_id}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(value.get("project", ""))):
        errors.append("project must be a lowercase hyphenated key")
    floor = value.get("risk_floor")
    maximum = value.get("maximum_authority")
    if floor not in RISK_ORDER or maximum not in RISK_ORDER:
        errors.append("risk_floor and maximum_authority must be R0, R1, R2, or R3")
    elif RISK_ORDER[maximum] < RISK_ORDER[floor]:
        errors.append("maximum_authority cannot be lower than risk_floor")
    for field in ("acceptance_contract", "non_goals", "dependencies", "allowed_actions", "forbidden_actions", "required_gates", "stop_conditions"):
        if not isinstance(value.get(field), list) or not value[field]:
            errors.append(f"{field} must be a non-empty list")
    if maximum != "R3":
        for action in value.get("allowed_actions", []):
            if R3_ACTION.search(str(action)):
                errors.append(f"R3-like action is not allowed under {maximum}: {action}")
    forbidden_text = " ".join(str(item) for item in value.get("forbidden_actions", []))
    for boundary in ("merge", "deploy", "production"):
        if boundary not in forbidden_text.lower() and maximum != "R3":
            errors.append(f"forbidden_actions must explicitly name {boundary} under non-R3 authority")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--required-extension",
        action="append",
        default=[],
        help="Adapter-nominated extension gate ID; repeat for every required gate",
    )
    args = parser.parse_args()
    try:
        value = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("manifest root must be an object")
        required_extensions = set(args.required_extension)
        if len(required_extensions) != len(args.required_extension):
            raise ValueError("--required-extension values must be unique")
        errors = validate_manifest(value, required_extensions)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"ERROR: {error}")
    print("VALID" if not errors else "INVALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
