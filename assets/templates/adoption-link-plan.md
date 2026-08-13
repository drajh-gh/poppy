---
type: plan
project: {{project_key}}
status: proposed
updated: {{date}}
valid_as_of: {{date}}
review_after: {{review_after}}
sensitivity: internal
---

# {{project_name}} PM navigation adoption plan

This proposal exists because onboarding preserved the existing navigation files. Review each target in context and apply only after explicit confirmation.

## Proposed links

| Existing surface | Additive link | Purpose |
|---|---|---|
| `Start Here.md` | `[[dashboards/{{project_name}} PM|{{project_name}} PM cockpit]]` | Primary PM entrypoint |
| `wiki/{{project_key}}/index.md` | `[[wiki/{{project_key}}/pm/index|PM control index]]` | Connect project knowledge to PM records |
| `wiki/{{project_key}}/current.md` | `[[dashboards/{{project_name}} PM|PM cockpit]]` | Current-state handoff |
| `wiki/{{project_key}}/source-map.md` | `[[wiki/{{project_key}}/pm/project-profile|Project profile]]` | Connect authority mappings to source configuration |

## Application gate

Before changing a target, reread its current contents, reject duplicate or malformed links, preserve its existing structure, show the exact patch, and obtain confirmation. After applying, lint the vault and record one adoption receipt. This file is a proposal and grants no write authority.

