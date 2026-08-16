#!/usr/bin/env python3
"""Recommendation-first onboarding wizard for Project Operations."""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_project_profile import validate_profile


SCRIPT_ROOT = Path(__file__).resolve().parent


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "project"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def recommended_archetype(stage: str, commercial_model: str) -> tuple[str, list[str]]:
    if stage == "maintenance":
        return "support-maintenance", ["fixed-scope-delivery"] if commercial_model == "fixed-price" else []
    if stage == "discovery":
        return "discovery-validation", ["fixed-scope-delivery"] if commercial_model == "fixed-price" else []
    if commercial_model == "retainer":
        return "retainer-capacity", []
    if commercial_model == "fixed-price":
        return "fixed-scope-delivery", []
    if stage in {"active-delivery", "stabilization"}:
        return "product-launch", ["retainer-capacity"] if commercial_model == "time-and-materials" else []
    return "internal-initiative", []


def defaults(name: str, key: str, client: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 1,
        "project": {
            "key": key,
            "name": name,
            "client": client,
            "stage": "active-delivery",
            "archetypes": {"primary": "product-launch", "overlays": []},
            "objectives": [],
            "next_milestone": None,
            "timezone": "Europe/Ljubljana",
            "sensitivity": "confidential",
        },
        "vault": {
            "strategy": "per-project",
            "path": None,
            "adoption_mode": "new",
            "project_root": f"wiki/{key}",
            "human_owned": ["inbox.md", "daily/"],
            "portfolio_publish": "sanitized-summary",
            "raw_retention": "sanitized-receipts",
            "canonical_language": "en",
        },
        "language": {
            "client_language": "en",
            "source_languages": ["en"],
            "transcript_quality": "reliable",
            "meeting_evidence_mode": "transcript-plus-confirmation",
            "preserve_material_originals": True,
            "client_style": "professional",
        },
        "sources": {
            "drive": {"folder_ids": [], "classes": {}},
            "povio_dashboard": {"project_id": None, "access": "read-only", "capabilities": ["hours", "allocation", "absences", "invoices", "health"]},
            "tracker": {"system": None, "project_ids": [], "canonical_for": ["work-status", "owner", "priority"]},
            "github": {"repositories": [], "default_branches": {}},
            "slack": {"client_channels": [], "internal_channels": [], "support_channels": []},
            "gmail": {"client_domains": [], "contacts": []},
            "calendar": {"calendar_ids": [], "recurring_meetings": []},
        },
        "authority": {
            "contracted_scope": None,
            "approved_estimate": None,
            "budget_baseline": None,
            "actual_hours": None,
            "planned_allocation": None,
            "invoice_state": None,
            "work_status": None,
            "implementation": None,
            "deployment": None,
            "requirements": None,
            "milestone_dates": None,
            "client_commitments": None,
            "conflicts": "preserve-and-escalate",
        },
        "stakeholders": {"records": [], "approvers": {"scope": [], "budget": [], "milestone": [], "release": [], "client_communication": []}},
        "approvals": {
            "preset": "conservative",
            "obsidian_internal_write": "allow-with-audit",
            "external_drafts": "allow",
            "tracker_write": "confirm",
            "email_send": "confirm",
            "slack_send": "confirm",
            "calendar_write": "confirm",
            "baseline_change": "named-approver",
            "finance_write": "deny",
            "merge_or_deploy": "deny",
        },
        "cadence": {
            "daily_brief": {"enabled": True, "time": "08:30", "changed_only": True},
            "weekly_review": {"enabled": True, "day": "friday", "time": "14:00"},
            "monthly_portfolio": {"enabled": True},
            "workflow_improvement": {"enabled": False, "frequency": "weekly", "time": "17:30", "changed_only": True, "max_specialists": 2},
            "workflow_research": {"enabled": False, "frequency": "weekly", "time": "16:30", "changed_only": True, "max_specialists": 2, "repository_access": "inspect-only", "themes": []},
            "meeting_followup": "event-driven",
            "quiet_hours": ["18:00", "08:00"],
        },
        "tolerances": {
            "schedule_yellow_days": 3,
            "schedule_red_days": 7,
            "budget_yellow_percent": 10,
            "budget_red_percent": 20,
            "critical_blocker_yellow_business_days": 2,
            "client_response_yellow_business_days": 2,
            "pr_review_yellow_hours": 48,
            "volatile_source_max_age_days": 7,
            "missing_required_baseline": "gray",
        },
        "onboarding": {"status": "draft", "last_completed_step": "identity", "accepted_gaps": [], "discovered_at": now, "completed_at": None},
    }


