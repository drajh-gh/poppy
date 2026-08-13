---
type: system
project: {{project_key}}
status: needs-review
updated: {{date}}
valid_as_of: {{date}}
review_after: {{review_after}}
sensitivity: {{sensitivity}}
sources: []
---

# {{project_name}} source map

| Source | Authority | Stable identifier | Access | Refresh pattern | Status |
| --- | --- | --- | --- | --- | --- |
| Google Drive | Configured documents |  | Read-only | Revision-aware | Unmapped |
| Povio Dashboard | Configured operational facts |  | Read-only | Weekly | Unmapped |
| Tracker | Work status and ownership |  | Read-only | Current-task | Unmapped |
| GitHub and CI | Implementation and release evidence |  | Read-only | Current-task | Unmapped |
| Slack and Gmail | Context and commitments |  | Read-only | Bounded | Unmapped |
| Calendar and meetings | Events and meeting evidence |  | Read-only | Event-driven | Unmapped |

## Contradiction rule

Preserve competing claims, identify the authority for the claim, and escalate material conflicts. Never use latest-value-wins.

