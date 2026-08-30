---
name: poppy-delivery
description: Turn a sufficiently selected product, design, or engineering change into a preserved and locally verified candidate. Use behind Poppy for implementation, defect repair, prototypes, architecture design, and release preparation; directly invokable for focused testing.
---

# Poppy Delivery

Read [engineering delivery](../../references/engineering-delivery.md).

## Change the candidate

Delivery owns creation or modification of the exact product, design, or software candidate and its local verification. It consumes the originating wording and settled behavioral contract; it must not silently redefine them.

If intended behavior, scope, lifecycle, decision ownership, or observable acceptance remains materially unsettled, return the missing decision to Poppy project work. Resolve minor reversible implementation details without ceremony.

Compose only the guidance that can change the candidate:

- architecture health, selected design, module boundaries, or dependency seams: [architecture and design](../../references/architecture-and-design.md);
- a bounded learning artifact: [prototype to learn](../../references/prototype-to-learn.md);
- diagnosis, regression-first repair, characterization, or test-first feedback: [diagnosis and test-first delivery](../../references/diagnosis-and-test-first-delivery.md);
- Git already stopped on a conflict: [Git conflict resolution](../../references/git-conflict-resolution.md);
- a guided checklist or helper with human-only stages: [human-guided procedures](../../references/human-guided-procedures.md);
- client or pre-PR visual evidence, recording, or exact-candidate acceptance: [client acceptance](../../references/client-acceptance.md).

Read [communication and writing](../../references/communication-and-writing.md) for documentation, captions, acceptance material, or sharing drafts. Use [delegation and continuity](../../references/delegation-and-continuity.md) only when delegation, a worktree transition, or artifact preservation is material.

Preserve existing changes and keep one writer per target. Before a commit, dependency adoption, deployment, publication, installation, destructive action, or external effect, read [authority and effects](../../references/authority-and-effects.md). Local implementation authority never implies one of those effects.

Use Poppy Assurance for a fresh read-only pass when uncertainty, blast radius, or release consequence warrants independence. Report the exact candidate, behavior changed, verification performed, limitations, and every later acceptance or effect state that remains unverified.
