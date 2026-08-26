#!/usr/bin/env python3
"""Validate the Poppy v2 foundation manifest, schemas, cases, and invariants."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from poppy_v2_validation import finalize_dag_fixture, validate_case_catalog, validate_manifest_invariants, validate_schema_references


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "v2"
MANIFEST_PATH = SCHEMA_ROOT / "manifest.json"
CASE_CATALOG_PATH = ROOT / "tests" / "v2_schema" / "fixtures" / "cases.json"
FIXTURE_ROOT = CASE_CATALOG_PATH.parent
DIALECT = "https://json-schema.org/draft/2020-12/schema"
EXPECTED_ENTRY_COUNT = 195


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_set_digest(manifest: dict[str, Any], implemented_schema_paths: list[Path]) -> str:
    basis = copy.deepcopy(manifest)
    basis["schema_set"]["digest"] = ""
    hasher = hashlib.sha256()
    hasher.update(canonical_json(basis))
    for path in sorted(implemented_schema_paths, key=lambda item: item.relative_to(ROOT).as_posix().encode("utf-8")):
        relative = path.relative_to(ROOT).as_posix()
        hasher.update(b"\n")
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
    return "sha256:" + hasher.hexdigest()


def _type_matches(instance: Any, expected: str) -> bool:
    return {
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "integer": isinstance(instance, int) and not isinstance(instance, bool),
        "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
        "boolean": isinstance(instance, bool),
        "null": instance is None,
    }.get(expected, False)


def resolve_fixture_ref(reference: str) -> Any:
    """Resolve one bounded synthetic fixture reference or declared executable operation."""
    if reference in {"schema-document:positive", "schema-document:negative", "manifest:positive", "manifest:negative"}:
        return {"operation": reference}
    if reference.startswith("manifest-mutation:POP2-INV-GOV-"):
        return {"operation": reference}
    path_text, separator, fragment = reference.partition("#")
    if path_text not in {"schema-instances.json", "authority-bundles.json", "effect-bundles.json", "evidence-bundles.json", "kernel-bundles.json", "capability-bundles.json", "dag-bundles.json"} or not separator or not fragment.startswith("/"):
        raise ValueError(f"unsupported synthetic fixture reference: {reference}")
    value = read_json(FIXTURE_ROOT / path_text)
    for token in fragment[1:].split("/"):
        token = unquote(token).replace("~1", "/").replace("~0", "~")
        if isinstance(value, list) and token.isdigit() and int(token) < len(value):
            value = value[int(token)]
            continue
        if not isinstance(value, dict) or token not in value:
            raise ValueError(f"unresolved synthetic fixture reference: {reference}")
        value = value[token]
    if path_text == "dag-bundles.json" and fragment == "/positive":
        value = finalize_dag_fixture(value)
    return value


class SchemaStore:
    """A deterministic evaluator for the conservative 2020-12 keyword subset used here.

    This is not claimed as a general JSON Schema implementation. A full runtime
    dependency remains a separately reviewed implementation choice.
    """

    def __init__(self, root: Path = SCHEMA_ROOT) -> None:
        self.by_id: dict[str, dict[str, Any]] = {}
        self.by_path: dict[Path, dict[str, Any]] = {}
        for path in sorted(root.rglob("*.schema.json")):
            value = read_json(path)
            if not isinstance(value, dict) or not isinstance(value.get("$id"), str):
                raise ValueError(f"schema has no $id: {path.relative_to(ROOT).as_posix()}")
            schema_id = value["$id"]
            if schema_id in self.by_id:
                raise ValueError(f"duplicate schema $id: {schema_id}")
            self.by_id[schema_id] = value
            self.by_path[path] = value

    def resolve(self, reference: str) -> dict[str, Any]:
        document_id, separator, fragment = reference.partition("#")
        if document_id not in self.by_id:
            raise ValueError(f"unresolved schema reference: {reference}")
        value: Any = self.by_id[document_id]
        if separator and fragment:
            if not fragment.startswith("/"):
                raise ValueError(f"unsupported schema fragment: {reference}")
            for token in fragment[1:].split("/"):
                token = unquote(token).replace("~1", "/").replace("~0", "~")
                if not isinstance(value, dict) or token not in value:
                    raise ValueError(f"unresolved schema fragment: {reference}")
                value = value[token]
        if not isinstance(value, dict):
            raise ValueError(f"schema reference is not an object: {reference}")
        return value

    def validate(self, instance: Any, schema_or_ref: dict[str, Any] | str, pointer: str = "") -> list[str]:
        schema = self.resolve(schema_or_ref) if isinstance(schema_or_ref, str) else schema_or_ref
        errors: list[str] = []

        if "$ref" in schema:
            try:
                errors.extend(self.validate(instance, schema["$ref"], pointer))
            except ValueError as exc:
                errors.append(f"{pointer or '/'}: {exc}")

        if "const" in schema and instance != schema["const"]:
            errors.append(f"{pointer or '/'}: must equal {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"{pointer or '/'}: must be one of {schema['enum']!r}")

        expected_type = schema.get("type")
        if isinstance(expected_type, str) and not _type_matches(instance, expected_type):
            return errors + [f"{pointer or '/'}: must be {expected_type}"]
        if isinstance(expected_type, list) and not any(isinstance(item, str) and _type_matches(instance, item) for item in expected_type):
            return errors + [f"{pointer or '/'}: must be one of the declared JSON types"]

        if isinstance(instance, str):
            if isinstance(schema.get("minLength"), int) and len(instance) < schema["minLength"]:
                errors.append(f"{pointer or '/'}: string is shorter than minLength")
            if isinstance(schema.get("pattern"), str) and re.fullmatch(schema["pattern"], instance) is None:
                errors.append(f"{pointer or '/'}: string does not match pattern")
            if schema.get("format") == "date-time":
                try:
                    parsed = datetime.fromisoformat(instance.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError
                except ValueError:
                    errors.append(f"{pointer or '/'}: must be a timezone-aware date-time")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if isinstance(schema.get("minimum"), (int, float)) and instance < schema["minimum"]:
                errors.append(f"{pointer or '/'}: number is below minimum")

        if isinstance(instance, list):
            if isinstance(schema.get("minItems"), int) and len(instance) < schema["minItems"]:
                errors.append(f"{pointer or '/'}: array has too few items")
            if isinstance(schema.get("maxItems"), int) and len(instance) > schema["maxItems"]:
                errors.append(f"{pointer or '/'}: array has too many items")
            if schema.get("uniqueItems") is True:
                encoded = [canonical_json(value) for value in instance]
                if len(encoded) != len(set(encoded)):
                    errors.append(f"{pointer or '/'}: array items must be unique")
            if isinstance(schema.get("items"), dict):
                for index, value in enumerate(instance):
                    errors.extend(self.validate(value, schema["items"], f"{pointer}/{index}"))

        if isinstance(instance, dict):
            required = schema.get("required", [])
            if isinstance(required, list):
                for name in required:
                    if name not in instance:
                        errors.append(f"{pointer or ''}/{name}: required property is missing")
            properties = schema.get("properties", {})
            if isinstance(properties, dict):
                for name, child_schema in properties.items():
                    if name in instance and isinstance(child_schema, dict):
                        errors.extend(self.validate(instance[name], child_schema, f"{pointer}/{name}"))
                if schema.get("unevaluatedProperties") is False or schema.get("additionalProperties") is False:
                    for name in sorted(set(instance) - set(properties)):
                        errors.append(f"{pointer}/{name}: property is not allowed")
        return errors

    def validate_artifact(
        self,
        instance: Any,
        schema_or_ref: dict[str, Any] | str,
        manifest_entry: dict[str, Any],
        *,
        locator: str,
    ) -> list[dict[str, str]]:
        """Emit owner-bound stable SHAPE findings for an artifact instance."""
        schema = self.resolve(schema_or_ref) if isinstance(schema_or_ref, str) else schema_or_ref
        findings: list[dict[str, str]] = []
        for error in self.validate(instance, schema):
            pointer, _separator, message = error.partition(": ")
            findings.append({
                "code": str(manifest_entry["stable_code"]),
                "owner_decision_id": str(manifest_entry["owner_decision_id"]),
                "manifest_entry_id": str(manifest_entry["id"]),
                "layer": "SHAPE",
                "locator": locator,
                "json_pointer": pointer,
                "schema_id": str(schema.get("$id", "")),
                "schema_version": str(schema.get("x-poppy-schema-version", "")),
                "schema_digest": "sha256:" + hashlib.sha256(canonical_json(schema)).hexdigest(),
                "message": message or error,
            })
        return findings


def validate_schema_document(schema: dict[str, Any], manifest_entry: dict[str, Any], locator: str) -> list[dict[str, str]]:
    """Emit the entry's stable SHAPE code for malformed schema documents."""
    problems: list[tuple[str, str]] = []
    if schema.get("$schema") != DIALECT:
        problems.append(("/$schema", "schema must declare JSON Schema Draft 2020-12"))
    if not isinstance(schema.get("$id"), str) or not schema["$id"].startswith("poppy://schema/"):
        problems.append(("/$id", "schema must declare its stable Poppy schema id"))
    if schema.get("x-poppy-schema-version") != manifest_entry.get("version"):
        problems.append(("/x-poppy-schema-version", "schema version must match the manifest entry"))
    if schema.get("x-poppy-manifest-entry") != manifest_entry.get("id"):
        problems.append(("/x-poppy-manifest-entry", "schema must cite its exact manifest entry"))
    return [{
        "code": str(manifest_entry["stable_code"]),
        "owner_decision_id": str(manifest_entry["owner_decision_id"]),
        "manifest_entry_id": str(manifest_entry["id"]),
        "layer": "SHAPE",
        "locator": locator,
        "json_pointer": pointer,
        "schema_id": str(schema.get("$id", "")),
        "schema_version": str(schema.get("x-poppy-schema-version", "")),
        "schema_digest": "sha256:" + hashlib.sha256(canonical_json(schema)).hexdigest(),
        "message": message,
    } for pointer, message in problems]


