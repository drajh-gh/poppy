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

Read [task housekeeping](../../references/task-housekeeping.md) before changing lifecycle metadata, auditing multiple tasks or worktrees, evaluating archive eligibility, or preparing a recurring housekeeping run.

## Reconcile the lifecycle

1. Re-read the originating request, current substantive owner, exact candidate, decisive evidence, unresolved gates, and latest user intent.
2. Classify only the metadata state supported by that evidence. Missing or conflicting evidence leaves the task active or preserves its existing marker.
3. Preview the exact task ID, current title, proposed title or archive effect, reason, read-back, and rollback.
4. Apply only the authorized metadata effect through the native Codex task tools.
5. Read the authoritative task state back. A successful tool response alone is not verification.

Title and archive mutations are external effects. Read [authority and effects](../../references/authority-and-effects.md) before performing them. A user may grant standing authority for one exact housekeeping policy; changed targets, policy, risk, or rollback require a new preview and approval.

## Audit proportionally

Start with the smallest authoritative task or project listing. Read individual tasks only when they are plausible candidates for a lifecycle change, duplicate, stale handoff, overlapping worktree, or archive action. Prefer a compact findings-and-actions report over rearranging the sidebar.

Keep pinned tasks protected. Suggest sidebar moves, title normalization, consolidation, and automation changes unless the user authorized those exact effects. Never treat task history as the durable artifact store, delete a worktree, or release a candidate owner merely because a task was marked or archived.

Treat the bundled Housekeeping hooks as stateless reminders and syntax guards, not as semantic authority. The separate Scribe helper may restore derived working context, but it cannot establish lifecycle truth. Housekeeping must still inspect current evidence and native task state.
