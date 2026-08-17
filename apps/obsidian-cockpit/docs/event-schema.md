# Event schema v1

Every event is normalized to the following envelope:

```json
{
  "schema_version": 1,
  "event_id": "evt-stable-id",
  "timestamp": "2026-01-02T09:15:00Z",
  "run_id": "run-id",
  "project": "atlas-demo",
  "kind": "capability.started",
  "status": "current",
  "capability": "delivery",
  "skill": "project-ops-delivery",
  "worker": "implementation-writer",
  "tool": null,
  "approval": "authorized",
  "duration_ms": null,
  "tokens": {"input": 0, "cached": 0, "reasoning": 0, "output": 0},
  "cost": {"amount": null, "currency": "USD", "basis": "unavailable"},
  "evidence": [],
  "parent_id": null,
  "message": "Implementation started",
  "metadata": {}
}
```

Allowed states are `completed`, `current`, `waiting`, `blocked`, `pending`, `failed`, and `gray`. Cost basis is one of `exact`, `estimated`, `shadow-price`, or `unavailable`. Evidence entries preserve `source`, `locator`, `freshness`, `authority`, `contradiction`, and `state`.

Run cost aggregation is deliberately conservative. An available amount must be a finite, non-negative, non-boolean number with a three-letter currency code and an allowed available basis. Malformed, non-finite, negative, boolean, unsupported, or currency-less values normalize to `amount: null` and `basis: unavailable`. If any event has unavailable cost, the whole run reports `amount: null`, `currency: null`, and `basis: unavailable`; known subtotals are never presented as the run total. A run is summed only when every available event has the same explicit currency, which is preserved in the aggregate (including non-USD currencies). Mixed or inconsistent currencies degrade the entire run to unavailable instead of being relabelled or summed. Otherwise, mixed events use the least exact allowed basis in this order: `shadow-price`, `estimated`, then `exact`. The aggregate never emits a fifth ad-hoc basis. API responses use strict JSON serialization and fail Gray rather than emitting non-standard `NaN` or infinity tokens.

Every deterministic optimization finding includes an `action` plus one or more structured `references`. Event references carry event, run, and project identity. Source references carry project/source identity and a locator. A finding without actionable lineage is invalid and must render Gray.

Kinds are open for compatibility, while the cockpit recognizes capability, skill, worker, tool, approval, verification, evidence, vault, run, plan, and Codex lifecycle prefixes. Unknown kinds are retained rather than discarded.
