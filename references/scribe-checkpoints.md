# Scribe checkpoints

Use this contract only after Poppy Scribe is explicitly active for the current task. A checkpoint is a compact derived reconstruction aid in current conversation context, not a transcript, receipt, artifact checkpoint, source of truth, lifecycle disposition, durable lesson, or private persistent record.

## Root recommendation and consent

Root Poppy should recommend Scribe when the likely future value justifies one short interruption:

- before continuity-risk work likely to span material phases, compaction or resume, a handoff, a long investigation, research or delivery, or several unresolved decisions and evidence threads;
- after Root has corrected or contained a material Poppy or Codex mistake, user correction, scope or authority drift, candidate drift, blind retry, stale-evidence reliance, or unsupported closure; or
- at a transition or comparison boundary where a compact reconstruction or recurring friction signal can materially change later work.

Say why Scribe would help and ask a direct yes-or-no question. Do not require the user to know the specialist name in advance. Ask at most once for the same material reason. A decline suppresses another offer unless a materially new reason appears. A prior standing preference applies only when the user explicitly supplied it.

The word “Scribe,” a question about Scribe, or Root's recommendation is not activation. Activate only on an explicit user request, an affirmative response to the current offer, or an applicable user-supplied standing preference.

## Semantic checkpoint

Preserve only material state:

- `mode`: quiet, review, or improve;
- `intent`: the current user-visible outcome and binding constraints;
- `decisions`: statement, status, rationale, and decisive evidence, with status proposed, user-confirmed, source-confirmed, superseded, or conflicted;
- `evidence`: claim, status, source pointer, and freshness, with status supported, unverified, conflicted, or contradicted;
- `changes`: exact target, state, summary, and verification, with state proposed, observed, locally-verified, or read-back-verified;
- `questions`: unresolved question, dependency, and owner;
- `next_step`: action, owner, required authority, and stop condition;
- `attention`: either absent or one material decision conflict, scope drift, authority drift, candidate drift, stale-evidence risk, blind retry, or unsupported closure;
- `friction`: at most three stable fingerprints with a short summary and evidence status; and
- `redactions`: short descriptions of deliberately omitted sensitive content.

For a material mistake or correction, capture only:

- expected behavior;
- observed failure;
- material consequence;
- correction or current state;
- closest evidence pointer and status; and
- one stable friction fingerprint that could be compared later.

Fix, stop, or contain the problem before recording it. Do not copy raw prompts or transcript passages. Prefer semantic statements and compact primary-evidence pointers. Never include credentials, access tokens, private keys, unnecessary personal data, full file contents, broad project records, or every attempt.

## Current transport boundary

Maintain the checkpoint in current conversation context only. Current Codex hooks do not expose a verified non-rendered model-to-hook payload channel, so this release does not persist, hydrate, expire, or delete Scribe checkpoints through a hook.

Never append raw JSON, HTML comments, hidden markers, or other machine-readable control payloads to assistant-visible text. Formatting is not a privacy boundary. If the host later exposes a genuinely private transport, it requires a separate selected design, exact-candidate verification, migration and rollback coverage, and updated acceptance scenarios before use.

When the user asks Scribe to stop or forget, stop maintaining the conversation checkpoint. Explain only if material that this does not delete conversation history, project artifacts, tracker state, or durable memory.

## Review and improvement

Quiet Scribe maintains state without narrating mechanics. Surface only one attention flag when it can change the next decision.

Scribe Review compares the current checkpoint with current evidence. Separate supported facts from unverified or conflicted reconstruction, identify material change, and provide the exact next action. When the user requests a checkpoint or portable handoff, return concise natural prose. Retain primary-evidence pointers and separately establish the artifact checkpoint required by [delegation and continuity](delegation-and-continuity.md); Scribe state alone never preserves a candidate.

Scribe Improve may compare only explicitly supplied bounded summaries from at least three independent tasks. Count independent task identities, not turns or repeated attempts. Require supported recurrence before naming a candidate. Report the pattern, representative examples available in the supplied summaries, a counterexample or expiry condition, likely consequence, and the smallest proposed intervention. A candidate may later be evaluated by Poppy Learn, but it cannot authorize a memory write, policy change, skill rewrite, tracker effect, or repository mutation.
