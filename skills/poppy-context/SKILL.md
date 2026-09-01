---
name: poppy-context
description: Resolve required project identity, source authority, cross-source current context, exact nominated profiles, and durable-memory destinations. Use behind Poppy when those facts can change the result; directly invokable for focused testing. Do not invoke merely because work is substantive or repository-backed.
---

# Poppy Context

Read [project context and memory](../../references/project-context.md).

## Resolve only what matters

1. Start from the current repository and applicable instruction files.
2. Stop there when they establish the scope and authority needed for the task.
3. Consult only an exact project-index match, nominated profile, or root project-ops.json when external project evidence, source authority, or memory configuration can change the result.
4. Validate only the identity, repository, sensitivity, source-authority, vault, and memory fields the task needs. Unknown legacy fields remain inert.
5. Read configured current.md and index.md once only when current project state, decisions, cross-source authority, domain context, or memory continuity can materially change the answer or requested effect.
6. Follow only task-relevant routes. Treat project sources as authority for current facts and memory as compiled context with provenance.

Task size alone does not determine orientation. When freshness, conflict, evidence status, or consequential reporting is load-bearing, read [evidence and assurance](../../references/evidence-and-assurance.md). For terminology or current-versus-intended behavior, read [domain modeling](../../references/domain-modeling.md).

## Pin Poppy before assessing Poppy

When Poppy itself is the subject of a current-state discussion, assessment, capability claim, source comparison, or version-sensitive recommendation:

1. Treat the loaded root `SKILL.md` location supplied to the current task as the active-runtime anchor.
2. Resolve the package manifest and declared skill inventory from that loaded package without selecting another cache entry by name, timestamp, or version ordering.
3. Pin the repository candidate independently with its revision, working-tree state, declared version, inventory, and digest when available.
4. Compare the active package with a repository source revision only through direct file, digest, or recorded provenance evidence.
5. Report the task-active package, repository candidate, parity status, and affected evidence limits separately.

A pre-upgrade task may still be running an older loaded package. Report that task-scoped fact and require fresh-task host evidence before claiming a newer package is active. Never use the current working directory or an arbitrary repository checkout as a substitute for active-package evidence.

## Fail closed where required

An already selected repository plus applicable instructions may establish repository identity. A profile is required only when nominated or when the task depends on its source or memory configuration.

If identity or authority required for the requested effect is missing or malformed, remain read-only for that effect. A profile never grants new authority.

## Write memory sparingly

Write only when the completed outcome changed future-useful understanding, the exact write is authorized, the destination is inside the configured project-memory root, and provenance can be preserved. Do not write for trivial, read-only, review-only, diagnosis-only, proposed, conflicted, or unverified material. Keep tracker state in the tracker.

For an Obsidian vault, respect its instructions, immutable receipts, compiled-page freshness, aliases, translations, and human-owned inbox or daily notes. Read back every authorized write.

Report the context actually used, stale or contradictory sources, and affected unverified or conflicted claims.
