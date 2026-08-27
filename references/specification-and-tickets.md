# Specification synthesis and ticket decomposition

Use the specification section to turn sufficiently settled intent into an implementation contract. Use ticket decomposition only after the requirements are stable enough to slice. Drafting, local capture, tracker publication, and tracker state changes are distinct effects.

## Synthesize a specification

Start from settled conversation and original decision wording. Orient boundedly to relevant current behavior, domain vocabulary, approved decisions, ADRs, and authoritative sources. Separate:

- observed evidence;
- settled decisions;
- proposed choices;
- assumptions; and
- unverified or conflicted gaps.

Ask only questions that materially change scope, solution, acceptance, safety, or readiness. Never fabricate missing requirements. Choose the smallest suitable form: stories, scenarios, use cases, invariants, technical requirements, or operational outcomes. Prefer the smallest sufficient observable test seams; do not impose exactly one seam.

Include only relevant sections from:

- problem and intended outcome;
- source baseline and current-state/change boundary;
- scope and non-goals;
- requirements and observable acceptance;
- implementation and testing decisions;
- decision-rich prototype evidence;
- evidence and decision status;
- constraints, risks, and dependencies;
- compatibility or migration;
- accessibility, security, privacy, performance, and observability; and
- rollout, rollback, and open questions.

Classify document readiness descriptively as `draft`, `review-ready`, `implementation-ready`, or `blocked by named decisions`. Do not score it. Readiness is not a tracker label, effect approval, or implementation authority.

Default to an inline draft. A named local file may be written only within local edit authority. Repository-history publication, tracker publication, labels, and state changes require exact target, content and effect preview, approval, execution, read-back, and rollback.

## Decompose outcome slices

Create independently verifiable tracer-bullet slices that touch only necessary layers. Each ticket owns an observable, falsifiable acceptance contract. Use an ephemeral coverage check against settled requirements and report omissions or duplication without rewriting the source acceptance.

Size by coherent outcome, ownership, reviewability, blast radius, verification, recovery, and project norms—not by one context window. Add enabling refactors only when evidence shows they are necessary. Use expand-migrate-contract for wide compatibility changes when appropriate.

Distinguish hard blockers, external dependencies, coordination needs, and shared risks. Validate references, self-edges, redundant direct hard edges, acyclicity, and actionable frontiers. This is an ephemeral decomposition aid, not a persistent graph.

Ticket readiness is evidence-based and never automatically applies `ready-for-agent` or another project label.

## Publish safely

Before any tracker write, preview:

- exact tracker, parent, ticket count, bodies, and order;
- relationships, labels, status, and parent effects;
- project-native or approved tracker-resident idempotency keys;
- read-back verification after each mutation; and
- partial-failure recovery and rollback.

Publish blockers first only when that ordering is justified and approved. After every created ticket, label, or relation, read back the authoritative tracker. Stop immediately on partial failure and reconcile observed state before retrying; do not duplicate or silently continue.

If stable correlation or complete read-back is unavailable, idempotent publication is unverified and must stop. The tracker remains authoritative. Do not create a local Markdown shadow, memory mirror, scratch ledger, or automatic publication label.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed guidance reviewed on 2026-08-27:

- https://github.com/mattpocock/skills/tree/main/skills/engineering/to-spec
- https://github.com/mattpocock/skills/tree/main/skills/engineering/to-tickets

