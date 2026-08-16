#!/usr/bin/env python3
"""Deterministic smoke tests for the Project Operations plugin."""

from __future__ import annotations

import copy
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
from validate_local_execution_preflight import validate_packet
from validate_research_packet import validate_packet as validate_research_packet


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


def assert_memory_lifecycle_contract() -> None:
    lifecycle = (ROOT / "references" / "project-memory-lifecycle.md").read_text(encoding="utf-8")
    memory = (ROOT / "skills" / "project-ops-memory" / "SKILL.md").read_text(encoding="utf-8")
    agents = (ROOT / "assets" / "templates" / "AGENTS.md").read_text(encoding="utf-8")
    for term in ("Orient", "Close", "750", "2,500"):
        if term.casefold() not in lifecycle.casefold():
            raise AssertionError(f"memory lifecycle contract is missing {term}")
    if "project-memory-lifecycle.md" not in memory:
        raise AssertionError("memory skill does not load the lifecycle contract")
    if "at close" not in agents.casefold() or "if nothing durable changed, write nothing" not in agents.casefold():
        raise AssertionError("generated repository adapter lacks a bounded close contract")


def assert_researcher_contract() -> None:
    valid = load_fixture("valid-research-packet.json")
    errors = validate_research_packet(valid)
    if errors:
        raise AssertionError(f"valid Researcher packet failed: {errors}")
    run(str(SCRIPTS / "validate_research_packet.py"), str(FIXTURES / "valid-research-packet.json"))

    adversaries: list[tuple[str, dict[str, object], str]] = []
    packet = copy.deepcopy(valid)
    packet["scope"]["repository_access"] = "clone"  # type: ignore[index]
    adversaries.append(("repository execution boundary", packet, "must be inspect-only"))
    packet = copy.deepcopy(valid)
    packet["sources"].append(  # type: ignore[union-attr]
        {
            "id": "S3",
            "kind": "social-evidence",
            "title": "Uncorroborated social claim",
            "url": "https://social.example/post/1",
            "publisher": "Unknown promoter",
            "retrieved": "2026-08-16",
            "reputation_basis": "Popularity only",
            "primary": False,
            "claim_refs": ["F1"],
            "social": True,
            "corroborated_by": [],
        }
    )
    adversaries.append(("social evidence", packet, "requires non-social corroboration"))
    packet = copy.deepcopy(valid)
    packet["findings"][0]["score"]["total"] = 91  # type: ignore[index]
    adversaries.append(("score drift", packet, "must equal deterministic score"))
    packet = copy.deepcopy(valid)
    packet["handoff"]["implementation_authorized"] = True  # type: ignore[index]
    adversaries.append(("implementation authority", packet, "must be false"))
    packet = copy.deepcopy(valid)
    packet["repositories"][0]["inspection_only"] = False  # type: ignore[index]
    adversaries.append(("repository inspection", packet, "must be true"))
    packet = copy.deepcopy(valid)
    packet["recommendations"][0]["lane"] = "addition"  # type: ignore[index]
    packet["recommendations"][0]["repair_gate"] = "deferred"  # type: ignore[index]
    adversaries.append(("repair-first order", packet, "cannot precede disposition"))
    packet = copy.deepcopy(valid)
    del packet["contract"]["source_commit"]  # type: ignore[index]
    adversaries.append(("contract identity", packet, "contract.source_commit"))
    packet = copy.deepcopy(valid)
    del packet["sources"][0]["publication_date"]  # type: ignore[index]
    adversaries.append(("source date", packet, "publication_date"))
    packet = copy.deepcopy(valid)
    del packet["sources"][0]["limitations"]  # type: ignore[index]
    adversaries.append(("source limitations", packet, "limitations"))
    packet = copy.deepcopy(valid)
    del packet["sources"][0]["confidence_note"]  # type: ignore[index]
    adversaries.append(("source confidence", packet, "confidence_note"))
    packet = copy.deepcopy(valid)
    packet["findings"][0]["applicability"] = [  # type: ignore[index]
        item
        for item in packet["findings"][0]["applicability"]  # type: ignore[index]
        if item["target"] != "project-beta"
    ]
    adversaries.append(("complete applicability", packet, "missing: project-beta"))
    packet = copy.deepcopy(valid)
    packet["coverage"]["task_history"]["complete"] = False  # type: ignore[index]
    adversaries.append(("false full coverage", packet, "full status requires complete true"))
    for label, packet, expected in adversaries:
        errors = validate_research_packet(packet)
        if not any(expected in error for error in errors):
            raise AssertionError(f"Researcher {label} adversary was accepted: {errors}")

    skill = (ROOT / "skills" / "project-ops-researcher" / "SKILL.md").read_text(encoding="utf-8")
    manager = (ROOT / "skills" / "project-ops-manager" / "SKILL.md").read_text(encoding="utf-8")
    upgrader = (ROOT / "skills" / "project-ops-upgrader" / "SKILL.md").read_text(encoding="utf-8")
    architecture = (ROOT / "references" / "architecture.md").read_text(encoding="utf-8")
    for term in ("repair-existing", "inspect-only", "project-ops-upgrader", "validate_research_packet.py"):
        if term not in skill:
            raise AssertionError(f"Researcher skill is missing required contract term: {term}")
    if "project-ops-researcher" not in manager:
        raise AssertionError("Chief of Staff does not route external discovery to Researcher")
    if "research-handoff.md" not in upgrader:
        raise AssertionError("Upgrader does not load the Researcher handoff contract")
    for term in ("Researcher", "core-agent triad", "Research loop"):
        if term.casefold() not in architecture.casefold():
            raise AssertionError(f"architecture is missing Researcher term: {term}")


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
    if validate_manifest(valid, {"project-content-impact"}):
        raise AssertionError("valid adapter-nominated extension gate was rejected")
    if not validate_manifest(legacy, {"project-content-impact"}):
        raise AssertionError("missing adapter-nominated extension gate was accepted")

    duplicate_extension = copy.deepcopy(valid)
    duplicate_extension["extension_gates"].append(
        copy.deepcopy(duplicate_extension["extension_gates"][0])
    )
    if not validate_manifest(duplicate_extension, {"project-content-impact"}):
        raise AssertionError("duplicate extension gate was accepted")

    invalid_extension = copy.deepcopy(valid)
    invalid_extension["extension_gates"][0]["classification"] = "optional"
    if not validate_manifest(invalid_extension, {"project-content-impact"}):
        raise AssertionError("invalid extension classification was accepted")

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


