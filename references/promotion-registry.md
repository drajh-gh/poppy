# Promotion registry

## Task orchestration v1

- Classification: plugin upgrade
- Status: integrated through the Poppy root; activation pending deterministic and independent assessment of the exact release
- Evidence: the original project-neutral plan, closure, title, authority, fan-out, reasoning-effort, archival, and privacy-minimized hygiene fixtures remain. Poppy adds trusted-turn trigger provenance, exact graph and plan digests, project identity, authority/risk reconciliation, root/parent/depth constraints, active-worker budgets, stop conditions, closure cards, join completeness, safe terminal paths, and postflight binding.
- Proposed contract: one root human-control surface; direct depth-1 workers; default two-active/five-created budget; structured no-prefix titles; event-only updates; relayed decisions; closure cards; clean or commit-recoverable worker archival; user-approved root archival; cleanup separation.
- Activation gate: the exact Poppy release must pass graph/plan/closure adversarial fixtures, the legacy task-orchestration suite, bounded live forward tests for worker start/decision/closure behavior, and fresh independent Functional QA and Final Assurance. Snapshot coverage remains Gray unless an explicitly normalized snapshot is supplied; analyzers never read private Codex databases.
- Remediation evidence: candidate `facfbb6b1ddc0ef48ac73218e04b36da012084a3` was blocked by Functional QA and live forward tests for substring triggering, unbound trigger/acceptance/risk, out-of-scope authority, over-constrained safe stops, denial/effect confusion, unresolved worker decisions, and default Windows skill decoding. The successor adds token-bound triggers, exact closure bindings, source-digested and action-bounded authority, plan-risk inheritance, normalized ask/escalate terminals, no-effect denial semantics, parent decision receipts, portable skill text, and deterministic regressions. It still requires fresh assessment as an exact new candidate.
- Second remediation evidence: candidate `319d6f60297603b4a399ce5a4476f11b01bd37c2` passed those regressions but was blocked because it could self-assert a non-root independent evaluator without a planned worker/closure card and because set comparison erased effect cardinality. The successor requires exactly one planned R2/R3 evaluator worker, binds its identity to a captured closure card, assigns stable unique effect IDs, and compares ordered effects without collapsing duplicates.
- Third remediation evidence: candidate `5aca349652aac2d6da9ad774ce203aeaa3ea4d3d` passed the live routing matrix but Functional QA found optional plan binding, stopped/failed evaluator states, a safe-stop execution branch, effects paired with skipped execution, contradictory authority, and Unicode-adjacent false triggers. The successor requires a bound plan for every closure, a planned/active evaluator plus completed closure card, no authorized execution on stopped dispositions, passing execution for every recorded effect, disjoint allowed/forbidden authority, and Unicode-aware name boundaries.
- Fourth remediation evidence: candidate `f1a6f26090dde8606f29da8bc523ae82a546e31d` passed a 50-case routing matrix but was blocked for evidence-free acceptance, authorized-versus-approval-required overlap, R3 authority inherited from a manifest, and self-asserted approval followed by execution. The successor requires direct evidence for passing acceptance, pairwise-disjoint authority buckets, separate exact R3 approval, and stop-only approval-required plans; execution begins only from a new authorized plan bound to the actual approval receipt.

## Generic owned-process supervisor

- Classification: plugin candidate
- Status: not activated
- Evidence: ordinary shell timeout can leave owned descendant processes running even when the local-execution policy requires an owned-process ledger and zero survivors. An isolated executable candidate and deterministic current-platform fixture cover pass, fail, timeout, a normal child/grandchild tree, unrelated-process survival, output/exit propagation, survivor reporting, and bounded rollback.
- Proposed contract: run a command under an owned process-tree supervisor, propagate output and exit status, terminate owned children and grandchildren on timeout, preserve unrelated processes, detect survivors, and provide a bounded rollback path.
- Promotion blocker: the Windows backend uses process-group signaling plus `taskkill`, not a Job Object, and has no ignored-termination, breakaway, racing-child, or leaked-handle evidence. POSIX execution and independent assessment are also missing.
- Next validation: implement a defensible Windows Job Object backend or explicitly narrow the guarantee to non-detaching descendants, then run adversarial Windows and POSIX matrices plus independent assessment. Do not activate or claim cross-platform containment until the exact stated guarantee passes.

## Operational control envelope v1

- Classification: plugin upgrade
- Status: activation authorized by Upgrader Run 01 for the exact package that passes independent Functional QA and Final Assurance; inactive until those gates pass and that assessed package is installed
- Evidence: Researcher Run 01 found cross-project reporting, authority, source-identity, and release-evidence gaps plus direct EverAway duplicate retrieval. A schema-v1 project-neutral packet and adversarial fixtures now cover R1, R4, R5, R6, R7, and the R9 Gray safeguard.
- Proposed contract: canonical source preflight; one logical retrieval with physical retries and success-only checkpoints; expiring human authority; outcome-first executive body with evidence appendix; and a source-revision-to-runtime release tuple with explicit Gray gaps.
- Validation: the deterministic suite rejects duplicate logical reads, failure checkpoint advancement, retired locators, unsupported incremental control without Gray, expired active authority, false Green, source-revision mismatch, false verified releases, word-cap overflow, appendix evidence loss, and client leakage. New profiles receive safe defaults; schema-v1 profiles without `controls` remain valid.
- Rollback: remove active skill references and default profile controls in an additive release while retaining stable source IDs, checkpoints, failures, authority receipts, detailed health records, and release evidence.
- Post-activation observation: review two daily and two weekly cycles per project for user concision corrections, evidence loss, request reuse, and call/time change. Reopen or roll back if presentation or evidence quality regresses.

## Researcher discovery and schema-v2 validation

- Classification: plugin upgrade
- Status: activated and verified
- Evidence: commit `d80ad176963b388ba78552f6221f12655b7c5fcf`, installed version `0.1.0+codex.20260816080042`, live skill-catalog discovery, strict schema-v2 packet validation, and negative fixtures.
- Decision: R8 requires no further source change in this run. A second bounded catalog/validator verification passed before the Upgrader mutation surface was opened.

## SloSki GRAD canonical-stage preflight

- Classification: project fix
- Status: implemented in isolated branch; not pushed, merged, deployed, or executed against production
- Evidence: the GRAD candidate used invented `STAGE=prod` while canonical configuration and deployment use `ss-prd`. Branch `codex/grad-stage-preflight-upgrader` at commit `f7d1d8f81` changes the boundary to `ss-prd` and adds pure tests for alias rejection, incomplete configuration, canonical config paths, database identity, and local/test safeguards.
- Validation: ten focused unit tests pass; repository format and check gates pass with warnings only. No database, GRAD endpoint, deployment, or production connection was used.
- Rollback: revert the isolated commit; retain the failed preflight and Upgrader receipt.

## Artifact attestations

- Classification: plugin candidate
- Status: deferred
- Blockers: the release tuple must first operate successfully; private-plan eligibility and a stable artifact identity are not nominated. Attestation proves build provenance, not store acceptance, deployment, or runtime behavior.
- Next validation: one metadata-only fixture after the release tuple is established. Any CI or repository mutation requires separate authority.

## Explicit no-action safeguards

- Missing, stale, contradictory, or unauthoritative evidence remains owned, review-dated Gray. Do not add an inference feature that converts absence into Red, Green, or proof.
- Do not adopt psutil as the containment boundary, unreleased OpenTelemetry GenAI conventions as a hard dependency, RDF/OWL or a graph database, or LangGraph for the observed needs.
