---
name: poppy-context
description: Resolve project identity, perform bounded two-page orientation, apply source authority, and manage durable project memory. Use behind Poppy when project context matters; directly invokable for focused testing.
---

# Poppy Context

Read [project context and memory](../../references/project-context.md) and [evidence and assurance](../../references/evidence-and-assurance.md).

## Orient

1. Resolve the repository and applicable instruction files.
2. Use only a profile already nominated by the task or instructions, or a root `project-ops.json`. Do not search broadly.
3. Validate the recognized identity, repository, vault, source-authority, sensitivity, and memory-write fields. Leave unknown legacy fields inert and unchanged.
4. For substantive work, read configured `current.md` and the project `index.md` once, then follow only task-relevant routes.
5. Treat project sources as authority for current facts and memory as compiled context with provenance.

Tiny work skips orientation.

## Fail closed

If identity is missing or malformed, permit read-only repository work only. Repository mutations and memory writes remain blocked until identity and applicable authority are confirmed. Never infer permission from a profile field that does not govern the exact effect.

## Write memory sparingly

Write only when evidence changed durable future understanding, the profile permits the exact write, the destination is confined to the configured project memory root, and the request is not trivial, read-only, diagnosis-only, or review-only. Preserve provenance. Do not mirror tracker items into memory.

Report what context was used, any stale or contradictory source, and every claim that remains Gray.
