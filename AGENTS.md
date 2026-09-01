# Poppy repository rules

This repository is the canonical, project-agnostic source for Poppy v3.

## Product boundary

- Keep the plugin installable from the repository root and expose only skills plus the declared optional trusted hooks.
- Keep the release's exact declared skill inventory: `poppy`, `poppy-context`, `poppy-intake`, `poppy-decide`, `poppy-coordinate`, `poppy-research`, `poppy-diagnose`, `poppy-delivery`, `poppy-acceptance`, `poppy-assure`, `poppy-learn`, `poppy-housekeeping`, and `poppy-scribe`. The count is not a product principle; an inventory change requires a distinct ownership contract, routing evidence, verifier update, and rollback coverage.
- Keep hooks deterministic, bounded, transcript-free, network-free, and subordinate to skill policy and native effect authority. Housekeeping remains stateless. Scribe remains conversation-bound until a supported non-rendered transport is separately selected and verified. Never embed raw checkpoint payloads in assistant-visible text or treat formatting as privacy.
- Do not add a cockpit, MCP server, telemetry, recurring automation, graph registry, daemon or persistent runtime, schema platform, execution ledger, project adapter, generated repository instructions, or repository-local installation.
- Keep real project names, vault contents, runtime records, credentials, machine paths, installed plugin copies, and live configuration out of Git.
- Use only clearly synthetic identifiers in tests and examples.

## Behavior and safety

- Preserve existing user changes. If an intended edit overlaps them, stop and ask for direction.
- Treat claims as unverified when required evidence is missing, stale, inaccessible, malformed, or insufficient, and conflicted when credible sources disagree. Never infer health from absence.
- Project profiles and confidence may narrow authority; they never expand it.
- External effects require a named target and effect, preview, exact approval, read-back verification, and rollback path.
- Keep tracker state and durable memory distinct.
- Keep one writer per target. A delegated writer uses an isolated worktree; otherwise delegates remain read-only.
- Do not publish, commit, push, merge, open a pull request, install, deploy, contact a remote, send a message, change a tracker, or perform a destructive action without the authority required for that exact effect.
- Keep local work bounded and preserve interactive machine responsiveness.

## Verification

Run `python scripts/verify_product.py`. Before handing off a separately authorized committed candidate, run `python scripts/verify_product.py --require-clean`. Preserve ancestry of the three nominated source commits and the v2 freeze commit declared in the verifier.
