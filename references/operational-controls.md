# Executable operational controls

Use this project-neutral contract for substantive multi-source refreshes, material health reports, human authority that changes an assessment, and release-readiness claims. Project adapters nominate authorities and may narrow behavior; they may not weaken Gray semantics, reuse a retired locator, or turn a read into an external write.

Normalize the run with `scripts/validate_operational_control_packet.py`. A passing packet proves internal consistency of the recorded control evidence. It does not prove that a connector returned the truth, that a release reached production, or that a mutation is authorized.

## Retrieval ledger

- Compute one normalized fingerprint for each logical request from provider, stable source identity, bounded query, pagination window, and material options. Parameter order and formatting do not create a new logical request.
- Execute a fingerprint once per run. Later consumers reuse the logical result and record a reuse event.
- Keep physical attempts inside the logical request. A retry increments the physical attempt only; it never creates a second logical read.
- Record every success, not-modified response, partial result, and failure. A partial or failed final attempt retains the prior checkpoint and a minimized failure reference.
- Advance a checkpoint exactly once and only after a successful or authoritative not-modified result. Store dynamic checkpoints in dated receipts, never in the project profile.
- Prefer provider-native change feeds, conditional reads, or webhooks. When unavailable, use bounded polling and report the affected coverage as Gray or Partial rather than pretending it is incremental.

The ledger is a read-control envelope, not a universal connector API. It never authorizes a write to the provider.

## Canonical source preflight

Resolve each source by stable provider ID or an adapter-verified canonical root before retrieval. Record the current locator, retired locators, mutable-target discovery rule, review date, and change-control capability.

- Reject a canonical locator that matches a retired locator.
- Rediscover mutable targets by stable parent or provider ID; do not hard-code a mutable “latest” name as authority.
- A missing, moved, stale, unsupported, or contradictory source makes only its dependent claims Gray.
- Preserve confirmed stable IDs and prior checkpoints on rollback.

## Expiring human authority

Human context may calibrate trajectory or approve a bounded decision, but it does not replace missing system evidence. Add a receipt without rewriting the original human input. Record:

- source reference and reason;
- bounded claim scope;
- effective timestamp and `review_after`;
- the assertion to re-check on the next run;
- active, expired, or superseded state; and
- `silence_is_approval: false`.

An active receipt past `review_after` is invalid. When required evidence remains missing, the affected status remains Gray even if a human receipt explains the context. Rollback removes derived evaluation fields only; the original receipt remains durable.

## Executive report envelope

The user-facing body starts with state and decision, then the smallest set of control signals and actions needed by the named audience. It remains within the configured word cap, never above 750 words. Every included material claim maps to evidence in a linked appendix or dated health record.

Internal, confidential, and restricted claims are filtered from a client report. Layering changes presentation, not the underlying evidence: the detailed snapshot remains the evidence appendix and retains Gray, contradictions, sensitivity, and source references.

## Release-evidence tuple

Record source revision, artifact digest, build identity, delivery event, and runtime identity as separate links. Delivery may mean deployment, store submission, or store acceptance only when the project adapter nominates that exact authority.

- Artifact and runtime source revisions must match the top-level source revision for a verified tuple.
- Build provenance does not prove submission, acceptance, deployment, or runtime behavior.
- A missing source, artifact, build, delivery, or runtime link makes the tuple Gray and must be named explicitly.
- Never infer runtime state from repository code, a merge, or a successful build.

Rollback makes tuple fields optional again; it never converts Gray into a favorable status or deletes collected evidence.

## Validation and rollout

Before promotion, exercise the success path and principal failures: duplicate logical reads, retries, retained partial failures, retired roots, unsupported incremental APIs, expired authority, false Green, mismatched source revisions, incomplete release tuples, evidence loss, word-cap overflow, and client leakage.

Start with bounded historical replay or a project experiment. Compare material findings, calls, elapsed time, corrections, and evidence coverage. A feature-disabled rollback returns to the previous prompt/template behavior while retaining stable identities, checkpoints, failures, receipts, and release evidence.
