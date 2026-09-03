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

## Completion offers

Root may offer to mark the current task done once when the substantive owner first establishes a completed disposition. The offer belongs in the final answer after the completed result; it does not load Housekeeping, inspect the task, request an ID, change metadata, or grant authority. Use this exact concise form: “This task appears complete. Would you like me to mark it as done? If so, reply ‘mark this task as done.’”

A completion episode begins at the first supported transition of one actionable scope to completed. Offer only when the originating outcome, candidate preservation, decisive verification, required effect read-backs, and all gates support completion. Do not offer for status-only or metadata-only work, courtesy replies, partial completion, paused or blocked work, pending approval or acceptance, or when the user already requested a lifecycle transition.

Make at most one offer in the episode. Acceptance, decline, silence, or a later status or metadata question suppresses repetition. Resume and compaction do not reset suppression. A new actionable request or a challenge that may invalidate completion reopens the disposition; a later supported completion of that new scope begins a new episode and may receive one new offer. This suppression is conversation-bound and stateless; do not add a store, ledger, or task field to strengthen it.

An affirmative phrase alone is not a lifecycle command. After an offer, require an explicit command that names the current task or thread and lifecycle state. The bounded prompt hook may accept a narrow polite or affirmative prefix such as `Yes, mark this task as done` and a narrow suffix such as `with the tag`, but it must reject bare `Yes`, archive language, batches, named other tasks, and unrelated marking requests.

## Single current-task fast path

The Housekeeping entrypoint contains the complete executable fast-path contract so an eligible request does not need this reference or `authority-and-effects.md`. Eligibility requires all of the following:

- narrow lifecycle language: an unqualified request to mark the calling task `done` means the completed title marker only; it does not request archive and must not introduce archive language;
- exact current task only: a bounded `UserPromptSubmit` hook supplies the current Codex `session_id` as the exact task ID for the matching lifecycle request, never a named other task or a title/list-order inference;
- explicit request: the user directly requests active, completed, paused, or blocked state, possibly as an explicit command after Root's offer, which semantically approves only the exact reversible title rename; a bare affirmation does not qualify;
- supported disposition: the current context already supplies the substantive owner's candidate-bound evidence required by the lifecycle contract, and the user command alone does not manufacture that evidence;
- well-formed title: the current title has a non-empty meaningful base and at most one exact recognized leading marker;
- informational preview: state the current-task target, requested state, title-only scope, evidence, authoritative read-back, and that the guarded call will resolve and retain the exact prior title as rollback, without seeking duplicate confirmation or first listing tasks solely to populate the preview;
- one orchestration turn: in exactly one `functions.exec` code-mode call, read the supplied exact task ID, validate its title/activity and transition, apply at most one marker to that same ID, and authoritatively read it back; and
- isolated effect: no archive, pin, move, sidebar, worktree, tracker, automation, project, or other task state changes.

An already-correct lifecycle title state, including an already-unmarked active title, is an idempotent read-back success when the disposition and activity remain current. Reject empty, malformed, or stacked markers without normalization or mutation.

Do not call `list_threads`, probe the workspace, or make a preliminary native task call. The single guarded code-mode orchestration reads the supplied exact task ID, resolves the prior title before mutation, fails closed on any invalid or drifted state, returns that title as rollback, and performs the authoritative read-back. If the prompt hook could not supply a non-empty task ID, stop immediately without reference loading or discovery.

Fall back to the full safe path and load both references for a named other task, batch, archive, ambiguous lifecycle intent, missing or conflicting evidence, unavailable exact current-task resolution, standing policy, consequential or less-reversible effect, or target/title/activity drift detected before mutation. On post-mutation drift or contradictory read-back, leave the observed mutation in place, report the lifecycle effect as unverified or conflicted, retain the prior title as rollback, and stop without broadening the authorized effect.

## Safe title mutation

Use a fresh task listing or task read to resolve the exact task ID and current title. Strip at most one recognized leading lifecycle prefix, preserve the remaining base title, and add the selected prefix exactly once. Reject an empty base title, malformed marker, or stacked marker.

