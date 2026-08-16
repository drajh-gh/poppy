# Project Operations vault instructions

## Purpose

This vault is the persistent, evidence-backed project memory and PM control record for {{project_name}} (`{{project_key}}`). External systems remain authoritative; Obsidian is the human interface and compiled memory.

## Ownership

- `inbox.md` and `daily/` are human-owned.
- `raw/` is immutable sanitized evidence; add a receipt instead of rewriting history.
- `wiki/` is compiled project knowledge and PM control records.
- `wiki/{{project_key}}/pm/records/research/` stores research briefs, repository assessments, and Researcher-to-Upgrader handoffs.
- `raw/{{project_key}}/research/` stores immutable minimized research receipts only when stable source links are insufficient.
- `dashboards/` and `templates/` are derived infrastructure.
- `log.md` is append-only; `project-ops.json` is the validated profile.

## Task lifecycle

For substantive project work, read `wiki/{{project_key}}/current.md` and the index first. Then follow task routing to at most three additional canonical pages or about 2,500 routed-page words before widening. Read the profile, source map, receipts, or live authorities only when authority, freshness, sensitivity, exactness, contradiction, or external effects require them.

Explicit read-only, review-only, or diagnosis-only scope suppresses every vault write, including receipts and log entries; return proposed memory updates instead. Otherwise, at close, update durable memory only when source-backed understanding changed. Promote confirmed decisions, commitments, risks, milestones, incidents, and reusable findings; preserve stable ticket, PR, commit, CI, deployment, and verification references; update `current.md` only when present orientation changed; append one concise log entry and lint changed files. If nothing durable changed, write nothing.

## Boundaries

- The nominated tracker remains the task system; do not create an Obsidian backlog.
- Repository code proves implementation, not deployment.
- Slack, email, meetings, and transcripts provide context but do not automatically approve scope.
- Source access never authorizes external writes.
- Repository research is inspect-only unless separately approved; do not clone, download, install, import, or execute third-party code.
- Exclude credentials, access instructions, raw production rows, unnecessary personal data, and unminimized sensitive cases.
