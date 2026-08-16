# Researcher to Upgrader handoff

Researcher owns external discovery, source quality, repository due diligence, applicability, and recommendation evidence. Upgrader owns final classification, project experiments, promotion threshold, source changes, validation, rollback, activation, and durable improvement receipts.

## Normalized packet

Validate every substantive handoff as schema v2 with `scripts/validate_research_packet.py`. The packet contains:

- the tested plugin name/version, full source commit, Researcher skill, and validator path;
- run scope, projects, themes, task/vault/web coverage, and repository access mode;
- observed need ledger with minimized task/vault evidence references;
- claim-level source ledger and repository assessments;
- findings with deterministic relevance scores and target-specific applicability;
- repair-first ordered recommendations with proposed classification, validation, and rollback;
- explicit project-fix and global-candidate IDs for Upgrader review;
- `implementation_authorized: false`.

Each source records publication/release date or an explicit living/unknown state, limitations, and confidence. Each finding states applicability for every scoped project and `project-operations`, including a reasoned not-applicable result. Every coverage surface records a completeness basis, evidence references, and limitations consistent with `full`, `partial`, or `gray` status.

Researcher may propose `no-action`, `project-fix`, or `plugin-candidate`. It never declares a plugin upgrade complete and never applies a recommendation. Upgrader may change the classification after reconciling work evidence, project authority, promotion thresholds, and deterministic validation.

## Handoff decision

For each recommendation, Upgrader records one disposition:

- accept as a project fix or experiment under project authority;
- add or refresh a promotion-registry candidate;
- request narrower research or missing evidence;
- defer with a review trigger;
- reject with rationale.

Project-specific evidence remains in its vault. Only sanitized project-neutral claims and opaque evidence references may enter a global registry or plugin candidate. A source URL supports a claim; it does not prove project fit, implementation, deployment, or permission to mutate.
