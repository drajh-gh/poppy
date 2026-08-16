# Researcher to Upgrader handoff

Researcher owns external discovery, source quality, repository due diligence, applicability, and recommendation evidence. Upgrader owns final classification, project experiments, promotion threshold, source changes, validation, rollback, activation, and durable improvement receipts.

## Normalized packet

Validate every substantive handoff with `scripts/validate_research_packet.py`. The packet contains:

- run scope, projects, themes, task/vault/web coverage, and repository access mode;
- observed need ledger with minimized task/vault evidence references;
- claim-level source ledger and repository assessments;
- findings with deterministic relevance scores and target-specific applicability;
- repair-first ordered recommendations with proposed classification, validation, and rollback;
- explicit project-fix and global-candidate IDs for Upgrader review;
- `implementation_authorized: false`.

Researcher may propose `no-action`, `project-fix`, or `plugin-candidate`. It never declares a plugin upgrade complete and never applies a recommendation. Upgrader may change the classification after reconciling work evidence, project authority, promotion thresholds, and deterministic validation.

## Handoff decision

For each recommendation, Upgrader records one disposition:

- accept as a project fix or experiment under project authority;
- add or refresh a promotion-registry candidate;
- request narrower research or missing evidence;
- defer with a review trigger;
- reject with rationale.

Project-specific evidence remains in its vault. Only sanitized project-neutral claims and opaque evidence references may enter a global registry or plugin candidate. A source URL supports a claim; it does not prove project fit, implementation, deployment, or permission to mutate.
