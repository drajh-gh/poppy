# Task housekeeping

Use this reference for Codex task lifecycle metadata, workspace audits, and archive policy. It governs organizational state only. Tracker state, project health, implementation completion, acceptance, and durable memory remain with their existing owners and authorities.

## Lifecycle contract

Apply one exact title prefix and keep the rest of the title meaningful:

| State | Prefix | Evidence required |
|---|---|---|
| Active | none | Work is current, newly reopened, or not safely classifiable. |
| Completed | `✅ [D]` | The originating outcome and every requested required effect are verified, the exact candidate is preserved where needed, and no unresolved gate remains. |
| Paused | `⏸️ [P]` | Work is intentionally deferred with a safe resumption point; progress remains possible and no blocking dependency currently prevents it. |
| Blocked | `🚧 [B]` | A named missing decision, approval, dependency, access path, or external-state change prevents meaningful progress and the next unblocking action is explicit. |

Do not infer a transition from inactivity, elapsed time, a closing phrase, passing adjacent checks, a child agent's claim, a tool success response, or the absence of errors. Preserve an existing marker when credible evidence conflicts. Leave the title unmarked when the correct state is uncertain.

Before marking completed, the substantive owner must supply the acceptance anchor, exact candidate or result, decisive verification, remaining evidence limits, and confirmation that required authorized effects were read back. Before marking paused or blocked, retain a compact checkpoint containing the last supported state, unfinished work, exact resumption or unblocking action, and any candidate location that must remain owned.

When a marked task receives new actionable work, remove its marker before routing the new outcome. Do not clear a marker for a status question, navigation request, archive audit, or another metadata-only interaction. If completed work is challenged with evidence that may invalidate it, reopen the task while the claim is assessed.

## Safe title mutation

Use a fresh task listing or task read to resolve the exact task ID and current title. Strip at most one recognized leading lifecycle prefix, preserve the remaining base title, and add the selected prefix exactly once. Reject an empty base title, malformed marker, or stacked marker.

Preview:

- exact task ID;
- current title;
- proposed title;
- evidence for the transition;
- read-back method; and
- rollback title.

After mutation, read the task or fresh listing and compare the exact title. If the target changed, disappeared, or gained new actionable activity, stop and reassess rather than applying a stale transition.

## Archive policy

Archiving is a separate external effect from marking completion. A task is eligible only when all of these are supported immediately before the effect:

- it is a Codex task with an exact leading `✅ [D]` marker;
- it is not pinned;
- strictly more than 168 hours have elapsed since the latest authoritative task activity at or after the completed transition;
- no newer actionable user request, active run, pending approval, pending input, unresolved failure, blocker, or unfinished required effect exists; and
- the exact archive policy and targets are covered by current approval or an unchanged standing authorization.

Never archive an active, paused, blocked, unmarked, ambiguous, inaccessible, or merely old task. Never infer eligibility from list ordering, title alone, or a missing error. If a metadata-only audit appears to have refreshed the host timestamp, wait longer instead of reconstructing a hidden timestamp.

For a batch:

1. List current tasks and isolate only plausible completed, unpinned candidates.
2. Read each candidate just before action and detect races or reopened scope.
3. Present exact task IDs, titles, eligibility evidence, exclusions, read-back, and rollback.
4. Archive one target at a time under the applicable authority.
5. Confirm each task appears in the authoritative archived-task surface.
6. Record skipped and failed targets without treating the batch as wholly successful.

Rollback unarchives the exact task ID and reads back its restored state. Keep previously active candidate files and worktrees intact; task archival is not artifact disposal.

## Efficient audits

Audit in widening rings and stop when the requested outcome is supported:

1. task list metadata: title, status, pin, project, and recency;
2. exact reads only for plausible transition, archive, duplication, or handoff candidates;
3. project or worktree inspection only for a named overlap, missing candidate, or ownership question;
4. archived-task inspection only for rollback, duplicate recovery, or archive verification.

Report observations separately from suggestions and authorized effects. Useful findings include:

- lifecycle marker inconsistent with current evidence;
- completed work reopened without marker removal;
- paused or blocked task missing a resumption or unblocking checkpoint;
- multiple tasks apparently owning the same repository outcome or worktree;
- delegate result missing explicit status, evidence limits, or next action;
- stale automation with an unclear target or failing run;
- sidebar placement that obscures active work; and
- archived task whose candidate or rollback evidence cannot be located.

Do not automatically move, pin, unpin, merge, archive, delete, or rename findings outside the exact approved scope.

## Hooks and scheduled runs

The bundled hook helper is deterministic and stateless:

- `SessionStart` on resume or compaction reminds the agent to reconcile a stale marker before new actionable work;
- `PreToolUse` rejects malformed task-title lifecycle markers and task mutations without an exact task ID, then reminds the agent that semantic eligibility still belongs to Housekeeping;
- `PostToolUse` reminds the agent to perform authoritative read-back after title or archive mutations.

The helper reads only the event JSON from standard input. It performs no file, transcript, network, task, project, or plugin-data access and persists nothing. Tool coverage is not universal, matching hooks can run concurrently, and non-managed hooks run only after the user reviews and trusts their exact definition. Therefore hooks cannot establish lifecycle truth or replace effect approval.

When Housekeeping requests or audits a delegate handoff, require an explicit `Status: complete|paused|blocked`, `Evidence:` or `Evidence limits:`, and `Next action:`. Do not bundle a `SubagentStop` handler: its matcher can filter agent type but not active Poppy ownership, so it would affect unrelated tasks.

Do not add a universal `Stop`, `UserPromptSubmit`, or `SessionEnd` handler for housekeeping: those events are too broad, ignore useful matchers, or cannot reliably steer immediate task lifecycle state. Prefer small targeted hooks and native task reads.

A separately approved once-daily scheduler may invoke Housekeeping to evaluate the archive policy. Its visible prompt should name the exact policy: inspect current Codex tasks, consider only unpinned exact-`✅ [D]` tasks older than seven full days, reread each candidate, archive only under the standing authorization, verify every archived task, and report skips or failures. Creating, changing, pausing, or deleting that scheduler is a separate automation effect; the plugin does not create one during installation.