def _implemented_schema_paths(manifest: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for entry in manifest["entries"]:
        if entry["kind"] == "schema" and entry["implementation_status"] == "implemented":
            paths.append(ROOT / entry["implementation"])
    return paths


def validate_repository() -> dict[str, Any]:
    manifest = read_json(MANIFEST_PATH)
    cases = read_json(CASE_CATALOG_PATH)
    store = SchemaStore()
    errors: list[str] = []

    if not isinstance(manifest, dict):
        errors.append("manifest root must be an object")
        manifest = {}
    else:
        errors.extend(store.validate(manifest, "poppy://schema/governance/schema-manifest/v1"))
        errors.extend(f"{item['code']} {item['json_pointer']}: {item['message']}" for item in validate_manifest_invariants(manifest))

    entries = manifest.get("entries", []) if isinstance(manifest, dict) else []
    if len(entries) != EXPECTED_ENTRY_COUNT:
        errors.append(f"manifest must contain {EXPECTED_ENTRY_COUNT} entries, found {len(entries)}")

    case_values = cases.get("cases", []) if isinstance(cases, dict) else []
    case_ids = [case.get("id") for case in case_values if isinstance(case, dict)]
    case_by_id = {case.get("id"): case for case in case_values if isinstance(case, dict) and isinstance(case.get("id"), str)}
    if len(case_ids) != len(set(case_ids)):
        errors.append("synthetic case ids must be unique")
    errors.extend(f"{item['code']} {item['json_pointer']}: {item['message']}" for item in validate_case_catalog(manifest, cases))
    for case in case_values:
        if not isinstance(case, dict) or not isinstance(case.get("fixture_ref"), str):
            errors.append("synthetic case must declare an executable fixture_ref")
            continue
        try:
            resolve_fixture_ref(case["fixture_ref"])
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(str(exc))

    implemented = [entry for entry in entries if entry.get("implementation_status") == "implemented"]
    implemented_ids = {entry.get("id") for entry in implemented}
    for entry in implemented:
        target = ROOT / str(entry.get("implementation", ""))
        if not target.is_file():
            errors.append(f"implemented target is missing: {entry.get('id')} -> {entry.get('implementation')}")
        if entry.get("positive_case") not in case_ids or entry.get("negative_case") not in case_ids:
            errors.append(f"implemented entry lacks its declared case pair: {entry.get('id')}")
        for field, polarity in (("positive_case", "positive"), ("negative_case", "negative")):
            case = case_by_id.get(entry.get(field), {})
            if case.get("entry_id") != entry.get("id") or case.get("owner_decision_id") != entry.get("owner_decision_id") or case.get("polarity") != polarity:
                errors.append(f"synthetic case does not cite its exact entry, owner, and polarity: {entry.get(field)}")
        negative_case = case_by_id.get(entry.get("negative_case"), {})
        if negative_case.get("expected_codes") != [entry.get("stable_code")]:
            errors.append(f"negative case does not assert its stable code: {entry.get('id')}")

    for path, schema in store.by_path.items():
        entry_id = schema.get("x-poppy-manifest-entry")
        if schema.get("$schema") != DIALECT:
            errors.append(f"schema dialect mismatch: {path.relative_to(ROOT).as_posix()}")
        if schema.get("x-poppy-schema-version") != "1.0.0":
            errors.append(f"schema version mismatch: {path.relative_to(ROOT).as_posix()}")
        if entry_id not in implemented_ids:
            errors.append(f"schema is not an implemented manifest entry: {path.relative_to(ROOT).as_posix()}")
        for reference in _walk_refs(schema):
            try:
                store.resolve(reference)
            except ValueError as exc:
                errors.append(str(exc))
    errors.extend(f"{item['code']} {item['json_pointer']}: {item['message']}" for item in validate_schema_references(store.by_id))

    implemented_schema_paths = _implemented_schema_paths(manifest)
    for path in implemented_schema_paths:
        if path.is_file() and path not in store.by_path:
            errors.append(f"implemented schema target is not a schema document: {path.relative_to(ROOT).as_posix()}")
    if isinstance(manifest.get("schema_set"), dict):
        actual_digest = schema_set_digest(manifest, [path for path in implemented_schema_paths if path.is_file()])
        if manifest["schema_set"].get("digest") != actual_digest:
            errors.append(f"schema-set digest mismatch: expected {actual_digest}")
        if manifest["schema_set"].get("implemented_entry_count") != len(implemented):
            errors.append("schema-set implemented_entry_count does not match manifest")

    return {
        "status": "pass" if not errors else "fail",
        "manifest_entries": len(entries),
        "implemented_entries": len(implemented),
        "schemas": len(store.by_path),
        "synthetic_cases": len(case_ids),
        "errors": sorted(set(errors)),
    }


def _walk_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                refs.append(child)
            else:
                refs.extend(_walk_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_walk_refs(child))
    return refs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without changing files (the only supported mode).")
    parser.parse_args(argv)
    try:
        result = validate_repository()
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