def ask(prompt: str, recommendation: str, choices: set[str] | None = None) -> str:
    suffix = f" [{recommendation}]" if recommendation else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip() or recommendation
        if choices is None or value in choices:
            return value
        print(f"Choose one of: {', '.join(sorted(choices))}")


def csv_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def ask_nonnegative_int(prompt: str, recommendation: int) -> int:
    while True:
        value = ask(prompt, str(recommendation))
        try:
            parsed = int(value)
        except ValueError:
            print("Enter a whole number.")
            continue
        if parsed < 0:
            print("Enter zero or a positive whole number.")
            continue
        return parsed


def interactive_profile() -> tuple[dict[str, Any], Path | None, str]:
    print("Project Operations onboarding — Discover → Recommend → Confirm → Generate → Validate")
    print("Onboarding is read-only until the final confirmed scaffold step. Never enter credentials.")
    name = ask("Project name", "New Project")
    key = ask("Project key", slugify(name))
    client = ask("Client or sponsoring organization", name)
    profile = defaults(name, key, client)

    mode = ask("Mode (new/existing/clone/reconfigure)", "new", {"new", "existing", "clone", "reconfigure"})
    vault_path = None
    if mode != "clone":
        while vault_path is None:
            vault_text = ask("Obsidian vault path", "")
            if vault_text:
                vault_path = Path(vault_text)
            else:
                print("A vault path is required. No files are written before the confirmed scaffold step.")
    stage = ask("Stage", "active-delivery", {"discovery", "active-delivery", "stabilization", "maintenance", "paused", "closed"})
    commercial = ask("Commercial model", "time-and-materials", {"fixed-price", "time-and-materials", "retainer", "mixed", "internal"})
    primary, overlays = recommended_archetype(stage, commercial)
    print(f"Recommendation: {primary}" + (f" with {', '.join(overlays)}" if overlays else ""))
    primary = ask("Primary archetype", primary, {"support-maintenance", "product-launch", "discovery-validation", "fixed-scope-delivery", "retainer-capacity", "internal-initiative"})

    client_language = ask("Client language", "en")
    transcript = ask("Transcript quality", "reliable", {"reliable", "partial", "unreliable", "unavailable"})
    if client_language == "sl-SI" and transcript in {"partial", "unreliable", "unavailable"}:
        meeting_mode = "structured-notes-plus-confirmation"
        client_style = "formal-vikanje"
        print("Recommendation: Slovenian structured notes, a post-meeting debrief, and written confirmation using formal vikanje.")
    else:
        meeting_mode = "transcript-plus-confirmation" if transcript == "reliable" else "structured-notes-plus-confirmation"
        client_style = "professional"

    profile["project"]["stage"] = stage
    profile["project"]["archetypes"] = {"primary": primary, "overlays": [item for item in overlays if item != primary]}
    profile["vault"]["adoption_mode"] = mode
    profile["vault"]["path"] = str(vault_path) if vault_path else None
    profile["language"].update({
        "client_language": client_language,
        "source_languages": list(dict.fromkeys([client_language, "en"])),
        "transcript_quality": transcript,
        "meeting_evidence_mode": meeting_mode,
        "client_style": client_style,
    })

    print("Configure stable identifiers only; leave a value empty to mark it as an accepted onboarding gap.")
    objective = ask("Primary project objective", "Deliver the next accepted outcome")
    next_milestone = ask("Next milestone", "")
    drive = ask("Drive project folder ID", "")
    contract_file = ask("Executed contract/SOW file ID", "")
    estimate_file = ask("Approved estimate file ID", "")
    budget_file = ask("Approved budget Sheet file ID", "")
    dashboard = ask("Povio Dashboard project ID", "")
    tracker_system = ask("Tracker system", "povio-boards")
    tracker_id = ask("Tracker project/team ID", "")
    github = ask("GitHub repository (owner/repo)", "")
    github_branch = ask("GitHub default branch", "dev") if github else ""
    slack_client = csv_values(ask("Client Slack channel IDs (comma-separated)", ""))
    slack_internal = csv_values(ask("Internal Slack channel IDs (comma-separated)", ""))
    gmail_domains = csv_values(ask("Client email domains (comma-separated)", ""))
    calendar_ids = csv_values(ask("Calendar IDs (comma-separated)", "primary"))
    approver = ask("Default scope/budget/milestone approver", "")
    approval_preset = ask("Approval preset", "conservative", {"conservative", "assisted"})
    use_tolerances = ask("Use recommended RAG tolerances? (yes/no)", "yes", {"yes", "no"})

    profile["project"]["objectives"] = [objective] if objective else []
    profile["project"]["next_milestone"] = next_milestone or None
    profile["sources"]["drive"]["folder_ids"] = [drive] if drive else []
    profile["sources"]["drive"]["classes"] = {
        key: value
        for key, value in {
            "contract": {"file_id": contract_file, "approval_status": "executed"} if contract_file else None,
            "estimate": {"file_id": estimate_file, "approval_status": "approved"} if estimate_file else None,
            "budget": {"file_id": budget_file, "approval_status": "approved"} if budget_file else None,
        }.items()
        if value is not None
    }
    profile["sources"]["povio_dashboard"]["project_id"] = dashboard or None
    profile["sources"]["tracker"].update({"system": tracker_system or None, "project_ids": [tracker_id] if tracker_id else []})
    profile["sources"]["github"]["repositories"] = [github] if github else []
    profile["sources"]["github"]["default_branches"] = {github: github_branch} if github else {}
    profile["sources"]["slack"]["client_channels"] = slack_client
    profile["sources"]["slack"]["internal_channels"] = slack_internal
    profile["sources"]["gmail"]["client_domains"] = gmail_domains
    profile["sources"]["calendar"]["calendar_ids"] = calendar_ids
    if approver:
        for field in ("scope", "budget", "milestone"):
            profile["stakeholders"]["approvers"][field] = [approver]
    profile["approvals"]["preset"] = approval_preset
    if approval_preset == "assisted":
        profile["approvals"]["tracker_write"] = "confirm"
        profile["approvals"]["calendar_write"] = "confirm"
    if use_tolerances == "no":
        profile["tolerances"]["schedule_yellow_days"] = ask_nonnegative_int("Schedule Yellow threshold in days", 3)
        profile["tolerances"]["schedule_red_days"] = ask_nonnegative_int("Schedule Red threshold in days", 7)
        profile["tolerances"]["budget_yellow_percent"] = ask_nonnegative_int("Budget Yellow threshold in percent", 10)
        profile["tolerances"]["budget_red_percent"] = ask_nonnegative_int("Budget Red threshold in percent", 20)

    authority_defaults = {
        "contracted_scope": "drive.contract" if contract_file else None,
        "approved_estimate": "drive.estimate" if estimate_file else None,
        "budget_baseline": "drive.budget" if budget_file else None,
        "actual_hours": "povio_dashboard.hours" if dashboard else None,
        "planned_allocation": None,
        "invoice_state": "povio_dashboard.invoices" if dashboard else None,
        "work_status": "tracker" if tracker_id else None,
        "implementation": "github" if github else None,
        "deployment": None,
        "requirements": None,
        "milestone_dates": None,
        "client_commitments": "confirmed-client-communication",
    }
    profile["authority"].update(authority_defaults)
    for field, value in authority_defaults.items():
        if value is None:
            profile["onboarding"]["accepted_gaps"].append(f"authority.{field}")

    profile["onboarding"]["last_completed_step"] = "preview"
    profile["onboarding"]["status"] = "ready-to-apply"
    return profile, vault_path, mode


