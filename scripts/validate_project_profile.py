#!/usr/bin/env python3
"""Validate a Project Operations project-ops.json profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STAGES = {"discovery", "active-delivery", "stabilization", "maintenance", "paused", "closed"}
ARCHETYPES = {
    "support-maintenance",
    "product-launch",
    "discovery-validation",
    "fixed-scope-delivery",
    "retainer-capacity",
    "internal-initiative",
}
TRANSCRIPT_QUALITY = {"reliable", "partial", "unreliable", "unavailable"}
ADOPTION_MODES = {"new", "existing", "clone", "reconfigure"}
SENSITIVITY = {"internal", "confidential", "restricted"}
AUTHORITY_FIELDS = {
    "contracted_scope",
    "approved_estimate",
    "budget_baseline",
    "actual_hours",
    "planned_allocation",
    "invoice_state",
    "work_status",
    "implementation",
    "deployment",
    "requirements",
    "milestone_dates",
    "client_commitments",
}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "project",
    "vault",
    "language",
    "sources",
    "authority",
    "stakeholders",
    "approvals",
    "cadence",
    "tolerances",
    "onboarding",
}
FORBIDDEN_KEY_PATTERN = re.compile(r"(?:password|passwd|secret|token|credential|api[_-]?key)$", re.I)
TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
REPOSITORY_PATTERN = re.compile(r"[^/\s]+/[^/\s]+")
TIMEZONE_PATTERN = re.compile(r"(?:UTC|[A-Za-z0-9._+-]+(?:/[A-Za-z0-9._+-]+)+)")
SOURCE_NAMES = {"drive", "povio_dashboard", "tracker", "github", "slack", "gmail", "calendar"}
APPROVER_ROLES = {"scope", "budget", "milestone", "release", "client_communication"}


def load_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("profile root must be a JSON object")
    return value


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _scan_forbidden_keys(value: Any, prefix: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if FORBIDDEN_KEY_PATTERN.search(str(key)):
                errors.append(f"{path}: credentials and secrets do not belong in a project profile")
            _scan_forbidden_keys(child, path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden_keys(child, f"{prefix}[{index}]", errors)


def _require_string_list(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path} must be a list of non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{path} must not contain duplicates")
    return value


def _validate_sources(
    sources: Any,
    authority: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    allow_draft: bool,
) -> None:
    if not isinstance(sources, dict):
        errors.append("sources must be an object")
        return
    for name in sorted(SOURCE_NAMES - set(sources)):
        errors.append(f"sources.{name} is missing")
    if any(not isinstance(sources.get(name), dict) for name in SOURCE_NAMES if name in sources):
        errors.append("every configured source must be an object")
        return

    drive = sources.get("drive", {})
    _require_string_list(drive.get("folder_ids", []), "sources.drive.folder_ids", errors)
    classes = drive.get("classes", {})
    if not isinstance(classes, dict):
        errors.append("sources.drive.classes must be an object")
        classes = {}
    for class_name, mapping in classes.items():
        if not isinstance(mapping, dict) or _is_missing(mapping.get("file_id")):
            errors.append(f"sources.drive.classes.{class_name} must include a stable file_id")

    dashboard = sources.get("povio_dashboard", {})
    if dashboard.get("access") not in {"read-only", "read-write"}:
        errors.append("sources.povio_dashboard.access must be read-only or read-write")
    dashboard_capabilities = _require_string_list(
        dashboard.get("capabilities", []), "sources.povio_dashboard.capabilities", errors
    )

    tracker = sources.get("tracker", {})
    tracker_ids = _require_string_list(tracker.get("project_ids", []), "sources.tracker.project_ids", errors)
    _require_string_list(tracker.get("canonical_for", []), "sources.tracker.canonical_for", errors)
    if tracker_ids and _is_missing(tracker.get("system")):
        errors.append("sources.tracker.system is required when tracker project_ids are configured")

    github = sources.get("github", {})
    repositories = _require_string_list(github.get("repositories", []), "sources.github.repositories", errors)
    for repository in repositories:
        if not REPOSITORY_PATTERN.fullmatch(repository):
            errors.append(f"sources.github.repositories has invalid owner/repo slug: {repository!r}")
    branches = github.get("default_branches", {})
    if not isinstance(branches, dict):
        errors.append("sources.github.default_branches must be an object")
    else:
        for repository in repositories:
            if _is_missing(branches.get(repository)):
                errors.append(f"sources.github.default_branches is missing {repository}")

    for source_name, field_names in {
        "slack": ("client_channels", "internal_channels", "support_channels"),
        "gmail": ("client_domains", "contacts"),
        "calendar": ("calendar_ids", "recurring_meetings"),
    }.items():
        source = sources.get(source_name, {})
        for field_name in field_names:
            _require_string_list(source.get(field_name, []), f"sources.{source_name}.{field_name}", errors)

    mapping_issues = warnings if allow_draft else errors
    for field in AUTHORITY_FIELDS:
        mapping = authority.get(field)
        if not isinstance(mapping, str):
            continue
        if mapping.startswith("drive.") and mapping.split(".", 1)[1] not in classes:
            mapping_issues.append(f"authority.{field} references missing sources.drive.classes.{mapping.split('.', 1)[1]}")
        if mapping.startswith("povio_dashboard.") and mapping.split(".", 1)[1] not in dashboard_capabilities:
            mapping_issues.append(f"authority.{field} references an unlisted Povio Dashboard capability")
        if mapping == "tracker" and not tracker_ids:
            mapping_issues.append(f"authority.{field} references tracker but no tracker project_ids are configured")
        if mapping in {"github", "github-ci"} and not repositories:
            mapping_issues.append(f"authority.{field} references GitHub but no repositories are configured")


def _validate_cadence(cadence: Any, errors: list[str]) -> None:
    if not isinstance(cadence, dict):
        errors.append("cadence must be an object")
        return
    for key in ("daily_brief", "weekly_review", "monthly_portfolio"):
        if not isinstance(cadence.get(key), dict) or not isinstance(cadence[key].get("enabled"), bool):
            errors.append(f"cadence.{key}.enabled must be boolean")
    for path, value in (
        ("cadence.daily_brief.time", cadence.get("daily_brief", {}).get("time")),
        ("cadence.weekly_review.time", cadence.get("weekly_review", {}).get("time")),
    ):
        if not isinstance(value, str) or not TIME_PATTERN.fullmatch(value):
            errors.append(f"{path} must use 24-hour HH:MM")
    day = cadence.get("weekly_review", {}).get("day")
    if day not in {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}:
        errors.append("cadence.weekly_review.day must be a lowercase weekday")
    quiet_hours = cadence.get("quiet_hours")
    if not isinstance(quiet_hours, list) or len(quiet_hours) != 2 or any(
        not isinstance(value, str) or not TIME_PATTERN.fullmatch(value) for value in quiet_hours
    ):
        errors.append("cadence.quiet_hours must contain two HH:MM values")
    improvement = cadence.get("workflow_improvement")
    if improvement is not None:
        if not isinstance(improvement, dict):
            errors.append("cadence.workflow_improvement must be an object")
        else:
            if not isinstance(improvement.get("enabled"), bool):
                errors.append("cadence.workflow_improvement.enabled must be boolean")
            if improvement.get("frequency") not in {"weekdays", "weekly"}:
                errors.append("cadence.workflow_improvement.frequency must be weekdays or weekly")
            if not isinstance(improvement.get("time"), str) or not TIME_PATTERN.fullmatch(improvement["time"]):
                errors.append("cadence.workflow_improvement.time must use 24-hour HH:MM")
            if not isinstance(improvement.get("changed_only"), bool):
                errors.append("cadence.workflow_improvement.changed_only must be boolean")
            if improvement.get("max_specialists") not in {0, 1, 2}:
                errors.append("cadence.workflow_improvement.max_specialists must be 0, 1, or 2")


def validate_profile(profile: dict[str, Any], allow_draft: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    missing_top = sorted(REQUIRED_TOP_LEVEL - set(profile))
    for key in missing_top:
        errors.append(f"missing top-level field: {key}")

    project = profile.get("project")
    vault = profile.get("vault")
    language = profile.get("language")
    authority = profile.get("authority")
    approvals = profile.get("approvals")
    sources = profile.get("sources")
    stakeholders = profile.get("stakeholders")
    cadence = profile.get("cadence")
    tolerances = profile.get("tolerances")
    onboarding = profile.get("onboarding")

    for name, value in {
        "project": project,
        "vault": vault,
        "language": language,
        "authority": authority,
        "approvals": approvals,
        "sources": sources,
        "stakeholders": stakeholders,
        "cadence": cadence,
        "tolerances": tolerances,
        "onboarding": onboarding,
    }.items():
        if not isinstance(value, dict):
            errors.append(f"{name} must be an object")

    if errors:
        _scan_forbidden_keys(profile, "", errors)
        return errors, warnings

    key = project.get("key")
    if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key):
        errors.append("project.key must use lowercase letters, numbers, and single hyphens")
    for field in ("name", "client", "timezone"):
        if _is_missing(project.get(field)):
            errors.append(f"project.{field} is required")
    if project.get("stage") not in STAGES:
        errors.append(f"project.stage must be one of {sorted(STAGES)}")
    if project.get("sensitivity") not in SENSITIVITY:
        errors.append(f"project.sensitivity must be one of {sorted(SENSITIVITY)}")

    archetypes = project.get("archetypes")
    if not isinstance(archetypes, dict):
        errors.append("project.archetypes must be an object")
    else:
        primary = archetypes.get("primary")
        overlays = archetypes.get("overlays", [])
        if primary not in ARCHETYPES:
            errors.append(f"project.archetypes.primary must be one of {sorted(ARCHETYPES)}")
        if not isinstance(overlays, list) or any(item not in ARCHETYPES for item in overlays):
            errors.append("project.archetypes.overlays contains an unknown archetype")
        if primary in overlays:
            errors.append("primary archetype must not be repeated as an overlay")

    if vault.get("adoption_mode") not in ADOPTION_MODES:
        errors.append(f"vault.adoption_mode must be one of {sorted(ADOPTION_MODES)}")
    if vault.get("strategy") != "per-project":
        errors.append("vault.strategy must be per-project")
    if isinstance(key, str) and vault.get("project_root") != f"wiki/{key}":
        errors.append("vault.project_root must equal wiki/<project.key>")
    human_owned = vault.get("human_owned")
    if not isinstance(human_owned, list) or "inbox.md" not in human_owned or "daily/" not in human_owned:
        errors.append("vault.human_owned must protect inbox.md and daily/")
    if vault.get("portfolio_publish") != "sanitized-summary":
        warnings.append("vault.portfolio_publish should normally be sanitized-summary")

    if language.get("transcript_quality") not in TRANSCRIPT_QUALITY:
        errors.append(f"language.transcript_quality must be one of {sorted(TRANSCRIPT_QUALITY)}")
    for field in ("client_language", "source_languages", "meeting_evidence_mode"):
        if _is_missing(language.get(field)):
            errors.append(f"language.{field} is required")
    if language.get("client_language") == "sl-SI" and language.get("transcript_quality") in {"unreliable", "unavailable"}:
        if language.get("meeting_evidence_mode") != "structured-notes-plus-confirmation":
            warnings.append("Slovenian projects without reliable transcripts should use structured-notes-plus-confirmation")

    timezone = project.get("timezone")
    if not isinstance(timezone, str) or not TIMEZONE_PATTERN.fullmatch(timezone):
        errors.append("project.timezone must use an IANA-style name such as Europe/Ljubljana")

    if authority.get("conflicts") != "preserve-and-escalate":
        errors.append("authority.conflicts must be preserve-and-escalate")
    accepted_gaps = onboarding.get("accepted_gaps", [])
    if not isinstance(accepted_gaps, list):
        errors.append("onboarding.accepted_gaps must be a list")
        accepted_gaps = []
    for field in sorted(AUTHORITY_FIELDS):
        if field not in authority:
            errors.append(f"authority.{field} is missing")
        elif _is_missing(authority.get(field)):
            path = f"authority.{field}"
            if allow_draft:
                warnings.append(f"{path} is unresolved")
            elif path not in accepted_gaps:
                errors.append(f"{path} must be mapped or listed in onboarding.accepted_gaps")
    unknown_gaps = sorted(set(accepted_gaps) - {f"authority.{field}" for field in AUTHORITY_FIELDS})
    for gap in unknown_gaps:
        warnings.append(f"onboarding.accepted_gaps contains a non-authority gap: {gap}")

    _validate_sources(sources, authority, errors, warnings, allow_draft)

    approvers = stakeholders.get("approvers")
    if not isinstance(stakeholders.get("records"), list):
        errors.append("stakeholders.records must be a list")
    if not isinstance(approvers, dict):
        errors.append("stakeholders.approvers must be an object")
        approvers = {}
    for role in sorted(APPROVER_ROLES):
        names = _require_string_list(approvers.get(role, []), f"stakeholders.approvers.{role}", errors)
        if onboarding.get("status") == "complete" and not names:
            warnings.append(f"stakeholders.approvers.{role} is empty in a complete profile")

    allowed_approval_values = {"allow", "allow-with-audit", "draft", "confirm", "named-approver", "deny"}
    for field in (
        "obsidian_internal_write",
        "external_drafts",
        "tracker_write",
        "email_send",
        "slack_send",
        "calendar_write",
        "baseline_change",
        "finance_write",
        "merge_or_deploy",
    ):
        value = approvals.get(field)
        if value not in allowed_approval_values:
            errors.append(f"approvals.{field} has unsupported value: {value!r}")

    for field, value in tolerances.items():
        if field == "missing_required_baseline":
            if value != "gray":
                errors.append("tolerances.missing_required_baseline must be gray")
        elif not isinstance(value, (int, float)) or value < 0:
            errors.append(f"tolerances.{field} must be a non-negative number")

    _validate_cadence(cadence, errors)

    if profile.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if onboarding.get("status") == "complete" and allow_draft:
        warnings.append("profile says onboarding is complete but draft validation was requested")
    if onboarding.get("status") not in {"draft", "ready-to-apply", "complete"}:
        errors.append("onboarding.status must be draft, ready-to-apply, or complete")

    _scan_forbidden_keys(profile, "", errors)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--allow-draft", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
        errors, warnings = validate_profile(profile, allow_draft=args.allow_draft)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        errors, warnings = [str(exc)], []

    if args.as_json:
        print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}, indent=2))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print("VALID" if not errors else "INVALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
