# Project context and memory

## Resolution order

For substantive work, resolve the project using only bounded, already-nominated locations:

1. the current repository and its instruction files;
2. the one matching entry in the user's local Poppy project index;
3. a profile named in the conversation or project instructions; or
4. `project-ops.json` at the repository root when present.

When a project instruction nominates one exact external project-memory or vault root, treat a `project-ops.json` at that exact root as nominated too. Do not probe sibling vaults or infer a different project from directory names.

The optional personal index lives at `poppy/projects.json` under the user's Codex home, outside repositories and plugin packages. It contains `version: 1` and a `projects` list. Each entry has `match.git_remote` or `match.repository_root` plus `profile`; every value is an exact string. Select only one exact match. Treat duplicate matches, malformed entries, or a missing file as Gray; never choose by a fuzzy directory-name match. The index nominates a profile but grants no effect authority. Do not create an `AGENTS.override.md` or copy the personal mapping into shared project files.

Do not search an entire user profile, vault collection, or drive for a project. Do not create repository-local overrides or generated policy.

## Backward-compatible profile read

Treat the profile as configuration, never as authority to perform a new effect. Read only the fields needed for:

- project identity and sensitivity;
- repository identity and default branch;
- vault root, project root, `current.md`, and `index.md`;
- source-authority mappings; and
- memory-write policy.

For older profiles, these values may be represented by `project`, `sources.github`, `vault`, `authority`, and the applicable memory approval field. Unknown fields remain inert and unchanged. Validate types and ensure resolved memory pages stay inside the configured vault root.

Missing or malformed project identity permits read-only repository work only. Repository mutations and memory writes fail closed until identity and authority are confirmed.

## Two-page orientation

For substantive work, read the configured `current.md` and project `index.md` once. Then follow only links relevant to the task. Do not repeatedly reload the same orientation pages unless the user changes the project or evidence changes materially. Tiny work skips orientation.

Use source systems for current facts. Treat memory as compiled understanding with provenance, not as automatically current.

## Memory writes

Write durable memory only when all are true:

- evidence changed future-useful understanding;
- the profile permits the exact write;
- the target page is inside the configured project memory root;
- the update preserves provenance and source authority; and
- the request is not read-only, diagnosis-only, review-only, or trivial.

Keep tracker state in the tracker. Memory may summarize a decision, rationale, risk, or lesson and link to authoritative sources; it must not become a second backlog.
