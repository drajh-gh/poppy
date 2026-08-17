# Poppy

Poppy is an evidence-backed Project Operations product for Codex and Obsidian. It combines a conversational orchestrator, a typed capability graph, project onboarding and memory, operational controls, delivery governance, research and improvement workflows, deterministic validators, and an Obsidian operations cockpit.

This repository is the complete project-agnostic product. The cockpit is one Poppy application, not the repository identity.

## Product map

- `.codex-plugin/` — installable Codex plugin metadata
- `skills/` — Poppy and its Project Operations capability skills
- `references/` — operating contracts and the canonical capability graph
- `assets/` — Obsidian templates and Bases used for project onboarding
- `scripts/` — bootstrap, validation, safety, and product verification tools
- `apps/obsidian-cockpit/` — Obsidian UI, localhost bridge, event contract, packaging, and tests
- `examples/` — synthetic documentation examples only
- `docs/` — product architecture, development, and release policy

## Data boundary

Poppy source never includes real project adapters, vault contents, live paths, credentials, runtime databases or ledgers, screenshots, or installed plugin copies. Projects supply their own adapter and local configuration. Missing configuration remains Gray.

The cockpit's checked-in `config/bridge.example.json` is intentionally inert: it binds to loopback, has no vaults, and disables Codex launch. Copy it to ignored `config/bridge.local.json` for local development, then supply project paths and explicitly validate the supported Codex boundary. Packaging uses the safe example; an installation process must provide its approved local configuration separately.

## Verify

```powershell
python scripts/verify_product.py
```

The single verifier runs the complete Project Operations deterministic suite, owned-process tests, Python compilation, cockpit unit/build/syntax/Obsidian/integration/package tests, client-boundary audit, canonical graph parity, and three-history ancestry proof. It uses disposable synthetic vaults and never depends on a real vault.

For a committed release candidate:

```powershell
python scripts/verify_product.py --require-clean
```

## Configure the cockpit locally

1. Copy `apps/obsidian-cockpit/config/bridge.example.json` to `apps/obsidian-cockpit/config/bridge.local.json`.
2. Add project keys, display names, and absolute vault roots to the local file.
3. Keep the bridge on `127.0.0.1`; nominate runtime storage and Codex integration explicitly.
4. Run the product verifier before any separately authorized development installation.

See [architecture](docs/architecture.md), [development](docs/development.md), [release policy](docs/release.md), and the [project adapter contract](references/project-adapter-contract.md).

## Waku

Waku informed several local-first dashboard ideas. No Waku source file is copied or executed. Attribution and the exact boundary are documented in `apps/obsidian-cockpit/docs/waku-attribution.md`.