Preview:

- exact task ID;
- current title;
- proposed title;
- evidence for the transition;
- read-back method; and
- rollback title.

Recheck the target, title, and activity immediately before mutation and stop without changing it if any has drifted. After mutation, read the task or fresh listing and compare the exact title and activity; if they contradict the intended result, report the observed effect as unverified or conflicted and follow the applicable rollback authority. The current-task fast path never auto-rolls back.

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

## Workspace resource retirement

Use [resource hygiene](resource-hygiene.md) for dirty, duplicated, generated, cached, or apparently obsolete workspace state. Task lifecycle and resource lifecycle are separate: a completed or archived task does not prove its worktree, branch, package path, artifact, or rollback is disposable.

For a requested workspace audit, start with the exact selected repository and native task list. Summarize counts and classes first. Read a task or inspect a worktree only when it is a plausible live owner, overlap, preservation risk, or cleanup candidate. Do not recursively inventory unrelated repositories, the whole user profile, or every cache.

Classify each proposed cleanup target immediately before action. Protect dirty, active, inaccessible, unmerged, uniquely valuable, rollback-bearing, or unknown targets. For each eligible task-owned target, preview its exact path, registration, branch or detached revision, clean state, candidate preservation, absence of a live owner, read-back, and recovery limit. Cleanup is a destructive effect and requires exact authority or an unchanged standing policy; remove and verify one target at a time.

Once a shared checkout is excluded in favor of an immutable ref or isolated worktree, keep that resolution in current context and stop announcing the unchanged dirty checkout in later phases. Retained resources should appear in one grouped housekeeping decision, not as repeated warnings in substantive work.

## Hooks and scheduled runs

The bundled Housekeeping hook helper is deterministic and stateless:

- `SessionStart` on resume or compaction reminds the agent to reconcile a stale marker before new actionable work and not repeat an earlier completion offer without a newly completed scope;
- `UserPromptSubmit` adds the host-supplied current Codex `session_id` only for a narrowly matched explicit current-task lifecycle request, including bounded affirmative or polite prefixes and marker suffixes, returns no context for bare affirmations or ordinary prompts, and fails closed without listing or probing when the ID is absent or malformed;
- `PreToolUse` rejects malformed task-title lifecycle markers, requires an explicit ID for lifecycle-prefixed title changes and archives, retains the native implicit target only for ordinary non-lifecycle title edits, and reminds the agent that semantic eligibility still belongs to Housekeeping;
- `PostToolUse` reminds the agent to perform authoritative read-back after title or archive mutations.

The Housekeeping helper reads only the event JSON from standard input. It performs no file, transcript, network, task, project, or plugin-data access and persists nothing. Tool coverage is not universal, matching hooks can run concurrently, and non-managed hooks run only after the user reviews and trusts their exact definition. Therefore hooks cannot establish lifecycle truth or replace effect approval.

Scribe checkpoints are conversation-bound in this release and Scribe has no separate hook helper. Any Scribe summary or visible incident artifact remains derived operational context, never lifecycle evidence. Housekeeping must not infer a marker, completion, archive eligibility, or authority from it.

When Housekeeping requests or audits a delegate handoff, require an explicit `Status: complete|paused|blocked`, `Evidence:` or `Evidence limits:`, and `Next action:`. Do not bundle a `SubagentStop` handler: its matcher can filter agent type but not active Poppy ownership, so it would affect unrelated tasks.

Codex invokes `UserPromptSubmit` handlers for every prompt, so the helper itself performs the semantic match and emits `{}` outside the narrow lifecycle request. Keep that path bounded and prompt-content-free in its output. Do not use universal context as a substitute for semantic eligibility.

A separately approved once-daily scheduler may invoke Housekeeping to evaluate the archive policy. Its visible prompt should name the exact policy: inspect current Codex tasks, consider only unpinned exact-`✅ [D]` tasks older than seven full days, reread each candidate, archive only under the standing authorization, verify every archived task, and report skips or failures. Creating, changing, pausing, or deleting that scheduler is a separate automation effect; the plugin does not create one during installation.
