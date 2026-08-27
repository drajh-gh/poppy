# Poppy v3

Poppy is a personal, skills-only Codex plugin. It helps one user move fluidly between project operations, product thinking, design, engineering, research, delivery, assurance, communication, and learning without installing project policy into a team's repository.

Poppy is deliberately small. There is no cockpit, telemetry service, automation, universal capability graph, runtime engine, schema platform, persistent execution ledger, or repository-local installation.

## Product map

- `.codex-plugin/plugin.json` — the skills-only plugin manifest.
- `skills/` — one adaptive root skill and six focused supporting skills.
- `references/` — progressively loaded behavioral guidance.
- `tests/scenarios.json` — deterministic synthetic acceptance material.
- `scripts/verify_product.py` — the canonical product gate.
- `docs/constitution-v3.md` — the product boundary and operating promise.

Poppy consumes project instructions, project-specific skills, and configured connectors as evidence and capability. It never generates or injects personal policy into shared project files.

## Verify

```powershell
python scripts/verify_product.py
```

For a separately authorized committed candidate:

```powershell
python scripts/verify_product.py --require-clean
```

See the [v3 constitution](docs/constitution-v3.md), [development guide](docs/development.md), and [release policy](docs/release.md).
