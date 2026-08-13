# Sloski adoption adapter

Sloski is an adoption target, not the template to copy blindly. Its established Delivery OS stays authoritative for ticket execution while Project Operations adds the PM control plane around it.

## Preserve

- Repository: `C:\Dev\sloski-drop` on the repository's current canonical base. The retired OneDrive checkout is not a fallback.
- Rulesync is the source of truth for generated `AGENTS.md` and `.codex` surfaces; do not edit generated copies directly.
- Repo-local delivery skills: `prepare-delivery-session`, `orchestrate-board-ticket`, `assess-delivery-gate`, ticket/PR lifecycle skills, dispatch manifest, one-writer worktrees, proof packet, and delivery receipt.
- Existing Obsidian human-owned and evidence surfaces, including `AGENTS.md`, `raw/`, `inbox.md`, `daily/`, `log.md`, `current.md`, and existing canonical pages.
- One vault per project. Never place EverAway or Orodjarna project material inside the Sloski vault.
- Existing Monday 07:30 weekly Project OS refresh until an explicit migration is approved.

## Local execution guardrails

### Bootstrap

- Resolve the saved Codex project and task working directory before repository work. Require `C:\Dev\sloski-drop` to exist and `git rev-parse --show-toplevel` to resolve to that exact path.
- If the saved project, automation target, task working directory, or Git root points elsewhere, stop repository-dependent work and report a Gray coverage warning with the observed path. Do not search the retired OneDrive location or ask the user to reconstruct the scheduled task's purpose.

### One writer and branch isolation

- Before an R1 or R2 repository mutation, record the target branch, HEAD, staged set, complete status summary, registered worktree, and active Codex tasks that share the intended checkout.
- Never write or commit from the primary checkout when it is dirty, has an active `index.lock`, is used by another active task, or is on a branch unrelated to the approved change. Use a dedicated clean worktree at the explicitly approved base instead.
- Allocate one writer for the isolated worktree. Readers may inspect frozen evidence, but they must not mutate the writer's checkout. If a clean isolated writer cannot be established, stop and preserve the intended patch or plan without staging or committing it.
- Before handoff, prove that the source checkout is unchanged, the isolated branch has the intended parent, the diff contains only approved files, and the staged set is empty unless an approved commit is being prepared.

### Deterministic mutation and verification preflight

- Before Git staging, inspect `.git/index.lock`, relevant Git processes, and lock age/ownership. Never delete or quarantine a live or ambiguous lock. An old, ownerless lock may be preserved and moved only under explicit cleanup authority.
- Before dependency installation, verify `node_modules/.modules.yaml`, its `virtualStoreDir`, representative workspace links, and active package-manager processes. If topology is inconsistent, select and record an explicit repair path before running the ordinary install; do not infer that a timeout rolled back partial changes.
- Before database-backed tests, verify the required Docker, PostgreSQL, MinIO, migration, and fixture prerequisites without starting or resetting operator-owned infrastructure. Run changed database cases in bounded fresh processes after the repository-required setup. If a full file hangs, isolate cases rather than repeating the opaque suite.
- For every bounded external command, record the owned process ID or process tree. After a timeout, stop only owned processes, verify that none survived, and run the scoped integrity check before continuing.
- For a long or interrupted delivery, preserve a compact resume packet: branch and HEAD, changed files, last passed gate, current owned processes, blocker, remaining external-write gates, and exact resume instruction.

## Add through confirmed onboarding

- A Sloski PM dashboard that links to, rather than replaces, the existing project dashboard.
- Project profile, source map, charter, scope baseline, approval and communication plans, glossary, and PM records for milestones, commitments, changes, RAID, stakeholders, budget and health.
- Operational records use `pm_state`; Project OS knowledge lifecycle continues to use `status`.
- An adoption decision and immutable onboarding receipt.
- Optional portfolio summary containing only approved fields.

## Validation and migration gate

Run a dry bootstrap and vault lint before any write. Apply only additive, non-conflicting files after explicit confirmation. Do not extract the Sloski Delivery OS into the generic plugin until its project-defined pilot gate is met; current evidence is insufficient to claim that extraction is proven. If a live-vault audit exposes malformed links, duplicate metadata, or overdue knowledge, report them as separate remediation recommendations rather than silently folding them into adoption.
