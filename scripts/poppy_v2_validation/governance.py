"""Governance invariants for the canonical Poppy v2 schema manifest."""

from __future__ import annotations

import re
from typing import Any


ACCEPTED_DECISIONS = {f"POP-V2-{number:03d}" for number in range(1, 13)}
ENTRY_ID = re.compile(r"^(schema|invariant)\.[a-z0-9]+(?:[.-][a-z0-9]+)*$")
STABLE_CODE = re.compile(r"^POP2-(SHP|INV|BEH|INT|REL)-[A-Z]{3}-[0-9]{3}$")
TEST_ID = re.compile(r"^TV2-[A-Z]{3}-[0-9]{3}$")


def _finding(code: str, entry_id: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "owner_decision_id": "POP-V2-011",
        "manifest_entry_id": entry_id,
        "layer": "INVARIANT",
        "locator": "schemas/v2/manifest.json",
        "json_pointer": pointer,
        "message": message,
    }


def _major(version: Any) -> int | None:
    if not isinstance(version, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:[-+].+)?", version):
        return None
    return int(version.split(".", 1)[0])


def validate_manifest_invariants(manifest: dict[str, Any]) -> list[dict[str, str]]:
    """Return stable findings for cross-entry governance violations."""
    findings: list[dict[str, str]] = []
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return [_finding("POP2-INV-GOV-011", "schema.governance.schema-manifest", "/entries", "entries must be a list")]

    seen_ids: set[str] = set()
    seen_codes: set[str] = set()
    seen_tests: set[str] = set()
    for index, entry in enumerate(entries):
        pointer = f"/entries/{index}"
        if not isinstance(entry, dict):
            findings.append(_finding("POP2-INV-GOV-011", "schema.governance.schema-manifest-entry", pointer, "entry must be an object"))
            continue
        entry_id = str(entry.get("id", "schema.governance.schema-manifest-entry"))
        owner = entry.get("owner_decision_id")
        if owner not in ACCEPTED_DECISIONS:
            findings.append(_finding("POP2-INV-GOV-011", entry_id, pointer + "/owner_decision_id", "entry must have exactly one accepted decision owner"))
        if entry.get("status") != "ratified":
            findings.append(_finding("POP2-INV-GOV-012", entry_id, pointer + "/status", "only ratified entries may be normative"))
        if not ENTRY_ID.fullmatch(entry_id) or entry_id in seen_ids:
            findings.append(_finding("POP2-INV-GOV-011", entry_id, pointer + "/id", "entry id must be valid and unique"))
        seen_ids.add(entry_id)

        kind = entry.get("kind")
        if kind not in {"schema", "invariant"} or not entry_id.startswith(f"{kind}."):
            findings.append(_finding("POP2-INV-GOV-011", entry_id, pointer + "/kind", "entry kind must match its id prefix"))

        code = entry.get("stable_code")
        if not isinstance(code, str) or not STABLE_CODE.fullmatch(code) or code in seen_codes:
            findings.append(_finding("POP2-INV-GOV-014", entry_id, pointer + "/stable_code", "stable code must be valid and unique"))
        if isinstance(code, str):
            seen_codes.add(code)

        test_id = entry.get("test_id")
        if not isinstance(test_id, str) or not TEST_ID.fullmatch(test_id) or test_id in seen_tests:
            findings.append(_finding("POP2-INV-GOV-016", entry_id, pointer + "/test_id", "test id must be valid and unique"))
        if isinstance(test_id, str):
            seen_tests.add(test_id)

        version_major = _major(entry.get("version"))
        compatibility = entry.get("compatibility")
        if not isinstance(compatibility, dict):
            findings.append(_finding("POP2-INV-GOV-013", entry_id, pointer + "/compatibility", "compatibility must be an object"))
        else:
            minimum_major = _major(compatibility.get("minimum"))
            maximum_major = _major(compatibility.get("maximum_exclusive"))
            if version_major is None or minimum_major != version_major or maximum_major != version_major + 1:
                findings.append(_finding("POP2-INV-GOV-013", entry_id, pointer + "/compatibility", "initial compatibility must be the same-major half-open interval"))

        expected_positive = f"CASE-{test_id}-POS"
        expected_negative = f"CASE-{test_id}-NEG"
        if entry.get("positive_case") != expected_positive or entry.get("negative_case") != expected_negative:
            findings.append(_finding("POP2-INV-GOV-017", entry_id, pointer, "entry must bind its exact positive and negative synthetic case ids"))

    declared = manifest.get("accepted_decisions")
    if not isinstance(declared, list) or set(declared) != ACCEPTED_DECISIONS or len(declared) != 12:
        findings.append(_finding("POP2-INV-GOV-011", "schema.governance.schema-manifest", "/accepted_decisions", "accepted decision catalog must be exactly POP-V2-001 through POP-V2-012"))
    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))


