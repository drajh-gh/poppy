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
    validate_case_catalog,
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
        cls.evidence = read_json(FIXTURES / "evidence-bundles.json")

    def test_repository_contract(self) -> None:
        result = validate_repository()
        self.assertEqual(result["status"], "pass", result["errors"])
        self.assertEqual(result["manifest_entries"], 195)
        self.assertEqual(result["implemented_entries"], 25)
        self.assertEqual(result["schemas"], 11)
        self.assertEqual(result["synthetic_cases"], 50)

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
                else:
                    self.assertIn(entry["stable_code"], actual_codes, findings)

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
