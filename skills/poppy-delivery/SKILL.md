---
name: poppy-delivery
description: Turn a sufficiently selected product, design, or engineering change into a preserved and locally verified candidate. Use behind Poppy when candidate mutation is authorized; directly invokable for focused testing. Do not use for unresolved causal diagnosis or human acceptance.
---

# Poppy Delivery

Read [engineering delivery](../../references/engineering-delivery.md).

## Own candidate mutation

Delivery creates or modifies the exact product, design, software, or operational candidate and verifies it locally. It consumes the originating wording and settled behavioral contract; it must not silently redefine them.

If behavior, scope, lifecycle, decision ownership, or observable acceptance remains materially unsettled, return the decision to Poppy Decide. If material causal uncertainty reappears, return the exact symptom and evidence to Poppy Diagnose. Resolve minor reversible implementation details without ceremony.

Use only the guidance that can change the candidate:

- module boundaries, dependency seams, or selected software design: [implementation design](../../references/implementation-design.md);
- a bounded learning artifact: [prototype to learn](../../references/prototype-to-learn.md);
- regression-first, characterization, or other observable implementation feedback: [test-first delivery](../../references/test-first-delivery.md);
- Git already stopped on a conflict: [Git conflict resolution](../../references/git-conflict-resolution.md);
- a helper or checklist with human-only stages: [human-guided procedures](../../references/human-guided-procedures.md).
- dirty, stale, generated, cached, duplicated, or temporary resource state: [resource hygiene](../../references/resource-hygiene.md).

## Preserve and hand off

Preserve existing changes and keep one writer per target. Classify working state before treating it as a blocker: unrelated dirt does not block a scoped change, while overlapping or base-defining dirt stays protected. Prefer immutable Git objects for read-only evidence or an exact isolated worktree for writes when the shared checkout is not a faithful candidate. Once excluded, do not repeat the shared checkout warning unless it changes. Before a commit, dependency adoption, deployment, publication, installation, destructive action, or external effect, read [authority and effects](../../references/authority-and-effects.md). Local implementation authority never implies one of those effects.

Keep verification inside the authorized candidate surface. Prefer equivalent no-cache or no-generated-artifact modes when available, inspect exact status or diff afterward, and never delete unknown or pre-existing artifacts to make a candidate appear clean.

Report exact candidate identity, behavior changed and preserved, checks and observed results, limitations, and remaining acceptance or effect states. Hand demonstrated product-owner or client review to Poppy Acceptance and an independent conformance or release judgment to Poppy Assure.
