---
name: poppy-scribe
description: Preserve a bounded semantic checkpoint for task continuity, review material drift, and identify recurring improvement candidates across independent tasks. Use behind Poppy when the user asks for Scribe, continuous analysis, a checkpoint, resume or handoff context, what changed, or recurring improvements; directly invokable for focused testing. Do not use as truth, durable memory, lifecycle status, or effect authority.
---

# Poppy Scribe

Keep the task's meaning easy to recover without turning the conversation into a transcript, log, or second source of truth.

Read [Scribe checkpoints](../../references/scribe-checkpoints.md) before creating, restoring, reviewing, forgetting, or aggregating a checkpoint.

## Own continuity, not truth

Represent only the latest material working state: current intent, decisions with status, evidence limits, candidate changes, open questions, one next step, and at most one attention flag. Reconcile restored content against the newest user intent and closest primary evidence before relying on it.

A Scribe checkpoint is derived task context. It never establishes project facts, completion, acceptance, tracker state, memory, authority, or the success of an external effect. Substantive owners still decide those states; Housekeeping still owns Codex lifecycle metadata; Context still resolves source authority and memory destinations; Learn still governs durable lessons.

## Choose the smallest mode

- Quiet Scribe is the default: update the checkpoint silently and surface at most one material conflict, drift, stale-evidence risk, blind retry, or unsupported closure.
- Scribe Review answers an explicit checkpoint, handoff, “what changed,” “what is unverified,” or challenge request from the latest checkpoint plus current evidence.
- Scribe Improve reports only supported friction fingerprints that recur across at least three independent task checkpoints. Treat them as proposals with examples, a counterexample or expiry, and a recommended smallest intervention—not as permission to change policy, skills, memory, trackers, or code.

Do not infer activation from ordinary substantive work. Activate when the user explicitly asks for Scribe or when Root Poppy routes a requested continuity, checkpoint-review, or recurring-improvement outcome here. Keep it active within that task until the user asks Scribe to forget it or its bounded retention expires.

## Preserve the checkpoint

When Scribe is active, append the reference's hidden `poppy-scribe:v1` marker after every visible final response. The hook stores only that structured marker in private plugin data; never place raw prompts, transcript excerpts, credentials, unnecessary personal data, or broad project records in it.

If restored state conflicts with current evidence or user intent, preserve the conflict explicitly instead of smoothing it away. If a hook reports that refresh failed or state may be stale, say so only when it affects the user's decision and rebuild the smallest safe checkpoint from current evidence.

When the user asks Scribe to forget this task, emit the exact forget marker from the reference. Forgetting removes Scribe's local checkpoint only; it does not delete conversation history, project artifacts, tracker state, or durable memory.

Lead review and improvement answers with the usable finding. Keep routine checkpoint mechanics invisible.
