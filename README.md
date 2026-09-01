# Poppy v3

Poppy is a personal Codex plugin for moving from project ambiguity to a verified and organized result without turning every request into a workflow. Its focused skills stay near-invisible during ordinary work, while optional bounded hooks provide lifecycle guards and opt-in semantic continuity.

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
- Scribe keeps one bounded semantic checkpoint, reviews material drift, and proposes recurring improvements without becoming truth or memory.
- Housekeeping maintains Codex task lifecycle metadata, archive eligibility, delegation hygiene, and workspace organization without deciding substantive project status. An explicitly requested marker for the calling task can use a tightly gated one-orchestration fast path when the disposition is already supported; other tasks, batches, archives, ambiguity, missing evidence, and drift retain the full safe path.

Communication guidance is progressively loaded. It favors concrete, reader-ready prose and natural judgment while preserving accepted wording, evidence status, canonical terminology, and commitments. Style patterns remain contextual heuristics.

At material failures, retries, consequential actions, and completion claims, Poppy quietly checks whether the next step can add evidence and still matches the request, candidate, gates, authority, and declared budget. It changes course or surfaces the exact blocker without creating a watcher, attempt ledger, telemetry stream, or automatic memory. Long or model-based evaluation is bounded before it starts and never resumes or expands itself beyond that boundary.

Poppy is deliberately small. There is no cockpit, telemetry service, recurring automation, universal capability graph, daemon or persistent runtime, schema platform, persistent execution ledger, project adapter, or repository-local installation. Hook helpers are deterministic, bounded, transcript-free, and network-free. Housekeeping remains stateless; opt-in Scribe may replace one size-capped checkpoint per task in private plugin data for seven days.

## Product map

- .codex-plugin/plugin.json — the skill-and-hook manifest.
- skills/ — one adaptive root and twelve focused specialists in the exact declared release inventory.
- hooks/ — reviewed lifecycle guards and opt-in Scribe continuity; installation never implies trust.
- references/ — progressively loaded behavioral guidance.
- tests/scenarios.json and tests/fixtures.json — synthetic acceptance contracts.
- scripts/verify_product.py — deterministic structure, catalog, hook-contract, boundary, ancestry, and candidate-identity gate.
- docs/constitution-v3.md — product boundaries and operating promise.
- docs/agent-skill-authoring-reference.md — focused guidance for creating, updating, and assessing skills.

## Using Scribe

Scribe combines four outcomes in one opt-in loop: it records the latest material working state, navigates resumes and handoffs, critiques one material drift or evidence problem, and proposes learning candidates only after supported recurrence across independent tasks.

- Quiet: “Poppy Scribe, continuously preserve the decisions, evidence limits, open questions, and next step for this task. Interrupt me only for one material issue.”
- Review: “Poppy Scribe Review: what changed, what is conflicted or unverified, and what should happen next?”
- Improve: “Poppy Scribe Improve: which supported friction patterns recur across at least three independent tasks, and what is the smallest intervention worth testing?”
- Forget: “Poppy Scribe, forget this task.”

Use Quiet for long implementation or research threads, Review before a handoff or consequential decision, and Improve periodically after enough independent work exists. Scribe checkpoints expire after seven days and never replace primary evidence, artifact preservation, project memory, tracker state, or effect approval.

Poppy consumes applicable project instructions and relevant native or project-specific skills. It does not inject personal policy into shared repositories. Optional external project memory remains evidence with provenance, never a shadow tracker or automatic source of current truth.

## Verify

Run:

    python scripts/verify_product.py

For a separately authorized committed candidate:

    python scripts/verify_product.py --require-clean

The verifier reports a line-ending-stable candidate digest based on Git-filtered blob identities. Model-based comparative evaluation is conditional on a decision that actually requires a behavioral superiority claim; it is not an ordinary release ritual.

See the [v3 constitution](docs/constitution-v3.md), [development guide](docs/development.md), [skill authoring and review reference](docs/agent-skill-authoring-reference.md), and [release policy](docs/release.md).