def summary(profile: dict[str, Any]) -> None:
    print("\nRecommendation preview")
    print(json.dumps({
        "project": profile["project"],
        "vault": profile["vault"],
        "language": profile["language"],
        "authority": profile["authority"],
        "approvals": profile["approvals"],
        "cadence": profile["cadence"],
        "accepted_gaps": profile["onboarding"]["accepted_gaps"],
        "external_operations": [],
    }, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", type=Path, help="JSON overrides for non-interactive or resumed onboarding")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--vault", type=Path)
    parser.add_argument("--apply", action="store_true", help="Apply the generated scaffold after a successful dry run")
    args = parser.parse_args()

    if args.answers:
        override = json.loads(args.answers.read_text(encoding="utf-8"))
        project_override = override.get("project", {})
        name = project_override.get("name", "New Project")
        key = project_override.get("key", slugify(name))
        client = project_override.get("client", name)
        profile = deep_merge(defaults(name, key, client), override)
        vault_path = args.vault or (Path(profile["vault"]["path"]) if profile["vault"].get("path") else None)
    elif args.non_interactive:
        print("ERROR: --non-interactive requires --answers")
        return 1
    else:
        profile, vault_path, _mode = interactive_profile()

    errors, warnings = validate_profile(profile, allow_draft=False)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    summary(profile)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PROFILE: {args.output}")

    if vault_path:
        command = [sys.executable, str(SCRIPT_ROOT / "bootstrap_project.py"), "--profile", str(args.output), "--vault", str(vault_path), "--dry-run"]
        dry_run = subprocess.run(command, check=False)
        if dry_run.returncode:
            return dry_run.returncode
        apply_now = args.apply
        if not args.non_interactive and not args.apply:
            apply_now = ask("Apply this exact scaffold? (yes/no)", "no", {"yes", "no"}) == "yes"
        if apply_now:
            command.remove("--dry-run")
            return subprocess.run(command, check=False).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
