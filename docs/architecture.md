# Product architecture

Poppy has one orchestration core and one optional operational instrument surface.

```text
trusted user turn
      |
      v
Codex plugin root
  Poppy orchestrator -> typed capability graph -> Project Operations skills
      |                         |
      |                         +-> validators, templates, Bases, receipts
      v
project adapter + project sources (owned outside this repository)
      |
      +-> compiled Obsidian project memory
      |
      +-> localhost telemetry bridge -> disposable SQLite projection
                                            |
                                            v
                                    Obsidian Ops Cockpit
```

`references/poppy-capability-graph.json` is the canonical topology. The cockpit build copies that exact file into its installable package and verification asserts byte parity.

Project sources retain authority for their facts. Poppy stores durable compiled understanding in the project's chosen memory surface and applies explicit authority, freshness, contradiction, and Gray-state rules. The cockpit reads configured vaults and its own append-only event ledger; it does not write canonical vault content.

The bridge is standard-library Python bound to loopback. SQLite is a replayable read model, not an authority source. The Obsidian plugin is dependency-free CommonJS JavaScript and CSS. Codex task preparation is disabled in the shipped example and must be explicitly enabled and revalidated by local configuration.
