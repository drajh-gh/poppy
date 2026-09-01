# Scribe checkpoints

Use this contract only while Poppy Scribe is explicitly active for the current task. A checkpoint is a compact derived reconstruction aid, not a transcript, receipt, artifact checkpoint, source of truth, lifecycle disposition, or durable lesson.

## Semantic checkpoint

Preserve only material state:

- `mode`: `quiet`, `review`, or `improve`;
- `intent`: the current user-visible outcome and binding constraints;
- `decisions`: statement, status, rationale, and decisive evidence, with status `proposed`, `user-confirmed`, `source-confirmed`, `superseded`, or `conflicted`;
- `evidence`: claim, status, source pointer, and freshness, with status `supported`, `unverified`, `conflicted`, or `contradicted`;
- `changes`: exact target, state, summary, and verification, with state `proposed`, `observed`, `locally-verified`, or `read-back-verified`;
- `questions`: unresolved question, dependency, and owner;
- `next_step`: action, owner, required authority, and stop condition;
- `attention`: either `null` or one material flag whose kind is `decision-conflict`, `scope-drift`, `authority-drift`, `candidate-drift`, `stale-evidence`, `blind-retry`, or `unsupported-closure`;
- `friction`: at most three stable fingerprints with a short summary and evidence status; and
- `redactions`: short descriptions of deliberately omitted sensitive content.

Do not copy raw prompts or transcript passages. Prefer semantic statements and compact primary-evidence pointers. Never include credentials, access tokens, private keys, unnecessary personal data, or full file contents.

## Hidden marker

Append exactly one marker after the visible final answer, using compact valid JSON between the boundary lines:

```html
<!-- poppy-scribe:v1
{"action":"checkpoint","checkpoint":{"mode":"quiet","intent":"...","decisions":[],"evidence":[],"changes":[],"questions":[],"next_step":{"action":"...","owner":"...","authority":"...","stop_condition":"..."},"attention":null,"friction":[],"redactions":[]}}
poppy-scribe:end -->
```

The model supplies semantic fields only. The hook supplies the task hash, sequence, capture time, expiry, and turn identity. Invalid or oversized markers leave the previous checkpoint unchanged. When Scribe is active and the marker is accidentally omitted, the Stop hook may request one continuation solely to append it; never alter the visible answer during that continuation.

To forget the current task's local Scribe checkpoint, append:

```html
<!-- poppy-scribe:v1
{"action":"forget"}
poppy-scribe:end -->
```

## Hook lifecycle

- `UserPromptSubmit` activates only on an explicit Scribe request or hydrates an already active task. It does not persist the prompt.
- `Stop` parses the hidden marker and atomically replaces the one latest checkpoint for that task.
- `PreCompact` reports an in-flight turn whose latest stored checkpoint may be stale.
- `SessionStart` after resume or compaction restores the latest non-expired checkpoint as non-authoritative additional context.
- `SessionEnd` performs bounded expiry cleanup only. It does not infer completion or create a new semantic summary.

The helper is deterministic, bounded, transcript-free, and network-free. State is confined to the plugin's private data directory, capped in size and file count, retained for seven days, and replaced rather than appended. It creates no telemetry, execution ledger, background worker, graph, tracker, project adapter, or durable-memory surface.

## Review and improvement

Quiet Scribe updates state without narrating it. Surface only one attention flag when it can change the next decision.

Scribe Review compares the checkpoint with current evidence. Separate supported facts from unverified or conflicted reconstruction, identify material change, and provide the exact next action. For a portable handoff, retain primary-evidence pointers and separately establish the artifact checkpoint required by [delegation and continuity](delegation-and-continuity.md); Scribe state alone never preserves a candidate.

Scribe Improve may aggregate only supported friction fingerprints across non-expired checkpoints. Count independent task identities, not turns or repeated attempts. Require at least three independent tasks before naming a recurring candidate. Report the pattern, representative examples available in the checkpoint summaries, a counterexample or expiry condition, likely consequence, and the smallest proposed intervention. A candidate may later be evaluated by Poppy Learn, but it cannot authorize a memory write, policy change, skill rewrite, tracker effect, or repository mutation.
