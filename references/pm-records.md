# PM control records

Create a canonical note only for a distinct project, domain, workflow, system, milestone, decision, material commitment, change, risk, stakeholder, incident pattern, or reusable analysis. Tickets, messages, emails, reports, and PRs normally remain evidence and update canonical records.

## Common fields

Every compiled record uses `status` for the knowledge lifecycle and `pm_state` for operational state:

```yaml
type: analysis
record_kind:
project:
status:
pm_state:
updated:
valid_as_of:
review_after:
sensitivity: internal
confidence:
evidence_grade:
supersedes: []
sources: []
```

Use `type: analysis` plus one of the operational `record_kind` values: `milestone`, `commitment`, `raid-item`, `change-request`, `stakeholder`, `budget-snapshot`, `health-snapshot`, `meeting-note`, `portfolio-summary`, `improvement-candidate`, `research-brief`, `repository-assessment`, `research-handoff`, `operational-control`, `human-authority`, or `release-evidence`. Decisions remain `type: decision`. This keeps Project Operations records compatible with the Project OS knowledge lifecycle while letting Bases select operational records precisely.

Poppy run evidence is not a canonical analysis by default. Use `type: source`, `record_kind: orchestration-run`, `source_system: pm-os`, and `orchestrator: poppy` under `raw/<project>/pm-os/runs/` only for a durable-evidence run, consequential decision or verified effect, material safety failure, or learning-worthy confidence change. Keep routine preflight and postflight inside that receipt and expose it through the Orchestration Base.

Use `status: current|draft|needs-review|superseded` for milestone, commitment, RAID, change, stakeholder, budget, and health records. Do not place values such as `blocked`, `overdue`, `approved`, or `at-risk` in `status`; those belong in `pm_state` or `health`. Decisions and open questions retain their Project OS lifecycle values.

## Milestone

Add `owner`, `target_date`, `forecast_date`, `acceptance_criteria`, `dependencies`, `health`, and `canonical_ticket`. Milestone completion requires authoritative acceptance evidence.

## Commitment

Add `owner`, `counterparty`, `due`, `status`, `related_milestone`, `canonical_ticket`, and `confirmation_status`. Do not create a duplicate Obsidian task when the tracker already owns execution.

## Change request

Add `classification`, `requested_by`, `scope_impact`, `cost_impact`, `schedule_impact`, `quality_impact`, `approval_status`, `approver`, and `linked_tickets`. Classifications: `in-scope`, `clarification`, `defect`, `material-enhancement`, `additional-work`, `uncertain`.

## Risk or issue

Add `kind`, `probability`, `impact`, `exposure`, `owner`, `trigger`, `response`, `due`, and `health`. Preserve assumptions and dependencies explicitly; do not collapse them into generic risks.

## Stakeholder

Add `organization`, `role`, `decision_rights`, `influence`, `interest`, `goals`, `success_criteria`, `preferred_channel`, `cadence`, `availability`, `last_touch`, `open_concerns`, and `commitments`. Record work preferences and verified decision patterns only. Do not infer personality, protected characteristics, or sensitive private traits.

## Budget snapshot

Add `period`, `currency`, `approved_budget`, `actual_cost`, `actual_hours`, `committed_cost`, `estimate_to_complete`, `estimate_at_completion`, `forecast_variance`, `unpriced_change`, and source references. If baseline is absent, report Gray instead of calculating a favorable status.

## Health snapshot

Add each configured health dimension, `overall_health`, `meaningful_changes`, `decisions_required`, `next_actions`, and `freshness_gaps`. Store a dated snapshot; `current.md` compiles only the present orientation.

## Research records

For a research brief, add `research_run_id`, `scope_level`, `priority_lane`, coverage, need IDs, finding IDs, and source references. For a repository assessment, add canonical URL, maintainer evidence, maintenance date, license, security/quality signals, inspection mode, and outcome. For an Upgrader handoff, add project-fix and global-candidate IDs and keep `implementation_authorized: false`.

## Operational controls

An operational-control record links the normalized retrieval ledger, source preflight, authority receipts, health assertions, release tuples, report envelope, and validator result for one bounded run. A human-authority record retains source, reason, scope, effective date, `review_after`, and next-run assertion without replacing missing system evidence. A release-evidence record keeps source, artifact, build, delivery/store, and runtime links separate and uses Gray for every incomplete tuple.
