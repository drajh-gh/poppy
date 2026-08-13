# Project Operations architecture

## Operating model

Use three peer orchestrators over one evidence-backed project record:

- **Solution Architect** designs or reconfigures the operating system, source authority, delivery adapter, gates, and project structure.
- **Chief of Staff** runs the project-management control loop and coordinates approved delivery through existing specialist skills.
- **Upgrader** studies actual work, friction, failures, corrections, and successful patterns; applies safe local improvements and governs promotion into the reusable plugin.

Use one persistent Chief of Staff task per project and one portfolio task consuming sanitized project summaries. Keep operational control, delivery execution, and improvement governance distinct while sharing evidence.

```text
External sources -> bounded evidence receipts -> compiled project memory
                                            -> operating design  -> Solution Architect
                                            -> PM control records -> Chief of Staff
                                            -> delivery context  -> Delivery workflow
                                            -> work evidence     -> Upgrader
```

## Authority boundaries

- Drive, contracts, trackers, GitHub, CI, finance systems, Slack, Gmail, Calendar, and Povio Dashboard remain authoritative for their nominated claims.
- Obsidian is the human interface, evidence index, compiled project memory, PM control record, and audit trail.
- Codex reconciles, assesses, drafts, and executes only within explicit authority.
- Boards or Linear remains the task tracker. Never maintain a duplicate Obsidian backlog.
- Repository code proves implementation, not deployment. Slack or a transcript explains context, not approved scope.

## Vault layers

```text
inbox.md, daily/       human-owned capture
raw/<project>/         immutable sanitized receipts
wiki/<project>/        canonical compiled knowledge and PM records
dashboards/            derived Obsidian Bases and navigation
templates/             reusable project-neutral scaffolds
log.md                 append-only knowledge operations
AGENTS.md              vault operating contract
project-ops.json       validated machine-readable project profile
```

## Core loops

### Architecture loop

1. Discover objectives, constraints, sources, authority, approvals, and project archetype.
2. Design or reconfigure the smallest viable operating system and delivery adapter.
3. Preview artifacts, gaps, migrations, and external effects.
4. Validate the profile and deterministic scaffolding.
5. Hand ongoing control to the Chief of Staff and improvement evidence to the Upgrader.

### PM loop

1. Sense changed evidence.
2. Reconcile sources and contradictions.
3. Assess outcomes, scope, budget, timeline, quality, capacity, risks, commitments, and freshness.
4. Produce ranked decisions and actions.
5. Draft communications or tracker changes.
6. Obtain approval when policy requires it.
7. Execute the exact approved write.
8. Verify the result and update durable memory.

### Delivery loop

1. Prepare candidate evidence.
2. Approve a bounded dispatch manifest.
3. Allocate one run and one writer.
4. Implement in isolation.
5. Freeze evidence and use a fresh assessor.
6. Remediate at most twice.
7. Prepare a one-stop handoff.
8. Require separate approval for merge, deployment, production, or sensitive communication.

### Upgrade loop

1. Bound the review period and enumerate relevant completed or materially attempted work.
2. Use one efficiency analyst and, when useful, one workflow-quality analyst as read-only subagents.
3. Reconcile outcomes, retries, delays, user corrections, tool failures, safeguards, and successful patterns.
4. Classify each supported improvement as no action, project fix, plugin candidate, or plugin upgrade.
5. Apply only authorized, reversible project-level improvements; validate them and record evidence.
6. Add reusable candidates to the promotion registry; require cross-project evidence or a project-neutral deterministic proof before promotion.
7. Prepare plugin changes and an independent assessment. Plugin activation, marketplace updates, and broad behavioral changes remain approval-gated unless the current manifest explicitly grants them.
8. Stay silent when there is no material learning.

## Portfolio isolation

Publish only normalized project health, milestone, capacity, commercial variance, risk, decision, and freshness fields. Never publish raw client evidence, credentials, personal data, production rows, or contract text into the portfolio vault.
