# Health, tolerances, and cadence

## Health dimensions

Assess outcomes, scope, schedule, budget, capacity, delivery flow, engineering quality, support, stakeholders, communication, risks, and evidence freshness. Raw activity counts do not determine health.

Use:

- `Green`: within agreed tolerance with current evidence.
- `Yellow`: material concern or forecast variance within escalation tolerance.
- `Red`: threshold breach, critical blocker, or outcome unlikely without intervention.
- `Gray`: required evidence, baseline, or authority is missing or stale.

Roll up with explicit rules: a critical Red makes overall Red unless an approved exception exists; otherwise the highest material concern wins. Always explain the threshold crossed and cite the evidence.

## Default measures

- Outcome and milestone confidence
- Approved versus suspected scope change
- Actual cost/hours, committed cost, estimate to complete, estimate at completion, and forecast variance
- Planned versus actual allocation
- Work age, WIP, throughput, cycle time, blocked age, and traceability to PR/release
- PR review age, CI state, deployment frequency, change lead time, change failure, recovery, and rework
- Incident/support age, recurrence, and escaped defects
- Unanswered asks, decisions waiting, commitments due, and stakeholder follow-ups
- Source freshness and contradictions

Do not use earned-value metrics unless the project has a trustworthy weighted scope and cost baseline.

## Operating cadence

- Event-driven: intake reconciliation, meeting debrief, material source change, incident, and milestone gate.
- Daily: changed-only ranked PM brief.
- Weekly: project health, plan versus actual, scope/budget/capacity reconciliation, commitments, and next-week plan.
- Monthly: portfolio and commercial review.
- Milestone: readiness, acceptance, handoff, and release gates.

No-change runs may refresh evidence silently. Do not notify merely because a scheduled job ran.

## Weekly report structure

1. Outcome and milestone confidence
2. Meaningful changes since the prior report
3. Scope, budget, schedule, and capacity variance
4. Delivery and quality
5. Top risks, issues, assumptions, and dependencies
6. Decisions required
7. Commitments due
8. Next-week plan
9. Evidence freshness and gaps

Derive internal and client-facing versions from the same source record. Exclude internal commercial detail, speculation, and sensitive evidence from the client version.
