# Poppy repository rules

This repository is the canonical source for the project-agnostic Poppy product.

## Product boundary

- Keep the Codex Project Operations plugin installable from the repository root.
- Keep the Obsidian cockpit and its localhost bridge under `apps/obsidian-cockpit`.
- Treat `references/poppy-capability-graph.json` as the only authoritative capability graph. Packaging may copy it; source code must not maintain another graph by hand.
- Keep real project adapters, vault contents, runtime ledgers/databases, screenshots, credentials, machine paths, installed plugin copies, and live configuration out of Git.
- Use only clearly synthetic identifiers in fixtures and examples.

## Authority and safety

- Do not write project vault content from product tests. Cockpit integration tests create disposable synthetic vaults.
- Bind the bridge only to `127.0.0.1`; external providers remain disabled unless a project-local configuration and authority explicitly enable them.
- Never infer a healthy state from missing evidence. Preserve Gray semantics.
- Do not publish, install into a real vault, contact a remote, merge, or deploy without separate exact authority.

## Verification

Run `python scripts/verify_product.py`. Before handing off a committed candidate, run `python scripts/verify_product.py --require-clean` and prove both nominated source commits remain ancestors of `HEAD`.
