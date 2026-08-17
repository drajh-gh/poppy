# Poppy Ops Cockpit repository rules

This repository contains a private, localhost-only Obsidian operations cockpit.

## Authority

- The frozen delivery manifest is `docs/delivery-adapter.md` plus the manifest identified there.
- Work locally on `feature/poppy-ops-cockpit`. Never push, merge, deploy, or create remote resources.
- Never write to project vault content. The bridge may read configured vaults and may write only its own repository-local runtime ledger and SQLite read model.
- Never inspect undocumented Codex storage, credentials, hidden prompts, or reasoning.
- Codex integration must use an official structured surface. When unavailable, report Gray; do not infer success from process presence.
- External providers are read-only, draft-only, or deep-link-only. This repository contains no connector write implementation.
- Real-vault installation is a separately sequenced, post-assurance effect even though its exact paths are already authorized.

## Implementation constraints

- The Obsidian plugin is dependency-free CommonJS JavaScript and CSS.
- The local bridge uses Python 3.14 standard library only.
- Bind only to `127.0.0.1`.
- Raw telemetry is append-only JSONL. SQLite is a replayable derived model.
- Missing, stale, contradictory, malformed, or unsupported evidence remains Gray.
- Tests may use synthetic events, but synthetic evidence never satisfies live Codex compatibility.

## Deterministic gates

Run `python scripts/verify.py`. It performs unit tests, deterministic replay, plugin runtime smoke, package build, fixture installation, and hash read-back. A release candidate is not eligible for review while the required live Codex stream gate is Gray.
