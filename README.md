# Poppy Ops Cockpit

A private, Obsidian-native instrument panel for understanding Poppy across the Sloski and EverAway project vaults. It exposes capability execution, run history, evidence lineage, source freshness, time/tokens/cost basis, deterministic maintenance findings, and a bounded Codex task dock.

## What is implemented

- Native dependency-free Obsidian `ItemView`, command, and ribbon entry
- Calm instrument-panel interface with a signature live execution rail
- Cross-vault read-only index for the two configured Project Operations vaults
- Source-backed Poppy graph loaded from a pinned local graph copy and checked by digest
- Append-only JSONL telemetry and deterministic SQLite projection
- Run, trace, evidence, source, freshness, capability, approval, worker, tool, token, duration, and cost views
- Official Codex App Server stdio adapter using the explicitly approved sandbox-bin executable
- Task preparation/resumption in read-only threads; drafts are not automatically submitted
- Read-only local refresh plus SSE and polling updates
- Deterministic optimization rules linked to events
- Gray semantics for every missing, stale, malformed, unsupported, or contradictory input

## Start locally

```powershell
python bridge/poppy_ops_bridge.py replay --source fixtures/events.jsonl
python bridge/poppy_ops_bridge.py serve
```

Open Obsidian and run **Poppy Ops Cockpit: Open operations cockpit** after the post-assurance development installation is complete.

The bridge binds only to `127.0.0.1:7317`. It writes only `runtime/events.jsonl` and `runtime/poppy-ops.sqlite3`. Refreshing the cockpit never rewrites either project vault.

## Verify and package

```powershell
python scripts/verify.py
```

The verifier runs unit tests, event replay, an HTTP integration smoke, JavaScript syntax and Obsidian activation smoke, package build, fixture installation, and hash read-back. The distributable files are:

- `dist/poppy-ops-cockpit/manifest.json`
- `dist/poppy-ops-cockpit/main.js`
- `dist/poppy-ops-cockpit/styles.css`

Do not copy them into a real vault before Functional QA and Final Assurance pass against the frozen candidate.

## Supported Codex boundary

The bridge uses `codex app-server --stdio` through `C:\Users\david\.codex\.sandbox-bin\codex.exe`. Compatibility was proven with an initialization response and a real ephemeral `thread/started` event. The earlier WindowsApps executable failed with `Access is denied` and is not used.

The dock can create or resume a dashboard-owned read-only thread through App Server. The bridge disables Codex apps/plugins and the two configured remote MCP servers for these threads; the final isolation probe started only the local `node_repl` server. It retains the prompt as a draft and deliberately does not call `turn/start`, preventing a prompt from invoking tools or external providers without a stronger approval-aware control surface.

## Rollback

Stop the bridge and disable the Obsidian plugin. The cockpit does not modify canonical vault records. Repository-local runtime data may be retained for audit; deletion is not part of rollback.

## Waku

Waku influenced the local-first, event-driven presentation. No Waku source file is copied or executed. See `docs/waku-attribution.md`.
