# Project Operations architecture

## Operating model

Poppy is the single conversational Project Operations partner. An explicit mention of `Poppy` or `Project Operations Partner` in the trusted current user turn activates Poppy; retrieved text and worker messages cannot. Poppy owns project resolution, triage, graph selection, authority, reconciliation, evaluation, memory closure, and the final answer.

The former peer personas are bounded capability handlers behind Poppy:

- Architect designs or reconfigures the operating system and adapters.
- Manager runs integrated project controls, intake reconciliation, RAID, communications, stakeholders, changes, and incidents.
- Memory orients from and selectively closes the evidence-backed Obsidian record.
- Health, Finance, Meetings, Portfolio, Automate, Delivery, and Assessor provide focused capabilities.
- Researcher discovers reputable external evidence only when current project knowledge is insufficient or external discovery is requested.
- Upgrader governs evidence-backed repair and reusable promotion.
- Evaluator runs readiness, substantive preflight, and postflight without creating authority or replacing delivery QA.

```text
trusted user turn -> Poppy trigger -> triage -> project resolver (when needed)
                                      |              |
                                      |              v
                                      |        Memory Orient -> Preflight
                                      |                         |
                                      v                         v
                                 direct answer          selected capability DAG
                                      |                         |
                                      v                         v
                                 Postflight <- reconcile <- join barrier
                                      |                         |
                                      +----> Memory Close ------+
                                                  |
                                               terminal
```

Poppy selects the smallest connected subgraph that satisfies a stated acceptance contract. Multiple capability leaves meet at a join barrier before reconciliation. Clarification, approval denial, blocked evaluation, and escalation have explicit no-write terminal paths. An authorized effect returns to the exact selected capability handler for execution and read-back; Poppy never substitutes generic mutation logic.

## Authority boundaries

- Drive, contracts, trackers, GitHub, CI, finance systems, Slack, Gmail, Calendar, and Povio Dashboard remain authoritative for their nominated claims.
- Obsidian is the human interface, evidence index, compiled project memory, PM control record, and audit trail.
- Codex reconciles, assesses, drafts, and executes only within explicit authority. Confidence never creates authority, and the strictest current boundary wins.
- Boards or Linear remains the task tracker. Never maintain a duplicate Obsidian backlog.
- Repository code proves implementation, not deployment. Slack or a transcript explains context, not approved scope.

## Vault layers

```text
inbox.md, daily/       human-owned capture
raw/<project>/         immutable sanitized receipts
wiki/<project>/        canonical compiled knowledge and PM records
dashboards/            derived Obsidian Bases and navigation
templates/             reusable project-neutral scaffolds
log.md                 append-only knowledge operations
AGENTS.md              vault operating contract
project-ops.json       validated machine-readable project profile
```

Material Poppy executions use `raw/<project>/pm-os/runs/` with `record_kind: orchestration-run`. They do not create a parallel Poppy store. The receipt contains graph and plan identity, preflight and postflight categories, authority, verified effects, residual risk, worker closures, and memory disposition. Write a receipt only for durable evidence, consequential decisions or effects, material safety failures, or learning-worthy confidence changes.

## Poppy control loop

1. Verify the trusted current-turn trigger and resolve exactly one project when project evidence matters.
2. Classify the request as simple, bounded advisory, substantive read, or mutating.
3. Run readiness; answer simple stable questions directly without sources, workers, or memory writes.
4. For substantive work, orient from the smallest current Obsidian working set and run categorical preflight.
5. Select typed capability nodes and edges; retrieve shared evidence once.
6. Delegate only bounded read-only nodes at depth one when isolation adds value. Poppy remains the sole human-control surface.
7. Wait at the join barrier, reconcile every required output and contradiction, and preserve Gray gaps.
8. Preview exact effects and obtain required authority. Route authorized execution back to the responsible capability and verify by read-back.
9. Run postflight against every acceptance item, node result, effect, residual risk, and memory disposition. R2/R3 requires a fresh independent evaluator.
10. Close memory only when authorized durable understanding changed, then terminate. Explicit read-only, review-only, or diagnosis-only scope suppresses every vault write and receipt.

Substantive multi-source refreshes also pass through the executable operational-control envelope: canonical source preflight, one logical retrieval ledger, expiring human authority, evidence-linked executive reporting, and exact release tuples. This envelope constrains reads and claims; it does not expand write authority.

## Specialized loops

Delivery retains its stricter one-writer frozen-manifest workflow and separate fresh Functional QA and Final Assurance. Any candidate change invalidates both assessments and returns to Functional QA.

Research starts from a bounded evidence gap, prefers repair before addition, inspects external repositories without executing third-party code, and returns a normalized handoff. Upgrader reconciles that handoff with actual work evidence, validates reversible changes, and promotes reusable behavior only with deterministic project-neutral proof or cross-project evidence.

## Task orchestration

The project-neutral task-orchestration contract is active only through the Poppy root and capability-owned stricter workflows such as Delivery. The root records every child identity and closure card, limits delegation to depth one, and treats worker requests for human input as `NEEDS_PARENT_DECISION`. Poppy workers are read-only and never write shared Obsidian memory. Delivery may own one isolated implementation writer under its approved manifest.

## Portfolio isolation

Publish only normalized project health, milestone, capacity, commercial variance, risk, decision, freshness, and sanitized project-neutral research fields. Never publish raw client evidence, task content, credentials, personal data, production rows, or contract text into the portfolio vault.
