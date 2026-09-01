# Poppy v3

Poppy is a personal Codex plugin for moving from project ambiguity to a verified and organized result without turning every request into a workflow. Its focused skills stay near-invisible during ordinary work, while optional stateless hooks provide narrow lifecycle reminders and metadata guards.

Poppy keeps adjacent kinds of work distinct:

- Poppy holds the request, user control, phase routing, and final answer.
- Context resolves project identity, source authority, and memory only when those facts matter.
- Intake reconciles incoming work into a decision-ready disposition.
- Decide owns intended outcomes, policy, domain meaning, architecture direction, and behavioral contracts.
- Coordinate owns priorities, sequencing, commitments, meetings, finance, work items, tracker effects, and stakeholder action.
- Diagnose owns read-only causal uncertainty; Delivery creates and locally verifies the selected candidate.
- Acceptance presents exact-candidate behavior to a named observer; Assurance supplies an independent read-only verdict.
- Research closes a named external evidence gap.
- Learn proposes the smallest durable lesson after an evidenced outcome.
- Housekeeping maintains Codex task lifecycle metadata, archive eligibility, delegation hygiene, and workspace organization without deciding substantive project status.

Communication guidance is progressively loaded. It favors concrete, reader-ready prose and natural judgment while preserving accepted wording, evidence status, canonical terminology, and commitments. Style patterns remain contextual heuristics.

At material failures, retries, consequential actions, and completion claims, Poppy quietly checks whether the next step can add evidence and still matches the request, candidate, gates, authority, and declared budget. It changes course or surfaces the exact blocker without creating a watcher, attempt ledger, telemetry stream, or automatic memory. Long or model-based evaluation is bounded before it starts and never resumes or expands itself beyond that boundary.

Poppy is deliberately small. There is no cockpit, telemetry service, recurring automation, universal capability graph, daemon or persistent runtime, schema platform, persistent execution ledger, project adapter, or repository-local installation. The optional hook helper is deterministic, stateless, transcript-free, and network-free.

## Product map

- .codex-plugin/plugin.json — the skill-and-hook manifest.
- skills/ — one adaptive root and eleven focused specialists in the exact declared release inventory.
- hooks/ — reviewed stateless lifecycle reminders and metadata guards; installation never implies trust.
- references/ — progressively loaded behavioral guidance.
- tests/scenarios.json and tests/fixtures.json — synthetic acceptance contracts.
- scripts/verify_product.py — deterministic structure, catalog, hook-contract, boundary, ancestry, and candidate-identity gate.
- docs/constitution-v3.md — product boundaries and operating promise.
- docs/agent-skill-authoring-reference.md — focused guidance for creating, updating, and assessing skills.

Poppy consumes applicable project instructions and relevant native or project-specific skills. It does not inject personal policy into shared repositories. Optional external project memory remains evidence with provenance, never a shadow tracker or automatic source of current truth.

## Verify

Run:

    python scripts/verify_product.py

For a separately authorized committed candidate:

    python scripts/verify_product.py --require-clean

The verifier reports a line-ending-stable candidate digest based on Git-filtered blob identities. Model-based comparative evaluation is conditional on a decision that actually requires a behavioral superiority claim; it is not an ordinary release ritual.

See the [v3 constitution](docs/constitution-v3.md), [development guide](docs/development.md), [skill authoring and review reference](docs/agent-skill-authoring-reference.md), and [release policy](docs/release.md).
