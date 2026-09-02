# Project context and memory

## Resolve only required context

Start with the current repository and its applicable instruction files. Stop when they establish the identity, scope, and source authority needed for the task.

Consult external project configuration only when it can change the result:

1. one exact match in the user's local Poppy project index;
2. a profile named in the conversation or project instructions; or
3. project-ops.json at the repository root or at one exact project-memory root nominated by project instructions.

Do not invoke project context merely because work is substantive or repository-backed. Do not search a user profile, vault collection, or drive for a project; infer identity from a directory name; probe sibling vaults; or create repository-local overrides or generated policy.

The optional personal index lives at poppy/projects.json under the user's Codex home, outside repositories and plugin packages. It contains version 1 and a projects list. Each entry uses an exact match.git_remote or match.repository_root plus profile. Select at most one exact match. Duplicate matches, malformed entries, and missing required values leave the dependent claim unverified. The index nominates a profile; it grants no effect authority.

Project selection cannot justify itself. Establish one eligible selection signal before opening an external target; do not open a candidate profile, vault, sibling repository, or memory page to discover whether that target should have been selected. A task title, working-directory or package name, thematic similarity, adjacent task, or target found by search is not a project match.

After a missing, malformed, duplicate, or zero-result index match, stop external orientation unless a different eligible signal was already supplied. Name that signal before following it. A handoff qualifies only when it explicitly carries the exact repository root, Git remote, or profile identity; a delegating task, title, or summary alone does not. Otherwise leave external project identity, source authority, and memory context unverified while continuing any unrelated work the selected repository can support.

## Resolve active Poppy from the task

When the subject is Poppy's current, installed, or running behavior, the current repository is not sufficient context by itself. Start with the loaded root `SKILL.md` path exposed to the task, walk upward only within that package to the nearest ancestor `.codex-plugin/plugin.json`, and read the plugin ID, manifest version, declared skill root, and observed inventory. This identifies the package the task can actually use.

Cache presence or version ordering is not activation evidence. Do not select a package because its directory name, manifest version, or modification time appears newest. Host-provided loaded-skill or enabled-plugin evidence outranks an unselected cache entry. A task created before an upgrade may remain bound to its older catalog; a claim about the newly active host package then requires a fresh task.

Pin the active package and repository candidate separately. For the active package, record the task-scoped plugin ID, version, inventory, and digest or source mapping when available. For the repository, record the exact revision, working-tree state, manifest version, inventory, and candidate digest when available. Establish parity only through direct normalized file comparison, equal candidate digests, or an authoritative installation receipt that binds both identities. Otherwise mark parity unverified; when the evidence disagrees and provenance does not resolve it, mark the dependent claim conflicted.

Use the active package for claims about what Poppy can do in the current task. Use the nominated repository candidate for implementation and source-history claims. Never silently substitute one for the other, and report a mismatch before a version-sensitive assessment continues.

For a Poppy self-update, treat the resolved canonical Git branch as release source and the installed package as an artifact derived from one exact merged revision. A dirty working tree, unmerged branch, cache directory, and pre-existing task are not releasable source identities. Resolve mismatch direction before mutation: if canonical source already contains the exact installed artifact, synchronize the checkout forward; do not reconstruct source backward from the cache. Treat cache-to-source copying as explicit recovery only when authoritative source is missing and direct provenance establishes the artifact.

## Read profiles backward-compatibly

Treat a profile as configuration, never authority for a new effect. Read only fields needed for:

- project identity and sensitivity;
- repository identity and default branch;
- vault root, optional home, project root, current page, and knowledge-map page, with `index` accepted only as a legacy alias;
- source-authority mappings; and
- memory-write policy.

Older profiles may express these through project, sources.github, vault, authority, and an applicable memory approval field. Unknown fields remain inert. Validate required types and ensure every resolved memory path stays inside the configured vault root.

A selected repository plus applicable instructions can establish repository identity. A profile is required only when nominated or when the task depends on its source or memory configuration. Missing or malformed required identity or authority leaves the dependent mutation or claim unverified; it does not block unrelated read-only repository work. A profile never grants broader authority.

## Orient only when current state matters

Read configured current and knowledge-map pages once only when cross-source current state, decisions, domain context, source authority, or memory continuity can materially change the answer or requested effect. Prefer `vault.knowledge_map`; use `vault.index` only for a profile that has not migrated. Then follow only task-relevant links. Do not repeatedly reload unchanged orientation pages.

Use source systems for current facts. Treat memory as compiled understanding with provenance, not as automatically current. Read only explicitly nominated glossaries, context maps, decisions, or architecture records. Code is authoritative for current implementation, not automatically for intended behavior or domain meaning.

A Poppy Scribe summary present in current task context is compiled working context, not a source-authority or memory surface. Use it to locate questions and primary evidence, then reconcile load-bearing claims against those sources. It cannot select a profile, resolve a conflict, establish current project state, or authorize a memory write.

For a nominated Obsidian vault, read its applicable instructions before its configured current and knowledge-map pages. Respect freshness, sensitivity, aliases, translations, links, and source ownership. Raw receipts are immutable evidence. Compiled pages may be refreshed only from stronger sources with the required authority. Do not scan the vault broadly or touch human-owned inbox or daily notes unless explicitly asked.

When the user explicitly requests a Scribe artifact, read only the profile's exact `scribe` fields required for that record. Resolve the target from the nominated vault root plus the configured incident, signal, review, improvement, or template path; reject absolute child paths, traversal, links or junctions escaping the vault, malformed configuration, ambiguous project selection, and a target under a human-owned path. Profile configuration narrows the destination but never supplies write approval.

## Write memory sparingly

Write durable memory only when all are true:

- a completed evidenced outcome changed future-useful understanding;
- the exact write is authorized by the request and project policy;
- the target is inside the configured project-memory root;
- provenance and source authority can be preserved; and
- the work is not trivial, read-only, review-only, diagnosis-only, proposed, conflicted, or unverified.

Tracker state remains in the tracker. Memory may preserve rationale, a decision, risk, or lesson and link to authoritative sources; it must not become a second backlog.

Prefer the existing canonical compiled page. Preserve frontmatter, links, freshness, provenance, aliases, translations, immutable receipts, and any required knowledge log. Preview the exact write, obtain approval, write only that target, and read the changed surface back. Never invent a memory silo because a session produced useful reasoning.
