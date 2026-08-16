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
from validate_operational_control_packet import validate_packet as validate_operational_control_packet
from validate_project_profile import validate_profile
from validate_research_packet import validate_packet as validate_research_packet
from summarize_task_hygiene import summarize as summarize_task_hygiene
from validate_local_execution_preflight import validate_packet as validate_local_packet
from validate_task_orchestration import validate_packet as validate_task_packet


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


def assert_operational_controls() -> None:
    valid = load_fixture("valid-operational-control-packet.json")
    errors = validate_operational_control_packet(valid)
    if errors:
        raise AssertionError(f"valid operational-control packet failed: {errors}")
    run(
        str(SCRIPTS / "validate_operational_control_packet.py"),
        str(FIXTURES / "valid-operational-control-packet.json"),
    )

    adversaries: list[tuple[str, dict[str, object], str]] = []

    packet = copy.deepcopy(valid)
    packet["retrieval"]["logical_requests"].append(  # type: ignore[index]
        copy.deepcopy(packet["retrieval"]["logical_requests"][0])  # type: ignore[index]
    )
    packet["retrieval"]["logical_requests"][1]["id"] = "REQ-2"  # type: ignore[index]
    packet["retrieval"]["logical_requests"][1]["stable_source_id"] = "source-linear-2"  # type: ignore[index]
    second_source = copy.deepcopy(packet["source_preflights"][0])  # type: ignore[index]
    second_source["id"] = "source-linear-2"
    second_source["canonical_locator"] = "workspace:test-project-2"
    packet["source_preflights"].append(second_source)  # type: ignore[index]
    adversaries.append(
        ("duplicate logical retrieval fingerprint", packet, "fingerprint duplicates")
    )

    packet = copy.deepcopy(valid)
    final_attempt = packet["retrieval"]["logical_requests"][0]["attempts"][-1]  # type: ignore[index]
    final_attempt["status"] = "failed"
    final_attempt["result_ref"] = None
    final_attempt["failure_ref"] = "evidence-final-failure"
    packet["retrieval"]["logical_requests"][0]["retained_failure_refs"].append(  # type: ignore[index]
        "evidence-final-failure"
    )
    adversaries.append(("failed checkpoint advance", packet, "cannot advance its checkpoint"))

    packet = copy.deepcopy(valid)
    packet["source_preflights"][0]["retired_locators"] = [  # type: ignore[index]
        packet["source_preflights"][0]["canonical_locator"]  # type: ignore[index]
    ]
    adversaries.append(("retired locator", packet, "points to a retired locator"))

    packet = copy.deepcopy(valid)
    packet["source_preflights"][0]["change_control"] = {  # type: ignore[index]
        "mode": "bounded-poll",
        "supported": False,
        "limitation": "Provider has no incremental API",
    }
    adversaries.append(("unsupported change control", packet, "status must be gray"))

    packet = copy.deepcopy(valid)
    packet["authority_receipts"][0]["review_after"] = "2026-08-16T09:00:00+02:00"  # type: ignore[index]
    adversaries.append(("expired authority", packet, "expired but still marked active"))

    packet = copy.deepcopy(valid)
    packet["authority_receipts"][0]["status"] = "expired"  # type: ignore[index]
    packet["health_assertions"][0].update(  # type: ignore[index]
        {
            "status": "Green",
            "required_evidence": ["human-input-2026-08-16"],
            "observed_evidence": ["human-input-2026-08-16"],
        }
    )
    adversaries.append(("expired authority green", packet, "receipt is not active"))

    packet = copy.deepcopy(valid)
    packet["health_assertions"][0]["status"] = "Green"  # type: ignore[index]
    adversaries.append(("false green", packet, "status must be Gray"))

    packet = copy.deepcopy(valid)
    packet["source_preflights"][0]["status"] = "rejected"  # type: ignore[index]
    packet["health_assertions"][0].update(  # type: ignore[index]
        {
            "status": "Green",
            "required_evidence": ["evidence-linear-result"],
            "observed_evidence": ["evidence-linear-result"],
        }
    )
    adversaries.append(("rejected source green", packet, "non-resolved sources"))

    packet = copy.deepcopy(valid)
    packet["releases"][0]["artifact"]["source_revision"] = "d" * 40  # type: ignore[index]
    adversaries.append(("release revision mismatch", packet, "must match source_revision"))

    packet = copy.deepcopy(valid)
    packet["releases"][0]["runtime"]["revision"] = None  # type: ignore[index]
    packet["releases"][0]["missing_links"] = ["runtime"]  # type: ignore[index]
    adversaries.append(("false verified release", packet, "cannot be verified"))

    packet = copy.deepcopy(valid)
    del packet["releases"][0]["artifact"]["source_revision"]  # type: ignore[index]
    del packet["releases"][0]["runtime"]["source_revision"]  # type: ignore[index]
    packet["releases"][0]["missing_links"] = ["artifact", "runtime"]  # type: ignore[index]
    adversaries.append(("missing release provenance", packet, "cannot be verified"))

    packet = copy.deepcopy(valid)
    packet["report"]["word_cap"] = 3  # type: ignore[index]
    adversaries.append(("executive word cap", packet, "exceeds report.word_cap"))

    packet = copy.deepcopy(valid)
    packet["report"]["evidence_appendix_refs"].remove("evidence-runtime-123")  # type: ignore[index]
    adversaries.append(("appendix evidence loss", packet, "missing from the evidence appendix"))

    packet = copy.deepcopy(valid)
    packet["report"]["audience"] = "client"  # type: ignore[index]
    adversaries.append(("client leakage", packet, "leaks non-client evidence"))

    for label, packet, expected in adversaries:
        errors = validate_operational_control_packet(packet)
        if not any(expected in error for error in errors):
            raise AssertionError(f"operational-control {label} adversary was accepted: {errors}")

    contract = (ROOT / "references" / "operational-controls.md").read_text(encoding="utf-8")
    for term in (
        "logical request",
        "physical attempt",
        "retired",
        "review_after",
        "source revision",
        "evidence appendix",
        "Gray",
    ):
        if term.casefold() not in contract.casefold():
            raise AssertionError(f"operational-control contract is missing {term}")
    for skill_name in (
        "project-ops-manager",
        "project-ops-health",
        "project-ops-memory",
        "project-ops-delivery",
    ):
        skill = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        if "operational-controls.md" not in skill:
            raise AssertionError(f"{skill_name} does not load operational controls")


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
        errors = validate_local_packet(load_fixture(fixture))
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
        errors = validate_local_packet(load_fixture(fixture))
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
        errors = validate_local_packet(packet)
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
        errors = validate_local_packet(packet)
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
        errors = validate_local_packet(packet)
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"{label} did not fail exact nominated-check coverage: {errors}")

    packet = copy.deepcopy(load_fixture("valid-local-execution-interrupted.json"))
    packet["interruption"]["resume_packet"]["owned_processes"].append("not-in-ledger")
    errors = validate_local_packet(packet)
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


