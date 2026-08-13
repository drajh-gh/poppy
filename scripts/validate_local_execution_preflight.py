#!/usr/bin/env python3
"""Validate a project-neutral local execution preflight packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


RISK_LEVELS = {"R1", "R2"}
CHECK_CATEGORIES = {"dependency", "prerequisite"}
CHECK_STATUSES = {"pass", "fail", "missing", "unverified"}
LOCK_STATES = {"clear", "live", "ambiguous"}
PROCESS_STATES = {"running", "exited", "stopped"}
RESUME_FIELDS = {
    "branch",
    "revision",
    "changed_files",
    "last_passed_gate",
    "owned_processes",
    "blocker",
    "remaining_external_write_gates",
    "resume_instruction",
}


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _normalized_root(value: str) -> str:
    return value.strip().replace("\\", "/").rstrip("/")


def _require_object(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def _validate_canonical_root(packet: dict[str, Any], errors: list[str]) -> None:
    root = _require_object(packet.get("canonical_root"), "canonical_root", errors)
    coverage = _require_object(packet.get("coverage"), "coverage", errors)
    nominated = root.get("nominated")
    observed = root.get("observed")
    exists = root.get("exists")

    root_valid = True
    if not _is_non_empty_string(nominated):
        errors.append("canonical_root.nominated must be a non-empty string")
        root_valid = False
    if not _is_non_empty_string(observed):
        errors.append("canonical_root.observed must be a non-empty string")
        root_valid = False
    if not isinstance(exists, bool):
        errors.append("canonical_root.exists must be boolean")
        root_valid = False
    elif not exists:
        errors.append("canonical root does not exist")
        root_valid = False
    if _is_non_empty_string(nominated) and _is_non_empty_string(observed):
        if _normalized_root(nominated) != _normalized_root(observed):
            errors.append("observed root does not match the project-nominated canonical root")
            root_valid = False

    status = coverage.get("status")
    reasons = coverage.get("reasons")
    if status not in {"full", "gray"}:
        errors.append("coverage.status must be full or gray")
    if not _is_string_list(reasons):
        errors.append("coverage.reasons must be a list of strings")
    elif status == "gray" and not reasons:
        errors.append("Gray coverage must include at least one reason")
    if not root_valid and status != "gray":
        errors.append("canonical-root failure must report dependent coverage as Gray")


def _validate_mutation(packet: dict[str, Any], errors: list[str]) -> None:
    mutation = _require_object(packet.get("mutation"), "mutation", errors)
    if mutation.get("requested") is not True:
        errors.append("mutation.requested must be true for an R1 or R2 preflight")
    if mutation.get("writer_count") != 1 or isinstance(mutation.get("writer_count"), bool):
        errors.append("mutation.writer_count must be exactly one")
    if mutation.get("writer_mode") != "isolated-worktree":
        errors.append("mutation.writer_mode must be isolated-worktree")

    surface = _require_object(mutation.get("surface"), "mutation.surface", errors)
    if surface.get("clean") is not True:
        errors.append("mutation surface must be clean")
    if surface.get("shared_with_active_task") is not False:
        errors.append("mutation surface must not be shared with an active task")
    if surface.get("lock_state") not in LOCK_STATES:
        errors.append("mutation.surface.lock_state must be clear, live, or ambiguous")
    elif surface.get("lock_state") != "clear":
        errors.append("mutation surface must not have a live or ambiguous lock")
    if surface.get("branch_related") is not True:
        errors.append("mutation branch must be related to the approved change")


def _validate_checks(packet: dict[str, Any], errors: list[str]) -> None:
    checks = packet.get("preflight_checks")
    if not isinstance(checks, list):
        errors.append("preflight_checks must be a list")
        return

    seen: set[str] = set()
    for index, value in enumerate(checks):
        path = f"preflight_checks[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            continue
        check_id = value.get("id")
        if not _is_non_empty_string(check_id):
            errors.append(f"{path}.id must be a non-empty string")
        elif check_id in seen:
            errors.append(f"{path}.id must be unique")
        else:
            seen.add(check_id)
        if value.get("category") not in CHECK_CATEGORIES:
            errors.append(f"{path}.category must be dependency or prerequisite")
        if not isinstance(value.get("required"), bool):
            errors.append(f"{path}.required must be boolean")
        status = value.get("status")
        if status not in CHECK_STATUSES:
            errors.append(f"{path}.status must be pass, fail, missing, or unverified")
        elif value.get("required") is True and status != "pass":
            errors.append(f"{path} is required and must pass")

    dependency = _require_object(packet.get("dependency_state"), "dependency_state", errors)
    if dependency.get("consistent") is not True:
        errors.append("dependency state must be consistent")
    if dependency.get("partial_mutation_detected") is not False:
        errors.append("dependency state must not contain a partial mutation")


def _validate_process_control(packet: dict[str, Any], errors: list[str]) -> None:
    control = _require_object(packet.get("process_control"), "process_control", errors)
    ledger = control.get("owned_processes")
    ledger_ids: set[str] = set()
    if not isinstance(ledger, list):
        errors.append("process_control.owned_processes must be a list")
        ledger = []
    for index, value in enumerate(ledger):
        path = f"process_control.owned_processes[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            continue
        process_id = value.get("id")
        if not _is_non_empty_string(process_id):
            errors.append(f"{path}.id must be a non-empty string")
        elif process_id in ledger_ids:
            errors.append(f"{path}.id must be unique")
        else:
            ledger_ids.add(process_id)
        if value.get("state") not in PROCESS_STATES:
            errors.append(f"{path}.state must be running, exited, or stopped")

    timed_out = control.get("timed_out")
    if not isinstance(timed_out, bool):
        errors.append("process_control.timed_out must be boolean")
    survivors = control.get("surviving_owned_processes")
    if not _is_string_list(survivors):
        errors.append("process_control.surviving_owned_processes must be a list of strings")
        survivors = []
    else:
        unknown = sorted(set(survivors) - ledger_ids)
        if unknown:
            errors.append("surviving owned processes must be present in the owned-process ledger")
        if survivors:
            errors.append("owned child processes survived the timeout boundary")
    if timed_out is True:
        if not ledger:
            errors.append("a timeout requires a non-empty owned-process ledger")
        if any(isinstance(item, dict) and item.get("state") == "running" for item in ledger):
            errors.append("timed-out owned processes must not remain running")
        if control.get("post_timeout_integrity") != "pass":
            errors.append("post-timeout integrity check must pass")
    elif control.get("post_timeout_integrity") not in {"not-required", "pass"}:
        errors.append("post_timeout_integrity must be not-required or pass")


def _validate_interruption(packet: dict[str, Any], errors: list[str]) -> None:
    interruption = _require_object(packet.get("interruption"), "interruption", errors)
    occurred = interruption.get("occurred")
    if not isinstance(occurred, bool):
        errors.append("interruption.occurred must be boolean")
        return
    resume = interruption.get("resume_packet")
    if not occurred:
        if resume is not None:
            errors.append("resume_packet must be null when no interruption occurred")
        return
    if not isinstance(resume, dict):
        errors.append("interrupted work requires a complete resume_packet")
        return
    for field in sorted(RESUME_FIELDS - set(resume)):
        errors.append(f"resume_packet missing field: {field}")
    for field in ("branch", "revision", "last_passed_gate", "resume_instruction"):
        if field in resume and not _is_non_empty_string(resume[field]):
            errors.append(f"resume_packet.{field} must be a non-empty string")
    if "blocker" in resume and not isinstance(resume["blocker"], str):
        errors.append("resume_packet.blocker must be a string")
    for field in ("changed_files", "owned_processes", "remaining_external_write_gates"):
        if field in resume and not _is_string_list(resume[field]):
            errors.append(f"resume_packet.{field} must be a list of strings")


def validate_packet(value: dict[str, Any]) -> list[str]:
    """Return deterministic validation errors without touching local state."""
    errors: list[str] = []
    if value.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for field in ("project", "run_id"):
        if not _is_non_empty_string(value.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if value.get("risk") not in RISK_LEVELS:
        errors.append("risk must be R1 or R2")
    _validate_canonical_root(value, errors)
    _validate_mutation(value, errors)
    _validate_checks(value, errors)
    _validate_process_control(value, errors)
    _validate_interruption(value, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        value = json.loads(args.packet.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("packet root must be an object")
        errors = validate_packet(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors = [str(exc)]
    if args.as_json:
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    else:
        for error in errors:
            print(f"ERROR: {error}")
        print("VALID" if not errors else "INVALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
