---
type: hub
project: {{project_key}}
status: current
updated: {{date}}
valid_as_of: {{date}}
review_after: {{stable_review_after}}
sensitivity: internal
---

# {{project_name}} Project Operations

Start with [[wiki/{{project_key}}/current|Current state]], then use [[wiki/{{project_key}}/index|the index]] and [[dashboards/{{project_name}} PM|the PM cockpit]].

The tracker owns tasks. Obsidian owns evidence-backed context, decisions, PM control records, and historical snapshots.

## Agent loading order

1. Read [[wiki/{{project_key}}/current|current state]] and [[wiki/{{project_key}}/index|the index]].
2. Follow task routing to the smallest canonical page set.
3. Read receipts or live authorities only for current, exact, disputed, or high-impact claims.
4. At task close, write only source-backed durable changes and lint the changed surface.

Human capture: [[inbox|inbox]]. Audit trail: [[log|knowledge operations log]].
