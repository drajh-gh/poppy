"""Capability-registry invariants owned by POP-V2-004."""

from __future__ import annotations

import copy
import re
from typing import Any

from .authority import canonical_digest


ENTRY_BY_CODE = {
    "POP2-INV-CAP-507": "invariant.capability.registry-snapshot-immutable",
    "POP2-INV-CAP-508": "invariant.capability.contract-identity-immutable",
    "POP2-INV-CAP-509": "invariant.capability.references-resolve-exactly",
    "POP2-INV-CAP-510": "invariant.capability.effect-ceiling-not-exceeded",
    "POP2-INV-CAP-511": "invariant.capability.claim-gate-satisfied",
    "POP2-INV-CAP-512": "invariant.capability.executor-role-permitted",
    "POP2-INV-CAP-513": "invariant.capability.run-binding-exact",
    "POP2-INT-CAP-514": "invariant.capability.kernel-compatible",
    "POP2-INT-CAP-515": "invariant.capability.implementation-matches-contract",
}
SEMVER = re.compile(
    r"^(0|[1-9][0-9]*)[.](0|[1-9][0-9]*)[.](0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:[.][0-9A-Za-z-]+)*))?"
    r"(?:[+]([0-9A-Za-z-]+(?:[.][0-9A-Za-z-]+)*))?$"
)


def _finding(code: str, pointer: str, message: str) -> dict[str, str]:
    return {
        "code": code,
        "owner_decision_id": "POP-V2-004",
        "manifest_entry_id": ENTRY_BY_CODE[code],
        "layer": "ASSEMBLY" if code.startswith("POP2-INT-") else "INVARIANT",
        "locator": "synthetic:capability-bundle",
        "json_pointer": pointer,
        "message": message,
    }


def _digest_without(value: Any, field: str) -> str | None:
    if not isinstance(value, dict):
        return None
    candidate = copy.deepcopy(value)
    candidate.pop(field, None)
    return canonical_digest(candidate)


def registry_snapshot_digest(registry: dict[str, Any]) -> str:
    """Hash a complete immutable registry snapshot excluding its self digest."""
    value = _digest_without(registry, "registry_digest")
    if value is None:
        raise ValueError("registry snapshot must be an object")
    return value


def capability_contract_digest(contract: dict[str, Any]) -> str:
    """Hash a complete immutable capability contract excluding its self digest."""
    value = _digest_without(contract, "contract_digest")
    if value is None:
        raise ValueError("capability contract must be an object")
    return value


def capability_binding_digest(binding: dict[str, Any]) -> str:
    """Hash an exact run binding excluding its self digest."""
    value = _digest_without(binding, "binding_digest")
    if value is None:
        raise ValueError("capability binding must be an object")
    return value


def _record_digest(record: Any, field: str) -> str | None:
    return _digest_without(record, field)


def _semver(value: Any) -> tuple[tuple[int, int, int], tuple[tuple[bool, int | str], ...] | None] | None:
    if not isinstance(value, str):
        return None
    match = SEMVER.fullmatch(value)
    if match is None:
        return None
    prerelease = match.group(4)
    identifiers: list[tuple[bool, int | str]] = []
    if prerelease is not None:
        for identifier in prerelease.split("."):
            if identifier.isdigit():
                if len(identifier) > 1 and identifier.startswith("0"):
                    return None
                identifiers.append((True, int(identifier)))
            else:
                identifiers.append((False, identifier))
    return (
        tuple(int(match.group(index)) for index in range(1, 4)),
        tuple(identifiers) if prerelease is not None else None,
    )


def _semver_precedence(left: Any, right: Any) -> int | None:
    """Compare SemVer 2.0 precedence, intentionally ignoring build metadata."""
    left_value = _semver(left)
    right_value = _semver(right)
    if left_value is None or right_value is None:
        return None
    left_core, left_pre = left_value
    right_core, right_pre = right_value
    if left_core != right_core:
        return -1 if left_core < right_core else 1
    if left_pre is None or right_pre is None:
        if left_pre is right_pre:
            return 0
        return 1 if left_pre is None else -1
    for left_identifier, right_identifier in zip(left_pre, right_pre):
        if left_identifier == right_identifier:
            continue
        left_numeric, left_token = left_identifier
        right_numeric, right_token = right_identifier
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return -1 if left_token < right_token else 1
    if len(left_pre) == len(right_pre):
        return 0
    return -1 if len(left_pre) < len(right_pre) else 1


