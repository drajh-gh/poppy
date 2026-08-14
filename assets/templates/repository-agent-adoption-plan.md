---
type: analysis
record_kind: repository-adoption-plan
project: {{project_key}}
status: draft
updated: {{date}}
valid_as_of: {{date}}
review_after: {{review_after}}
sensitivity: internal
sources: []
---

# {{project_name}} repository memory adoption plan

- Vault: `{{vault_path}}`
- Configured repositories: {{github_repositories}}

## Additive adapter

> For substantive {{project_name}} work, read `{{vault_path}}\wiki\{{project_key}}\current.md` and the project index, then follow task routing to the smallest canonical page set. Use `project-ops-memory` for retrieval, refresh, filing, and lint. External systems retain their configured authority. At close, update existing canonical memory only when source-backed durable understanding changed; otherwise write nothing.

## Application checklist

1. Find the repository's source-of-truth agent instructions; do not edit generated outputs.
2. Keep the always-on adapter below 150 words.
3. Preserve repository-specific authority and approval rules.
4. Verify root-to-working-directory instruction discovery.
5. Rehearse implementation, review-only, diagnosis, and no-durable-change prompts.

This plan does not authorize repository writes by itself.
