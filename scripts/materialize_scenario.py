#!/usr/bin/env python3
"""Materialize one self-contained Poppy v3 acceptance scenario into a fresh directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests" / "scenarios.json"
FIXTURES = ROOT / "tests" / "fixtures.json"
GRADING_ONLY_FIELDS = {
    "kind",
    "setup",
    "observable_assertions",
    "expected_evidence_limits",
    "permitted_effects",
    "verification",
    "git",
    "arm",
    "desired_result",
    "grader_rationale",
}


def load_catalogs() -> tuple[dict, dict, dict[str, dict]]:
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    cases = {
        item["id"]: item
        for item in [*scenarios.get("scenarios", []), *scenarios.get("negative_cases", [])]
    }
    fixture_map = fixtures.get("fixtures", {})
    if set(cases) != set(fixture_map):
        missing = sorted(set(cases) - set(fixture_map))
        extra = sorted(set(fixture_map) - set(cases))
        raise ValueError(f"fixture coverage mismatch; missing={missing}, extra={extra}")
    return scenarios, fixtures, cases


def safe_relative(raw: str) -> Path:
    if "\\" in raw or ":" in raw:
        raise ValueError(f"unsafe host-sensitive fixture path: {raw}")
    pure = PurePosixPath(raw)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"unsafe fixture path: {raw}")
    if raw.startswith(("\\", "/")):
        raise ValueError(f"absolute fixture path: {raw}")
    return Path(*pure.parts)


def resolved_member(root: Path, raw: str) -> Path:
    resolved_root = root.resolve()
    destination = (resolved_root / safe_relative(raw)).resolve()
    try:
        destination.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"fixture path escapes output root: {raw}") from exc
    return destination


def validate_fixture(case_id: str, fixture: dict) -> None:
    required = {"kind", "setup", "files", "evidence", "verification"}
    if frozenset(fixture) not in {frozenset(required), frozenset(required | {"git"})}:
        raise ValueError(f"fixture fields invalid for {case_id}")
    if fixture["kind"] not in {"workspace", "evidence"}:
        raise ValueError(f"fixture kind invalid for {case_id}")
    for field in ("setup", "evidence", "verification"):
        values = fixture[field]
        if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() for v in values):
            raise ValueError(f"fixture {field} invalid for {case_id}")
    if not isinstance(fixture["files"], dict):
        raise ValueError(f"fixture files invalid for {case_id}")
    for raw, content in fixture["files"].items():
        safe_relative(raw)
        if not isinstance(content, str):
            raise ValueError(f"fixture file content invalid for {case_id}: {raw}")
    if "git" in fixture:
        git = fixture["git"]
        expected_git = {
            "repository_root",
            "base_files",
            "mutations",
            "remote_origin",
            "expected_status",
        }
        if not isinstance(git, dict) or set(git) != expected_git:
            raise ValueError(f"git fixture fields invalid for {case_id}")
        if git["repository_root"] != ".":
            safe_relative(git["repository_root"])
        for field in ("base_files", "mutations"):
            if not isinstance(git[field], dict):
                raise ValueError(f"git fixture {field} invalid for {case_id}")
            for raw, content in git[field].items():
                safe_relative(raw)
                if not isinstance(content, str):
                    raise ValueError(f"git fixture content invalid for {case_id}: {raw}")
        if git["remote_origin"] is not None and not isinstance(git["remote_origin"], str):
            raise ValueError(f"git remote invalid for {case_id}")
        if not isinstance(git["expected_status"], list) or not all(
            isinstance(value, str) for value in git["expected_status"]
        ):
            raise ValueError(f"git expected status invalid for {case_id}")


def fixture_digest(case: dict, fixture: dict) -> str:
    payload = json.dumps(
        {"case": case, "fixture": fixture},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def task_descriptor(case: dict, fixture: dict) -> dict:
    """Project only authentic task input into a behavior workspace."""
    return {
        "prompt": case["prompt"],
        "evidence": {
            key: fixture[key]
            for key in ("evidence",)
            if key in fixture
        },
    }


def assert_task_projection(descriptor: dict) -> None:
    serialized = json.dumps(descriptor, ensure_ascii=False)
    leaked = sorted(field for field in GRADING_ONLY_FIELDS if f'"{field}"' in serialized)
    if leaked:
        raise ValueError(f"grading-only fields leaked into task descriptor: {leaked}")


def render_content(content: str, output: Path) -> str:
    return content.replace("{{FIXTURE_ROOT}}", output.resolve().as_posix())


def write_fixture_file(output: Path, raw: str, content: str) -> Path:
    destination = resolved_member(output, raw)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_content(content, output), encoding="utf-8", newline="\n")
    return destination


def run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        text=True,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    if completed.returncode:
        raise ValueError(
            f"git {' '.join(arguments)} failed in {repository}: "
            f"{completed.stdout.strip()} {completed.stderr.strip()}"
        )
    return completed.stdout.rstrip("\r\n")


def materialize(case_id: str, output: Path) -> dict:
    _, fixtures, cases = load_catalogs()
    if case_id not in cases:
        raise ValueError(f"unknown scenario: {case_id}")
    fixture = fixtures["fixtures"][case_id]
    validate_fixture(case_id, fixture)
    resolved = output.resolve()
    if output.exists():
        raise ValueError(f"output must not already exist: {output}")
    if resolved == ROOT.resolve() or ROOT.resolve() in resolved.parents:
        raise ValueError("fixture output must be outside the product repository")
    output.mkdir(parents=True)
    for raw, content in fixture["files"].items():
        write_fixture_file(output, raw, content)
    descriptor = task_descriptor(cases[case_id], fixture)
    assert_task_projection(descriptor)
    (output / "task.json").write_text(
        json.dumps(descriptor, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if "git" in fixture:
        git = fixture["git"]
        repository = (
            output.resolve()
            if git["repository_root"] == "."
            else resolved_member(output, git["repository_root"])
        )
        repository.mkdir(parents=True, exist_ok=True)
        for raw, content in git["base_files"].items():
            destination = write_fixture_file(output, raw, content).resolve()
            try:
                destination.relative_to(repository.resolve())
            except ValueError as exc:
                raise ValueError(f"git base file escapes repository for {case_id}: {raw}") from exc
        run_git(repository, "init", "-q")
        if git["remote_origin"]:
            run_git(repository, "remote", "add", "origin", git["remote_origin"])
        run_git(repository, "add", "--all")
        run_git(
            repository,
            "-c",
            "user.name=Poppy Fixture",
            "-c",
            "user.email=poppy-fixture@example.invalid",
            "commit",
            "-qm",
            "synthetic fixture base",
        )
        for raw, content in git["mutations"].items():
            destination = write_fixture_file(output, raw, content).resolve()
            try:
                destination.relative_to(repository.resolve())
            except ValueError as exc:
                raise ValueError(f"git mutation escapes repository for {case_id}: {raw}") from exc
        observed_status = run_git(repository, "status", "--porcelain").splitlines()
        if observed_status != git["expected_status"]:
            raise ValueError(
                f"git status mismatch for {case_id}: expected={git['expected_status']}, "
                f"observed={observed_status}"
            )
    return {
        "scenario_id": case_id,
        "output": str(output),
        "files": sorted(
            [
                *fixture["files"],
                *fixture.get("git", {}).get("base_files", {}),
                *fixture.get("git", {}).get("mutations", {}),
                "task.json",
            ]
        ),
        "fixture_digest_sha256": fixture_digest(cases[case_id], fixture),
    }


def verify_catalog() -> dict:
    _, fixtures, cases = load_catalogs()
    digests: dict[str, str] = {}
    canaries = {
        "case": "PRIVATE-CASE-CANARY-8C92F7",
        "setup": "PRIVATE-SETUP-CANARY-36D1A4",
        "kind": "PRIVATE-KIND-CANARY-574BE2",
        "verification": "PRIVATE-VERIFY-CANARY-91AF03",
        "git": "PRIVATE-GIT-CANARY-C4E885",
    }
    projected_canary = task_descriptor(
        {
            "prompt": "Synthetic task prompt.",
            "permitted_effects": [canaries["case"]],
            "expected_evidence_limits": canaries["case"],
            "observable_assertions": [canaries["case"]],
        },
        {
            "kind": canaries["kind"],
            "setup": [canaries["setup"]],
            "files": {},
            "evidence": ["Synthetic evidence."],
            "verification": [canaries["verification"]],
            "git": {"private": canaries["git"]},
        },
    )
    projected_text = json.dumps(projected_canary, ensure_ascii=False)
    leaked_canaries = sorted(name for name, value in canaries.items() if value in projected_text)
    if leaked_canaries:
        raise ValueError(f"grading canaries leaked into task projection: {leaked_canaries}")
    assert_task_projection(projected_canary)
    unsafe_paths = ("../outside", "..\\outside", "nested/..\\outside", "C" + ":/outside", "nested:file")
    for unsafe in unsafe_paths:
        try:
            safe_relative(unsafe)
        except ValueError:
            continue
        raise ValueError(f"unsafe fixture path was accepted: {unsafe}")
    with tempfile.TemporaryDirectory(prefix="poppy-v3-scenarios-") as temporary:
        root = Path(temporary)
        for case_id in sorted(cases):
            fixture = fixtures["fixtures"][case_id]
            validate_fixture(case_id, fixture)
            result = materialize(case_id, root / case_id)
            expected_files = {
                **fixture["files"],
                **fixture.get("git", {}).get("base_files", {}),
                **fixture.get("git", {}).get("mutations", {}),
            }
            for raw, content in expected_files.items():
                expected = render_content(content, root / case_id)
                if resolved_member(root / case_id, raw).read_text(encoding="utf-8") != expected:
                    raise ValueError(f"materialized content mismatch for {case_id}: {raw}")
            descriptor = json.loads((root / case_id / "task.json").read_text(encoding="utf-8"))
            if descriptor != task_descriptor(cases[case_id], fixture):
                raise ValueError(f"task projection mismatch for {case_id}")
            assert_task_projection(descriptor)
            if "git" in fixture:
                repository = (
                    root / case_id
                    if fixture["git"]["repository_root"] == "."
                    else resolved_member(root / case_id, fixture["git"]["repository_root"])
                )
                observed = run_git(repository, "status", "--porcelain").splitlines()
                if observed != fixture["git"]["expected_status"]:
                    raise ValueError(f"verified git status mismatch for {case_id}: {observed}")
            digests[case_id] = result["fixture_digest_sha256"]
    return {
        "status": "pass",
        "scenarios": len(cases),
        "fixture_digests": digests,
        "task_projection": {
            "behavior_fields": ["prompt", "evidence.evidence", "materialized fixture files"],
            "grading_only_fields_excluded": sorted(GRADING_ONLY_FIELDS),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario_id", nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-catalog", action="store_true")
    args = parser.parse_args()
    if args.verify_catalog:
        print(json.dumps(verify_catalog(), indent=2))
        return 0
    if not args.scenario_id or args.output is None:
        parser.error("scenario_id and --output are required unless --verify-catalog is used")
    print(json.dumps(materialize(args.scenario_id, args.output), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
