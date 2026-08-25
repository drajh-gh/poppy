from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from poppy_v2_validation import (  # noqa: E402
    authority_resolution_digest,
    candidate_set_digest,
    canonical_digest,
    effect_authority_subject_digest,
    effect_binding_digest,
    receipt_digest,
    validate_authority_invariants,
    validate_case_catalog,
    validate_effect_invariants,
    validate_evidence_invariants,
    validate_manifest_invariants,
    validate_schema_references,
)
from validate_v2_schemas import (  # noqa: E402
    CASE_CATALOG_PATH,
    MANIFEST_PATH,
    SchemaStore,
    read_json,
    resolve_fixture_ref,
    validate_schema_document,
    validate_repository,
)


FIXTURES = ROOT / "tests" / "v2_schema" / "fixtures"


class FoundationSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = read_json(MANIFEST_PATH)
        cls.entries = {entry["id"]: entry for entry in cls.manifest["entries"]}
        cls.store = SchemaStore()
        cls.instances = read_json(FIXTURES / "schema-instances.json")
        cls.cases = read_json(CASE_CATALOG_PATH)
        cls.authority = read_json(FIXTURES / "authority-bundles.json")
        cls.effects = read_json(FIXTURES / "effect-bundles.json")
        cls.trust_anchors = read_json(FIXTURES / "authority-effect-trust-anchors.json")
        cls.authority_anchors = cls.trust_anchors["authority_bundle"]
        cls.effect_anchors = cls.trust_anchors["effect_bundle"]
        cls.evidence = read_json(FIXTURES / "evidence-bundles.json")

    def test_repository_contract(self) -> None:
        result = validate_repository()
        self.assertEqual(result["status"], "pass", result["errors"])
        self.assertEqual(result["manifest_entries"], 195)
        self.assertEqual(result["implemented_entries"], 47)
        self.assertEqual(result["schemas"], 22)
        self.assertEqual(result["synthetic_cases"], 94)

    def test_every_implemented_schema_has_executable_positive_and_negative_case(self) -> None:
        implemented = [entry for entry in self.manifest["entries"] if entry["kind"] == "schema" and entry["implementation_status"] == "implemented"]
        for entry in implemented:
            with self.subTest(entry=entry["id"]):
                path = ROOT / entry["implementation"]
                schema = read_json(path)
                if entry["id"] == "schema.governance.common-definitions":
                    positive_findings = validate_schema_document(schema, entry, entry["positive_case"])
                    negative = copy.deepcopy(schema)
                    negative.pop("$id")
                    negative_findings = validate_schema_document(negative, entry, entry["negative_case"])
                elif entry["id"] == "schema.governance.schema-manifest":
                    positive_findings = self.store.validate_artifact(self.manifest, schema, entry, locator=entry["positive_case"])
                    negative = copy.deepcopy(self.manifest)
                    negative["accepted_decisions"] = negative["accepted_decisions"][:-1]
                    negative_findings = self.store.validate_artifact(negative, schema, entry, locator=entry["negative_case"])
                else:
                    fixtures = self.instances[entry["id"]]
                    positive_findings = self.store.validate_artifact(fixtures["positive"], schema, entry, locator=entry["positive_case"])
                    negative_findings = self.store.validate_artifact(fixtures["negative"], schema, entry, locator=entry["negative_case"])
                self.assertEqual(positive_findings, [], positive_findings)
                self.assertTrue(negative_findings)
                self.assertEqual({finding["code"] for finding in negative_findings}, {entry["stable_code"]})
                self.assertTrue(all(finding["owner_decision_id"] == entry["owner_decision_id"] for finding in negative_findings))
                negative_case = next(case for case in self.cases["cases"] if case["id"] == entry["negative_case"])
                self.assertEqual(negative_case["expected_codes"], [entry["stable_code"]])

    def test_governance_invariant_cases(self) -> None:
        self.assertEqual(validate_manifest_invariants(self.manifest), [])
        cases: list[tuple[str, dict, str]] = []

        value = copy.deepcopy(self.manifest)
        value["entries"][0]["owner_decision_id"] = "POP-V2-999"
        cases.append(("exact owner", value, "POP2-INV-GOV-011"))

        value = copy.deepcopy(self.manifest)
        value["entries"][0]["status"] = "proposed"
        cases.append(("ratified normative", value, "POP2-INV-GOV-012"))

        value = copy.deepcopy(self.manifest)
        value["entries"][0]["compatibility"]["maximum_exclusive"] = "3.0.0"
        cases.append(("compatibility", value, "POP2-INV-GOV-013"))

        value = copy.deepcopy(self.manifest)
        value["entries"][1]["stable_code"] = value["entries"][0]["stable_code"]
        cases.append(("stable code", value, "POP2-INV-GOV-014"))

        value = copy.deepcopy(self.manifest)
        value["entries"][0]["positive_case"] = "CASE-TV2-GOV-999-POS"
        cases.append(("case pair", value, "POP2-INV-GOV-017"))

        for name, value, expected in cases:
            with self.subTest(case=name):
                self.assertIn(expected, {finding["code"] for finding in validate_manifest_invariants(value)})

        with self.assertRaisesRegex(ValueError, "unresolved schema reference"):
            self.store.resolve("poppy://schema/governance/missing/v1")

        schemas = copy.deepcopy(self.store.by_id)
        schemas["poppy://schema/evidence/claim/v1"]["properties"]["claim_id"]["$ref"] = "poppy://schema/governance/missing/v1"
        self.assertIn("POP2-INV-GOV-015", {finding["code"] for finding in validate_schema_references(schemas)})

        cases_value = copy.deepcopy(self.cases)
        cases_value["cases"][0]["owner_decision_id"] = "POP-V2-999"
        self.assertIn("POP2-INV-GOV-016", {finding["code"] for finding in validate_case_catalog(self.manifest, cases_value)})

        cases_value = copy.deepcopy(self.cases)
        cases_value["cases"] = cases_value["cases"][1:]
        self.assertIn("POP2-INV-GOV-017", {finding["code"] for finding in validate_case_catalog(self.manifest, cases_value)})

        cases_value = copy.deepcopy(self.cases)
        cases_value["cases"].append({
            "id": "CASE-TV2-GOV-999-NEG",
            "entry_id": "schema.governance.schema-manifest",
            "owner_decision_id": "POP-V2-011",
            "polarity": "negative",
            "expected_codes": ["POP2-INV-GOV-016"],
            "fixture_ref": "manifest:negative",
        })
        self.assertIn("POP2-INV-GOV-016", {finding["code"] for finding in validate_case_catalog(self.manifest, cases_value)})

    def test_evidence_invariant_cases(self) -> None:
        base = self.evidence["positive"]
        self.assertEqual(validate_evidence_invariants(base), [])
        mutations: dict[str, dict] = {}

        value = copy.deepcopy(base)
        value["revisions"][1]["state"] = "gray"
        value["revisions"][1]["reason_codes"] = ["missing_evidence"]
        value["revisions"][0]["state"] = "gray"
        value["revisions"][0]["reason_codes"] = ["required_dependency_gray"]
        value["revisions"][0]["dependency_reasons"] = []
        mutations["POP2-INV-EVD-305"] = value

        value = copy.deepcopy(base)
        value["revisions"][0]["revision"] = 2
        mutations["POP2-INV-EVD-306"] = value

        value = copy.deepcopy(base)
        value["revisions"][0]["state"] = "green"
        mutations["POP2-INV-EVD-307"] = value

        value = copy.deepcopy(base)
        value["contradictions"] = [{
            "claim_id": value["claims"][0]["claim_id"],
            "left_observation_id": value["observations"][0]["observation_id"],
            "right_observation_id": value["observations"][0]["observation_id"],
            "status": "resolved",
            "material": False
        }]
        mutations["POP2-INV-EVD-308"] = value

        value = copy.deepcopy(base)
        value["observations"] = value["observations"][1:]
        mutations["POP2-INV-EVD-309"] = value

        value = copy.deepcopy(base)
        value["confidence_score"] = 0.99
        mutations["POP2-INV-EVD-310"] = value

        value = copy.deepcopy(base)
        value["dependencies"].append({
            "dependent_claim_id": value["claims"][1]["claim_id"],
            "dependency_claim_id": value["claims"][0]["claim_id"],
            "relationship": "required"
        })
        mutations["POP2-INV-EVD-311"] = value

        for expected, bundle in mutations.items():
            with self.subTest(code=expected):
                self.assertIn(expected, {finding["code"] for finding in validate_evidence_invariants(bundle)})

    def test_authority_invariant_cases(self) -> None:
        base = self.authority["positive"]
        self.assertEqual(validate_authority_invariants(base, self.authority_anchors), [])
        for expected, fixture in self.authority["negative_by_code"].items():
            with self.subTest(code=expected):
                bundle = self._mutated_authority_bundle(fixture["mutation"])
                anchors = self._anchors_for_authority_mutation(fixture["mutation"], bundle)
                self.assertEqual({finding["code"] for finding in validate_authority_invariants(bundle, anchors)}, {expected})

    def test_effect_invariant_cases(self) -> None:
        base = self.effects["positive"]
        self.assertEqual(validate_effect_invariants(base, self.effect_anchors), [])
        self.assertEqual(effect_binding_digest(base["proposal"]), base["proposal"]["effect_digest"])
        for expected, fixture in self.effects["negative_by_code"].items():
            with self.subTest(code=expected):
                bundle = self._mutated_effect_bundle(fixture["mutation"])
                anchors = self._anchors_for_effect_mutation(fixture["mutation"], bundle)
                self.assertEqual({finding["code"] for finding in validate_effect_invariants(bundle, anchors)}, {expected})

    def test_canonical_authority_identity_helpers(self) -> None:
        left = {"z": "ž", "a": [1, {"β": True}]}
        right = {"a": [1, {"β": True}], "z": "ž"}
        self.assertEqual(canonical_digest(left), canonical_digest(right))
        self.assertRegex(canonical_digest(left), r"^sha256:[0-9a-f]{64}$")

        candidates = copy.deepcopy(self.authority["positive"]["candidates"])
        second = copy.deepcopy(candidates[0])
        second["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
        second["source_ref_id"] = "source.synthetic.second-human"
        self.assertEqual(candidate_set_digest(candidates + [second]), candidate_set_digest([second] + candidates))
        with self.assertRaisesRegex(ValueError, "duplicate candidate_id"):
            candidate_set_digest(candidates + [copy.deepcopy(candidates[0])])
        second["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
        second["source_ref_id"] = candidates[0]["source_ref_id"]
        with self.assertRaisesRegex(ValueError, "duplicate source_ref_id"):
            candidate_set_digest(candidates + [second])

    def test_authority_candidate_and_selection_adversarial_bindings(self) -> None:
        direct_changes = {
            "principal_ref": "human.synthetic.changed",
            "position_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "authority_ref": "human-authority.synthetic.changed",
            "applicability": "inapplicable",
            "freshness": "expired",
            "safety": "denies",
            "specificity": "broader_scope",
        }
        for field, replacement in direct_changes.items():
            with self.subTest(change=field):
                value = copy.deepcopy(self.authority["positive"])
                value["candidates"][0][field] = replacement
                self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        for duplicate_field in ("candidate_id", "source_ref_id"):
            with self.subTest(duplicate=duplicate_field):
                value = copy.deepcopy(self.authority["positive"])
                candidate = copy.deepcopy(value["candidates"][0])
                if duplicate_field == "candidate_id":
                    candidate["source_ref_id"] = "source.synthetic.phantom"
                else:
                    candidate["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
                value["candidates"].append(candidate)
                value["query"]["candidate_source_refs"].append(candidate["source_ref_id"])
                self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        value = copy.deepcopy(self.authority["positive"])
        phantom = copy.deepcopy(value["candidates"][0])
        phantom["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
        phantom["source_ref_id"] = "source.synthetic.phantom"
        value["candidates"].append(phantom)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        value = copy.deepcopy(self.authority["positive"])
        coordinated_phantom = copy.deepcopy(value["candidates"][0])
        coordinated_phantom["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
        coordinated_phantom["source_ref_id"] = "source.synthetic.coordinated-phantom"
        value["candidates"].append(coordinated_phantom)
        value["query"]["candidate_source_refs"].append(coordinated_phantom["source_ref_id"])
        self._refresh_authority_digests(value)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        for name, mutate in (
            ("classification-mismatch", lambda item: item.update(data_class="evidence")),
            ("semantics-mismatch", lambda item: item.update(authority_kind="constrain")),
        ):
            with self.subTest(source_binding=name):
                value = copy.deepcopy(self.authority["positive"])
                mutate(value["candidates"][0])
                self._refresh_authority_digests(value)
                self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        value = copy.deepcopy(self.authority["positive"])
        value["sources"].append(copy.deepcopy(value["sources"][0]))
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        for field, replacement in (("applicability", "inapplicable"), ("freshness", "expired"), ("safety", "denies")):
            with self.subTest(selected_non_viable=field):
                value = copy.deepcopy(self.authority["positive"])
                value["candidates"][0][field] = replacement
                self._refresh_authority_digests(value)
                self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        value = copy.deepcopy(self.authority["positive"])
        value["candidates"][0]["specificity"] = "broader_scope"
        better = copy.deepcopy(value["candidates"][0])
        better["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
        better["source_ref_id"] = "source.synthetic.more-specific"
        better["specificity"] = "exact_scope"
        value["candidates"].append(better)
        value["query"]["candidate_source_refs"].append(better["source_ref_id"])
        source = copy.deepcopy(value["sources"][0])
        source["source_ref_id"] = better["source_ref_id"]
        value["sources"].append(source)
        self._refresh_authority_digests(value)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        legitimate = copy.deepcopy(self.authority["positive"])
        legitimate["registry"]["registry_digest"] = "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd"
        legitimate["registry"]["source_kinds"].append({
            "source_kind_id": "source-kind.accepted-reference",
            "data_class": "instruction",
            "owner_kind": "human",
            "authority_semantics": "reference_only",
            "lifetime": "turn",
        })
        legitimate["sources"][0]["registry_digest"] = legitimate["registry"]["registry_digest"]
        accepted_source = copy.deepcopy(legitimate["sources"][0])
        accepted_source.update({
            "source_ref_id": "source.synthetic.accepted-reference",
            "source_kind_id": "source-kind.accepted-reference",
            "owner_ref": "human.synthetic.reference-002",
            "authority_semantics": "reference_only",
        })
        accepted_candidate = copy.deepcopy(legitimate["candidates"][0])
        accepted_candidate.update({
            "candidate_id": "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3",
            "source_ref_id": accepted_source["source_ref_id"],
            "principal_ref": "human.synthetic.reference-002",
            "authority_kind": "evidence",
            "authority_ref": None,
            "position_digest": "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
        })
        legitimate["sources"].append(accepted_source)
        legitimate["candidates"].append(accepted_candidate)
        legitimate["query"]["candidate_source_refs"].append(accepted_source["source_ref_id"])
        self._refresh_authority_digests(legitimate)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(legitimate, self.authority_anchors)})
        legitimate_anchors = copy.deepcopy(self.authority_anchors)
        self._refresh_authority_anchors(legitimate, legitimate_anchors)
        self.assertEqual(validate_authority_invariants(legitimate, legitimate_anchors), [])

        value = copy.deepcopy(self.authority["positive"])
        value["resolution"]["resolution_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

    def test_authority_trust_anchors_freshness_and_platform_denies(self) -> None:
        self.assertIn(
            "POP2-INV-AUT-109",
            {item["code"] for item in validate_authority_invariants(self.authority["positive"], {})},
        )
        with self.assertRaises(TypeError):
            validate_authority_invariants(self.authority["positive"])  # type: ignore[call-arg]

        coordinated_changes = (
            ("source-scope", lambda value: value["sources"][0].update(scope_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999")),
            ("source-owner", lambda value: value["sources"][0].update(owner_ref="human.synthetic.forged")),
            ("source-expiry", lambda value: value["sources"][0].update(fresh_until="2026-08-24T11:01:00Z")),
            ("source-future", lambda value: value["sources"][0].update(observed_at="2026-08-24T11:01:01Z")),
            ("source-superseded", lambda value: value["sources"][0].update(superseded_by="source.synthetic.replacement")),
            ("candidate-principal", lambda value: value["candidates"][0].update(principal_ref="human.synthetic.forged")),
            ("candidate-position", lambda value: value["candidates"][0].update(position_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999")),
            ("registry-rewrite", lambda value: value["registry"].update(registry_version="1.0.1")),
        )
        for name, mutate in coordinated_changes:
            with self.subTest(coordinated_attack=name):
                value = copy.deepcopy(self.authority["positive"])
                mutate(value)
                self._refresh_authority_digests(value)
                self.assertIn(
                    "POP2-INV-AUT-109",
                    {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)},
                )

        for name, mutate in (
            ("scope", lambda value: value["sources"][0].update(scope_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999")),
            ("future", lambda value: value["sources"][0].update(observed_at="2026-08-24T11:01:01Z")),
            ("expired", lambda value: value["sources"][0].update(fresh_until="2026-08-24T11:01:00Z")),
            ("superseded", lambda value: value["sources"][0].update(superseded_by="source.synthetic.replacement")),
        ):
            with self.subTest(anchored_freshness=name):
                value = copy.deepcopy(self.authority["positive"])
                mutate(value)
                anchors = copy.deepcopy(self.authority_anchors)
                self._refresh_authority_anchors(value, anchors)
                self.assertIn(
                    "POP2-INV-AUT-109",
                    {item["code"] for item in validate_authority_invariants(value, anchors)},
                )

        value = copy.deepcopy(self.authority["positive"])
        fabricated_source = copy.deepcopy(value["sources"][0])
        fabricated_source.update(source_ref_id="source.synthetic.fabricated-human", owner_ref="human.synthetic.fabricated")
        fabricated_candidate = copy.deepcopy(value["candidates"][0])
        fabricated_candidate.update(
            candidate_id="018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3",
            source_ref_id=fabricated_source["source_ref_id"],
            principal_ref="human.synthetic.fabricated",
            authority_ref="human-authority.synthetic.fabricated",
        )
        value["sources"].append(fabricated_source)
        value["candidates"].append(fabricated_candidate)
        value["query"]["candidate_source_refs"].append(fabricated_source["source_ref_id"])
        self._refresh_authority_digests(value)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, self.authority_anchors)})

        value = copy.deepcopy(self.authority["positive"])
        value["registry"]["registry_digest"] = "sha256:abababababababababababababababababababababababababababababababab"
        value["registry"]["source_kinds"].append({
            "source_kind_id": "source-kind.platform-constraint",
            "data_class": "instruction",
            "owner_kind": "platform",
            "authority_semantics": "constrain",
            "lifetime": "run",
        })
        for source in value["sources"]:
            source["registry_digest"] = value["registry"]["registry_digest"]
        constraint_source = copy.deepcopy(value["sources"][0])
        constraint_source.update({
            "source_ref_id": "source.synthetic.platform-deny",
            "source_kind_id": "source-kind.platform-constraint",
            "owner_kind": "platform",
            "owner_ref": "platform.synthetic.safety",
            "authority_semantics": "constrain",
        })
        value["sources"].append(constraint_source)
        constraint = copy.deepcopy(value["candidates"][0])
        constraint.update({
            "candidate_id": "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3",
            "source_ref_id": constraint_source["source_ref_id"],
            "principal_kind": "platform",
            "principal_ref": "platform.synthetic.safety",
            "authority_kind": "constrain",
            "safety": "denies",
            "position_digest": "sha256:abababababababababababababababababababababababababababababababab",
            "authority_ref": None,
            "task_scope_ref": None,
        })
        value["candidates"].append(constraint)
        value["query"]["candidate_source_refs"].append(constraint_source["source_ref_id"])
        self._refresh_authority_digests(value)
        anchors = copy.deepcopy(self.authority_anchors)
        self._refresh_authority_anchors(value, anchors)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, anchors)})
        value["candidates"][1]["safety"] = "narrows"
        self._refresh_authority_digests(value)
        self._refresh_authority_anchors(value, anchors)
        self.assertIn("POP2-INV-AUT-109", {item["code"] for item in validate_authority_invariants(value, anchors)})

    def test_effect_authority_sensitive_fields_and_coordinated_rebinding(self) -> None:
        mutations = {
            "target": lambda value: value["proposal"]["target"].update(locator="synthetic:artifact/changed"),
            "preview": lambda value: value["proposal"].update(preview_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999"),
            "rollback": lambda value: value["proposal"]["rollback"].update(plan_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999"),
            "verification": lambda value: value["proposal"]["verification"].update(plan_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999"),
            "objective": lambda value: value["proposal"].update(objective_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999"),
            "plan_revision": lambda value: value["proposal"].update(plan_revision=4),
            "resolution_id": lambda value: value["proposal"].update(authority_resolution_id="018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac8"),
            "resolution_digest": lambda value: value["proposal"].update(authority_resolution_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999"),
            "authority_ref": lambda value: value["proposal"].update(authority_ref="human-authority.synthetic.changed"),
            "authority_principal": lambda value: value["proposal"].update(authority_principal_kind="platform"),
            "high_risk_approval": lambda value: value["proposal"].update(high_risk_approval_ref="human-approval.synthetic.changed"),
        }
        for name, mutate in mutations.items():
            with self.subTest(field=name):
                value = copy.deepcopy(self.effects["positive"])
                mutate(value)
                self.assertIn("POP2-INV-EFF-205", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["proposal"]["target"]["locator"] = "synthetic:artifact/coordinated-reuse"
        self._rebind_effect_bundle(value, preserve_history=True)
        self.assertIn("POP2-INV-EFF-206", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

    def test_effect_requires_substantively_valid_embedded_authority(self) -> None:
        value = copy.deepcopy(self.effects["positive"])
        value["authority_resolution"]["selected_candidate_ids"] = ["018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac9"]
        self._rebind_effect_bundle(value)
        self.assertIn("POP2-INV-EFF-205", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["authority_candidates"][0]["freshness"] = "expired"
        self._rebind_effect_bundle(value)
        self.assertIn("POP2-INV-EFF-205", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["authority_candidates"][0]["source_ref_id"] = "source.synthetic.phantom"
        self._rebind_effect_bundle(value)
        self.assertIn("POP2-INV-EFF-205", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["authority_query"]["candidate_set_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
        self.assertIn("POP2-INV-EFF-205", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["authority_candidates"][0]["authority_ref"] = "human-authority.synthetic.forged"
        self._rebind_effect_bundle(value)
        self.assertIn("POP2-INV-EFF-205", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["proposal"]["target"]["locator"] = "synthetic:artifact/new-authority"
        value["proposal"]["authority_resolution_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac8"
        self._rebind_effect_bundle(value, preserve_history=True)
        self.assertIn("POP2-INV-EFF-206", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})
        updated_anchors = copy.deepcopy(self.effect_anchors)
        self._refresh_effect_anchors(value, updated_anchors)
        self.assertEqual(validate_effect_invariants(value, updated_anchors), [])

        value = copy.deepcopy(self.effects["positive"])
        value["proposal"]["objective_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
        value["proposal"]["plan_revision"] = 4
        self._rebind_effect_bundle(value, preserve_history=True)
        self.assertIn("POP2-INV-EFF-206", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

    def test_high_risk_approval_records_are_exact_and_human(self) -> None:
        value = copy.deepcopy(self.effects["positive"])
        value["proposal"]["effect_class"] = "destructive"
        value["proposal"]["high_risk_approval_ref"] = "human-approval.synthetic.destructive-001"
        value["high_risk_approvals"] = [{
            "approval_ref": "human-approval.synthetic.destructive-001",
            "principal_kind": "human",
            "principal_ref": "human.synthetic.approver-002",
            "effect_digest": "sha256:placeholder",
            "approved_at": "2026-08-24T11:03:30Z",
        }]
        self._rebind_effect_bundle(value)
        high_risk_anchors = copy.deepcopy(self.effect_anchors)
        self._refresh_effect_anchors(value, high_risk_anchors)
        self.assertEqual(validate_effect_invariants(value, high_risk_anchors), [])

        for name, mutate in (
            ("missing", lambda item: item.clear()),
            ("worker", lambda item: item.update(principal_kind="internal_worker")),
            ("wrong-effect", lambda item: item.update(effect_digest="sha256:9999999999999999999999999999999999999999999999999999999999999999")),
            ("same-as-authority", lambda item: item.update(approval_ref="human-authority.synthetic.owner-001")),
        ):
            with self.subTest(invalid=name):
                invalid = copy.deepcopy(value)
                mutate(invalid["high_risk_approvals"][0])
                if name == "same-as-authority":
                    invalid["proposal"]["high_risk_approval_ref"] = invalid["proposal"]["authority_ref"]
                    self._rebind_effect_bundle(invalid)
                self.assertIn("POP2-INV-EFF-207", {item["code"] for item in validate_effect_invariants(invalid, high_risk_anchors)})

    def test_verification_evidence_is_independent_and_time_bound(self) -> None:
        for name in (
            "missing", "attempt-marker", "receipt-self", "attempt-evidence-kind", "unrelated-effect",
            "unrelated-effect-digest", "unrelated-attempt", "mismatched-expected", "mismatched-state",
            "pre-attempt", "early-verified", "duplicate",
        ):
            with self.subTest(invalid=name):
                value = copy.deepcopy(self.effects["positive"])
                evidence = value["verification_evidence"][0]
                if name == "missing":
                    value["verification_evidence"] = []
                elif name == "attempt-marker":
                    value["receipt"]["verification_evidence_refs"] = [f"synthetic:attempt:{value['receipt']['attempt_id']}"]
                elif name == "receipt-self":
                    value["receipt"]["verification_evidence_refs"] = [f"synthetic:receipt:{value['receipt']['receipt_id']}"]
                elif name == "attempt-evidence-kind":
                    evidence["evidence_kind"] = "attempt"
                elif name == "unrelated-effect":
                    evidence["effect_id"] = "effect.synthetic.other-001"
                elif name == "unrelated-effect-digest":
                    evidence["effect_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
                elif name == "unrelated-attempt":
                    evidence["attempt_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac9"
                elif name == "mismatched-expected":
                    evidence["expected_state_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
                elif name == "mismatched-state":
                    evidence["observed_state_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
                elif name == "pre-attempt":
                    evidence["observed_at"] = "2026-08-24T11:03:59Z"
                elif name == "early-verified":
                    value["receipt"]["verified_at"] = "2026-08-24T11:04:15Z"
                elif name == "duplicate":
                    value["verification_evidence"].append(copy.deepcopy(evidence))
                value["receipt"]["receipt_digest"] = receipt_digest(value["receipt"])
                self.assertIn("POP2-INV-EFF-208", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

    def test_attempt_and_receipt_are_unique_and_fully_bound(self) -> None:
        value = copy.deepcopy(self.effects["positive"])
        value["attempts"].append(copy.deepcopy(value["attempts"][0]))
        self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        attempt_changes = {
            "effect_id": "effect.synthetic.other-001",
            "effect_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "authority_resolution_id": "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac8",
            "authority_resolution_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "authority_ref": "human-authority.synthetic.other",
            "target": {"synthetic": "mismatch"},
            "preview_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "objective_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            "plan_revision": 4,
            "attempted_at": "2026-08-24T11:04:10Z",
            "outcome": "failed",
        }
        receipt_changes = {key: value for key, value in attempt_changes.items() if key != "outcome"}
        receipt_changes["attempt_outcome"] = "failed"
        for field, replacement in attempt_changes.items():
            with self.subTest(attempt_mismatch=field):
                value = copy.deepcopy(self.effects["positive"])
                value["attempts"][0][field] = replacement
                self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        for field, replacement in receipt_changes.items():
            with self.subTest(receipt_mismatch=field):
                value = copy.deepcopy(self.effects["positive"])
                value["receipt"][field] = replacement
                value["receipt"]["receipt_digest"] = receipt_digest(value["receipt"])
                self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["receipt"]["receipt_digest"] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
        self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        value = copy.deepcopy(self.effects["positive"])
        value["receipts"] = [copy.deepcopy(value["receipt"]), copy.deepcopy(value["receipt"])]
        self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

    def test_effect_trust_anchors_approval_and_strict_chronology(self) -> None:
        self.assertEqual(validate_effect_invariants(self.effects["positive"], self.effect_anchors), [])
        self.assertIn(
            "POP2-INV-EFF-205",
            {item["code"] for item in validate_effect_invariants(self.effects["positive"], {})},
        )
        with self.assertRaises(TypeError):
            validate_effect_invariants(self.effects["positive"])  # type: ignore[call-arg]

        for anchor_map, expected in (
            ("attempt_digests", "POP2-INV-EFF-209"),
            ("receipt_digests", "POP2-INV-EFF-209"),
            ("verification_evidence_digests", "POP2-INV-EFF-208"),
        ):
            for state in ("missing", "empty", "stale"):
                with self.subTest(anchor_map=anchor_map, state=state):
                    anchors = copy.deepcopy(self.effect_anchors)
                    if state == "missing":
                        anchors["effect"].pop(anchor_map)
                    elif state == "empty":
                        anchors["effect"][anchor_map] = {}
                    else:
                        key = next(iter(anchors["effect"][anchor_map]))
                        anchors["effect"][anchor_map][key] = "sha256:9999999999999999999999999999999999999999999999999999999999999999"
                    self.assertEqual(
                        {item["code"] for item in validate_effect_invariants(self.effects["positive"], anchors)},
                        {expected},
                    )

        attempt_rewrite = copy.deepcopy(self.effects["positive"])
        new_attempt_id = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac8"
        attempt_rewrite["attempts"][0]["attempt_id"] = new_attempt_id
        attempt_rewrite["receipt"]["attempt_id"] = new_attempt_id
        attempt_rewrite["verification_evidence"][0]["attempt_id"] = new_attempt_id
        attempt_rewrite["receipt"]["receipt_digest"] = receipt_digest(attempt_rewrite["receipt"])
        self.assertEqual(
            {item["code"] for item in validate_effect_invariants(attempt_rewrite, self.effect_anchors)},
            {"POP2-INV-EFF-209"},
        )

        receipt_rewrite = copy.deepcopy(self.effects["positive"])
        receipt_rewrite["receipt"]["receipt_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac9"
        receipt_rewrite["receipt"]["receipt_digest"] = receipt_digest(receipt_rewrite["receipt"])
        self.assertEqual(
            {item["code"] for item in validate_effect_invariants(receipt_rewrite, self.effect_anchors)},
            {"POP2-INV-EFF-209"},
        )

        evidence_rewrite = copy.deepcopy(self.effects["positive"])
        new_evidence_ref = "synthetic:readback/demo-renamed"
        evidence_rewrite["verification_evidence"][0]["evidence_ref"] = new_evidence_ref
        evidence_rewrite["receipt"]["verification_evidence_refs"] = [new_evidence_ref]
        evidence_rewrite["receipt"]["receipt_digest"] = receipt_digest(evidence_rewrite["receipt"])
        self.assertEqual(
            {item["code"] for item in validate_effect_invariants(evidence_rewrite, self.effect_anchors)},
            {"POP2-INV-EFF-208"},
        )

        legitimate = copy.deepcopy(self.effects["positive"])
        legitimate["attempts"][0]["attempt_id"] = new_attempt_id
        legitimate["receipt"]["receipt_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac9"
        legitimate["receipt"]["attempt_id"] = new_attempt_id
        legitimate["verification_evidence"][0]["attempt_id"] = new_attempt_id
        legitimate["verification_evidence"][0]["evidence_ref"] = new_evidence_ref
        legitimate["receipt"]["verification_evidence_refs"] = [new_evidence_ref]
        legitimate["receipt"]["receipt_digest"] = receipt_digest(legitimate["receipt"])
        self.assertIn(
            "POP2-INV-EFF-209",
            {item["code"] for item in validate_effect_invariants(legitimate, self.effect_anchors)},
        )
        legitimate_anchors = copy.deepcopy(self.effect_anchors)
        self._refresh_postexecution_anchors(legitimate, legitimate_anchors)
        self.assertEqual(validate_effect_invariants(legitimate, legitimate_anchors), [])

        value = copy.deepcopy(self.effects["positive"])
        value["proposal"]["target"]["locator"] = "synthetic:artifact/same-id-rehash"
        self._rebind_effect_bundle(value)
        self.assertIn("POP2-INV-EFF-206", {item["code"] for item in validate_effect_invariants(value, self.effect_anchors)})

        high_risk = copy.deepcopy(self.effects["positive"])
        high_risk["proposal"]["effect_class"] = "destructive"
        high_risk["proposal"]["high_risk_approval_ref"] = "human-approval.synthetic.destructive-001"
        high_risk["high_risk_approvals"] = [{
            "approval_ref": "human-approval.synthetic.destructive-001",
            "principal_kind": "human",
            "principal_ref": "human.synthetic.approver-002",
            "effect_digest": "sha256:placeholder",
            "approved_at": "2026-08-24T11:03:30Z",
        }]
        self._rebind_effect_bundle(high_risk)
        high_risk_anchors = copy.deepcopy(self.effect_anchors)
        self._refresh_effect_anchors(high_risk, high_risk_anchors)
        self.assertEqual(validate_effect_invariants(high_risk, high_risk_anchors), [])

        for name, mutate in (
            ("self-effect", lambda value: value["high_risk_approvals"][0].update(approval_ref=value["proposal"]["effect_id"])),
            ("self-receipt", lambda value: value["high_risk_approvals"][0].update(approval_ref=value["receipt"]["receipt_id"])),
            ("self-attempt", lambda value: value["high_risk_approvals"][0].update(approval_ref=value["receipt"]["attempt_id"])),
            ("self-digest", lambda value: value["high_risk_approvals"][0].update(approval_ref=value["proposal"]["effect_digest"])),
            ("post-execution", lambda value: value["high_risk_approvals"][0].update(approved_at="2026-08-24T11:04:01Z")),
        ):
            with self.subTest(approval=name):
                invalid = copy.deepcopy(high_risk)
                mutate(invalid)
                invalid["proposal"]["high_risk_approval_ref"] = invalid["high_risk_approvals"][0]["approval_ref"]
                self.assertIn(
                    "POP2-INV-EFF-207",
                    {item["code"] for item in validate_effect_invariants(invalid, high_risk_anchors)},
                )

        fabricated = copy.deepcopy(high_risk)
        fabricated["high_risk_approvals"][0]["principal_ref"] = "human.synthetic.fabricated"
        self.assertIn("POP2-INV-EFF-207", {item["code"] for item in validate_effect_invariants(fabricated, high_risk_anchors)})

        equal_resolution = copy.deepcopy(high_risk)
        equal_resolution["high_risk_approvals"][0]["approved_at"] = equal_resolution["authority_resolution"]["resolved_at"]
        equality_anchors = copy.deepcopy(high_risk_anchors)
        approval_record = equal_resolution["high_risk_approvals"][0]
        equality_anchors["effect"]["approval_digests"] = {
            approval_record["approval_ref"]: canonical_digest(approval_record)
        }
        self.assertEqual(
            {item["code"] for item in validate_effect_invariants(equal_resolution, equality_anchors)},
            {"POP2-INV-EFF-207"},
        )

        for name, mutate in (
            ("attempt-before-resolution", lambda value: value["attempts"][0].update(attempted_at="2026-08-24T11:01:59Z")),
            ("attempt-equal-resolution", lambda value: value["attempts"][0].update(attempted_at="2026-08-24T11:02:00Z")),
            ("attempt-before-proposal", lambda value: value["attempts"][0].update(attempted_at="2026-08-24T11:01:00Z")),
        ):
            with self.subTest(chronology=name):
                invalid = copy.deepcopy(self.effects["positive"])
                mutate(invalid)
                invalid["receipt"]["attempted_at"] = invalid["attempts"][0]["attempted_at"]
                invalid["receipt"]["receipt_digest"] = receipt_digest(invalid["receipt"])
                self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(invalid, self.effect_anchors)})

        equal_times = copy.deepcopy(self.effects["positive"])
        equal_times["verification_evidence"][0]["observed_at"] = equal_times["receipt"]["attempted_at"]
        equal_times["receipt"]["verified_at"] = equal_times["receipt"]["attempted_at"]
        equal_times["receipt"]["receipt_digest"] = receipt_digest(equal_times["receipt"])
        self.assertIn("POP2-INV-EFF-208", {item["code"] for item in validate_effect_invariants(equal_times, self.effect_anchors)})

        extra_attempt = copy.deepcopy(self.effects["positive"])
        extra = copy.deepcopy(extra_attempt["attempts"][0])
        extra["attempt_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac9"
        extra["outcome"] = "failed"
        extra_attempt["attempts"].append(extra)
        self.assertIn("POP2-INV-EFF-209", {item["code"] for item in validate_effect_invariants(extra_attempt, self.effect_anchors)})

    def test_claim_value_null_and_valid_as_of_are_executable(self) -> None:
        entry = self.entries["schema.evidence.claim"]
        schema = self.store.by_id["poppy://schema/evidence/claim/v1"]
        value = copy.deepcopy(self.instances[entry["id"]]["positive"])
        value["value"] = None
        self.assertEqual(self.store.validate_artifact(value, schema, entry, locator="synthetic:claim-null"), [])
        value["valid_as_of"] = None
        self.assertEqual(self.store.validate_artifact(value, schema, entry, locator="synthetic:claim-null-valid-as-of"), [])
        value.pop("valid_as_of")
        findings = self.store.validate_artifact(value, schema, entry, locator="synthetic:claim-missing-valid-as-of")
        self.assertEqual({finding["code"] for finding in findings}, {"POP2-SHP-EVD-300"})

    def test_dependency_reason_paths_bind_exactly_to_non_supported_required_dependencies(self) -> None:
        base = self.evidence["positive"]
        dependent = base["claims"][0]["claim_id"]
        required = base["claims"][1]["claim_id"]
        unrelated = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8a92"

        for name, reason in (("supported", required), ("unrelated", unrelated)):
            with self.subTest(reject=name):
                value = copy.deepcopy(base)
                value["revisions"][0]["dependency_reasons"] = [{
                    "dependency_claim_id": reason,
                    "reason_code": "required_dependency_gray",
                }]
                findings = validate_evidence_invariants(value)
                self.assertIn("POP2-INV-EVD-305", {finding["code"] for finding in findings})

        value = copy.deepcopy(base)
        value["revisions"][1]["state"] = "gray"
        value["revisions"][1]["reason_codes"] = ["missing_evidence"]
        value["revisions"][0]["state"] = "gray"
        value["revisions"][0]["reason_codes"] = ["required_dependency_gray"]
        value["revisions"][0]["dependency_reasons"] = [{
            "dependency_claim_id": required,
            "reason_code": "required_dependency_gray",
        }]
        self.assertEqual(validate_evidence_invariants(value), [])

        value["revisions"][0]["dependency_reasons"].append({
            "dependency_claim_id": dependent,
            "reason_code": "required_dependency_gray",
        })
        findings = validate_evidence_invariants(value)
        self.assertIn("POP2-INV-EVD-305", {finding["code"] for finding in findings})

    def test_all_case_fixture_references_resolve_and_execute(self) -> None:
        for case in self.cases["cases"]:
            with self.subTest(case=case["id"]):
                fixture = resolve_fixture_ref(case["fixture_ref"])
                self.assertIsNotNone(fixture)
                entry = self.entries[case["entry_id"]]
                if entry["kind"] == "schema":
                    schema = read_json(ROOT / entry["implementation"])
                    if case["fixture_ref"].startswith("schema-document:"):
                        candidate = copy.deepcopy(schema)
                        if case["polarity"] == "negative":
                            candidate.pop("$id")
                        findings = validate_schema_document(candidate, entry, case["id"])
                    elif case["fixture_ref"].startswith("manifest:"):
                        candidate = copy.deepcopy(self.manifest)
                        if case["polarity"] == "negative":
                            candidate["accepted_decisions"] = candidate["accepted_decisions"][:-1]
                        findings = self.store.validate_artifact(candidate, schema, entry, locator=case["id"])
                    else:
                        findings = self.store.validate_artifact(fixture, schema, entry, locator=case["id"])
                elif entry["domain"] == "authority":
                    bundle = copy.deepcopy(fixture) if case["polarity"] == "positive" else self._mutated_authority_bundle(fixture["mutation"])
                    anchors = self.authority_anchors if case["polarity"] == "positive" else self._anchors_for_authority_mutation(fixture["mutation"], bundle)
                    findings = validate_authority_invariants(bundle, anchors)
                elif entry["domain"] == "effect":
                    bundle = copy.deepcopy(fixture) if case["polarity"] == "positive" else self._mutated_effect_bundle(fixture["mutation"])
                    anchors = self.effect_anchors if case["polarity"] == "positive" else self._anchors_for_effect_mutation(fixture["mutation"], bundle)
                    findings = validate_effect_invariants(bundle, anchors)
                elif entry["domain"] == "evidence":
                    if case["polarity"] == "positive":
                        bundle = copy.deepcopy(fixture)
                    else:
                        bundle = self._mutated_evidence_bundle(fixture["mutation"])
                    findings = validate_evidence_invariants(bundle)
                else:
                    findings = self._governance_case_findings(entry["stable_code"], case["polarity"])
                actual_codes = {finding["code"] for finding in findings}
                if case["polarity"] == "positive":
                    self.assertEqual(actual_codes, set(), findings)
                elif entry["domain"] in {"authority", "effect"}:
                    self.assertEqual(actual_codes, set(case["expected_codes"]), findings)
                else:
                    self.assertIn(entry["stable_code"], actual_codes, findings)

    def _mutated_authority_bundle(self, mutation: str) -> dict:
        value = copy.deepcopy(self.authority["positive"])
        if mutation == "change-source-classification-outside-registry":
            value["sources"][0]["owner_kind"] = "operator"
        elif mutation == "add-precedence-number":
            value["resolution_policy"] = {"precedence_number": 1}
        elif mutation == "reorder-resolution-checks":
            value["resolution"]["checks"][0:2] = ["authority", "applicability"]
            value["resolution"]["resolution_digest"] = authority_resolution_digest(value["resolution"])
        elif mutation == "change-bound-plan-revision":
            value["resolution"]["plan_revision"] = 4
        elif mutation == "infer-away-authority-conflict":
            candidate = copy.deepcopy(value["candidates"][0])
            candidate["candidate_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac3"
            candidate["source_ref_id"] = "source.synthetic.other-human"
            candidate["principal_ref"] = "human.synthetic.owner-002"
            candidate["authority_ref"] = "human-authority.synthetic.owner-002"
            candidate["position_digest"] = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            value["candidates"].append(candidate)
            value["query"]["candidate_source_refs"].append(candidate["source_ref_id"])
            source = copy.deepcopy(value["sources"][0])
            source["source_ref_id"] = candidate["source_ref_id"]
            source["owner_ref"] = candidate["principal_ref"]
            value["sources"].append(source)
            self._refresh_authority_digests(value)
        elif mutation == "treat-worker-as-human-authority":
            value["candidates"][0]["principal_kind"] = "internal_worker"
            value["candidates"][0]["principal_ref"] = "worker.synthetic.001"
            self._refresh_authority_digests(value)
        else:
            self.fail(f"unknown authority mutation: {mutation}")
        return value

    def _refresh_authority_digests(self, value: dict) -> None:
        digest = candidate_set_digest(value["candidates"])
        value["query"]["candidate_set_digest"] = digest
        value["resolution"]["candidate_set_digest"] = digest
        value["resolution"]["resolution_digest"] = authority_resolution_digest(value["resolution"])

    def _refresh_authority_anchors(self, value: dict, anchors: dict, *, effect_context: bool = False) -> None:
        registry_key = "authority_registry" if effect_context else "registry"
        sources_key = "authority_sources" if effect_context else "sources"
        candidates_key = "authority_candidates" if effect_context else "candidates"
        authority = anchors.setdefault("authority", {})
        authority["registry_digest"] = canonical_digest(value[registry_key])
        authority["source_digests"] = {
            item["source_ref_id"]: canonical_digest(item) for item in value[sources_key]
        }
        authority["candidate_digests"] = {
            item["candidate_id"]: canonical_digest(item) for item in value[candidates_key]
        }

    def _refresh_effect_anchors(self, value: dict, anchors: dict) -> None:
        self._refresh_authority_anchors(value, anchors, effect_context=True)
        effect = anchors.setdefault("effect", {})
        effect["authority_anchor_digest"] = canonical_digest(anchors["authority"])
        effect["proposal_history_digest"] = canonical_digest(value["proposal_history"])
        effect["resolution_bindings"] = {
            item["authority_resolution_id"]: {
                "authority_resolution_digest": item["authority_resolution_digest"],
                "effect_digest": item["effect_digest"],
            }
            for item in value["proposal_history"]
        }
        effect["approval_digests"] = {
            item["approval_ref"]: canonical_digest(item) for item in value.get("high_risk_approvals", [])
        }
        self._refresh_postexecution_anchors(value, anchors)

    def _refresh_postexecution_anchors(self, value: dict, anchors: dict) -> None:
        effect = anchors.setdefault("effect", {})
        effect["attempt_digests"] = {
            item["attempt_id"]: canonical_digest(item) for item in value.get("attempts", [])
        }
        receipt = value.get("receipt", {})
        effect["receipt_digests"] = (
            {receipt["receipt_id"]: canonical_digest(receipt)}
            if isinstance(receipt, dict) and isinstance(receipt.get("receipt_id"), str)
            else {}
        )
        effect["verification_evidence_digests"] = {
            item["evidence_ref"]: canonical_digest(item)
            for item in value.get("verification_evidence", [])
        }

    def _anchors_for_authority_mutation(self, mutation: str, value: dict) -> dict:
        anchors = copy.deepcopy(self.authority_anchors)
        if mutation in {
            "change-source-classification-outside-registry",
            "infer-away-authority-conflict",
            "treat-worker-as-human-authority",
        }:
            self._refresh_authority_anchors(value, anchors)
        return anchors

    def _anchors_for_effect_mutation(self, mutation: str, value: dict) -> dict:
        anchors = copy.deepcopy(self.effect_anchors)
        if mutation == "omit-distinct-high-risk-approval":
            self._refresh_effect_anchors(value, anchors)
        elif mutation == "change-target-after-authority":
            self._refresh_postexecution_anchors(value, anchors)
        elif mutation == "treat-attempt-as-verification":
            receipt = value["receipt"]
            anchors["effect"]["receipt_digests"] = {
                receipt["receipt_id"]: canonical_digest(receipt)
            }
        elif mutation == "receipt-without-authorized-attempt":
            receipt = value["receipt"]
            anchors["effect"]["receipt_digests"] = {
                receipt["receipt_id"]: canonical_digest(receipt)
            }
            anchors["effect"]["verification_evidence_digests"] = {
                item["evidence_ref"]: canonical_digest(item)
                for item in value["verification_evidence"]
            }
        return anchors

    def _mutated_effect_bundle(self, mutation: str) -> dict:
        value = copy.deepcopy(self.effects["positive"])
        if mutation == "change-target-after-authority":
            value["proposal"]["target"]["locator"] = "synthetic:artifact/demo-changed"
            value["attempts"][0]["target"] = copy.deepcopy(value["proposal"]["target"])
            value["receipt"]["target"] = copy.deepcopy(value["proposal"]["target"])
            value["receipt"]["receipt_digest"] = receipt_digest(value["receipt"])
        elif mutation == "reuse-authority-after-effect-change":
            value["proposal_history"].append({
                "authority_resolution_id": value["proposal"]["authority_resolution_id"],
                "authority_resolution_digest": value["proposal"]["authority_resolution_digest"],
                "effect_digest": "sha256:9999999999999999999999999999999999999999999999999999999999999999",
            })
        elif mutation == "omit-distinct-high-risk-approval":
            value["proposal"]["effect_class"] = "destructive"
            self._rebind_effect_bundle(value)
        elif mutation == "treat-attempt-as-verification":
            value["receipt"]["verification_evidence_refs"] = []
            value["receipt"]["receipt_digest"] = receipt_digest(value["receipt"])
        elif mutation == "receipt-without-authorized-attempt":
            value["receipt"]["attempt_id"] = "018f3f70-7b3a-7c12-8a2d-5f4e6c7b8ac9"
            value["verification_evidence"][0]["attempt_id"] = value["receipt"]["attempt_id"]
            value["receipt"]["receipt_digest"] = receipt_digest(value["receipt"])
        else:
            self.fail(f"unknown effect mutation: {mutation}")
        return value

    def _rebind_effect_bundle(self, value: dict, *, preserve_history: bool = False) -> None:
        prior_history = copy.deepcopy(value.get("proposal_history", []))
        proposal = value["proposal"]
        query = value["authority_query"]
        resolution = value["authority_resolution"]
        scope = query["scope"]
        subject_digest = effect_authority_subject_digest(proposal)
        scope.update({
            "subject_id": proposal["effect_id"],
            "subject_digest": subject_digest,
            "objective_digest": proposal["objective_digest"],
            "plan_revision": proposal["plan_revision"],
        })
        for candidate in value.get("authority_candidates", []):
            if isinstance(candidate, dict):
                candidate.update({
                    "scope_digest": scope["scope_digest"],
                    "subject_id": proposal["effect_id"],
                    "subject_digest": subject_digest,
                    "data_class": scope["data_class"],
                    "plan_revision": proposal["plan_revision"],
                })
        query["candidate_source_refs"] = [item["source_ref_id"] for item in value.get("authority_candidates", [])]
        candidate_digest = candidate_set_digest(value.get("authority_candidates", []))
        query["candidate_set_digest"] = candidate_digest
        resolution.update({
            "resolution_id": proposal["authority_resolution_id"],
            "query_id": query["query_id"],
            "subject_id": proposal["effect_id"],
            "subject_digest": subject_digest,
            "objective_digest": proposal["objective_digest"],
            "plan_revision": proposal["plan_revision"],
            "authority_ref": proposal["authority_ref"],
            "outcome": "authorized",
            "candidate_set_digest": candidate_digest,
        })
        resolution["resolution_digest"] = authority_resolution_digest(resolution)
        proposal["authority_resolution_digest"] = resolution["resolution_digest"]
        proposal["effect_digest"] = effect_binding_digest(proposal)
        current = {
            "authority_resolution_id": proposal["authority_resolution_id"],
            "authority_resolution_digest": proposal["authority_resolution_digest"],
            "effect_digest": proposal["effect_digest"],
        }
        value["proposal_history"] = prior_history + [current] if preserve_history else [current]
        execution_fields = (
            "effect_id", "effect_digest", "objective_digest", "plan_revision", "target", "preview_digest",
            "authority_resolution_id", "authority_resolution_digest", "authority_ref",
        )
        for attempt in value["attempts"]:
            for field in execution_fields:
                attempt[field] = copy.deepcopy(proposal[field])
        receipt = value["receipt"]
        for field in execution_fields:
            receipt[field] = copy.deepcopy(proposal[field])
        for approval in value.get("high_risk_approvals", []):
            if isinstance(approval, dict):
                approval["effect_digest"] = proposal["effect_digest"]
        for evidence in value.get("verification_evidence", []):
            if isinstance(evidence, dict):
                evidence["effect_id"] = proposal["effect_id"]
                evidence["effect_digest"] = proposal["effect_digest"]
                evidence["attempt_id"] = receipt["attempt_id"]
                evidence["expected_state_digest"] = proposal["verification"]["expected_state_digest"]
                evidence["observed_state_digest"] = proposal["verification"]["expected_state_digest"]
        receipt["receipt_digest"] = receipt_digest(receipt)

    def _mutated_evidence_bundle(self, mutation: str) -> dict:
        value = copy.deepcopy(self.evidence["positive"])
        if mutation == "make-required-dependency-gray-without-propagation":
            value["revisions"][1]["state"] = "gray"
            value["revisions"][1]["reason_codes"] = ["missing_evidence"]
            value["revisions"][0]["state"] = "gray"
            value["revisions"][0]["reason_codes"] = ["required_dependency_gray"]
            value["revisions"][0]["dependency_reasons"] = []
        elif mutation == "skip-claim-revision-number":
            value["revisions"][0]["revision"] = 2
        elif mutation == "use-green-claim-state":
            value["revisions"][0]["state"] = "green"
        elif mutation == "collapse-contradiction-sides":
            observation_id = value["observations"][0]["observation_id"]
            value["contradictions"] = [{"claim_id": value["claims"][0]["claim_id"], "left_observation_id": observation_id, "right_observation_id": observation_id, "status": "resolved", "material": False}]
        elif mutation == "remove-own-support-from-supported-claim":
            value["observations"] = value["observations"][1:]
        elif mutation == "add-confidence-score":
            value["confidence_score"] = 0.99
        elif mutation == "create-required-dependency-cycle":
            value["dependencies"].append({"dependent_claim_id": value["claims"][1]["claim_id"], "dependency_claim_id": value["claims"][0]["claim_id"], "relationship": "required"})
        else:
            self.fail(f"unknown evidence mutation: {mutation}")
        return value

    def _governance_case_findings(self, code: str, polarity: str) -> list[dict[str, str]]:
        if polarity == "positive":
            return validate_manifest_invariants(self.manifest) + validate_case_catalog(self.manifest, self.cases) + validate_schema_references(self.store.by_id)
        if code == "POP2-INV-GOV-015":
            schemas = copy.deepcopy(self.store.by_id)
            schemas["poppy://schema/evidence/claim/v1"]["properties"]["claim_id"]["$ref"] = "poppy://schema/governance/missing/v1"
            return validate_schema_references(schemas)
        if code in {"POP2-INV-GOV-016", "POP2-INV-GOV-017"}:
            cases = copy.deepcopy(self.cases)
            if code == "POP2-INV-GOV-016":
                cases["cases"][0]["owner_decision_id"] = "POP-V2-999"
            else:
                cases["cases"] = cases["cases"][1:]
            return validate_case_catalog(self.manifest, cases)
        value = copy.deepcopy(self.manifest)
        if code == "POP2-INV-GOV-011":
            value["entries"][0]["owner_decision_id"] = "POP-V2-999"
        elif code == "POP2-INV-GOV-012":
            value["entries"][0]["status"] = "proposed"
        elif code == "POP2-INV-GOV-013":
            value["entries"][0]["compatibility"]["maximum_exclusive"] = "3.0.0"
        elif code == "POP2-INV-GOV-014":
            value["entries"][1]["stable_code"] = value["entries"][0]["stable_code"]
        else:
            self.fail(f"unknown governance mutation: {code}")
        return validate_manifest_invariants(value)


if __name__ == "__main__":
    unittest.main()
