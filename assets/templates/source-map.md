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

| Source | Authority | Stable ID or verified root | Change control | Review after | Status |
| --- | --- | --- | --- | --- | --- |
| Google Drive | Configured documents |  | Revision/change-feed |  | Unmapped |
| Povio Dashboard | Configured operational facts |  | Bounded polling |  | Unmapped |
| Tracker | Work status and ownership |  | Provider-native when available |  | Unmapped |
| GitHub and CI | Implementation and release evidence |  | Conditional/webhook |  | Unmapped |
| Slack and Gmail | Context and commitments |  | Provider-native when available |  | Unmapped |
| Calendar and meetings | Events and meeting evidence |  | Event-driven |  | Unmapped |

## Retired locators and mutable targets

List retired paths or identifiers explicitly. Rediscover mutable “latest” targets from a stable parent/provider ID and record `review_after`; never treat the mutable name itself as authority.

## Contradiction rule

Preserve competing claims, identify the authority for the claim, and escalate material conflicts. Never use latest-value-wins.

