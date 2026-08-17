# Development

## Prerequisites

- Git
- Python 3.11 or newer
- Node.js for JavaScript syntax and the dependency-free Obsidian smoke harness

No package installation is required for the deterministic suite.

## Workflow

1. Work on an isolated branch with one writer.
2. Keep project-specific adapters and live configuration outside tracked product source.
3. Edit the canonical capability graph only at `references/poppy-capability-graph.json`.
4. Run `python scripts/verify_product.py`.
5. Commit reviewable changes, then run `python scripts/verify_product.py --require-clean`.

Cockpit-only verification is available with:

```powershell
python apps/obsidian-cockpit/scripts/verify.py --check
```

It creates synthetic Atlas Demo and Beacon Demo vaults in a temporary directory, validates server-enforced project isolation, builds the six-file plugin package, and hash-checks two temporary installations. It never reads or writes a real vault.

## Local configuration

`apps/obsidian-cockpit/config/bridge.local.json` is ignored. Begin with `bridge.example.json`, then add local project paths. Do not commit the resulting file. Build output and runtime state are ignored as well.

To create a reviewed local installation candidate without changing the inert default package, use the ignored local configuration and an output below the ignored product runtime:

```powershell
python apps/obsidian-cockpit/scripts/build.py --config apps/obsidian-cockpit/config/bridge.local.json --output runtime/installation-candidate/poppy-ops-cockpit
```

The builder refuses custom output outside `runtime/` and always emits the exact six-file inventory.
