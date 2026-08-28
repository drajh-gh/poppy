# Evidence and assurance

## Claim-level evidence

For every material claim, distinguish:

- supported: current evidence directly supports the claim;
- contradicted: current credible evidence directly opposes the claim;
- conflicted: credible sources disagree and authority or recency does not resolve them; and
- unverified: required evidence is missing, stale, inaccessible, malformed, or insufficient.

An evidence gap propagates only to claims that require it. It does not make unrelated work unusable. Confidence, consensus, or absence of errors cannot turn an unverified or conflicted claim into a supported one.

Do not invent numerical confidence. Use a percentage or score only when a named calibrated method and relevant evidence justify that number; otherwise report claim-level evidence, residual risk, and the next decisive gate.

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

Technical cleanliness establishes only the surface actually checked. Schema, lint, test, link, or repository gates do not by themselves establish that a workflow, vault, interface, recommendation, or stakeholder artifact is understandable and useful. When usefulness is part of acceptance, verify the human-facing navigation, wording, decision value, or exact-candidate behavior separately before calling the outcome assured.

An announced blocking gate remains blocking. Reclassify it only before the gated effect, with the observed evidence, rationale, replacement coverage, and residual risk made explicit; never merge or publish first and rationalize the gate afterward.

## Independent assurance

Assurance is a fresh read-only pass. Give the reviewer the objective, exact candidate identity, acceptance conditions, allowed checks, and declared evidence—not the desired verdict. The reviewer does not edit the candidate or approve external effects.

Separate functional verification from final assurance when the candidate is consequential. Any relevant candidate change invalidates earlier verdicts.

## Outcome acceptance

Technical verification, exact-candidate product acceptance, deployment, runtime read-back, and external stakeholder acceptance are separate claims. No earlier state implies a later one. Record the exact candidate, environment, scenario, observer, and decision authority for each supported state; leave unavailable states unverified.

For a business workflow change, map the exact candidate to the confirmed behavioral scenarios and production-shaped state that matter. Visual media may be appropriate for interface behavior. For imports, integrations, migrations, data repair, or other nonvisual behavior, use the closest faithful evidence such as a bounded fixture, dry-run manifest, API result, integration response, or authorized runtime observation. A reported incident is reproduction evidence, not approval of a generalized policy.

Treat external stakeholder acceptance as supported only when the named stakeholder or decision owner accepts the relevant outcome. User acceptance qualifies that state only when the user owns the product decision. Neither stakeholder nor user acceptance supplies Git, release, deployment, production-write, or publication authority.

## Visual product acceptance

For a user-visible change, visual evidence helps the user judge whether the implemented experience matches the intended outcome. It complements deterministic checks; it does not prove accessibility, production behavior, security, or usability beyond what was actually observed.

When the user requests pre-PR judgment or the project requires it:

- bind the evidence to the exact commit or working-tree snapshot under review;
- prefer focused screenshots for static states and a short video for interaction, motion, or a sequence, using only already-available authorized capabilities;
- map each capture to the original acceptance wording and record the reproduction state, viewport or device when relevant, capture time, and material limitations;
- present the media in the current task when the interface supports it, keep local artifacts disposable and out of Git, declare their disposition, and never upload or publish them without separate authority; and
- when faithful execution or capture is unavailable, mark the affected claim unverified instead of fabricating evidence. A nonvisual change may use a reasoned not-applicable result plus the closest observable evidence.

Pause before pull-request preparation until the user returns an explicit `ACCEPT`, `REJECT`, or `REQUEST_CHANGES` decision. That decision qualifies only the displayed candidate and never authorizes a commit, push, pull request, merge, publication, or deployment. A relevant candidate change invalidates visual acceptance. Rejection or requested changes return to the authorized delivery path and require new evidence for the changed candidate.

## Code review

Pin one exact comparison basis before review. Resolve the named base or fixed point, exact candidate identity, merge base and diff scope, and commit list where Git is available. Stop on an unresolved basis or an unexplained empty candidate.

Discover intent from user-named paths, issue references, repository documents, and history, but keep discovery separate from authority. Project and repository instructions plus approved or user-confirmed requirements govern. Bind specification review to the original acceptance wording; implementation, remediation, and assurance must not silently rephrase or narrow it.

Keep two evidence axes separate:

1. **Specification fidelity:** one `pass`, `fail`, or `unverified` result for every original acceptance item, with direct evidence or reason. Missing, duplicated, reworded, or reviewer-invented items are invalid. A required fail or unverified item blocks a passing verdict.
2. **Repository conformance:** compliance with applicable repository and project rules plus explicitly advisory quality heuristics. Deterministic tooling, runtime checks, security review, and project-specific expertise remain distinct.

Preserve both reports, then derive the overall evidence-backed verdict without merging or reranking the axes. Finding counts are summaries, never quality scores. A diff cannot prove runtime behavior. Use one context-separated review pass by default; add a separate read-only specialist only when risk, coverage, or independence materially warrants it.
