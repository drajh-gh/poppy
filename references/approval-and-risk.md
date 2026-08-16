# Approval and risk policy

Authority comes from the current user instruction or an approved manifest. Confidence never creates authority.

## Conservative PM policy

| Operation | Default |
| --- | --- |
| Read configured sources | Allowed |
| Search reputable public sources and inspect public repository pages/metadata | Allowed |
| Clone, download, install, import, or execute third-party repository code | Denied unless separately approved |
| Write sanitized Obsidian receipts and compiled internal records | Allowed with audit |
| Generate reports, messages, tickets, and schedule changes | Draft allowed |
| Create or update a tracker item | Confirm each |
| Send email or Slack, or modify Calendar | Confirm each |
| Change a scope, budget, or milestone baseline | Named approver required |
| Close tickets, merge PRs, or deploy | Denied to the PM branch |
| Modify invoices, finance records, or production | Denied |

## Delivery risk tiers

- `R0`: read-only inspection, retrieval, planning, and diagnostics.
- `R1`: reversible local edits in an isolated worktree and local verification.
- `R2`: commit, push, draft PR, or structured tracker/GitHub update explicitly granted by an approved manifest.
- `R3`: merge, deployment, production mutation, security boundary, sensitive communication, material scope expansion, or difficult rollback.

An approved manifest may grant R0–R2 actions. Every R3 action requires separate exact approval. Failed required gates prevent R2 autonomy. A material disagreement between assessors or sources requires escalation.

## External-write protocol

1. Name the target, exact mutation, evidence, authority, and rollback.
2. Draft or preview the result.
3. Obtain the configured approval.
4. Execute only the approved mutation.
5. Read back or otherwise verify the result.
6. Capture a concise audited receipt.

Source access alone never authorizes messages, comments, tickets, calendar changes, code changes, deployments, or production writes.
Research evidence and repository inspection never authorize third-party execution, dependency adoption, project changes, or plugin promotion.

