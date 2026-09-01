#!/usr/bin/env python3
"""Canonical deterministic verification gate for the Poppy v3 skill-and-hook plugin."""

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
CANDIDATE_DIGEST_ALGORITHM = "sha256(relative-path-nul-git-filtered-blob-oid-nul)"

EXPECTED_SKILLS = {
    "poppy",
    "poppy-context",
    "poppy-intake",
    "poppy-decide",
    "poppy-coordinate",
    "poppy-research",
    "poppy-diagnose",
    "poppy-delivery",
    "poppy-acceptance",
    "poppy-assure",
    "poppy-learn",
    "poppy-housekeeping",
}

EXPECTED_REFERENCES = {
    "architecture-assessment.md",
    "authority-and-effects.md",
    "client-acceptance.md",
    "communication-and-writing.md",
    "decision-discovery.md",
    "delegation-and-continuity.md",
    "diagnosis.md",
    "domain-modeling.md",
    "durable-learning.md",
    "engineering-delivery.md",
    "evidence-and-assurance.md",
    "external-research.md",
    "git-conflict-resolution.md",
    "human-guided-procedures.md",
    "implementation-design.md",
    "operating-model.md",
    "operations.md",
    "process-observation.md",
    "project-context.md",
    "prototype-to-learn.md",
    "specification.md",
    "test-first-delivery.md",
    "work-intake.md",
    "work-items.md",
    "task-housekeeping.md",
}

REFERENCE_OWNERS = {
    "architecture-assessment.md": "poppy-decide",
    "authority-and-effects.md": "poppy",
    "client-acceptance.md": "poppy-acceptance",
    "communication-and-writing.md": "poppy",
    "decision-discovery.md": "poppy-decide",
    "delegation-and-continuity.md": "poppy",
    "diagnosis.md": "poppy-diagnose",
    "domain-modeling.md": "poppy-decide",
    "durable-learning.md": "poppy-learn",
    "engineering-delivery.md": "poppy-delivery",
    "evidence-and-assurance.md": "poppy-assure",
    "external-research.md": "poppy-research",
    "git-conflict-resolution.md": "poppy-delivery",
    "human-guided-procedures.md": "poppy-coordinate",
    "implementation-design.md": "poppy-delivery",
    "operating-model.md": "poppy",
    "operations.md": "poppy-coordinate",
    "process-observation.md": "poppy",
    "project-context.md": "poppy-context",
    "prototype-to-learn.md": "poppy-delivery",
    "specification.md": "poppy-decide",
    "test-first-delivery.md": "poppy-delivery",
    "work-intake.md": "poppy-intake",
    "work-items.md": "poppy-coordinate",
    "task-housekeeping.md": "poppy-housekeeping",
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
    "S21_PRE_PR_VISUAL_ACCEPTANCE",
    "S22_CLIENT_REPORT_READINESS_BOUNDARY",
    "S23_BATCH_TRIAGE_DECISION_READY",
    "S24_DELEGATED_JOIN_FIDELITY",
    "S25_ARTIFACT_AND_CONTEXT_CHECKPOINT",
    "S26_PREPARED_APPROVAL_AND_REUSE",
    "S27_BLOCKING_GATE_INTEGRITY",
    "S28_CALIBRATED_EVIDENCE_RECOMMENDATION",
    "S29_PENDING_CLIENT_RECORDING_CHECKPOINT",
    "S30_CLIENT_READY_ACCEPTANCE_RECORDING",
    "S31_CONSUMER_READY_COMMUNICATION",
    "S32_CONDITIONAL_PROJECT_ORIENTATION",
    "S33_VISIBLE_POPPY_SIGNATURE",
    "S34_TRANSIENT_COURSE_CORRECTION",
    "S35_VERIFICATION_AVOIDS_GENERATED_ARTIFACTS",
    "S36_ACTIVE_POPPY_IDENTITY",
    "S37_TASK_HOUSEKEEPING",
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
    "N35_VISUAL_ACCEPTANCE_NOT_PR_AUTHORITY",
    "N36_INCIDENT_DOES_NOT_AUTHORIZE_PREVENTION",
    "N37_QUEUE_THROUGHPUT_NOT_COMPLETION",
    "N38_FULL_HISTORY_AND_VISIBLE_TASK_SPRAWL",
    "N39_ADJACENT_CHILD_RESULT_NOT_JOINED",
    "N40_EPHEMERAL_CANDIDATE_NOT_COMPLETE",
    "N41_APPROVAL_NOT_DEBUGGING_OR_INCANTATION",
    "N42_UNCALIBRATED_CONFIDENCE_AND_GATE_DRIFT",
    "N43_UNSLOP_PRESERVES_SOURCE_FIDELITY",
    "N44_STYLE_HEURISTICS_NOT_LAWS",
    "N45_SIGNATURE_ARTIFACT_BOUNDARY",
    "N46_BLIND_RETRY_IS_NOT_PROGRESS",
    "N47_PROCESS_OBSERVATIONS_STAY_TRANSIENT",
    "N48_CACHE_ORDER_IS_NOT_ACTIVATION",
    "N49_PROJECT_INDEX_NO_MATCH_STAYS_CLOSED",
    "N50_HOUSEKEEPING_ARCHIVE_FAILS_CLOSED",
}

