# Cockpit architecture

```text
Obsidian ItemView  --HTTP/SSE-->  127.0.0.1 bridge
        |                             |-- read configured project vaults
        |                             |-- read canonical packaged Poppy graph
        |                             |-- append local JSONL telemetry
        |                             `-- rebuild disposable SQLite projection
        `-- never writes project vaults
```

The configured project vault remains authoritative for compiled project memory. The cockpit derives views and never copies records back into a vault. External providers remain disabled unless project-local configuration and authority explicitly enable a supported boundary.

Every operational plugin request carries the active project key. The bridge validates it against configuration and applies the scope before returning vault snapshots, runs, events, findings, or server-sent updates. Missing, empty, and unknown keys receive non-success Gray responses. An unmatched vault makes no operational request or SSE connection, and a response with a different project key is discarded. Untagged portfolio history never leaks into a project workspace.

The product root owns `references/poppy-capability-graph.json`. The package build copies it to `config/poppy-capability-graph.json`; the verifier requires byte-for-byte parity.

The bridge binds only to loopback, accepts bounded JSON bodies, and sends restrictive response headers. Raw events are append-only. SQLite is a deterministic replay target and can be deleted and rebuilt. Missing or malformed evidence remains Gray.

The shipped example has no vaults and disables Codex launch. Real paths and supported Codex compatibility live only in ignored or installed local configuration.
