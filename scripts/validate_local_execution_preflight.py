#!/usr/bin/env python3
"""Validate a project-neutral local execution preflight packet."""

from __future__ import annotations

import argparse
import json
import ntpath
import posixpath
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


def _canonical_root_identity(value: str) -> tuple[tuple[str, str] | None, str | None]:
    """Return a safe lexical identity for an absolute path without filesystem access."""
    if value != value.strip() or "\x00" in value:
        return None, "must not contain surrounding whitespace or null bytes"

    windows = value.replace("/", "\\")
    if windows.startswith(("\\\\.\\", "\\\\?\\")):
        return None, "must not use a Windows device or extended-length namespace"
    drive_path = False
    if len(windows) >= 2 and windows[1] == ":":
        if not (windows[0].isalpha() and len(windows) >= 3 and windows[2] == "\\"):
            return None, "must be absolute; Windows drive-relative paths are not allowed"
        path_style = "windows"
        drive_path = True
    elif windows.startswith("\\\\"):
        drive, _ = ntpath.splitdrive(windows)
        share_parts = [part for part in drive[2:].split("\\") if part]
        if len(share_parts) != 2 or not ntpath.isabs(windows):
            return None, "must be an absolute UNC path with server and share"
        path_style = "windows"
    elif value.startswith("/") and not value.startswith("//"):
        path_style = "posix"
    else:
        return None, "must be a syntactically absolute Windows, UNC, or POSIX path"

    separator = "\\" if path_style == "windows" else "/"
    candidate = windows if path_style == "windows" else value
    segments = [part for part in candidate.split(separator) if part]
    if ".." in segments:
        return None, "must not contain parent-traversal segments"
    if path_style == "windows" and any(
        part != "." and part.rstrip(" .") != part for part in segments
    ):
        return None, "must not contain Windows path segments with trailing spaces or dots"
    stream_segments = segments[1:] if drive_path else segments
    if path_style == "windows" and any(":" in part for part in stream_segments):
        return None, "must not use a Windows alternate-data-stream path"

    if path_style == "windows":
        return (path_style, ntpath.normcase(ntpath.normpath(candidate))), None
    return (path_style, posixpath.normpath(candidate)), None


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
    nominated_identity = None
    observed_identity = None
    if _is_non_empty_string(nominated):
        nominated_identity, path_error = _canonical_root_identity(nominated)
        if path_error:
            errors.append(f"canonical_root.nominated {path_error}")
            root_valid = False
    if _is_non_empty_string(observed):
        observed_identity, path_error = _canonical_root_identity(observed)
        if path_error:
            errors.append(f"canonical_root.observed {path_error}")
            root_valid = False
    if nominated_identity is not None and observed_identity is not None:
        if nominated_identity != observed_identity:
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
    nominated = packet.get("nominated_checks")
    nominated_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(nominated, list):
        errors.append("nominated_checks must be a list")
        nominated = []
    for index, value in enumerate(nominated):
        path = f"nominated_checks[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            continue
        check_id = value.get("id")
        if not _is_non_empty_string(check_id):
            errors.append(f"{path}.id must be a non-empty string")
        elif check_id in nominated_by_id:
            errors.append(f"{path}.id must be unique")
        else:
            nominated_by_id[check_id] = value
        if value.get("category") not in CHECK_CATEGORIES:
            errors.append(f"{path}.category must be dependency or prerequisite")
        if not isinstance(value.get("required"), bool):
            errors.append(f"{path}.required must be boolean")

    checks = packet.get("preflight_checks")
    if not isinstance(checks, list):
        errors.append("preflight_checks must be a list")
        checks = []

    checks_by_id: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(checks):
        path = f"preflight_checks[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            continue
        check_id = value.get("id")
        if not _is_non_empty_string(check_id):
            errors.append(f"{path}.id must be a non-empty string")
        elif check_id in checks_by_id:
            errors.append(f"{path}.id must be unique")
        else:
            checks_by_id[check_id] = value
        if value.get("category") not in CHECK_CATEGORIES:
            errors.append(f"{path}.category must be dependency or prerequisite")
        if not isinstance(value.get("required"), bool):
            errors.append(f"{path}.required must be boolean")
        status = value.get("status")
        if status not in CHECK_STATUSES:
            errors.append(f"{path}.status must be pass, fail, missing, or unverified")
        elif status != "pass":
            errors.append(f"{path} is nominated and must have status pass")

    for check_id in sorted(nominated_by_id.keys() - checks_by_id.keys()):
        errors.append(f"preflight_checks omits nominated check: {check_id}")
    for check_id in sorted(checks_by_id.keys() - nominated_by_id.keys()):
        errors.append(f"preflight_checks contains undeclared check: {check_id}")
    for check_id in sorted(nominated_by_id.keys() & checks_by_id.keys()):
        declaration = nominated_by_id[check_id]
        result = checks_by_id[check_id]
        if result.get("category") != declaration.get("category"):
            errors.append(f"preflight check category does not match nomination: {check_id}")
        if result.get("required") != declaration.get("required"):
            errors.append(f"preflight check required flag does not match nomination: {check_id}")

    dependency = _require_object(packet.get("dependency_state"), "dependency_state", errors)
    if dependency.get("consistent") is not True:
        errors.append("dependency state must be consistent")
    if dependency.get("partial_mutation_detected") is not False:
        errors.append("dependency state must not contain a partial mutation")


def _validate_process_control(packet: dict[str, Any], errors: list[str]) -> set[str]:
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
    return ledger_ids


def _validate_interruption(
    packet: dict[str, Any], errors: list[str], authoritative_process_ids: set[str]
) -> None:
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
    if "blocker" in resume and not _is_non_empty_string(resume["blocker"]):
        errors.append("resume_packet.blocker must be a non-empty string")
    for field in ("changed_files", "owned_processes", "remaining_external_write_gates"):
        if field in resume and not _is_string_list(resume[field]):
            errors.append(f"resume_packet.{field} must be a list of strings")
    resume_processes = resume.get("owned_processes")
    if _is_string_list(resume_processes):
        if len(resume_processes) != len(set(resume_processes)):
            errors.append("resume_packet.owned_processes must not contain duplicates")
        resume_ids = set(resume_processes)
        for process_id in sorted(authoritative_process_ids - resume_ids):
            errors.append(f"resume_packet.owned_processes omits ledger process: {process_id}")
        for process_id in sorted(resume_ids - authoritative_process_ids):
            errors.append(f"resume_packet.owned_processes contains non-ledger process: {process_id}")


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
    authoritative_process_ids = _validate_process_control(value, errors)
    _validate_interruption(value, errors, authoritative_process_ids)
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
