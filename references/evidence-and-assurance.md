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

### Client-ready acceptance recording

For every client-visible behavioral change, keep a pending client-acceptance recording checkpoint in the delivery flow. If the user did not request a recording with the implementation, offer the checkpoint after local verification; do not prepare data or record merely because the checkpoint exists. A later recording request may begin from an already-implemented candidate.

Before recording, propose a compact demo contract for the user's approval. Derive it from the original stakeholder wording, accepted behavior, exact candidate, implementation, and tests. Include the relevant scenarios, starting state, synthetic seed data, acting roles, visible steps and outcomes, permission or validation paths, lifecycle or error cases, and explicit exclusions. Resolve clear details without ceremony, but ask when conflict or ambiguity could change client expectations or material scope.

Choose between an authorized local, development, or preview environment by fidelity rather than habit. Prefer development or preview when the exact candidate and required integrations can be represented safely; prefer local when isolation and deterministic data produce more faithful evidence. Keep the environment and technical limitations in the user's private coverage notes rather than the client media unless they materially affect what the client is being asked to accept. Any deployment remains a separately gated effect.

Prepare realistic synthetic, client-safe accounts, records, roles, sessions, and lifecycle state. Never expose real personal data, credentials, production exports, terminals, setup machinery, or secrets. Keep disposable demo support out of Git unless it is separately justified and authorized as durable test support.

Produce one concise video when the complete story remains easy to follow, or several clearly named clips when roles or scenarios would make one video hard to understand. Record at a readable full-interface scale with deliberate movement and pauses, no dead time, and no artificial speed-up. Use concise burned-in subtitles in the client's language and no audio narration. Ask the user when the language is not certain. Keep the client media free of ticket numbers, commit hashes, test names, environment badges, AI references, implementation detail, and ornamental introductions or conclusions. Explain only the user action, relevant context, and visible outcome.

Watch every rendered clip from beginning to end before handoff. Give the user the media, private candidate and environment identity, scenario coverage and limitations, artifact location and disposition, and a short natural client-message draft. Do not upload, publish, contact the client, or retain the media in Git without separate authority.

Client acceptance is semantic, not an incantation. A named client's ordinary affirmative response such as “yes, that's it” supports acceptance of the behavior faithfully shown in that recording when the user supplies or summarizes the response. It does not authorize release or another external effect. A candidate change that could alter an accepted scenario requires replacement evidence; a demonstrably irrelevant change does not. Requested changes invalidate only the affected scenarios, which return through implementation, verification, and recapture.

## Code review

Pin one exact comparison basis before review. Resolve the named base or fixed point, exact candidate identity, merge base and diff scope, and commit list where Git is available. Stop on an unresolved basis or an unexplained empty candidate.

Discover intent from user-named paths, issue references, repository documents, and history, but keep discovery separate from authority. Project and repository instructions plus approved or user-confirmed requirements govern. Bind specification review to the original acceptance wording; implementation, remediation, and assurance must not silently rephrase or narrow it.

Keep two evidence axes separate:

1. **Specification fidelity:** one `pass`, `fail`, or `unverified` result for every original acceptance item, with direct evidence or reason. Missing, duplicated, reworded, or reviewer-invented items are invalid. A required fail or unverified item blocks a passing verdict.
2. **Repository conformance:** compliance with applicable repository and project rules plus explicitly advisory quality heuristics. Deterministic tooling, runtime checks, security review, and project-specific expertise remain distinct.

Preserve both reports, then derive the overall evidence-backed verdict without merging or reranking the axes. Finding counts are summaries, never quality scores. A diff cannot prove runtime behavior. Use one context-separated review pass by default; add a separate read-only specialist only when risk, coverage, or independence materially warrants it.
