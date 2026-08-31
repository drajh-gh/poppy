# Release policy

## Candidate eligibility

A candidate is eligible for personal installation preview only when:

1. python scripts/verify_product.py passes;
2. the exact source revision, package version, candidate digest algorithm, and candidate digest are recorded;
3. the nominated source commits and v2 rollback tag remain ancestors or valid rollback evidence;
4. the complete synthetic catalog materializes;
5. the smallest decision-relevant evidence for the changed behavior passes, with broader behavioral or efficiency claims left unverified when their optional evaluation was not run;
6. no safety, authority, request-fidelity, evidence-calibration, or material capability regression is observed;
7. any model-based evaluation stays within a declared call and elapsed-time budget, uses deterministic grading first, and records only the semantic judging or human adjudication on which the decision actually depends;
8. trigger and non-trigger checks affected by the candidate pass;
9. a fresh independent read-only assurance pass finds no blocking defect;
10. the candidate is committed under separate authority and python scripts/verify_product.py --require-clean passes; and
11. the user's shared project surfaces remain unchanged.

Static verification establishes structure and contract integrity, not behavioral superiority. Paired evaluation establishes only the scenarios and conditions observed. No aggregate score can offset a safety failure. Efficiency matters only after quality passes.

Universal superiority is not a release requirement. Full paired evaluation, private held-out cases, judge calibration, human adjudication, activation-matrix testing, and performance measurement are conditional evidence for claims that actually depend on them. Before such work starts, set the decision question, selected cases, maximum model calls, maximum elapsed time, and stop condition. Without separate approval, allow at most one scenario and one fresh task per arm, with no automatic resume or expansion. Reaching the boundary leaves the dependent claim unverified; it does not license another run.

An ownership-routing candidate may instead use the catalog's bounded candidate-only smoke: at most three fresh tasks and 30 elapsed minutes, with no baseline arm, blind judge, performance study, or automatic expansion. This establishes only the observed routing cases, not general superiority.

## Exact-effect separation

Commit, local tag, remote tag, push, pull request, merge, publication, personal installation, automation mutation, deployment, tracker mutation, communication, and memory write are distinct effects.

Before personal installation, present the exact committed candidate, version, digest, evaluation and assurance results, installation target, current rollback package, read-back procedure, and rollback action. Install only after approval of that unchanged preview.

## Installation proof

A fresh task after installation must establish:

- active plugin ID, version, source revision, digest algorithm, and digest;
- exactly the declared Poppy skill inventory and no active v2 or removed skill identities;
- explicit Poppy invocation in one fresh task;
- automatic activation and routine non-activation only when trigger behavior changed;
- pre-existing-task catalog behavior only when upgrade lifecycle behavior is an acceptance item;
- no active Poppy MCP server, app, cockpit, telemetry, automation, or repository-local installation;
- installation under the user's plugin environment for Codex Desktop and CLI; and
- the exact preserved rollback package can be restored.

Retain the raw machine-readable traces for checks actually run. If a pre-existing task keeps a stale skill catalog, record it as a host lifecycle limitation rather than adding version checks or installation narration to Poppy. ChatGPT and other hosts remain unverified unless separately tested. Any later plugin, root, authority, profile, delegation, or assurance change invalidates this proof.

## Rollback

Keep the previously active package intact until the new installation and fresh-task proof pass. Rollback restores that exact package, reads back its active version and declared skill surface, and records any limitation. Do not delete rollback material as part of successful cutover.

## Natural-use follow-up

Synthetic evaluation does not replace real use. When suitable tasks occur naturally, privately observe one read-only project decision, one diagnosis or assurance task, and one bounded reversible local-code task. Do not manufacture work or broaden authority for evaluation. Treat corrections as evidence for a future versioned candidate, never as permission to rewrite installed skills silently.