EXPECTED_SOURCE_FILES = {
    ".codex-plugin/plugin.json",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "docs/agent-skill-authoring-reference.md",
    "docs/constitution-v3.md",
    "docs/development.md",
    "docs/release.md",
    "hooks/hooks.json",
    "hooks/housekeeping_hook.py",
    "references/authority-and-effects.md",
    "references/architecture-assessment.md",
    "references/client-acceptance.md",
    "references/communication-and-writing.md",
    "references/decision-discovery.md",
    "references/delegation-and-continuity.md",
    "references/diagnosis.md",
    "references/domain-modeling.md",
    "references/durable-learning.md",
    "references/engineering-delivery.md",
    "references/evidence-and-assurance.md",
    "references/external-research.md",
    "references/git-conflict-resolution.md",
    "references/human-guided-procedures.md",
    "references/implementation-design.md",
    "references/operating-model.md",
    "references/operations.md",
    "references/process-observation.md",
    "references/project-context.md",
    "references/prototype-to-learn.md",
    "references/specification.md",
    "references/test-first-delivery.md",
    "references/task-housekeeping.md",
    "references/work-intake.md",
    "references/work-items.md",
    "scripts/materialize_scenario.py",
    "scripts/verify_product.py",
    "skills/poppy/SKILL.md",
    "skills/poppy-assure/SKILL.md",
    "skills/poppy-acceptance/SKILL.md",
    "skills/poppy-context/SKILL.md",
    "skills/poppy-coordinate/SKILL.md",
    "skills/poppy-decide/SKILL.md",
    "skills/poppy-delivery/SKILL.md",
    "skills/poppy-diagnose/SKILL.md",
    "skills/poppy-intake/SKILL.md",
    "skills/poppy-learn/SKILL.md",
    "skills/poppy-housekeeping/SKILL.md",
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
    return sorted(
        (ROOT / line for line in output.splitlines() if line and (ROOT / line).is_file()),
        key=lambda p: p.as_posix(),
    )


def candidate_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        blob_oid = run(
            ["git", "hash-object", f"--path={relative}", "--", relative],
            f"candidate blob {relative}",
        )
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(blob_oid.encode("ascii"))
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
        "name": "exact skill-and-hook inventory",
        "status": "pass",
        "files": len(paths),
        "skills": sorted(EXPECTED_SKILLS),
    }


def manifest_check() -> dict:
    path = ROOT / ".codex-plugin" / "plugin.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = {"name", "version", "description", "author", "skills", "hooks", "interface"}
    if set(manifest) != required:
        raise VerificationError(
            f"Manifest keys must be exactly {sorted(required)}, got {sorted(manifest)}"
        )
    if (
        manifest["name"] != "project-operations"
        or manifest["skills"] != "./skills/"
        or manifest["hooks"] != "./hooks/hooks.json"
    ):
        raise VerificationError("Manifest package identity, skills path, or hooks path is invalid")
    if not re.fullmatch(r"0\.3\.0\+codex\.\d{14}", manifest["version"]):
        raise VerificationError(f"Manifest version is not a v3 local candidate: {manifest['version']}")
    component_fields = {"skills", "mcpServers", "apps", "ui", "commands", "hooks"}
    exposed = component_fields.intersection(manifest)
    if exposed != {"skills", "hooks"}:
        raise VerificationError(f"Manifest must expose only skills and hooks, got {sorted(exposed)}")
    return {
        "name": "skill-and-hook plugin manifest",
        "status": "pass",
        "version": manifest["version"],
    }


