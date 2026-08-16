#!/usr/bin/env python3
"""Validate a normalized Project Operations Researcher handoff packet."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


MODES = {"project", "portfolio", "global"}
COVERAGE = {"full", "partial", "gray"}
SOURCE_KINDS = {
    "official-doc",
    "primary-research",
    "standard",
    "maintainer-doc",
    "engineering-case-study",
    "repository",
    "release-note",
    "issue-discussion",
    "social-evidence",
}
NEED_LEVELS = {"project", "global"}
NEED_STATES = {"unresolved", "addressed", "not-actionable"}
CONFIDENCE = {"low", "medium", "high"}
LANES = {"repair-existing", "addition"}
CLASSIFICATIONS = {"no-action", "project-fix", "plugin-candidate"}
OWNER_LAYERS = {"project", "global", "mixed"}
DISPOSITIONS = {"upgrader-review", "experiment-candidate", "watch", "reject", "no-action"}
REPOSITORY_OUTCOMES = {"strong-candidate", "experiment-candidate", "watch", "reject"}


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    return value


def _string(value: Any, path: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")
        return ""
    return value.strip()


def _strings(value: Any, path: str, errors: list[str], *, nonempty: bool = False) -> list[str]:
    values = _list(value, path, errors)
    if any(not isinstance(item, str) or not item.strip() for item in values):
        errors.append(f"{path} must contain only non-empty strings")
        return []
    normalized = [item.strip() for item in values]
    if len(normalized) != len(set(normalized)):
        errors.append(f"{path} must not contain duplicates")
    if nonempty and not normalized:
        errors.append(f"{path} must not be empty")
    return normalized


def _dated(value: Any, path: str, errors: list[str]) -> None:
    text = _string(value, path, errors)
    if not text:
        return
    try:
        date.fromisoformat(text)
    except ValueError:
        errors.append(f"{path} must use YYYY-MM-DD")


def _https_url(value: Any, path: str, errors: list[str]) -> str:
    text = _string(value, path, errors)
    parsed = urlparse(text)
    if text and (parsed.scheme != "https" or not parsed.netloc):
        errors.append(f"{path} must be a direct HTTPS URL")
    return text


def _unique_ids(items: list[Any], path: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(items):
        item = _object(value, f"{path}[{index}]", errors)
        item_id = _string(item.get("id"), f"{path}[{index}].id", errors)
        if item_id in indexed:
            errors.append(f"{path}.id must be unique: {item_id}")
        elif item_id:
            indexed[item_id] = item
    return indexed


def _references(values: list[str], known: set[str], path: str, errors: list[str]) -> None:
    for value in values:
        if value not in known:
            errors.append(f"{path} references unknown id: {value}")


def _validate_scope(packet: dict[str, Any], errors: list[str]) -> tuple[str, list[str]]:
    scope = _object(packet.get("scope"), "scope", errors)
    mode = scope.get("mode")
    if mode not in MODES:
        errors.append(f"scope.mode must be one of {sorted(MODES)}")
    projects = _strings(scope.get("projects"), "scope.projects", errors)
    if mode in {"project", "portfolio"} and not projects:
        errors.append(f"scope.projects must not be empty in {mode} mode")
    if mode == "project" and len(projects) != 1:
        errors.append("project mode requires exactly one project")
    _strings(scope.get("themes"), "scope.themes", errors, nonempty=True)
    _string(scope.get("decision"), "scope.decision", errors)
    if scope.get("repository_access") != "inspect-only":
        errors.append("scope.repository_access must be inspect-only")
    if scope.get("priority_order") != ["repair-existing", "addition"]:
        errors.append("scope.priority_order must be repair-existing then addition")
    window = _object(scope.get("research_window"), "scope.research_window", errors)
    _dated(window.get("started"), "scope.research_window.started", errors)
    _dated(window.get("ended"), "scope.research_window.ended", errors)
    return str(mode), projects


def _validate_coverage(packet: dict[str, Any], errors: list[str]) -> None:
    coverage = _object(packet.get("coverage"), "coverage", errors)
    incomplete = False
    for name in ("task_history", "vaults", "web", "repositories"):
        item = _object(coverage.get(name), f"coverage.{name}", errors)
        if item.get("status") not in COVERAGE:
            errors.append(f"coverage.{name}.status must be full, partial, or gray")
        if item.get("status") != "full":
            incomplete = True
        _strings(item.get("refs"), f"coverage.{name}.refs", errors)
    gaps = _strings(coverage.get("gaps"), "coverage.gaps", errors)
    if incomplete and not gaps:
        errors.append("non-full coverage requires at least one coverage.gaps entry")


def _score_total(score: dict[str, Any], path: str, errors: list[str]) -> None:
    weights = {
        "need": 5,
        "impact": 5,
        "fit": 4,
        "evidence": 4,
        "timeliness": 2,
        "cost": -2,
        "risk": -2,
    }
    values: dict[str, int] = {}
    for name in weights:
        value = score.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            errors.append(f"{path}.{name} must be an integer from 0 to 5")
        else:
            values[name] = value
    total = score.get("total")
    if isinstance(total, bool) or not isinstance(total, int) or not 0 <= total <= 100:
        errors.append(f"{path}.total must be an integer from 0 to 100")
    if len(values) == len(weights):
        expected = max(0, min(100, sum(values[name] * weight for name, weight in weights.items())))
        if total != expected:
            errors.append(f"{path}.total must equal deterministic score {expected}")


def validate_packet(packet: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet root must be an object"]
    if packet.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    _string(packet.get("run_id"), "run_id", errors)
    mode, scope_projects = _validate_scope(packet, errors)
    _validate_coverage(packet, errors)

    needs_list = _list(packet.get("needs"), "needs", errors)
    sources_list = _list(packet.get("sources"), "sources", errors)
    repositories_list = _list(packet.get("repositories"), "repositories", errors)
    findings_list = _list(packet.get("findings"), "findings", errors)
    recommendations_list = _list(packet.get("recommendations"), "recommendations", errors)
    for path, values in (
        ("needs", needs_list),
        ("sources", sources_list),
        ("findings", findings_list),
        ("recommendations", recommendations_list),
    ):
        if not values:
            errors.append(f"{path} must not be empty")

    needs = _unique_ids(needs_list, "needs", errors)
    for index, value in enumerate(needs_list):
        item = value if isinstance(value, dict) else {}
        if item.get("level") not in NEED_LEVELS:
            errors.append(f"needs[{index}].level must be project or global")
        projects = _strings(item.get("projects"), f"needs[{index}].projects", errors)
        if item.get("level") == "project" and not projects:
            errors.append(f"needs[{index}].projects must not be empty for a project need")
        if scope_projects and any(project not in scope_projects for project in projects):
            errors.append(f"needs[{index}].projects contains a project outside scope")
        _string(item.get("workflow"), f"needs[{index}].workflow", errors)
        _string(item.get("problem"), f"needs[{index}].problem", errors)
        _strings(item.get("evidence_refs"), f"needs[{index}].evidence_refs", errors, nonempty=True)
        impact = item.get("impact")
        if isinstance(impact, bool) or not isinstance(impact, int) or not 0 <= impact <= 5:
            errors.append(f"needs[{index}].impact must be an integer from 0 to 5")
        if item.get("status") not in NEED_STATES:
            errors.append(f"needs[{index}].status has an unsupported value")

    sources = _unique_ids(sources_list, "sources", errors)
    for index, value in enumerate(sources_list):
        item = value if isinstance(value, dict) else {}
        kind = item.get("kind")
        if kind not in SOURCE_KINDS:
            errors.append(f"sources[{index}].kind has an unsupported value")
        _string(item.get("title"), f"sources[{index}].title", errors)
        _https_url(item.get("url"), f"sources[{index}].url", errors)
        _string(item.get("publisher"), f"sources[{index}].publisher", errors)
        _dated(item.get("retrieved"), f"sources[{index}].retrieved", errors)
        _string(item.get("reputation_basis"), f"sources[{index}].reputation_basis", errors)
        _strings(item.get("claim_refs"), f"sources[{index}].claim_refs", errors, nonempty=True)
        if not isinstance(item.get("primary"), bool):
            errors.append(f"sources[{index}].primary must be boolean")
        if not isinstance(item.get("social"), bool):
            errors.append(f"sources[{index}].social must be boolean")
        corroborated = _strings(item.get("corroborated_by"), f"sources[{index}].corroborated_by", errors)
        if item.get("social") or kind == "social-evidence":
            if kind != "social-evidence" or item.get("social") is not True:
                errors.append(f"sources[{index}] social flag and kind must agree")
            if not corroborated:
                errors.append(f"sources[{index}] social evidence requires non-social corroboration")

    for source_id, item in sources.items():
        corroborated = item.get("corroborated_by", [])
        if isinstance(corroborated, list):
            _references(corroborated, set(sources), f"source {source_id}.corroborated_by", errors)
            for corroborator in corroborated:
                other = sources.get(corroborator, {})
                if other.get("social") is True:
                    errors.append(f"source {source_id} must be corroborated by a non-social source")

    repositories = _unique_ids(repositories_list, "repositories", errors)
    assessed_source_ids: set[str] = set()
    for index, value in enumerate(repositories_list):
        item = value if isinstance(value, dict) else {}
        source_id = _string(item.get("source_id"), f"repositories[{index}].source_id", errors)
        _references([source_id] if source_id else [], set(sources), f"repositories[{index}].source_id", errors)
        if source_id and sources.get(source_id, {}).get("kind") != "repository":
            errors.append(f"repositories[{index}].source_id must reference a repository source")
        assessed_source_ids.add(source_id)
        url = _https_url(item.get("url"), f"repositories[{index}].url", errors)
        parsed = urlparse(url)
        if url and parsed.netloc.casefold() not in {"github.com", "www.github.com"}:
            errors.append(f"repositories[{index}].url must be a GitHub repository URL")
        _string(item.get("owner"), f"repositories[{index}].owner", errors)
        _string(item.get("repository"), f"repositories[{index}].repository", errors)
        _string(item.get("owner_reputation"), f"repositories[{index}].owner_reputation", errors)
        _strings(item.get("evidence_refs"), f"repositories[{index}].evidence_refs", errors, nonempty=True)
        _string(item.get("license"), f"repositories[{index}].license", errors)
        _string(item.get("license_evidence"), f"repositories[{index}].license_evidence", errors)
        maintenance = _object(item.get("maintenance"), f"repositories[{index}].maintenance", errors)
        _string(maintenance.get("status"), f"repositories[{index}].maintenance.status", errors)
        _dated(maintenance.get("last_activity"), f"repositories[{index}].maintenance.last_activity", errors)
        _string(maintenance.get("release_evidence"), f"repositories[{index}].maintenance.release_evidence", errors)
        _string(maintenance.get("issue_health"), f"repositories[{index}].maintenance.issue_health", errors)
        _strings(item.get("quality_evidence"), f"repositories[{index}].quality_evidence", errors, nonempty=True)
        _strings(item.get("security_signals"), f"repositories[{index}].security_signals", errors, nonempty=True)
        adoption = _object(item.get("adoption"), f"repositories[{index}].adoption", errors)
        _string(adoption.get("fit"), f"repositories[{index}].adoption.fit", errors)
        _strings(adoption.get("constraints"), f"repositories[{index}].adoption.constraints", errors)
        if adoption.get("risk") not in {"low", "medium", "high", "unknown"}:
            errors.append(f"repositories[{index}].adoption.risk has an unsupported value")
        if item.get("outcome") not in REPOSITORY_OUTCOMES:
            errors.append(f"repositories[{index}].outcome has an unsupported value")
        if item.get("inspection_only") is not True:
            errors.append(f"repositories[{index}].inspection_only must be true")
    for source_id, source in sources.items():
        if source.get("kind") == "repository" and source_id not in assessed_source_ids:
            errors.append(f"repository source {source_id} has no repository assessment")

    findings = _unique_ids(findings_list, "findings", errors)
    finding_needs: dict[str, set[str]] = {}
    for index, value in enumerate(findings_list):
        item = value if isinstance(value, dict) else {}
        need_ids = _strings(item.get("need_ids"), f"findings[{index}].need_ids", errors, nonempty=True)
        source_ids = _strings(item.get("source_ids"), f"findings[{index}].source_ids", errors, nonempty=True)
        repository_ids = _strings(item.get("repository_ids"), f"findings[{index}].repository_ids", errors)
        _references(need_ids, set(needs), f"findings[{index}].need_ids", errors)
        _references(source_ids, set(sources), f"findings[{index}].source_ids", errors)
        _references(repository_ids, set(repositories), f"findings[{index}].repository_ids", errors)
        item_id = item.get("id")
        if isinstance(item_id, str):
            finding_needs[item_id] = set(need_ids)
        _string(item.get("claim"), f"findings[{index}].claim", errors)
        if item.get("confidence") not in CONFIDENCE:
            errors.append(f"findings[{index}].confidence must be low, medium, or high")
        _strings(item.get("contradictions"), f"findings[{index}].contradictions", errors)
        _score_total(_object(item.get("score"), f"findings[{index}].score", errors), f"findings[{index}].score", errors)
        applicability = _list(item.get("applicability"), f"findings[{index}].applicability", errors)
        if not applicability:
            errors.append(f"findings[{index}].applicability must not be empty")
        for app_index, app_value in enumerate(applicability):
            app = _object(app_value, f"findings[{index}].applicability[{app_index}]", errors)
            if app.get("level") not in {"project", "global"}:
                errors.append(f"findings[{index}].applicability[{app_index}].level is invalid")
            _string(app.get("target"), f"findings[{index}].applicability[{app_index}].target", errors)
            _string(app.get("rationale"), f"findings[{index}].applicability[{app_index}].rationale", errors)

    for source_id, source in sources.items():
        claim_refs = source.get("claim_refs", [])
        if isinstance(claim_refs, list):
            _references(claim_refs, set(findings), f"source {source_id}.claim_refs", errors)

    recommendations = _unique_ids(recommendations_list, "recommendations", errors)
    repair_sequences: list[int] = []
    addition_sequences: list[int] = []
    repaired_need_ids: set[str] = set()
    for index, value in enumerate(recommendations_list):
        item = value if isinstance(value, dict) else {}
        finding_ids = _strings(item.get("finding_ids"), f"recommendations[{index}].finding_ids", errors, nonempty=True)
        _references(finding_ids, set(findings), f"recommendations[{index}].finding_ids", errors)
        lane = item.get("lane")
        if lane not in LANES:
            errors.append(f"recommendations[{index}].lane has an unsupported value")
        sequence = item.get("sequence")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            errors.append(f"recommendations[{index}].sequence must be a positive integer")
        elif lane == "repair-existing":
            repair_sequences.append(sequence)
        elif lane == "addition":
            addition_sequences.append(sequence)
        if lane == "repair-existing":
            for finding_id in finding_ids:
                repaired_need_ids.update(finding_needs.get(finding_id, set()))
            if item.get("repair_gate") != "not-applicable":
                errors.append(f"recommendations[{index}].repair_gate must be not-applicable for repairs")
        elif lane == "addition" and item.get("repair_gate") not in {"cleared", "deferred"}:
            errors.append(f"recommendations[{index}].repair_gate must be cleared or deferred for additions")
        if item.get("proposed_classification") not in CLASSIFICATIONS:
            errors.append(f"recommendations[{index}].proposed_classification has an unsupported value")
        if item.get("owner_layer") not in OWNER_LAYERS:
            errors.append(f"recommendations[{index}].owner_layer has an unsupported value")
        _strings(item.get("targets"), f"recommendations[{index}].targets", errors, nonempty=True)
        if item.get("disposition") not in DISPOSITIONS:
            errors.append(f"recommendations[{index}].disposition has an unsupported value")
        for field in ("change", "expected_benefit", "validation", "rollback"):
            _string(item.get(field), f"recommendations[{index}].{field}", errors)
    sequences = [item.get("sequence") for item in recommendations_list if isinstance(item, dict)]
    if len(sequences) != len(set(sequences)):
        errors.append("recommendations.sequence must be unique")
    if repair_sequences and addition_sequences and max(repair_sequences) >= min(addition_sequences):
        errors.append("all repair-existing recommendations must precede additions")
    material_needs = {
        need_id
        for need_id, need in needs.items()
        if need.get("status") == "unresolved" and isinstance(need.get("impact"), int) and need.get("impact") >= 3
    }
    if addition_sequences and material_needs - repaired_need_ids:
        errors.append("additions cannot precede disposition of every material unresolved repair need")

    handoff = _object(packet.get("handoff"), "handoff", errors)
    if handoff.get("implementation_authorized") is not False:
        errors.append("handoff.implementation_authorized must be false")
    if not isinstance(handoff.get("upgrader_required"), bool):
        errors.append("handoff.upgrader_required must be boolean")
    candidate_ids = _strings(handoff.get("candidate_ids"), "handoff.candidate_ids", errors)
    project_fix_ids = _strings(handoff.get("project_fix_ids"), "handoff.project_fix_ids", errors)
    global_ids = _strings(handoff.get("global_candidate_ids"), "handoff.global_candidate_ids", errors)
    for path, values in (
        ("handoff.candidate_ids", candidate_ids),
        ("handoff.project_fix_ids", project_fix_ids),
        ("handoff.global_candidate_ids", global_ids),
    ):
        _references(values, set(recommendations), path, errors)
    for rec_id in project_fix_ids:
        if recommendations.get(rec_id, {}).get("proposed_classification") != "project-fix":
            errors.append(f"handoff project fix {rec_id} is not classified project-fix")
    for rec_id in global_ids:
        if recommendations.get(rec_id, {}).get("proposed_classification") != "plugin-candidate":
            errors.append(f"handoff global candidate {rec_id} is not classified plugin-candidate")
    actionable = any(
        item.get("disposition") in {"upgrader-review", "experiment-candidate"}
        for item in recommendations.values()
    )
    if actionable and handoff.get("upgrader_required") is not True:
        errors.append("actionable recommendations require Upgrader handoff")
    _strings(handoff.get("questions"), "handoff.questions", errors)

    if mode == "global" and any(need.get("level") == "project" for need in needs.values()) and not scope_projects:
        errors.append("global mode cannot contain project needs without scoped projects")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        value = json.loads(args.packet.read_text(encoding="utf-8"))
        errors = validate_packet(value)
    except (OSError, json.JSONDecodeError) as exc:
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
