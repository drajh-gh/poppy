#!/usr/bin/env python3
"""Validate normalized, project-neutral task-orchestration packets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TITLE_SEPARATOR = " · "
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{7,64}$")
RAW_MARKUP_PATTERNS = (
    re.compile(r"<[^>]+>"),
    re.compile(r"\{\{[^}]+\}\}"),
    re.compile(r"\[(?:TODO|INSERT|PLACEHOLDER)[^]]*\]", re.IGNORECASE),
    re.compile(r"```|(?:^|\s)(?:prompt|message|instructions):", re.IGNORECASE),
)
EFFORTS = {"low", "medium", "high", "xhigh"}
EVENTS = {
    "start",
    "ownership",
    "milestone",
    "changed_direction",
    "blocker",
    "decision_request",
    "final",
}


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _raw_markup(value: str) -> bool:
    return any(pattern.search(value) for pattern in RAW_MARKUP_PATTERNS)


def _validate_title(
    title: Any,
    role: Any,
    redundant_prefixes: set[str],
    location: str,
) -> list[str]:
    errors: list[str] = []
    if not _non_empty(title):
        return [f"{location}.title must be a non-empty string"]
    assert isinstance(title, str)
    if _raw_markup(title):
        errors.append(f"{location}.title contains raw prompt markup")
    parts = title.split(TITLE_SEPARATOR)
    if len(parts) != 3 or any(not part.strip() for part in parts):
        errors.append(f"{location}.title must use '<work-key> · <role> · <outcome>'")
        return errors
    if not _non_empty(role) or parts[1].strip().casefold() != str(role).strip().casefold():
        errors.append(f"{location}.title role does not match {location}.role")
    if parts[0].strip().casefold() in redundant_prefixes:
        errors.append(f"{location}.title begins with a redundant project prefix")
    return errors


def _validate_effort(worker: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    effort = worker.get("effort")
    rationale = worker.get("effort_rationale")
    if effort not in EFFORTS:
        errors.append(f"{location}.effort must be one of {sorted(EFFORTS)}")
    if not _non_empty(rationale):
        errors.append(f"{location}.effort_rationale must be a non-empty string")
    elif effort == "xhigh":
        normalized = str(rationale).casefold()
        exceptional_terms = ("exceptional", "architecture", "safety", "high-risk", "high risk")
        if len(str(rationale).strip()) < 40 or not any(term in normalized for term in exceptional_terms):
            errors.append(f"{location}.xhigh effort requires a concrete exceptional architecture or safety rationale")
    return errors


def _validated_limits(packet: dict[str, Any], errors: list[str]) -> tuple[int, int]:
    max_active = packet.get("max_active_workers")
    max_created = packet.get("max_created_workers")
    if not _integer(max_active) or max_active < 1:
        errors.append("max_active_workers must be a positive integer")
        max_active = 0
    if not _integer(max_created) or max_created < 1:
        errors.append("max_created_workers must be a positive integer")
        max_created = 0
    if max_active > 2 or max_created > 5:
        extension = packet.get("approved_budget_extension")
        if not isinstance(extension, dict):
            errors.append("task budget above two active or five created requires approved_budget_extension")
        else:
            if not _non_empty(extension.get("approved_by")) or not _non_empty(extension.get("rationale")):
                errors.append("approved_budget_extension requires approved_by and rationale")
            if (
                extension.get("max_active_workers") != max_active
                or extension.get("max_created_workers") != max_created
            ):
                errors.append("approved_budget_extension limits must match the packet limits")
    return int(max_active), int(max_created)


def validate_plan(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root_id = packet.get("root_task_id")
    if not _non_empty(root_id):
        errors.append("root_task_id must be a non-empty string")
    if packet.get("root_human_authority") is not True:
        errors.append("root_human_authority must be true")
    if packet.get("recursive_delegation_allowed") is not False:
        errors.append("recursive_delegation_allowed must be false")

    prefixes_value = packet.get("redundant_project_prefixes", [])
    if not isinstance(prefixes_value, list) or any(not _non_empty(value) for value in prefixes_value):
        errors.append("redundant_project_prefixes must be a list of non-empty strings")
        prefixes: set[str] = set()
    else:
        prefixes = {str(value).strip().casefold() for value in prefixes_value}

    max_active, max_created = _validated_limits(packet, errors)
    workers = packet.get("workers")
    if not isinstance(workers, list):
        return errors + ["workers must be a list"]
    if len(workers) > max_created:
        errors.append("workers exceed max_created_workers")

    seen: set[str] = set()
    active_count = 0
    for index, value in enumerate(workers):
        location = f"workers[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{location} must be an object")
            continue
        task_id = value.get("task_id")
        if not _non_empty(task_id):
            errors.append(f"{location}.task_id must be a non-empty string")
        elif task_id in seen:
            errors.append(f"{location}.task_id must be unique")
        else:
            seen.add(str(task_id))
        if value.get("root_task_id") != root_id or value.get("parent_task_id") != root_id:
            errors.append(f"{location} must name the root as root_task_id and parent_task_id")
        if value.get("delegation_depth") != 1:
            errors.append(f"{location}.delegation_depth must be 1")
        if value.get("human_authority") is not False:
            errors.append(f"{location}.human_authority must be false")
        if value.get("decision_protocol") != "relay_to_root":
            errors.append(f"{location}.decision_protocol must be relay_to_root")
        if value.get("missing_authority_signal") != "NEEDS_PARENT_DECISION":
            errors.append(f"{location}.missing_authority_signal must be NEEDS_PARENT_DECISION")
        if value.get("created_child_ids") != []:
            errors.append(f"{location}.created_child_ids must be empty; recursive delegation is forbidden")
        if value.get("status") == "active":
            active_count += 1
        remaining = value.get("remaining_task_allowance")
        if not _integer(remaining) or remaining < 0 or remaining >= max_created:
            errors.append(f"{location}.remaining_task_allowance must be between zero and max_created_workers - 1")
        errors.extend(_validate_title(value.get("title"), value.get("role"), prefixes, location))
        errors.extend(_validate_effort(value, location))

    if active_count > max_active:
        errors.append("active workers exceed max_active_workers")
    updates = packet.get("updates", [])
    if not isinstance(updates, list):
        errors.append("updates must be a list")
    else:
        for index, update in enumerate(updates):
            if not isinstance(update, dict) or update.get("event") not in EVENTS:
                errors.append(f"updates[{index}].event is not a material task event")
    return errors


def _repository_recoverable(state: Any, location: str, errors: list[str]) -> bool:
    if not isinstance(state, dict):
        errors.append(f"{location}.repository_state must be an object")
        return False
    kind = state.get("kind")
    if kind in {"clean", "not_applicable"}:
        return True
    if kind == "commit_recoverable":
        if not _non_empty(state.get("branch")) or not _non_empty(state.get("commit")):
            errors.append(f"{location}.repository_state commit_recoverable requires branch and commit")
            return False
        if not SHA_PATTERN.fullmatch(str(state["commit"])):
            errors.append(f"{location}.repository_state.commit must look like a Git commit")
            return False
        return True
    errors.append(f"{location}.repository_state.kind must be clean, not_applicable, or commit_recoverable")
    return False


def validate_closure(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    root_id = packet.get("root_task_id")
    if not _non_empty(root_id):
        errors.append("root_task_id must be a non-empty string")
    expected = packet.get("expected_worker_ids")
    workers = packet.get("workers")
    if not isinstance(expected, list) or any(not _non_empty(value) for value in expected):
        errors.append("expected_worker_ids must be a list of non-empty strings")
        expected_set: set[str] = set()
    else:
        expected_set = {str(value) for value in expected}
        if len(expected_set) != len(expected):
            errors.append("expected_worker_ids must be unique")
    if not isinstance(workers, list):
        return errors + ["workers must be a list"]

    observed: set[str] = set()
    for index, value in enumerate(workers):
        location = f"workers[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{location} must be an object")
            continue
        task_id = value.get("task_id")
        if _non_empty(task_id):
            if str(task_id) in observed:
                errors.append(f"{location}.task_id must be unique")
            observed.add(str(task_id))
        else:
            errors.append(f"{location}.task_id must be a non-empty string")
        if value.get("root_task_id") != root_id or value.get("parent_task_id") != root_id:
            errors.append(f"{location} must name the root as root_task_id and parent_task_id")
        if value.get("status") != "complete":
            errors.append(f"{location}.status must be complete")
        if value.get("attention_required") is not False:
            errors.append(f"{location}.attention_required must be false")
        if value.get("result_captured_by_parent") is not True:
            errors.append(f"{location}.result_captured_by_parent must be true")
        card = value.get("closure_card")
        if not isinstance(card, dict):
            errors.append(f"{location}.closure_card must be an object")
        else:
            for field in ("outcome", "repository_state", "residual_risk", "next_action"):
                if not _non_empty(card.get(field)):
                    errors.append(f"{location}.closure_card.{field} must be a non-empty string")
            evidence = card.get("evidence")
            if not isinstance(evidence, list) or not evidence or any(not _non_empty(item) for item in evidence):
                errors.append(f"{location}.closure_card.evidence must be a non-empty string list")
        recoverable = _repository_recoverable(value.get("repository_state"), location, errors)
        if value.get("archive_requested") is True and not recoverable:
            errors.append(f"{location} cannot be archived with unrecoverable repository state")
        if value.get("worktree_cleanup_requested") is True and value.get("cleanup_approved") is not True:
            errors.append(f"{location} cleanup requires separate explicit approval")

    if observed != expected_set:
        missing = sorted(expected_set - observed)
        extra = sorted(observed - expected_set)
        errors.append(f"worker closure cards do not match expected_worker_ids; missing={missing}, extra={extra}")

    root = packet.get("root")
    if not isinstance(root, dict):
        errors.append("root must be an object")
    else:
        if root.get("task_id") != root_id:
            errors.append("root.task_id must match root_task_id")
        if root.get("archive_requested") is True and root.get("user_archive_approved") is not True:
            errors.append("root task cannot auto-archive without explicit user approval")
        if root.get("cleanup_requested") is True and root.get("cleanup_approved") is not True:
            errors.append("root cleanup requires separate explicit approval")
    return errors


def validate_packet(packet: Any) -> list[str]:
    if not isinstance(packet, dict):
        return ["packet root must be an object"]
    if packet.get("schema_version") != 1:
        return ["schema_version must be 1"]
    packet_type = packet.get("packet_type")
    if packet_type == "plan":
        return validate_plan(packet)
    if packet_type == "closure":
        return validate_closure(packet)
    return ["packet_type must be plan or closure"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate_packet(packet)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"PASS: valid task-orchestration {packet['packet_type']} packet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