def execute_hook(event: dict) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "hooks" / "housekeeping_hook.py")],
        cwd=ROOT,
        input=json.dumps(event, ensure_ascii=False),
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=5,
    )
    if completed.returncode != 0:
        raise VerificationError(
            f"Housekeeping hook exited {completed.returncode}: {completed.stderr.strip()}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise VerificationError(
            f"Housekeeping hook returned invalid JSON: {completed.stdout!r}"
        ) from exc
    if not isinstance(result, dict):
        raise VerificationError("Housekeeping hook output must be a JSON object")
    return result


def hook_contract_check() -> dict:
    config_path = ROOT / "hooks" / "hooks.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if set(config) != {"description", "hooks"} or not config["description"].strip():
        raise VerificationError("Hook config metadata is incomplete")
    hooks = config["hooks"]
    expected_events = {"SessionStart", "PreToolUse", "PostToolUse"}
    if set(hooks) != expected_events:
        raise VerificationError(
            f"Hook event inventory mismatch: expected {sorted(expected_events)}, got {sorted(hooks)}"
        )
    expected_matchers = {
        "SessionStart": "^(resume|compact)$",
        "PreToolUse": "^mcp__codex_app__(set_thread_title|set_thread_archived)$",
        "PostToolUse": "^mcp__codex_app__(set_thread_title|set_thread_archived)$",
    }
    for event_name, groups in hooks.items():
        if not isinstance(groups, list) or len(groups) != 1:
            raise VerificationError(f"Hook event must have one matcher group: {event_name}")
        group = groups[0]
        expected_group_fields = {"matcher", "hooks"}
        if set(group) != expected_group_fields:
            raise VerificationError(f"Hook matcher group fields invalid for {event_name}")
        if group["matcher"] != expected_matchers[event_name]:
            raise VerificationError(f"Hook matcher is not narrowly pinned for {event_name}")
        handlers = group["hooks"]
        if not isinstance(handlers, list) or len(handlers) != 1:
            raise VerificationError(f"Hook event must have one command handler: {event_name}")
        handler = handlers[0]
        required_handler_fields = {
            "type",
            "command",
            "commandWindows",
            "timeout",
            "additionalContextLimit",
        }
        if set(handler) != required_handler_fields:
            raise VerificationError(f"Hook handler fields invalid for {event_name}")
        if (
            handler["type"] != "command"
            or handler["timeout"] != 3
            or "$PLUGIN_ROOT/hooks/housekeeping_hook.py" not in handler["command"]
            or "%PLUGIN_ROOT%\\hooks\\housekeeping_hook.py" not in handler["commandWindows"]
        ):
            raise VerificationError(f"Hook handler is not bounded and plugin-relative for {event_name}")
        if handler["additionalContextLimit"] != 240:
            raise VerificationError(f"Hook context limit is not bounded for {event_name}")

    script = (ROOT / "hooks" / "housekeeping_hook.py").read_text(encoding="utf-8")
    forbidden_runtime_tokens = (
        "transcript_path",
        "PLUGIN_DATA",
        "urllib",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "Path(",
    )
    found = [token for token in forbidden_runtime_tokens if token in script]
    if found:
        raise VerificationError(
            "Housekeeping hook must remain transcript-free, network-free, and stateless: "
            + ", ".join(found)
        )

    resume = execute_hook({"hook_event_name": "SessionStart", "source": "resume"})
    resume_context = resume.get("hookSpecificOutput", {}).get("additionalContext", "")
    if "Poppy Housekeeping" not in resume_context or "Clear the marker" not in resume_context:
        raise VerificationError("SessionStart hook does not preserve reopen semantics")

    invalid_title = execute_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__codex_app__set_thread_title",
            "tool_input": {"threadId": "synthetic-task-1", "title": "✅ [D] 🚧 [B] Atlas"},
        }
    )
    if invalid_title.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
        raise VerificationError("PreToolUse hook did not reject a stacked lifecycle marker")

    valid_title = execute_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__codex_app__set_thread_title",
            "tool_input": {"threadId": "synthetic-task-1", "title": "✅ [D] Atlas review"},
        }
    )
    if "additionalContext" not in valid_title.get("hookSpecificOutput", {}):
        raise VerificationError("PreToolUse hook did not admit an exact lifecycle marker with context")

    implicit_archive = execute_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "mcp__codex_app__set_thread_archived",
            "tool_input": {"archived": True},
        }
    )
    if implicit_archive.get("hookSpecificOutput", {}).get("permissionDecision") != "deny":
        raise VerificationError("PreToolUse hook did not require an exact archive target")

    post_title = execute_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "mcp__codex_app__set_thread_title",
            "tool_input": {"threadId": "synthetic-task-1", "title": "✅ [D] Atlas review"},
            "tool_response": {"status": "ok"},
        }
    )
    if "read the authoritative task title back" not in post_title.get("hookSpecificOutput", {}).get("additionalContext", ""):
        raise VerificationError("PostToolUse hook does not require title read-back")

    return {
        "name": "stateless Housekeeping hook contract",
        "status": "pass",
        "events": sorted(expected_events),
        "representative_payloads": 5,
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


def active_poppy_identity_contract_check() -> dict:
    root_skill = (ROOT / "skills" / "poppy" / "SKILL.md").read_text(encoding="utf-8")
    context_skill = (ROOT / "skills" / "poppy-context" / "SKILL.md").read_text(encoding="utf-8")
    context_reference = (ROOT / "references" / "project-context.md").read_text(encoding="utf-8")
    release_policy = (ROOT / "docs" / "release.md").read_text(encoding="utf-8")
    required_markers = {
        "root routing": (root_skill, "loaded root `SKILL.md`"),
        "active anchor": (context_skill, "loaded root `SKILL.md`"),
        "manifest resolution": (context_reference, "nearest ancestor `.codex-plugin/plugin.json`"),
        "cache ordering boundary": (context_reference, "Cache presence or version ordering is not activation evidence."),
        "separate candidate identities": (context_reference, "Pin the active package and repository candidate separately"),
        "installation proof": (release_policy, "loaded root `SKILL.md` path"),
    }
    missing = [name for name, (text, marker) in required_markers.items() if marker not in text]
    if missing:
        raise VerificationError(
            "Active Poppy identity contract is incomplete: " + ", ".join(sorted(missing))
        )
    return {
        "name": "active Poppy package and repository identity separation",
        "status": "pass",
    }


def linked_reference_check(paths: list[Path]) -> dict:
    skill_entrypoints = [
        path
        for path in paths
        if path.name == "SKILL.md" and path.parent.parent == ROOT / "skills"
    ]
    entrypoint_set = set(skill_entrypoints)
    markdown = [path for path in paths if path.suffix.casefold() == ".md"]
    linked_references: set[str] = set()
    links_by_skill: dict[str, set[str]] = {name: set() for name in EXPECTED_SKILLS}
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
            if path in entrypoint_set and resolved.parent == ROOT / "references":
                linked_references.add(resolved.name)
                links_by_skill[path.parent.name].add(resolved.name)
    if linked_references != EXPECTED_REFERENCES:
        raise VerificationError(
            f"Every reference must be progressively linked; got {sorted(linked_references)}"
        )
    if set(REFERENCE_OWNERS) != EXPECTED_REFERENCES:
        raise VerificationError("Every reference must have one declared primary owner")
    ownership_violations = [
        f"{reference} is not directly linked by declared owner {owner}"
        for reference, owner in sorted(REFERENCE_OWNERS.items())
        if reference not in links_by_skill[owner]
    ]
    if ownership_violations:
        raise VerificationError(
            "Reference ownership check failed:\n" + "\n".join(ownership_violations)
        )
    return {
        "name": "owned entrypoint-reachable progressive references",
        "status": "pass",
        "references": sorted(linked_references),
        "owners": REFERENCE_OWNERS,
    }


def provenance_check(paths: list[Path]) -> dict:
    github_url = re.compile(r"https://github\.com/[^\s)>\]]+")
    immutable_blob = re.compile(r"/blob/[0-9a-f]{40}/")
    violations: list[str] = []
    links = 0
    for path in paths:
        if path.parent != ROOT / "references" or path.suffix.casefold() != ".md":
            continue
        for url in github_url.findall(path.read_text(encoding="utf-8")):
            links += 1
            if not immutable_blob.search(url):
                violations.append(f"mutable GitHub provenance in {path.name}: {url}")
    if not links:
        raise VerificationError("No pinned GitHub provenance links found")
    if violations:
        raise VerificationError("Provenance check failed:\n" + "\n".join(sorted(violations)))
    return {"name": "immutable source provenance", "status": "pass", "links": links}


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
    scanned = 0
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix.casefold() not in {".md", ".json", ".py"} and path.name != ".gitignore":
            continue
        scanned += 1
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
    return {"name": "project and secret boundary", "status": "pass", "files_scanned": scanned}


def scenario_check() -> dict:
    catalog = json.loads((ROOT / "tests" / "scenarios.json").read_text(encoding="utf-8"))
    fixtures = json.loads((ROOT / "tests" / "fixtures.json").read_text(encoding="utf-8"))
    scenarios = catalog.get("scenarios", [])
    negative = catalog.get("negative_cases", [])
    if catalog.get("catalog_version") != 2:
        raise VerificationError("Scenario catalog version must be 2")
    if {item.get("id") for item in scenarios} != REQUIRED_SCENARIOS:
        raise VerificationError("Required mixed-scenario identifiers are incomplete or renamed")
    if {item.get("id") for item in negative} != REQUIRED_NEGATIVE_CASES:
        raise VerificationError("Required negative-control identifiers are incomplete or renamed")
    routing = catalog.get("routing_expectations", {})
    if set(routing) != {"purpose", "candidate_smoke", "sequences"}:
        raise VerificationError("Routing-expectation contract is incomplete")
    candidate_smoke = routing["candidate_smoke"]
    required_smoke_fields = {
        "maximum_fresh_tasks",
        "maximum_elapsed_minutes",
        "baseline_arm_required",
        "automatic_expansion_forbidden",
        "rerun_policy",
    }
    if (
        set(candidate_smoke) != required_smoke_fields
        or candidate_smoke["maximum_fresh_tasks"] != 3
        or candidate_smoke["maximum_elapsed_minutes"] != 30
        or candidate_smoke["baseline_arm_required"] is not False
        or candidate_smoke["automatic_expansion_forbidden"] is not True
        or not candidate_smoke["rerun_policy"].strip()
    ):
        raise VerificationError("Candidate-only routing smoke must remain bounded and non-comparative")
    sequences = routing["sequences"]
    if set(sequences) != REQUIRED_SCENARIOS:
        raise VerificationError("Every mixed scenario must declare one primary-owner sequence")
    allowed_owners = EXPECTED_SKILLS | {"root-direct"}
    for case_id, sequence in sequences.items():
        if (
            not isinstance(sequence, list)
            or not sequence
            or any(owner not in allowed_owners for owner in sequence)
            or ("root-direct" in sequence and sequence != ["root-direct"])
        ):
            raise VerificationError(f"Routing sequence invalid for {case_id}: {sequence}")
    required_boundaries = {
        "S1_DIRECT_TINY_EDIT": ["root-direct"],
        "S3_DEFECT_FIX": ["poppy-diagnose", "poppy-delivery"],
        "S6_RELEASE_READINESS": ["poppy-assure"],
        "S7_MEETING_TO_ACTIONS": ["poppy-coordinate"],
        "S10_DECISION_DISCOVERY_AND_WAYFINDING": ["poppy-decide"],
        "S13_DIAGNOSIS_ONLY": ["poppy-diagnose"],
        "S17_WORK_INTAKE_TRIAGE": ["poppy-intake"],
        "S21_PRE_PR_VISUAL_ACCEPTANCE": ["poppy-delivery", "poppy-acceptance"],
        "S22_CLIENT_REPORT_READINESS_BOUNDARY": ["poppy-intake", "poppy-decide"],
        "S30_CLIENT_READY_ACCEPTANCE_RECORDING": ["poppy-acceptance"],
        "S37_TASK_HOUSEKEEPING": ["poppy-housekeeping"],
    }
    for case_id, expected in required_boundaries.items():
        if sequences.get(case_id) != expected:
            raise VerificationError(
                f"Required ownership boundary changed for {case_id}: {sequences.get(case_id)}"
            )
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
        "arm",
        "model",
        "reasoning_effort",
        "plugin_version",
        "source_revision",
        "candidate_digest_algorithm",
        "candidate_digest",
        "task_id",
        "started_at",
        "completed_at",
        "fixture_digest",
        "behavior_input_sha256",
        "behavior_prompt_sha256",
        "judge_prompt_sha256_by_order",
        "tool_trace",
        "loaded_skill_reference_bytes",
        "loaded_skill_reference_files",
        "tool_calls",
        "turns",
        "observed_effects",
        "deterministic_results",
        "assertions",
        "blind_judge",
        "human_adjudication",
        "limitations",
        "shared_surface_digest_before",
        "shared_surface_digest_after",
        "verdict",
    }
    if set(template) != required_template:
        raise VerificationError("Evidence-capture template is incomplete")
    if catalog.get("execution", {}).get("fresh_task_required") is not True:
        raise VerificationError("Scenario catalog must require fresh tasks")
    behavior_input = catalog.get("execution", {}).get("behavior_input", {})
    required_behavior_input = {
        "case_fields",
        "fixture_fields",
        "grading_only_fields",
        "read_only_fresh_empty_directory",
        "behavior_prompt_hash_required",
        "judge_prompt_hash_required",
    }
    if set(behavior_input) != required_behavior_input:
        raise VerificationError("Behavior-input isolation contract is incomplete")
    if behavior_input["case_fields"] != ["prompt"] or behavior_input["fixture_fields"] != ["files", "evidence"]:
        raise VerificationError("Behavior input must contain only the authentic prompt and fixture evidence")
    required_grading_only = {
        "kind",
        "setup",
        "permitted_effects",
        "expected_evidence_limits",
        "observable_assertions",
        "verification",
        "git",
        "arm",
        "desired_result",
        "grader_rationale",
    }
    if set(behavior_input["grading_only_fields"]) != required_grading_only:
        raise VerificationError("Grading-only behavior-input exclusions are incomplete")
    if not all(
        behavior_input[field] is True
        for field in (
            "read_only_fresh_empty_directory",
            "behavior_prompt_hash_required",
            "judge_prompt_hash_required",
        )
    ):
        raise VerificationError("Behavior prompt isolation and prompt digests must be required")
    paired = catalog.get("execution", {}).get("paired_evaluation", {})
    required_paired = {
        "model",
        "arms",
        "fresh_task_per_run",
        "required_only_for",
        "explicit_budget_approval_required",
        "default_targeted_probe_trials_per_arm",
        "automatic_resume_forbidden",
        "trials_per_arm",
        "third_pair_on_disagreement",
        "matched_dimensions",
        "blind_judge_required",
        "position_swap_required",
        "deterministic_graders_required",
        "human_calibration_required",
        "held_out_cases_required",
        "human_adjudication_triggers",
        "acceptance_rule",
    }
    if set(paired) != required_paired:
        raise VerificationError("Paired-evaluation contract is incomplete")
    if paired["model"] != "gpt-5.6-sol" or paired["arms"] != ["baseline", "candidate"]:
        raise VerificationError("Paired evaluation must compare baseline and candidate on GPT-5.6 Sol")
    if set(paired["required_only_for"]) != {
        "broad behavioral superiority claim",
        "release decision that depends on subjective comparative behavior",
    }:
        raise VerificationError("Full paired evaluation must remain conditional on a decision-bearing broad claim")
    if paired["explicit_budget_approval_required"] is not True:
        raise VerificationError("Full paired evaluation must require explicit budget approval")
    if paired["default_targeted_probe_trials_per_arm"] != 1 or paired["automatic_resume_forbidden"] is not True:
        raise VerificationError("Targeted behavioral probes must default to one pair without automatic resume")
    if paired["fresh_task_per_run"] is not True or paired["trials_per_arm"] != 2:
        raise VerificationError("Paired evaluation must use two fresh-task trials per arm")
    if paired["third_pair_on_disagreement"] is not True or paired["blind_judge_required"] is not True:
        raise VerificationError("Paired evaluation must resolve disagreement with a third blind-judged pair")
    if not all(
        paired[field] is True
        for field in (
            "position_swap_required",
            "deterministic_graders_required",
            "human_calibration_required",
            "held_out_cases_required",
        )
    ):
        raise VerificationError("Bias controls, deterministic graders, calibration, and held-out cases are required")
    required_adjudication = {
        "safety_or_fidelity_difference",
        "position_sensitive_result",
        "deterministic_semantic_disagreement",
        "split_trials",
    }
    if set(paired["human_adjudication_triggers"]) != required_adjudication:
        raise VerificationError("Human-adjudication triggers are incomplete")
    private_evidence = catalog.get("execution", {}).get("private_evidence", {})
    required_private_evidence = {
        "conditional_on_full_evaluation",
        "held_out_manifest_hash_required",
        "judge_calibration_manifest_hash_required",
        "activation_trace_manifest_hash_required",
        "performance_routes",
        "minimum_interleaved_performance_pairs_per_route",
        "performance_metrics",
        "activation_cases",
        "raw_machine_readable_traces_required",
    }
    if set(private_evidence) != required_private_evidence:
        raise VerificationError("Private evaluation-evidence contract is incomplete")
    if private_evidence["conditional_on_full_evaluation"] is not True:
        raise VerificationError("Private evaluation evidence must remain conditional on full evaluation")
    if not all(
        private_evidence[field] is True
        for field in (
            "held_out_manifest_hash_required",
            "judge_calibration_manifest_hash_required",
            "activation_trace_manifest_hash_required",
            "raw_machine_readable_traces_required",
        )
    ):
        raise VerificationError("Private evaluation manifests and raw traces must be required")
    if private_evidence["performance_routes"] != [
        "routine_edit",
        "stakeholder_synthesis",
        "bounded_delivery",
    ] or private_evidence["minimum_interleaved_performance_pairs_per_route"] < 5:
        raise VerificationError("Performance methodology must use five interleaved pairs on three routes")
    required_performance_metrics = {
        "input_tokens",
        "output_tokens",
        "loaded_bytes",
        "response_characters",
        "tool_calls",
        "turns",
        "median_latency",
        "dispersion",
        "outliers",
        "cache_state",
        "task_success",
    }
    if set(private_evidence["performance_metrics"]) != required_performance_metrics:
        raise VerificationError("Performance evidence metrics are incomplete")
    if set(private_evidence["activation_cases"]) != {
        "explicit_fresh",
        "automatic_fresh",
        "routine_non_activation",
        "pre_upgrade_task",
    }:
        raise VerificationError("Activation lifecycle evidence cases are incomplete")
    matched_dimensions = {
        "prompt",
        "fixture",
        "model",
        "reasoning_effort",
        "harness",
        "tools",
        "permissions",
        "environment",
    }
    if set(paired["matched_dimensions"]) != matched_dimensions:
        raise VerificationError("Paired evaluation dimensions are incomplete")
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
    projection = materializer.get("task_projection", {})
    if projection.get("behavior_fields") != [
        "prompt",
        "evidence.evidence",
        "materialized fixture files",
    ]:
        raise VerificationError("Scenario materializer task projection is not behavior-safe")
    if set(projection.get("grading_only_fields_excluded", [])) != required_grading_only:
        raise VerificationError("Scenario materializer grading-only exclusions are incomplete")
    return {
        "name": "synthetic scenario contract",
        "status": "pass",
        "mixed_scenarios": len(scenarios),
        "negative_controls": len(negative),
        "routing_expectations": len(sequences),
        "candidate_routing_smoke": candidate_smoke,
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
        hook_contract_check(),
        active_poppy_identity_contract_check(),
        linked_reference_check(paths),
        provenance_check(paths),
        boundary_check(paths),
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
        "candidate_digest_algorithm": CANDIDATE_DIGEST_ALGORITHM,
        "candidate_digest": candidate_digest(paths),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationError, json.JSONDecodeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
