# Project Operations vault instructions

## Purpose

This vault is the persistent, evidence-backed project memory and PM control record for {{project_name}} (`{{project_key}}`). External systems remain authoritative; Obsidian is the human interface and compiled memory.

## Ownership

- `inbox.md` and `daily/` are human-owned.
- `raw/` is immutable sanitized evidence; add a new receipt instead of rewriting history.
- `wiki/` is compiled project knowledge and PM control records.
- `dashboards/` and `templates/` are derived infrastructure.
- `log.md` is append-only.
- `project-ops.json` is the validated project profile.

## Start

Read `project-ops.json`, `wiki/{{project_key}}/index.md`, `wiki/{{project_key}}/current.md`, and `wiki/{{project_key}}/source-map.md`. Follow only relevant links and reread authoritative systems for current or high-impact claims.

## Boundaries

- The nominated tracker remains the task system; do not create an Obsidian backlog.
- Drive documents are authoritative only for the claim and approved revision configured in the profile.
- Repository code proves implementation, not deployment.
- Slack, email, meeting notes, and transcripts provide context but do not automatically approve scope.
- Source access never authorizes external writes.
- Exclude credentials, access instructions, raw production rows, unnecessary personal data, and unminimized sensitive cases.

## Close

Update durable knowledge only when it changed, capture one concise log entry, preserve evidence links, and lint the changed surface.

