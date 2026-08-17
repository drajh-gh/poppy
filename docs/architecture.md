# Architecture

Poppy Ops Cockpit is a desktop-only Obsidian `ItemView` backed by a localhost Python service. The plugin is a deliberately thin read interface; the bridge owns cross-vault discovery, event normalization, append-only storage, deterministic projections, and supported Codex adapter boundaries.

```text
Obsidian ItemView  --HTTP/SSE-->  127.0.0.1 bridge
        |                             |-- read Sloski vault
        |                             |-- read EverAway vault
        |                             |-- read Poppy capability graph
        |                             |-- append runtime/events.jsonl
        |                             `-- derive runtime/poppy-ops.sqlite3
        `-- no canonical vault writes
```

## Trust and authority boundaries

The two vaults remain authoritative for compiled project memory. The cockpit derives views and never copies canonical records back into either vault. External providers remain behind read-only status and deep links. The bridge binds to loopback, responds with restrictive headers, accepts JSON bodies only on bounded local endpoints, and has no provider credentials.

Codex is an adapter, not an inferred data source. The bridge exposes compatibility as `green` only after it receives a real event from an explicitly supported interface. Process discovery, synthetic fixtures, or private storage never satisfy that contract.

## Storage

`events.jsonl` is immutable input. Every accepted event receives a stable event ID and schema version. SQLite is disposable: replaying the same ledger recreates the same rows, run summaries, and deterministic findings. Price estimates include the label and basis used; unknown model pricing remains unavailable.

## Design direction

Subject: one operator maintaining Poppy across confidential project vaults. Job: reveal what the system is doing beneath the surface without turning operations into a generic admin console.

- Palette: Night ledger `#111417`, graphite `#1b2025`, paper mist `#e7e9e4`, signal cyan `#70d6c8`, amber `#e7b66b`, fault coral `#df776f`.
- Type: Obsidian system UI for body, condensed system faces for headings, tabular monospace for telemetry.
- Layout: narrow command rail, wide live execution rail, quiet evidence desk.
- Signature: a vertical live execution rail that reads like an instrument trace; node states illuminate in place rather than becoming decorative cards.
- Motion: one brief rail pulse for new events, removed under reduced-motion preferences.

Initial critique removed gradients, oversized KPI cards, and a decorative grid. State and lineage now carry the visual character. This is specific to Poppy's graph and evidence vocabulary rather than a reusable SaaS dashboard theme.

