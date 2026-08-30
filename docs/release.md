# Release policy

## Candidate eligibility

A candidate is eligible for personal installation preview only when:

1. python scripts/verify_product.py passes;
2. the exact source revision, package version, candidate digest algorithm, and candidate digest are recorded;
3. the nominated source commits and v2 rollback tag remain ancestors or valid rollback evidence;
4. the complete synthetic catalog materializes;
5. matched GPT-5.6 Sol baseline-versus-candidate evaluation passes for the impact-selected scenarios;
6. no safety, authority, request-fidelity, evidence-calibration, or material capability regression is observed;
7. a fresh independent read-only assurance pass finds no blocking defect;
8. the candidate is committed under separate authority and python scripts/verify_product.py --require-clean passes; and
9. the user's shared project surfaces remain unchanged.

Static verification establishes structure and contract integrity, not behavioral superiority. Paired evaluation establishes only the scenarios and conditions observed. No aggregate score can offset a safety failure. Efficiency matters only after quality passes.

## Exact-effect separation

Commit, local tag, remote tag, push, pull request, merge, publication, personal installation, automation mutation, deployment, tracker mutation, communication, and memory write are distinct effects.

Before personal installation, present the exact committed candidate, version, digest, evaluation and assurance results, installation target, current rollback package, read-back procedure, and rollback action. Install only after approval of that unchanged preview.

## Installation proof

A fresh task after installation must establish:

- active plugin ID, version, source revision, digest algorithm, and digest;
- exactly the seven Poppy v3 skills and no active v2 skill identities;
- no active Poppy MCP server, app, cockpit, telemetry, automation, or repository-local installation;
- installation under the user's plugin environment for Codex Desktop and CLI; and
- the exact preserved rollback package can be restored.

ChatGPT and other hosts remain unverified unless separately tested. Any later plugin, root, authority, profile, delegation, or assurance change invalidates this proof.

## Rollback

Keep the previously active package intact until the new installation and fresh-task proof pass. Rollback restores that exact package, reads back the active version and seven-skill surface, and records any limitation. Do not delete rollback material as part of successful cutover.

## Natural-use follow-up

Synthetic evaluation does not replace real use. When suitable tasks occur naturally, privately observe one read-only project decision, one diagnosis or assurance task, and one bounded reversible local-code task. Do not manufacture work or broaden authority for evaluation. Treat corrections as evidence for a future versioned candidate, never as permission to rewrite installed skills silently.
