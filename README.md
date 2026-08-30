# Poppy v3

Poppy is a personal, skills-only Codex plugin for moving from project ambiguity to a verified result without turning every request into a workflow. It stays near-invisible during ordinary work and uses one restrained, content-bearing Poppy signature when a substantive conversational recommendation or status benefits from reassurance.

Poppy keeps project decisions and candidate delivery distinct:

- Poppy holds the request, user control, phase routing, and final answer.
- Context resolves project identity, source authority, and memory only when those facts matter.
- Operations owns priorities, readiness, coordination, meetings, finance, work items, and stakeholder outcomes.
- Delivery creates and locally verifies an exact selected product, design, or engineering candidate.
- Assurance supplies an independent read-only verdict.
- Research closes a named external evidence gap.
- Learn proposes the smallest durable lesson after an evidenced outcome.

Communication guidance is progressively loaded. It favors concrete, reader-ready prose and natural judgment while preserving accepted wording, evidence status, canonical terminology, and commitments. Style patterns remain contextual heuristics.

Poppy is deliberately small. There is no cockpit, telemetry service, automation, universal capability graph, runtime engine, schema platform, persistent execution ledger, project adapter, or repository-local installation.

## Product map

- .codex-plugin/plugin.json — the skills-only manifest.
- skills/ — exactly one adaptive root and six focused supporting skills.
- references/ — progressively loaded behavioral guidance.
- tests/scenarios.json and tests/fixtures.json — synthetic acceptance contracts.
- scripts/verify_product.py — deterministic structure, catalog, boundary, ancestry, and candidate-identity gate.
- docs/constitution-v3.md — product boundaries and operating promise.

Poppy consumes applicable project instructions and relevant native or project-specific skills. It does not inject personal policy into shared repositories. Optional external project memory remains evidence with provenance, never a shadow tracker or automatic source of current truth.

## Verify

Run:

    python scripts/verify_product.py

For a separately authorized committed candidate:

    python scripts/verify_product.py --require-clean

The verifier reports a line-ending-stable candidate digest based on Git-filtered blob identities. Behavioral improvement is established separately through matched GPT-5.6 Sol baseline-versus-candidate evaluation.

See the [v3 constitution](docs/constitution-v3.md), [development guide](docs/development.md), and [release policy](docs/release.md).
