# Reusable delivery orchestration

This protocol generalizes the proven Sloski Delivery OS. Project adapters retain repository-specific ticket, test, worktree, CI, deployment, and tracker rules.

## Dispatch manifest

Record project, session/run ID, work item, objective, acceptance contract, non-goals, dependencies, base revision, risk floor, maximum authority, allowed systems/actions, forbidden actions, execution budget, concurrency, required gates, stop conditions, approval identity/time, and evidence links. Never infer dispatch from backlog readiness.

Schema version 1 permits this optional execution policy:

```json
{
  "execution_policy": {
    "max_automatic_remediations": 1,
    "review_stages": ["functional_qa", "final_assurance"]
  }
}
```

The plugin ceiling is two automatic remediation rounds. Resolve the effective ceiling as the minimum of two and every declared adapter or approved-manifest limit; each declared value must be an integer from zero through two. An adapter or manifest may narrow the ceiling but cannot widen another boundary. Omitting `execution_policy` or either member preserves the plugin defaults: two rounds and ordered `functional_qa`, then `final_assurance`. A declared `review_stages` value must contain those two distinct roles in exactly that order.

## Concurrency and ownership

- Default to at most two active delivery workstreams unless the profile sets a lower limit.
- Use one parent run and one isolated branch/worktree per work item.
- Exactly one writer owns each worktree.
- Specialists, Functional QA, and Final Assurance begin read-only; the writer integrates findings.
- Run Functional QA and Final Assurance as separate fresh-assessor tasks. Do not collapse them into one review or verdict.

## State machine

`BRIEFED -> DISPATCH_APPROVED -> ALLOCATED -> REVALIDATED -> IN_PROGRESS -> FUNCTIONAL_QA_PENDING -> FINAL_ASSURANCE_PENDING -> PR_READY -> AWAITING_APPROVAL -> VERIFYING -> COMPLETE|PAUSED|ESCALATED|BLOCKED`

Either review stage may route a rejection to `REMEDIATION_n`; any changed candidate then returns to `FUNCTIONAL_QA_PENDING` before Final Assurance. Budget overrun, scope change, missing required evidence, exhaustion of the effective remediation ceiling, a risk-tier increase beyond authority, or an R3 boundary pauses and escalates. Preserve recoverable work and evidence.

## Review stages

- **Functional QA** checks only the approved acceptance contract and directly affected regressions on one exact candidate. It reports outcome evidence and a stage verdict without deciding broader approval authority.
- **Final Assurance** confirms that the passing Functional QA verdict applies to the same candidate, then checks exact identity, deterministic and hosted evidence, authority, separation of duties, external effects, rollback, and residual risk. It does not repeat Functional QA, invent acceptance criteria, or broaden the manifest.

A candidate revision change invalidates both stage verdicts. Missing, failed, stale, collapsed, or reversed stage evidence blocks handoff.

## Evidence packet

Freeze manifest version, effective execution policy, base/head, diff, acceptance matrix, deterministic tests/CI, specialist reports, proposed action, rollback/observability, external effects, prior remediation findings, and stage verdicts. Each assessor returns only `PASS_HANDOFF`, `BLOCK_REMEDIATE`, or `ESCALATE_APPROVAL` for its named stage. A stage verdict qualifies evidence; it does not itself authorize a write or any R2/R3 action.

The generic plugin defines this protocol but is not an executable delivery adapter by itself. A project must nominate and validate its tracker, repository, base branch, worktree allocator, deterministic gates, receipt schema, and approval boundaries. Preserve Sloski's repo-local adapter until its own pilot gate authorizes extraction.

## Closure

Verify the exact completed claim, capture one compact immutable run receipt, update durable knowledge only when it changed, and leave merge/deployment/production/client communication gated by the project policy.
