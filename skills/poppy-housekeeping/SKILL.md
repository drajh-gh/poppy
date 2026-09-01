---
name: poppy-housekeeping
description: Maintain Codex task lifecycle metadata, titles, archive eligibility, delegation hygiene, and workspace organization. Use behind Poppy when work itself is resumed, paused, blocked, completed, audited, or archived; directly invokable for focused testing. Do not use for substantive project-status judgment.
---

# Poppy Housekeeping

Keep Codex work easy to find, resume, and safely retire without turning organization into a second project system.

## Own metadata, not truth

Consume the current primary owner's evidenced disposition. Do not decide that implementation, acceptance, assurance, coordination, or another substantive outcome is complete merely because activity stopped or a response sounded final.

Use exactly one lifecycle marker at the start of a Codex task title:

- active: no marker;
- completed: `✅ [D]`;
- paused: `⏸️ [P]`;
- blocked: `🚧 [B]`.

Preserve the meaningful base title. Never stack markers. A new actionable request in a marked task reopens it and clears the marker before substantive work continues; a status question or metadata-only audit does not.

## Use the single current-task fast path

After this skill is loaded, use this self-contained path only when every condition below is already supported:

- the user directly and explicitly requests active, completed, paused, or blocked state for the calling Codex task; that request is semantic approval for this exact reversible lifecycle-title effect, not evidence for the substantive disposition;
- the current context already contains the substantive owner's supported disposition: completed means the originating outcome and required effects are verified, the exact candidate is preserved where needed, and no gate remains; paused means work is intentionally deferred with a safe resumption point and no present blocker; blocked means a named dependency prevents progress and its next unblocking action is explicit; active means work is current or explicitly reopened;
- the native task surface can resolve the calling task, its exact current title, and current activity without guessing from list order or title similarity;
- the title has a meaningful base and either no marker or one exact recognized leading marker; and
- the only effect is this task's lifecycle title. No archive, pin, move, worktree, tracker, automation, project, or other task state may change.

Give one concise informational preview naming the calling task, requested state, title-only scope, supporting disposition, authoritative read-back, and prior-title rollback. Do not ask for a second confirmation: the direct request already approved that exact effect.

Then, in one orchestration turn, compose the available native Codex task calls to freshly resolve the calling task and current title/activity, validate the unchanged transition, apply at most one exact prefix, and read the exact title and activity back from the resolved task ID. Prefer the native implicit calling-task title target when it prevents heuristic task selection. If the exact requested lifecycle title state is already present and no activity drift exists, perform no mutation and finish from authoritative read-back.

Fail closed before mutation if the target, title, activity, evidence, or requested transition is ambiguous, missing, contradictory, or has drifted. If post-mutation read-back shows a title mismatch or newer contradictory activity, stop, report the observed mutation and the unverified or conflicted lifecycle result, and retain the exact prior title as rollback; do not silently claim success or automatically roll back. Reject a malformed, empty, or stacked title immediately without normalizing or mutating it.

Do not load [task housekeeping](../../references/task-housekeeping.md) or [authority and effects](../../references/authority-and-effects.md) for an eligible fast path or a syntax-only rejection. Read both references and use the full safe path for a named other task, multiple tasks, archiving, sidebar or worktree organization, standing policy, ambiguous intent, missing or conflicting disposition evidence, unavailable exact current-task resolution, drift before mutation, or any consequential or less-reversible effect.

## Use full reconciliation otherwise

1. Re-read the originating request, current substantive owner, exact candidate, decisive evidence, unresolved gates, and latest user intent.
2. Classify only the metadata state supported by that evidence. Missing or conflicting evidence leaves the task active or preserves its existing marker.
3. Preview the exact task ID, current title, proposed title or archive effect, reason, read-back, and rollback.
4. Apply only the authorized metadata effect through the native Codex task tools.
5. Read the authoritative task state back. A successful tool response alone is not verification.

Outside the eligible single current-task fast path, title and archive mutations are external effects. Read [task housekeeping](../../references/task-housekeeping.md) and [authority and effects](../../references/authority-and-effects.md) before performing them. A user may grant standing authority for one exact housekeeping policy; changed targets, policy, risk, or rollback require a new preview and approval.

## Audit proportionally

Start with the smallest authoritative task or project listing. Read individual tasks only when they are plausible candidates for a lifecycle change, duplicate, stale handoff, overlapping worktree, or archive action. Prefer a compact findings-and-actions report over rearranging the sidebar.

Keep pinned tasks protected. Suggest sidebar moves, title normalization, consolidation, and automation changes unless the user authorized those exact effects. Never treat task history as the durable artifact store, delete a worktree, or release a candidate owner merely because a task was marked or archived.

Treat the bundled Housekeeping hooks as stateless reminders and syntax guards, not as semantic authority. The separate Scribe helper may restore derived working context, but it cannot establish lifecycle truth. Housekeeping must still inspect current evidence and native task state.
