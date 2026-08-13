#!/usr/bin/env python3
"""Deterministic smoke tests for the Project Operations plugin."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from validate_delivery_manifest import (
    REVIEW_STAGES,
    effective_automatic_remediation_limit,
    effective_review_stages,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = SCRIPTS / "tests" / "fixtures"


def run(*args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run([sys.executable, *args], text=True, capture_output=True, check=False)
    if completed.returncode != expect:
        raise AssertionError(
            f"command returned {completed.returncode}, expected {expect}: {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def assert_no_placeholders(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".base", ".json", ".yaml", ".py"}:
            text = path.read_text(encoding="utf-8")
            if "[" + "TODO:" in text:
                raise AssertionError(f"TODO placeholder remains in {path}")


def assert_skills() -> None:
    for skill in (ROOT / "skills").iterdir():
        if not skill.is_dir():
            continue
        skill_file = skill / "SKILL.md"
        agent_file = skill / "agents" / "openai.yaml"
        if not skill_file.exists() or not agent_file.exists():
            raise AssertionError(f"incomplete skill: {skill.name}")
        first = skill_file.read_text(encoding="utf-8").splitlines()[:6]
        if f"name: {skill.name}" not in first:
            raise AssertionError(f"skill name mismatch: {skill.name}")
        if f"${skill.name}" not in agent_file.read_text(encoding="utf-8"):
            raise AssertionError(f"default prompt does not mention ${skill.name}")


def assert_base_yaml(vault: Path) -> None:
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None
    for path in (vault / "dashboards").glob("*.base"):
        text = path.read_text(encoding="utf-8")
        if "{{" in text or "}}" in text:
            raise AssertionError(f"unresolved template placeholder in {path}")
        if yaml is not None:
            parsed = yaml.safe_load(text)
            if not isinstance(parsed, dict) or "views" not in parsed or "filters" not in parsed:
                raise AssertionError(f"invalid Base schema in {path}")


def load_fixture(name: str) -> dict[str, object]:
    value = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"fixture root is not an object: {name}")
    return value


def assert_delivery_execution_policy() -> None:
    valid = load_fixture("valid-manifest.json")
    legacy = load_fixture("valid-manifest-without-execution-policy.json")

    if effective_automatic_remediation_limit(valid) != 1:
        raise AssertionError("manifest remediation ceiling of one was not honored")
    if effective_automatic_remediation_limit(legacy) != 2:
        raise AssertionError("legacy manifest did not retain the plugin ceiling of two")
    if effective_automatic_remediation_limit(legacy, adapter_limit=1) != 1:
        raise AssertionError("stricter adapter remediation ceiling was not honored")
    if effective_automatic_remediation_limit(valid, adapter_limit=0) != 0:
        raise AssertionError("effective remediation ceiling is not the strictest configured limit")
    if effective_review_stages(valid) != REVIEW_STAGES or effective_review_stages(legacy) != REVIEW_STAGES:
        raise AssertionError("review stages did not resolve to ordered functional QA then final assurance")

    invalid_bool = dict(valid)
    invalid_bool["execution_policy"] = {
        "max_automatic_remediations": True,
        "review_stages": list(REVIEW_STAGES),
    }
    if not validate_manifest(invalid_bool):
        raise AssertionError("boolean remediation ceiling was accepted as an integer")
    try:
        effective_automatic_remediation_limit(legacy, adapter_limit=3)
    except ValueError:
        pass
    else:
        raise AssertionError("adapter remediation ceiling above the plugin maximum was accepted")


def main() -> int:
    assert_no_placeholders(ROOT)
    assert_skills()

    run(str(SCRIPTS / "validate_project_profile.py"), str(FIXTURES / "valid-project.json"))
    run(str(SCRIPTS / "validate_project_profile.py"), str(FIXTURES / "invalid-project.json"), expect=1)
    run(str(SCRIPTS / "validate_delivery_manifest.py"), str(FIXTURES / "valid-manifest.json"))
    run(
        str(SCRIPTS / "validate_delivery_manifest.py"),
        str(FIXTURES / "valid-manifest-without-execution-policy.json"),
    )
    for invalid_manifest in (
        "invalid-manifest-remediation-over-limit.json",
        "invalid-manifest-remediation-negative.json",
        "invalid-manifest-collapsed-review-stages.json",
        "invalid-manifest-reversed-review-stages.json",
    ):
        run(
            str(SCRIPTS / "validate_delivery_manifest.py"),
            str(FIXTURES / invalid_manifest),
            expect=1,
        )
    assert_delivery_execution_policy()

    with tempfile.TemporaryDirectory(prefix="project-operations-") as temporary:
        vault = Path(temporary) / "Test Vault"
        dry = run(
            str(SCRIPTS / "bootstrap_project.py"),
            "--profile", str(FIXTURES / "valid-project.json"),
            "--vault", str(vault),
            "--dry-run",
        )
        if vault.exists():
            raise AssertionError("dry run created the vault")
        if "DRY RUN" not in dry.stdout:
            raise AssertionError("dry run did not identify itself")

        run(
            str(SCRIPTS / "bootstrap_project.py"),
            "--profile", str(FIXTURES / "valid-project.json"),
            "--vault", str(vault),
        )
        required = [
            "AGENTS.md",
            "project-ops.json",
            "wiki/test-project/current.md",
            "wiki/test-project/pm/project-profile.md",
            "wiki/test-project/pm/records/health",
            "dashboards/Test Project PM.md",
            "dashboards/Test Project Health.base",
            "templates/meeting-note.md",
            "templates/promotion-candidate.md",
            "wiki/test-project/pm/records/improvements",
            "dashboards/Test Project Improvements.base",
        ]
        for relative in required:
            if not (vault / relative).exists():
                raise AssertionError(f"missing generated artifact: {relative}")

        second = run(
            str(SCRIPTS / "bootstrap_project.py"),
            "--profile", str(FIXTURES / "valid-project.json"),
            "--vault", str(vault),
        )
        if "CREATE (0)" not in second.stdout or "UPDATE (0)" not in second.stdout:
            raise AssertionError("bootstrap rerun is not idempotent")

        assert_base_yaml(vault)
        for path in (vault / "wiki/test-project/pm").rglob("*.md"):
            if "- [ ]" in path.read_text(encoding="utf-8"):
                raise AssertionError(f"compiled PM record contains task checkbox: {path}")
        generated_profile = json.loads((vault / "project-ops.json").read_text(encoding="utf-8"))
        if generated_profile["language"]["meeting_evidence_mode"] != "structured-notes-plus-confirmation":
            raise AssertionError("Slovenian no-transcript meeting mode was not preserved")
        improvement = generated_profile["cadence"]["workflow_improvement"]
        if improvement["max_specialists"] != 2 or not improvement["changed_only"]:
            raise AssertionError("workflow improvement cadence was not preserved")

    print("PASS: Project Operations deterministic smoke tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