def _inside_half_open_interval(value: Any, minimum: Any, maximum_exclusive: Any) -> bool:
    lower = _semver_precedence(value, minimum)
    upper = _semver_precedence(value, maximum_exclusive)
    return lower is not None and upper is not None and lower >= 0 and upper < 0


def _unique_strings(values: Any) -> bool:
    return (
        isinstance(values, list)
        and all(isinstance(item, str) and item for item in values)
        and len(values) == len(set(values))
    )


def _contract_key(contract: dict[str, Any]) -> str | None:
    contract_id = contract.get("contract_id")
    version = contract.get("contract_version")
    if not isinstance(contract_id, str) or not isinstance(version, str):
        return None
    return f"{contract_id}@{version}"


def _schema_bindings(contract: dict[str, Any]) -> list[dict[str, Any]]:
    bindings = contract.get("schema_bindings")
    if not isinstance(bindings, dict):
        return []
    return [value for value in bindings.values() if isinstance(value, dict)]


def _contract_for_binding(registry: Any, binding: Any) -> dict[str, Any] | None:
    if not isinstance(registry, dict) or not isinstance(binding, dict):
        return None
    contracts = registry.get("contracts")
    if not isinstance(contracts, list):
        return None
    matches = [
        item for item in contracts
        if isinstance(item, dict)
        and item.get("contract_id") == binding.get("contract_id")
        and item.get("contract_version") == binding.get("contract_version")
    ]
    return matches[0] if len(matches) == 1 else None


