# Work-item decomposition and publication

## Slice settled outcomes

Decompose only when requirements are stable enough to preserve their meaning. Drafting work items, saving a local artifact, publishing to a tracker, and changing tracker state are distinct effects.

Create independently verifiable outcome slices that touch only necessary layers. Each item carries:

- user or operational outcome;
- relevant source and scope;
- observable, falsifiable acceptance;
- dependencies and coordination needs;
- verification and recovery expectations; and
- unverified or conflicted gaps.

Use an ephemeral coverage check against the settled specification. Report omissions or duplication without rewriting the source acceptance.

Size by coherent outcome, ownership, reviewability, blast radius, verification, recovery, and project norms, not by one context window. Add enabling refactors only when evidence shows they are necessary. Use expand-migrate-contract for wide compatibility changes when appropriate.

Distinguish hard blockers, external dependencies, coordination needs, and shared risks. Validate references, self-edges, redundant direct hard edges, acyclicity, and actionable frontiers only when dependency structure warrants it. This remains an ephemeral decomposition aid, not a persistent graph.

Readiness is evidence-based and never automatically applies ready-for-agent or another label.

## Publish safely

Before any tracker write, preview:

- exact tracker, parent, item count, bodies, and order;
- relationships, labels, status, and parent effects;
- project-native or approved tracker-resident idempotency keys;
- read-back verification after each mutation; and
- partial-failure recovery and rollback.

Publish blockers first only when justified and approved. Read back every created item, label, relation, or state change from the authoritative tracker. Stop immediately on partial failure and reconcile observed state before retrying. Do not duplicate or silently continue.

If stable correlation or complete read-back is unavailable, idempotent publication remains unverified and must stop. The tracker stays authoritative. Do not create a Markdown shadow, memory mirror, scratch ledger, or automatic publication label.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed to-tickets guidance pinned at revision 321658273cb1d20b76026717d027d505790106d4:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/to-tickets/SKILL.md
