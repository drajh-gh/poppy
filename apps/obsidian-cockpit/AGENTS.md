# Poppy Ops Cockpit subsystem rules

This directory contains Poppy's private, localhost-only Obsidian operations cockpit. Repository-wide rules live at `../../AGENTS.md`.

## Authority

- Treat `../../references/poppy-capability-graph.json` as canonical; `scripts/build.py` copies it into the generated package.
- Never commit `config/bridge.local.json`, generated `dist`, runtime state, evidence captures, real project identities, or machine paths.
- Never write to project vault content. The bridge may read configured vaults and may write only its own repository-local runtime ledger and SQLite read model.
- Never inspect undocumented Codex storage, credentials, hidden prompts, or reasoning.
- Codex integration must use an official structured surface. When unavailable, report Gray; do not infer success from process presence.
- External providers are read-only, draft-only, or deep-link-only. This repository contains no connector write implementation.
- Real-vault installation is a separately authorized post-assurance effect.

## Implementation constraints

- The Obsidian plugin is dependency-free CommonJS JavaScript and CSS.
- The local bridge uses Python 3.14 standard library only.
- Bind only to `127.0.0.1`.
- Raw telemetry is append-only JSONL. SQLite is a replayable derived model.
- Missing, stale, contradictory, malformed, or unsupported evidence remains Gray.
- Tests may use synthetic events, but synthetic evidence never satisfies live Codex compatibility.

## Deterministic gates

Run `python scripts/verify.py --check`. It performs unit tests, deterministic synthetic replay, plugin runtime smoke, package build, localhost integration, project-isolation checks, temporary fixture installation, canonical-graph parity, and hash read-back. Live Codex compatibility remains a local release gate when that feature is enabled.
