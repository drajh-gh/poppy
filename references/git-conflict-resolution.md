# Git conflict resolution

Use this playbook only when Git is already stopped on a conflicted merge, rebase, cherry-pick, or revert. Resolving content, staging, completing or abandoning the operation, changing history, and publication are separate authority levels.

## Pin operation and scope

Before editing, inspect:

- operation type and exact repository;
- current status and unrelated modified or untracked work;
- unresolved paths and index stages;
- named base, candidate commits, and operation todo state when applicable; and
- project instructions and defined verification.

Keep one writer for the conflicted index. Delegates may investigate intent read-only. Do not use broad staging or include unrelated work.

During rebase, explain that `ours` is the branch being rebased onto and `theirs` is the commit currently being replayed—the opposite of many users' merge intuition. Prefer semantic evidence over side labels.

## Reconstruct intent

Inspect authoritative commits, pull requests, issues, decisions, project instructions, and tests. Keep discovery separate from authority. Missing or ambiguous intent remains unverified; credible unresolved disagreement is conflicted.

Resolve behavior semantically, preserving both intents when compatible and naming a genuine tradeoff when they conflict. Do not mechanically choose one side or invent an unsupported third design. Stop when product intent is materially ambiguous or safe integration should not proceed.

Classify and handle text, rename/delete, modify/delete, add/add, binary, generated, lockfile, and submodule conflicts according to project policy. Regenerate derived files only with authorized, trusted tooling. Never execute contributed or downloaded code merely because it is part of a conflict.

## Verify before any completion effect

Require:

- an empty unresolved-index result;
- a scoped check for remaining conflict artifacts;
- review of the exact staged result if staging is authorized; and
- project-defined combined-behavior checks.

Never use `git add .`, `git add -A`, or `git commit -a`. Stage only reviewed exact paths with applicable approval. A clean worktree conflict resolution does not authorize staging, commit, continue, abort, skip, quit, branch changes, push, or publication. Git supports stopping and abandoning paths; “always resolve” is not a rule.

## Provenance

Adapted in original Poppy wording from Matt Pocock's MIT-licensed `resolving-merge-conflicts` guidance pinned at revision `321658273cb1d20b76026717d027d505790106d4`:

- https://github.com/mattpocock/skills/blob/321658273cb1d20b76026717d027d505790106d4/skills/engineering/resolving-merge-conflicts/SKILL.md

