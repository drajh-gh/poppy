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

Poppy starts from the user's situation and progressively loads only the specialist guidance needed for the next coherent phase. Decision maps, review structures, diagnosis evidence, specifications, and ticket previews are informational task aids—not a workflow runtime or persistent graph.

When a project is mapped to an external Obsidian vault, Poppy can use it as evidence-backed project memory through the nominated profile. The vault remains outside the repository, raw receipts remain immutable, compiled pages retain provenance and freshness, and tracker state is never mirrored into memory. No Obsidian bridge or cockpit is required.

## Verify

```powershell
python scripts/verify_product.py
```

For a separately authorized committed candidate:

```powershell
python scripts/verify_product.py --require-clean
```

See the [v3 constitution](docs/constitution-v3.md), [development guide](docs/development.md), and [release policy](docs/release.md).
