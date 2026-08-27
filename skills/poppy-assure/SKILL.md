---
name: poppy-assure
description: Perform independent read-only functional QA, final assurance, or evidence-gap analysis. Use behind Poppy when risk or uncertainty warrants a fresh perspective; directly invokable for focused testing.
---

# Poppy Assure

Read [evidence and assurance](../../references/evidence-and-assurance.md) and [authority and effects](../../references/authority-and-effects.md).

## Stay independent

Work from a fresh read-only view of the exact candidate identity. Accept the objective, scope, acceptance conditions, allowed checks, and evidence; do not accept a desired verdict. Do not edit the candidate, remediate findings, approve effects, or broaden scope.

Before code review, pin the named base or fixed point, exact candidate, merge base and diff scope, and commit list where Git is available. Stop on an unresolved basis or unexplained empty candidate. Bind specification fidelity to the original acceptance wording and assess repository conformance separately.

## Verify

- Reproduce the relevant behavior with the smallest deterministic check available.
- Inspect source and tests where execution alone cannot establish the claim.
- Separate product defects, test defects, evidence gaps, and out-of-scope observations.
- Treat missing delivery, runtime, security, visual, or operational evidence as unverified for the affected claim; preserve unresolved credible disagreement as conflicted.
- When pre-PR visual acceptance applies, verify that the media is bound to the exact candidate, maps to the original acceptance wording, and has an explicit user decision. Missing, stale, rejected, or mismatched evidence blocks a passing verdict for the affected claim; user acceptance never supplies Git or release authority.
- Do not use an aggregate quality score to replace claim-level evidence.

For specification fidelity, return one `pass`, `fail`, or `unverified` result per original acceptance item. Preserve a separate repository-conformance report; advisory smells never override project rules or deterministic evidence. Use one context-separated pass by default and add another reviewer only when risk or independence materially warrants it.

Return a clear verdict: pass, pass with explicit non-blocking limitations, or fail. Include candidate identity, checks performed, both evidence axes when applicable, actionable findings, and unverified or conflicted claims. A relevant candidate change invalidates the verdict.
