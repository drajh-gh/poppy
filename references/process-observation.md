# Quiet course correction

## Observe only at decision boundaries

Use readily available working context at four boundaries: a material failure, a proposed retry, a consequential action, or a completion claim. Do not watch every tool call or narrate the check.

Compare only what can change the next decision:

- the originating acceptance anchor and current phase;
- the exact candidate, input, environment, and observed state;
- decisive evidence, unresolved claims, and binding gates;
- the authorized target and effects; and
- the proposed next action and the new information it should produce.

Stop before a high-risk mistake when the target or effect is uncertain, user work may be overwritten, required authority, read-back, or rollback is missing, a blocking gate would be bypassed, candidate identity drifted, or a load-bearing safety fact remains unverified.

## Change the premise, not the attempt count

A retry is materially unchanged when its objective, candidate or input, relevant environment, causal hypothesis, and expected failure signal are unchanged. Repeating an unchanged deterministic action is not progress, regardless of attempt count.

Repeat only for a stated reason that can change the evidence:

- candidate, input, environment, or relevant state changed;
- freshness, insufficiency, or credible conflict limits the earlier result;
- a bounded transient failure is plausible and the retry policy permits it;
- a project-required gate must run against the changed candidate; or
- authoritative read-back is required after an effect.

Otherwise select one testable premise and name the concrete smallest probe that can distinguish it. Keep the observed symptom or failure fingerprint separate from an evidence-established cause or blocker. When no safe in-scope probe exists, stop and report the exact blocker instead of looping.

Before a long-running or model-based evaluation, name the decision it can change, the selected cases, the maximum calls and elapsed time, and the stop condition. Treat that budget as a boundary: do not automatically resume, widen, or repeat the run after it is reached. Preserve partial evidence, leave the dependent claim unverified, and ask only if a concrete expansion can materially change the decision.

## Keep completion phase-scoped

Reject completion when the evidence answers an adjacent question, a required gate remains binding, the decisive requested behavior is unverified, or the only exact candidate is not preserved. Do not require every possible downstream state: deployment, runtime, stakeholder acceptance, or another later phase may remain unverified when the requested phase is complete.

## Escalate without creating an observer

Route only a material candidate-bound uncertainty to Poppy Assure. Supply a compact transient question containing the acceptance item, exact candidate and state, observed failure or suspected mistake, proposed next action, authority and gates, and allowed checks. Root Poppy retains user-facing control and decides the course after the read-only result.

Course-correction observations are working context. Do not create an attempt log, receipt, score, graph, background task, watcher, telemetry stream, automation, tracker item, or memory entry. Ordinary observation does not silently activate Scribe. After correcting or containing a material Poppy or Codex mistake, Root may offer Scribe once to retain a compact redacted reconstruction and stable friction fingerprint in current conversation context. The offer is not activation, a decline suppresses repetition for the same reason, and Scribe still may not preserve every attempt or claim truth, completion, or learning. A completed supported outcome may later produce a durable lesson through Poppy Learn and, for an actual memory write, Poppy Context's separate authority and provenance gate.