def assert_task_orchestration() -> None:
    valid_plan = load_fixture("valid-task-plan.json")
    valid_closure = load_fixture("valid-task-closure.json")
    for fixture, packet in (
        ("valid-task-plan.json", valid_plan),
        ("valid-task-closure.json", valid_closure),
    ):
        errors = validate_task_packet(packet)
        if errors:
            raise AssertionError(f"valid task-orchestration fixture failed: {fixture}: {errors}")
        run(str(SCRIPTS / "validate_task_orchestration.py"), str(FIXTURES / fixture))

    invalid_plan_cases: list[tuple[str, dict[str, object], str]] = []
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["title"] = "<work-key> · Writer · raw prompt"
    invalid_plan_cases.append(("raw title markup", packet, "raw prompt markup"))
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["title"] = "Acme · Writer · Implement task controls"
    invalid_plan_cases.append(("redundant project prefix", packet, "redundant project prefix"))
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["human_authority"] = True
    invalid_plan_cases.append(("worker authority", packet, "human_authority must be false"))
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["decision_protocol"] = "accept_child_input"
    invalid_plan_cases.append(("child decision authority", packet, "decision_protocol must be relay_to_root"))
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["created_child_ids"] = ["recursive-worker"]
    invalid_plan_cases.append(("recursive delegation", packet, "recursive delegation is forbidden"))
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["delegation_depth"] = 2
    invalid_plan_cases.append(("delegation depth", packet, "delegation_depth must be 1"))
    packet = copy.deepcopy(valid_plan)
    packet["workers"][0]["effort"] = "xhigh"
    packet["workers"][0]["effort_rationale"] = "Review carefully."
    invalid_plan_cases.append(("unjustified xhigh", packet, "xhigh effort requires"))
    packet = copy.deepcopy(valid_plan)
    packet["max_active_workers"] = 3
    invalid_plan_cases.append(("unapproved active budget", packet, "approved_budget_extension"))
    for label, packet, expected_error in invalid_plan_cases:
        errors = validate_task_packet(packet)
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"{label} was accepted or failed unclearly: {errors}")

    invalid_closure_cases: list[tuple[str, dict[str, object], str]] = []
    packet = copy.deepcopy(valid_closure)
    packet["workers"] = []
    invalid_closure_cases.append(("missing worker closure", packet, "do not match expected_worker_ids"))
    packet = copy.deepcopy(valid_closure)
    packet["workers"][0]["repository_state"] = {"kind": "dirty"}
    invalid_closure_cases.append(("dirty worker archive", packet, "cannot be archived"))
    packet = copy.deepcopy(valid_closure)
    packet["workers"][0]["attention_required"] = True
    invalid_closure_cases.append(("attention worker archive", packet, "attention_required must be false"))
    packet = copy.deepcopy(valid_closure)
    packet["root"]["archive_requested"] = True
    invalid_closure_cases.append(("root auto archive", packet, "cannot auto-archive"))
    packet = copy.deepcopy(valid_closure)
    packet["workers"][0]["worktree_cleanup_requested"] = True
    invalid_closure_cases.append(("worker cleanup without approval", packet, "cleanup requires separate"))
    packet = copy.deepcopy(valid_closure)
    packet["root"]["cleanup_requested"] = True
    invalid_closure_cases.append(("root cleanup without approval", packet, "cleanup requires separate"))
    for label, packet, expected_error in invalid_closure_cases:
        errors = validate_task_packet(packet)
        if not any(expected_error in error for error in errors):
            raise AssertionError(f"{label} was accepted or failed unclearly: {errors}")

    snapshot = load_fixture("valid-task-hygiene-snapshot.json")
    summary = summarize_task_hygiene(snapshot)
    if summary["summary"] != {"task_count": 2, "exception_count": 1}:
        raise AssertionError(f"unexpected hygiene summary: {summary}")
    if [item["code"] for item in summary["exceptions"]] != ["archive_candidate"]:
        raise AssertionError(f"valid snapshot did not produce one archive candidate: {summary}")

    adversarial = copy.deepcopy(snapshot)
    adversarial["tasks"][0]["title"] = "ROOT-1 · Delivery · private root title"
    adversarial["tasks"][0]["archive_requested"] = True
    adversarial["tasks"][1]["title"] = "{{ raw delegation blob }}"
    adversarial["tasks"][1]["delegation_depth"] = 2
    adversarial["tasks"][1]["created_child_count"] = 1
    adversarial["tasks"][1]["human_authority"] = True
    hygienic = summarize_task_hygiene(adversarial)
    codes = {item["code"] for item in hygienic["exceptions"]}
    required_codes = {
        "raw_title_markup",
        "recursive_delegation",
        "worker_authority",
        "root_archive_without_approval",
    }
    if not required_codes.issubset(codes):
        raise AssertionError(f"hygiene analyzer missed adversarial cases: {hygienic}")
    rendered = json.dumps(hygienic)
    for forbidden in ("private root title", "raw delegation blob", "root-ops-41", "worker-ops-41-writer"):
        if forbidden in rendered:
            raise AssertionError(f"hygiene output leaked task text or raw identity: {forbidden}")

    for script_name in ("validate_task_orchestration.py", "summarize_task_hygiene.py"):
        script = (SCRIPTS / script_name).read_text(encoding="utf-8")
        for forbidden in ("state_5.sqlite", "threads.sqlite", "conversation body"):
            if forbidden in script:
                raise AssertionError(f"{script_name} reads or names private task storage: {forbidden}")

    task_reference = (ROOT / "references" / "task-orchestration.md").read_text(encoding="utf-8")
    for required in (
        "sole human-control surface",
        "NEEDS_PARENT_DECISION",
        "delegation depth 1",
        "two active workers and five created workers",
        "<work-key> · <role> · <outcome>",
        "never auto-archives",
        "Cleanup is a",
    ):
        if required.casefold() not in task_reference.casefold():
            raise AssertionError(f"task-orchestration contract is missing {required}")

    for skill_name in (
        "project-ops-manager",
        "project-ops-delivery",
        "project-ops-assess",
        "project-ops-automate",
        "project-ops-upgrader",
    ):
        skill = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        if "../../references/task-orchestration.md" in skill:
            raise AssertionError(f"{skill_name} activates the unpromoted task-orchestration candidate")

    run(str(SCRIPTS / "test_owned_process_supervisor.py"))
    promotion = (ROOT / "references" / "promotion-registry.md").read_text(encoding="utf-8")
    for required in ("Windows", "POSIX", "independent assessment", "not activated"):
        if required.casefold() not in promotion.casefold():
            raise AssertionError(f"owned-process promotion gate is missing {required}")


