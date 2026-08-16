#!/usr/bin/env python3
"""Deterministic smoke tests for the Project Operations plugin."""

from __future__ import annotations

import copy
import hashlib
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
from validate_poppy_orchestration import (
    canonical_digest as poppy_digest,
    validate_closure as validate_poppy_closure,
    validate_graph as validate_poppy_graph,
    validate_plan as validate_poppy_plan,
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
    upgrader = (ROOT / "skills" / "project-ops-upgrader" / "SKILL.md").read_text(encoding="utf-8")
    architecture = (ROOT / "references" / "architecture.md").read_text(encoding="utf-8")
    for term in ("repair-existing", "inspect-only", "project-ops-upgrader", "validate_research_packet.py"):
        if term not in skill:
            raise AssertionError(f"Researcher skill is missing required contract term: {term}")
    capability_graph = json.loads(
        (ROOT / "references" / "poppy-capability-graph.json").read_text(encoding="utf-8")
    )
    research_nodes = [node for node in capability_graph["nodes"] if node.get("id") == "research"]
    if len(research_nodes) != 1 or research_nodes[0].get("handler") != "project-ops-researcher":
        raise AssertionError("Poppy graph does not route bounded external discovery to Researcher")
    if "research-handoff.md" not in upgrader:
        raise AssertionError("Upgrader does not load the Researcher handoff contract")
    for term in ("Poppy", "Researcher", "selected capability"):
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


def assert_poppy_orchestration() -> None:
    graph = json.loads((ROOT / "references" / "poppy-capability-graph.json").read_text(encoding="utf-8"))
    graph_errors = validate_poppy_graph(graph)
    if graph_errors:
        raise AssertionError(f"Poppy capability graph failed: {graph_errors}")
    run(str(SCRIPTS / "validate_poppy_orchestration.py"), str(ROOT / "references" / "poppy-capability-graph.json"))

    simple = load_fixture("valid-poppy-simple-plan.json")
    plan = load_fixture("valid-poppy-plan.json")
    closure = load_fixture("valid-poppy-closure.json")
    if errors := validate_poppy_plan(simple, graph):
        raise AssertionError(f"valid simple Poppy plan failed: {errors}")
    alias_plan = copy.deepcopy(simple)
    alias_text = "Project Operations Partner, what does Gray mean?"
    alias_plan["trigger"]["mention"] = alias_text  # type: ignore[index]
    alias_plan["trigger"]["turn_digest"] = hashlib.sha256(alias_text.encode("utf-8")).hexdigest()  # type: ignore[index]
    alias_plan["authority"]["source_digest"] = alias_plan["trigger"]["turn_digest"]  # type: ignore[index]
    if errors := validate_poppy_plan(alias_plan, graph):
        raise AssertionError(f"Project Operations Partner alias failed: {errors}")
    if errors := validate_poppy_plan(plan, graph):
        raise AssertionError(f"valid substantive Poppy plan failed: {errors}")
    if errors := validate_poppy_closure(closure, graph, plan):
        raise AssertionError(f"valid Poppy closure failed: {errors}")
    errors = validate_poppy_closure(closure, graph)
    if not any("requires the exact bound plan" in error for error in errors):
        raise AssertionError(f"Poppy accepted an unbound closure: {errors}")

    mutating = copy.deepcopy(plan)
    mutating.update(  # type: ignore[arg-type]
        {
            "run_id": "poppy-mutation-001",
            "interaction_class": "mutating",
            "scope_mode": "write-authorized",
            "objective": "Update one approved local project-control field and verify it",
            "acceptance": ["Apply exactly the approved field update and verify the read-back"],
            "selected_nodes": [
                "trigger", "triage", "project-resolve", "readiness-screen", "memory-orient",
                "preflight-evaluate", "dispatch", "operations-control", "join", "reconcile",
                "authorized-execution", "postflight-evaluate", "memory-close", "terminal",
            ],
            "selected_edges": [
                {"from": "trigger", "to": "triage"},
                {"from": "triage", "to": "project-resolve"},
                {"from": "project-resolve", "to": "readiness-screen"},
                {"from": "readiness-screen", "to": "memory-orient"},
                {"from": "memory-orient", "to": "preflight-evaluate"},
                {"from": "preflight-evaluate", "to": "dispatch"},
                {"from": "dispatch", "to": "operations-control"},
                {"from": "operations-control", "to": "join"},
                {"from": "join", "to": "reconcile"},
                {"from": "reconcile", "to": "authorized-execution"},
                {"from": "authorized-execution", "to": "postflight-evaluate"},
                {"from": "postflight-evaluate", "to": "memory-close"},
                {"from": "memory-close", "to": "terminal"},
            ],
        }
    )
    mutating["trigger"]["turn_id"] = "user-turn-mutation-001"  # type: ignore[index]
    mutating_turn = "Poppy, I authorize this exact action: Set review_mode to evidence-first"
    mutating["trigger"]["mention"] = mutating_turn  # type: ignore[index]
    mutating["trigger"]["turn_digest"] = hashlib.sha256(mutating_turn.encode("utf-8")).hexdigest()  # type: ignore[index]
    mutating["preflight"].update({"confidence": "high", "risk": "R1"})  # type: ignore[union-attr]
    mutating["authority"] = {  # type: ignore[index]
        "status": "authorized",
        "maximum_risk": "R1",
        "receipt_id": "user-turn-mutation-001",
        "source": "current-user-turn",
        "source_digest": mutating["trigger"]["turn_digest"],
        "allowed_actions": ["Set review_mode to evidence-first"],
        "approval_required": [],
        "forbidden_actions": ["Any external-system mutation"],
        "effect_previews": [
            {
                "effect_id": "effect-review-mode-001",
                "target": "local-project-control",
                "action": "Set review_mode to evidence-first",
                "rollback": "Restore the prior field value",
                "handler": "project-ops-manager",
            }
        ],
    }
    mutating["memory"]["durable_write"] = "planned"  # type: ignore[index]
    if errors := validate_poppy_plan(mutating, graph):
        raise AssertionError(f"valid mutating Poppy plan failed: {errors}")
    forged_turn_authority = copy.deepcopy(mutating)
    non_authorizing_turn = "Poppy, assess this project's health and commercial exposure"
    forged_turn_authority["trigger"]["mention"] = non_authorizing_turn  # type: ignore[index]
    forged_turn_authority["trigger"]["turn_digest"] = hashlib.sha256(  # type: ignore[index]
        non_authorizing_turn.encode("utf-8")
    ).hexdigest()
    forged_turn_authority["authority"]["source_digest"] = forged_turn_authority["trigger"]["turn_digest"]  # type: ignore[index]
    forged_turn_authority["authority"]["allowed_actions"] = ["Delete the project controls"]  # type: ignore[index]
    forged_turn_authority["authority"]["effect_previews"][0]["action"] = "Delete the project controls"  # type: ignore[index]
    errors = validate_poppy_plan(forged_turn_authority, graph)
    if not any("explicit authorization language" in error for error in errors):
        raise AssertionError(f"Poppy self-promoted a non-authorizing turn into write authority: {errors}")

    mutation_closure = {
        "schema_version": 1,
        "packet_type": "closure",
        "run_id": "poppy-mutation-001-closure",
        "plan_run_id": mutating["run_id"],
        "root_task_id": mutating["root_task_id"],
        "project_id": mutating["project_id"],
        "graph_id": mutating["graph_id"],
        "graph_digest": mutating["graph_digest"],
        "plan_digest": poppy_digest(mutating),
        "authority_receipt_id": "user-turn-mutation-001",
        "scope_mode": "write-authorized",
        "trigger": copy.deepcopy(mutating["trigger"]),
        "interaction_class": "mutating",
        "objective": mutating["objective"],
        "risk": "R1",
        "selected_nodes": copy.deepcopy(mutating["selected_nodes"]),
        "selected_edges": copy.deepcopy(mutating["selected_edges"]),
        "node_results": [
            {"node": node, "status": "pass", "summary": f"{node} completed", "evidence_refs": []}
            for node in mutating["selected_nodes"]
        ],
        "acceptance_results": [
            {"item": mutating["acceptance"][0], "status": "pass", "evidence_refs": ["effect-readback"]}
        ],
        "external_effects": [
            {
                "effect_id": "effect-review-mode-001",
                "target": "local-project-control",
                "action": "Set review_mode to evidence-first",
                "handler": "project-ops-manager",
                "authority_receipt_id": "user-turn-mutation-001",
                "verified": True,
                "evidence_refs": ["effect-readback"],
            }
        ],
        "worker_closures": [],
        "postflight": {
            "verdict": "PASS",
            "confidence": "high",
            "evidence_basis": ["The exact authorized effect was read back"],
            "residual_risks": [],
            "evaluator": "root",
            "evaluator_task_id": mutating["root_task_id"],
            "independent": False,
        },
        "memory": {"closure": "updated"},
    }
    if errors := validate_poppy_closure(mutation_closure, graph, mutating):
        raise AssertionError(f"valid mutating Poppy closure failed: {errors}")
    wrong_effect = copy.deepcopy(mutation_closure)
    wrong_effect["external_effects"][0]["action"] = "Set a different field"  # type: ignore[index]
    errors = validate_poppy_closure(wrong_effect, graph, mutating)
    if not any("exactly match" in error for error in errors):
        raise AssertionError(f"Poppy closure accepted an effect outside the authority receipt: {errors}")
    duplicate_effect = copy.deepcopy(mutation_closure)
    duplicate_effect["external_effects"].append(  # type: ignore[union-attr]
        copy.deepcopy(duplicate_effect["external_effects"][0])  # type: ignore[index]
    )
    errors = validate_poppy_closure(duplicate_effect, graph, mutating)
    if not any("effect_id must be unique" in error for error in errors) or not any(
        "exactly match" in error for error in errors
    ):
        raise AssertionError(f"Poppy closure accepted duplicate execution of one approved effect: {errors}")

    authority_attack = copy.deepcopy(mutating)
    authority_attack["authority"]["receipt_id"] = "fabricated-receipt"  # type: ignore[index]
    authority_attack["authority"]["allowed_actions"] = ["Read a dashboard only"]  # type: ignore[index]
    authority_attack["authority"]["effect_previews"][0]["action"] = "Delete all project items"  # type: ignore[index]
    errors = validate_poppy_plan(authority_attack, graph)
    if not any("receipt_id must match" in error for error in errors) or not any(
        "outside allowed_actions" in error for error in errors
    ):
        raise AssertionError(f"Poppy accepted fabricated or out-of-scope authority: {errors}")
    contradictory_authority = copy.deepcopy(mutating)
    contradictory_authority["authority"]["forbidden_actions"].append(  # type: ignore[index]
        "Set review_mode to evidence-first"
    )
    errors = validate_poppy_plan(contradictory_authority, graph)
    if not any("must not overlap" in error for error in errors):
        raise AssertionError(f"Poppy accepted contradictory allowed/forbidden authority: {errors}")
    contradictory_approval = copy.deepcopy(mutating)
    contradictory_approval["authority"]["approval_required"] = [  # type: ignore[index]
        "Set review_mode to evidence-first"
    ]
    errors = validate_poppy_plan(contradictory_approval, graph)
    if not any("allowed_actions and approval_required" in error for error in errors):
        raise AssertionError(f"Poppy accepted authorized and approval-required action overlap: {errors}")
    unicode_authority = copy.deepcopy(mutating)
    unicode_authority["authority"]["allowed_actions"] = ["Set café mode"]  # type: ignore[index]
    unicode_authority["authority"]["forbidden_actions"] = ["Set cafe\u0301 mode"]  # type: ignore[index]
    unicode_authority["authority"]["effect_previews"][0]["action"] = "Set café mode"  # type: ignore[index]
    errors = validate_poppy_plan(unicode_authority, graph)
    if not any("allowed_actions and forbidden_actions must not overlap" in error for error in errors):
        raise AssertionError(f"Poppy accepted canonically equivalent contradictory authority: {errors}")
    packet = copy.deepcopy(mutation_closure)
    packet["risk"] = "R0"
    errors = validate_poppy_closure(packet, graph, mutating)
    if not any("risk does not match" in error for error in errors):
        raise AssertionError(f"Poppy closure lowered the bound plan risk: {errors}")
    skipped_execution = copy.deepcopy(mutation_closure)
    for node_result in skipped_execution["node_results"]:  # type: ignore[union-attr]
        if node_result["node"] == "authorized-execution":
            node_result.update({"status": "skipped", "skip_reason": "Not executed"})
    skipped_execution["postflight"]["verdict"] = "ESCALATE"  # type: ignore[index]
    errors = validate_poppy_closure(skipped_execution, graph, mutating)
    if not any("passing authorized-execution" in error for error in errors):
        raise AssertionError(f"Poppy recorded effects while authorized execution was skipped: {errors}")
    packet = copy.deepcopy(closure)
    packet["trigger"]["mention"] = "Poppy, do something else"  # type: ignore[index]
    packet["trigger"]["turn_digest"] = hashlib.sha256(  # type: ignore[index]
        packet["trigger"]["mention"].encode("utf-8")  # type: ignore[index]
    ).hexdigest()
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("closure trigger does not match" in error for error in errors):
        raise AssertionError(f"Poppy closure substituted another trigger: {errors}")
    packet = copy.deepcopy(closure)
    packet["acceptance_results"] = [
        {"item": "Unrelated easy assertion", "status": "pass", "evidence_refs": ["unrelated"]}
    ]
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("exactly cover" in error for error in errors):
        raise AssertionError(f"Poppy closure replaced the acceptance contract: {errors}")
    packet = copy.deepcopy(closure)
    for acceptance_result in packet["acceptance_results"]:  # type: ignore[union-attr]
        acceptance_result["evidence_refs"] = []
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("direct evidence" in error for error in errors):
        raise AssertionError(f"Poppy PASS accepted evidence-free acceptance results: {errors}")
    packet = copy.deepcopy(simple)
    false_trigger = "Tell me what poppycock means"
    packet["trigger"]["mention"] = false_trigger  # type: ignore[index]
    packet["trigger"]["turn_digest"] = hashlib.sha256(false_trigger.encode("utf-8")).hexdigest()  # type: ignore[index]
    packet["authority"]["source_digest"] = packet["trigger"]["turn_digest"]  # type: ignore[index]
    errors = validate_poppy_plan(packet, graph)
    if not any("explicitly contain Poppy" in error for error in errors):
        raise AssertionError(f"Poppy substring trigger accepted poppycock: {errors}")
    for unicode_false_trigger in (
        "Tell me about äppoppyβ",
        "Tell me about Poppy\u0301",
        "Tell me about Poppy\u200dX",
        "Tell me about Poppy\u00adX",
        "Tell me about Poppy\ufe0fX",
    ):
        packet = copy.deepcopy(simple)
        packet["trigger"]["mention"] = unicode_false_trigger  # type: ignore[index]
        packet["trigger"]["turn_digest"] = hashlib.sha256(  # type: ignore[index]
            unicode_false_trigger.encode("utf-8")
        ).hexdigest()
        packet["authority"]["source_digest"] = packet["trigger"]["turn_digest"]  # type: ignore[index]
        errors = validate_poppy_plan(packet, graph)
        if not any("explicitly contain Poppy" in error for error in errors):
            raise AssertionError(
                f"Poppy accepted a Unicode-adjacent false trigger {unicode_false_trigger!r}: {errors}"
            )

    ask_user = copy.deepcopy(plan)
    ask_user.update(  # type: ignore[arg-type]
        {
            "run_id": "poppy-ask-project-001",
            "project_id": "unresolved",
            "objective": "Resolve an ambiguous project before reading project evidence",
            "acceptance": ["Stop safely and ask for the project identity"],
            "selected_nodes": [
                "trigger", "triage", "project-resolve", "needs-user-decision", "terminal"
            ],
            "selected_edges": [
                {"from": "trigger", "to": "triage"},
                {"from": "triage", "to": "project-resolve"},
                {"from": "project-resolve", "to": "needs-user-decision"},
                {"from": "needs-user-decision", "to": "terminal"},
            ],
        }
    )
    ask_user["preflight"].update(  # type: ignore[union-attr]
        {"confidence": "insufficient", "risk": "R0", "disposition": "ask-user"}
    )
    ask_user["memory"] = {  # type: ignore[index]
        "orientation": "not-required", "closure": "not-required", "durable_write": "not-planned"
    }
    if errors := validate_poppy_plan(ask_user, graph):
        raise AssertionError(f"valid ambiguous-project safe-stop plan failed: {errors}")

    unsafe_stop = copy.deepcopy(mutating)
    unsafe_stop["preflight"]["disposition"] = "ask-user"  # type: ignore[index]
    unsafe_stop["selected_nodes"].insert(  # type: ignore[index]
        unsafe_stop["selected_nodes"].index("dispatch"), "needs-user-decision"  # type: ignore[index]
    )
    unsafe_stop["selected_edges"] = [  # type: ignore[index]
        edge
        for edge in unsafe_stop["selected_edges"]
        if edge != {"from": "preflight-evaluate", "to": "dispatch"}
    ]
    unsafe_stop["selected_edges"].extend(  # type: ignore[union-attr]
        [
            {"from": "preflight-evaluate", "to": "needs-user-decision"},
            {"from": "needs-user-decision", "to": "dispatch"},
            {"from": "needs-user-decision", "to": "terminal"},
        ]
    )
    errors = validate_poppy_plan(unsafe_stop, graph)
    if not any("stopped plan cannot select authorized execution" in error for error in errors):
        raise AssertionError(f"Poppy ask-user stop retained authorized execution: {errors}")

    approval_plan = copy.deepcopy(ask_user)
    approval_plan.update(  # type: ignore[arg-type]
        {
            "run_id": "poppy-approval-001",
            "interaction_class": "mutating",
            "scope_mode": "write-authorized",
            "objective": "Request authority for one exact local control update",
            "acceptance": ["Respect a denied or deferred approval without any effect"],
        }
    )
    approval_plan["preflight"].update(  # type: ignore[union-attr]
        {"confidence": "medium", "risk": "R1", "disposition": "escalate-approval"}
    )
    approval_plan["authority"] = {  # type: ignore[index]
        "status": "approval-required",
        "maximum_risk": "R1",
        "receipt_id": approval_plan["trigger"]["turn_id"],
        "source": "current-user-turn",
        "source_digest": approval_plan["trigger"]["turn_digest"],
        "allowed_actions": [],
        "approval_required": ["Set review_mode to evidence-first"],
        "forbidden_actions": ["Any effect before approval"],
        "effect_previews": [
            {
                "effect_id": "effect-review-mode-approval-001",
                "target": "local-project-control",
                "action": "Set review_mode to evidence-first",
                "rollback": "Restore the prior field value",
                "handler": "project-ops-manager",
            }
        ],
    }
    if errors := validate_poppy_plan(approval_plan, graph):
        raise AssertionError(f"valid approval-escalation conditional plan failed: {errors}")
    approval_execution = copy.deepcopy(mutating)
    approval_execution["authority"]["status"] = "approval-required"  # type: ignore[index]
    approval_execution["authority"]["allowed_actions"] = []  # type: ignore[index]
    approval_execution["authority"]["approval_required"] = [  # type: ignore[index]
        "Set review_mode to evidence-first"
    ]
    errors = validate_poppy_plan(approval_execution, graph)
    if not any("must stop before authorized execution" in error for error in errors):
        raise AssertionError(f"Poppy approval-required plan selected execution: {errors}")
    denial_closure = {
        "schema_version": 1,
        "packet_type": "closure",
        "run_id": "poppy-approval-001-closure",
        "plan_run_id": approval_plan["run_id"],
        "root_task_id": approval_plan["root_task_id"],
        "project_id": approval_plan["project_id"],
        "graph_id": approval_plan["graph_id"],
        "graph_digest": approval_plan["graph_digest"],
        "plan_digest": poppy_digest(approval_plan),
        "authority_receipt_id": approval_plan["authority"]["receipt_id"],
        "approval_decision": "denied",
        "scope_mode": approval_plan["scope_mode"],
        "trigger": copy.deepcopy(approval_plan["trigger"]),
        "interaction_class": approval_plan["interaction_class"],
        "objective": approval_plan["objective"],
        "risk": approval_plan["preflight"]["risk"],
        "selected_nodes": copy.deepcopy(approval_plan["selected_nodes"]),
        "selected_edges": copy.deepcopy(approval_plan["selected_edges"]),
        "node_results": [
            {
                "node": node,
                "status": "pass" if node in {
                    "trigger", "triage", "project-resolve", "readiness-screen", "memory-orient",
                    "preflight-evaluate", "needs-user-decision", "terminal",
                } else "skipped",
                "summary": "Approval denied safely" if node == "terminal" else f"{node} resolved",
                "evidence_refs": ["approval-denial"] if node in {"needs-user-decision", "terminal"} else [],
                **({"skip_reason": "Approval denied before execution"} if node not in {
                    "trigger", "triage", "project-resolve", "readiness-screen", "memory-orient",
                    "preflight-evaluate", "needs-user-decision", "terminal",
                } else {}),
            }
            for node in approval_plan["selected_nodes"]
        ],
        "acceptance_results": [
            {
                "item": approval_plan["acceptance"][0],
                "status": "pass",
                "evidence_refs": ["approval-denial"],
            }
        ],
        "external_effects": [],
        "worker_closures": [],
        "postflight": {
            "verdict": "ESCALATE",
            "confidence": "high",
            "evidence_basis": ["The denied decision is recorded and no effect occurred"],
            "residual_risks": ["Requested mutation remains unapplied"],
            "evaluator": "root",
            "evaluator_task_id": approval_plan["root_task_id"],
            "independent": False,
        },
        "memory": {"closure": "no-change"},
    }
    if errors := validate_poppy_closure(denial_closure, graph, approval_plan):
        raise AssertionError(f"valid approval-denial no-effect closure failed: {errors}")

    worker_plan = copy.deepcopy(plan)
    worker_plan["delegation"] = {  # type: ignore[index]
        "mode": "bounded",
        "max_depth": 1,
        "max_active_workers": 1,
        "max_created_workers": 1,
        "workers": [
            {
                "id": "worker-health-decision-001",
                "root_task_id": worker_plan["root_task_id"],
                "parent_task_id": worker_plan["root_task_id"],
                "depth": 1,
                "can_delegate": False,
                "shared_memory_write": False,
                "decision_protocol": "NEEDS_PARENT_DECISION",
                "status": "complete",
                "node": "health-reporting",
                "skill": "project-ops-health",
                "authority": "read-only",
                "minimized_inputs": ["decision-queue"],
                "stop_conditions": ["human decision required"],
                "output_contract": "health-snapshot",
                "effort": "medium",
                "effort_rationale": "Independent bounded health assessment",
                "remaining_task_allowance": 0,
            }
        ],
    }
    if errors := validate_poppy_plan(worker_plan, graph):
        raise AssertionError(f"valid bounded-worker Poppy plan failed: {errors}")
    unresolved_worker = copy.deepcopy(closure)
    unresolved_worker["plan_digest"] = poppy_digest(worker_plan)
    unresolved_worker["worker_closures"] = [
        {
            "worker_id": "worker-health-decision-001",
            "root_task_id": worker_plan["root_task_id"],
            "parent_task_id": worker_plan["root_task_id"],
            "outcome": "NEEDS_PARENT_DECISION",
            "evidence_refs": ["worker-decision-packet"],
            "repository_state": {"status": "not-applicable"},
            "residual_risk": "Human decision remains unresolved",
            "next_action": "Poppy must resolve or relay the decision",
        }
    ]
    errors = validate_poppy_closure(unresolved_worker, graph, worker_plan)
    if not any("selected root decision node" in error for error in errors):
        raise AssertionError(f"Poppy PASS accepted unresolved worker decision relay: {errors}")
    resolved_worker_plan = copy.deepcopy(worker_plan)
    dispatch_index = resolved_worker_plan["selected_nodes"].index("dispatch")  # type: ignore[index]
    resolved_worker_plan["selected_nodes"].insert(dispatch_index, "needs-user-decision")  # type: ignore[index]
    resolved_worker_plan["selected_edges"] = [  # type: ignore[index]
        edge
        for edge in resolved_worker_plan["selected_edges"]
        if edge != {"from": "preflight-evaluate", "to": "dispatch"}
    ]
    resolved_worker_plan["selected_edges"].extend(  # type: ignore[union-attr]
        [
            {"from": "preflight-evaluate", "to": "needs-user-decision"},
            {"from": "needs-user-decision", "to": "dispatch"},
        ]
    )
    if errors := validate_poppy_plan(resolved_worker_plan, graph):
        raise AssertionError(f"valid resolved-worker decision plan failed: {errors}")
    resolved_worker = copy.deepcopy(closure)
    resolved_worker["plan_digest"] = poppy_digest(resolved_worker_plan)
    resolved_worker["selected_nodes"] = copy.deepcopy(resolved_worker_plan["selected_nodes"])
    resolved_worker["selected_edges"] = copy.deepcopy(resolved_worker_plan["selected_edges"])
    resolved_worker["node_results"].insert(  # type: ignore[index]
        dispatch_index,
        {
            "node": "needs-user-decision",
            "status": "pass",
            "summary": "Poppy resolved the relayed worker decision",
            "evidence_refs": ["parent-resolution-001"],
        },
    )
    resolved_worker["worker_closures"] = [
        {
            "worker_id": "worker-health-decision-001",
            "root_task_id": resolved_worker_plan["root_task_id"],
            "parent_task_id": resolved_worker_plan["root_task_id"],
            "outcome": "NEEDS_PARENT_DECISION",
            "parent_resolution_receipt": "parent-resolution-001",
            "evidence_refs": ["worker-decision-packet"],
            "repository_state": {"status": "not-applicable"},
            "residual_risk": "Decision resolved by Poppy",
            "next_action": "Use the recorded parent disposition",
        }
    ]
    if errors := validate_poppy_closure(resolved_worker, graph, resolved_worker_plan):
        raise AssertionError(f"valid resolved-worker decision closure failed: {errors}")
    failed_worker = copy.deepcopy(resolved_worker)
    failed_worker["worker_closures"][0]["outcome"] = "failed"  # type: ignore[index]
    failed_worker["worker_closures"][0].pop("parent_resolution_receipt")  # type: ignore[index]
    errors = validate_poppy_closure(failed_worker, graph, resolved_worker_plan)
    if not any("failed worker outcomes" in error for error in errors):
        raise AssertionError(f"Poppy PASS accepted a failed ordinary worker: {errors}")

    r2_without_evaluator = copy.deepcopy(mutating)
    r2_without_evaluator["preflight"]["risk"] = "R2"  # type: ignore[index]
    r2_without_evaluator["authority"]["maximum_risk"] = "R2"  # type: ignore[index]
    errors = validate_poppy_plan(r2_without_evaluator, graph)
    if not any("planned fresh postflight evaluator" in error for error in errors):
        raise AssertionError(f"Poppy R2 plan omitted its independent evaluator worker: {errors}")

    r3_manifest = copy.deepcopy(r2_without_evaluator)
    r3_manifest["preflight"]["risk"] = "R3"  # type: ignore[index]
    r3_manifest["authority"].update(  # type: ignore[union-attr]
        {
            "maximum_risk": "R3",
            "receipt_id": "manifest-release-001",
            "source": "approved-manifest",
            "source_digest": "f" * 64,
        }
    )
    errors = validate_poppy_plan(r3_manifest, graph)
    if not any("cannot come from an approved manifest" in error for error in errors):
        raise AssertionError(f"Poppy accepted R3 authority from an approved manifest: {errors}")

    r2_plan = copy.deepcopy(r2_without_evaluator)
    r2_plan["delegation"] = {  # type: ignore[index]
        "mode": "bounded",
        "max_depth": 1,
        "max_active_workers": 1,
        "max_created_workers": 1,
        "workers": [
            {
                "id": "worker-postflight-r2-001",
                "root_task_id": r2_plan["root_task_id"],
                "parent_task_id": r2_plan["root_task_id"],
                "depth": 1,
                "can_delegate": False,
                "shared_memory_write": False,
                "decision_protocol": "NEEDS_PARENT_DECISION",
                "status": "planned",
                "node": "postflight-evaluate",
                "skill": "project-ops-evaluate",
                "authority": "read-only",
                "minimized_inputs": ["verified-effects"],
                "stop_conditions": ["candidate identity changes", "human decision required"],
                "output_contract": "postflight-verdict",
                "effort": "high",
                "effort_rationale": "R2 independent release gate",
                "remaining_task_allowance": 0,
            }
        ],
    }
    if errors := validate_poppy_plan(r2_plan, graph):
        raise AssertionError(f"valid R2 plan with fresh evaluator failed: {errors}")
    stopped_evaluator_plan = copy.deepcopy(r2_plan)
    stopped_evaluator_plan["delegation"]["workers"][0]["status"] = "stopped"  # type: ignore[index]
    errors = validate_poppy_plan(stopped_evaluator_plan, graph)
    if not any("planned fresh postflight evaluator" in error for error in errors):
        raise AssertionError(f"Poppy R2 plan accepted a stopped evaluator: {errors}")
    fake_r2_closure = copy.deepcopy(mutation_closure)
    fake_r2_closure["risk"] = "R2"
    fake_r2_closure["plan_digest"] = poppy_digest(r2_plan)
    fake_r2_closure["postflight"].update(  # type: ignore[union-attr]
        {
            "evaluator": "fresh-worker",
            "evaluator_task_id": "worker-postflight-r2-001",
            "independent": True,
        }
    )
    errors = validate_poppy_closure(fake_r2_closure, graph, r2_plan)
    if not any("planned worker and closure card" in error for error in errors):
        raise AssertionError(f"Poppy accepted a fabricated independent evaluator identity: {errors}")
    valid_r2_closure = copy.deepcopy(fake_r2_closure)
    valid_r2_closure["worker_closures"] = [
        {
            "worker_id": "worker-postflight-r2-001",
            "root_task_id": r2_plan["root_task_id"],
            "parent_task_id": r2_plan["root_task_id"],
            "outcome": "complete",
            "evidence_refs": ["independent-postflight-verdict"],
            "repository_state": {"status": "not-applicable"},
            "residual_risk": "No material residual risk",
            "next_action": "Return verdict to Poppy",
        }
    ]
    valid_r2_closure["postflight"]["evidence_basis"].append(  # type: ignore[index]
        "independent-postflight-verdict"
    )
    if errors := validate_poppy_closure(valid_r2_closure, graph, r2_plan):
        raise AssertionError(f"valid R2 independent-evaluator closure failed: {errors}")
    unbound_evaluator_evidence = copy.deepcopy(valid_r2_closure)
    unbound_evaluator_evidence["postflight"]["evidence_basis"] = [  # type: ignore[index]
        "The root claims the evaluator passed"
    ]
    errors = validate_poppy_closure(unbound_evaluator_evidence, graph, r2_plan)
    if not any("must cite the independent evaluator evidence" in error for error in errors):
        raise AssertionError(f"Poppy accepted unbound independent-evaluator evidence: {errors}")
    failed_evaluator = copy.deepcopy(valid_r2_closure)
    failed_evaluator["worker_closures"][0]["outcome"] = "failed"  # type: ignore[index]
    errors = validate_poppy_closure(failed_evaluator, graph, r2_plan)
    if not any("planned worker and closure card" in error for error in errors):
        raise AssertionError(f"Poppy PASS accepted a failed R2 evaluator: {errors}")

    delivery_plan = copy.deepcopy(mutating)
    delivery_plan["selected_nodes"] = [  # type: ignore[index]
        "trigger", "triage", "project-resolve", "readiness-screen", "memory-orient",
        "preflight-evaluate", "dispatch", "delivery", "functional-qa", "final-assurance",
        "join", "reconcile", "authorized-execution", "postflight-evaluate", "memory-close",
        "terminal",
    ]
    delivery_plan["selected_edges"] = [  # type: ignore[index]
        {"from": "trigger", "to": "triage"},
        {"from": "triage", "to": "project-resolve"},
        {"from": "project-resolve", "to": "readiness-screen"},
        {"from": "readiness-screen", "to": "memory-orient"},
        {"from": "memory-orient", "to": "preflight-evaluate"},
        {"from": "preflight-evaluate", "to": "dispatch"},
        {"from": "dispatch", "to": "delivery"},
        {"from": "delivery", "to": "functional-qa"},
        {"from": "functional-qa", "to": "final-assurance"},
        {"from": "final-assurance", "to": "join"},
        {"from": "join", "to": "reconcile"},
        {"from": "reconcile", "to": "authorized-execution"},
        {"from": "authorized-execution", "to": "postflight-evaluate"},
        {"from": "postflight-evaluate", "to": "memory-close"},
        {"from": "memory-close", "to": "terminal"},
    ]
    delivery_plan["authority"]["effect_previews"][0]["handler"] = "project-ops-delivery"  # type: ignore[index]
    errors = validate_poppy_plan(delivery_plan, graph)
    if not all(
        any(f"selected fresh-worker node {node} requires exactly one separately planned worker" in error for error in errors)
        for node in ("functional-qa", "final-assurance")
    ):
        raise AssertionError(f"Poppy delivery chain omitted fresh stage-separated assessors: {errors}")
    delivery_plan["delegation"] = {  # type: ignore[index]
        "mode": "bounded",
        "max_depth": 1,
        "max_active_workers": 1,
        "max_created_workers": 2,
        "workers": [
            {
                "id": f"worker-{node}-001",
                "root_task_id": delivery_plan["root_task_id"],
                "parent_task_id": delivery_plan["root_task_id"],
                "depth": 1,
                "can_delegate": False,
                "shared_memory_write": False,
                "decision_protocol": "NEEDS_PARENT_DECISION",
                "status": "planned",
                "node": node,
                "skill": "project-ops-assess",
                "authority": "read-only",
                "minimized_inputs": [
                    "frozen-delivery-evidence" if node == "functional-qa" else "functional-qa-verdict"
                ],
                "stop_conditions": ["candidate identity changes", "required prior-stage evidence is missing"],
                "output_contract": "functional-qa-verdict" if node == "functional-qa" else "final-assurance-verdict",
                "effort": "high",
                "effort_rationale": "Fresh stage-separated delivery assessment",
                "remaining_task_allowance": 0,
            }
            for node in ("functional-qa", "final-assurance")
        ],
    }
    if errors := validate_poppy_plan(delivery_plan, graph):
        raise AssertionError(f"valid delivery plan with fresh stage-separated assessors failed: {errors}")
    delivery_without_review = copy.deepcopy(delivery_plan)
    delivery_without_review["selected_nodes"] = [  # type: ignore[index]
        node for node in delivery_without_review["selected_nodes"]
        if node not in {"functional-qa", "final-assurance"}
    ]
    delivery_without_review["selected_edges"] = [  # type: ignore[index]
        edge for edge in delivery_without_review["selected_edges"]
        if edge["from"] not in {"delivery", "functional-qa", "final-assurance"}
        and edge["to"] not in {"functional-qa", "final-assurance"}
    ]
    delivery_without_review["selected_edges"].insert(  # type: ignore[index]
        8, {"from": "delivery", "to": "join"}
    )
    delivery_without_review["delegation"] = {  # type: ignore[index]
        "mode": "none", "max_depth": 0, "max_active_workers": 0,
        "max_created_workers": 0, "workers": [],
    }
    errors = validate_poppy_plan(delivery_without_review, graph)
    if not any("requires Functional QA and Final Assurance" in error for error in errors):
        raise AssertionError(f"Poppy delivery bypassed mandatory assessment stages: {errors}")
    wrong_assurance_input = copy.deepcopy(delivery_plan)
    wrong_assurance_input["delegation"]["workers"][1]["minimized_inputs"] = [  # type: ignore[index]
        "unrelated-marketing-note"
    ]
    errors = validate_poppy_plan(wrong_assurance_input, graph)
    if not any("minimized_inputs must exactly match selected incoming artifacts" in error for error in errors):
        raise AssertionError(f"Poppy Final Assurance accepted unrelated worker input: {errors}")
    wrong_assurance_output = copy.deepcopy(delivery_plan)
    wrong_assurance_output["delegation"]["workers"][1]["output_contract"] = "free-form-opinion"  # type: ignore[index]
    errors = validate_poppy_plan(wrong_assurance_output, graph)
    if not any("output_contract must match one declared node output" in error for error in errors):
        raise AssertionError(f"Poppy Final Assurance accepted an untyped worker output: {errors}")
    run(str(SCRIPTS / "validate_poppy_orchestration.py"), str(FIXTURES / "valid-poppy-simple-plan.json"))
    run(str(SCRIPTS / "validate_poppy_orchestration.py"), str(FIXTURES / "valid-poppy-plan.json"))
    run(
        str(SCRIPTS / "validate_poppy_orchestration.py"),
        str(FIXTURES / "valid-poppy-closure.json"),
        "--plan",
        str(FIXTURES / "valid-poppy-plan.json"),
    )

    plan_cases: list[tuple[str, dict[str, object], str]] = []
    packet = copy.deepcopy(plan)
    packet["trigger"]["provenance"] = "retrieved-document"  # type: ignore[index]
    plan_cases.append(("untrusted trigger", packet, "current-user-turn"))
    packet = copy.deepcopy(plan)
    packet["preflight"]["confidence"] = "low"  # type: ignore[index]
    plan_cases.append(("low-confidence execution", packet, "cannot dispatch execution"))
    packet = copy.deepcopy(plan)
    packet["preflight"]["risk"] = "R1"  # type: ignore[index]
    plan_cases.append(("authority below risk floor", packet, "below the preflight risk floor"))
    for invalid_project in ("not-required", "unknown", "sample-project,other-project"):
        packet = copy.deepcopy(plan)
        packet["project_id"] = invalid_project
        plan_cases.append((f"unresolved substantive project {invalid_project}", packet, "exact resolved project_id"))
    packet = copy.deepcopy(plan)
    packet["acceptance"] = []
    plan_cases.append(("empty acceptance", packet, "acceptance must be a non-empty string list"))
    packet = copy.deepcopy(plan)
    packet["preflight"]["evidence_basis"] = []  # type: ignore[index]
    plan_cases.append(("empty preflight evidence", packet, "preflight.evidence_basis must be a non-empty"))
    packet = copy.deepcopy(mutating)
    packet["interaction_class"] = "substantive-read"
    packet["scope_mode"] = "read-only"
    packet["authority"]["status"] = "read-only"  # type: ignore[index]
    packet["authority"]["allowed_actions"] = []  # type: ignore[index]
    packet["authority"]["effect_previews"] = []  # type: ignore[index]
    packet["memory"]["durable_write"] = "not-planned"  # type: ignore[index]
    plan_cases.append(("read-only authorized execution", packet, "non-mutating plans cannot select"))
    for non_execution_disposition in ("discover-then-plan", "orient-then-answer"):
        packet = copy.deepcopy(mutating)
        packet["preflight"]["disposition"] = non_execution_disposition  # type: ignore[index]
        plan_cases.append(
            (
                f"mutation under {non_execution_disposition}",
                packet,
                "authorized mutation requires execute-graph disposition",
            )
        )
    packet = copy.deepcopy(plan)
    packet["selected_nodes"].remove("join")  # type: ignore[union-attr]
    packet["selected_edges"] = [  # type: ignore[index]
        edge for edge in packet["selected_edges"] if "join" not in (edge["from"], edge["to"])
    ]
    plan_cases.append(("missing join barrier", packet, "join"))
    packet = copy.deepcopy(plan)
    packet["delegation"] = {  # type: ignore[index]
        "mode": "bounded",
        "max_depth": 1,
        "max_active_workers": 1,
        "max_created_workers": 1,
        "workers": [
            {
                "id": "worker-health-001",
                "root_task_id": packet["root_task_id"],
                "parent_task_id": packet["root_task_id"],
                "depth": 1,
                "can_delegate": True,
                "shared_memory_write": False,
                "decision_protocol": "NEEDS_PARENT_DECISION",
                "status": "planned",
                "node": "health-reporting",
                "skill": "project-ops-health",
                "authority": "read-only",
                "minimized_inputs": ["decision-queue"],
                "stop_conditions": ["human decision required"],
                "output_contract": "health-snapshot",
                "effort": "medium",
                "effort_rationale": "Independent bounded health assessment",
                "remaining_task_allowance": 0,
            }
        ],
    }
    plan_cases.append(("recursive worker", packet, "can_delegate must be false"))
    packet = copy.deepcopy(simple)
    packet["memory"]["durable_write"] = "conditional"  # type: ignore[index]
    plan_cases.append(("read-only memory write", packet, "suppress every durable memory write"))
    packet = copy.deepcopy(worker_plan)
    packet["delegation"]["workers"][0]["minimized_inputs"] = []  # type: ignore[index]
    plan_cases.append(("empty worker inputs", packet, "minimized_inputs must be a non-empty"))
    packet = copy.deepcopy(worker_plan)
    packet["delegation"]["workers"][0]["stop_conditions"] = []  # type: ignore[index]
    plan_cases.append(("empty worker stops", packet, "stop_conditions must be a non-empty"))
    packet = copy.deepcopy(worker_plan)
    packet["delegation"]["max_depth"] = 0  # type: ignore[index]
    plan_cases.append(("worker beyond declared depth", packet, "requires max_depth of at least 1"))
    packet = copy.deepcopy(worker_plan)
    packet["delegation"]["max_active_workers"] = 0  # type: ignore[index]
    plan_cases.append(("worker without active budget", packet, "positive max_active_workers budget"))
    packet = copy.deepcopy(worker_plan)
    packet["delegation"]["workers"][0]["remaining_task_allowance"] = 3  # type: ignore[index]
    plan_cases.append(("recursive task allowance", packet, "must be 0 because recursive delegation is forbidden"))
    for label, packet, expected in plan_cases:
        errors = validate_poppy_plan(packet, graph)
        if not any(expected in error for error in errors):
            raise AssertionError(f"Poppy {label} adversary was accepted: {errors}")

    packet = copy.deepcopy(closure)
    packet["plan_digest"] = "0" * 64
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("plan_digest does not match" in error for error in errors):
        raise AssertionError(f"Poppy closure accepted the wrong plan digest: {errors}")
    packet = copy.deepcopy(closure)
    packet["node_results"][0]["status"] = "limited"  # type: ignore[index]
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("every selected node to pass" in error for error in errors):
        raise AssertionError(f"Poppy PASS accepted a limited required node: {errors}")
    packet = copy.deepcopy(closure)
    packet["memory"]["closure"] = "updated"  # type: ignore[index]
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("non-write scope cannot update memory" in error for error in errors):
        raise AssertionError(f"Poppy read-only closure accepted a memory update: {errors}")
    packet = copy.deepcopy(closure)
    packet["postflight"]["evidence_basis"] = []  # type: ignore[index]
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("postflight.evidence_basis must be a non-empty" in error for error in errors):
        raise AssertionError(f"Poppy closure accepted an evidence-free postflight: {errors}")
    packet = copy.deepcopy(resolved_worker)
    packet["worker_closures"][0]["evidence_refs"] = []  # type: ignore[index]
    errors = validate_poppy_closure(packet, graph, resolved_worker_plan)
    if not any("evidence_refs must be a non-empty" in error for error in errors):
        raise AssertionError(f"Poppy closure accepted an evidence-free worker card: {errors}")
    packet = copy.deepcopy(closure)
    packet["postflight"].update(  # type: ignore[union-attr]
        {"evaluator": "fresh-worker", "evaluator_task_id": "fabricated-r0-evaluator", "independent": True}
    )
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("planned worker and closure card" in error for error in errors):
        raise AssertionError(f"Poppy R0 closure self-asserted an unplanned independent evaluator: {errors}")
    packet = copy.deepcopy(closure)
    packet["postflight"]["independent"] = True  # type: ignore[index]
    errors = validate_poppy_closure(packet, graph, plan)
    if not any("root evaluator cannot claim independent" in error for error in errors):
        raise AssertionError(f"Poppy root evaluator self-asserted independence: {errors}")
    packet = copy.deepcopy(closure)
    packet["risk"] = "R2"
    packet["postflight"].update(  # type: ignore[union-attr]
        {"evaluator": "fresh-worker", "evaluator_task_id": packet["root_task_id"], "independent": True}
    )
    errors = validate_poppy_closure(packet, graph)
    if not any("root task cannot claim independent" in error for error in errors):
        raise AssertionError(f"Poppy root claimed independent R2 evaluation: {errors}")

    poppy = (ROOT / "skills" / "poppy" / "SKILL.md").read_text(encoding="utf-8")
    evaluator = (ROOT / "skills" / "project-ops-evaluate" / "SKILL.md").read_text(encoding="utf-8")
    for required in (
        "trusted current user turn",
        "sole Project Operations counterpart",
        "join barrier",
        "NEEDS_PARENT_DECISION",
        "Explicit read-only, review-only, or diagnosis-only scope suppresses every vault write",
        "orchestration-run",
    ):
        if required.casefold() not in poppy.casefold():
            raise AssertionError(f"Poppy skill is missing {required}")
    for required in ("Readiness screen", "Substantive preflight", "Postflight", "Confidence never creates authority"):
        if required.casefold() not in evaluator.casefold():
            raise AssertionError(f"Poppy evaluator is missing {required}")


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

    poppy = (ROOT / "skills" / "poppy" / "SKILL.md").read_text(encoding="utf-8")
    if "../../references/task-orchestration.md" not in poppy:
        raise AssertionError("Poppy does not load the promoted task-orchestration contract")

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
    poppy_profile = copy.deepcopy(load_fixture("valid-project.json"))
    poppy_profile["controls"]["poppy"] = {  # type: ignore[index]
        "trigger_name": "Poppy",
        "substantive_memory": "required",
        "preflight": "required",
        "postflight": "required",
        "confidence_scale": ["high", "medium", "low", "insufficient"],
        "max_delegation_depth": 1,
        "max_active_workers": 2,
        "max_created_workers": 5,
    }
    profile_errors, _ = validate_profile(poppy_profile)
    if profile_errors:
        raise AssertionError(f"profile rejected safe Poppy controls: {profile_errors}")
    unsafe_poppy = copy.deepcopy(poppy_profile)
    unsafe_poppy["controls"]["poppy"]["max_delegation_depth"] = 2  # type: ignore[index]
    profile_errors, _ = validate_profile(unsafe_poppy)
    if not any("max_delegation_depth" in error for error in profile_errors):
        raise AssertionError(f"profile allowed Poppy controls to widen delegation: {profile_errors}")
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
    assert_poppy_orchestration()
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
            "templates/orchestration-run.md",
            "wiki/test-project/pm/records/improvements",
            "dashboards/Test Project Improvements.base",
            "wiki/test-project/pm/records/research",
            "raw/test-project/research",
            "dashboards/Test Project Research.base",
            "wiki/test-project/pm/records/authority",
            "wiki/test-project/pm/records/releases",
            "raw/test-project/pm-os/controls",
            "raw/test-project/pm-os/runs",
            "dashboards/Test Project Orchestration.base",
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
        orchestration_base = (vault / "dashboards/Test Project Orchestration.base").read_text(encoding="utf-8")
        if 'record_kind == "orchestration-run"' not in orchestration_base or "poppy" not in orchestration_base.casefold():
            raise AssertionError("generated Orchestration Base does not isolate Poppy orchestration receipts")
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
