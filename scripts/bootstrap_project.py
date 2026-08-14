#!/usr/bin/env python3
"""Safely scaffold a Project Operations Obsidian vault from project-ops.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from validate_project_profile import load_profile, validate_profile


PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "templates"
BASE_ROOT = PLUGIN_ROOT / "assets" / "bases"

PROTECTED_EXISTING = {
    "AGENTS.md",
    "inbox.md",
    "log.md",
    "Start Here.md",
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "None"
    return str(value)


def substitutions(profile: dict[str, Any]) -> dict[str, str]:
    today = date.today()
    project = profile["project"]
    vault = profile["vault"]
    language = profile["language"]
    approvals = profile["approvals"]
    archetypes = project["archetypes"]
    return {
        "project_key": _text(project["key"]),
        "project_name": _text(project["name"]),
        "client": _text(project["client"]),
        "stage": _text(project["stage"]),
        "sensitivity": _text(project["sensitivity"]),
        "primary_archetype": _text(archetypes["primary"]),
        "archetype_overlays": _text(archetypes.get("overlays", [])),
        "working_language": _text(vault.get("canonical_language", "en")),
        "client_language": _text(language["client_language"]),
        "client_style": _text(language.get("client_style", "professional")),
        "transcript_quality": _text(language["transcript_quality"]),
        "meeting_evidence_mode": _text(language["meeting_evidence_mode"]),
        "approval_preset": _text(approvals["preset"]),
        "tracker_write": _text(approvals["tracker_write"]),
        "email_send": _text(approvals["email_send"]),
        "slack_send": _text(approvals["slack_send"]),
        "calendar_write": _text(approvals["calendar_write"]),
        "baseline_change": _text(approvals["baseline_change"]),
        "finance_write": _text(approvals["finance_write"]),
        "merge_or_deploy": _text(approvals["merge_or_deploy"]),
        "date": today.isoformat(),
        "review_after": (today + timedelta(days=7)).isoformat(),
        "stable_review_after": (today + timedelta(days=60)).isoformat(),
    }


def render(template_path: Path, values: dict[str, str]) -> str:
    content = template_path.read_text(encoding="utf-8")
    for key, value in values.items():
        content = content.replace("{{" + key + "}}", value)
    unresolved = sorted({part.split("}}", 1)[0] for part in content.split("{{")[1:] if "}}" in part})
    if unresolved:
        raise ValueError(f"unresolved placeholders in {template_path.name}: {', '.join(unresolved)}")
    return content


def planned_files(profile: dict[str, Any], vault: Path) -> list[tuple[Path | None, Path, str | None]]:
    values = substitutions(profile)
    values["vault_path"] = str(vault.resolve())
    values["github_repositories"] = _text(
        profile.get("sources", {}).get("github", {}).get("repositories", [])
    )
    key = values["project_key"]
    name = values["project_name"]
    files: list[tuple[Path | None, Path, str | None]] = []

    template_map = {
        "AGENTS.md": "AGENTS.md",
        "Start Here.md": "Start Here.md",
        f"wiki/{key}/index.md": "index.md",
        f"wiki/{key}/current.md": "current.md",
        f"wiki/{key}/source-map.md": "source-map.md",
        f"wiki/{key}/pm/project-profile.md": "project-profile.md",
        f"wiki/{key}/pm/index.md": "pm-index.md",
        f"wiki/{key}/pm/charter.md": "charter.md",
        f"wiki/{key}/pm/scope-baseline.md": "scope-baseline.md",
        f"wiki/{key}/pm/approval-policy.md": "approval-policy.md",
        f"wiki/{key}/pm/communication-plan.md": "communication-plan.md",
        f"wiki/{key}/pm/glossary.md": "glossary.md",
        f"wiki/{key}/pm/portfolio-summary.md": "portfolio-summary.md",
        f"wiki/{key}/pm/repository-agent-adoption-plan.md": "repository-agent-adoption-plan.md",
        f"wiki/{key}/decisions/{values['date']}-adopt-project-operations.md": "adopt-project-operations-decision.md",
        f"dashboards/{name} PM.md": "dashboard.md",
        "templates/project-profile.md": "project-profile.md",
        "templates/milestone.md": "milestone.md",
        "templates/commitment.md": "commitment.md",
        "templates/raid-item.md": "raid-item.md",
        "templates/change-request.md": "change-request.md",
        "templates/stakeholder.md": "stakeholder.md",
        "templates/budget-snapshot.md": "budget-snapshot.md",
        "templates/health-snapshot.md": "health-snapshot.md",
        "templates/meeting-note.md": "meeting-note.md",
        "templates/source-receipt.md": "source-receipt.md",
        "templates/decision.md": "decision.md",
        "templates/open-question.md": "open-question.md",
        "templates/promotion-candidate.md": "promotion-candidate.md",
    }
    for destination, template in template_map.items():
        files.append((TEMPLATE_ROOT / template, vault / destination, render(TEMPLATE_ROOT / template, values)))

    if profile["vault"]["adoption_mode"] in {"existing", "reconfigure"}:
        destination = f"wiki/{key}/pm/adoption-navigation-plan.md"
        template = "adoption-link-plan.md"
        files.append((TEMPLATE_ROOT / template, vault / destination, render(TEMPLATE_ROOT / template, values)))

    for source in sorted(BASE_ROOT.glob("*.base")):
        destination = vault / "dashboards" / f"{name} {source.name}"
        files.append((source, destination, render(source, values)))

    profile_text = json.dumps(profile, ensure_ascii=False, indent=2) + "\n"
    files.append((None, vault / "project-ops.json", profile_text))
    digest = hashlib.sha256(profile_text.encode("utf-8")).hexdigest()[:12]
    receipt = (
        "---\n"
        "type: source\n"
        f"project: {key}\n"
        "source_system: pm-os\n"
        f"source_id: onboarding-{digest}\n"
        f"captured: {values['date']}\n"
        f"sensitivity: {values['sensitivity']}\n"
        "evidence_grade: A\n"
        "immutable: true\n"
        "---\n\n"
        f"# {name} Project Operations onboarding\n\n"
        "## Accepted profile\n\n"
        "```json\n"
        f"{profile_text}```\n\n"
        "## External effects\n\n"
        "The onboarding scaffold itself performs no tracker, GitHub, Drive, Dashboard, Slack, Gmail, Calendar, finance, deployment, or production mutation.\n"
    )
    files.append((None, vault / f"raw/{key}/pm-os/onboarding/{values['date']}-onboarding-{digest}.md", receipt))
    files.append((None, vault / "inbox.md", "# Inbox\n"))
    files.append((None, vault / "log.md", "# Project Operations log\n"))
    return files


def required_directories(profile: dict[str, Any], vault: Path) -> list[Path]:
    key = profile["project"]["key"]
    relative = [
        "archive",
        "assets",
        "daily",
        "dashboards",
        "raw",
        f"raw/{key}",
        f"raw/{key}/meetings",
        f"raw/{key}/pm-os/onboarding",
        f"raw/{key}/pm-os/runs",
        f"raw/{key}/pm-os/weekly",
        "templates",
        "wiki",
        f"wiki/{key}",
        f"wiki/{key}/decisions",
        f"wiki/{key}/human-input",
        f"wiki/{key}/meetings",
        f"wiki/{key}/pm",
        f"wiki/{key}/pm/records/milestones",
        f"wiki/{key}/pm/records/commitments",
        f"wiki/{key}/pm/records/raid",
        f"wiki/{key}/pm/records/changes",
        f"wiki/{key}/pm/records/stakeholders",
        f"wiki/{key}/pm/records/budgets",
        f"wiki/{key}/pm/records/health",
        f"wiki/{key}/pm/records/reports",
        f"wiki/{key}/pm/records/improvements",
    ]
    return [vault / item for item in relative]


def bootstrap(profile: dict[str, Any], vault: Path, dry_run: bool, update_profile: bool) -> dict[str, list[str]]:
    mode = profile["vault"]["adoption_mode"]
    existing = vault.exists() and any(vault.iterdir())
    if mode == "new" and existing:
        existing_profile = vault / "project-ops.json"
        if not existing_profile.exists():
            raise ValueError("vault is not empty but adoption_mode is new")
        try:
            existing_key = json.loads(existing_profile.read_text(encoding="utf-8"))["project"]["key"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("existing project-ops.json cannot be identified safely") from exc
        if existing_key != profile["project"]["key"]:
            raise ValueError("existing vault belongs to a different project")
    if mode in {"existing", "reconfigure"} and not existing:
        raise ValueError(f"adoption_mode {mode} requires an existing non-empty vault")

    if existing:
        wiki = vault / "wiki"
        other_projects = []
        if wiki.exists():
            for child in wiki.iterdir():
                if child.is_dir() and child.name != profile["project"]["key"] and (child / "index.md").exists():
                    other_projects.append(child.name)
        if other_projects:
            raise ValueError(f"one-vault-per-project violation; found: {', '.join(sorted(other_projects))}")

    result: dict[str, list[str]] = {"create": [], "update": [], "unchanged": [], "skip": [], "directories": []}
    for directory in required_directories(profile, vault):
        if not directory.exists():
            result["directories"].append(str(directory))
            if not dry_run:
                directory.mkdir(parents=True, exist_ok=True)

    for _source, destination, content in planned_files(profile, vault):
        relative = destination.relative_to(vault).as_posix()
        if destination.exists():
            current = destination.read_text(encoding="utf-8")
            if current == content:
                result["unchanged"].append(relative)
                continue
            if relative == "project-ops.json" and update_profile:
                stamp = date.today().isoformat()
                receipt = vault / f"raw/{profile['project']['key']}/pm-os/onboarding/{stamp}-project-profile-before-update.json"
                result["update"].append(relative)
                if not dry_run:
                    receipt.parent.mkdir(parents=True, exist_ok=True)
                    if not receipt.exists():
                        shutil.copyfile(destination, receipt)
                    destination.write_text(content, encoding="utf-8")
                continue
            result["skip"].append(relative)
            continue

        result["create"].append(relative)
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    return result


def print_result(result: dict[str, list[str]], dry_run: bool) -> None:
    print("DRY RUN" if dry_run else "APPLIED")
    for category in ("directories", "create", "update", "unchanged", "skip"):
        print(f"{category.upper()} ({len(result[category])})")
        for value in result[category]:
            print(f"  {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-draft", action="store_true")
    parser.add_argument("--update-profile", action="store_true", help="Version the old project-ops.json and replace it")
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
        errors, warnings = validate_profile(profile, allow_draft=args.allow_draft)
        for warning in warnings:
            print(f"WARNING: {warning}")
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        result = bootstrap(profile, args.vault.resolve(), args.dry_run, args.update_profile)
        print_result(result, args.dry_run)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