def assert_local_execution_safety() -> None:
    valid_fixtures = (
        "valid-local-execution-preflight.json",
        "valid-local-execution-interrupted.json",
    )
    for fixture in valid_fixtures:
        errors = validate_packet(load_fixture(fixture))
        if errors:
            raise AssertionError(f"valid local-execution fixture failed: {fixture}: {errors}")
        run(str(SCRIPTS / "validate_local_execution_preflight.py"), str(FIXTURES / fixture))

    invalid_fixtures = {
        "invalid-local-execution-root-absent.json": (
            "canonical root does not exist",
            "must report dependent coverage as Gray",
        ),
        "invalid-local-execution-root-mismatch.json": ("does not match",),
        "invalid-local-execution-dirty.json": ("must be clean",),
        "invalid-local-execution-shared-writer.json": (
            "exactly one",
            "must be isolated-worktree",
            "must not be shared",
        ),
        "invalid-local-execution-ambiguous-lock.json": ("live or ambiguous lock",),
        "invalid-local-execution-live-lock.json": ("live or ambiguous lock",),
        "invalid-local-execution-unrelated-branch.json": ("related to the approved change",),
        "invalid-local-execution-dependency-state.json": (
            "must have status pass",
            "dependency state must be consistent",
            "must not contain a partial mutation",
        ),
        "invalid-local-execution-missing-prerequisite.json": ("must have status pass",),
        "invalid-local-execution-surviving-process.json": (
            "survived the timeout boundary",
            "must not remain running",
            "integrity check must pass",
        ),
        "invalid-local-execution-incomplete-resume.json": ("resume_packet missing field",),
        "invalid-local-execution-check-omission.json": (
            "preflight_checks omits nominated check: adapter-prerequisite-check",
        ),
        "invalid-local-execution-resume-process-omission.json": (
            "resume_packet.owned_processes omits ledger process: worker-1",
        ),
        "invalid-local-execution-optional-fail.json": ("must have status pass",),
        "invalid-local-execution-optional-missing.json": ("must have status pass",),
        "invalid-local-execution-optional-unverified.json": ("must have status pass",),
        "invalid-local-execution-empty-blocker.json": (
            "resume_packet.blocker must be a non-empty string",
        ),
    }
    for fixture, expected_errors in invalid_fixtures.items():
        errors = validate_packet(load_fixture(fixture))
        if not errors or not all(
            any(expected_error in error for error in errors) for expected_error in expected_errors
        ):
            raise AssertionError(
                f"invalid local-execution fixture did not fail as expected: "
                f"{fixture}: {errors}"
            )
        run(
            str(SCRIPTS / "validate_local_execution_preflight.py"),
            str(FIXTURES / fixture),
            expect=1,
        )

    base = load_fixture("valid-local-execution-preflight.json")

    for label, nominated, observed in (
        ("POSIX", "/project/root", "/project/./root/"),
        ("Windows", r"C:\Project\Root", "c:/project/./root/"),
        ("UNC", r"\\server\share\root", "//SERVER/share/./root/"),
    ):
        packet = copy.deepcopy(base)
        packet["canonical_root"] = {
            "nominated": nominated,
            "observed": observed,
            "exists": True,
        }
        errors = validate_packet(packet)
        if errors:
            raise AssertionError(f"valid absolute {label} roots failed lexical comparison: {errors}")

    for label, nominated, observed, expected_error in (
        ("relative", "project/root", "project/root", "syntactically absolute"),
        ("drive-only", "C:", "C:", "drive-relative"),
        ("drive-relative", "C:project", "C:project", "drive-relative"),
        ("rooted-current-drive", r"\project\root", r"\project\root", "syntactically absolute"),
        ("Windows parent traversal", r"C:\safe\..\root", r"C:\root", "parent-traversal"),
        ("POSIX parent traversal", "/safe/../root", "/root", "parent-traversal"),
        ("cross-platform alias", "/C:/root", r"C:\root", "does not match"),
        ("device namespace", r"\\.\C:\repo", r"\\.\C:\repo", "device or extended-length"),
        ("extended-length namespace", r"\\?\C:\repo", r"\\?\C:\repo", "device or extended-length"),
        (
            "extended-length UNC namespace",
            r"\\?\UNC\server\share\repo",
            r"\\?\UNC\server\share\repo",
            "device or extended-length",
        ),
        ("alternate data stream", r"C:\repo:stream", r"C:\repo:stream", "alternate-data-stream"),
    ):
        packet = copy.deepcopy(base)
        packet["canonical_root"] = {
            "nominated": nominated,
            "observed": observed,
            "exists": True,
        }
        packet["coverage"] = {"status": "gray", "reasons": [f"invalid {label} root"]}
        errors = validate_packet(packet)
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"unsafe {label} roots were not rejected as expected: {errors}")

    check_adversaries = []
    packet = copy.deepcopy(base)
    packet["preflight_checks"].append(
        {"id": "undeclared-check", "category": "prerequisite", "required": True, "status": "pass"}
    )
    check_adversaries.append(("extra result", packet, "contains undeclared check"))
    packet = copy.deepcopy(base)
    packet["preflight_checks"][0]["category"] = "prerequisite"
    check_adversaries.append(("category change", packet, "category does not match nomination"))
    packet = copy.deepcopy(base)
    packet["preflight_checks"].append(copy.deepcopy(packet["preflight_checks"][0]))
    check_adversaries.append(("duplicate result", packet, ".id must be unique"))
    packet = copy.deepcopy(base)
    packet["nominated_checks"].append(copy.deepcopy(packet["nominated_checks"][0]))
    check_adversaries.append(("duplicate nomination", packet, ".id must be unique"))
    packet = copy.deepcopy(base)
    packet["preflight_checks"][0]["required"] = False
    check_adversaries.append(("required-flag change", packet, "required flag does not match nomination"))
    for label, packet, expected_error in check_adversaries:
        errors = validate_packet(packet)
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"{label} did not fail exact nominated-check coverage: {errors}")

    packet = copy.deepcopy(load_fixture("valid-local-execution-interrupted.json"))
    packet["interruption"]["resume_packet"]["owned_processes"].append("not-in-ledger")
    errors = validate_packet(packet)
    if not any("contains non-ledger process" in error for error in errors):
        raise AssertionError(f"resume packet accepted a non-ledger process: {errors}")

    reference_path = ROOT / "references" / "local-execution-safety.md"
    reference = reference_path.read_text(encoding="utf-8")
    for forbidden in ("Sloski", "PNPM", "Docker", "MinIO", "sloski-drop"):
        if forbidden.casefold() in reference.casefold():
            raise AssertionError(f"generic local-execution contract contains project-specific term: {forbidden}")
    for skill_name in ("project-ops-delivery", "project-ops-upgrader"):
        skill = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        if "../../references/local-execution-safety.md" not in skill:
            raise AssertionError(f"{skill_name} does not load the local-execution safety contract")
        if "read" not in skill.casefold() or "apply" not in skill.casefold():
            raise AssertionError(f"{skill_name} does not explicitly read and apply the safety contract")

    adapter = (ROOT / "references" / "sloski-adapter.md").read_text(encoding="utf-8")
    if r"C:\Dev\sloski-drop" not in adapter:
        raise AssertionError("Sloski adapter does not preserve the current canonical repository")
    if r"C:\Users\david\OneDrive\Documents\GitHub\sloski-drop" in adapter:
        raise AssertionError("Sloski adapter still treats the retired checkout as canonical")


