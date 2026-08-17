# Poppy Ops Cockpit

The Ops Cockpit is Poppy's private, Obsidian-native operational instrument panel. It exposes capability execution, project-scoped run history, evidence lineage, source freshness, time/tokens/cost basis, deterministic maintenance findings, and a bounded Codex task dock.

It is a subsystem of the Poppy product. Canonical orchestration skills, contracts, templates, and the capability graph live at the repository root.

## Boundaries

- Native dependency-free Obsidian `ItemView`, command, and ribbon entry
- Python standard-library localhost bridge bound to `127.0.0.1`
- Append-only JSONL telemetry and replayable SQLite projection
- Server-enforced project scoping for vaults, runs, events, findings, refresh, SSE, and owned Codex tasks
- Fail-closed Gray behavior when a vault has no configured project key or a response scope does not match
- Read-only vault indexing; no canonical vault writes
- Gray semantics for missing, stale, malformed, unsupported, or contradictory evidence
- External providers disabled in the shipped example configuration

## Configuration

`config/bridge.example.json` is a safe, inert template. It contains no projects, paths, credentials, or enabled Codex launch. For repository-local development, copy it to ignored `config/bridge.local.json` and supply approved project paths.

The build packages the safe template as `config/bridge.json`. A separately authorized installation workflow must provide its approved local config. Relative runtime paths are resolved inside the installed plugin directory; absolute paths are also supported when explicitly configured.

An installed cockpit never falls back to portfolio data. If the active vault does not exactly match one configured project, the plugin opens no operational HTTP or SSE stream and shows an explicit Gray configuration state. The bridge independently rejects missing, empty, and unknown scope on every operational endpoint.

## Shared bridge ownership

Multiple configured vaults share one localhost bridge. The Obsidian client derives the loopback endpoint from the packaged `bridge.json`, so health, API, SSE, and spawned service all use the same configured port. Each startup child carries an opaque instance token, while the Python service claims ownership by binding that port before opening the shared runtime. A losing child exits immediately; the plugin verifies the winning token and terminates any losing or timed-out child before returning. Only the vault instance that owns the active child may stop it on unload. Another active vault can then claim a fresh singleton after its next health or SSE retry.

The deterministic lifecycle regression starts two vault contenders concurrently, exercises repeated project-scoped polling and SSE reconnects, performs a simultaneous reload cycle, tests an unavailable-service timeout, and requires zero owned process survivors.

## Verify and package

From the product root:

```powershell
python scripts/verify_product.py
```

Or run the cockpit gate directly:

```powershell
python scripts/verify.py --check
```

The cockpit verifier runs Python unit tests, deterministic synthetic event replay, singleton dual-vault localhost lifecycle coverage, JavaScript syntax, Obsidian activation smoke, package build, project-isolation checks, temporary fixture installation, hash read-back, and canonical graph parity. It creates only temporary synthetic vaults.

The generated six-file package is under ignored `dist/poppy-ops-cockpit/`:

- `manifest.json`
- `main.js`
- `styles.css`
- `bridge/poppy_ops_bridge.py`
- `config/bridge.json`
- `config/poppy-capability-graph.json`

Do not copy it into a real vault without separate exact authority and completed review gates.

## Codex boundary

The bridge supports the official Codex App Server stdio interface, but the shipped example leaves launch disabled and compatibility unverified. A local operator must nominate the executable and controls, validate MCP isolation, and record compatibility before enabling the task dock. Draft preparation never implies tool or external-write authority.

## Waku

Waku influenced the local-first, event-driven presentation. No Waku source file is copied or executed. See `docs/waku-attribution.md`.
