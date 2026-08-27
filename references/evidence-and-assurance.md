# Evidence and assurance

## Claim-level evidence

For every material claim, distinguish:

- supported: current evidence directly supports the claim;
- contradicted: current credible evidence conflicts with it; and
- Gray: required evidence is missing, stale, inaccessible, malformed, or insufficient.

Gray propagates only to claims that require the missing evidence. It does not make unrelated work unusable. Confidence, consensus, or absence of errors cannot turn Gray into supported.

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
- release readiness: verify required evidence explicitly and leave unavailable delivery or runtime evidence Gray.

Do not replace missing evidence with a fixed quality score.

## Independent assurance

Assurance is a fresh read-only pass. Give the reviewer the objective, exact candidate identity, acceptance conditions, allowed checks, and declared evidence—not the desired verdict. The reviewer does not edit the candidate or approve external effects.

Separate functional verification from final assurance when the candidate is consequential. Any relevant candidate change invalidates earlier verdicts.
