#!/usr/bin/env python3
"""Validate a normalized Project Operations operational-control packet."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


FINGERPRINT = re.compile(r"[0-9a-f]{64}")
SOURCE_REVISION = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
DIGEST = re.compile(r"(?:sha256|sha512):[0-9a-f]{64,128}")
RETRIEVAL_STATES = {"success", "not-modified", "partial", "failed"}
SOURCE_STATES = {"resolved", "gray", "rejected"}
HEALTH_STATES = {"Green", "Yellow", "Red", "Gray"}
RELEASE_STATES = {"verified", "Gray"}
SENSITIVITY = {"public", "client", "internal", "confidential", "restricted"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return {}
    return value


def _array(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return []
    return value


def _string(value: Any, path: str, errors: list[str]) -> str:
    if not _nonempty(value):
        errors.append(f"{path} must be a non-empty string")
        return ""
    return value.strip()


def _strings(value: Any, path: str, errors: list[str]) -> list[str]:
    items = _array(value, path, errors)
    strings: list[str] = []
    for index, item in enumerate(items):
        if not _nonempty(item):
            errors.append(f"{path}[{index}] must be a non-empty string")
        else:
            strings.append(item.strip())
    if len(strings) != len(set(strings)):
        errors.append(f"{path} must not contain duplicates")
    return strings


def _moment(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not _nonempty(value):
        errors.append(f"{path} must be an ISO-8601 timestamp")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{path} must include a timezone")
        return None
    return parsed


def _unique_objects(
    values: Any, path: str, errors: list[str]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    objects: list[dict[str, Any]] = []
    indexed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(_array(values, path, errors)):
        item_path = f"{path}[{index}]"
        obj = _object(item, item_path, errors)
        if not obj:
            continue
        item_id = _string(obj.get("id"), f"{item_path}.id", errors)
        if item_id in indexed:
            errors.append(f"{item_path}.id must be unique")
        elif item_id:
            indexed[item_id] = obj
        objects.append(obj)
    return objects, indexed


def _validate_coverage(packet: dict[str, Any], errors: list[str]) -> None:
    coverage = _object(packet.get("coverage"), "coverage", errors)
    status = coverage.get("status")
    if status not in {"full", "partial", "gray"}:
        errors.append("coverage.status must be full, partial, or gray")
    limitations = _strings(coverage.get("limitations"), "coverage.limitations", errors)
    if status == "full" and limitations:
        errors.append("full coverage cannot declare limitations")
    if status in {"partial", "gray"} and not limitations:
        errors.append(f"{status} coverage requires at least one limitation")


def _validate_retrieval(
    packet: dict[str, Any], errors: list[str]
) -> tuple[set[str], set[str]]:
    retrieval = _object(packet.get("retrieval"), "retrieval", errors)
    logical, logical_by_id = _unique_objects(
        retrieval.get("logical_requests"), "retrieval.logical_requests", errors
    )
    seen_requests: set[tuple[str, str, str]] = set()
    source_ids: set[str] = set()
    evidence_refs: set[str] = set()
    for index, request in enumerate(logical):
        path = f"retrieval.logical_requests[{index}]"
        provider = _string(request.get("provider"), f"{path}.provider", errors)
        source_id = _string(request.get("stable_source_id"), f"{path}.stable_source_id", errors)
        source_ids.add(source_id)
        fingerprint = _string(request.get("fingerprint"), f"{path}.fingerprint", errors)
        if fingerprint and not FINGERPRINT.fullmatch(fingerprint):
            errors.append(f"{path}.fingerprint must be a lowercase SHA-256 digest")
        _string(request.get("purpose"), f"{path}.purpose", errors)
        key = (provider.casefold(), source_id, fingerprint)
        if key in seen_requests:
            errors.append(f"{path} duplicates an existing logical request")
        seen_requests.add(key)

        attempts = _array(request.get("attempts"), f"{path}.attempts", errors)
        if not attempts:
            errors.append(f"{path}.attempts must contain at least one physical attempt")
            continue
        retained = set(
            _strings(request.get("retained_failure_refs"), f"{path}.retained_failure_refs", errors)
        )
        states: list[str] = []
        for attempt_index, item in enumerate(attempts, start=1):
            attempt_path = f"{path}.attempts[{attempt_index - 1}]"
            attempt = _object(item, attempt_path, errors)
            if attempt.get("physical_attempt") != attempt_index:
                errors.append(f"{attempt_path}.physical_attempt must be {attempt_index}")
            state = attempt.get("status")
            if state not in RETRIEVAL_STATES:
                errors.append(f"{attempt_path}.status is invalid")
                continue
            states.append(state)
            result_ref = attempt.get("result_ref")
            failure_ref = attempt.get("failure_ref")
            if state in {"success", "not-modified"}:
                ref = _string(result_ref, f"{attempt_path}.result_ref", errors)
                if ref:
                    evidence_refs.add(ref)
                if failure_ref is not None:
                    errors.append(f"{attempt_path}.failure_ref must be null on success")
            else:
                ref = _string(failure_ref, f"{attempt_path}.failure_ref", errors)
                if ref:
                    evidence_refs.add(ref)
                if ref not in retained:
                    errors.append(f"{attempt_path}.failure_ref must be retained")
                if result_ref is not None:
                    errors.append(f"{attempt_path}.result_ref must be null on failure or partial")
        final_state = states[-1] if states else None
        before = request.get("checkpoint_before")
        after = request.get("checkpoint_after")
        if before is not None and not _nonempty(before):
            errors.append(f"{path}.checkpoint_before must be null or a non-empty string")
        if after is not None and not _nonempty(after):
            errors.append(f"{path}.checkpoint_after must be null or a non-empty string")
        if final_state in {"failed", "partial"} and after != before:
            errors.append(f"{path} cannot advance its checkpoint after {final_state}")
        if final_state not in {"success", "not-modified"} and after != before:
            errors.append(f"{path} advances a checkpoint without a successful final attempt")

    for index, item in enumerate(_array(retrieval.get("reuse_events"), "retrieval.reuse_events", errors)):
        path = f"retrieval.reuse_events[{index}]"
        reuse = _object(item, path, errors)
        logical_id = _string(reuse.get("logical_request_id"), f"{path}.logical_request_id", errors)
        if logical_id and logical_id not in logical_by_id:
            errors.append(f"{path}.logical_request_id references an unknown request")
        _string(reuse.get("consumer"), f"{path}.consumer", errors)
    return source_ids, evidence_refs


def _validate_sources(packet: dict[str, Any], known_sources: set[str], errors: list[str]) -> None:
    sources, source_by_id = _unique_objects(packet.get("source_preflights"), "source_preflights", errors)
    for index, source in enumerate(sources):
        path = f"source_preflights[{index}]"
        source_id = source.get("id")
        locator = _string(source.get("canonical_locator"), f"{path}.canonical_locator", errors)
        if source.get("locator_kind") not in {"stable-id", "verified-root"}:
            errors.append(f"{path}.locator_kind must be stable-id or verified-root")
        status = source.get("status")
        if status not in SOURCE_STATES:
            errors.append(f"{path}.status must be resolved, gray, or rejected")
        retired = _strings(source.get("retired_locators"), f"{path}.retired_locators", errors)
        if locator and locator.casefold() in {item.casefold() for item in retired}:
            errors.append(f"{path}.canonical_locator points to a retired locator")
        mutable = source.get("mutable_target")
        if not isinstance(mutable, bool):
            errors.append(f"{path}.mutable_target must be boolean")
        if mutable:
            _string(source.get("discovery_rule"), f"{path}.discovery_rule", errors)
            _moment(source.get("review_after"), f"{path}.review_after", errors)
        change = _object(source.get("change_control"), f"{path}.change_control", errors)
        if change.get("mode") not in {"change-feed", "conditional", "webhook", "bounded-poll"}:
            errors.append(f"{path}.change_control.mode is invalid")
        supported = change.get("supported")
        if not isinstance(supported, bool):
            errors.append(f"{path}.change_control.supported must be boolean")
        if supported is False:
            _string(change.get("limitation"), f"{path}.change_control.limitation", errors)
            if status != "gray":
                errors.append(f"{path}.status must be gray when incremental control is unsupported")
        elif change.get("limitation") is not None:
            errors.append(f"{path}.change_control.limitation must be null when supported")
    for source_id in sorted(known_sources - set(source_by_id)):
        errors.append(f"source_preflights is missing retrieval source: {source_id}")


def _validate_authority(
    packet: dict[str, Any], evaluated_at: datetime | None, errors: list[str]
) -> dict[str, dict[str, Any]]:
    receipts, receipt_by_id = _unique_objects(
        packet.get("authority_receipts"), "authority_receipts", errors
    )
    for index, receipt in enumerate(receipts):
        path = f"authority_receipts[{index}]"
        _string(receipt.get("source_ref"), f"{path}.source_ref", errors)
        _string(receipt.get("reason"), f"{path}.reason", errors)
        _strings(receipt.get("scope"), f"{path}.scope", errors)
        effective = _moment(receipt.get("effective_at"), f"{path}.effective_at", errors)
        review_after = _moment(receipt.get("review_after"), f"{path}.review_after", errors)
        _string(receipt.get("next_run_assertion"), f"{path}.next_run_assertion", errors)
        if receipt.get("silence_is_approval") is not False:
            errors.append(f"{path}.silence_is_approval must be false")
        status = receipt.get("status")
        if status not in {"active", "expired", "superseded"}:
            errors.append(f"{path}.status is invalid")
        if effective and review_after and review_after <= effective:
            errors.append(f"{path}.review_after must be after effective_at")
        if status == "active" and evaluated_at and review_after and review_after <= evaluated_at:
            errors.append(f"{path} is expired but still marked active")
    return receipt_by_id


def _validate_health(
    packet: dict[str, Any], receipt_by_id: dict[str, dict[str, Any]], errors: list[str]
) -> set[str]:
    assertions, _ = _unique_objects(packet.get("health_assertions"), "health_assertions", errors)
    assertion_ids: set[str] = set()
    for index, assertion in enumerate(assertions):
        path = f"health_assertions[{index}]"
        assertion_id = assertion.get("id")
        if isinstance(assertion_id, str):
            assertion_ids.add(assertion_id)
        status = assertion.get("status")
        if status not in HEALTH_STATES:
            errors.append(f"{path}.status must be Green, Yellow, Red, or Gray")
        required = set(_strings(assertion.get("required_evidence"), f"{path}.required_evidence", errors))
        observed = set(_strings(assertion.get("observed_evidence"), f"{path}.observed_evidence", errors))
        missing = required - observed
        if missing and status != "Gray":
            errors.append(f"{path}.status must be Gray when required evidence is missing")
        receipt_id = assertion.get("authority_receipt_id")
        if receipt_id is not None:
            if receipt_id not in receipt_by_id:
                errors.append(f"{path}.authority_receipt_id references an unknown receipt")
            elif assertion_id not in receipt_by_id[receipt_id].get("scope", []):
                errors.append(f"{path}.authority_receipt_id does not cover this assertion")
    return assertion_ids


def _release_missing(release: dict[str, Any]) -> list[str]:
    paths = {
        "source": release.get("source_revision"),
        "artifact": _object(release.get("artifact"), "release.artifact", []).get("digest"),
        "build": _object(release.get("artifact"), "release.artifact", []).get("build_id"),
        "delivery": _object(release.get("delivery"), "release.delivery", []).get("event_id"),
        "runtime": _object(release.get("runtime"), "release.runtime", []).get("revision"),
    }
    return sorted(label for label, value in paths.items() if not _nonempty(value))


def _validate_releases(packet: dict[str, Any], errors: list[str]) -> set[str]:
    releases, _ = _unique_objects(packet.get("releases"), "releases", errors)
    release_ids: set[str] = set()
    for index, release in enumerate(releases):
        path = f"releases[{index}]"
        release_id = release.get("id")
        if isinstance(release_id, str):
            release_ids.add(release_id)
        status = release.get("status")
        if status not in RELEASE_STATES:
            errors.append(f"{path}.status must be verified or Gray")
        source_revision = release.get("source_revision")
        if source_revision is not None and (
            not _nonempty(source_revision) or not SOURCE_REVISION.fullmatch(source_revision)
        ):
            errors.append(f"{path}.source_revision must be a full lowercase Git revision")
        artifact = _object(release.get("artifact"), f"{path}.artifact", errors)
        digest = artifact.get("digest")
        if digest is not None and (not _nonempty(digest) or not DIGEST.fullmatch(digest)):
            errors.append(f"{path}.artifact.digest must be a sha256 or sha512 digest")
        for field in ("build_id", "evidence_ref"):
            if artifact.get(field) is not None:
                _string(artifact.get(field), f"{path}.artifact.{field}", errors)
        artifact_revision = artifact.get("source_revision")
        if artifact_revision is not None and artifact_revision != source_revision:
            errors.append(f"{path}.artifact.source_revision must match source_revision")
        delivery = _object(release.get("delivery"), f"{path}.delivery", errors)
        if delivery.get("state") not in {None, "submitted", "accepted", "deployed"}:
            errors.append(f"{path}.delivery.state is invalid")
        for field in ("event_id", "evidence_ref"):
            if delivery.get(field) is not None:
                _string(delivery.get(field), f"{path}.delivery.{field}", errors)
        runtime = _object(release.get("runtime"), f"{path}.runtime", errors)
        for field in ("revision", "evidence_ref"):
            if runtime.get(field) is not None:
                _string(runtime.get(field), f"{path}.runtime.{field}", errors)
        runtime_revision = runtime.get("source_revision")
        if runtime_revision is not None and runtime_revision != source_revision:
            errors.append(f"{path}.runtime.source_revision must match source_revision")
        missing = _release_missing(release)
        declared_missing = _strings(release.get("missing_links"), f"{path}.missing_links", errors)
        if declared_missing != missing:
            errors.append(f"{path}.missing_links must exactly match missing tuple links: {missing}")
        if status == "verified" and missing:
            errors.append(f"{path}.status cannot be verified with missing tuple links")
        if status == "Gray" and not missing:
            errors.append(f"{path}.status cannot be Gray when every tuple link is present")
    return release_ids


def _validate_report(
    packet: dict[str, Any], known_claim_ids: set[str], errors: list[str]
) -> None:
    report = _object(packet.get("report"), "report", errors)
    audience = report.get("audience")
    if audience not in {"internal", "client"}:
        errors.append("report.audience must be internal or client")
    body = _string(report.get("executive_body"), "report.executive_body", errors)
    cap = report.get("word_cap")
    if not isinstance(cap, int) or isinstance(cap, bool) or not 1 <= cap <= 750:
        errors.append("report.word_cap must be an integer from 1 to 750")
    elif len(re.findall(r"\b\w[\w'-]*\b", body)) > cap:
        errors.append("report.executive_body exceeds report.word_cap")
    if report.get("outcome_first") is not True:
        errors.append("report.outcome_first must be true")
    sections = _strings(report.get("sections"), "report.sections", errors)
    if not sections or sections[0] != "state-and-decision":
        errors.append("report.sections must begin with state-and-decision")
    appendix = set(
        _strings(report.get("evidence_appendix_refs"), "report.evidence_appendix_refs", errors)
    )
    claims, _ = _unique_objects(report.get("claims"), "report.claims", errors)
    for index, claim in enumerate(claims):
        path = f"report.claims[{index}]"
        claim_id = claim.get("id")
        if claim_id not in known_claim_ids:
            errors.append(f"{path}.id references an unknown health assertion or release")
        sensitivity = claim.get("sensitivity")
        if sensitivity not in SENSITIVITY:
            errors.append(f"{path}.sensitivity is invalid")
        included = claim.get("included")
        if not isinstance(included, bool):
            errors.append(f"{path}.included must be boolean")
        evidence = set(_strings(claim.get("evidence_refs"), f"{path}.evidence_refs", errors))
        if claim.get("material") is not True:
            errors.append(f"{path}.material must be true for a normalized report claim")
        if included and not evidence:
            errors.append(f"{path} is included without evidence references")
        if included and not evidence.issubset(appendix):
            errors.append(f"{path}.evidence_refs are missing from the evidence appendix")
        if audience == "client" and included and sensitivity in {"internal", "confidential", "restricted"}:
            errors.append(f"{path} leaks non-client evidence into a client report")
        if not included:
            _string(claim.get("filtered_reason"), f"{path}.filtered_reason", errors)


def validate_packet(value: Any) -> list[str]:
    errors: list[str] = []
    packet = _object(value, "packet", errors)
    if packet.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    _string(packet.get("project"), "project", errors)
    _string(packet.get("run_id"), "run_id", errors)
    evaluated_at = _moment(packet.get("evaluated_at"), "evaluated_at", errors)
    _validate_coverage(packet, errors)
    source_ids, _ = _validate_retrieval(packet, errors)
    _validate_sources(packet, source_ids, errors)
    receipts = _validate_authority(packet, evaluated_at, errors)
    health_ids = _validate_health(packet, receipts, errors)
    release_ids = _validate_releases(packet, errors)
    _validate_report(packet, health_ids | release_ids, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        with args.packet.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    else:
        errors = validate_packet(value)
    if args.as_json:
        print(json.dumps({"valid": not errors, "errors": errors}, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("VALID")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
