# Resource hygiene

Use this contract when dirty, stale, obsolete, generated, cached, or duplicated resources could affect the requested outcome. Resource state is a condition to resolve, not a reason to narrate routine housekeeping.

## Classify before reacting

Pin the exact outcome and the source or candidate it requires, then classify only the resources that can affect it:

- **authoritative:** the exact current source, runtime, or immutable candidate needed for the claim;
- **user-owned working state:** tracked or untracked changes whose ownership or intent is not supplied;
- **task-owned temporary state:** a worktree, generated artifact, process, or cache created for the current task with an explicit purpose and disposal boundary;
- **retained recovery state:** a rollback package, patch, branch, or artifact still needed for recovery;
- **host-managed state:** a task catalog, plugin cache, generated index, or other resource whose lifecycle belongs to the host; or
- **unknown:** anything whose owner, purpose, freshness requirement, or recovery value is not supported.

`Dirty`, `stale`, and `obsolete` are not interchangeable. A dirty workspace may contain valuable user work. Evidence is stale only relative to a claim that requires newer evidence. A resource is obsolete only when its replacement, lack of live owner or reference, recovery value, and cleanup authority are all established.

## Resolve once at the narrowest faithful seam

Use one bounded probe that can change the next action. Refresh one exact authoritative source when freshness matters. Inspect only the relevant status, diff, task, package, process, or worktree inventory. Do not scan broad histories, caches, profiles, or sibling repositories merely to make the environment look tidy.

For Git state:

1. Pin the repository, revision or remote ref, and requested target.
2. Separate substantive tracked changes, untracked material, generated output, and representational churn such as line-ending-only differences. A whitespace-ignoring comparison is a diagnostic aid, never permission to discard the remaining diff.
3. Determine whether the changed paths overlap the requested candidate or make its base identity unreliable.
4. Continue in place when task ownership and overlap are safe. Otherwise use immutable Git objects for read-only work or an exact isolated worktree for writes.
5. Once another exact source is selected, exclude the noisy checkout from evidence and do not repeat its unchanged warning.

Unrelated dirt does not block unrelated work or make every claim unverified. Overlapping or base-defining dirt remains protected and must not be reset, cleaned, normalized, or overwritten without exact authority.

For freshness, silently refresh when the current authoritative value is cheaply available and the refresh has no material effect. Report a stale or unavailable source only when it leaves a claim unverified, creates a conflict, or changes the next action. Reuse the refreshed result until the source or candidate can reasonably have changed.

## Retire task-owned resources deliberately

Creation establishes a cleanup obligation, not deletion authority. Record a task-owned temporary resource's exact path or identity, purpose, owner, candidate preservation state, and intended disposal boundary in current task context.

A worktree or artifact is cleanup-eligible only when all relevant facts are supported immediately before removal:

- it is exactly identified and task-owned;
- no task, process, or person still uses it;
- required work is complete or explicitly abandoned;
- the candidate and any rollback value are preserved elsewhere;
- the worktree is clean, or every remaining artifact has an approved disposition;
- no needed unique commit or branch state would be lost; and
- the exact cleanup effect is covered by current approval or an unchanged standing policy.

Preview the exact path, associated branch or artifact, eligibility evidence, read-back, and recovery limit. Remove one target at a time, verify both filesystem and Git registration when applicable, and stop on drift or partial cleanup. Dirty, active, unmerged, uniquely valuable, unknown, or inaccessible resources remain protected.

Group recurring cleanup findings into one bounded decision. Do not make every substantive task inventory the whole machine, enumerate an unactionable backlog, or repeatedly announce the same retained resource.

## Preserve task-compatible plugin upgrades

A plugin rollback copy outside the task-loaded path is recovery material; it does not keep a pre-existing task operational. Before a Poppy installation, treat every unfinished task known to use the current package as bound to its exact loaded package path.

The installation preview must state whether that path will remain byte-identical and readable. If the installer rotates or removes it, either:

- stop before installation and use a maintenance boundary in which affected tasks first reach a safe checkpoint; or
- include an exact compatibility action that preserves or restores the prior package at the original task-loaded path from verified byte-identical source, then read both old-path continuity and new-task selection back.

Do not call another cache entry active, redirect an old task to a newer package, or use cache ordering as evidence. A fresh task proves the new package. A pre-existing task remains bound to its original package until the host supplies authoritative migration evidence. If a required loaded file has already disappeared, report that host lifecycle failure once; use instructions already loaded in the task when sufficient, but do not claim compliance with an unread replacement skill. Request a fresh task only when the missing contract can materially change safety or outcome and no faithful current-task path remains.

Retire an old package path only after no retained task or rollback depends on it and the exact cleanup effect is authorized. Cache accumulation and cache rotation are both lifecycle failures when ownership and retirement are not explicit.

## Keep resource mechanics quiet

Surface resource state only when it changes the candidate, evidence status, authority, risk, or next action. Prefer a concrete statement such as “I excluded the shared checkout and pinned commit X” over a generic “the worktree is dirty.” After resolution, carry the decision in current context and do not repeat it unless the state changes.

This contract adds no daemon, registry, telemetry, generated policy, cleanup automation, or persistent ledger. It relies on bounded inspection, exact ownership, existing task context, and effect-specific read-back.
