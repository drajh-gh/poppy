# Poppy repository rules

This repository is the canonical, project-agnostic source for Poppy v3.

## Product boundary

- Keep the plugin installable from the repository root and expose only skills.
- Keep exactly seven skill directories: `poppy`, `poppy-context`, `poppy-operations`, `poppy-delivery`, `poppy-assure`, `poppy-research`, and `poppy-learn`.
- Do not add a cockpit, MCP server, telemetry, automation, graph registry, runtime, schema platform, execution ledger, project adapter, generated repository instructions, or repository-local installation.
- Keep real project names, vault contents, runtime records, credentials, machine paths, installed plugin copies, and live configuration out of Git.
- Use only clearly synthetic identifiers in tests and examples.

## Behavior and safety

- Preserve existing user changes. If an intended edit overlaps them, stop and ask for direction.
- Treat missing, stale, unsupported, or contradictory evidence as Gray at claim level. Never infer health from absence.
- Project profiles and confidence may narrow authority; they never expand it.
- External effects require a named target and effect, preview, exact approval, read-back verification, and rollback path.
- Keep tracker state and durable memory distinct.
- Keep one writer per target. A delegated writer uses an isolated worktree; otherwise delegates remain read-only.
- Do not publish, commit, push, merge, open a pull request, install, deploy, contact a remote, send a message, change a tracker, or perform a destructive action without the authority required for that exact effect.
- Keep local work bounded and preserve interactive machine responsiveness.

## Verification

Run `python scripts/verify_product.py`. Before handing off a separately authorized committed candidate, run `python scripts/verify_product.py --require-clean`. Preserve ancestry of the three nominated source commits and the v2 freeze commit declared in the verifier.
