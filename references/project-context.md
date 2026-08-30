# Project context and memory

## Resolve only required context

Start with the current repository and its applicable instruction files. Stop when they establish the identity, scope, and source authority needed for the task.

Consult external project configuration only when it can change the result:

1. one exact match in the user's local Poppy project index;
2. a profile named in the conversation or project instructions; or
3. project-ops.json at the repository root or at one exact project-memory root nominated by project instructions.

Do not invoke project context merely because work is substantive or repository-backed. Do not search a user profile, vault collection, or drive for a project; infer identity from a directory name; probe sibling vaults; or create repository-local overrides or generated policy.

The optional personal index lives at poppy/projects.json under the user's Codex home, outside repositories and plugin packages. It contains version 1 and a projects list. Each entry uses an exact match.git_remote or match.repository_root plus profile. Select at most one exact match. Duplicate matches, malformed entries, and missing required values leave the dependent claim unverified. The index nominates a profile; it grants no effect authority.

## Read profiles backward-compatibly

Treat a profile as configuration, never authority for a new effect. Read only fields needed for:

- project identity and sensitivity;
- repository identity and default branch;
- vault root, project root, current page, and index page;
- source-authority mappings; and
- memory-write policy.

Older profiles may express these through project, sources.github, vault, authority, and an applicable memory approval field. Unknown fields remain inert. Validate required types and ensure every resolved memory path stays inside the configured vault root.

A selected repository plus applicable instructions can establish repository identity. A profile is required only when nominated or when the task depends on its source or memory configuration. Missing or malformed required identity or authority leaves the dependent mutation or claim unverified; it does not block unrelated read-only repository work. A profile never grants broader authority.

## Orient only when current state matters

Read configured current.md and index.md once only when cross-source current state, decisions, domain context, source authority, or memory continuity can materially change the answer or requested effect. Then follow only task-relevant links. Do not repeatedly reload unchanged orientation pages.

Use source systems for current facts. Treat memory as compiled understanding with provenance, not as automatically current. Read only explicitly nominated glossaries, context maps, decisions, or architecture records. Code is authoritative for current implementation, not automatically for intended behavior or domain meaning.

For a nominated Obsidian vault, read its applicable instructions before its configured current and index pages. Respect freshness, sensitivity, aliases, translations, links, and source ownership. Raw receipts are immutable evidence. Compiled pages may be refreshed only from stronger sources with the required authority. Do not scan the vault broadly or touch human-owned inbox or daily notes unless explicitly asked.

## Write memory sparingly

Write durable memory only when all are true:

- a completed evidenced outcome changed future-useful understanding;
- the exact write is authorized by the request and project policy;
- the target is inside the configured project-memory root;
- provenance and source authority can be preserved; and
- the work is not trivial, read-only, review-only, diagnosis-only, proposed, conflicted, or unverified.

Tracker state remains in the tracker. Memory may preserve rationale, a decision, risk, or lesson and link to authoritative sources; it must not become a second backlog.

Prefer the existing canonical compiled page. Preserve frontmatter, links, freshness, provenance, aliases, translations, immutable receipts, and any required knowledge log. Preview the exact write, obtain approval, write only that target, and read the changed surface back. Never invent a memory silo because a session produced useful reasoning.
