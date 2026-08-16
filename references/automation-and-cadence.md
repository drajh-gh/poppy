# Automation and cadence

Automations are execution triggers, not project memory. The confirmed project profile defines cadence intent; Obsidian stores durable outputs and receipts; source systems remain authoritative for their owned facts.

## Default control purposes

| Control purpose | Suggested cadence | Output | No-change behavior |
|---|---|---|---|
| operational scan | weekdays, changed-only | exceptions, overdue commitments, blockers | stay silent |
| weekly planning | once weekly before planning | health snapshot, priority proposal, decisions needed | publish concise stable-state note only if requested |
| monthly governance | once monthly | budget, scope, milestone and stakeholder review | record reviewed/no material change |
| portfolio roll-up | after project refreshes | cross-project exceptions and decisions needed | stay silent |
| meeting follow-up | event-driven/manual | decisions, commitments, questions, confirmation draft | do not send without approval |
| workflow improvement | weekdays changed-only or weekly | evidence-backed project fixes, plugin candidates, and upgrade proposals | stay silent |
| external research | weekly or monthly changed-only | repair-first evidence, repository assessments, Researcher-to-Upgrader handoff | stay silent |

These are recommendations, not mandatory schedules. Frequency should follow project stage, client expectations, risk, budget burn, and signal availability.

## Safety contract

- Inspect existing automations before create or update.
- One automation per project and control purpose unless the user explicitly accepts overlap.
- Prefer a task heartbeat for recurring follow-up in the current context. Use a standalone job only when explicitly requested and a valid project target exists.
- Show schedule in the user's local timezone and keep recurrence syntax internal.
- External writes, messages, ticket changes, and client-facing outputs remain approval-gated even when an automation discovers them.
- A source outage or incomplete scan must produce a coverage warning, never a false green status.
- Workflow-improvement automations use `project-ops-upgrader`, inspect only the bounded task period, and may use at most two read-only specialists.
- Research automations use `project-ops-researcher` and `project-ops-memory`, bound task/vault/theme coverage, keep repository access `inspect-only`, and route actionable packets to `project-ops-upgrader` without applying them.
- Durable scheduled prompts explicitly invoke `project-ops-manager` and `project-ops-memory`, follow the repository adapter, and pass a manual rehearsal before activation.
- Prefer one consolidated project loop: weekday changed-only refresh, Friday semantic lint, and first-Monday governance. Add another automation only when isolation has a concrete operational benefit.
- Automatic project or plugin source mutations require an explicit approved manifest; ordinary scheduled runs classify, record candidates, and draft changes.
- Deconflict research and workflow-improvement schedules. Prefer one changed-only research-to-upgrade pipeline over overlapping scans.
- Changed-only monitoring should be quiet when there is no material change.
- Use the Codex automation API for all lifecycle changes. Never hand-edit automation files.

## Sloski coexistence

Sloski already has a Monday 07:30 weekly Project OS refresh. Treat it as an existing control surface. During adoption, either retain it and attach the PM roll-up to its output, or replace it only after the user confirms a complete migration. Do not create another Monday weekly refresh by default.