def validate_capability_invariants(bundle: dict[str, Any], trusted_anchors: dict[str, Any]) -> list[dict[str, str]]:
    """Validate one runtime use against an independently trusted registry identity.

    Caller-supplied registry, contracts, bindings, claims, authority outcomes, and
    implementation identities never attest themselves. Missing or corrupt anchors
    therefore fail only the affected capability boundary.
    """
    findings: list[dict[str, str]] = []
    registry = bundle.get("registry") if isinstance(bundle, dict) else None
    binding = bundle.get("run_binding") if isinstance(bundle, dict) else None
    capability_anchor = trusted_anchors.get("capability") if isinstance(trusted_anchors, dict) else None
    anchor_complete = isinstance(capability_anchor, dict)
    anchor = capability_anchor if isinstance(capability_anchor, dict) else {}

    registry_identity = anchor.get("registry_identity")
    registry_invalid = (
        not isinstance(registry, dict)
        or not isinstance(registry_identity, dict)
        or registry.get("registry_digest") != registry_snapshot_digest(registry) if isinstance(registry, dict) else True
    )
    if isinstance(registry, dict):
        registry_invalid = registry_invalid or (
            not anchor_complete
            or anchor.get("registry_snapshot_digest") != canonical_digest(registry)
            or registry_identity != {
                "registry_id": registry.get("registry_id"),
                "registry_version": registry.get("registry_version"),
                "registry_digest": registry.get("registry_digest"),
            }
        )
        contracts = registry.get("contracts")
        keys = [_contract_key(item) for item in contracts if isinstance(item, dict)] if isinstance(contracts, list) else []
        registry_invalid = registry_invalid or not _unique_strings(keys) or len(keys) != len(contracts or [])
    if registry_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-507", "/registry",
            "the registry snapshot must be immutable, self-consistent, uniquely versioned, and independently anchored",
        ))

    contracts = registry.get("contracts", []) if isinstance(registry, dict) else []
    contract_values = [item for item in contracts if isinstance(item, dict)] if isinstance(contracts, list) else []
    anchored_contracts = anchor.get("contract_record_digests")
    actual_contracts = {
        key: canonical_digest(item)
        for item in contract_values
        if (key := _contract_key(item)) is not None
    }
    contract_invalid = (
        not isinstance(anchored_contracts, dict)
        or actual_contracts != anchored_contracts
        or len(actual_contracts) != len(contract_values)
        or any(item.get("contract_digest") != capability_contract_digest(item) for item in contract_values)
        or any(
            requirement.get("requirement_digest") != _record_digest(requirement, "requirement_digest")
            for item in contract_values
            for field in ("required_claims", "authority_requirements")
            for requirement in item.get(field, [])
            if isinstance(requirement, dict)
        )
        or any(
            not isinstance(item.get("compatibility"), dict)
            or item["compatibility"].get("declaration_digest") != _record_digest(item["compatibility"], "declaration_digest")
            for item in contract_values
        )
    )
    if contract_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-508", "/registry/contracts",
            "contract id, version, content digest, and independently anchored record identity must agree exactly",
        ))

    trusted_schemas = anchor.get("schema_bindings")
    reference_invalid = not isinstance(trusted_schemas, dict)
    for contract in contract_values:
        direct_bindings = _schema_bindings(contract)
        if len(direct_bindings) != 3:
            reference_invalid = True
        requirement_bindings = [
            item.get("claim_schema") for item in contract.get("required_claims", [])
            if isinstance(item, dict) and isinstance(item.get("claim_schema"), dict)
        ] + [
            item.get("authority_schema") for item in contract.get("authority_requirements", [])
            if isinstance(item, dict) and isinstance(item.get("authority_schema"), dict)
        ]
        bindings = direct_bindings + requirement_bindings
        for schema_binding in bindings:
            schema_id = schema_binding.get("schema_id")
            schema_version = schema_binding.get("schema_version")
            schema_digest = schema_binding.get("schema_digest")
            key = f"{schema_id}@{schema_version}"
            if (
                not isinstance(schema_id, str)
                or not isinstance(schema_version, str)
                or not isinstance(schema_digest, str)
                or "latest" in key.casefold()
                or not isinstance(trusted_schemas, dict)
                or trusted_schemas.get(key) != schema_digest
            ):
                reference_invalid = True
    if reference_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-509", "/registry/contracts/schema_bindings",
            "input, output, and verification schemas must resolve by exact independently trusted id, version, and digest",
        ))

    contract = _contract_for_binding(registry, binding)
    requested_effects = bundle.get("requested_effect_classes") if isinstance(bundle, dict) else None
    allowed_effects = contract.get("effect_ceiling") if isinstance(contract, dict) else None
    effect_invalid = (
        not anchor_complete
        or not _unique_strings(requested_effects)
        or not _unique_strings(allowed_effects)
        or not set(requested_effects or []).issubset(set(allowed_effects or []))
    )
    if effect_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-510", "/requested_effect_classes",
            "every requested effect class must remain within the exact anchored contract ceiling",
        ))

    claim_records = bundle.get("claim_states") if isinstance(bundle, dict) else None
    authority_records = bundle.get("authority_resolutions") if isinstance(bundle, dict) else None
    anchored_claims = anchor.get("claim_state_digests")
    anchored_authority = anchor.get("authority_resolution_digests")
    claim_invalid = (
        not isinstance(claim_records, list)
        or not isinstance(authority_records, list)
        or not isinstance(anchored_claims, dict)
        or not isinstance(anchored_authority, dict)
        or not isinstance(contract, dict)
    )
    claims_by_requirement = {
        item.get("requirement_id"): item for item in claim_records or []
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    authority_by_requirement = {
        item.get("requirement_id"): item for item in authority_records or []
        if isinstance(item, dict) and isinstance(item.get("requirement_id"), str)
    }
    if len(claims_by_requirement) != len(claim_records or []) or len(authority_by_requirement) != len(authority_records or []):
        claim_invalid = True
    claim_requirements = contract.get("required_claims", []) if isinstance(contract, dict) else []
    authority_requirements = contract.get("authority_requirements", []) if isinstance(contract, dict) else []
    required_claim_ids = {
        item.get("requirement_id") for item in claim_requirements if isinstance(item, dict)
    }
    required_authority_ids = {
        item.get("requirement_id") for item in authority_requirements if isinstance(item, dict)
    }
    if set(claims_by_requirement) != required_claim_ids or set(authority_by_requirement) != required_authority_ids:
        claim_invalid = True
    for requirement in contract.get("required_claims", []) if isinstance(contract, dict) else []:
        if not isinstance(requirement, dict):
            claim_invalid = True
            continue
        requirement_id = requirement.get("requirement_id")
        record = claims_by_requirement.get(requirement_id)
        if (
            not isinstance(record, dict)
            or record.get("claim_class") != requirement.get("claim_class")
            or record.get("state") != "supported"
            or record.get("revision_digest") != anchored_claims.get(requirement_id) if isinstance(anchored_claims, dict) else True
        ):
            claim_invalid = True
    for requirement in contract.get("authority_requirements", []) if isinstance(contract, dict) else []:
        if not isinstance(requirement, dict):
            claim_invalid = True
            continue
        requirement_id = requirement.get("requirement_id")
        record = authority_by_requirement.get(requirement_id)
        if (
            not isinstance(record, dict)
            or record.get("outcome") != "authorized"
            or record.get("resolution_digest") != anchored_authority.get(requirement_id) if isinstance(anchored_authority, dict) else True
            or requirement.get("registration_grants_authority") is not False
        ):
            claim_invalid = True
    if claim_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-511", "/claim_states",
            "required claims must be supported and required authority must be currently authorized by independent anchored evidence",
        ))

    executor = bundle.get("executor") if isinstance(bundle, dict) else None
    role_catalog = registry.get("executor_role_catalog") if isinstance(registry, dict) else None
    roles = role_catalog.get("roles") if isinstance(role_catalog, dict) else None
    role_ids = [item.get("role_id") for item in roles if isinstance(item, dict)] if isinstance(roles, list) else []
    role_invalid = (
        not isinstance(executor, dict)
        or not isinstance(role_catalog, dict)
        or role_catalog.get("registration_grants_authority") is not False
        or role_catalog.get("catalog_digest") != _record_digest(role_catalog, "catalog_digest")
        or anchor.get("role_catalog_digest") != canonical_digest(role_catalog)
        or not _unique_strings(role_ids)
        or executor.get("role_id") not in role_ids
        or not isinstance(contract, dict)
        or executor.get("role_id") not in contract.get("permitted_executor_roles", [])
        or any(item.get("authority_capability") is not False for item in roles or [] if isinstance(item, dict))
    )
    if role_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-512", "/executor/role_id",
            "the executor role must be uniquely cataloged, explicitly permitted, and must not acquire authority by registration",
        ))

    run_context = bundle.get("run_context") if isinstance(bundle, dict) else None
    binding_invalid = (
        not isinstance(binding, dict)
        or not isinstance(run_context, dict)
        or not isinstance(registry, dict)
        or not isinstance(contract, dict)
        or binding.get("binding_digest") != capability_binding_digest(binding) if isinstance(binding, dict) else True
    )
    if isinstance(binding, dict) and isinstance(run_context, dict) and isinstance(registry, dict) and isinstance(contract, dict):
        binding_invalid = binding_invalid or (
            anchor.get("run_binding_digest") != canonical_digest(binding)
            or binding.get("run_id") != run_context.get("run_id")
            or binding.get("registry_id") != registry.get("registry_id")
            or binding.get("registry_version") != registry.get("registry_version")
            or binding.get("registry_digest") != registry.get("registry_digest")
            or binding.get("contract_id") != contract.get("contract_id")
            or binding.get("contract_version") != contract.get("contract_version")
            or binding.get("contract_digest") != contract.get("contract_digest")
            or "latest" in str(binding.get("contract_version", "")).casefold()
        )
    if binding_invalid:
        findings.append(_finding(
            "POP2-INV-CAP-513", "/run_binding",
            "the run must bind one exact independently anchored registry and capability-contract version and digest",
        ))

    compatibility = contract.get("compatibility") if isinstance(contract, dict) else None
    compatibility_invalid = (
        not anchor_complete
        or not isinstance(compatibility, dict)
        or compatibility.get("declaration_digest") != _record_digest(compatibility, "declaration_digest")
        or not isinstance(run_context, dict)
    )
    if isinstance(compatibility, dict) and isinstance(run_context, dict):
        compatibility_invalid = compatibility_invalid or not _inside_half_open_interval(
            run_context.get("kernel_version"),
            compatibility.get("kernel_minimum"),
            compatibility.get("kernel_maximum_exclusive"),
        )
        compatibility_invalid = compatibility_invalid or not _inside_half_open_interval(
            run_context.get("run_contract_version"),
            compatibility.get("run_contract_minimum"),
            compatibility.get("run_contract_maximum_exclusive"),
        )
    if compatibility_invalid:
        findings.append(_finding(
            "POP2-INT-CAP-514", "/run_context/kernel_version",
            "kernel and run-contract versions must fall inside their declared half-open compatibility intervals",
        ))

    implementation_invalid = (
        not isinstance(executor, dict)
        or not isinstance(contract, dict)
        or executor.get("implementation_uri") != contract.get("implementation_uri")
        or executor.get("implementation_digest") != contract.get("implementation_digest")
        or anchor.get("implementation_identity_digest") != canonical_digest({
            "implementation_uri": executor.get("implementation_uri") if isinstance(executor, dict) else None,
            "implementation_digest": executor.get("implementation_digest") if isinstance(executor, dict) else None,
        })
    )
    if implementation_invalid:
        findings.append(_finding(
            "POP2-INT-CAP-515", "/executor/implementation_uri",
            "the logical implementation URI and digest must exactly match both contract and independent identity anchor",
        ))

    return sorted(findings, key=lambda item: (item["code"], item["json_pointer"], item["message"]))