def validate_case_catalog(manifest: dict[str, Any], catalog: dict[str, Any]) -> list[dict[str, str]]:
    """Prove that implemented entries have exact owner-bound positive/negative cases."""
    findings: list[dict[str, str]] = []
    entries = {
        entry.get("id"): entry
        for entry in manifest.get("entries", [])
        if isinstance(entry, dict) and entry.get("implementation_status") == "implemented"
    }
    cases = catalog.get("cases", []) if isinstance(catalog, dict) else []
    case_by_id = {
        case.get("id"): case
        for case in cases
        if isinstance(case, dict) and isinstance(case.get("id"), str)
    }
    expected_case_ids = {
        str(entry[field])
        for entry in entries.values()
        for field in ("positive_case", "negative_case")
    }
    for orphan_id in sorted(set(case_by_id) - expected_case_ids):
        findings.append(_finding("POP2-INV-GOV-016", "schema.governance.traceability-report", f"/cases/{orphan_id}", "orphan synthetic cases are not allowed"))
    for entry_id, entry in entries.items():
        for field, polarity in (("positive_case", "positive"), ("negative_case", "negative")):
            case_id = entry.get(field)
            case = case_by_id.get(case_id)
            if not isinstance(case, dict):
                findings.append(_finding("POP2-INV-GOV-017", str(entry_id), f"/cases/{case_id}", "implemented entry must have its declared positive and negative cases"))
                continue
            if case.get("entry_id") != entry_id or case.get("owner_decision_id") != entry.get("owner_decision_id") or case.get("polarity") != polarity:
                findings.append(_finding("POP2-INV-GOV-016", str(entry_id), f"/cases/{case_id}", "test case must cite its exact manifest entry, owner, and polarity"))
            expected = [] if polarity == "positive" else [entry.get("stable_code")]
            if case.get("expected_codes") != expected:
                findings.append(_finding("POP2-INV-GOV-016", str(entry_id), f"/cases/{case_id}/expected_codes", "test case must assert the entry's exact stable-code outcome"))
            if not isinstance(case.get("fixture_ref"), str) or not case["fixture_ref"]:
                findings.append(_finding("POP2-INV-GOV-016", str(entry_id), f"/cases/{case_id}/fixture_ref", "test case must bind an executable fixture reference"))
    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))


def validate_schema_references(schemas: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Return a stable finding for every unresolved product schema reference."""
    findings: list[dict[str, str]] = []

    def walk(value: Any) -> list[str]:
        refs: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "$ref" and isinstance(child, str):
                    refs.append(child)
                else:
                    refs.extend(walk(child))
        elif isinstance(value, list):
            for child in value:
                refs.extend(walk(child))
        return refs

    for schema_id, schema in schemas.items():
        entry_id = str(schema.get("x-poppy-manifest-entry", "schema.governance.schema-manifest"))
        for reference in walk(schema):
            document_id = reference.split("#", 1)[0]
            if document_id not in schemas:
                findings.append(_finding("POP2-INV-GOV-015", entry_id, "/$ref", f"schema reference does not resolve: {reference}"))
    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))
