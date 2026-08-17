# Event schema v1

Every event is normalized to the following envelope:

```json
{
  "schema_version": 1,
  "event_id": "evt-stable-id",
  "timestamp": "2026-08-17T09:15:00Z",
  "run_id": "run-id",
  "project": "everaway",
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

Run cost aggregation is deliberately conservative. If any event has unavailable cost, the whole run reports `amount: null` and `basis: unavailable`; known subtotals are never presented as the run total. Otherwise, mixed events use the least exact allowed basis in this order: `shadow-price`, `estimated`, then `exact`. The aggregate never emits a fifth ad-hoc basis.

Every deterministic optimization finding includes an `action` plus one or more structured `references`. Event references carry event, run, and project identity. Source references carry project/source identity and a locator. A finding without actionable lineage is invalid and must render Gray.

Kinds are open for compatibility, while the cockpit recognizes capability, skill, worker, tool, approval, verification, evidence, vault, run, plan, and Codex lifecycle prefixes. Unknown kinds are retained rather than discarded.