def main() -> int:
    assert_no_placeholders(ROOT)
    assert_skills()
    assert_memory_lifecycle_contract()
    assert_researcher_contract()
    assert_operational_controls()

    run(str(SCRIPTS / "validate_project_profile.py"), str(FIXTURES / "valid-project.json"))
    run(str(SCRIPTS / "validate_project_profile.py"), str(FIXTURES / "invalid-project.json"), expect=1)
    invalid_controls = copy.deepcopy(load_fixture("valid-project.json"))
    invalid_controls["controls"]["retrieval"]["checkpoint_policy"] = "always"  # type: ignore[index]
    control_errors, _ = validate_profile(invalid_controls)
    if not any("checkpoint_policy must be success-only" in error for error in control_errors):
        raise AssertionError(f"profile accepted unsafe retrieval checkpoint policy: {control_errors}")
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
    assert_task_orchestration()

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
            "templates/operational-control-run.md",
            "templates/human-authority-receipt.md",
            "templates/release-evidence.md",
            "wiki/test-project/pm/records/improvements",
            "dashboards/Test Project Improvements.base",
            "wiki/test-project/pm/records/research",
            "raw/test-project/research",
            "dashboards/Test Project Research.base",
            "wiki/test-project/pm/records/authority",
            "wiki/test-project/pm/records/releases",
            "raw/test-project/pm-os/controls",
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
        controls = generated_profile["controls"]
        if controls["retrieval"]["checkpoint_policy"] != "success-only":
            raise AssertionError("retrieval checkpoint safety was not preserved")
        if controls["release_evidence"]["missing_link_state"] != "gray":
            raise AssertionError("release-evidence Gray default was not preserved")

    print("PASS: Project Operations deterministic smoke tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
