---
name: project-ops-assess
description: Independently assess a frozen Project Operations delivery gate submission as either Functional QA or Final Assurance. Use as a fresh read-only reviewer before approved R2 actions, final PR assurance, consequential approval requests, or after remediation while preserving stage separation, risk floors, evidence quality, reversibility, and authority boundaries.
---

# Project Operations assessor

Read [delivery orchestration](../../references/delivery-orchestration.md), [task orchestration](../../references/task-orchestration.md), and [approval policy](../../references/approval-and-risk.md). Use only the submitted review stage, manifest version, effective execution policy, project rules, base/head revision, diff, acceptance matrix, deterministic and hosted results, specialist reports, prior stage verdict, rollback/observability, external effects, and prior findings.

1. Require exactly one named stage: `functional_qa` or `final_assurance`. Validate submission completeness, exact candidate identity, and independence; never combine both stages in one task or verdict.
2. Set the deterministic risk floor; raise but never lower it.
3. For `functional_qa`, check the approved acceptance contract and directly affected regressions against authoritative evidence. Do not decide broader approval authority.
4. For `final_assurance`, require a passing Functional QA verdict for the same exact candidate, then check identity, deterministic and hosted evidence, authority, separation, external effects, rollback, and residual risk. Do not repeat acceptance or regression review, invent criteria, or substitute assurance judgment for missing QA evidence.
5. Treat missing, stale, or failed required gates as failure, not reduced confidence. Any candidate revision change invalidates both review verdicts.
6. Identify contradictions, security/data boundaries, stage-specific risk, and unsupported claims without crossing the selected stage boundary.
7. Do not invent or intuit a confidence percentage. Use a score only when the active project adapter explicitly requires a validated deterministic method.
8. Return concise findings and exactly one stage verdict: `PASS_HANDOFF`, `BLOCK_REMEDIATE`, or `ESCALATE_APPROVAL`.

Remain a direct depth-1 worker with no human authority or child-task creation. Return a complete
closure card and `NEEDS_PARENT_DECISION` for any missing authority; never interpret user input in
the assessor task as approval.

Remain read-only. A verdict qualifies only the submitted evidence and never grants execution authority. Do not repair findings, reuse implementer-only hidden context, approve beyond the stricter adapter or manifest, collapse review roles, or let confidence authorize R2/R3 actions.
