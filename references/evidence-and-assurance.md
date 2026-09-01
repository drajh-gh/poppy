# Evidence and assurance

## Keep claims calibrated

For every material claim, distinguish:

- supported: current evidence directly supports it;
- contradicted: current credible evidence directly opposes it;
- conflicted: credible sources disagree and authority or recency does not resolve them; and
- unverified: required evidence is missing, stale, inaccessible, malformed, or insufficient.

An evidence gap propagates only to dependent claims. Confidence, consensus, or absence of errors cannot turn an unverified or conflicted claim into a supported one. Do not invent a numerical confidence score.

Describe unavailable evidence precisely: say it was not supplied, observed, or accessible rather than claiming it does not exist unless nonexistence is itself evidenced.

Keep observed fact, inference, recommendation, decision, proposed effect, and verified completed effect separate.

When recommending the smallest decisive next probe, name the question it resolves, the evidence shape needed to interpret it, and the authoritative owner or access boundary when one is known. Separate permission to inspect a cohort or system from permission to remediate it.

Keep the recommendation inside the evidence scope. Evidence from one case does not support cohort-wide remediation: say what must not yet be generalized and name the residual risk. If the recommended action is not currently authorized, make the recommendation conditional at the point it is stated rather than disclosing the missing authority only afterward.

## Verify in proportion to risk

- Routine edit: inspect the exact diff or result.
- Product or code change: verify changed behavior plus the smallest relevant static, integration, build, or visual gate.
- Cross-cutting or consequential change: add broader project-required gates and independent read-only assurance.
- Release readiness: verify each required state explicitly and leave unavailable runtime or delivery evidence unverified.

Technical cleanliness establishes only the surface checked. Schema, lint, tests, links, and repository gates do not prove that a workflow, interface, recommendation, or stakeholder artifact is understandable or useful. Check those acceptance qualities separately when they matter.

An announced blocking gate remains blocking. Reclassify it only before the effect, with observed evidence, rationale, replacement coverage, and residual risk made explicit.

## Prove load-bearing safety facts

For a meaningful blast-radius or safety claim, identify the one or two facts on which the candidate's safety depends. Verify each against the closest faithful allowed artifact or runtime path. Examples include the actual caller set, authorization boundary, migration invariant, rollback behavior, data-selection guard, or production-shaped integration response.

An unproven load-bearing fact remains unverified. This focused probe supplements complete claim-level analysis; it never replaces acceptance coverage or licenses a broader effect.

## Bounded meta-verification

When the object of verification is Poppy, another agent workflow, or the verification process itself, prevent the check from recursively expanding into a full workflow run:

- Pin the exact candidate and one claim before loading more context.
- Reuse current candidate-bound orientation, receipts, and passed checks. Reopen them only when the candidate changed or the evidence is stale, insufficient, inaccessible, or contradicted.
- Name the smallest missing probe and its evidence surface. Do not read the full repository, vault, installed package, or history when one source-specific check can decide the claim.
- Stop when the probe resolves the claim. If it cannot, leave the claim unverified and name the next decisive probe; expand only for a specific unresolved dependency exposed by the result.

Evidence volume is not confidence. A broader read is justified by a named evidence gap, not by the fact that the system can inspect itself. Suspected process failure is one claim to check, not authority to audit the whole task. Required fresh matched evaluation arms and predeclared trials remain required probes; reuse valid supporting evidence within them, never across a candidate change or in place of the trial itself.

## Perform independent assurance

Assurance is a fresh read-only pass over an exact candidate. Give the reviewer the objective, original acceptance wording, comparison basis, allowed checks, and evidence, never a desired verdict. The reviewer does not edit, remediate, approve effects, or broaden scope.

Pin the base or fixed point, candidate identity, merge base and diff scope, and commit list where Git is available. Stop on an unresolved comparison basis or unexplained empty candidate.

Assess two independent axes:

1. Specification fidelity: one pass, fail, or unverified result per original acceptance item, with direct evidence or a reason.
2. Repository conformance: applicable project rules and deterministic evidence, with advisory heuristics explicitly separated.

A required fail or unverified item blocks a passing verdict. Finding counts are summaries, not scores. A diff cannot prove runtime behavior.

For a workflow, navigation surface, or stakeholder artifact, also assess audience, language, format, specificity, source fidelity, and supported commitments. For exact-candidate or client review, use the client-acceptance reference.

Finish with pass, pass with explicit non-blocking limitations, or fail. A relevant candidate change invalidates the verdict. Assurance never authorizes a commit, publication, installation, deployment, message, tracker change, or other effect.

## Provenance

The load-bearing-fact heuristic is adapted in original Poppy wording from Cursor's MIT-licensed Blast radius guidance pinned at revision 68836ddaf5697224520f1847d90cdb90ca8babaa: https://github.com/cursor/plugins/blob/68836ddaf5697224520f1847d90cdb90ca8babaa/pstack/skills/blast-radius/SKILL.md
