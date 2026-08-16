---
type: analysis
record_kind: operational-control
project: {{project_key}}
status: current
pm_state: recorded
run_id:
coverage: Gray
updated: {{date}}
valid_as_of: {{date}}
review_after: {{review_after}}
sensitivity: {{sensitivity}}
sources: []
---

# Operational control run

## Retrieval ledger

Record one logical request per normalized provider, stable source ID, and request fingerprint. Keep physical attempts, retained failures, checkpoint-before/checkpoint-after, and reuse events together.

## Canonical source preflight

Record stable or verified locator, retired locators, mutable-target discovery, freshness, and provider change-control limitations.

## Human authority and Gray assertions

Link active, expired, or superseded authority receipts. Missing required evidence remains Gray.

## Release tuples

Record source revision, artifact digest, build, delivery/store event, runtime identity, missing links, and evidence references separately.

## Validation

Validate the normalized JSON evidence with `validate_operational_control_packet.py`. A valid packet is internally consistent; it is not external-write or release authority.
