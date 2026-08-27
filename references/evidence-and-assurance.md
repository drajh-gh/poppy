# Evidence and assurance

## Claim-level evidence

For every material claim, distinguish:

- supported: current evidence directly supports the claim;
- contradicted: current credible evidence directly opposes the claim;
- conflicted: credible sources disagree and authority or recency does not resolve them; and
- unverified: required evidence is missing, stale, inaccessible, malformed, or insufficient.

An evidence gap propagates only to claims that require it. It does not make unrelated work unusable. Confidence, consensus, or absence of errors cannot turn an unverified or conflicted claim into a supported one.

Keep these categories distinct in reports:

- observed fact;
- inference;
- recommendation;
- user or project decision;
- proposed effect; and
- verified completed effect.

## Proportionate verification

Match verification to the risk and surface changed:

- trivial edit: inspect the diff or targeted result;
- code change: focused tests plus the smallest relevant lint, type, build, or visual check;
- cross-cutting or consequential change: broader gates and an independent read-only review;
- release readiness: verify required evidence explicitly and leave unavailable delivery or runtime evidence unverified.

Do not replace missing evidence with a fixed quality score.

## Independent assurance

Assurance is a fresh read-only pass. Give the reviewer the objective, exact candidate identity, acceptance conditions, allowed checks, and declared evidence—not the desired verdict. The reviewer does not edit the candidate or approve external effects.

Separate functional verification from final assurance when the candidate is consequential. Any relevant candidate change invalidates earlier verdicts.

## Code review

Pin one exact comparison basis before review. Resolve the named base or fixed point, exact candidate identity, merge base and diff scope, and commit list where Git is available. Stop on an unresolved basis or an unexplained empty candidate.

Discover intent from user-named paths, issue references, repository documents, and history, but keep discovery separate from authority. Project and repository instructions plus approved or user-confirmed requirements govern. Bind specification review to the original acceptance wording; implementation, remediation, and assurance must not silently rephrase or narrow it.

Keep two evidence axes separate:

1. **Specification fidelity:** one `pass`, `fail`, or `unverified` result for every original acceptance item, with direct evidence or reason. Missing, duplicated, reworded, or reviewer-invented items are invalid. A required fail or unverified item blocks a passing verdict.
2. **Repository conformance:** compliance with applicable repository and project rules plus explicitly advisory quality heuristics. Deterministic tooling, runtime checks, security review, and project-specific expertise remain distinct.

Preserve both reports, then derive the overall evidence-backed verdict without merging or reranking the axes. Finding counts are summaries, never quality scores. A diff cannot prove runtime behavior. Use one context-separated review pass by default; add a separate read-only specialist only when risk, coverage, or independence materially warrants it.
