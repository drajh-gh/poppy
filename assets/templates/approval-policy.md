---
type: workflow
project: {{project_key}}
status: current
updated: {{date}}
valid_as_of: {{date}}
review_after: {{stable_review_after}}
sensitivity: {{sensitivity}}
sources: []
---

# {{project_name}} approval policy

Preset: **{{approval_preset}}**

| Operation | Policy |
| --- | --- |
| Read configured sources | Allowed |
| Write sanitized internal Obsidian records | Allow with audit |
| Generate reports, tickets, and messages | Draft |
| Tracker write | {{tracker_write}} |
| Email send | {{email_send}} |
| Slack send | {{slack_send}} |
| Calendar write | {{calendar_write}} |
| Baseline change | {{baseline_change}} |
| Finance write | {{finance_write}} |
| Merge or deployment | {{merge_or_deploy}} |

## Named approvers

## Exceptions