def main() -> int:
    assert_no_placeholders(ROOT)
    assert_skills()
    assert_memory_lifecycle_contract()
    assert_researcher_contract()

    run(str(SCRIPTS / "validate_project_profile.py"), str(FIXTURES / "valid-project.json"))
    run(str(SCRIPTS / "validate_project_profile.py"), str(FIXTURES / "invalid-project.json"), expect=1)
    run(str(SCRIPTS / "validate_delivery_manifest.py"), str(FIXTURES / "valid-manifest.json"))
    run(
        str(SCRIPTS / "validate_delivery_manifest.py"),
        str(FIXTURES / "valid-manifest.json"),
        "--required-extension", "project-content-impact",
    )
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
    assert_local_execution_safety()

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
            ".obsidian/graph.json",
            "AGENTS.md",
            "project-ops.json",
            "wiki/test-project/current.md",
            "wiki/test-project/pm/project-profile.md",
            "wiki/test-project/pm/repository-agent-adoption-plan.md",
            "wiki/test-project/decisions",
            "wiki/test-project/pm/records/health",
            "dashboards/Test Project PM.md",
            "dashboards/Test Project Health.base",
            "templates/meeting-note.md",
            "templates/promotion-candidate.md",
            "templates/research-brief.md",
            "templates/repository-assessment.md",
            "templates/research-handoff.md",
            "wiki/test-project/pm/records/improvements",
            "dashboards/Test Project Improvements.base",
            "wiki/test-project/pm/records/research",
            "raw/test-project/research",
            "dashboards/Test Project Research.base",
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

        existing_profile = json.loads((FIXTURES / "valid-project.json").read_text(encoding="utf-8"))
        existing_profile["vault"]["adoption_mode"] = "existing"
        existing_profile_path = Path(temporary) / "existing-project.json"
        existing_profile_path.write_text(json.dumps(existing_profile, indent=2) + "\n", encoding="utf-8")
        existing_vault = Path(temporary) / "Existing Vault"
        existing_vault.mkdir()
        (existing_vault / "inbox.md").write_text("# Human inbox\n", encoding="utf-8")
        run(
            str(SCRIPTS / "bootstrap_project.py"),
            "--profile", str(existing_profile_path),
            "--vault", str(existing_vault),
            "--date", "2026-01-02",
        )
        existing_profile["cadence"]["daily_brief"]["time"] = "09:15"
        evolved_profile_text = json.dumps(existing_profile, indent=2) + "\n"
        existing_profile_path.write_text(json.dumps(existing_profile, separators=(",", ":")) + "\n", encoding="utf-8")
        (existing_vault / "project-ops.json").write_text(evolved_profile_text, encoding="utf-8")
        canonical = existing_vault / "wiki/test-project/current.md"
        canonical.write_text("# Human canonical current\n", encoding="utf-8")
        for command_date, dry_run in (("2026-02-03", True), ("2026-03-04", False), ("2026-04-05", True)):
            args = [
                str(SCRIPTS / "bootstrap_project.py"),
                "--profile", str(existing_profile_path),
                "--vault", str(existing_vault),
                "--date", command_date,
            ]
            if dry_run:
                args.append("--dry-run")
            rerun = run(*args)
            if "CREATE (0)" not in rerun.stdout or "UPDATE (0)" not in rerun.stdout:
                raise AssertionError(f"existing-vault onboarding is not semantically idempotent on {command_date}")
        decisions = list((existing_vault / "wiki/test-project/decisions").glob("*-adopt-project-operations.md"))
        receipts = list((existing_vault / "raw/test-project/pm-os/onboarding").glob("*-onboarding-*.md"))
        if len(decisions) != 1 or len(receipts) != 1:
            raise AssertionError("existing-vault onboarding duplicated a one-time decision or receipt")
        if (existing_vault / "inbox.md").read_text(encoding="utf-8") != "# Human inbox\n":
            raise AssertionError("existing-vault onboarding overwrote a human-owned file")
        if canonical.read_text(encoding="utf-8") != "# Human canonical current\n":
            raise AssertionError("existing-vault onboarding overwrote a canonical page")
        reconfigure_profile = copy.deepcopy(existing_profile)
        reconfigure_profile["vault"]["adoption_mode"] = "reconfigure"
        reconfigure_profile_path = Path(temporary) / "reconfigure-project.json"
        reconfigure_profile_path.write_text(json.dumps(reconfigure_profile, indent=2) + "\n", encoding="utf-8")
        reconfigure = run(
            str(SCRIPTS / "bootstrap_project.py"),
            "--profile", str(reconfigure_profile_path),
            "--vault", str(existing_vault),
            "--dry-run",
            "--date", "2026-05-06",
        )
        if "2026-05-06-adopt-project-operations.md" not in reconfigure.stdout:
            raise AssertionError("explicit reconfigure path did not remain available")

        assert_base_yaml(vault)
        run(str(SCRIPTS / "validate_project_vault.py"), str(vault), "--project-key", "test-project")
        graph = json.loads((vault / ".obsidian/graph.json").read_text(encoding="utf-8"))
        if graph.get("search") != 'path:"wiki" OR path:"dashboards" OR file:"Start Here"':
            raise AssertionError("generated Obsidian graph does not use the focused positive query")
        if graph.get("showOrphans") is not False or graph.get("scale") != 0.9:
            raise AssertionError("generated Obsidian graph focus defaults are invalid")

        index_path = vault / "wiki/test-project/index.md"
        original_index = index_path.read_text(encoding="utf-8")

        def validate_table_case(snippet: str, *, rejected: bool) -> None:
            index_path.write_text(original_index + snippet, encoding="utf-8")
            result = run(
                str(SCRIPTS / "validate_project_vault.py"),
                str(vault),
                "--project-key", "test-project",
                expect=1 if rejected else 0,
            )
            identified = "unescaped wikilink alias pipe in Markdown table" in result.stdout
            if rejected and not identified:
                raise AssertionError("vault validator did not identify the malformed table wikilink")
            if not rejected and identified:
                raise AssertionError("vault validator falsely identified a non-table wikilink")

        validate_table_case(
            "\nTask | Read\n--- | ---\nInspect | [[wiki/test-project/current|Current]]\n",
            rejected=True,
        )
        validate_table_case(
            "\n| Task | Read |\n| :--- | ---: |\n| Inspect | [[wiki/test-project/current|Current]] |\n",
            rejected=True,
        )
        validate_table_case(
            "\nTask | Read\n--- | ---\nInspect | [[wiki/test-project/current\\|Current]]\n",
            rejected=False,
        )
        validate_table_case(
            "\n```markdown\nTask | Read\n--- | ---\nInspect | [[wiki/test-project/current|Current]]\n```\n",
            rejected=False,
        )
        validate_table_case(
            "\n--- | ---\nInspect | [[wiki/test-project/current|Current]]\n",
            rejected=False,
        )
        validate_table_case(
            "\n--- | ---\n--- | ---\nInspect | [[wiki/test-project/current|Current]]\n",
            rejected=False,
        )
        index_path.write_text(original_index, encoding="utf-8")
        for path in (vault / "wiki/test-project/pm").rglob("*.md"):
            if "- [ ]" in path.read_text(encoding="utf-8"):
                raise AssertionError(f"compiled PM record contains task checkbox: {path}")
        generated_profile = json.loads((vault / "project-ops.json").read_text(encoding="utf-8"))
        if generated_profile["language"]["meeting_evidence_mode"] != "structured-notes-plus-confirmation":
            raise AssertionError("Slovenian no-transcript meeting mode was not preserved")
        improvement = generated_profile["cadence"]["workflow_improvement"]
        if improvement["max_specialists"] != 2 or not improvement["changed_only"]:
            raise AssertionError("workflow improvement cadence was not preserved")
        research = generated_profile["cadence"]["workflow_research"]
        if research["repository_access"] != "inspect-only" or research["enabled"]:
            raise AssertionError("workflow research cadence was not preserved safely")

    print("PASS: Project Operations deterministic smoke tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
