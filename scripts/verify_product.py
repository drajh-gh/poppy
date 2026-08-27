#!/usr/bin/env python3
"""Canonical deterministic verification gate for the Poppy v3 skills-only plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_SOURCE = "85797ef39dfa641a87716d1c04d2613b67da7c22"
COCKPIT_SOURCE = "b7373b7ad3760243621bac2198f2b4c6ec4b9729"
REMOTE_SEED = "305efbd300a1c59ef0e84553b84638d0def22568"
V2_FREEZE = "7c4a7b3306319e9810c6e89bd6fb5e2bc97cda1e"
V2_TAG = "poppy-v2-final"

EXPECTED_SKILLS = {
    "poppy",
    "poppy-context",
    "poppy-operations",
    "poppy-delivery",
    "poppy-assure",
    "poppy-research",
    "poppy-learn",
}

EXPECTED_REFERENCES = {
    "architecture-and-design.md",
    "authority-and-effects.md",
    "decision-discovery.md",
    "delegation-and-delivery.md",
    "diagnosis-and-test-first-delivery.md",
    "domain-modeling.md",
    "evidence-and-assurance.md",
    "git-conflict-resolution.md",
    "human-guided-procedures.md",
    "operating-model.md",
    "operations.md",
    "project-context.md",
    "prototype-to-learn.md",
    "research-and-learning.md",
    "specification-and-tickets.md",
    "work-intake.md",
}

REQUIRED_SCENARIOS = {
    "S1_DIRECT_TINY_EDIT",
    "S2_ROUGH_FEATURE",
    "S3_DEFECT_FIX",
    "S4_UX_IMPROVEMENT",
    "S5_RESEARCH_DECISION",
    "S6_RELEASE_READINESS",
    "S7_MEETING_TO_ACTIONS",
    "S8_DURABLE_LESSON",
    "S9_PHASE_BOUNDARY_CONTINUE",
    "S10_DECISION_DISCOVERY_AND_WAYFINDING",
    "S11_ARCHITECTURE_ASSESSMENT_AND_DESIGN",
    "S12_PROTOTYPE_TO_LEARN",
    "S13_DIAGNOSIS_ONLY",
    "S14_LEGACY_CHARACTERIZATION",
    "S15_SPECIFICATION_TO_TICKET_PREVIEW",
    "S16_GIT_CONFLICT_RESOLUTION",
    "S17_WORK_INTAKE_TRIAGE",
    "S18_HUMAN_GUIDED_PROCEDURE",
    "S19_REQUEST_FIDELITY_AND_LANGUAGE",
    "S20_LEGACY_GATE_CHRONOLOGY",
}

REQUIRED_NEGATIVE_CASES = {
    "N1_PROFILE_NEVER_WIDENS_AUTHORITY",
    "N2_MISSING_MEMORY_CONTROL",
    "N3_NO_FALSE_HEALTH",
    "N4_SHORT_CONSEQUENTIAL_REQUEST",
    "N5_NO_UNAPPROVED_THIRD_PARTY_ACTION",
    "N6_PRESERVE_USER_CHANGES",
    "N7_ONE_WRITER",
    "N8_NON_POPPY_SESSION_UNCHANGED",
    "N9_SHARED_SURFACE_INTEGRITY",
    "N10_MALFORMED_PROJECT_IDENTITY",
    "N11_MALFORMED_MEMORY_POLICY",
    "N12_UNKNOWN_LEGACY_FIELDS",
    "N13_PROJECT_INDEX_EXACT_MATCH_CONTROL",
    "N14_PROJECT_INDEX_DUPLICATE_MATCH",
    "N15_PROJECT_INDEX_MALFORMED",
    "N16_ROUTING_SUMMARY_NOT_AUTHORITY",
    "N17_HANDOFF_PORTABILITY_ONLY",
    "N18_REVIEW_ACCEPTANCE_INTEGRITY",
    "N19_REVIEW_EVIDENCE_NOT_SCORE_OR_RUNTIME",
    "N20_DIAGNOSIS_WITHOUT_LOOP_OR_AUTHORITY",
    "N21_ARTIFACT_DISPOSITION_REQUIRES_AUTHORITY",
    "N22_DISCOVERY_DOMAIN_AND_CAPTURE_BOUNDARY",
    "N23_ARCHITECTURE_SELECTION_AND_NO_CHANGE",
    "N24_DESIGN_HEURISTICS_NOT_LAWS",
    "N25_PROTOTYPE_EXECUTION_OR_PROMOTION",
    "N26_NO_TEST_FIRST_DOGMA",
    "N27_SPEC_READINESS_AND_PUBLICATION_GATE",
    "N28_TICKET_PUBLICATION_AND_RECOVERY",
    "N29_UNTRUSTED_PR_BOUNDARY",
    "N30_TRACKER_EFFECT_NO_SHADOW_STATE",
    "N31_DECISION_MAP_NEVER_GRANTS_AUTHORITY",
    "N32_GIT_NO_AUTOMATIC_COMPLETION",
    "N33_HUMAN_PROCEDURE_EFFECT_SAFETY",
    "N34_OBSIDIAN_MEMORY_BOUNDARY",
}

EXPECTED_SOURCE_FILES = {
    ".codex-plugin/plugin.json",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "docs/constitution-v3.md",
    "docs/development.md",
    "docs/release.md",
    "references/authority-and-effects.md",
    "references/architecture-and-design.md",
    "references/decision-discovery.md",
    "references/delegation-and-delivery.md",
    "references/diagnosis-and-test-first-delivery.md",
    "references/domain-modeling.md",
    "references/evidence-and-assurance.md",
    "references/git-conflict-resolution.md",
    "references/human-guided-procedures.md",
    "references/operating-model.md",
    "references/operations.md",
    "references/project-context.md",
    "references/prototype-to-learn.md",
    "references/research-and-learning.md",
    "references/specification-and-tickets.md",
    "references/work-intake.md",
    "scripts/materialize_scenario.py",
    "scripts/verify_product.py",
    "skills/poppy/SKILL.md",
    "skills/poppy-assure/SKILL.md",
    "skills/poppy-context/SKILL.md",
    "skills/poppy-delivery/SKILL.md",
    "skills/poppy-learn/SKILL.md",
    "skills/poppy-operations/SKILL.md",
    "skills/poppy-research/SKILL.md",
    "tests/fixtures.json",
    "tests/scenarios.json",
}
LEGACY_ROOTS = {"apps", "assets", "examples", "schemas"}
LEGACY_FILES = {
    ".mcp.json",
    "references/poppy-capability-graph.json",
}


class VerificationError(RuntimeError):
    pass


def run(command: list[str], name: str) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=60,
    )
    if completed.returncode:
        raise VerificationError(f"{name} failed\n{completed.stdout}\n{completed.stderr}")
    return completed.stdout.strip()


def candidate_paths() -> list[Path]:
    output = run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        "candidate inventory",
    )
    return sorted((ROOT / line for line in output.splitlines() if line), key=lambda p: p.as_posix())


def candidate_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        payload = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def inventory_check(paths: list[Path]) -> dict:
    relative_paths = {path.relative_to(ROOT).as_posix() for path in paths}
    violations: list[str] = []
    if relative_paths != EXPECTED_SOURCE_FILES:
        violations.append(
            "source inventory mismatch: "
            f"missing={sorted(EXPECTED_SOURCE_FILES - relative_paths)}, "
            f"extra={sorted(relative_paths - EXPECTED_SOURCE_FILES)}"
        )
    for relative in relative_paths:
        first = relative.split("/", 1)[0]
        if first in LEGACY_ROOTS or relative in LEGACY_FILES:
            violations.append(f"legacy surface remains: {relative}")
        if relative.startswith(".codex/") or relative == "AGENTS.override.md":
            violations.append(f"repository-local personal installation/policy: {relative}")
        if relative.startswith("skills/project-ops-"):
            violations.append(f"removed v2 skill identity remains: {relative}")

    actual_skills = {
        path.parent.name
        for path in paths
        if path.name == "SKILL.md" and path.parent.parent == ROOT / "skills"
    }
    if actual_skills != EXPECTED_SKILLS:
        violations.append(
            f"skill inventory mismatch: expected {sorted(EXPECTED_SKILLS)}, got {sorted(actual_skills)}"
        )
    actual_skill_files = {
        path.relative_to(ROOT).as_posix()
        for path in paths
        if path.relative_to(ROOT).as_posix().startswith("skills/")
    }
    expected_skill_files = {f"skills/{name}/SKILL.md" for name in EXPECTED_SKILLS}
    if actual_skill_files != expected_skill_files:
        violations.append(
            f"skill package files mismatch: expected {sorted(expected_skill_files)}, got {sorted(actual_skill_files)}"
        )

    actual_references = {
        path.name for path in paths if path.parent == ROOT / "references"
    }
    if actual_references != EXPECTED_REFERENCES:
        violations.append(
            f"reference inventory mismatch: expected {sorted(EXPECTED_REFERENCES)}, got {sorted(actual_references)}"
        )

    if violations:
        raise VerificationError("Inventory check failed:\n" + "\n".join(sorted(violations)))
    return {
        "name": "exact skills-only inventory",
        "status": "pass",
        "files": len(paths),
        "skills": sorted(EXPECTED_SKILLS),
    }


def manifest_check() -> dict:
    path = ROOT / ".codex-plugin" / "plugin.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {"name", "version", "description", "author", "skills", "interface"}
    if set(manifest) != required:
        raise VerificationError(
            f"Manifest keys must be exactly {sorted(required)}, got {sorted(manifest)}"
        )
    if manifest["name"] != "project-operations" or manifest["skills"] != "./skills/":
        raise VerificationError("Manifest package identity or skills path is invalid")
    if not re.fullmatch(r"0\.3\.0\+codex\.\d{14}", manifest["version"]):
        raise VerificationError(f"Manifest version is not a v3 local candidate: {manifest['version']}")
    component_fields = {"skills", "mcpServers", "apps", "ui", "commands", "hooks"}
    exposed = component_fields.intersection(manifest)
    if exposed != {"skills"}:
        raise VerificationError(f"Manifest must expose only skills, got {sorted(exposed)}")
    return {
        "name": "skills-only plugin manifest",
        "status": "pass",
        "version": manifest["version"],
    }


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise VerificationError(f"Missing YAML frontmatter: {path.relative_to(ROOT)}")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise VerificationError(f"Malformed YAML frontmatter: {path.relative_to(ROOT)}") from exc
    values: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise VerificationError(f"Unsupported frontmatter line in {path.relative_to(ROOT)}: {line}")
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def skill_check() -> dict:
    for name in EXPECTED_SKILLS:
        path = ROOT / "skills" / name / "SKILL.md"
        values = parse_frontmatter(path)
        if set(values) != {"name", "description"}:
            raise VerificationError(f"Skill frontmatter keys invalid for {name}: {sorted(values)}")
        if values["name"] != name:
            raise VerificationError(f"Skill name mismatch for {name}: {values['name']}")
        if not (20 <= len(values["description"]) <= 1024):
            raise VerificationError(f"Skill description length invalid for {name}")
        if not re.fullmatch(r"[a-z0-9-]{1,64}", values["name"]):
            raise VerificationError(f"Skill name syntax invalid for {name}")
        description = values["description"].casefold()
        if name == "poppy":
            if "use automatically" not in description or "use behind poppy" in description:
                raise VerificationError("Root skill must be the only automatic entrypoint")
        elif (
            "use behind poppy" not in description
            or "directly invokable for focused testing" not in description
            or "use automatically" in description
        ):
            raise VerificationError(
                f"Supporting skill must be root-routed and test-invokable: {name}"
            )
    return {"name": "skill frontmatter", "status": "pass", "count": len(EXPECTED_SKILLS)}


def linked_reference_check(paths: list[Path]) -> dict:
    markdown = [path for path in paths if path.suffix.casefold() == ".md"]
    linked_references: set[str] = set()
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in markdown:
        text = path.read_text(encoding="utf-8")
        for raw in link_pattern.findall(text):
            target = raw.strip().strip("<>").split("#", 1)[0]
            if not target or re.match(r"^[a-z]+://", target, re.IGNORECASE):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError as exc:
                raise VerificationError(
                    f"Link escapes product root in {path.relative_to(ROOT)}: {raw}"
                ) from exc
            if not resolved.is_file():
                raise VerificationError(f"Broken link in {path.relative_to(ROOT)}: {raw}")
            if resolved.parent == ROOT / "references":
                linked_references.add(resolved.name)
    if linked_references != EXPECTED_REFERENCES:
        raise VerificationError(
            f"Every reference must be progressively linked; got {sorted(linked_references)}"
        )
    return {
        "name": "progressive reference links",
        "status": "pass",
        "references": sorted(linked_references),
    }


def boundary_check(paths: list[Path]) -> dict:
    forbidden_identities = ("slo" + "ski", "ever" + "away", "orod" + "jarna")
    deprecated_evidence_label = "gr" + "ay"
    retired_project_identity = "project" + " os"
    retired_project_slug = "project" + "-os"
    slash = "/"
    backslash = chr(92)
    forbidden_machine_paths = (
        "c:" + backslash + "users" + backslash + "david",
        slash.join(("c:", "users", "david")),
        "c:" + backslash + "va" + "ults",
        slash.join(("c:", "va" + "ults")),
    )
    credential = re.compile(
        r"['\"]?(?:api[_-]?key|client[_-]?secret|access[_-]?token|password|private[_-]?key)['\"]?"
        r"\s*[:=]\s*['\"]?(?!<|example|synthetic|none|null)[a-z0-9_./+=-]{8,}",
        re.IGNORECASE,
    )
    absolute_paths = (
        re.compile(r"(?<![a-z0-9])(?:[a-z]:[\\/]|\\\\[^\\\s]+\\[^\\\s]+)", re.IGNORECASE),
        re.compile(r"(?<![a-z0-9])/(?:home|users|volumes|mnt|var|etc)/", re.IGNORECASE),
    )
    secret_shapes = (
        re.compile(r"(?<![a-z0-9])sk-[a-z0-9_-]{16,}", re.IGNORECASE),
        re.compile(r"(?<![a-z0-9])ghp_[a-z0-9]{20,}", re.IGNORECASE),
        re.compile(r"(?<![a-z0-9])github_pat_[a-z0-9_]{20,}", re.IGNORECASE),
        re.compile(r"(?<![a-z0-9])akia[a-z0-9]{12,}", re.IGNORECASE),
    )
    positive_credential_samples = (
        json.dumps({"api_" + "key": "a" * 16}),
        json.dumps({"pass" + "word": "b" * 16}),
        ("access_" + "token") + "=" + ("c" * 20),
    )
    negative_credential_samples = (
        json.dumps({"api_" + "key": "<redacted>"}),
        json.dumps({"pass" + "word": None}),
        json.dumps({"client_" + "secret": "synthetic"}),
    )
    if not all(credential.search(sample) for sample in positive_credential_samples):
        raise VerificationError("Credential detector failed a required positive self-test")
    if any(credential.search(sample) for sample in negative_credential_samples):
        raise VerificationError("Credential detector failed a required negative self-test")
    violations: list[str] = []
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.casefold() not in {".md", ".json", ".py"}:
            continue
        text = path.read_text(encoding="utf-8").casefold()
        for token in (*forbidden_identities, *forbidden_machine_paths):
            if token in text:
                violations.append(f"forbidden identity or machine path in {relative}: {token}")
        if any(pattern.search(text) for pattern in absolute_paths):
            violations.append(f"generic absolute machine path in {relative}")
        if re.search(rf"\b{deprecated_evidence_label}\b", text):
            violations.append(f"deprecated evidence label in {relative}")
        if retired_project_identity in text or retired_project_slug in text:
            violations.append(f"retired project identity in {relative}")
        if credential.search(text):
            violations.append(f"credential-shaped assignment in {relative}")
        if any(pattern.search(text) for pattern in secret_shapes):
            violations.append(f"secret-shaped token prefix in {relative}")
    if violations:
        raise VerificationError("Product boundary check failed:\n" + "\n".join(sorted(violations)))
    return {"name": "project and secret boundary", "status": "pass", "files": len(paths)}


def policy_check() -> dict:
    root = (ROOT / "skills" / "poppy" / "SKILL.md").read_text(encoding="utf-8").casefold()
    combined = "\n".join(
        path.read_text(encoding="utf-8").casefold()
        for path in sorted([*(ROOT / "skills").glob("*/SKILL.md"), *(ROOT / "references").glob("*.md")])
    )
    required_root = (
        "simple question or truly trivial reversible edit",
        "short consequential request",
        "start from the user's situation and desired next decision",
        "routing summaries orient; specialist sources govern",
        "native ephemeral task plan",
        "profiles and confidence can narrow authority but never expand it",
        "named target and effect, preview, exact approval, read-back verification, and rollback path",
        "preserve existing user changes",
        "leaves the affected claim unverified",
        "leaves it conflicted",
        "standing personal preference for adaptive sub-agent use",
        "keep the originating request as the acceptance anchor",
    )
    required_combined = (
        "one writer per target",
        "isolated worktree",
        "research authority is read-only",
        "tracker state in the tracker",
        "diagnosis-only",
        "writes remain blocked",
        "specification fidelity",
        "repository conformance",
        "handoff only when work must travel",
        "production instrumentation is prohibited",
        "raw receipts are immutable",
        "never mandate `context.md`",
        "a justified no-change outcome",
        "execution alone is not validation",
        "never automatically applies `ready-for-agent`",
        "never use `git add .`",
        "a skipped or failed stage is not success",
        "evidence gathering serves the acceptance anchor",
        "compare record creation and transition history",
        "working response language distinct from the language and register",
    )
    missing = [phrase for phrase in required_root if phrase not in root]
    missing += [phrase for phrase in required_combined if phrase not in combined]
    if missing:
        raise VerificationError("Required behavioral invariants missing:\n" + "\n".join(missing))
    return {"name": "behavioral invariants", "status": "pass"}


def scenario_check() -> dict:
    catalog = json.loads((ROOT / "tests" / "scenarios.json").read_text(encoding="utf-8"))
    fixtures = json.loads((ROOT / "tests" / "fixtures.json").read_text(encoding="utf-8"))
    scenarios = catalog.get("scenarios", [])
    negative = catalog.get("negative_cases", [])
    if {item.get("id") for item in scenarios} != REQUIRED_SCENARIOS:
        raise VerificationError("Required mixed-scenario identifiers are incomplete or renamed")
    if {item.get("id") for item in negative} != REQUIRED_NEGATIVE_CASES:
        raise VerificationError("Required negative-control identifiers are incomplete or renamed")
    required_fields = {
        "id",
        "prompt",
        "permitted_effects",
        "expected_evidence_limits",
        "observable_assertions",
    }
    for item in [*scenarios, *negative]:
        if set(item) != required_fields:
            raise VerificationError(f"Scenario fields invalid for {item.get('id')}")
        if not item["prompt"].strip() or not item["permitted_effects"] or not item["observable_assertions"]:
            raise VerificationError(f"Scenario content incomplete for {item['id']}")
        if not item["expected_evidence_limits"].strip():
            raise VerificationError(f"Scenario lacks explicit evidence limits: {item['id']}")
    template = catalog.get("execution", {}).get("evidence_capture_template", {})
    required_template = {
        "scenario_id",
        "plugin_version",
        "source_revision",
        "candidate_digest",
        "task_id",
        "started_at",
        "observed_effects",
        "assertions",
        "shared_surface_digest_before",
        "shared_surface_digest_after",
        "verdict",
    }
    if set(template) != required_template:
        raise VerificationError("Evidence-capture template is incomplete")
    if catalog.get("execution", {}).get("fresh_task_required") is not True:
        raise VerificationError("Scenario catalog must require fresh tasks")
    all_ids = REQUIRED_SCENARIOS | REQUIRED_NEGATIVE_CASES
    if set(fixtures) != {"fixture_version", "purpose", "fixtures"}:
        raise VerificationError("Fixture catalog top-level fields are invalid")
    if set(fixtures.get("fixtures", {})) != all_ids:
        raise VerificationError("Every scenario must have one exact self-contained fixture")
    materializer = json.loads(
        run([sys.executable, "scripts/materialize_scenario.py", "--verify-catalog"], "scenario materializer")
    )
    if materializer.get("status") != "pass" or materializer.get("scenarios") != len(all_ids):
        raise VerificationError("Scenario materializer did not verify the complete catalog")
    return {
        "name": "synthetic scenario contract",
        "status": "pass",
        "mixed_scenarios": len(scenarios),
        "negative_controls": len(negative),
        "self_contained_fixtures": materializer["scenarios"],
    }


def ancestry_check() -> dict:
    ancestors = [CORE_SOURCE, COCKPIT_SOURCE, REMOTE_SEED, V2_FREEZE]
    for revision in ancestors:
        run(["git", "merge-base", "--is-ancestor", revision, "HEAD"], f"ancestry {revision}")
    peeled = run(["git", "rev-parse", f"{V2_TAG}^{{}}"], "v2 rollback tag")
    if peeled != V2_FREEZE:
        raise VerificationError(f"{V2_TAG} points to {peeled}, expected {V2_FREEZE}")
    tag_type = run(["git", "cat-file", "-t", V2_TAG], "v2 rollback tag type")
    if tag_type != "tag":
        raise VerificationError(f"{V2_TAG} must be an annotated tag, got {tag_type}")
    return {
        "name": "four-history ancestry and local rollback tag",
        "status": "pass",
        "ancestors": ancestors,
        "v2_tag": V2_TAG,
    }


def syntax_check(paths: list[Path]) -> dict:
    for path in paths:
        if path.suffix.casefold() == ".py":
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        elif path.suffix.casefold() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
    return {"name": "Python and JSON syntax", "status": "pass"}


def clean_check() -> dict:
    status = run(["git", "status", "--porcelain=v2"], "clean candidate")
    if status:
        raise VerificationError("Candidate tree is not clean:\n" + status)
    return {"name": "clean committed candidate", "status": "pass"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="Require a separately authorized committed, clean candidate.",
    )
    args = parser.parse_args(argv)
    paths = candidate_paths()
    checks = [
        manifest_check(),
        inventory_check(paths),
        skill_check(),
        linked_reference_check(paths),
        boundary_check(paths),
        policy_check(),
        scenario_check(),
        syntax_check(paths),
        ancestry_check(),
    ]
    if args.require_clean:
        checks.append(clean_check())
    result = {
        "status": "pass",
        "product": "Poppy v3",
        "source_head": run(["git", "rev-parse", "HEAD"], "source identity"),
        "branch": run(["git", "branch", "--show-current"], "branch identity"),
        "candidate_digest_sha256": candidate_digest(paths),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, json.JSONDecodeError, OSError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
