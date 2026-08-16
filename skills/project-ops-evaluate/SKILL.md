---
name: project-ops-evaluate
description: Evaluate Project Operations readiness, confidence, risk, authority, graph completeness, execution evidence, and outcomes before and after work. Use internally whenever Poppy performs a readiness screen, substantive preflight, postflight self-evaluation, acceptance audit, confidence reassessment, or independent evaluation outside delivery-specific Functional QA and Final Assurance. Also use when the user asks Poppy to assess its own work or explain how confident it is.
---

# Project Operations evaluator

Read [Poppy orchestration](../../references/poppy-orchestration.md), [the capability graph](../../references/poppy-capability-graph.json), [evaluation cases](../../references/evaluation.md), and [approval policy](../../references/approval-and-risk.md). Evaluate evidence; do not perform the work being evaluated or create authority.

## Readiness screen

Before retrieval or mutation, classify the interaction and assess whether the objective, project, horizon, requested outcome, and risk surface are sufficiently clear. Return the interaction class, initial categorical confidence, risk floor, missing context, and one disposition: `answer-directly`, `orient-then-answer`, `discover-then-plan`, `execute-graph`, `ask-user`, or `escalate-approval`.

Keep this screen silent for simple questions unless uncertainty changes the answer or requires clarification.

## Substantive preflight

After bounded memory orientation and before dispatch:

1. Restate the objective and measurable acceptance items.
2. Verify project identity, source authority, evidence freshness, contradictions, and known gaps.
3. Verify that every selected graph node has its required input and that selected edges preserve dependency order.
4. Set the deterministic risk floor; raise but never lower it.
5. Separate authority already granted, actions that require approval, and forbidden effects.
6. Assess reversibility, rollback, verification, and whether delegation provides real isolation or coverage value.
7. Assign `high`, `medium`, `low`, or `insufficient` confidence with a concise evidence basis and explicit assumptions.
8. Block consequential execution when a required gate is missing, even if overall confidence would otherwise be high.

Do not invent percentages or average away a failed required gate. Confidence never creates authority; it is explanatory while gates and authority remain decisive.

## Postflight

Evaluate the exact plan and executed candidate:

1. Check every acceptance item as `pass`, `limited`, `fail`, or `unverified` against direct evidence.
2. Confirm that selected nodes ran or were explicitly skipped with a valid reason and that every required output reached its consumer.
3. Verify exact external effects, read-back evidence, repository/worktree state, and rollback readiness.
4. Reconcile contradictions, worker limitations, failed checks, stale evidence, and scope drift.
5. Confirm that memory disposition follows the read/write authority and that trivial/no-change work created no noise.
6. Reassess final confidence from the resulting evidence and state residual risk and unresolved questions.
7. Return exactly one general verdict: `PASS`, `PASS_WITH_LIMITATIONS`, `BLOCK_REMEDIATE`, or `ESCALATE`.

A failed or unverified required acceptance item cannot receive `PASS`. A changed delivery candidate invalidates delivery assessment and returns to its separate Functional QA stage; this evaluator never replaces [project-ops-assess](../project-ops-assess/SKILL.md).

For consequential work, remain read-only and independent from the implementer. Validate material Poppy plans and closures with `../../scripts/validate_poppy_orchestration.py`.
